#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_query_tracer.hpp"

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
        : state_{dimensions, &counter_, inner_product} {}
    std::size_t get_data_size() override { return state_.dimensions * sizeof(float); }
    hnswlib::DISTFUNC<float> get_dist_func() override { return distance; }
    void* get_dist_func_param() override { return &state_; }
    void reset() { counter_.store(0); }
    std::uint64_t count() const { return counter_.load(); }
    void set_counting(bool enabled) { state_.counting = enabled; }

   private:
    struct State {
        std::size_t dimensions;
        std::atomic<std::uint64_t>* counter;
        bool inner_product;
        bool counting{true};
    };
    static float distance(const void* left_raw, const void* right_raw,
                          const void* state_raw) {
        const auto* state = static_cast<const State*>(state_raw);
        const auto* left = static_cast<const float*>(left_raw);
        const auto* right = static_cast<const float*>(right_raw);
        if (state->counting)
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
    if (!input) throw std::runtime_error("cannot open query matrix");
    Matrix matrix;
    matrix.rows = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    matrix.columns = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    matrix.values.resize(matrix.rows * matrix.columns);
    input.read(reinterpret_cast<char*>(matrix.values.data()),
               static_cast<std::streamsize>(matrix.values.size() * sizeof(float)));
    if (!input || input.peek() != std::ifstream::traits_type::eof())
        throw std::runtime_error("invalid query matrix payload length");
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
        throw std::runtime_error("invalid truth matrix payload length");
    return truth;
}

std::vector<std::size_t> parse_efs(const std::string& raw) {
    std::vector<std::size_t> values;
    std::stringstream stream(raw);
    std::string token;
    while (std::getline(stream, token, ',')) values.push_back(std::stoul(token));
    if (values.empty() || !std::is_sorted(values.begin(), values.end()) ||
        std::adjacent_find(values.begin(), values.end()) != values.end())
        throw std::invalid_argument("ef values must be unique and increasing");
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

std::string labels_string(const std::vector<std::pair<float, std::uint32_t>>& result) {
    std::ostringstream output;
    for (std::size_t index = 0; index < result.size(); ++index) {
        if (index) output << ';';
        output << result[index].second;
    }
    return output.str();
}

struct ExpansionProgress {
    float source_distance{};
    float lower_bound{};
    bool strict{};
    bool eta{};
    bool beam{};
};

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 10) {
            std::cerr << "usage: hnsw_e0_evaluate_index INDEX QUERIES TRUTH METRIC EFS WARMUP "
                         "ROUNDS RUN_ID OUTPUT_CSV\n";
            return 2;
        }
        const std::filesystem::path index_path = argv[1];
        const Matrix queries = read_matrix(argv[2]);
        const Truth truth = read_truth(argv[3]);
        const std::string metric = argv[4];
        if (metric != "l2" && metric != "ip")
            throw std::invalid_argument("metric must be l2 or ip");
        const auto efs = parse_efs(argv[5]);
        const auto warmup = std::stoul(argv[6]);
        const auto rounds = std::stoul(argv[7]);
        const std::string run_id = argv[8];
        const std::filesystem::path output_path = argv[9];
        if (queries.rows != 500 || truth.rows != 500 || truth.k != 10 ||
            queries.rows != truth.rows || rounds != 3)
            throw std::invalid_argument("E0 requires 500 queries, top-10 truth, and 3 rounds");
        CountingSpace space(queries.columns, metric == "ip");
        Index index(&space, index_path.string(), false);
        if (index.cur_element_count.load() != 10000)
            throw std::invalid_argument("E0 evaluator requires a 10K index");
        std::ofstream output(output_path);
        if (!output) throw std::runtime_error("cannot create query output");
        output << "run_id,ef_search,query_id,latency_round,recall_at_10,full_recall,"
                  "recall_at_1,returned_top10,ndc,upper_evaluations,upper_improvements,"
                  "base_evaluations,base_expansions,traversal_hops,"
                  "strict_progress_rate,multiplicative_progress_eta_0_05_rate,"
                  "beam_admissible_progress_rate,local_minimum_fraction,latency_ns\n";
        output << std::setprecision(9);
        for (const auto ef : efs) {
            index.setEf(ef);
            for (std::size_t query_id = 0; query_id < std::min(warmup, queries.rows);
                 ++query_id) {
                space.set_counting(false);
                index.searchKnn(queries.values.data() + query_id * queries.columns, truth.k);
            }
            for (std::size_t query_id = 0; query_id < queries.rows; ++query_id) {
                const auto* query = queries.values.data() + query_id * queries.columns;
                space.set_counting(true);
                space.reset();
                const auto trace = narhnsw::HnswQueryTracer<float>::search(
                    index, query, truth.k, ef, query_id);
                const auto ndc = space.count();
                const auto traced = ordered_results(trace.results);
                std::set<std::uint32_t> expected;
                for (std::size_t offset = 0; offset < truth.k; ++offset)
                    expected.insert(truth.labels[query_id * truth.k + offset]);
                std::size_t hits = 0;
                for (const auto& item : traced) hits += expected.count(item.second);

                std::map<hnswlib::tableint, ExpansionProgress> progress;
                std::size_t upper_improvements = 0;
                for (const auto& event : trace.events) {
                    if (event.phase == "upper" && event.event == "improved")
                        ++upper_improvements;
                    if (event.phase != "base") continue;
                    if (event.event == "expanded") {
                        progress[event.source] =
                            {event.distance_to_query, event.lower_bound_before, false, false, false};
                    } else if (event.event == "enqueued" || event.event == "pruned") {
                        auto found = progress.find(event.source);
                        if (found == progress.end()) continue;
                        found->second.strict = found->second.strict ||
                                               event.distance_to_query <
                                                   found->second.source_distance;
                        found->second.eta = found->second.eta ||
                                            event.distance_to_query <=
                                                0.9025F * found->second.source_distance;
                        found->second.beam = found->second.beam ||
                                             event.distance_to_query < found->second.lower_bound;
                    }
                }
                std::size_t strict = 0;
                std::size_t eta = 0;
                std::size_t beam = 0;
                for (const auto& [_, item] : progress) {
                    strict += item.strict;
                    eta += item.eta;
                    beam += item.beam;
                }
                const double denominator =
                    static_cast<double>(std::max<std::size_t>(1, progress.size()));
                for (std::size_t round = 0; round < rounds; ++round) {
                    space.set_counting(false);
                    space.reset();
                    const auto started = Clock::now();
                    const auto reference = ordered_results(index.searchKnn(query, truth.k));
                    const auto finished = Clock::now();
                    if (reference != traced)
                        throw std::runtime_error("query tracer diverged from searchKnn");
                    const auto latency = std::chrono::duration_cast<std::chrono::nanoseconds>(
                                             finished - started)
                                             .count();
                    output << run_id << ',' << ef << ',' << query_id << ',' << round << ','
                           << static_cast<double>(hits) / truth.k << ',' << (hits == truth.k)
                           << ','
                           << (!traced.empty() &&
                               traced.front().second == truth.labels[query_id * truth.k])
                           << ',' << labels_string(traced) << ',' << ndc << ','
                           << trace.upper_evaluations << ',' << upper_improvements << ','
                           << trace.base_evaluations << ',' << trace.base_expansions << ','
                           << upper_improvements + trace.base_expansions << ','
                           << strict / denominator << ','
                           << eta / denominator << ',' << beam / denominator << ','
                           << (progress.size() - strict) / denominator << ',' << latency << '\n';
                }
            }
        }
        std::cout << "status=complete run_id=" << run_id << " queries=" << queries.rows
                  << " efs=" << efs.size() << " rounds=" << rounds << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
