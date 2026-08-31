#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/resource.h>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {
using Index = hnswlib::HierarchicalNSW<float>;

class CountingL2Space final : public hnswlib::SpaceInterface<float> {
 public:
  explicit CountingL2Space(std::size_t dimensions) : state_{dimensions, &counter_} {}
  std::size_t get_data_size() override { return state_.dimensions * sizeof(float); }
  hnswlib::DISTFUNC<float> get_dist_func() override { return distance; }
  void* get_dist_func_param() override { return &state_; }
  void reset() { counter_.store(0); }
  std::uint64_t count() const { return counter_.load(); }

 private:
  struct State {
    std::size_t dimensions;
    std::atomic<std::uint64_t>* counter;
  };
  static float distance(const void* left_raw, const void* right_raw, const void* state_raw) {
    const auto* state = static_cast<const State*>(state_raw);
    const auto* left = static_cast<const float*>(left_raw);
    const auto* right = static_cast<const float*>(right_raw);
    state->counter->fetch_add(1, std::memory_order_relaxed);
    float result = 0.0F;
    for (std::size_t index = 0; index < state->dimensions; ++index) {
      const float delta = left[index] - right[index];
      result += delta * delta;
    }
    return result;
  }
  std::atomic<std::uint64_t> counter_{0};
  State state_;
};

template <class T>
T read_scalar(std::ifstream& input) {
  T value{};
  input.read(reinterpret_cast<char*>(&value), sizeof(value));
  if (!input) throw std::runtime_error("short binary input");
  return value;
}

struct Matrix {
  std::size_t rows{};
  std::size_t columns{};
  std::vector<float> values;
};

Matrix read_matrix(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open matrix: " + path.string());
  Matrix matrix;
  matrix.rows = read_scalar<std::uint64_t>(input);
  matrix.columns = read_scalar<std::uint64_t>(input);
  matrix.values.resize(matrix.rows * matrix.columns);
  input.read(reinterpret_cast<char*>(matrix.values.data()),
             static_cast<std::streamsize>(matrix.values.size() * sizeof(float)));
  if (!input) throw std::runtime_error("short matrix payload: " + path.string());
  return matrix;
}

std::vector<std::uint32_t> read_order(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open order: " + path.string());
  const auto count = read_scalar<std::uint64_t>(input);
  std::vector<std::uint32_t> order(count);
  input.read(reinterpret_cast<char*>(order.data()),
             static_cast<std::streamsize>(order.size() * sizeof(std::uint32_t)));
  if (!input) throw std::runtime_error("short order payload: " + path.string());
  return order;
}

template <class T>
void write_key(std::ofstream& output, const std::string& key, const T& value) {
  output << key << '=' << value << '\n';
}

std::vector<hnswlib::tableint> neighbors(const Index& index, hnswlib::tableint node,
                                          int layer = 0) {
  auto* raw = index.get_linklist_at_level(node, layer);
  const auto degree = index.getListCount(raw);
  const auto* ids = reinterpret_cast<const hnswlib::tableint*>(raw + 1);
  return {ids, ids + degree};
}

void mix(std::uint64_t& hash, std::uint64_t value) {
  for (int byte = 0; byte < 8; ++byte) {
    hash ^= (value >> (8 * byte)) & 255U;
    hash *= 1099511628211ULL;
  }
}

std::uint64_t graph_hash(const Index& index) {
  std::uint64_t hash = 1469598103934665603ULL;
  for (hnswlib::tableint node = 0; node < index.cur_element_count.load(); ++node) {
    for (int layer = 0; layer <= index.element_levels_[node]; ++layer) {
      const auto adjacent = neighbors(index, node, layer);
      mix(hash, node);
      mix(hash, static_cast<std::uint64_t>(layer));
      mix(hash, adjacent.size());
      for (const auto target : adjacent) mix(hash, target);
    }
  }
  return hash;
}

struct Inspection {
  bool valid_ids{true};
  bool no_self_loops{true};
  bool no_duplicates{true};
  bool degree_cap{true};
  bool labels_complete{true};
  std::vector<hnswlib::tableint> bfs;
};

Inspection inspect(const Index& index) {
  Inspection result;
  const auto count = index.cur_element_count.load();
  std::vector<std::vector<hnswlib::tableint>> graph(count);
  for (hnswlib::tableint node = 0; node < count; ++node) {
    graph[node] = neighbors(index, node);
    result.degree_cap = result.degree_cap && graph[node].size() <= index.maxM0_;
    std::set<hnswlib::tableint> unique;
    for (const auto target : graph[node]) {
      result.valid_ids = result.valid_ids && target < count;
      result.no_self_loops = result.no_self_loops && target != node;
      result.no_duplicates = result.no_duplicates && unique.insert(target).second;
    }
    const auto label = index.getExternalLabel(node);
    result.labels_complete = result.labels_complete && label < count;
  }
  result.labels_complete = result.labels_complete && index.label_lookup_.size() == count;
  for (std::size_t label = 0; label < count; ++label) {
    result.labels_complete = result.labels_complete && index.label_lookup_.count(label) == 1;
  }
  if (count == 0 || index.enterpoint_node_ >= count) return result;
  std::vector<char> seen(count, 0);
  std::queue<hnswlib::tableint> queue;
  queue.push(index.enterpoint_node_);
  seen[index.enterpoint_node_] = 1;
  while (!queue.empty()) {
    const auto node = queue.front();
    queue.pop();
    result.bfs.push_back(node);
    for (const auto target : graph[node]) {
      if (target < count && !seen[target]) {
        seen[target] = 1;
        queue.push(target);
      }
    }
  }
  return result;
}

using Result = std::vector<std::pair<float, hnswlib::labeltype>>;

Result canonical(
    std::priority_queue<std::pair<float, hnswlib::labeltype>> queue) {
  Result result;
  while (!queue.empty()) {
    result.push_back(queue.top());
    queue.pop();
  }
  std::sort(result.begin(), result.end(), [](const auto& left, const auto& right) {
    if (left.first != right.first) return left.first < right.first;
    return left.second < right.second;
  });
  return result;
}

bool exact_equal(const Result& left, const Result& right) {
  if (left.size() != right.size()) return false;
  for (std::size_t index = 0; index < left.size(); ++index) {
    if (left[index].first != right[index].first || left[index].second != right[index].second)
      return false;
  }
  return true;
}

std::string labels_string(const Result& result) {
  std::string text;
  for (std::size_t index = 0; index < result.size(); ++index) {
    if (index) text.push_back(';');
    text += std::to_string(result[index].second);
  }
  return text;
}

std::vector<std::string> split_simple_csv(const std::string& line) {
  std::vector<std::string> fields;
  std::stringstream stream(line);
  std::string field;
  while (std::getline(stream, field, ',')) fields.push_back(field);
  return fields;
}

std::vector<hnswlib::labeltype> parse_labels(const std::string& raw) {
  std::vector<hnswlib::labeltype> labels;
  std::stringstream stream(raw);
  std::string token;
  while (std::getline(stream, token, ';')) {
    if (!token.empty()) labels.push_back(static_cast<hnswlib::labeltype>(std::stoull(token)));
  }
  return labels;
}

std::vector<std::vector<hnswlib::labeltype>> read_truth_labels(
    const std::filesystem::path& path) {
  std::ifstream input(path);
  if (!input) throw std::runtime_error("cannot open truth CSV: " + path.string());
  std::string line;
  if (!std::getline(input, line) ||
      line != "query_row,truth_acquisition_ndc,truth_acquisition_wall_clock_ns,"
              "boundary_distance_tie,truth_labels")
    throw std::runtime_error("unexpected truth CSV header");
  std::vector<std::vector<hnswlib::labeltype>> truth;
  while (std::getline(input, line)) {
    const auto fields = split_simple_csv(line);
    if (fields.size() != 5 || std::stoull(fields[0]) != truth.size())
      throw std::runtime_error("invalid truth CSV row");
    auto labels = parse_labels(fields[4]);
    if (labels.size() != 10 || std::set<hnswlib::labeltype>(labels.begin(), labels.end()).size() != 10)
      throw std::runtime_error("truth row is not an exact unique top-10");
    truth.push_back(std::move(labels));
  }
  return truth;
}

float scalar_l2(const float* left, const float* right, std::size_t dimensions) {
  float result = 0.0F;
  for (std::size_t index = 0; index < dimensions; ++index) {
    const float delta = left[index] - right[index];
    result += delta * delta;
  }
  return result;
}

struct LeanTrace {
  std::priority_queue<std::pair<float, hnswlib::labeltype>> results;
  std::size_t base_expansions{};
  std::size_t visited_count{};
};

using InternalQueue =
    std::priority_queue<std::pair<float, hnswlib::tableint>,
                        std::vector<std::pair<float, hnswlib::tableint>>,
                        Index::CompareByFirst>;

float query_distance(const Index& index, const void* query, hnswlib::tableint node) {
  return index.fstdistfunc_(query, index.getDataByInternalId(node), index.dist_func_param_);
}

LeanTrace lean_search(const Index& index, const void* query, std::size_t k, std::size_t ef) {
  if (index.cur_element_count.load() == 0) return {};
  auto current = index.enterpoint_node_;
  float current_distance = query_distance(index, query, current);
  for (int layer = index.maxlevel_; layer > 0; --layer) {
    bool changed = true;
    while (changed) {
      changed = false;
      for (const auto candidate : neighbors(index, current, layer)) {
        const float candidate_distance = query_distance(index, query, candidate);
        if (candidate_distance < current_distance) {
          current_distance = candidate_distance;
          current = candidate;
          changed = true;
        }
      }
    }
  }

  const std::size_t search_ef = std::max(ef, k);
  InternalQueue top_candidates;
  InternalQueue candidate_set;
  const float entry_distance = query_distance(index, query, current);
  float lower_bound = entry_distance;
  top_candidates.emplace(entry_distance, current);
  candidate_set.emplace(-entry_distance, current);
  std::vector<std::uint8_t> visited(index.cur_element_count.load(), 0);
  visited[current] = 1;
  std::size_t visited_count = 1;
  std::size_t expansions = 0;
  while (!candidate_set.empty()) {
    const auto current_pair = candidate_set.top();
    const float candidate_distance = -current_pair.first;
    if (candidate_distance > lower_bound) break;
    candidate_set.pop();
    ++expansions;
    for (const auto neighbor : neighbors(index, current_pair.second)) {
      if (visited[neighbor]) continue;
      visited[neighbor] = 1;
      ++visited_count;
      const float neighbor_distance = query_distance(index, query, neighbor);
      if (top_candidates.size() < search_ef || lower_bound > neighbor_distance) {
        candidate_set.emplace(-neighbor_distance, neighbor);
        top_candidates.emplace(neighbor_distance, neighbor);
        if (top_candidates.size() > search_ef) top_candidates.pop();
        if (!top_candidates.empty()) lower_bound = top_candidates.top().first;
      }
    }
  }
  while (top_candidates.size() > k) top_candidates.pop();
  LeanTrace trace;
  trace.base_expansions = expansions;
  trace.visited_count = visited_count;
  while (!top_candidates.empty()) {
    const auto result = top_candidates.top();
    trace.results.emplace(result.first, index.getExternalLabel(result.second));
    top_candidates.pop();
  }
  return trace;
}

std::vector<std::size_t> parse_efs(const std::string& raw) {
  std::vector<std::size_t> values;
  std::stringstream stream(raw);
  std::string token;
  while (std::getline(stream, token, ',')) values.push_back(std::stoull(token));
  if (values.empty()) throw std::runtime_error("empty ef grid");
  return values;
}

int command_build(int argc, char** argv) {
  if (argc != 8)
    throw std::runtime_error("usage: runner build BASE ORDER DIM SEED INDEX META");
  const auto base = read_matrix(argv[2]);
  const auto order = read_order(argv[3]);
  const auto dimensions = static_cast<std::size_t>(std::stoull(argv[4]));
  const auto seed = static_cast<std::size_t>(std::stoull(argv[5]));
  if (base.rows != 100000 || base.columns != dimensions || order.size() != base.rows)
    throw std::runtime_error("build input shape mismatch");
  std::vector<char> seen(base.rows, 0);
  for (const auto label : order) {
    if (label >= base.rows || seen[label]) throw std::runtime_error("invalid insertion order");
    seen[label] = 1;
  }
  CountingL2Space space(dimensions);
  Index index(&space, base.rows, 16, 100, seed);
  const auto started = std::chrono::steady_clock::now();
  for (const auto label : order)
    index.addPoint(base.values.data() + static_cast<std::size_t>(label) * dimensions, label);
  const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(
                           std::chrono::steady_clock::now() - started)
                           .count();
  index.saveIndex(argv[6]);
  struct rusage usage {};
  getrusage(RUSAGE_SELF, &usage);
  std::ofstream meta(argv[7]);
  if (!meta) throw std::runtime_error("cannot write build metadata");
  write_key(meta, "status", "PASS");
  write_key(meta, "rows", base.rows);
  write_key(meta, "dimensions", base.columns);
  write_key(meta, "seed", seed);
  write_key(meta, "M", 16);
  write_key(meta, "efConstruction", 100);
  write_key(meta, "build_threads", 1);
  write_key(meta, "build_time_ns", elapsed);
  write_key(meta, "build_distance_computations", space.count());
  write_key(meta, "peak_rss_kib", usage.ru_maxrss);
  write_key(meta, "entry_point", index.enterpoint_node_);
  write_key(meta, "max_level", index.maxlevel_);
  return 0;
}

int command_inspect(int argc, char** argv) {
  if (argc != 8)
    throw std::runtime_error("usage: runner inspect INDEX DIM CONNECTIVITY ROUNDTRIP META EXPECTED");
  const auto dimensions = static_cast<std::size_t>(std::stoull(argv[3]));
  const auto expected = static_cast<std::size_t>(std::stoull(argv[7]));
  CountingL2Space space(dimensions);
  Index index(&space, argv[2], false);
  const auto first = inspect(index);
  index.saveIndex(argv[5]);
  Index reloaded(&space, argv[5], false);
  const auto second = inspect(reloaded);
  const auto first_hash = graph_hash(index);
  const auto second_hash = graph_hash(reloaded);
  const bool count_ok = index.cur_element_count.load() == expected &&
                        index.max_elements_ == expected && reloaded.cur_element_count.load() == expected;
  const bool deletion_ok = index.num_deleted_.load() == 0 && reloaded.num_deleted_.load() == 0;
  const bool connectivity_ok = first.bfs.size() == expected && second.bfs == first.bfs;
  const bool graph_replay = first_hash == second_hash;
  std::ofstream connectivity(argv[4], std::ios::binary);
  const auto traversal_count = static_cast<std::uint64_t>(first.bfs.size());
  connectivity.write(reinterpret_cast<const char*>(&traversal_count), sizeof(traversal_count));
  connectivity.write(reinterpret_cast<const char*>(first.bfs.data()),
                     static_cast<std::streamsize>(first.bfs.size() * sizeof(hnswlib::tableint)));
  std::ofstream meta(argv[6]);
  write_key(meta, "status", count_ok && deletion_ok && connectivity_ok && graph_replay &&
                                    first.valid_ids && first.no_self_loops && first.no_duplicates &&
                                    first.degree_cap && first.labels_complete
                                ? "PASS"
                                : "FAIL");
  write_key(meta, "current_count", index.cur_element_count.load());
  write_key(meta, "max_elements", index.max_elements_);
  write_key(meta, "num_deleted", index.num_deleted_.load());
  write_key(meta, "entry_point", index.enterpoint_node_);
  write_key(meta, "directed_reachable_count", first.bfs.size());
  write_key(meta, "valid_ids", first.valid_ids);
  write_key(meta, "no_self_loops", first.no_self_loops);
  write_key(meta, "no_duplicates", first.no_duplicates);
  write_key(meta, "degree_cap", first.degree_cap);
  write_key(meta, "labels_complete", first.labels_complete);
  write_key(meta, "graph_hash_fnv64", first_hash);
  write_key(meta, "roundtrip_graph_hash_fnv64", second_hash);
  write_key(meta, "roundtrip_graph_equal", graph_replay);
  write_key(meta, "roundtrip_connectivity_equal", second.bfs == first.bfs);
  return count_ok && deletion_ok && connectivity_ok && graph_replay && first.valid_ids &&
                 first.no_self_loops && first.no_duplicates && first.degree_cap &&
                 first.labels_complete
             ? 0
             : 1;
}

int command_design(int argc, char** argv) {
  if (argc != 9)
    throw std::runtime_error("usage: runner design INDEX BASE QUERIES DIM EF CSV META");
  const auto base = read_matrix(argv[3]);
  const auto queries = read_matrix(argv[4]);
  const auto dimensions = static_cast<std::size_t>(std::stoull(argv[5]));
  const auto ef = static_cast<std::size_t>(std::stoull(argv[6]));
  if (base.rows != 100000 || base.columns != dimensions || queries.columns != dimensions ||
      ef != base.rows)
    throw std::runtime_error("design input shape or ef mismatch");
  CountingL2Space space(dimensions);
  Index index(&space, argv[2], false);
  CountingL2Space replay_space(dimensions);
  Index replay(&replay_space, argv[2], false);
  index.setEf(ef);
  replay.setEf(ef);
  std::ofstream csv(argv[7]);
  csv << "query_row,requested_ef,native_ndc,tracer_ndc,replay_ndc,actual_expansions,"
         "visited_count,wall_clock_ns,"
         "native_tracer_topk_equal,native_tracer_ndc_equal,native_bruteforce_exact_topk,"
         "replay_topk_equal,replay_ndc_equal,boundary_distance_tie,native_labels,"
         "tracer_labels,bruteforce_labels,replay_labels\n";
  bool all_pass = true;
  for (std::size_t query_row = 0; query_row < queries.rows; ++query_row) {
    const float* query = queries.values.data() + query_row * dimensions;
    space.reset();
    const auto started = std::chrono::steady_clock::now();
    const auto native_queue = index.searchKnn(query, 10);
    const auto wall = std::chrono::duration_cast<std::chrono::nanoseconds>(
                          std::chrono::steady_clock::now() - started)
                          .count();
    const auto native_ndc = space.count();
    const auto native = canonical(native_queue);
    space.reset();
    const auto traced_raw = lean_search(index, query, 10, ef);
    const auto tracer_ndc = space.count();
    const auto traced = canonical(traced_raw.results);
    space.reset();
    Result all;
    all.reserve(base.rows);
    for (std::size_t label = 0; label < base.rows; ++label) {
      const auto distance = index.fstdistfunc_(
          query, base.values.data() + label * dimensions, index.dist_func_param_);
      all.emplace_back(distance, label);
    }
    std::sort(all.begin(), all.end(), [](const auto& left, const auto& right) {
      if (left.first != right.first) return left.first < right.first;
      return left.second < right.second;
    });
    const bool boundary_tie = all.size() > 10 && all[9].first == all[10].first;
    Result brute(all.begin(), all.begin() + 10);
    const bool topk_equal = exact_equal(native, traced);
    const bool ndc_equal = native_ndc == tracer_ndc;
    const bool exact_topk = exact_equal(native, brute);
    replay_space.reset();
    const auto replay_result = canonical(replay.searchKnn(query, 10));
    const auto replay_ndc = replay_space.count();
    const bool replay_topk_equal = exact_equal(native, replay_result);
    const bool replay_ndc_equal = native_ndc == replay_ndc;
    const bool expansions_full = traced_raw.base_expansions == base.rows;
    const bool visited_full = traced_raw.visited_count == base.rows;
    all_pass = all_pass && topk_equal && ndc_equal && exact_topk && replay_topk_equal &&
               replay_ndc_equal && expansions_full && visited_full;
    csv << query_row << ',' << ef << ',' << native_ndc << ',' << tracer_ndc << ','
        << replay_ndc << ',' << traced_raw.base_expansions << ',' << traced_raw.visited_count
        << ',' << wall << ',' << topk_equal << ',' << ndc_equal << ',' << exact_topk << ','
        << replay_topk_equal << ',' << replay_ndc_equal << ',' << boundary_tie << ','
        << labels_string(native) << ',' << labels_string(traced) << ','
        << labels_string(brute) << ',' << labels_string(replay_result) << '\n';
  }
  std::ofstream meta(argv[8]);
  write_key(meta, "status", all_pass ? "PASS" : "FAIL");
  write_key(meta, "queries", queries.rows);
  write_key(meta, "requested_ef", ef);
  write_key(meta, "native_tracer_topk_all_equal", all_pass);
  write_key(meta, "native_tracer_ndc_all_equal", all_pass);
  write_key(meta, "native_bruteforce_exact_top10_all_equal", all_pass);
  write_key(meta, "native_save_load_replay_all_equal", all_pass);
  write_key(meta, "full_expansion_all_queries", all_pass);
  return all_pass ? 0 : 1;
}

int command_equivalence(int argc, char** argv) {
  if (argc != 8)
    throw std::runtime_error("usage: runner equivalence INDEX QUERIES DIM EFS CSV META");
  const auto queries = read_matrix(argv[3]);
  const auto dimensions = static_cast<std::size_t>(std::stoull(argv[4]));
  const auto efs = parse_efs(argv[5]);
  if (queries.columns != dimensions) throw std::runtime_error("equivalence shape mismatch");
  CountingL2Space space(dimensions);
  Index index(&space, argv[2], false);
  std::ofstream csv(argv[6]);
  csv << "query_row,requested_ef,native_ndc,tracer_ndc,actual_expansions,visited_count,"
         "native_tracer_topk_equal,native_tracer_ndc_equal\n";
  bool all_pass = true;
  std::size_t rows = 0;
  for (std::size_t query_row = 0; query_row < queries.rows; ++query_row) {
    const float* query = queries.values.data() + query_row * dimensions;
    for (const auto ef : efs) {
      index.setEf(ef);
      space.reset();
      const auto native = canonical(index.searchKnn(query, 10));
      const auto native_ndc = space.count();
      space.reset();
      const auto traced_raw = lean_search(index, query, 10, ef);
      const auto tracer_ndc = space.count();
      const auto traced = canonical(traced_raw.results);
      const bool topk_equal = exact_equal(native, traced);
      const bool ndc_equal = native_ndc == tracer_ndc;
      all_pass = all_pass && topk_equal && ndc_equal;
      ++rows;
      csv << query_row << ',' << ef << ',' << native_ndc << ',' << tracer_ndc << ','
          << traced_raw.base_expansions << ',' << traced_raw.visited_count << ','
          << topk_equal << ',' << ndc_equal << '\n';
    }
  }
  std::ofstream meta(argv[7]);
  write_key(meta, "status", all_pass ? "PASS" : "FAIL");
  write_key(meta, "queries", queries.rows);
  write_key(meta, "ef_count", efs.size());
  write_key(meta, "rows", rows);
  write_key(meta, "native_tracer_topk_all_equal", all_pass);
  write_key(meta, "native_tracer_ndc_all_equal", all_pass);
  return all_pass ? 0 : 1;
}

int command_truth(int argc, char** argv) {
  if (argc != 7)
    throw std::runtime_error("usage: runner truth BASE QUERIES DIM CSV META");
  const auto base = read_matrix(argv[2]);
  const auto queries = read_matrix(argv[3]);
  const auto dimensions = static_cast<std::size_t>(std::stoull(argv[4]));
  if (base.rows != 100000 || base.columns != dimensions || queries.columns != dimensions)
    throw std::runtime_error("truth input shape mismatch");
  std::ofstream csv(argv[5]);
  if (!csv) throw std::runtime_error("cannot write truth CSV");
  csv << "query_row,truth_acquisition_ndc,truth_acquisition_wall_clock_ns,"
         "boundary_distance_tie,truth_labels\n";
  std::uint64_t total_wall_ns = 0;
  std::size_t boundary_ties = 0;
  for (std::size_t query_row = 0; query_row < queries.rows; ++query_row) {
    const float* query = queries.values.data() + query_row * dimensions;
    const auto started = std::chrono::steady_clock::now();
    Result all;
    all.reserve(base.rows);
    for (std::size_t label = 0; label < base.rows; ++label) {
      all.emplace_back(
          scalar_l2(query, base.values.data() + label * dimensions, dimensions), label);
    }
    std::sort(all.begin(), all.end(), [](const auto& left, const auto& right) {
      if (left.first != right.first) return left.first < right.first;
      return left.second < right.second;
    });
    const auto wall_ns = static_cast<std::uint64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now() - started)
            .count());
    total_wall_ns += wall_ns;
    const bool boundary_tie = all[9].first == all[10].first;
    boundary_ties += boundary_tie;
    const Result exact(all.begin(), all.begin() + 10);
    csv << query_row << ',' << base.rows << ',' << wall_ns << ',' << boundary_tie << ','
        << labels_string(exact) << '\n';
  }
  std::ofstream meta(argv[6]);
  if (!meta) throw std::runtime_error("cannot write truth metadata");
  write_key(meta, "status", "PASS");
  write_key(meta, "queries", queries.rows);
  write_key(meta, "base_rows", base.rows);
  write_key(meta, "truth_acquisition_ndc_per_query", base.rows);
  write_key(meta, "truth_acquisition_total_ndc", base.rows * queries.rows);
  write_key(meta, "truth_acquisition_total_wall_clock_ns", total_wall_ns);
  write_key(meta, "boundary_distance_ties", boundary_ties);
  write_key(meta, "tie_rule", "distance_then_label");
  return 0;
}

int command_sentinel(int argc, char** argv) {
  if (argc != 8)
    throw std::runtime_error("usage: runner sentinel INDEX QUERIES DIM EFS TRUTH CSV");
  const auto queries = read_matrix(argv[3]);
  const auto dimensions = static_cast<std::size_t>(std::stoull(argv[4]));
  const auto efs = parse_efs(argv[5]);
  const auto truth = read_truth_labels(argv[6]);
  if (queries.columns != dimensions || truth.size() != queries.rows)
    throw std::runtime_error("sentinel input shape or truth-count mismatch");
  CountingL2Space space(dimensions);
  Index index(&space, argv[2], false);
  if (index.cur_element_count.load() != 100000 || index.num_deleted_.load() != 0)
    throw std::runtime_error("sentinel index count/deletion gate failed");
  std::ofstream csv(argv[7]);
  if (!csv) throw std::runtime_error("cannot write sentinel CSV");
  auto meta_path = std::filesystem::path(argv[7]);
  meta_path.replace_extension(".meta");
  csv << "query_row,requested_ef,raw_recall_at_10,Z_abs,native_ndc,tracer_ndc,"
         "actual_expansions,visited_count,wall_clock_ns,endpoint_status,"
         "native_tracer_topk_equal,native_tracer_ndc_equal,native_labels\n";
  bool instrumentation_valid = true;
  std::size_t endpoint_failures = 0;
  std::size_t rows = 0;
  for (std::size_t query_row = 0; query_row < queries.rows; ++query_row) {
    const float* query = queries.values.data() + query_row * dimensions;
    const std::set<hnswlib::labeltype> exact(truth[query_row].begin(), truth[query_row].end());
    for (const auto ef : efs) {
      ++rows;
      const auto action_started = std::chrono::steady_clock::now();
      std::uint64_t charged_ndc = 0;
      try {
        index.setEf(ef);
        space.reset();
        const auto native = canonical(index.searchKnn(query, 10));
        const auto wall_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                                 std::chrono::steady_clock::now() - action_started)
                                 .count();
        const auto native_ndc = space.count();
        charged_ndc = native_ndc;
        space.reset();
        const auto traced_raw = lean_search(index, query, 10, ef);
        const auto tracer_ndc = space.count();
        const auto traced = canonical(traced_raw.results);
        const bool topk_equal = exact_equal(native, traced);
        const bool ndc_equal = native_ndc == tracer_ndc;
        instrumentation_valid = instrumentation_valid && topk_equal && ndc_equal;
        std::size_t matches = 0;
        for (const auto& item : native) matches += exact.count(item.second);
        const double recall = static_cast<double>(matches) / 10.0;
        const bool endpoint_ok = native.size() == 10;
        endpoint_failures += !endpoint_ok;
        const bool failure = recall < 0.90 || !endpoint_ok;
        csv << query_row << ',' << ef << ',' << std::fixed << std::setprecision(6) << recall
            << ',' << failure << ',' << native_ndc << ',' << tracer_ndc << ','
            << traced_raw.base_expansions << ',' << traced_raw.visited_count << ',' << wall_ns
            << ',' << (endpoint_ok ? "PASS" : "INFEASIBLE_TOPK_SIZE") << ',' << topk_equal
            << ',' << ndc_equal << ',' << labels_string(native) << '\n';
      } catch (const std::exception&) {
        ++endpoint_failures;
        const auto wall_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                                 std::chrono::steady_clock::now() - action_started)
                                 .count();
        if (charged_ndc == 0) charged_ndc = space.count();
        csv << query_row << ',' << ef << ",0.000000,1," << charged_ndc
            << ",0,0,0," << wall_ns << ",EXECUTION_FAILURE,0,0,\n";
      }
    }
  }
  std::ofstream meta(meta_path);
  if (!meta) throw std::runtime_error("cannot write sentinel metadata");
  write_key(meta, "status", instrumentation_valid ? "PASS" : "INVALID_CIBS_NDC_INSTRUMENTATION");
  write_key(meta, "queries", queries.rows);
  write_key(meta, "ef_count", efs.size());
  write_key(meta, "rows", rows);
  write_key(meta, "endpoint_failures", endpoint_failures);
  write_key(meta, "native_tracer_topk_all_successes_equal", instrumentation_valid);
  write_key(meta, "native_tracer_ndc_all_successes_equal", instrumentation_valid);
  return instrumentation_valid ? 0 : 1;
}
}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc < 2) throw std::runtime_error("missing command");
    const std::string command = argv[1];
    if (command == "build") return command_build(argc, argv);
    if (command == "inspect") return command_inspect(argc, argv);
    if (command == "design") return command_design(argc, argv);
    if (command == "equivalence") return command_equivalence(argc, argv);
    if (command == "truth") return command_truth(argc, argv);
    if (command == "sentinel") return command_sentinel(argc, argv);
    throw std::runtime_error("unknown command: " + command);
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
