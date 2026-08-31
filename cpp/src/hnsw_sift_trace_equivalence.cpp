#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_query_tracer.hpp"
#include <algorithm>
#include <atomic>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
class CountingL2Space final : public hnswlib::SpaceInterface<float> {
 public:
  explicit CountingL2Space(std::size_t d) : state_{d, &counter_} {}
  std::size_t get_data_size() override { return state_.d * sizeof(float); }
  hnswlib::DISTFUNC<float> get_dist_func() override { return distance; }
  void* get_dist_func_param() override { return &state_; }
  void reset() { counter_.store(0); }
  long count() const { return counter_.load(); }
 private:
  struct State { std::size_t d; std::atomic<long>* counter; };
  static float distance(const void* a0, const void* b0, const void* s0) {
    const auto* s=static_cast<const State*>(s0); const auto* a=static_cast<const float*>(a0); const auto* b=static_cast<const float*>(b0);
    s->counter->fetch_add(1,std::memory_order_relaxed); float result=0;
    for(std::size_t i=0;i<s->d;++i){const float x=a[i]-b[i];result+=x*x;} return result;
  }
  std::atomic<long> counter_{0}; State state_;
};
template<class T>T scalar(std::ifstream& in){T v{};in.read(reinterpret_cast<char*>(&v),sizeof(v));if(!in)throw std::runtime_error("short input");return v;}
struct Matrix{std::size_t rows{},cols{};std::vector<float> data;};
Matrix matrix(const std::filesystem::path& p){std::ifstream in(p,std::ios::binary);if(!in)throw std::runtime_error("cannot open queries");Matrix m;m.rows=scalar<std::uint64_t>(in);m.cols=scalar<std::uint64_t>(in);m.data.resize(m.rows*m.cols);in.read(reinterpret_cast<char*>(m.data.data()),m.data.size()*sizeof(float));if(!in)throw std::runtime_error("short payload");return m;}
std::set<std::size_t> labels(std::priority_queue<std::pair<float,hnswlib::labeltype>> h){std::set<std::size_t> r;while(!h.empty()){r.insert(h.top().second);h.pop();}return r;}
std::vector<std::size_t> parse_efs(const std::string& raw){std::vector<std::size_t> r;std::stringstream s(raw);std::string t;while(std::getline(s,t,','))r.push_back(std::stoul(t));return r;}
void header(std::ofstream& o){o<<"query_id,build_id,source_target_id,requested_ef,actual_expansions,actual_ndc,wall_clock_ns,upper_layer_path,base_layer_expansion_order,candidate_queue_insertion_order,introduction_parent_edge,composite_priority_key,top_candidate_heap_state,lower_bound_change,visited_state,first_safe_discovery,endpoint_status,checkpoint_top_k,checkpoint_candidate_set,backup_path,edge_layer,tie_event,filter_deletion_state,search_stop_reason\n";}
template<class C>void row(std::ofstream& o,const C& c){o<<c.query_id<<",\""<<c.build_id<<"\",\""<<c.source_target_id<<"\","<<c.requested_ef<<','<<c.actual_expansions<<','<<c.actual_ndc<<','<<c.wall_clock_ns<<",\""<<c.upper_layer_path<<"\",\""<<c.base_layer_expansion_order<<"\",\""<<c.candidate_queue_insertion_order<<"\",\""<<c.introduction_parent_edge<<"\",\""<<c.composite_priority_key<<"\",\""<<c.top_candidate_heap_state<<"\",\""<<c.lower_bound_change<<"\",\""<<c.visited_state<<"\",\""<<c.first_safe_discovery<<"\",\""<<c.endpoint_status<<"\",\""<<c.checkpoint_top_k<<"\",\""<<c.checkpoint_candidate_set<<"\",\""<<c.backup_path<<"\",\""<<c.edge_layer<<"\",\""<<c.tie_event<<"\",\""<<c.filter_deletion_state<<"\",\""<<c.search_stop_reason<<"\"\n";}
}
int main(int argc,char** argv){try{
 if(argc!=9){std::cerr<<"usage: INDEX QUERIES EFS LIMIT SUMMARY CONTRACT BUILD_ID SOURCE_TARGET\n";return 2;}
 auto q=matrix(argv[2]);auto grid=parse_efs(argv[3]);auto limit=std::min(q.rows,std::stoul(argv[4]));CountingL2Space space(q.cols);hnswlib::HierarchicalNSW<float> index(&space,argv[1],false);
 std::ofstream summary(argv[5]),contract(argv[6]);summary<<"query_id,ef,topk_equal,ndc_equal,native_ndc,tracer_ndc\n";header(contract);
 for(std::size_t qi=0;qi<limit;++qi)for(auto ef:grid){const float* query=q.data.data()+qi*q.cols;index.setEf(ef);space.reset();auto native=index.searchKnn(query,10);auto native_ndc=space.count();space.reset();auto traced=narhnsw::HnswQueryTracer<float>::search(index,query,10,ef,qi);auto tracer_ndc=space.count();bool same=labels(native)==labels(traced.results);traced.contract.actual_ndc=tracer_ndc;traced.contract.build_id=argv[7];traced.contract.source_target_id=argv[8];summary<<qi<<','<<ef<<','<<same<<','<<(native_ndc==tracer_ndc)<<','<<native_ndc<<','<<tracer_ndc<<'\n';row(contract,traced.contract);if(!same||native_ndc!=tracer_ndc)throw std::runtime_error("native/tracer divergence");}
 std::cout<<"status=complete queries="<<limit<<" efs="<<grid.size()<<'\n';return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
