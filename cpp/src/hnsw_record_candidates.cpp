#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_candidate_logger.hpp"

#include <algorithm>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

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

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 8) {
            std::cerr << "usage: hnsw_record_candidates INPUT.fbin POINTS DIMENSIONS SEED M "
                         "EF_CONSTRUCTION OUTPUT_DIR\n";
            return 2;
        }
        const std::filesystem::path input_path = argv[1];
        const auto points = parse_size(argv[2], "points");
        const auto dimensions = parse_size(argv[3], "dimensions");
        const auto seed = parse_size(argv[4], "seed");
        const auto m = parse_size(argv[5], "M");
        const auto ef_construction = parse_size(argv[6], "ef_construction");
        const std::filesystem::path output = argv[7];
        if (std::filesystem::exists(output))
            throw std::runtime_error("output directory already exists");
        const auto values = load_points(input_path, points, dimensions);
        std::vector<std::size_t> order(points);
        std::iota(order.begin(), order.end(), 0);
        std::mt19937 generator(static_cast<std::uint32_t>(seed));
        std::shuffle(order.begin(), order.end(), generator);

        hnswlib::L2Space space(dimensions);
        hnswlib::HierarchicalNSW<float> index(&space, points, m, ef_construction, seed);
        narhnsw::HnswCandidateLogger<float> logger;
        for (const auto label : order)
            logger.add_point(index, values.data() + label * dimensions, label);

        std::filesystem::create_directories(output);
        logger.export_csv(output, index);
        std::ofstream mapping(output / "internal_to_external.csv");
        mapping << "internal_id,external_label\n";
        for (std::size_t internal = 0; internal < points; ++internal)
            mapping << internal << ',' << index.getExternalLabel(internal) << '\n';
        std::ofstream metadata(output / "metadata.json");
        metadata << "{\n"
                 << "  \"status\": \"complete\",\n"
                 << "  \"points\": " << points << ",\n"
                 << "  \"dimensions\": " << dimensions << ",\n"
                 << "  \"build_seed\": " << seed << ",\n"
                 << "  \"M\": " << m << ",\n"
                 << "  \"ef_construction\": " << ef_construction << ",\n"
                 << "  \"candidate_rows\": " << logger.decisions().size() << ",\n"
                 << "  \"adjacency_change_rows\": " << logger.adjacency_changes().size()
                 << ",\n"
                 << "  \"accessed_hdf5_members\": [\"train\"],\n"
                 << "  \"formal_test_members_accessed\": false,\n"
                 << "  \"index_saved\": false\n"
                 << "}\n";
        std::cout << "candidate_rows=" << logger.decisions().size()
                  << " adjacency_change_rows=" << logger.adjacency_changes().size() << '\n';
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
    return 0;
}
