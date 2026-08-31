#pragma once

#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
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
struct TraceContract24 {
    std::size_t query_id{};
    std::string build_id{"UNSET"};
    std::string source_target_id{"UNSET"};
    std::size_t requested_ef{};
    std::size_t actual_expansions{};
    std::size_t actual_ndc{};
    std::uint64_t wall_clock_ns{};
    std::string upper_layer_path{"NONE"};
    std::string base_layer_expansion_order{"NONE"};
    std::string candidate_queue_insertion_order{"NONE"};
    std::string introduction_parent_edge{"NONE"};
    std::string composite_priority_key{"(distance,node_id)"};
    std::string top_candidate_heap_state{"NONE"};
    std::string lower_bound_change{"NONE"};
    std::string visited_state{"NONE"};
    std::string first_safe_discovery{"TRUTH_NOT_PROVIDED"};
    std::string endpoint_status{"NOT_EVALUATED"};
    std::string checkpoint_top_k{"NONE"};
    std::string checkpoint_candidate_set{"NONE"};
    std::string backup_path{"NOT_EVALUATED"};
    std::string edge_layer{"NONE"};
    std::string tie_event{"NONE"};
    std::string filter_deletion_state{"NO_FILTER_NO_DELETION"};
    std::string search_stop_reason{"UNSET"};
};

template <typename dist_t>
struct TraceCheckpoint {
    std::size_t expansion_count{};
    std::vector<hnswlib::tableint> top_k_internal;
    std::vector<hnswlib::tableint> candidate_set_internal;
};

template <typename dist_t>
struct TracedQueryResult {
    std::priority_queue<std::pair<dist_t, hnswlib::labeltype>> results;
    std::vector<QueryTraceEvent<dist_t>> events;
    std::size_t upper_evaluations{};
    std::size_t base_evaluations{};
    std::size_t base_expansions{};
    std::vector<TraceCheckpoint<dist_t>> checkpoints;
    TraceContract24<dist_t> contract;
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
        const auto started = std::chrono::steady_clock::now();
        if (index.cur_element_count.load() == 0) {
            TracedQueryResult<dist_t> empty;
            empty.contract.query_id = query_id;
            empty.contract.requested_ef = ef;
            empty.contract.endpoint_status = "EMPTY_INDEX";
            empty.contract.search_stop_reason = "EMPTY_INDEX";
            return empty;
        }
        TracedQueryResult<dist_t> trace;
        trace.contract.query_id = query_id;
        trace.contract.requested_ef = ef;
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
            if (candidate_distance > lower_bound) {
                trace.contract.search_stop_reason = "DISTANCE_BOUND";
                break;
            }
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
                if (neighbor_distance == lower_bound)
                    trace.contract.tie_event = "EXACT_DISTANCE_LOWER_BOUND_TIE";
                append(trace, query_id, ef, event_index, "base", 0, expanded, neighbor,
                       neighbor_distance, before, size_before, enqueued ? "enqueued" : "pruned");
                if (!enqueued) continue;
                candidate_set.emplace(-neighbor_distance, neighbor);
                top_candidates.emplace(neighbor_distance, neighbor);
                if (top_candidates.size() > search_ef) top_candidates.pop();
                if (!top_candidates.empty()) lower_bound = top_candidates.top().first;
            }
            trace.checkpoints.push_back(
                {trace.base_expansions, top_k_snapshot(top_candidates, k),
                 queue_snapshot(candidate_set)});
        }

        while (top_candidates.size() > k) top_candidates.pop();
        if (trace.contract.search_stop_reason == "UNSET")
            trace.contract.search_stop_reason = "CANDIDATE_QUEUE_EMPTY";
        while (!top_candidates.empty()) {
            const auto result = top_candidates.top();
            trace.results.emplace(result.first, index.getExternalLabel(result.second));
            top_candidates.pop();
        }
        finalize_contract(trace, started);
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

    static std::vector<hnswlib::tableint> queue_snapshot(InternalQueue queue) {
        std::vector<hnswlib::tableint> result;
        result.reserve(queue.size());
        while (!queue.empty()) {
            result.push_back(queue.top().second);
            queue.pop();
        }
        return result;
    }

    static std::vector<hnswlib::tableint> top_k_snapshot(InternalQueue queue,
                                                          std::size_t k) {
        while (queue.size() > k) queue.pop();
        return queue_snapshot(std::move(queue));
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

    static void add_token(std::string& field, const std::string& token) {
        if (field == "NONE") field.clear();
        if (!field.empty()) field.push_back('|');
        field += token;
    }

    static void finalize_contract(TracedQueryResult<dist_t>& trace,
                                  std::chrono::steady_clock::time_point started) {
        trace.contract.actual_expansions = trace.base_expansions;
        trace.contract.actual_ndc = trace.upper_evaluations + trace.base_evaluations + 2;
        trace.contract.wall_clock_ns = static_cast<std::uint64_t>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now() - started).count());
        for (const auto& e : trace.events) {
            const std::string edge = std::to_string(e.source) + ">" + std::to_string(e.target);
            if (e.phase == "upper" && (e.event == "entry" || e.event == "improved"))
                add_token(trace.contract.upper_layer_path, std::to_string(e.target));
            if (e.phase == "base" && e.event == "expanded")
                add_token(trace.contract.base_layer_expansion_order, std::to_string(e.target));
            if (e.phase == "base" && e.event == "enqueued") {
                add_token(trace.contract.candidate_queue_insertion_order, std::to_string(e.target));
                if (trace.contract.introduction_parent_edge == "NONE")
                    trace.contract.introduction_parent_edge = edge;
            }
            if (e.phase == "base") add_token(trace.contract.edge_layer, "0");
            add_token(trace.contract.lower_bound_change, std::to_string(e.lower_bound_before));
            add_token(trace.contract.visited_state, std::to_string(e.target));
            add_token(trace.contract.top_candidate_heap_state,
                      std::to_string(e.result_size_before));
        }
        trace.contract.checkpoint_candidate_set = trace.contract.candidate_queue_insertion_order;
        trace.contract.checkpoint_top_k = "FINAL_TOP_K_AVAILABLE_IN_RESULTS";
        trace.contract.endpoint_status = "SEARCH_COMPLETED_TRUTH_NOT_EVALUATED";
    }
};

}  // namespace narhnsw
