#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Index = hnswlib::HierarchicalNSW<float>;
using Internal = hnswlib::tableint;
using Label = hnswlib::labeltype;
using RawQueue = std::priority_queue<std::pair<float, Internal>,
                                     std::vector<std::pair<float, Internal>>,
                                     Index::CompareByFirst>;

struct Matrix { std::size_t n{}, d{}; std::vector<float> x; };
template <class T> T readv(std::ifstream& f) { T v{}; f.read(reinterpret_cast<char*>(&v), sizeof(v)); if (!f) throw std::runtime_error("short binary"); return v; }
Matrix matrix(const char* path) { std::ifstream f(path, std::ios::binary); if (!f) throw std::runtime_error("query matrix missing"); Matrix m{static_cast<std::size_t>(readv<std::uint64_t>(f)), static_cast<std::size_t>(readv<std::uint64_t>(f)), {}}; m.x.resize(m.n*m.d); f.read(reinterpret_cast<char*>(m.x.data()), static_cast<std::streamsize>(m.x.size()*sizeof(float))); if (!f) throw std::runtime_error("short query matrix"); return m; }
std::vector<std::size_t> ids(const char* path) { std::ifstream f(path); if (!f) throw std::runtime_error("query ids missing"); std::vector<std::size_t> v; std::string s; while (std::getline(f,s)) { if (s.empty() || s.find("query_id") != std::string::npos) continue; v.push_back(std::stoull(s)); } return v; }
std::vector<std::size_t> efs(const char* raw) { std::vector<std::size_t> v; std::stringstream ss(raw); std::string s; while (std::getline(ss,s,',')) v.push_back(std::stoull(s)); if (v.empty()) throw std::runtime_error("empty ef grid"); return v; }

struct Trace {
  std::vector<std::pair<float,Label>> topk;
  std::size_t upper_steps{}, expansions{}, evaluations{}, visited{}, duplicate_edges{};
  std::size_t pushes{}, pops{}, enqueued{}, pruned{}, max_queue{};
  double improve4{}, improve8{}, improve16{}, yield4{}, yield8{}, yield16{};
  float frontier_min{}, kth_distance{}, frontier_kth_ratio{};
  std::uint64_t expansion_hash{1469598103934665603ULL};
  std::string stop_reason{"candidate_exhausted"};
};

static float distance(const Index& idx, const float* q, Internal n) { return idx.fstdistfunc_(q, idx.getDataByInternalId(n), idx.dist_func_param_); }
static std::vector<Internal> links(const Index& idx, Internal n, int level) { auto* raw=idx.get_linklist_at_level(n,level); auto count=idx.getListCount(raw); auto* p=reinterpret_cast<const Internal*>(raw+1); return {p,p+count}; }
static std::vector<std::pair<float,Label>> ordered(std::priority_queue<std::pair<float,Label>> q) { std::vector<std::pair<float,Label>> v; while(!q.empty()){v.push_back(q.top());q.pop();} std::sort(v.begin(),v.end()); return v; }
static double window_improvement(const std::vector<float>& x, std::size_t w) { if (x.size()<2) return 0.0; const auto a=x.size()>w?x.size()-w:0; const float first=x[a], last=x.back(); return first>0.0F ? static_cast<double>(first-last)/first : 0.0; }
static double window_yield(const std::vector<std::size_t>& x, std::size_t w) { if (x.empty()) return 0.0; const auto a=x.size()>w?x.size()-w:0; std::size_t sum=0; for(std::size_t i=a;i<x.size();++i) sum+=x[i]; return static_cast<double>(sum)/(x.size()-a); }

Trace trace(const Index& idx, const float* q, std::size_t ef, std::size_t k) {
  Trace t; Internal cur=idx.enterpoint_node_; float cd=distance(idx,q,cur); ++t.evaluations;
  for(int level=idx.maxlevel_;level>0;--level){ bool changed=true; while(changed){ changed=false; for(auto n:links(idx,cur,level)){ float d=distance(idx,q,n); ++t.evaluations; ++t.upper_steps; if(d<cd){cd=d;cur=n;changed=true;} } } }
  RawQueue top, candidates; top.emplace(cd,cur); candidates.emplace(-cd,cur); t.pushes=1; t.max_queue=1;
  std::vector<bool> seen(idx.cur_element_count.load(),false); seen[cur]=true; t.visited=1;
  float lower=cd; const auto search_ef=std::max(ef,k); std::vector<float> lower_history; std::vector<std::size_t> yields;
  while(!candidates.empty()){
    const auto cp=candidates.top(); const float candidate_distance=-cp.first;
    if(candidate_distance>lower){t.stop_reason="frontier_exceeds_kth";break;}
    candidates.pop(); ++t.pops; ++t.expansions; const Internal expanded=cp.second;
    t.expansion_hash^=idx.getExternalLabel(expanded); t.expansion_hash*=1099511628211ULL;
    std::size_t new_enqueued=0;
    for(auto n:links(idx,expanded,0)){
      if(seen[n]){++t.duplicate_edges;continue;} seen[n]=true; ++t.visited;
      float d=distance(idx,q,n); ++t.evaluations;
      if(top.size()<search_ef || lower>d){candidates.emplace(-d,n);top.emplace(d,n);++t.pushes;++t.enqueued;++new_enqueued;if(top.size()>search_ef)top.pop();lower=top.top().first;t.max_queue=std::max(t.max_queue,candidates.size());}
      else ++t.pruned;
    }
    lower_history.push_back(lower); yields.push_back(new_enqueued);
  }
  t.frontier_min=candidates.empty()?std::numeric_limits<float>::quiet_NaN():-candidates.top().first;
  t.kth_distance=lower; t.frontier_kth_ratio=(!candidates.empty() && lower>0.0F)?t.frontier_min/lower:std::numeric_limits<float>::quiet_NaN();
  t.improve4=window_improvement(lower_history,4);t.improve8=window_improvement(lower_history,8);t.improve16=window_improvement(lower_history,16);
  t.yield4=window_yield(yields,4);t.yield8=window_yield(yields,8);t.yield16=window_yield(yields,16);
  while(top.size()>k)top.pop(); while(!top.empty()){auto z=top.top();top.pop();t.topk.emplace_back(z.first,idx.getExternalLabel(z.second));} std::sort(t.topk.begin(),t.topk.end()); return t;
}

int main(int argc,char** argv){try{
  if(argc!=7){std::cerr<<"usage: bn_apd_observable_trace INDEX QUERIES QUERY_IDS EFS BUILD OUTPUT\n";return 2;}
  Matrix q=matrix(argv[2]); auto qids=ids(argv[3]); auto grid=efs(argv[4]); hnswlib::L2Space space(q.d); Index idx(&space,argv[1],false); std::ofstream out(argv[6]); if(!out)throw std::runtime_error("output unavailable");
  out<<"query_id,build_id,raw_ef,upper_steps,base_expansions,distance_evaluations,visited_count,duplicate_neighbor_edges,duplicate_ratio,queue_pushes,queue_pops,max_queue_size,enqueued,pruned,candidate_yield_w4,candidate_yield_w8,candidate_yield_w16,kth_improvement_w4,kth_improvement_w8,kth_improvement_w16,frontier_min_distance,kth_distance,frontier_kth_ratio,stop_reason,expansion_hash,native_tracer_equal\n"<<std::setprecision(std::numeric_limits<double>::max_digits10);
  for(auto ef:grid)for(auto qi:qids){if(qi>=q.n)throw std::runtime_error("query id out of range");const float* x=q.x.data()+qi*q.d;idx.setEf(ef);auto native_result=ordered(idx.searchKnn(x,10));auto z=trace(idx,x,ef,10);bool equal=native_result==z.topk;const auto denom=z.duplicate_edges+z.visited-1;out<<qi<<','<<argv[5]<<','<<ef<<','<<z.upper_steps<<','<<z.expansions<<','<<z.evaluations<<','<<z.visited<<','<<z.duplicate_edges<<','<<(denom?static_cast<double>(z.duplicate_edges)/denom:0.0)<<','<<z.pushes<<','<<z.pops<<','<<z.max_queue<<','<<z.enqueued<<','<<z.pruned<<','<<z.yield4<<','<<z.yield8<<','<<z.yield16<<','<<z.improve4<<','<<z.improve8<<','<<z.improve16<<','<<z.frontier_min<<','<<z.kth_distance<<','<<z.frontier_kth_ratio<<','<<z.stop_reason<<','<<z.expansion_hash<<','<<equal<<'\n';if(!equal)throw std::runtime_error("native/tracer top-k mismatch");}
  std::cout<<"status=complete queries="<<qids.size()<<" efs="<<grid.size()<<"\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
