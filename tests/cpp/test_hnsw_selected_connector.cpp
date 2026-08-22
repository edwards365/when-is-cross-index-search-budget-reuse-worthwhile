#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_selected_connector.hpp"

#include <array>
#include <iostream>
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

}  // namespace

int main() {
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
    std::cout << "selected=" << selected.size()
              << " reciprocal_retained=" << reciprocal_retained << '\n';
    return 0;
}
