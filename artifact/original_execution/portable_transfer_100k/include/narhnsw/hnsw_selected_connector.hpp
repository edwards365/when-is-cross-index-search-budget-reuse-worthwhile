#pragma once

#include "hnswlib/hnswlib.h"

#include <set>
#include <mutex>
#include <queue>
#include <stdexcept>
#include <utility>
#include <vector>

namespace narhnsw {

// Apply an externally selected neighbor set, then execute hnswlib's reciprocal
// insertion and reverse-pruning rule. This is the fixed-selection analogue of
// HierarchicalNSW::mutuallyConnectNewElement; candidate scoring remains outside
// this boundary so an audit can separate selection from graph retention.
template <typename dist_t>
void mutually_connect_selected(
    hnswlib::HierarchicalNSW<dist_t>& index, hnswlib::tableint source,
    const std::vector<hnswlib::tableint>& selected, int layer) {
    if (source >= index.cur_element_count.load())
        throw std::invalid_argument("source is outside the index");
    if (layer < 0 || layer > index.element_levels_[source])
        throw std::invalid_argument("source does not exist at the requested layer");
    if (selected.empty() || selected.size() > index.M_)
        throw std::invalid_argument("selected size must lie in [1, M]");
    if (std::set<hnswlib::tableint>(selected.begin(), selected.end()).size() !=
        selected.size())
        throw std::invalid_argument("selected neighbors must be unique");

    const std::size_t reciprocal_capacity = layer ? index.maxM_ : index.maxM0_;
    for (const auto target : selected) {
        if (target == source || target >= index.cur_element_count.load())
            throw std::invalid_argument("selected neighbor identity is invalid");
        if (layer > index.element_levels_[target])
            throw std::invalid_argument("selected neighbor does not exist at the layer");
    }

    {
        std::unique_lock<std::mutex> lock(index.link_list_locks_[source]);
        auto* raw = index.get_linklist_at_level(source, layer);
        auto* neighbors = reinterpret_cast<hnswlib::tableint*>(raw + 1);
        for (std::size_t offset = 0; offset < selected.size(); ++offset)
            neighbors[offset] = selected[offset];
        index.setListCount(raw, selected.size());
    }

    for (const auto target : selected) {
        std::unique_lock<std::mutex> lock(index.link_list_locks_[target]);
        auto* raw = index.get_linklist_at_level(target, layer);
        const std::size_t degree = index.getListCount(raw);
        if (degree > reciprocal_capacity)
            throw std::runtime_error("target degree exceeds the HNSW capacity");
        auto* neighbors = reinterpret_cast<hnswlib::tableint*>(raw + 1);
        bool already_present = false;
        for (std::size_t offset = 0; offset < degree; ++offset)
            already_present = already_present || neighbors[offset] == source;
        if (already_present) continue;

        if (degree < reciprocal_capacity) {
            neighbors[degree] = source;
            index.setListCount(raw, degree + 1);
            continue;
        }

        using Index = hnswlib::HierarchicalNSW<dist_t>;
        using Queue = std::priority_queue<
            std::pair<dist_t, hnswlib::tableint>,
            std::vector<std::pair<dist_t, hnswlib::tableint>>,
            typename Index::CompareByFirst>;
        Queue candidates;
        candidates.emplace(
            index.fstdistfunc_(index.getDataByInternalId(source),
                               index.getDataByInternalId(target), index.dist_func_param_),
            source);
        for (std::size_t offset = 0; offset < degree; ++offset) {
            candidates.emplace(
                index.fstdistfunc_(index.getDataByInternalId(neighbors[offset]),
                                   index.getDataByInternalId(target), index.dist_func_param_),
                neighbors[offset]);
        }
        index.getNeighborsByHeuristic2(candidates, reciprocal_capacity);
        std::size_t retained = 0;
        while (!candidates.empty()) {
            neighbors[retained++] = candidates.top().second;
            candidates.pop();
        }
        index.setListCount(raw, retained);
    }
}

}  // namespace narhnsw
