#pragma once

#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <limits>
#include <optional>
#include <queue>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace narhnsw {

enum class CandidateDecision { accepted, occluded, budget_exhausted };

inline const char* decision_name(CandidateDecision decision) {
    switch (decision) {
        case CandidateDecision::accepted:
            return "accepted";
        case CandidateDecision::occluded:
            return "occluded";
        case CandidateDecision::budget_exhausted:
            return "budget_exhausted";
    }
    throw std::runtime_error("unknown candidate decision");
}

template <typename dist_t>
struct CandidateDecisionRow {
    hnswlib::tableint insertion_id{};
    int layer{};
    hnswlib::tableint candidate_id{};
    dist_t distance_to_new{};
    CandidateDecision decision{CandidateDecision::accepted};
    std::optional<hnswlib::tableint> blocker_id;
    bool new_to_candidate_after{false};
    bool candidate_to_new_after{false};
};

struct AdjacencyChangeRow {
    hnswlib::tableint insertion_id{};
    int layer{};
    hnswlib::tableint source{};
    hnswlib::tableint target{};
    std::string action;
};

template <typename dist_t>
class HnswCandidateLogger {
   public:
    using Index = hnswlib::HierarchicalNSW<dist_t>;
    using Queue = std::priority_queue<std::pair<dist_t, hnswlib::tableint>,
                                      std::vector<std::pair<dist_t, hnswlib::tableint>>,
                                      typename Index::CompareByFirst>;

    hnswlib::tableint add_point(Index& index, const void* data_point, hnswlib::labeltype label) {
        const auto insertion_id = static_cast<hnswlib::tableint>(index.cur_element_count.load());
        const int predicted_level = predict_next_level(index);
        const auto layer_traces = replay_insertion(index, data_point, insertion_id, predicted_level);

        std::vector<NeighborSnapshot> before;
        for (const auto& trace : layer_traces) {
            for (const auto selected : trace.selected) {
                before.push_back(
                    {trace.layer, selected, connection_set(index, selected, trace.layer)});
            }
        }

        const auto observed_id = index.addPoint(data_point, label, -1);
        if (observed_id != insertion_id || index.element_levels_[observed_id] != predicted_level) {
            throw std::runtime_error("candidate replay diverged from HNSW insertion identity/level");
        }

        for (const auto& trace : layer_traces) {
            const auto actual = connection_set(index, observed_id, trace.layer);
            const std::set<hnswlib::tableint> expected(trace.selected.begin(), trace.selected.end());
            if (actual != expected) {
                throw std::runtime_error("candidate replay diverged from HNSW selected neighbors");
            }
        }

        for (auto trace : layer_traces) {
            const auto new_neighbors = connection_set(index, observed_id, trace.layer);
            for (auto& row : trace.rows) {
                row.new_to_candidate_after = new_neighbors.count(row.candidate_id) != 0;
                if (trace.layer <= index.element_levels_[row.candidate_id]) {
                    row.candidate_to_new_after =
                        connection_set(index, row.candidate_id, trace.layer).count(observed_id) != 0;
                }
                decisions_.push_back(row);
            }
        }

        for (const auto& snapshot : before) {
            const auto after = connection_set(index, snapshot.node, snapshot.layer);
            append_changes(insertion_id, snapshot.layer, snapshot.node, snapshot.neighbors, after);
        }
        return observed_id;
    }

    const std::vector<CandidateDecisionRow<dist_t>>& decisions() const { return decisions_; }
    const std::vector<AdjacencyChangeRow>& adjacency_changes() const { return adjacency_changes_; }

    void export_csv(const std::filesystem::path& output, const Index& final_index) const {
        std::filesystem::create_directories(output);
        std::ofstream decisions_file(output / "insertion_candidates.csv");
        if (!decisions_file) throw std::runtime_error("cannot create insertion candidate log");
        decisions_file << "insertion_id,layer,candidate_id,distance_to_new,decision,blocker_id,"
                          "new_to_candidate_after,candidate_to_new_after,new_to_candidate_final,"
                          "candidate_to_new_final\n";
        decisions_file.precision(std::numeric_limits<dist_t>::max_digits10);
        for (const auto& row : decisions_) {
            const bool new_to_candidate_final =
                has_connection(final_index, row.insertion_id, row.candidate_id, row.layer);
            const bool candidate_to_new_final =
                has_connection(final_index, row.candidate_id, row.insertion_id, row.layer);
            decisions_file << row.insertion_id << ',' << row.layer << ',' << row.candidate_id << ','
                           << row.distance_to_new << ',' << decision_name(row.decision) << ',';
            if (row.blocker_id) decisions_file << *row.blocker_id;
            decisions_file << ',' << row.new_to_candidate_after << ','
                           << row.candidate_to_new_after << ',' << new_to_candidate_final << ','
                           << candidate_to_new_final << '\n';
        }

        std::ofstream changes_file(output / "insertion_adjacency_changes.csv");
        if (!changes_file) throw std::runtime_error("cannot create insertion adjacency-change log");
        changes_file << "insertion_id,layer,source,target,action\n";
        for (const auto& row : adjacency_changes_) {
            changes_file << row.insertion_id << ',' << row.layer << ',' << row.source << ','
                         << row.target << ',' << row.action << '\n';
        }
    }

   private:
    struct LayerTrace {
        int layer{};
        std::vector<hnswlib::tableint> selected;
        std::vector<CandidateDecisionRow<dist_t>> rows;
        std::optional<hnswlib::tableint> next_closest;
    };

    struct NeighborSnapshot {
        int layer{};
        hnswlib::tableint node{};
        std::set<hnswlib::tableint> neighbors;
    };

    static int predict_next_level(const Index& index) {
        auto generator = index.level_generator_;
        std::uniform_real_distribution<double> distribution(0.0, 1.0);
        return static_cast<int>(-std::log(distribution(generator)) * index.mult_);
    }

    static std::vector<hnswlib::tableint> connections(const Index& index,
                                                       hnswlib::tableint node, int layer) {
        if (node >= index.cur_element_count.load() || layer > index.element_levels_[node]) return {};
        auto* raw = index.get_linklist_at_level(node, layer);
        const auto degree = index.getListCount(raw);
        const auto* neighbors = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
        return {neighbors, neighbors + degree};
    }

    static std::set<hnswlib::tableint> connection_set(const Index& index,
                                                       hnswlib::tableint node, int layer) {
        const auto ordered = connections(index, node, layer);
        return {ordered.begin(), ordered.end()};
    }

    static bool has_connection(const Index& index, hnswlib::tableint source,
                               hnswlib::tableint target, int layer) {
        return connection_set(index, source, layer).count(target) != 0;
    }

    static LayerTrace trace_heuristic(Index& index, Queue candidates,
                                      hnswlib::tableint insertion_id, int layer) {
        LayerTrace trace;
        trace.layer = layer;
        if (candidates.size() < index.M_) {
            while (!candidates.empty()) {
                const auto [distance, candidate] = candidates.top();
                candidates.pop();
                trace.next_closest = candidate;
                trace.selected.push_back(candidate);
                trace.rows.push_back({insertion_id, layer, candidate, distance,
                                      CandidateDecision::accepted, std::nullopt});
            }
            return trace;
        }

        std::priority_queue<std::pair<dist_t, hnswlib::tableint>> closest;
        while (!candidates.empty()) {
            closest.emplace(-candidates.top().first, candidates.top().second);
            candidates.pop();
        }
        while (!closest.empty()) {
            const auto [negative_distance, candidate] = closest.top();
            closest.pop();
            const dist_t distance = -negative_distance;
            if (trace.selected.size() >= index.M_) {
                trace.rows.push_back({insertion_id, layer, candidate, distance,
                                      CandidateDecision::budget_exhausted, std::nullopt});
                continue;
            }
            std::optional<hnswlib::tableint> blocker;
            for (const auto selected : trace.selected) {
                const dist_t interdistance = index.fstdistfunc_(
                    index.getDataByInternalId(selected), index.getDataByInternalId(candidate),
                    index.dist_func_param_);
                if (interdistance < distance) {
                    blocker = selected;
                    break;
                }
            }
            if (blocker) {
                trace.rows.push_back({insertion_id, layer, candidate, distance,
                                      CandidateDecision::occluded, blocker});
            } else {
                trace.selected.push_back(candidate);
                trace.rows.push_back({insertion_id, layer, candidate, distance,
                                      CandidateDecision::accepted, std::nullopt});
            }
        }
        Queue selected_queue;
        for (const auto& row : trace.rows) {
            if (row.decision == CandidateDecision::accepted)
                selected_queue.emplace(row.distance_to_new, row.candidate_id);
        }
        while (!selected_queue.empty()) {
            trace.next_closest = selected_queue.top().second;
            selected_queue.pop();
        }
        return trace;
    }

    static std::vector<LayerTrace> replay_insertion(Index& index, const void* data_point,
                                                     hnswlib::tableint insertion_id,
                                                     int predicted_level) {
        std::vector<LayerTrace> traces;
        if (index.cur_element_count.load() == 0) return traces;
        hnswlib::tableint current = index.enterpoint_node_;
        const int old_max_level = index.maxlevel_;
        if (predicted_level < old_max_level) {
            dist_t current_distance = index.fstdistfunc_(
                data_point, index.getDataByInternalId(current), index.dist_func_param_);
            for (int layer = old_max_level; layer > predicted_level; --layer) {
                bool changed = true;
                while (changed) {
                    changed = false;
                    for (const auto candidate : connections(index, current, layer)) {
                        const dist_t distance = index.fstdistfunc_(
                            data_point, index.getDataByInternalId(candidate), index.dist_func_param_);
                        if (distance < current_distance) {
                            current_distance = distance;
                            current = candidate;
                            changed = true;
                        }
                    }
                }
            }
        }
        for (int layer = std::min(predicted_level, old_max_level); layer >= 0; --layer) {
            auto candidates = index.searchBaseLayer(current, data_point, layer);
            auto trace = trace_heuristic(index, std::move(candidates), insertion_id, layer);
            if (trace.selected.empty() || !trace.next_closest) {
                throw std::runtime_error("HNSW replay produced an empty candidate selection");
            }
            current = *trace.next_closest;
            traces.push_back(std::move(trace));
        }
        return traces;
    }

    void append_changes(hnswlib::tableint insertion_id, int layer,
                        hnswlib::tableint source,
                        const std::set<hnswlib::tableint>& before,
                        const std::set<hnswlib::tableint>& after) {
        for (const auto target : before) {
            if (!after.count(target))
                adjacency_changes_.push_back({insertion_id, layer, source, target, "removed"});
        }
        for (const auto target : after) {
            if (!before.count(target))
                adjacency_changes_.push_back({insertion_id, layer, source, target, "added"});
        }
    }

    std::vector<CandidateDecisionRow<dist_t>> decisions_;
    std::vector<AdjacencyChangeRow> adjacency_changes_;
};

}  // namespace narhnsw
