#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_candidate_logger.hpp"
#include "narhnsw/hnsw_selected_connector.hpp"

#include <array>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <vector>

namespace {

using Index = hnswlib::HierarchicalNSW<float>;

std::set<hnswlib::tableint> neighbors(const Index& index, hnswlib::tableint node) {
    auto* raw = index.get_linklist0(node);
    const auto degree = index.getListCount(raw);
    const auto* ids = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
    return {ids, ids + degree};
}

std::set<hnswlib::tableint> neighbors(const Index& index, hnswlib::tableint node, int layer) {
    auto* raw = index.get_linklist_at_level(node, layer);
    const auto degree = index.getListCount(raw);
    const auto* ids = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
    return {ids, ids + degree};
}

using LayerSnapshot = std::map<std::pair<hnswlib::tableint, int>, std::set<hnswlib::tableint>>;

LayerSnapshot upper_layers(const Index& index, std::size_t count) {
    LayerSnapshot result;
    for (std::size_t node = 0; node < count; ++node) {
        for (int layer = 1; layer <= index.element_levels_[node]; ++layer) {
            result[{static_cast<hnswlib::tableint>(node), layer}] =
                neighbors(index, static_cast<hnswlib::tableint>(node), layer);
        }
    }
    return result;
}

void test_single_external_selection() {
    constexpr std::size_t count = 96;
    constexpr std::size_t dimensions = 3;
    constexpr std::size_t m = 8;
    hnswlib::L2Space space(dimensions);
    Index index(&space, count, m, 80, 7);
    std::vector<std::array<float, dimensions>> points(count);
    for (std::size_t node = 0; node < count; ++node) {
        points[node] = {static_cast<float>(node % 12), static_cast<float>(node / 12),
                        static_cast<float>((node * 7) % 11)};
        index.addPoint(points[node].data(), node);
    }

    const hnswlib::tableint source = 95;
    const auto original = neighbors(index, source);
    if (original.empty()) throw std::runtime_error("fixture source has no neighbors");
    hnswlib::tableint incoming = 0;
    while (incoming == source || original.count(incoming)) ++incoming;
    std::vector<hnswlib::tableint> selected(original.begin(), original.end());
    selected.back() = incoming;
    const std::set<hnswlib::tableint> expected(selected.begin(), selected.end());

    narhnsw::mutually_connect_selected(index, source, selected, 0);
    if (neighbors(index, source) != expected)
        throw std::runtime_error("external selection was not written exactly");
    for (std::size_t node = 0; node < count; ++node) {
        const auto observed = neighbors(index, static_cast<hnswlib::tableint>(node));
        if (observed.size() > index.maxM0_)
            throw std::runtime_error("reciprocal insertion exceeded the degree cap");
        if (observed.count(static_cast<hnswlib::tableint>(node)))
            throw std::runtime_error("connector introduced a self-loop");
    }

    const bool reciprocal_retained = neighbors(index, incoming).count(source) != 0;
    std::cout << "single_selected=" << selected.size()
              << " reciprocal_retained=" << reciprocal_retained << '\n';
}

void test_complete_original_replay() {
    constexpr std::size_t count = 384;
    constexpr std::size_t dimensions = 5;
    constexpr std::size_t m = 8;
    constexpr std::size_t ef_construction = 80;
    constexpr std::size_t seed = 17;
    hnswlib::L2Space original_space(dimensions);
    hnswlib::L2Space replay_space(dimensions);
    Index original(&original_space, count, m, ef_construction, seed);
    Index replay(&replay_space, count, m, ef_construction, seed);
    narhnsw::HnswCandidateLogger<float> logger;
    std::vector<std::array<float, dimensions>> points(count);
    for (std::size_t node = 0; node < count; ++node) {
        points[node] = {static_cast<float>((node * 17) % 101),
                        static_cast<float>((node * 29) % 103),
                        static_cast<float>((node * 43) % 107),
                        static_cast<float>((node * 61) % 109),
                        static_cast<float>((node * 73) % 113)};
        logger.add_point(original, points[node].data(), node);
        replay.addPoint(points[node].data(), node);
    }

    const auto upper_before = upper_layers(replay, count);
    for (std::size_t node = 0; node < count; ++node)
        replay.setListCount(replay.get_linklist0(static_cast<hnswlib::tableint>(node)), 0);

    std::map<hnswlib::tableint, std::vector<hnswlib::tableint>> plan;
    for (const auto& row : logger.decisions()) {
        if (row.layer == 0 && row.decision == narhnsw::CandidateDecision::accepted)
            plan[row.insertion_id].push_back(row.candidate_id);
    }
    for (const auto& [source, selected] : plan)
        narhnsw::mutually_connect_selected(replay, source, selected, 0);

    for (std::size_t node = 0; node < count; ++node) {
        const auto internal = static_cast<hnswlib::tableint>(node);
        if (neighbors(original, internal) != neighbors(replay, internal))
            throw std::runtime_error("Algorithm-4 replay did not reproduce final layer 0");
    }
    if (upper_before != upper_layers(replay, count))
        throw std::runtime_error("layer-0 replay modified an upper layer");
    std::cout << "complete_original_replay_points=" << count
              << " upper_layer_records=" << upper_before.size() << '\n';
}

}  // namespace

int main() {
    test_single_external_selection();
    test_complete_original_replay();
    return 0;
}
