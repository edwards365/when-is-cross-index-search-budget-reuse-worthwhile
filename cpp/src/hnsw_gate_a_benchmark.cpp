#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_query_tracer.hpp"
#include "narhnsw/hnsw_selected_connector.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {

using Index = hnswlib::HierarchicalNSW<float>;
using Clock = std::chrono::steady_clock;

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

class CountingSpace final : public hnswlib::SpaceInterface<float> {
   public:
    CountingSpace(std::size_t dimensions, bool inner_product)
        : state_{dimensions, inner_product, &counter_} {}

    std::size_t get_data_size() override { return state_.dimensions * sizeof(float); }
    hnswlib::DISTFUNC<float> get_dist_func() override { return distance; }
    void* get_dist_func_param() override { return &state_; }
    void reset() { counter_.store(0); }
    std::uint64_t count() const { return counter_.load(); }

   private:
    struct State {
        std::size_t dimensions;
        bool inner_product;
        std::atomic<std::uint64_t>* counter;
    };

    static float distance(const void* left_raw, const void* right_raw, const void* state_raw) {
        const auto* state = static_cast<const State*>(state_raw);
        const auto* left = static_cast<const float*>(left_raw);
        const auto* right = static_cast<const float*>(right_raw);
        state->counter->fetch_add(1, std::memory_order_relaxed);
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

    std::atomic<std::uint64_t> counter_{0};
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
    if (!input) throw std::runtime_error("cannot open matrix input");
    Matrix matrix;
    matrix.rows = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    matrix.columns = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    matrix.values.resize(matrix.rows * matrix.columns);
    input.read(reinterpret_cast<char*>(matrix.values.data()),
               static_cast<std::streamsize>(matrix.values.size() * sizeof(float)));
    if (!input || input.peek() != std::ifstream::traits_type::eof())
        throw std::runtime_error("invalid matrix payload length");
    return matrix;
}

std::vector<std::uint32_t> read_order(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot open insertion order");
    const auto count = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    std::vector<std::uint32_t> order(count);
    input.read(reinterpret_cast<char*>(order.data()),
               static_cast<std::streamsize>(count * sizeof(std::uint32_t)));
    if (!input || input.peek() != std::ifstream::traits_type::eof())
        throw std::runtime_error("invalid insertion-order payload length");
    return order;
}

Truth read_truth(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot open ground truth");
    Truth truth;
    truth.rows = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    truth.k = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    truth.labels.resize(truth.rows * truth.k);
    input.read(reinterpret_cast<char*>(truth.labels.data()),
               static_cast<std::streamsize>(truth.labels.size() * sizeof(std::uint32_t)));
    if (!input || input.peek() != std::ifstream::traits_type::eof())
        throw std::runtime_error("invalid truth payload length");
    return truth;
}

std::map<std::uint32_t, std::vector<std::uint32_t>> read_plan(
    const std::filesystem::path& path) {
    std::map<std::uint32_t, std::vector<std::uint32_t>> plan;
    if (path == "-") return plan;
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open selection plan");
    std::string line;
    while (std::getline(input, line)) {
        if (line.empty()) continue;
        const auto comma = line.find(',');
        if (comma == std::string::npos) throw std::runtime_error("invalid plan row");
        const auto source = static_cast<std::uint32_t>(std::stoul(line.substr(0, comma)));
        const auto target = static_cast<std::uint32_t>(std::stoul(line.substr(comma + 1)));
        plan[source].push_back(target);
    }
    return plan;
}

std::vector<std::size_t> parse_efs(const std::string& raw) {
    std::vector<std::size_t> values;
    std::stringstream stream(raw);
    std::string token;
    while (std::getline(stream, token, ',')) values.push_back(std::stoul(token));
    if (values.empty()) throw std::invalid_argument("ef list is empty");
    return values;
}

std::vector<std::pair<float, std::uint32_t>> ordered_results(
    std::priority_queue<std::pair<float, hnswlib::labeltype>> heap) {
    std::vector<std::pair<float, std::uint32_t>> result;
    while (!heap.empty()) {
        result.emplace_back(heap.top().first, static_cast<std::uint32_t>(heap.top().second));
        heap.pop();
    }
    std::sort(result.begin(), result.end(), [](const auto& left, const auto& right) {
        return left.first < right.first ||
               (left.first == right.first && left.second < right.second);
    });
    return result;
}

std::uint64_t edge_key(hnswlib::tableint source, hnswlib::tableint target) {
    return (static_cast<std::uint64_t>(source) << 32U) | target;
}

std::unordered_set<std::uint64_t> graph_edges(const Index& index) {
    std::unordered_set<std::uint64_t> edges;
    for (hnswlib::tableint source = 0; source < index.cur_element_count.load(); ++source) {
        auto* raw = index.get_linklist0(source);
        const auto degree = index.getListCount(raw);
        const auto* targets = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
        for (std::size_t offset = 0; offset < degree; ++offset)
            edges.insert(edge_key(source, targets[offset]));
    }
    return edges;
}

void export_edges(const Index& index, const std::filesystem::path& path) {
    std::ofstream output(path);
    if (!output) throw std::runtime_error("cannot create edge output");
    output << "source_internal,target_internal,source_label,target_label\n";
    for (hnswlib::tableint source = 0; source < index.cur_element_count.load(); ++source) {
        auto* raw = index.get_linklist0(source);
        const auto degree = index.getListCount(raw);
        const auto* targets = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
        for (std::size_t offset = 0; offset < degree; ++offset) {
            output << source << ',' << targets[offset] << ',' << index.getExternalLabel(source)
                   << ',' << index.getExternalLabel(targets[offset]) << '\n';
        }
    }
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 20) {
            std::cerr << "usage: hnsw_gate_a_benchmark POINTS ORDER QUERIES TRUTH PLAN METRIC "
                         "M EFCON SEED DATASET METHOD CONTROL_SEED EFS WARMUP ROUNDS CONFIG_HASH "
                         "HARDWARE_ID RUN_ID OUTPUT_DIR\n";
            return 2;
        }
        const Matrix points = read_matrix(argv[1]);
        const auto order = read_order(argv[2]);
        const Matrix queries = read_matrix(argv[3]);
        const Truth truth = read_truth(argv[4]);
        const auto plan = read_plan(argv[5]);
        const std::string metric = argv[6];
        const std::size_t m = std::stoul(argv[7]);
        const std::size_t ef_construction = std::stoul(argv[8]);
        const std::size_t seed = std::stoul(argv[9]);
        const std::string dataset = argv[10];
        const std::string method = argv[11];
        const std::string control_seed = argv[12];
        const auto efs = parse_efs(argv[13]);
        const std::size_t warmup = std::stoul(argv[14]);
        const std::size_t rounds = std::stoul(argv[15]);
        const std::string config_hash = argv[16];
        const std::string hardware_id = argv[17];
        const std::string run_id = argv[18];
        const std::filesystem::path output = argv[19];
        if (metric != "l2" && metric != "ip")
            throw std::invalid_argument("metric must be l2 or ip");
        if (points.rows != order.size() || points.columns != queries.columns ||
            queries.rows != truth.rows || truth.k == 0 || rounds == 0)
            throw std::invalid_argument("input dimensions are inconsistent");

        std::filesystem::create_directories(output);
        CountingSpace space(points.columns, metric == "ip");
        Index index(&space, points.rows, m, ef_construction, seed);
        const auto build_started = Clock::now();
        for (const auto label : order) {
            if (label >= points.rows) throw std::invalid_argument("insertion label is invalid");
            index.addPoint(points.values.data() + label * points.columns, label);
        }
        const auto build_finished = Clock::now();
        const auto before_edges = graph_edges(index);

        const auto treatment_started = Clock::now();
        std::size_t proposed_targets = 0;
        for (const auto& [source_label, target_labels] : plan) {
            if (target_labels.size() != m)
                throw std::invalid_argument("every plan source must contain exactly M targets");
            const auto source = index.label_lookup_.at(source_label);
            std::vector<hnswlib::tableint> targets;
            targets.reserve(target_labels.size());
            for (const auto label : target_labels) targets.push_back(index.label_lookup_.at(label));
            narhnsw::mutually_connect_selected(index, source, targets, 0);
            proposed_targets += targets.size();
        }
        const auto treatment_finished = Clock::now();
        const auto after_edges = graph_edges(index);
        export_edges(index, output / "edges.csv");
        index.saveIndex((output / "index.bin").string());

        std::ofstream query_output(output / "queries.csv");
        if (!query_output) throw std::runtime_error("cannot create query output");
        query_output << "dataset,method,build_seed,control_seed,ef_search,query_id,"
                        "latency_round,recall_at_10,full_recall,returned_top10,ndc,"
                        "visited_nodes,candidate_queue_pushes,candidate_queue_pops,"
                        "result_queue_pushes,result_queue_pops,latency_ns,config_hash,"
                        "hardware_id,run_id\n";
        query_output << std::setprecision(9);
        for (const auto ef : efs) {
            index.setEf(ef);
            for (std::size_t query_id = 0; query_id < std::min(warmup, queries.rows);
                 ++query_id) {
                index.searchKnn(queries.values.data() + query_id * queries.columns, truth.k);
            }
            for (std::size_t query_id = 0; query_id < queries.rows; ++query_id) {
                const auto* query = queries.values.data() + query_id * queries.columns;
                space.reset();
                const auto trace = narhnsw::HnswQueryTracer<float>::search(
                    index, query, truth.k, ef, query_id);
                const auto ndc = space.count();
                const auto traced_results = ordered_results(trace.results);
                std::set<std::uint32_t> expected;
                for (std::size_t offset = 0; offset < truth.k; ++offset)
                    expected.insert(truth.labels[query_id * truth.k + offset]);
                std::size_t hits = 0;
                std::ostringstream labels;
                for (std::size_t offset = 0; offset < traced_results.size(); ++offset) {
                    if (offset) labels << ';';
                    labels << traced_results[offset].second;
                    hits += expected.count(traced_results[offset].second);
                }
                std::set<hnswlib::tableint> visited;
                std::size_t candidate_pushes = 1;
                std::size_t candidate_pops = 0;
                std::size_t result_pushes = 1;
                std::size_t result_pops = 0;
                const std::size_t search_ef = std::max(ef, truth.k);
                for (const auto& event : trace.events) {
                    if (event.event == "entry" || event.event == "improved" ||
                        event.event == "evaluated" || event.event == "enqueued" ||
                        event.event == "pruned")
                        visited.insert(event.target);
                    if (event.event == "expanded") ++candidate_pops;
                    if (event.event == "enqueued") {
                        ++candidate_pushes;
                        ++result_pushes;
                        if (event.result_size_before >= search_ef) ++result_pops;
                    }
                }
                for (std::size_t round = 0; round < rounds; ++round) {
                    space.reset();
                    const auto latency_started = Clock::now();
                    const auto reference = ordered_results(index.searchKnn(query, truth.k));
                    const auto latency_finished = Clock::now();
                    if (reference != traced_results)
                        throw std::runtime_error("query tracer diverged from upstream searchKnn");
                    const auto latency_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                                                latency_finished - latency_started)
                                                .count();
                    query_output << dataset << ',' << method << ',' << seed << ',';
                    if (control_seed != "-") query_output << control_seed;
                    query_output << ',' << ef << ',' << query_id << ',' << round << ','
                                 << static_cast<double>(hits) / truth.k << ','
                                 << (hits == truth.k) << ',' << labels.str() << ',' << ndc << ','
                                 << visited.size() << ',' << candidate_pushes << ','
                                 << candidate_pops << ',' << result_pushes << ',' << result_pops
                                 << ',' << latency_ns << ',' << config_hash << ',' << hardware_id
                                 << ',' << run_id << '\n';
                }
            }
        }

        std::size_t intersection = 0;
        for (const auto edge : before_edges) intersection += after_edges.count(edge);
        const std::size_t edge_union = before_edges.size() + after_edges.size() - intersection;
        const auto index_size = std::filesystem::file_size(output / "index.bin");
        std::ofstream metadata(output / "metadata.json");
        metadata << std::fixed << std::setprecision(9)
                 << "{\n"
                 << "  \"run_id\": \"" << run_id << "\",\n"
                 << "  \"method\": \"" << method << "\",\n"
                 << "  \"build_seed\": " << seed << ",\n"
                 << "  \"control_seed\": "
                 << (control_seed == "-" ? "null" : control_seed) << ",\n"
                 << "  \"points\": " << points.rows << ",\n"
                 << "  \"queries\": " << queries.rows << ",\n"
                 << "  \"plan_sources\": " << plan.size() << ",\n"
                 << "  \"proposed_targets\": " << proposed_targets << ",\n"
                 << "  \"before_directed_edges\": " << before_edges.size() << ",\n"
                 << "  \"after_directed_edges\": " << after_edges.size() << ",\n"
                 << "  \"directed_edge_jaccard\": "
                 << static_cast<double>(intersection) / edge_union << ",\n"
                 << "  \"build_seconds\": "
                 << std::chrono::duration<double>(build_finished - build_started).count() << ",\n"
                 << "  \"treatment_seconds\": "
                 << std::chrono::duration<double>(treatment_finished - treatment_started).count()
                 << ",\n"
                 << "  \"index_size_bytes\": " << index_size << ",\n"
                 << "  \"config_hash\": \"" << config_hash << "\",\n"
                 << "  \"hardware_id\": \"" << hardware_id << "\",\n"
                 << "  \"formal_test_members_accessed\": false\n"
                 << "}\n";
        std::cout << "run_id=" << run_id << " points=" << points.rows
                  << " plan_sources=" << plan.size() << " build_seconds="
                  << std::chrono::duration<double>(build_finished - build_started).count()
                  << " treatment_seconds="
                  << std::chrono::duration<double>(treatment_finished - treatment_started).count()
                  << " index_size_bytes=" << index_size << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
