#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstddef>
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

class CountingInnerProductSpace final : public hnswlib::SpaceInterface<float> {
 public:
  explicit CountingInnerProductSpace(std::size_t dim) : state_{dim, &count_} {}
  std::size_t get_data_size() override { return state_.dim * sizeof(float); }
  hnswlib::DISTFUNC<float> get_dist_func() override { return distance; }
  void* get_dist_func_param() override { return &state_; }
  void reset() { count_.store(0, std::memory_order_relaxed); }
  long count() const { return count_.load(std::memory_order_relaxed); }

 private:
  struct State { std::size_t dim; std::atomic<long>* count; };
  static float distance(const void* a_raw, const void* b_raw, const void* state_raw) {
    const auto* state = static_cast<const State*>(state_raw);
    const auto* a = static_cast<const float*>(a_raw);
    const auto* b = static_cast<const float*>(b_raw);
    state->count->fetch_add(1, std::memory_order_relaxed);
    float dot = 0.0F;
    for (std::size_t i = 0; i < state->dim; ++i) dot += a[i] * b[i];
    return 1.0F - dot;
  }
  std::atomic<long> count_{0};
  State state_;
};

std::vector<std::vector<float>> read_fvecs(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open fvecs: " + path);
  std::vector<std::vector<float>> rows;
  while (true) {
    std::int32_t dim = 0;
    in.read(reinterpret_cast<char*>(&dim), sizeof(dim));
    if (!in) break;
    if (dim <= 0) throw std::runtime_error("invalid fvec dimension");
    rows.emplace_back(static_cast<std::size_t>(dim));
    in.read(reinterpret_cast<char*>(rows.back().data()), dim * sizeof(float));
    if (!in) throw std::runtime_error("truncated fvecs");
  }
  if (rows.empty()) throw std::runtime_error("empty fvecs");
  return rows;
}

std::vector<std::vector<std::int32_t>> read_ivecs(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open ivecs: " + path);
  std::vector<std::vector<std::int32_t>> rows;
  while (true) {
    std::int32_t dim = 0;
    in.read(reinterpret_cast<char*>(&dim), sizeof(dim));
    if (!in) break;
    if (dim <= 0) throw std::runtime_error("invalid ivec dimension");
    rows.emplace_back(static_cast<std::size_t>(dim));
    in.read(reinterpret_cast<char*>(rows.back().data()), dim * sizeof(std::int32_t));
    if (!in) throw std::runtime_error("truncated ivecs");
  }
  if (rows.empty()) throw std::runtime_error("empty ivecs");
  return rows;
}

std::vector<std::size_t> parse_grid(const std::string& value) {
  std::vector<std::size_t> result;
  std::stringstream stream(value);
  std::string token;
  while (std::getline(stream, token, ',')) result.push_back(std::stoul(token));
  if (result.empty()) throw std::runtime_error("empty ef grid");
  return result;
}

std::vector<hnswlib::labeltype> ordered_labels(
    std::priority_queue<std::pair<float, hnswlib::labeltype>> heap) {
  std::vector<hnswlib::labeltype> out;
  while (!heap.empty()) { out.push_back(heap.top().second); heap.pop(); }
  std::reverse(out.begin(), out.end());
  return out;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 7) {
      std::cerr << "usage: deep1m_counting_runner INDEX QUERIES_FVECS TRUTH_IVECS EF_GRID BUILD_ID OUTPUT_CSV\n";
      return 2;
    }
    const auto queries = read_fvecs(argv[2]);
    const auto truth = read_ivecs(argv[3]);
    if (queries.size() != truth.size()) throw std::runtime_error("query/truth row mismatch");
    const std::size_t dim = queries.front().size();
    for (const auto& q : queries) if (q.size() != dim) throw std::runtime_error("query dim mismatch");
    CountingInnerProductSpace space(dim);
    hnswlib::HierarchicalNSW<float> index(&space, argv[1], false);
    const auto grid = parse_grid(argv[4]);
    std::ofstream out(argv[6]);
    if (!out) throw std::runtime_error("cannot open output");
    out << "build,query_id,ef,recall,ndc,wall_ns,topk\n" << std::setprecision(17);
    for (const auto ef : grid) {
      index.setEf(ef);
      for (std::size_t qid = 0; qid < queries.size(); ++qid) {
        space.reset();
        const auto start = std::chrono::steady_clock::now();
        auto labels = ordered_labels(index.searchKnn(queries[qid].data(), truth[qid].size()));
        const auto stop = std::chrono::steady_clock::now();
        std::size_t hits = 0;
        for (const auto label : labels)
          if (std::find(truth[qid].begin(), truth[qid].end(), static_cast<std::int32_t>(label)) != truth[qid].end()) ++hits;
        out << argv[5] << ',' << qid << ',' << ef << ','
            << static_cast<double>(hits) / static_cast<double>(truth[qid].size()) << ','
            << space.count() << ','
            << std::chrono::duration_cast<std::chrono::nanoseconds>(stop - start).count() << ",\"";
        for (std::size_t i = 0; i < labels.size(); ++i) { if (i) out << ';'; out << labels[i]; }
        out << "\"\n";
      }
    }
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
