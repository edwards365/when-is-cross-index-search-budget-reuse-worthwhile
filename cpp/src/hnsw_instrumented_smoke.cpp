#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_candidate_logger.hpp"
#include "narhnsw/hnsw_query_tracer.hpp"

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <optional>
#include <queue>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

using Point = std::vector<float>;

class CountingL2Space final : public hnswlib::SpaceInterface<float> {
   public:
    explicit CountingL2Space(std::size_t dimensions) : state_{dimensions, &counter_} {}

    std::size_t get_data_size() override { return state_.dimensions * sizeof(float); }
    hnswlib::DISTFUNC<float> get_dist_func() override { return distance; }
    void* get_dist_func_param() override { return &state_; }
    void reset() { counter_.store(0); }
    long count() const { return counter_.load(); }

   private:
    struct State {
        std::size_t dimensions;
        std::atomic<long>* counter;
    };

    static float distance(const void* left_raw, const void* right_raw, const void* state_raw) {
        const auto* state = static_cast<const State*>(state_raw);
        const auto* left = static_cast<const float*>(left_raw);
        const auto* right = static_cast<const float*>(right_raw);
        state->counter->fetch_add(1, std::memory_order_relaxed);
        float result = 0.0F;
        for (std::size_t i = 0; i < state->dimensions; ++i) {
            const float difference = left[i] - right[i];
            result += difference * difference;
        }
        return result;
    }

    std::atomic<long> counter_{0};
    State state_;
};

float squared_l2(const Point& left, const Point& right) {
    float result = 0.0F;
    for (std::size_t i = 0; i < left.size(); ++i) {
        const float difference = left[i] - right[i];
        result += difference * difference;
    }
    return result;
}

std::set<std::size_t> exact_top_k(const std::vector<Point>& base, const Point& query,
                                  std::size_t k) {
    std::vector<std::pair<float, std::size_t>> distances;
    distances.reserve(base.size());
    for (std::size_t i = 0; i < base.size(); ++i) distances.emplace_back(squared_l2(base[i], query), i);
    std::partial_sort(distances.begin(), distances.begin() + static_cast<std::ptrdiff_t>(k),
                      distances.end());
    std::set<std::size_t> result;
    for (std::size_t i = 0; i < k; ++i) result.insert(distances[i].second);
    return result;
}

struct GraphSummary {
    std::size_t directed_edges{0};
    std::size_t reciprocal_directed_edges{0};
    std::size_t max_degree{0};
};

std::set<std::size_t> labels_from_heap(
    std::priority_queue<std::pair<float, hnswlib::labeltype>> heap) {
    std::set<std::size_t> labels;
    while (!heap.empty()) {
        labels.insert(heap.top().second);
        heap.pop();
    }
    return labels;
}

GraphSummary inspect_level_zero(const hnswlib::HierarchicalNSW<float>& index, std::size_t n) {
    GraphSummary summary;
    std::vector<std::set<hnswlib::tableint>> adjacency(n);
    for (std::size_t node = 0; node < n; ++node) {
        auto* raw = index.get_linklist0(static_cast<hnswlib::tableint>(node));
        const auto degree = index.getListCount(raw);
        if (degree > index.maxM0_) throw std::runtime_error("level-zero maximum degree exceeded");
        const auto* neighbors = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
        for (std::size_t offset = 0; offset < degree; ++offset) {
            const auto neighbor = neighbors[offset];
            if (neighbor >= n) throw std::runtime_error("invalid neighbor id");
            if (neighbor == node) throw std::runtime_error("self-loop");
            if (!adjacency[node].insert(neighbor).second) throw std::runtime_error("duplicate edge");
        }
        summary.directed_edges += degree;
        summary.max_degree = std::max(summary.max_degree, static_cast<std::size_t>(degree));
    }
    for (std::size_t node = 0; node < n; ++node)
        for (const auto neighbor : adjacency[node])
            if (adjacency[neighbor].count(static_cast<hnswlib::tableint>(node)))
                ++summary.reciprocal_directed_edges;
    return summary;
}

void export_fixture(const std::filesystem::path& output, const std::vector<Point>& points,
                    const hnswlib::HierarchicalNSW<float>& index,
                    const narhnsw::HnswCandidateLogger<float>& candidate_logger) {
    std::filesystem::create_directories(output);
    std::ofstream point_file(output / "points.csv");
    for (const auto& point : points) {
        for (std::size_t dimension = 0; dimension < point.size(); ++dimension) {
            if (dimension) point_file << ',';
            point_file << point[dimension];
        }
        point_file << '\n';
    }
    std::ofstream edge_file(output / "edges.csv");
    edge_file << "source,target\n";
    for (std::size_t node = 0; node < points.size(); ++node) {
        auto* raw = index.get_linklist0(static_cast<hnswlib::tableint>(node));
        const auto degree = index.getListCount(raw);
        const auto* neighbors = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
        for (std::size_t offset = 0; offset < degree; ++offset)
            edge_file << node << ',' << neighbors[offset] << '\n';
    }
    std::ofstream metadata_file(output / "metadata.txt");
    metadata_file << "entrypoint=" << index.enterpoint_node_ << '\n';
    metadata_file << "max_degree=" << index.maxM0_ << '\n';
    metadata_file << "seed=7\n";
    metadata_file << "candidate_rows=" << candidate_logger.decisions().size() << '\n';
    metadata_file << "adjacency_change_rows=" << candidate_logger.adjacency_changes().size()
                  << '\n';
    metadata_file << "candidate_logging_replays_distances=true\n";
    candidate_logger.export_csv(output, index);
}

}  // namespace

int main(int argc, char** argv) {
    constexpr std::size_t dimensions = 8;
    constexpr std::size_t n = 512;
    constexpr std::size_t queries = 32;
    constexpr std::size_t k = 10;
    constexpr std::size_t m = 16;
    std::mt19937 generator(7);
    std::normal_distribution<float> noise(0.0F, 0.45F);
    std::vector<Point> base(n, Point(dimensions));
    for (std::size_t node = 0; node < n; ++node) {
        const float center = node < n / 2 ? -2.5F : 2.5F;
        for (float& value : base[node]) value = noise(generator);
        base[node][0] += center;
    }

    CountingL2Space space(dimensions);
    hnswlib::HierarchicalNSW<float> index(&space, n, m, 100, 7);
    narhnsw::HnswCandidateLogger<float> candidate_logger;
    for (std::size_t node = 0; node < n; ++node)
        candidate_logger.add_point(index, base[node].data(), node);
    index.setEf(40);
    const GraphSummary graph = inspect_level_zero(index, n);
    const std::optional<std::filesystem::path> output =
        argc == 2 ? std::optional<std::filesystem::path>(argv[1]) : std::nullopt;
    if (output) export_fixture(*output, base, index, candidate_logger);

    double recall_sum = 0.0;
    std::vector<long> exact_distance_computations;
    std::vector<long> upstream_distance_metric;
    std::vector<long> hops;
    for (std::size_t query_id = 0; query_id < queries; ++query_id) {
        Point query = base[(query_id * 13) % n];
        for (float& value : query) value += 0.01F * noise(generator);
        const auto expected = exact_top_k(base, query, k);
        std::optional<std::set<std::size_t>> traced_reference;
        long traced_reference_ndc = 0;
        if (query_id == 0) {
            space.reset();
            const auto traced = narhnsw::HnswQueryTracer<float>::search(
                index, query.data(), k, 40, query_id);
            traced_reference_ndc = space.count();
            traced_reference = labels_from_heap(traced.results);
        }
        index.metric_distance_computations.store(0);
        index.metric_hops.store(0);
        space.reset();
        auto observed_heap = index.searchKnn(query.data(), k);
        std::set<std::size_t> observed;
        while (!observed_heap.empty()) {
            observed.insert(observed_heap.top().second);
            observed_heap.pop();
        }
        if (traced_reference &&
            (*traced_reference != observed || traced_reference_ndc != space.count()))
            throw std::runtime_error("query trace diverged from upstream searchKnn");
        std::vector<std::size_t> intersection;
        std::set_intersection(expected.begin(), expected.end(), observed.begin(), observed.end(),
                              std::back_inserter(intersection));
        recall_sum += static_cast<double>(intersection.size()) / static_cast<double>(k);
        exact_distance_computations.push_back(space.count());
        upstream_distance_metric.push_back(index.metric_distance_computations.load());
        hops.push_back(index.metric_hops.load());
    }
    const double mean_recall = recall_sum / static_cast<double>(queries);
    const double mean_exact_ndc = static_cast<double>(
                                      std::accumulate(exact_distance_computations.begin(),
                                                      exact_distance_computations.end(), 0L)) /
                                  static_cast<double>(queries);
    const double mean_upstream_ndc = static_cast<double>(
                                         std::accumulate(upstream_distance_metric.begin(),
                                                         upstream_distance_metric.end(), 0L)) /
                            static_cast<double>(queries);
    const double mean_hops =
        static_cast<double>(std::accumulate(hops.begin(), hops.end(), 0L)) /
        static_cast<double>(queries);
    std::cout << "recall_at_10=" << mean_recall << " mean_exact_ndc=" << mean_exact_ndc
              << " mean_upstream_ndc_metric=" << mean_upstream_ndc << " mean_hops=" << mean_hops
              << " directed_edges=" << graph.directed_edges
              << " reciprocal_directed_edges=" << graph.reciprocal_directed_edges
              << " max_degree=" << graph.max_degree
              << " insertion_candidate_rows=" << candidate_logger.decisions().size()
              << " insertion_adjacency_changes=" << candidate_logger.adjacency_changes().size()
              << '\n';
    if (mean_recall < 0.95 || mean_exact_ndc <= mean_upstream_ndc || mean_hops <= 0.0 ||
        graph.directed_edges == 0 || candidate_logger.decisions().empty() ||
        candidate_logger.adjacency_changes().empty())
        return 1;

    if (output) {
        constexpr std::size_t traced_queries = 256;
        const std::vector<std::size_t> traced_efs{10, 20, 40};
        std::ofstream query_file(*output / "query_points.csv");
        std::ofstream summary_file(*output / "query_trace_summary.csv");
        std::ofstream trace_file(*output / "query_trace_events.csv");
        query_file << "query_id,source_id";
        for (std::size_t dimension = 0; dimension < dimensions; ++dimension)
            query_file << ",x" << dimension;
        query_file << '\n';
        summary_file << "query_id,ef,recall,exact_ndc,upper_evaluations,base_evaluations,"
                        "base_expansions,ground_truth,observed\n";
        trace_file << "query_id,ef,event_index,phase,layer,source,target,distance_to_query,"
                      "lower_bound_before,result_size_before,event\n";
        trace_file.precision(std::numeric_limits<float>::max_digits10);
        for (std::size_t query_id = 0; query_id < traced_queries; ++query_id) {
            const std::size_t source_id = (query_id * 13) % n;
            Point query = base[source_id];
            for (float& value : query) value += 0.01F * noise(generator);
            query_file << query_id << ',' << source_id;
            for (const float value : query) query_file << ',' << value;
            query_file << '\n';
            const auto expected = exact_top_k(base, query, k);
            for (const auto ef : traced_efs) {
                space.reset();
                auto traced = narhnsw::HnswQueryTracer<float>::search(index, query.data(), k, ef,
                                                                      query_id);
                const long traced_ndc = space.count();
                const auto observed = labels_from_heap(traced.results);
                index.setEf(ef);
                space.reset();
                const auto reference = labels_from_heap(index.searchKnn(query.data(), k));
                const long reference_ndc = space.count();
                if (observed != reference || traced_ndc != reference_ndc)
                    throw std::runtime_error("query trace diverged from upstream searchKnn");
                std::vector<std::size_t> intersection;
                std::set_intersection(expected.begin(), expected.end(), observed.begin(),
                                      observed.end(), std::back_inserter(intersection));
                const double recall =
                    static_cast<double>(intersection.size()) / static_cast<double>(k);
                summary_file << query_id << ',' << ef << ',' << recall << ',' << traced_ndc << ','
                             << traced.upper_evaluations << ',' << traced.base_evaluations << ','
                             << traced.base_expansions << ",\"";
                bool first = true;
                for (const auto label : expected) {
                    if (!first) summary_file << ';';
                    summary_file << label;
                    first = false;
                }
                summary_file << "\",\"";
                first = true;
                for (const auto label : observed) {
                    if (!first) summary_file << ';';
                    summary_file << label;
                    first = false;
                }
                summary_file << "\"\n";
                for (const auto& event : traced.events)
                    trace_file << event.query_id << ',' << event.ef << ',' << event.event_index
                               << ',' << event.phase << ',' << event.layer << ',' << event.source
                               << ',' << event.target << ',' << event.distance_to_query << ','
                               << event.lower_bound_before << ',' << event.result_size_before << ','
                               << event.event << '\n';
            }
        }
    }
    return 0;
}
