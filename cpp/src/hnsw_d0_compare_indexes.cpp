#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_query_tracer.hpp"

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace {

using Index = hnswlib::HierarchicalNSW<float>;
using Event = narhnsw::QueryTraceEvent<float>;

struct Matrix {
    std::size_t rows{};
    std::size_t columns{};
    std::vector<float> values;
};

struct Truth {
    std::size_t rows{};
    std::size_t k{};
    std::vector<std::uint32_t> labels;
};

class MetricSpace final : public hnswlib::SpaceInterface<float> {
   public:
    MetricSpace(std::size_t dimensions, bool inner_product)
        : state_{dimensions, inner_product} {}
    std::size_t get_data_size() override { return state_.dimensions * sizeof(float); }
    hnswlib::DISTFUNC<float> get_dist_func() override { return distance_function; }
    void* get_dist_func_param() override { return &state_; }
    float distance(const void* left, const void* right) const {
        return distance_function(left, right, &state_);
    }

   private:
    struct State {
        std::size_t dimensions;
        bool inner_product;
    };
    static float distance_function(const void* left_raw, const void* right_raw,
                                   const void* state_raw) {
        const auto* state = static_cast<const State*>(state_raw);
        const auto* left = static_cast<const float*>(left_raw);
        const auto* right = static_cast<const float*>(right_raw);
        float value = 0.0F;
        if (state->inner_product) {
            for (std::size_t dimension = 0; dimension < state->dimensions; ++dimension)
                value += left[dimension] * right[dimension];
            return 1.0F - value;
        }
        for (std::size_t dimension = 0; dimension < state->dimensions; ++dimension) {
            const float difference = left[dimension] - right[dimension];
            value += difference * difference;
        }
        return value;
    }
    State state_;
};

template <typename Value>
Value read_scalar(std::ifstream& input) {
    Value value{};
    input.read(reinterpret_cast<char*>(&value), sizeof(value));
    if (!input) throw std::runtime_error("binary input ended unexpectedly");
    return value;
}

Matrix read_matrix(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot open query matrix");
    Matrix matrix;
    matrix.rows = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    matrix.columns = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    matrix.values.resize(matrix.rows * matrix.columns);
    input.read(reinterpret_cast<char*>(matrix.values.data()),
               static_cast<std::streamsize>(matrix.values.size() * sizeof(float)));
    if (!input || input.peek() != std::ifstream::traits_type::eof())
        throw std::runtime_error("invalid query matrix payload");
    return matrix;
}

Truth read_truth(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot open truth matrix");
    Truth truth;
    truth.rows = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    truth.k = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    truth.labels.resize(truth.rows * truth.k);
    input.read(reinterpret_cast<char*>(truth.labels.data()),
               static_cast<std::streamsize>(truth.labels.size() * sizeof(std::uint32_t)));
    if (!input || input.peek() != std::ifstream::traits_type::eof())
        throw std::runtime_error("invalid truth matrix payload");
    return truth;
}

std::vector<std::size_t> parse_efs(const std::string& raw) {
    std::vector<std::size_t> values;
    std::stringstream stream(raw);
    std::string token;
    while (std::getline(stream, token, ',')) values.push_back(std::stoul(token));
    if (values.empty()) throw std::invalid_argument("empty ef grid");
    return values;
}

std::vector<std::pair<float, std::uint32_t>> ordered(
    std::priority_queue<std::pair<float, hnswlib::labeltype>> heap) {
    std::vector<std::pair<float, std::uint32_t>> result;
    while (!heap.empty()) {
        result.emplace_back(heap.top().first, static_cast<std::uint32_t>(heap.top().second));
        heap.pop();
    }
    std::sort(result.begin(), result.end());
    return result;
}

std::string labels(const std::vector<std::pair<float, std::uint32_t>>& result) {
    std::ostringstream output;
    for (std::size_t index = 0; index < result.size(); ++index) {
        if (index) output << ';';
        output << result[index].second;
    }
    return output.str();
}

std::size_t recall_hits(const std::vector<std::pair<float, std::uint32_t>>& result,
                        const Truth& truth, std::size_t query_id) {
    std::set<std::uint32_t> expected;
    for (std::size_t offset = 0; offset < truth.k; ++offset)
        expected.insert(truth.labels[query_id * truth.k + offset]);
    std::size_t hits = 0;
    for (const auto& item : result) hits += expected.count(item.second);
    return hits;
}

std::vector<Event> phase_events(const std::vector<Event>& events, const std::string& kind) {
    std::vector<Event> result;
    for (const auto& event : events) {
        if (event.phase != "base") continue;
        if (kind == "visited" && (event.event == "enqueued" || event.event == "pruned"))
            result.push_back(event);
        if (kind == "expanded" && event.event == "expanded") result.push_back(event);
        if (kind == "accepted" && event.event == "enqueued") result.push_back(event);
    }
    return result;
}

std::optional<std::size_t> first_difference(const std::vector<Event>& left,
                                             const std::vector<Event>& right) {
    const auto shared = std::min(left.size(), right.size());
    for (std::size_t index = 0; index < shared; ++index) {
        if (std::tie(left[index].source, left[index].target, left[index].event) !=
            std::tie(right[index].source, right[index].target, right[index].event))
            return index;
    }
    if (left.size() != right.size()) return shared;
    return std::nullopt;
}

std::vector<hnswlib::tableint> neighbors(const Index& index, hnswlib::tableint node) {
    auto* raw = index.get_linklist_at_level(node, 0);
    const auto degree = index.getListCount(raw);
    const auto* ids = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
    return {ids, ids + degree};
}

bool has_edge(const Index& index, hnswlib::tableint source, hnswlib::tableint target) {
    const auto adjacent = neighbors(index, source);
    return std::find(adjacent.begin(), adjacent.end(), target) != adjacent.end();
}

std::optional<Event> first_absent_original_edge(const std::vector<Event>& events,
                                                 const Index& primary) {
    for (const auto& event : events) {
        if (event.phase != "base" || (event.event != "enqueued" && event.event != "pruned"))
            continue;
        if (!has_edge(primary, event.source, event.target)) return event;
    }
    return std::nullopt;
}

long long optional_index(const std::optional<std::size_t>& value) {
    return value ? static_cast<long long>(*value) : -1;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 11) {
            std::cerr << "usage: hnsw_d0_compare_indexes ORIGINAL PRIMARY QUERIES TRUTH "
                         "METRIC EFS RUN_ID OUTPUT_CSV OUTPUT_COVERAGE OUTPUT_META\n";
            return 2;
        }
        const Matrix queries = read_matrix(argv[3]);
        const Truth truth = read_truth(argv[4]);
        const std::string metric = argv[5];
        if (metric != "l2" && metric != "ip")
            throw std::invalid_argument("metric must be l2 or ip");
        const auto efs = parse_efs(argv[6]);
        const std::string run_id = argv[7];
        if (queries.rows != 500 || truth.rows != 500 || truth.k != 10)
            throw std::invalid_argument("D0-D requires frozen 500-query top-10 inputs");
        MetricSpace original_space(queries.columns, metric == "ip");
        MetricSpace primary_space(queries.columns, metric == "ip");
        Index original(&original_space, argv[1], false);
        Index primary(&primary_space, argv[2], false);
        if (original.cur_element_count.load() != 10000 ||
            primary.cur_element_count.load() != 10000)
            throw std::invalid_argument("D0-D requires two 10K indexes");

        std::ofstream output(argv[8]);
        if (!output) throw std::runtime_error("cannot create D0-D output");
        std::ofstream coverage(argv[9]);
        if (!coverage) throw std::runtime_error("cannot create D0-D coverage output");
        coverage << "run_id,ef_search,query_id,source_internal,target_internal,"
                    "source_external,target_external,strict_progress,beam_admissible,"
                    "target_is_missed_true_top10,target_expanded_original\n";
        output << "run_id,ef_search,query_id,original_recall,primary_recall,original_ndc,"
                  "primary_ndc,first_visited_divergence,first_queue_divergence,"
                  "first_result_heap_divergence,absent_source_internal,absent_target_internal,"
                  "absent_source_external,absent_target_external,strict_progress,"
                  "beam_admissible,target_is_missed_true_top10,target_expanded_original,"
                  "original_results,primary_results\n";
        std::size_t harmed = 0;
        std::size_t coverage_rows = 0;
        for (const auto ef : efs) {
            original.setEf(ef);
            primary.setEf(ef);
            for (std::size_t query_id = 0; query_id < queries.rows; ++query_id) {
                const auto* query = queries.values.data() + query_id * queries.columns;
                const auto original_trace =
                    narhnsw::HnswQueryTracer<float>::search(original, query, truth.k, ef, query_id);
                const auto primary_trace =
                    narhnsw::HnswQueryTracer<float>::search(primary, query, truth.k, ef, query_id);
                const auto original_result = ordered(original_trace.results);
                const auto primary_result = ordered(primary_trace.results);
                if (ordered(original.searchKnn(query, truth.k)) != original_result ||
                    ordered(primary.searchKnn(query, truth.k)) != primary_result)
                    throw std::runtime_error("trace diverged from native searchKnn");
                const auto original_hits = recall_hits(original_result, truth, query_id);
                const auto primary_hits = recall_hits(primary_result, truth, query_id);
                if (original_hits <= primary_hits) continue;
                ++harmed;
                const auto original_visited = phase_events(original_trace.events, "visited");
                const auto primary_visited = phase_events(primary_trace.events, "visited");
                const auto original_expanded = phase_events(original_trace.events, "expanded");
                const auto primary_expanded = phase_events(primary_trace.events, "expanded");
                const auto original_accepted = phase_events(original_trace.events, "accepted");
                const auto primary_accepted = phase_events(primary_trace.events, "accepted");
                const auto absent = first_absent_original_edge(original_visited, primary);
                std::set<std::pair<hnswlib::tableint, hnswlib::tableint>> written_edges;
                std::set<std::uint32_t> primary_labels;
                for (const auto& item : primary_result) primary_labels.insert(item.second);
                std::set<std::uint32_t> missed_truth;
                for (std::size_t offset = 0; offset < truth.k; ++offset) {
                    const auto label = truth.labels[query_id * truth.k + offset];
                    if (!primary_labels.count(label)) missed_truth.insert(label);
                }
                for (const auto& event : original_visited) {
                    if (has_edge(primary, event.source, event.target) ||
                        !written_edges.emplace(event.source, event.target).second)
                        continue;
                    const auto source_label = original.getExternalLabel(event.source);
                    const auto target_label = original.getExternalLabel(event.target);
                    const float source_distance = original_space.distance(
                        query, original.getDataByInternalId(event.source));
                    const bool strict_edge = event.distance_to_query < source_distance;
                    const bool beam_edge = event.distance_to_query < event.lower_bound_before;
                    const bool expanded_edge = std::any_of(
                        original_expanded.begin(), original_expanded.end(),
                        [&](const Event& expanded) { return expanded.source == event.target; });
                    coverage << run_id << ',' << ef << ',' << query_id << ',' << event.source
                             << ',' << event.target << ',' << source_label << ',' << target_label
                             << ',' << strict_edge << ',' << beam_edge << ','
                             << missed_truth.count(static_cast<std::uint32_t>(target_label)) << ','
                             << expanded_edge << '\n';
                    ++coverage_rows;
                }
                long long source_internal = -1;
                long long target_internal = -1;
                long long source_external = -1;
                long long target_external = -1;
                bool strict = false;
                bool beam = false;
                bool target_missed_truth = false;
                bool target_expanded = false;
                if (absent) {
                    source_internal = absent->source;
                    target_internal = absent->target;
                    source_external = static_cast<long long>(original.getExternalLabel(absent->source));
                    target_external = static_cast<long long>(original.getExternalLabel(absent->target));
                    const float source_distance = original_space.distance(
                        query, original.getDataByInternalId(absent->source));
                    strict = absent->distance_to_query < source_distance;
                    beam = absent->distance_to_query < absent->lower_bound_before;
                    for (std::size_t offset = 0; offset < truth.k; ++offset) {
                        const auto label = truth.labels[query_id * truth.k + offset];
                        target_missed_truth = target_missed_truth ||
                                              (static_cast<std::uint32_t>(target_external) == label &&
                                               !primary_labels.count(label));
                    }
                    target_expanded = std::any_of(
                        original_expanded.begin(), original_expanded.end(),
                        [&](const Event& event) { return event.source == absent->target; });
                }
                output << run_id << ',' << ef << ',' << query_id << ','
                       << static_cast<double>(original_hits) / truth.k << ','
                       << static_cast<double>(primary_hits) / truth.k << ','
                       << original_trace.upper_evaluations + original_trace.base_evaluations + 2
                       << ','
                       << primary_trace.upper_evaluations + primary_trace.base_evaluations + 2
                       << ',' << optional_index(first_difference(original_visited, primary_visited))
                       << ',' << optional_index(first_difference(original_expanded, primary_expanded))
                       << ',' << optional_index(first_difference(original_accepted, primary_accepted))
                       << ',' << source_internal << ',' << target_internal << ',' << source_external
                       << ',' << target_external << ',' << strict << ',' << beam << ','
                       << target_missed_truth << ',' << target_expanded << ','
                       << labels(original_result) << ',' << labels(primary_result) << '\n';
            }
        }
        std::ofstream metadata(argv[10]);
        metadata << "{\n  \"status\": \"complete\",\n  \"run_id\": \"" << run_id
                 << "\",\n  \"harmed_query_ef_pairs\": " << harmed
                 << ",\n  \"original_only_trace_edge_rows\": " << coverage_rows
                 << ",\n  \"trace_matches_native_search\": true,\n"
                    "  \"new_ef_points\": false,\n"
                    "  \"validation_dev_accessed\": false,\n"
                    "  \"formal_test_members_accessed\": false\n}\n";
        std::cout << "status=complete run_id=" << run_id << " harmed=" << harmed << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
