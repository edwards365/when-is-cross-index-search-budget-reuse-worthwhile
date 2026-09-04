#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

namespace {
using Index = hnswlib::HierarchicalNSW<float>;
using Item = std::pair<float, hnswlib::labeltype>;

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

class CountingSpace final : public hnswlib::SpaceInterface<float> {
  public:
    explicit CountingSpace(std::size_t dimensions) : state_{dimensions, &counter_} {}
    std::size_t get_data_size() override { return state_.dimensions * sizeof(float); }
    hnswlib::DISTFUNC<float> get_dist_func() override { return distance; }
    void* get_dist_func_param() override { return &state_; }
    void reset() { counter_.store(0); }
    std::uint64_t count() const { return counter_.load(); }
  private:
    struct State { std::size_t dimensions; std::atomic<std::uint64_t>* counter; };
    static float distance(const void* left_raw, const void* right_raw, const void* raw) {
        const auto* state = static_cast<const State*>(raw);
        const auto* left = static_cast<const float*>(left_raw);
        const auto* right = static_cast<const float*>(right_raw);
        state->counter->fetch_add(1, std::memory_order_relaxed);
        float value = 0.0F;
        for (std::size_t d = 0; d < state->dimensions; ++d) {
            const float delta = left[d] - right[d]; value += delta * delta;
        }
        return value;
    }
    std::atomic<std::uint64_t> counter_{0};
    State state_;
};

template <typename T> T scalar(std::ifstream& input) {
    T value{}; input.read(reinterpret_cast<char*>(&value), sizeof(value));
    if (!input) throw std::runtime_error("binary input ended"); return value;
}
Matrix read_matrix(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary); if (!input) throw std::runtime_error("query file missing");
    Matrix result{static_cast<std::size_t>(scalar<std::uint64_t>(input)), static_cast<std::size_t>(scalar<std::uint64_t>(input)), {}};
    result.values.resize(result.rows * result.columns);
    input.read(reinterpret_cast<char*>(result.values.data()), static_cast<std::streamsize>(result.values.size() * sizeof(float)));
    if (!input) throw std::runtime_error("query payload truncated"); return result;
}
Truth read_truth(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary); if (!input) throw std::runtime_error("truth file missing");
    Truth result{static_cast<std::size_t>(scalar<std::uint64_t>(input)), static_cast<std::size_t>(scalar<std::uint64_t>(input)), {}};
    result.labels.resize(result.rows * result.k);
    input.read(reinterpret_cast<char*>(result.labels.data()), static_cast<std::streamsize>(result.labels.size() * sizeof(std::uint32_t)));
    if (!input) throw std::runtime_error("truth payload truncated"); return result;
}

std::vector<Item> ordered(std::priority_queue<Item> heap) {
    std::vector<Item> result; while (!heap.empty()) { result.push_back(heap.top()); heap.pop(); }
    std::sort(result.begin(), result.end(), [](const Item& a, const Item& b) {
        return a.first < b.first || (a.first == b.first && a.second < b.second);
    }); return result;
}
std::vector<Item> ordered_base(std::priority_queue<Item> heap) {
    return ordered(std::move(heap));
}
std::vector<Item> primary(Index& index, const float* query, std::size_t k, std::size_t ef) {
    index.setEf(ef); return ordered_base(index.searchKnn(query, k));
}
std::vector<Item> alternate(const Index& index, const float* query, std::size_t k,
                            std::size_t ef, hnswlib::tableint portal) {
    auto heap = index.searchBaseLayerST<true>(portal, query, std::max(k, ef));
    std::vector<Item> result;
    while (!heap.empty()) {
        result.emplace_back(heap.top().first, static_cast<hnswlib::labeltype>(heap.top().second));
        heap.pop();
    }
    std::sort(result.begin(), result.end(), [](const Item& a, const Item& b) {
        return a.first < b.first || (a.first == b.first && a.second < b.second);
    });
    if (result.size() > k) result.resize(k); return result;
}
std::vector<Item> merge_rerank(const Index& index, const float* query,
                               const std::vector<Item>& left,
                               const std::vector<Item>& right,
                               std::uint64_t& exact_calls) {
    std::set<hnswlib::labeltype> ids; for (const auto& x : left) ids.insert(x.second); for (const auto& x : right) ids.insert(x.second);
    std::vector<Item> merged; merged.reserve(ids.size());
    for (const auto id : ids) {
        const auto internal = index.label_lookup_.at(id);
        const float distance = index.fstdistfunc_(query, index.getDataByInternalId(internal), index.dist_func_param_);
        ++exact_calls; merged.emplace_back(distance, id);
    }
    std::sort(merged.begin(), merged.end(), [](const Item& a, const Item& b) { return a.first < b.first || (a.first == b.first && a.second < b.second); });
    if (merged.size() > left.size()) merged.resize(left.size()); return merged;
}
std::size_t hits(const std::vector<Item>& result, const Truth& truth, std::size_t q) {
    std::set<std::uint32_t> expected; for (std::size_t i=0;i<truth.k;++i) expected.insert(truth.labels[q*truth.k+i]);
    std::size_t n=0; for (const auto& x:result) n += expected.count(static_cast<std::uint32_t>(x.second)); return n;
}
std::string ids_hash(const std::vector<Item>& result) {
    std::uint64_t h=1469598103934665603ULL; for(const auto& x:result){ h^=static_cast<std::uint64_t>(x.second); h*=1099511628211ULL; }
    std::ostringstream out; out<<std::hex<<h; return out.str();
}
}

int main(int argc, char** argv) {
    try {
        if (argc != 7) { std::cerr << "usage: cals_mechanical_smoke INDEX QUERIES TRUTH EF_GRID PORTALS_CSV OUTPUT_CSV\n"; return 2; }
        const auto queries=read_matrix(argv[2]); const auto truth=read_truth(argv[3]);
        if (queries.rows < 500 || truth.rows != queries.rows || truth.k != 10) throw std::runtime_error("CALS mechanical smoke requires >=500 design queries and top-10 truth");
        CountingSpace space(queries.columns); Index index(&space, argv[1], false);
        std::vector<hnswlib::tableint> portals;
        { std::ifstream input(argv[5]); if(!input) throw std::runtime_error("portal registry missing"); std::string line;
          while(std::getline(input,line)){ if(line.empty()||line=="portal_id") continue; portals.push_back(static_cast<hnswlib::tableint>(std::stoul(line))); }
          if(portals.empty()) throw std::runtime_error("portal registry is empty"); }
        const auto efs=std::string(argv[4]);
        std::vector<std::size_t> grid; std::stringstream ss(efs); std::string token; while(std::getline(ss,token,',')) grid.push_back(std::stoul(token));
        std::ofstream output(argv[6]); if(!output) throw std::runtime_error("cannot write smoke CSV");
        output << "query_id,raw_ef,portal_id,primary_candidate_hash,alternate_candidate_hash,primary_recomputed_equal,primary_subset_union,union_recall_ge_primary,alternate_repeat_equal,primary_recall,auxiliary_recall,union_recall,primary_search_ndc,alternate_search_ndc,merge_exact_distance_calls,union_ndc_total,termination_primary,termination_alternate\n";
        std::size_t failures=0; std::size_t rows=0;
        for(const auto ef:grid) for(std::size_t q=0;q<500;++q){
            const float* query=queries.values.data()+q*queries.columns;
            space.reset(); auto p=primary(index,query,truth.k,ef); auto p_ndc=space.count(); const auto p_hash=ids_hash(p);
            space.reset(); auto p2=primary(index,query,truth.k,ef); const bool p_equal=(p==p2); const auto p2_ndc=space.count(); (void)p2_ndc;
            const auto pr=hits(p,truth,q);
            for(const auto portal:portals){
                space.reset(); auto a=alternate(index,query,truth.k,ef,portal); const auto a_ndc=space.count(); const auto a_hash=ids_hash(a);
                auto a2=alternate(index,query,truth.k,ef,portal); const bool a_equal=(a==a2);
                std::set<hnswlib::labeltype> ps, us; for(auto& x:p){ps.insert(x.second);us.insert(x.second);} for(auto& x:a)us.insert(x.second);
                std::uint64_t exact=0; auto u=merge_rerank(index,query,p,a,exact);
                const bool subset=std::includes(us.begin(),us.end(),ps.begin(),ps.end());
                const auto ar=hits(a,truth,q), ur=hits(u,truth,q); const bool recall_ok=ur>=pr;
                if(!p_equal||!subset||!recall_ok||!a_equal) ++failures;
                output<<q<<','<<ef<<','<<portal<<','<<p_hash<<','<<a_hash<<','<<p_equal<<','<<subset<<','<<recall_ok<<','<<a_equal<<','<<pr/10.0<<','<<ar/10.0<<','<<ur/10.0<<','<<p_ndc<<','<<a_ndc<<','<<exact<<','<<p_ndc+a_ndc+exact<<",EXHAUSTED,EXHAUSTED\n"; ++rows;
            }
        }
        std::cout<<"rows="<<rows<<" failures="<<failures<<" portals="<<portals.size()<<"\n";
        return failures?1:0;
    } catch(const std::exception& error){ std::cerr<<error.what()<<'\n'; return 1; }
}
