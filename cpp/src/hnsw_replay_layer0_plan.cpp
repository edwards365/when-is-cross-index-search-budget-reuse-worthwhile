#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_selected_connector.hpp"

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <numeric>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using Index = hnswlib::HierarchicalNSW<float>;
using Plan = std::map<hnswlib::tableint, std::vector<hnswlib::tableint>>;

std::size_t parse_size(const char* raw, const char* name) {
    const auto value = std::stoull(raw);
    if (value == 0) throw std::invalid_argument(std::string(name) + " must be positive");
    return value;
}

std::vector<float> load_points(const std::filesystem::path& path, std::size_t points,
                               std::size_t dimensions) {
    const auto expected = points * dimensions;
    std::vector<float> values(expected);
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot open input fbin");
    input.read(reinterpret_cast<char*>(values.data()),
               static_cast<std::streamsize>(expected * sizeof(float)));
    if (input.gcount() != static_cast<std::streamsize>(expected * sizeof(float)))
        throw std::runtime_error("input fbin is shorter than declared shape");
    char extra{};
    if (input.read(&extra, 1)) throw std::runtime_error("input fbin is longer than declared shape");
    return values;
}

Plan read_plan(const std::filesystem::path& path, std::size_t points, std::size_t m) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open selection plan");
    Plan plan;
    std::string line;
    while (std::getline(input, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line == "source,target") continue;
        const auto comma = line.find(',');
        if (comma == std::string::npos) throw std::runtime_error("invalid selection-plan row");
        const auto source = static_cast<hnswlib::tableint>(std::stoul(line.substr(0, comma)));
        const auto target = static_cast<hnswlib::tableint>(std::stoul(line.substr(comma + 1)));
        if (source == 0 || source >= points || target >= source)
            throw std::invalid_argument("plan endpoints violate insertion order");
        plan[source].push_back(target);
    }
    if (plan.size() != points - 1)
        throw std::invalid_argument("selection plan must cover every noninitial insertion");
    for (std::size_t source = 1; source < points; ++source) {
        const auto found = plan.find(static_cast<hnswlib::tableint>(source));
        if (found == plan.end() || found->second.empty() || found->second.size() > m)
            throw std::invalid_argument("selection count is outside [1, M]");
        if (std::set<hnswlib::tableint>(found->second.begin(), found->second.end()).size() !=
            found->second.size())
            throw std::invalid_argument("selection plan contains a duplicate target");
    }
    return plan;
}

std::vector<hnswlib::tableint> neighbors(const Index& index, hnswlib::tableint node,
                                         int layer) {
    auto* raw = index.get_linklist_at_level(node, layer);
    const auto degree = index.getListCount(raw);
    const auto* ids = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
    return {ids, ids + degree};
}

void hash_value(std::uint64_t& hash, std::uint64_t value) {
    constexpr std::uint64_t prime = 1099511628211ULL;
    for (int byte = 0; byte < 8; ++byte) {
        hash ^= (value >> (byte * 8)) & 0xffU;
        hash *= prime;
    }
}

std::uint64_t upper_checksum(const Index& index, std::size_t points) {
    std::uint64_t hash = 1469598103934665603ULL;
    for (std::size_t node = 0; node < points; ++node) {
        hash_value(hash, node);
        hash_value(hash, static_cast<std::uint64_t>(index.element_levels_[node]));
        for (int layer = 1; layer <= index.element_levels_[node]; ++layer) {
            hash_value(hash, static_cast<std::uint64_t>(layer));
            const auto adjacent = neighbors(index, static_cast<hnswlib::tableint>(node), layer);
            hash_value(hash, adjacent.size());
            for (const auto target : adjacent) hash_value(hash, target);
        }
    }
    return hash;
}

std::size_t validate_and_export(const Index& index, std::size_t points,
                                const std::filesystem::path& path) {
    std::ofstream output(path);
    if (!output) throw std::runtime_error("cannot create layer-0 edge output");
    output << "source,target\n";
    std::size_t edges = 0;
    for (std::size_t source = 0; source < points; ++source) {
        const auto internal = static_cast<hnswlib::tableint>(source);
        const auto adjacent = neighbors(index, internal, 0);
        if (adjacent.size() > index.maxM0_)
            throw std::runtime_error("layer-0 degree exceeds maxM0");
        const std::set<hnswlib::tableint> unique(adjacent.begin(), adjacent.end());
        if (unique.size() != adjacent.size() || unique.count(internal))
            throw std::runtime_error("layer-0 graph contains a duplicate or self-edge");
        for (const auto target : adjacent) {
            if (target >= points) throw std::runtime_error("layer-0 endpoint is out of range");
            output << source << ',' << target << '\n';
            ++edges;
        }
    }
    return edges;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 10) {
            std::cerr << "usage: hnsw_replay_layer0_plan INPUT.fbin POINTS DIMENSIONS SEED M "
                         "EF_CONSTRUCTION METRIC PLAN.csv OUTPUT_DIR\n";
            return 2;
        }
        const std::filesystem::path input_path = argv[1];
        const auto points = parse_size(argv[2], "points");
        const auto dimensions = parse_size(argv[3], "dimensions");
        const auto seed = parse_size(argv[4], "seed");
        const auto m = parse_size(argv[5], "M");
        const auto ef_construction = parse_size(argv[6], "ef_construction");
        const std::string metric = argv[7];
        const std::filesystem::path plan_path = argv[8];
        const std::filesystem::path output = argv[9];
        if (metric != "l2" && metric != "ip")
            throw std::invalid_argument("metric must be l2 or ip");
        if (std::filesystem::exists(output))
            throw std::runtime_error("output directory already exists");

        const auto values = load_points(input_path, points, dimensions);
        const auto plan = read_plan(plan_path, points, m);
        std::unique_ptr<hnswlib::SpaceInterface<float>> space;
        if (metric == "l2")
            space = std::make_unique<hnswlib::L2Space>(dimensions);
        else
            space = std::make_unique<hnswlib::InnerProductSpace>(dimensions);
        Index index(space.get(), points, m, ef_construction, seed);
        std::vector<std::size_t> order(points);
        std::iota(order.begin(), order.end(), 0);
        std::mt19937 generator(static_cast<std::uint32_t>(seed));
        std::shuffle(order.begin(), order.end(), generator);
        for (const auto label : order)
            index.addPoint(values.data() + label * dimensions, label);

        const auto upper_before = upper_checksum(index, points);
        for (std::size_t node = 0; node < points; ++node)
            index.setListCount(index.get_linklist0(static_cast<hnswlib::tableint>(node)), 0);
        std::size_t planned_source_edges = 0;
        std::size_t source_edges_retained_immediately = 0;
        std::size_t reciprocal_edges_retained_immediately = 0;
        for (const auto& [source, selected] : plan) {
            narhnsw::mutually_connect_selected(index, source, selected, 0);
            const auto source_adjacent = neighbors(index, source, 0);
            const std::set<hnswlib::tableint> source_neighbors(source_adjacent.begin(),
                                                                source_adjacent.end());
            planned_source_edges += selected.size();
            for (const auto target : selected) {
                source_edges_retained_immediately += source_neighbors.count(target);
                const auto target_neighbors = neighbors(index, target, 0);
                reciprocal_edges_retained_immediately +=
                    std::find(target_neighbors.begin(), target_neighbors.end(), source) !=
                    target_neighbors.end();
            }
        }
        const auto upper_after = upper_checksum(index, points);
        if (upper_before != upper_after)
            throw std::runtime_error("layer-0 replay changed an upper layer");

        std::filesystem::create_directories(output);
        const auto edges = validate_and_export(index, points, output / "layer0_edges.csv");
        index.saveIndex((output / "index.bin").string());
        std::ofstream mapping(output / "internal_to_external.csv");
        mapping << "internal_id,external_label\n";
        for (std::size_t internal = 0; internal < points; ++internal)
            mapping << internal << ',' << index.getExternalLabel(internal) << '\n';
        std::ofstream metadata(output / "metadata.json");
        metadata << "{\n"
                 << "  \"status\": \"complete\",\n"
                 << "  \"points\": " << points << ",\n"
                 << "  \"directed_layer0_edges\": " << edges << ",\n"
                 << "  \"planned_source_edges\": " << planned_source_edges << ",\n"
                 << "  \"source_edges_retained_immediately\": "
                 << source_edges_retained_immediately << ",\n"
                 << "  \"reciprocal_edges_retained_immediately\": "
                 << reciprocal_edges_retained_immediately << ",\n"
                 << "  \"upper_checksum_before\": " << upper_before << ",\n"
                 << "  \"upper_checksum_after\": " << upper_after << ",\n"
                 << "  \"upper_checksum_equal\": true,\n"
                 << "  \"formal_test_members_accessed\": false\n"
                 << "}\n";
        std::cout << "points=" << points << " directed_layer0_edges=" << edges
                  << " upper_checksum=" << upper_after << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
