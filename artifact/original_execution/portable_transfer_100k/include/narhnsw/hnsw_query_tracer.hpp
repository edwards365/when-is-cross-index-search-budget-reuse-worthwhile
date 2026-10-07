#pragma once

#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <cstddef>
#include <limits>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace narhnsw {

template <typename dist_t>
struct QueryTraceEvent {
    std::size_t query_id{};
    std::size_t ef{};
    std::size_t event_index{};
    std::string phase;
    int layer{};
    hnswlib::tableint source{};
    hnswlib::tableint target{};
    dist_t distance_to_query{};
    dist_t lower_bound_before{};
    std::size_t result_size_before{};
    std::string event;
};

template <typename dist_t>
struct TracedQueryResult {
    std::priority_queue<std::pair<dist_t, hnswlib::labeltype>> results;
    std::vector<QueryTraceEvent<dist_t>> events;
    std::size_t upper_evaluations{};
    std::size_t base_evaluations{};
    std::size_t base_expansions{};
};

template <typename dist_t>
class HnswQueryTracer {
   public:
    using Index = hnswlib::HierarchicalNSW<dist_t>;
    using InternalQueue =
        std::priority_queue<std::pair<dist_t, hnswlib::tableint>,
                            std::vector<std::pair<dist_t, hnswlib::tableint>>,
                            typename Index::CompareByFirst>;

    static TracedQueryResult<dist_t> search(const Index& index, const void* query_data,
                                             std::size_t k, std::size_t ef,
                                             std::size_t query_id) {
        if (index.cur_element_count.load() == 0) return {};
        TracedQueryResult<dist_t> trace;
        std::size_t event_index = 0;
        hnswlib::tableint current = index.enterpoint_node_;
        dist_t current_distance = distance(index, query_data, current);
        append(trace, query_id, ef, event_index, "upper", index.maxlevel_, current, current,
               current_distance, current_distance, 1, "entry");

        for (int layer = index.maxlevel_; layer > 0; --layer) {
            bool changed = true;
            while (changed) {
                changed = false;
                const auto neighbors = connections(index, current, layer);
                for (const auto candidate : neighbors) {
                    const dist_t before = current_distance;
                    const dist_t candidate_distance = distance(index, query_data, candidate);
                    ++trace.upper_evaluations;
                    const bool improved = candidate_distance < current_distance;
                    append(trace, query_id, ef, event_index, "upper", layer, current, candidate,
                           candidate_distance, before, 1, improved ? "improved" : "evaluated");
                    if (improved) {
                        current_distance = candidate_distance;
                        current = candidate;
                        changed = true;
                    }
                }
            }
        }

        InternalQueue top_candidates;
        InternalQueue candidate_set;
        const dist_t entry_distance = distance(index, query_data, current);
        dist_t lower_bound = entry_distance;
        top_candidates.emplace(entry_distance, current);
        candidate_set.emplace(-entry_distance, current);
        std::vector<bool> visited(index.cur_element_count.load(), false);
        visited[current] = true;
        append(trace, query_id, ef, event_index, "base", 0, current, current, entry_distance,
               lower_bound, top_candidates.size(), "entry");

        const std::size_t search_ef = std::max(ef, k);
        while (!candidate_set.empty()) {
            const auto current_pair = candidate_set.top();
            const dist_t candidate_distance = -current_pair.first;
            if (candidate_distance > lower_bound) break;
            candidate_set.pop();
            const auto expanded = current_pair.second;
            append(trace, query_id, ef, event_index, "base", 0, expanded, expanded,
                   candidate_distance, lower_bound, top_candidates.size(), "expanded");
            ++trace.base_expansions;
            for (const auto neighbor : connections(index, expanded, 0)) {
                if (visited[neighbor]) continue;
                visited[neighbor] = true;
                const dist_t before = lower_bound;
                const std::size_t size_before = top_candidates.size();
                const dist_t neighbor_distance = distance(index, query_data, neighbor);
                ++trace.base_evaluations;
                const bool enqueued =
                    top_candidates.size() < search_ef || lower_bound > neighbor_distance;
                append(trace, query_id, ef, event_index, "base", 0, expanded, neighbor,
                       neighbor_distance, before, size_before, enqueued ? "enqueued" : "pruned");
                if (!enqueued) continue;
                candidate_set.emplace(-neighbor_distance, neighbor);
                top_candidates.emplace(neighbor_distance, neighbor);
                if (top_candidates.size() > search_ef) top_candidates.pop();
                if (!top_candidates.empty()) lower_bound = top_candidates.top().first;
            }
        }

        while (top_candidates.size() > k) top_candidates.pop();
        while (!top_candidates.empty()) {
            const auto result = top_candidates.top();
            trace.results.emplace(result.first, index.getExternalLabel(result.second));
            top_candidates.pop();
        }
        return trace;
    }

   private:
    static dist_t distance(const Index& index, const void* query_data,
                           hnswlib::tableint node) {
        return index.fstdistfunc_(query_data, index.getDataByInternalId(node),
                                 index.dist_func_param_);
    }

    static std::vector<hnswlib::tableint> connections(const Index& index,
                                                       hnswlib::tableint node, int layer) {
        auto* raw = index.get_linklist_at_level(node, layer);
        const auto degree = index.getListCount(raw);
        const auto* neighbors = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
        return {neighbors, neighbors + degree};
    }

    static void append(TracedQueryResult<dist_t>& trace, std::size_t query_id,
                       std::size_t ef, std::size_t& event_index, std::string phase, int layer,
                       hnswlib::tableint source, hnswlib::tableint target,
                       dist_t distance_to_query, dist_t lower_bound_before,
                       std::size_t result_size_before, std::string event) {
        trace.events.push_back({query_id, ef, event_index++, std::move(phase), layer, source,
                                target, distance_to_query, lower_bound_before,
                                result_size_before, std::move(event)});
    }
};

}  // namespace narhnsw
