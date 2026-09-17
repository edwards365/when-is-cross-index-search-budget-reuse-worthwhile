#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
class CountingSpace final : public hnswlib::SpaceInterface<float> {
 public:
  CountingSpace(std::size_t dim, bool ip) : state_{dim, ip, &count_} {}
  std::size_t get_data_size() override { return state_.dim * sizeof(float); }
  hnswlib::DISTFUNC<float> get_dist_func() override { return distance; }
  void* get_dist_func_param() override { return &state_; }
  void reset() { count_.store(0, std::memory_order_relaxed); }
  std::uint64_t count() const { return count_.load(std::memory_order_relaxed); }
 private:
  struct State { std::size_t dim; bool ip; std::atomic<std::uint64_t>* count; };
  static float distance(const void* a0, const void* b0, const void* s0) {
    const auto* s = static_cast<const State*>(s0);
    const auto* a = static_cast<const float*>(a0);
    const auto* b = static_cast<const float*>(b0);
    s->count->fetch_add(1, std::memory_order_relaxed);
    float value = 0.0F;
    if (s->ip) {
      for (std::size_t i = 0; i < s->dim; ++i) value += a[i] * b[i];
      return 1.0F - value;
    }
    for (std::size_t i = 0; i < s->dim; ++i) { const float d = a[i] - b[i]; value += d * d; }
    return value;
  }
  std::atomic<std::uint64_t> count_{0};
  State state_;
};

template <class T> std::vector<std::vector<T>> read_vecs(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open vecs: " + path);
  std::vector<std::vector<T>> rows;
  while (true) {
    std::int32_t dim = 0; in.read(reinterpret_cast<char*>(&dim), sizeof(dim));
    if (!in) break;
    if (dim <= 0) throw std::runtime_error("invalid vec dimension");
    rows.emplace_back(static_cast<std::size_t>(dim));
    in.read(reinterpret_cast<char*>(rows.back().data()), dim * sizeof(T));
    if (!in) throw std::runtime_error("truncated vecs");
  }
  if (rows.empty()) throw std::runtime_error("empty vecs");
  return rows;
}

std::vector<std::size_t> parse_grid(const std::string& raw) {
  std::vector<std::size_t> out; std::stringstream stream(raw); std::string token;
  while (std::getline(stream, token, ',')) out.push_back(std::stoul(token));
  if (out.empty() || !std::is_sorted(out.begin(), out.end())) throw std::runtime_error("invalid grid");
  return out;
}

std::vector<hnswlib::labeltype> labels(std::priority_queue<std::pair<float,hnswlib::labeltype>> heap) {
  std::vector<hnswlib::labeltype> out;
  while (!heap.empty()) { out.push_back(heap.top().second); heap.pop(); }
  std::reverse(out.begin(), out.end()); return out;
}
}

int main(int argc, char** argv) {
  try {
    if (argc != 8) {
      std::cerr << "usage: s4_hnsw_replay INDEX QUERIES_FVECS TRUTH_IVECS METRIC EF_GRID BUILD_ID OUTPUT_CSV\n";
      return 2;
    }
    auto queries = read_vecs<float>(argv[2]);
    auto truth = read_vecs<std::int32_t>(argv[3]);
    if (queries.size() != truth.size()) throw std::runtime_error("query/truth row mismatch");
    const std::string metric = argv[4];
    if (metric != "l2" && metric != "ip") throw std::runtime_error("invalid metric");
    CountingSpace space(queries.front().size(), metric == "ip");
    hnswlib::HierarchicalNSW<float> index(&space, argv[1], false);
    if (index.cur_element_count.load() != 100000) throw std::runtime_error("index is not 100K");
    auto grid = parse_grid(argv[5]);
    std::ofstream out(argv[7]); if (!out) throw std::runtime_error("cannot create output");
    out << "build,query_id,ef,recall,ndc,wall_ns,topk\n" << std::setprecision(17);
    for (auto ef : grid) {
      index.setEf(ef);
      for (std::size_t qid = 0; qid < queries.size(); ++qid) {
        space.reset(); const auto start = std::chrono::steady_clock::now();
        auto found = labels(index.searchKnn(queries[qid].data(), truth[qid].size()));
        const auto stop = std::chrono::steady_clock::now();
        std::size_t hits = 0;
        for (auto x : found) if (std::find(truth[qid].begin(), truth[qid].end(), static_cast<std::int32_t>(x)) != truth[qid].end()) ++hits;
        out << argv[6] << ',' << qid << ',' << ef << ',' << static_cast<double>(hits)/truth[qid].size() << ',' << space.count() << ','
            << std::chrono::duration_cast<std::chrono::nanoseconds>(stop-start).count() << ",\"";
        for (std::size_t i=0;i<found.size();++i) { if(i) out << ';'; out << found[i]; }
        out << "\"\n";
      }
    }
    std::cout << "status=complete build=" << argv[6] << " rows=" << queries.size()*grid.size() << '\n';
    return 0;
  } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
