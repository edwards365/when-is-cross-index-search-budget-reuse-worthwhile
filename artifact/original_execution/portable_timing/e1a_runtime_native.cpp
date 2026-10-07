#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <numeric>
#include <queue>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <time.h>
#include <vector>

namespace {
template <typename T> T read_one(std::ifstream& in) {
  T value{};
  in.read(reinterpret_cast<char*>(&value), sizeof(value));
  if (!in) throw std::runtime_error("truncated query input");
  return value;
}
struct Query { std::int64_t id; std::vector<float> vector; };
std::vector<Query> read_queries(const std::string& path, std::size_t& dim) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open query input");
  char magic[8]; in.read(magic, 8);
  if (!in || std::string(magic, 8) != "E1AQ0001") throw std::runtime_error("bad query role format");
  auto count = read_one<std::uint64_t>(in);
  dim = read_one<std::uint64_t>(in);
  if (count != 1000 || dim == 0 || dim > 4096) throw std::runtime_error("invalid evaluation role shape");
  std::vector<Query> result;
  for (std::uint64_t i = 0; i < count; ++i) {
    Query q{read_one<std::int64_t>(in), std::vector<float>(dim)};
    in.read(reinterpret_cast<char*>(q.vector.data()), dim * sizeof(float));
    if (!in) throw std::runtime_error("truncated query vector");
    result.push_back(std::move(q));
  }
  if (in.peek() != std::char_traits<char>::eof()) throw std::runtime_error("trailing query bytes");
  return result;
}
std::vector<std::size_t> grid(const std::string& csv) {
  std::istringstream in(csv); std::string part; std::vector<std::size_t> result;
  while (std::getline(in, part, ',')) result.push_back(std::stoull(part));
  if (result.empty() || !std::is_sorted(result.begin(), result.end()) ||
      std::adjacent_find(result.begin(), result.end()) != result.end() || result.back() != 2400)
    throw std::runtime_error("invalid locked actions");
  return result;
}
std::vector<hnswlib::labeltype> ordered(std::priority_queue<std::pair<float, hnswlib::labeltype>> found) {
  std::vector<hnswlib::labeltype> out;
  while (!found.empty()) { out.push_back(found.top().second); found.pop(); }
  std::reverse(out.begin(), out.end());
  return out;
}
std::string join(const std::vector<hnswlib::labeltype>& ids) {
  std::ostringstream out;
  for (std::size_t i = 0; i < ids.size(); ++i) { if (i) out << ';'; out << ids[i]; }
  return out.str();
}
std::uint64_t now_ns(clockid_t clock) {
  timespec ts{};
  if (clock_gettime(clock, &ts)) throw std::runtime_error("clock_gettime failed");
  return std::uint64_t(ts.tv_sec) * 1000000000ULL + ts.tv_nsec;
}
std::map<std::pair<std::int64_t, std::size_t>, std::string> expected(const std::string& path) {
  std::ifstream in(path); std::string line;
  if (!std::getline(in, line) || line != "query_id,ef,ndc,topk") throw std::runtime_error("bad sealed response schema");
  std::map<std::pair<std::int64_t, std::size_t>, std::string> result;
  while (std::getline(in, line)) {
    std::istringstream row(line); std::string id, ef, ndc, topk;
    if (!std::getline(row,id,',') || !std::getline(row,ef,',') || !std::getline(row,ndc,',') ||
        !std::getline(row,topk) || topk.empty()) throw std::runtime_error("bad sealed response row");
    if (!result.emplace(std::make_pair(std::stoll(id), std::stoull(ef)), topk).second)
      throw std::runtime_error("duplicate sealed response cell");
  }
  return result;
}
}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 11) throw std::runtime_error("usage: runtime INDEX QBIN METRIC ACTIONS EXPECTED_COUNT EXPECTED_CSV LIMIT SEED REPS OUT_CSV");
    if (std::filesystem::exists(argv[10])) throw std::runtime_error("output exists; no overwrite");
    auto actions = grid(argv[4]);
    const auto count = std::stoull(argv[5]);
    const auto limit = std::stoull(argv[7]);
    const auto seed = std::stoull(argv[8]);
    const auto reps = std::stoull(argv[9]);
    if ((limit != 100 && limit != 1000) || reps != 7) throw std::runtime_error("invalid pilot/formal protocol");
    std::size_t dim = 0;
    auto queries = read_queries(argv[2], dim);
    auto truth = expected(argv[6]);
    const std::string metric = argv[3];
    if (metric != "l2" && metric != "ip") throw std::runtime_error("invalid metric");
    std::unique_ptr<hnswlib::SpaceInterface<float>> space(metric == "l2"
        ? static_cast<hnswlib::SpaceInterface<float>*>(new hnswlib::L2Space(dim))
        : static_cast<hnswlib::SpaceInterface<float>*>(new hnswlib::InnerProductSpace(dim)));
    hnswlib::HierarchicalNSW<float> index(space.get(), argv[1], false);
    if (index.cur_element_count.load() != count) throw std::runtime_error("index count mismatch");
    for (auto ef : actions) for (std::size_t i = 0; i < limit; ++i)
      if (!truth.count({queries[i].id, ef})) throw std::runtime_error("sealed response missing cell");
    for (auto ef : actions) {
      index.setEf(ef);
      for (std::size_t i = 0; i < 50; ++i) index.searchKnn(queries[i].vector.data(), 10);
    }
    std::ofstream out(argv[10]);
    if (!out) throw std::runtime_error("cannot create output");
    out << "query_id,query_position,repetition,ef,action_order,wall_ns,cpu_ns,ordered_top10,stop_or_error\n";
    std::mt19937_64 rng(seed);
    std::vector<std::size_t> positions(limit);
    std::iota(positions.begin(), positions.end(), 0);
    std::uint64_t rows = 0;
    for (std::size_t rep = 0; rep < reps; ++rep) {
      std::shuffle(positions.begin(), positions.end(), rng);
      for (auto i : positions) {
        auto order = actions;
        std::shuffle(order.begin(), order.end(), rng);
        for (std::size_t a = 0; a < order.size(); ++a) {
          const auto ef = order[a];
          index.setEf(ef);
          const auto wall0 = now_ns(CLOCK_MONOTONIC_RAW);
          const auto cpu0 = now_ns(CLOCK_PROCESS_CPUTIME_ID);
          auto found = ordered(index.searchKnn(queries[i].vector.data(), 10));
          const auto cpu1 = now_ns(CLOCK_PROCESS_CPUTIME_ID);
          const auto wall1 = now_ns(CLOCK_MONOTONIC_RAW);
          if (found.size() != 10 || join(found) != truth.at({queries[i].id, ef}))
            throw std::runtime_error("timed native top-k differs from sealed response");
          out << queries[i].id << ',' << i << ',' << rep << ',' << ef << ',' << a << ','
              << wall1-wall0 << ',' << cpu1-cpu0 << ',' << join(found) << ",OK\n";
          ++rows;
        }
      }
    }
    if (!out) throw std::runtime_error("output write failed");
    std::cout << "rows=" << rows << " equivalent=1\n";
    return 0;
  } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
