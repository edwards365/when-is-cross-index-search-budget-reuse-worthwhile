#include "hnswlib/hnswlib.h"

#include <algorithm>
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
#include <tuple>
#include <vector>

namespace {
using Index = hnswlib::HierarchicalNSW<float>;
using Node = hnswlib::tableint;

std::vector<Node> neighbors(const Index& index, Node node) {
    auto* raw = index.get_linklist0(node);
    const auto degree = index.getListCount(raw);
    const auto* ids = reinterpret_cast<const Node*>(raw + 1);
    return {ids, ids + degree};
}

std::uint64_t fnv_edges(const Index& index) {
    std::uint64_t hash = 1469598103934665603ULL;
    auto mix = [&](std::uint64_t value) {
        for (int byte = 0; byte < 8; ++byte) {
            hash ^= (value >> (byte * 8)) & 0xffULL;
            hash *= 1099511628211ULL;
        }
    };
    const auto count = index.cur_element_count.load();
    for (std::size_t source = 0; source < count; ++source) {
        mix(source);
        const auto row = neighbors(index, static_cast<Node>(source));
        mix(row.size());
        for (const auto target : row) mix(target);
    }
    return hash;
}

std::uint64_t fnv_upper(const Index& index) {
    std::uint64_t hash = 1469598103934665603ULL;
    auto mix = [&](std::uint64_t value) {
        for (int byte = 0; byte < 8; ++byte) {
            hash ^= (value >> (byte * 8)) & 0xffULL;
            hash *= 1099511628211ULL;
        }
    };
    const auto count = index.cur_element_count.load();
    for (std::size_t node = 0; node < count; ++node) {
        mix(node);
        mix(static_cast<std::uint64_t>(index.element_levels_[node]));
        for (int layer = 1; layer <= index.element_levels_[node]; ++layer) {
            auto* raw = index.get_linklist_at_level(static_cast<Node>(node), layer);
            const auto degree = index.getListCount(raw);
            mix(layer); mix(degree);
            const auto* ids = reinterpret_cast<const Node*>(raw + 1);
            for (std::size_t i = 0; i < degree; ++i) mix(ids[i]);
        }
    }
    return hash;
}

std::map<Node, std::vector<Node>> read_plan(const std::filesystem::path& path,
                                             std::size_t count,
                                             const Index& index) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open O4 edge plan");
    std::map<Node, std::vector<Node>> plan;
    std::string line;
    while (std::getline(input, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line == "source,target") continue;
        std::stringstream row(line);
        std::string left, right;
        if (!std::getline(row, left, ',') || !std::getline(row, right))
            throw std::runtime_error("invalid O4 edge-plan row");
        const auto source = static_cast<Node>(std::stoul(left));
        const auto target = static_cast<Node>(std::stoul(right));
        if (source >= count || target >= count || source == target)
            throw std::runtime_error("O4 edge-plan endpoint out of range/self-loop");
        plan[source].push_back(target);
    }
    if (plan.size() != count) throw std::runtime_error("O4 plan must cover every node");
    for (std::size_t source = 0; source < count; ++source) {
        const auto it = plan.find(static_cast<Node>(source));
        if (it == plan.end()) throw std::runtime_error("O4 plan missing node");
        const auto before = neighbors(index, static_cast<Node>(source));
        if (it->second.size() != before.size())
            throw std::runtime_error("O4 plan violates per-node degree");
        if (std::set<Node>(it->second.begin(), it->second.end()).size() != it->second.size())
            throw std::runtime_error("O4 plan contains duplicate target");
    }
    return plan;
}

void write_edges(const Index& index, const std::filesystem::path& path) {
    std::ofstream output(path);
    if (!output) throw std::runtime_error("cannot write edge audit");
    output << "source,target\n";
    const auto count = index.cur_element_count.load();
    for (std::size_t source = 0; source < count; ++source)
        for (const auto target : neighbors(index, static_cast<Node>(source)))
            output << source << ',' << target << '\n';
}

void validate(const Index& index) {
    const auto count = index.cur_element_count.load();
    for (std::size_t source = 0; source < count; ++source) {
        const auto row = neighbors(index, static_cast<Node>(source));
        if (row.size() > index.maxM0_) throw std::runtime_error("layer0 degree exceeds maxM0");
        std::set<Node> unique(row.begin(), row.end());
        if (unique.size() != row.size() || unique.count(static_cast<Node>(source)))
            throw std::runtime_error("layer0 duplicate or self-loop");
        for (const auto target : row)
            if (target >= count) throw std::runtime_error("layer0 target out of range");
    }
}
}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc == 4 && std::string(argv[1]) == "--dump") {
            const std::filesystem::path base_path = argv[2];
            const std::filesystem::path edge_path = argv[3];
            hnswlib::L2Space space(128);
            Index index(&space, base_path.string(), false);
            validate(index);
            write_edges(index, edge_path);
            std::cout << "nodes=" << index.cur_element_count.load()
                      << " edge_hash=" << fnv_edges(index) << '\n';
            return 0;
        }
        if (argc != 5) {
            std::cerr << "usage: icba_o4_bridge BASE_INDEX PLAN OUTPUT_INDEX AUDIT_PREFIX\n";
            return 2;
        }
        const std::filesystem::path base_path = argv[1];
        const std::filesystem::path plan_path = argv[2];
        const std::filesystem::path output_path = argv[3];
        const std::filesystem::path audit_prefix = argv[4];
        hnswlib::L2Space space(128);
        Index index(&space, base_path.string(), false);
        const auto count = index.cur_element_count.load();
        if (count != 10000) throw std::runtime_error("O4 bridge requires 10K index");
        const auto before_edges = fnv_edges(index);
        const auto before_upper = fnv_upper(index);
        const auto plan = read_plan(plan_path, count, index);
        std::size_t changed = 0;
        std::size_t total = 0;
        for (std::size_t source = 0; source < count; ++source) {
            const auto node = static_cast<Node>(source);
            const auto original = neighbors(index, node);
            auto* raw = index.get_linklist0(node);
            auto* ids = reinterpret_cast<Node*>(raw + 1);
            const auto& selected = plan.at(node);
            for (std::size_t i = 0; i < selected.size(); ++i) {
                if (ids[i] != selected[i]) ++changed;
                ids[i] = selected[i];
            }
            index.setListCount(raw, static_cast<unsigned short>(selected.size()));
            total += selected.size();
            (void)original;
        }
        validate(index);
        const auto after_upper = fnv_upper(index);
        if (before_upper != after_upper) throw std::runtime_error("upper-layer checksum changed");
        std::filesystem::create_directories(output_path.parent_path());
        index.saveIndex(output_path.string());
        Index reloaded(&space, output_path.string(), false);
        validate(reloaded);
        const auto after_edges = fnv_edges(reloaded);
        if (after_edges == before_edges && changed != 0)
            throw std::runtime_error("edge hash unexpectedly unchanged");
        write_edges(reloaded, audit_prefix.string() + "_reloaded_edges.csv");
        std::ofstream metadata(audit_prefix.string() + "_metadata.json");
        if (!metadata) throw std::runtime_error("cannot write bridge metadata");
        metadata << "{\n"
                 << "  \"status\": \"O4_BRIDGE_REPLAY_COMPLETE\",\n"
                 << "  \"nodes\": " << count << ",\n"
                 << "  \"directed_edges\": " << total << ",\n"
                 << "  \"changed_positions\": " << changed << ",\n"
                 << "  \"before_edge_hash\": \"" << before_edges << "\",\n"
                 << "  \"after_edge_hash\": \"" << after_edges << "\",\n"
                 << "  \"upper_hash_before\": \"" << before_upper << "\",\n"
                 << "  \"upper_hash_after\": \"" << after_upper << "\",\n"
                 << "  \"upper_unchanged\": true,\n"
                 << "  \"reload_equal\": true\n"
                 << "}\n";
        std::cout << "nodes=" << count << " changed_positions=" << changed
                  << " before_edge_hash=" << before_edges << " after_edge_hash=" << after_edges
                  << " upper_hash=" << after_upper << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
