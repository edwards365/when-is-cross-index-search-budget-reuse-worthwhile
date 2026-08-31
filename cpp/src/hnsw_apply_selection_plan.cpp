#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_selected_connector.hpp"

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using Index = hnswlib::HierarchicalNSW<float>;

struct Points {
    std::size_t rows{};
    std::size_t dimensions{};
    std::vector<float> values;
};

Points read_points(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot open point file");
    std::uint64_t rows = 0;
    std::uint64_t dimensions = 0;
    input.read(reinterpret_cast<char*>(&rows), sizeof(rows));
    input.read(reinterpret_cast<char*>(&dimensions), sizeof(dimensions));
    if (!input || rows == 0 || dimensions == 0)
        throw std::runtime_error("invalid point-file header");
    Points points{static_cast<std::size_t>(rows), static_cast<std::size_t>(dimensions), {}};
    points.values.resize(points.rows * points.dimensions);
    input.read(reinterpret_cast<char*>(points.values.data()),
               static_cast<std::streamsize>(points.values.size() * sizeof(float)));
    if (!input || input.peek() != std::ifstream::traits_type::eof())
        throw std::runtime_error("invalid point-file payload length");
    return points;
}

std::map<hnswlib::tableint, std::vector<hnswlib::tableint>> read_plan(
    const std::filesystem::path& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open selection plan");
    std::map<hnswlib::tableint, std::vector<hnswlib::tableint>> plan;
    std::string line;
    while (std::getline(input, line)) {
        if (line.empty()) continue;
        const auto comma = line.find(',');
        if (comma == std::string::npos) throw std::runtime_error("invalid selection-plan row");
        const auto source = static_cast<hnswlib::tableint>(std::stoul(line.substr(0, comma)));
        const auto target = static_cast<hnswlib::tableint>(std::stoul(line.substr(comma + 1)));
        plan[source].push_back(target);
    }
    if (plan.empty()) throw std::runtime_error("selection plan is empty");
    return plan;
}

std::set<hnswlib::tableint> neighbors(const Index& index, hnswlib::tableint node) {
    auto* raw = index.get_linklist0(node);
    const auto degree = index.getListCount(raw);
    const auto* ids = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
    return {ids, ids + degree};
}

void export_edges(const Index& index, std::size_t count,
                  const std::filesystem::path& path) {
    std::ofstream output(path);
    if (!output) throw std::runtime_error("cannot create edge output");
    output << "source,target\n";
    for (std::size_t source = 0; source < count; ++source) {
        for (const auto target : neighbors(index, static_cast<hnswlib::tableint>(source)))
            output << source << ',' << target << '\n';
    }
}

struct AuditRow {
    hnswlib::tableint source{};
    hnswlib::tableint target{};
    bool proposed_added{};
    bool target_to_source_before{};
    bool source_to_target_immediate{};
    bool target_to_source_immediate{};
    std::size_t original_degree{};
    std::size_t selected_degree{};
};

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 9) {
            std::cerr << "usage: hnsw_apply_selection_plan POINTS BASE_PLAN TREATMENT_PLAN "
                         "METRIC M EF SEED OUTPUT\n";
            return 2;
        }
        const auto points = read_points(argv[1]);
        const auto base_plan = read_plan(argv[2]);
        const auto treatment_plan = read_plan(argv[3]);
        const std::string metric = argv[4];
        const std::size_t m = std::stoul(argv[5]);
        const std::size_t ef_construction = std::stoul(argv[6]);
        const std::size_t seed = std::stoul(argv[7]);
        const std::filesystem::path output = argv[8];
        if (metric != "l2" && metric != "ip")
            throw std::invalid_argument("metric must be l2 or ip");

        std::unique_ptr<hnswlib::SpaceInterface<float>> space;
        if (metric == "l2")
            space = std::make_unique<hnswlib::L2Space>(points.dimensions);
        else
            space = std::make_unique<hnswlib::InnerProductSpace>(points.dimensions);
        Index base_index(space.get(), points.rows, m, ef_construction, seed);
        Index treatment_index(space.get(), points.rows, m, ef_construction, seed);
        for (std::size_t node = 0; node < points.rows; ++node) {
            const auto* point = points.values.data() + node * points.dimensions;
            base_index.addPoint(point, node);
            treatment_index.addPoint(point, node);
        }

        if (base_plan.size() != treatment_plan.size())
            throw std::invalid_argument("base and treatment plans have different source counts");
        for (const auto& [source, selected] : base_plan) {
            if (!treatment_plan.count(source))
                throw std::invalid_argument("base and treatment plan sources differ");
            if (selected.size() != m)
                throw std::invalid_argument("every base selection must contain exactly M rows");
            narhnsw::mutually_connect_selected(base_index, source, selected, 0);
        }

        std::filesystem::create_directories(output.parent_path());
        auto before_path = output;
        before_path.replace_filename(output.stem().string() + "_before_edges.csv");
        export_edges(base_index, points.rows, before_path);

        std::vector<AuditRow> rows;
        for (const auto& [source, selected] : treatment_plan) {
            if (source >= points.rows) throw std::invalid_argument("plan source is invalid");
            if (selected.size() != m)
                throw std::invalid_argument("every planned selection must contain exactly M rows");
            const auto before = neighbors(base_index, source);
            for (const auto target : selected) {
                if (target >= points.rows) throw std::invalid_argument("plan target is invalid");
                rows.push_back({source, target, before.count(target) == 0,
                                neighbors(base_index, target).count(source) != 0, false, false,
                                before.size(), selected.size()});
            }
            narhnsw::mutually_connect_selected(treatment_index, source, selected, 0);
            for (auto& row : rows) {
                if (row.source != source) continue;
                row.source_to_target_immediate =
                    neighbors(treatment_index, source).count(row.target) != 0;
                row.target_to_source_immediate =
                    neighbors(treatment_index, row.target).count(source) != 0;
            }
        }

        auto after_path = output;
        after_path.replace_filename(output.stem().string() + "_after_edges.csv");
        export_edges(treatment_index, points.rows, after_path);
        std::ofstream result(output);
        if (!result) throw std::runtime_error("cannot create audit output");
        result << "source,target,proposed_added,target_to_source_before,"
                  "source_to_target_immediate,target_to_source_immediate,"
                  "source_to_target_final,target_to_source_final,original_degree,selected_degree\n";
        std::size_t added = 0;
        std::size_t reciprocal_final = 0;
        for (const auto& row : rows) {
            const bool source_final =
                neighbors(treatment_index, row.source).count(row.target) != 0;
            const bool target_final =
                neighbors(treatment_index, row.target).count(row.source) != 0;
            added += row.proposed_added;
            reciprocal_final += row.proposed_added && target_final;
            result << row.source << ',' << row.target << ',' << row.proposed_added << ','
                   << row.target_to_source_before << ',' << row.source_to_target_immediate << ','
                   << row.target_to_source_immediate << ',' << source_final << ',' << target_final
                   << ',' << row.original_degree << ',' << row.selected_degree << '\n';
        }
        auto index_path = output;
        index_path.replace_filename(output.stem().string() + "_stable_index.bin");
        treatment_index.saveIndex(index_path.string());
        auto metadata_path = output;
        metadata_path.replace_filename(output.stem().string() + "_metadata.json");
        std::ofstream metadata(metadata_path);
        metadata << "{\n"
                 << "  \"status\": \"complete\",\n"
                 << "  \"seed\": " << seed << ",\n"
                 << "  \"points\": " << points.rows << ",\n"
                 << "  \"changed_sources\": " << treatment_plan.size() << ",\n"
                 << "  \"proposed_added\": " << added << ",\n"
                 << "  \"proposed_added_reciprocal_final\": " << reciprocal_final << ",\n"
                 << "  \"entry_point\": " << treatment_index.enterpoint_node_ << ",\n"
                 << "  \"max_degree_layer0\": " << treatment_index.maxM0_ << ",\n"
                 << "  \"formal_test_members_accessed\": false,\n"
                 << "  \"certification_reserved_accessed\": false,\n"
                 << "  \"evaluation_reserved_accessed\": false\n"
                 << "}\n";
        std::cout << "points=" << points.rows << " planned_centers=" << treatment_plan.size()
                  << " proposed_added=" << added
                  << " proposed_added_reciprocal_final=" << reciprocal_final << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
