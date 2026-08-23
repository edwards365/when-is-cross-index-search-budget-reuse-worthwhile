#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_query_tracer.hpp"

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {

using Index = hnswlib::HierarchicalNSW<float>;

struct Matrix {
    std::size_t rows{};
    std::size_t columns{};
    std::vector<float> values;
};

struct Truth {
    std::size_t rows{};
    std::size_t k{};
    std::vector<std::uint32_t> labels;
};

template <typename Value>
Value read_scalar(std::ifstream& input) {
    Value value{};
    input.read(reinterpret_cast<char*>(&value), sizeof(value));
    if (!input) throw std::runtime_error("binary input ended unexpectedly");
    return value;
}

Matrix read_matrix(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot open query matrix");
    Matrix matrix;
    matrix.rows = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    matrix.columns = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    matrix.values.resize(matrix.rows * matrix.columns);
    input.read(reinterpret_cast<char*>(matrix.values.data()),
               static_cast<std::streamsize>(matrix.values.size() * sizeof(float)));
    if (!input || input.peek() != std::ifstream::traits_type::eof())
        throw std::runtime_error("invalid query matrix payload length");
    return matrix;
}

Truth read_truth(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot open development truth matrix");
    Truth truth;
    truth.rows = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    truth.k = static_cast<std::size_t>(read_scalar<std::uint64_t>(input));
    truth.labels.resize(truth.rows * truth.k);
    input.read(reinterpret_cast<char*>(truth.labels.data()),
               static_cast<std::streamsize>(truth.labels.size() * sizeof(std::uint32_t)));
    if (!input || input.peek() != std::ifstream::traits_type::eof())
        throw std::runtime_error("invalid truth matrix payload length");
    return truth;
}

std::unordered_set<std::uint32_t> read_sources(const std::filesystem::path& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open frozen R0 source labels");
    std::unordered_set<std::uint32_t> result;
    std::string line;
    while (std::getline(input, line)) {
        if (!line.empty()) result.insert(static_cast<std::uint32_t>(std::stoul(line)));
    }
    if (result.empty()) throw std::runtime_error("R0 source-label set is empty");
    return result;
}

std::vector<std::size_t> parse_efs(const std::string& raw) {
    std::vector<std::size_t> values;
    std::stringstream stream(raw);
    std::string token;
    while (std::getline(stream, token, ',')) values.push_back(std::stoul(token));
    if (values.empty() || !std::is_sorted(values.begin(), values.end()) ||
        std::adjacent_find(values.begin(), values.end()) != values.end())
        throw std::invalid_argument("ef values must be nonempty, unique, and increasing");
    return values;
}

template <typename Value>
std::string join(const std::vector<Value>& values) {
    std::ostringstream output;
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index) output << ';';
        output << values[index];
    }
    return output.str();
}

std::vector<std::uint32_t> ordered_result_labels(
    std::priority_queue<std::pair<float, hnswlib::labeltype>> heap) {
    std::vector<std::pair<float, std::uint32_t>> ordered;
    while (!heap.empty()) {
        ordered.emplace_back(heap.top().first,
                             static_cast<std::uint32_t>(heap.top().second));
        heap.pop();
    }
    std::sort(ordered.begin(), ordered.end(), [](const auto& left, const auto& right) {
        return left.first < right.first ||
               (left.first == right.first && left.second < right.second);
    });
    std::vector<std::uint32_t> labels;
    labels.reserve(ordered.size());
    for (const auto& item : ordered) labels.push_back(item.second);
    return labels;
}

struct Expansion {
    std::size_t event_index{};
    std::uint32_t source_label{};
    float source_distance{};
    float lower_bound{};
};

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 8) {
            std::cerr << "usage: hnsw_r0_trace_existing INDEX QUERIES TRUTH SOURCES "
                         "METRIC EFS OUTPUT_CSV\n";
            return 2;
        }
        const std::filesystem::path index_path = argv[1];
        const Matrix queries = read_matrix(argv[2]);
        const Truth truth = read_truth(argv[3]);
        const auto sources = read_sources(argv[4]);
        const std::string metric = argv[5];
        const auto efs = parse_efs(argv[6]);
        const std::filesystem::path output_path = argv[7];
        if (metric != "l2" && metric != "ip")
            throw std::invalid_argument("metric must be l2 or ip");
        if (queries.rows != truth.rows || queries.rows != 500 || truth.k != 10)
            throw std::invalid_argument("trace addendum requires 500 queries and top-10 truth");

        std::unique_ptr<hnswlib::SpaceInterface<float>> space;
        if (metric == "ip")
            space = std::make_unique<hnswlib::InnerProductSpace>(queries.columns);
        else
            space = std::make_unique<hnswlib::L2Space>(queries.columns);
        Index index(space.get(), index_path.string(), false);
        if (index.cur_element_count.load() != 100000)
            throw std::invalid_argument("trace addendum requires an existing 100K index");

        std::ofstream output(output_path);
        if (!output) throw std::runtime_error("cannot create matched trace output");
        output << "query_id,ef,event_index,source_label,source_distance,"
                  "lower_bound,later_expanded_labels,returned_top10,truth_top10\n";
        output << std::setprecision(std::numeric_limits<float>::max_digits10);
        for (const auto ef : efs) {
            for (std::size_t query_id = 0; query_id < queries.rows; ++query_id) {
                const auto* query = queries.values.data() + query_id * queries.columns;
                const auto trace = narhnsw::HnswQueryTracer<float>::search(
                    index, query, truth.k, ef, query_id);
                const auto returned = ordered_result_labels(trace.results);
                std::vector<std::uint32_t> expected(
                    truth.labels.begin() + static_cast<std::ptrdiff_t>(query_id * truth.k),
                    truth.labels.begin() +
                        static_cast<std::ptrdiff_t>((query_id + 1) * truth.k));
                std::vector<Expansion> expansions;
                for (const auto& event : trace.events) {
                    if (event.phase == "base" && event.event == "expanded") {
                        expansions.push_back(
                            {event.event_index,
                             static_cast<std::uint32_t>(index.getExternalLabel(event.source)),
                             event.distance_to_query, event.lower_bound_before});
                    }
                }
                std::unordered_set<std::uint32_t> written;
                for (std::size_t position = 0; position < expansions.size(); ++position) {
                    const auto& expansion = expansions[position];
                    if (!sources.count(expansion.source_label) ||
                        !written.insert(expansion.source_label).second)
                        continue;
                    std::vector<std::uint32_t> later;
                    later.reserve(expansions.size() - position - 1);
                    for (std::size_t later_position = position + 1;
                         later_position < expansions.size(); ++later_position)
                        later.push_back(expansions[later_position].source_label);
                    output << query_id << ',' << ef << ',' << expansion.event_index << ','
                           << expansion.source_label << ',' << expansion.source_distance << ','
                           << expansion.lower_bound << ",\"" << join(later) << "\",\""
                           << join(returned) << "\",\"" << join(expected) << "\"\n";
                }
            }
        }
        std::cout << "status=complete matched_sources=" << sources.size()
                  << " queries=" << queries.rows << " efs=" << efs.size() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
