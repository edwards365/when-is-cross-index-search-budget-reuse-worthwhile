#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

class CountingSpace final : public hnswlib::SpaceInterface<float> {
 public:
  CountingSpace(std::size_t dim, bool inner_product)
      : native_(inner_product
                    ? std::unique_ptr<hnswlib::SpaceInterface<float>>(new hnswlib::InnerProductSpace(dim))
                    : std::unique_ptr<hnswlib::SpaceInterface<float>>(new hnswlib::L2Space(dim))) {
    state_.native_function = native_->get_dist_func();
    state_.native_parameter = native_->get_dist_func_param();
    state_.count = &count_;
  }

  std::size_t get_data_size() override { return native_->get_data_size(); }
  hnswlib::DISTFUNC<float> get_dist_func() override { return distance; }
  void* get_dist_func_param() override { return &state_; }
  void reset() { count_ = 0; }
  std::uint64_t count() const { return count_; }

 private:
  struct State {
    hnswlib::DISTFUNC<float> native_function;
    void* native_parameter;
    std::uint64_t* count;
  };

  static float distance(const void* a, const void* b, const void* parameter) {
    const auto* state = static_cast<const State*>(parameter);
    ++(*state->count);
    return state->native_function(a, b, state->native_parameter);
  }

  std::unique_ptr<hnswlib::SpaceInterface<float>> native_;
  std::uint64_t count_ = 0;
  State state_{};
};

template <typename T>
T read_one(std::ifstream& input) {
  T value{};
  input.read(reinterpret_cast<char*>(&value), sizeof(value));
  if (!input) throw std::runtime_error("Truncated query input");
  return value;
}

struct Query {
  std::int64_t raw_id;
  std::vector<float> vector;
};

std::vector<Query> read_queries(const std::string& path, std::size_t& dimension) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("Cannot open query input");
  char magic[8]{};
  input.read(magic, sizeof(magic));
  if (!input || std::string(magic, sizeof(magic)) != "E1AQ0001")
    throw std::runtime_error("Query format mismatch");
  const auto count = read_one<std::uint64_t>(input);
  dimension = static_cast<std::size_t>(read_one<std::uint64_t>(input));
  if (count != 500 || dimension == 0 || dimension > 4096)
    throw std::runtime_error("Unexpected source-design shape");
  std::vector<Query> queries;
  queries.reserve(static_cast<std::size_t>(count));
  for (std::uint64_t i = 0; i < count; ++i) {
    Query query{read_one<std::int64_t>(input), std::vector<float>(dimension)};
    input.read(reinterpret_cast<char*>(query.vector.data()), dimension * sizeof(float));
    if (!input) throw std::runtime_error("Truncated query vector");
    queries.push_back(std::move(query));
  }
  if (input.peek() != std::char_traits<char>::eof())
    throw std::runtime_error("Trailing query bytes");
  return queries;
}

std::vector<std::size_t> parse_grid(const std::string& value) {
  std::stringstream input(value);
  std::string token;
  std::vector<std::size_t> grid;
  while (std::getline(input, token, ',')) {
    const auto ef = std::stoull(token);
    if (ef < 10) throw std::runtime_error("ef below k");
    grid.push_back(static_cast<std::size_t>(ef));
  }
  if (grid.empty() || !std::is_sorted(grid.begin(), grid.end()) ||
      std::adjacent_find(grid.begin(), grid.end()) != grid.end())
    throw std::runtime_error("Invalid ef grid");
  return grid;
}

std::vector<hnswlib::labeltype> ordered_labels(
    std::priority_queue<std::pair<float, hnswlib::labeltype>> found) {
  std::vector<hnswlib::labeltype> result;
  while (!found.empty()) {
    result.push_back(found.top().second);
    found.pop();
  }
  std::reverse(result.begin(), result.end());
  return result;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 8) {
      std::cerr << "usage: e1a_ndc_replay INDEX QUERY_BIN METRIC EF_GRID QUERY_LIMIT EXPECTED_COUNT OUTPUT_CSV\n";
      return 2;
    }
    const std::string metric = argv[3];
    if (metric != "l2" && metric != "ip") throw std::runtime_error("Invalid metric");
    const auto grid = parse_grid(argv[4]);
    const auto limit = std::stoull(argv[5]);
    const auto expected_count = std::stoull(argv[6]);
    if (limit == 0 || limit > 500) throw std::runtime_error("Invalid query limit");
    if (std::filesystem::exists(argv[7])) throw std::runtime_error("Output exists; refusing overwrite");
    std::size_t dimension = 0;
    const auto queries = read_queries(argv[2], dimension);
    CountingSpace space(dimension, metric == "ip");
    hnswlib::HierarchicalNSW<float> index(&space, argv[1], false);
    if (index.cur_element_count.load() != expected_count)
      throw std::runtime_error("Index count mismatch");
    std::ofstream output(argv[7]);
    if (!output) throw std::runtime_error("Cannot create output");
    output << "query_id,ef,ndc,topk\n";
    for (const auto ef : grid) {
      index.setEf(ef);
      for (std::size_t i = 0; i < limit; ++i) {
        space.reset();
        const auto found = ordered_labels(index.searchKnn(queries[i].vector.data(), 10));
        if (found.size() != 10) throw std::runtime_error("Incomplete top-k");
        output << queries[i].raw_id << ',' << ef << ',' << space.count() << ',';
        for (std::size_t j = 0; j < found.size(); ++j) {
          if (j) output << ';';
          output << found[j];
        }
        output << '\n';
      }
    }
    if (!output) throw std::runtime_error("Output write failed");
    std::cout << "rows=" << grid.size() * limit << " status=REPLAY_PENDING_VALIDATION\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
