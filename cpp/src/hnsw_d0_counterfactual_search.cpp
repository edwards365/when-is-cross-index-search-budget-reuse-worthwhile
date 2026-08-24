#include "hnswlib/hnswlib.h"

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {
using Index = hnswlib::HierarchicalNSW<float>;
using Node = hnswlib::tableint;
using Result = std::vector<std::pair<float, std::uint32_t>>;
using Adj = std::vector<std::vector<Node>>;

struct Matrix { std::size_t rows{}, columns{}; std::vector<float> values; };
struct Truth { std::size_t rows{}, k{}; std::vector<std::uint32_t> labels; };
struct SearchResult { Result result; std::size_t ndc{}; };

class MetricSpace final : public hnswlib::SpaceInterface<float> {
 public:
  MetricSpace(std::size_t dimensions, bool ip) : state_{dimensions, ip} {}
  std::size_t get_data_size() override { return state_.dimensions * sizeof(float); }
  hnswlib::DISTFUNC<float> get_dist_func() override { return distance_function; }
  void* get_dist_func_param() override { return &state_; }
 private:
  struct State { std::size_t dimensions; bool ip; } state_;
  static float distance_function(const void* a0, const void* b0, const void* s0) {
    const auto* s = static_cast<const State*>(s0);
    const auto* a = static_cast<const float*>(a0);
    const auto* b = static_cast<const float*>(b0);
    float value = 0;
    if (s->ip) { for (std::size_t i=0;i<s->dimensions;++i) value += a[i]*b[i]; return 1-value; }
    for (std::size_t i=0;i<s->dimensions;++i) { const float d=a[i]-b[i]; value += d*d; }
    return value;
  }
};

template<class T> T scalar(std::ifstream& in) {
  T x{}; in.read(reinterpret_cast<char*>(&x), sizeof(x));
  if (!in) throw std::runtime_error("truncated binary input"); return x;
}
Matrix read_matrix(const std::filesystem::path& p) {
  std::ifstream in(p, std::ios::binary); if (!in) throw std::runtime_error("cannot open queries");
  Matrix m; m.rows=scalar<std::uint64_t>(in); m.columns=scalar<std::uint64_t>(in);
  m.values.resize(m.rows*m.columns); in.read(reinterpret_cast<char*>(m.values.data()), m.values.size()*sizeof(float));
  if (!in || in.peek()!=std::ifstream::traits_type::eof()) throw std::runtime_error("invalid queries"); return m;
}
Truth read_truth(const std::filesystem::path& p) {
  std::ifstream in(p, std::ios::binary); if (!in) throw std::runtime_error("cannot open truth");
  Truth t; t.rows=scalar<std::uint64_t>(in); t.k=scalar<std::uint64_t>(in); t.labels.resize(t.rows*t.k);
  in.read(reinterpret_cast<char*>(t.labels.data()), t.labels.size()*sizeof(std::uint32_t));
  if (!in || in.peek()!=std::ifstream::traits_type::eof()) throw std::runtime_error("invalid truth"); return t;
}
std::vector<std::size_t> parse_efs(const std::string& raw) {
  std::vector<std::size_t> out; std::stringstream ss(raw); std::string item;
  while (std::getline(ss,item,',')) out.push_back(std::stoul(item));
  if (out.empty()) throw std::invalid_argument("empty ef list"); return out;
}
Adj read_edges(const std::filesystem::path& p, std::size_t n) {
  std::ifstream in(p); if (!in) throw std::runtime_error("cannot open edge CSV: "+p.string());
  Adj out(n); std::string line; std::getline(in,line);
  while (std::getline(in,line)) { if (line.empty()) continue; std::stringstream ss(line); std::string a,b;
    std::getline(ss,a,','); std::getline(ss,b,','); const auto u=std::stoul(a), v=std::stoul(b);
    if (u>=n || v>=n) throw std::runtime_error("edge endpoint out of range"); out[u].push_back(static_cast<Node>(v)); }
  return out;
}
std::set<std::pair<Node,Node>> read_plan(const std::filesystem::path& p) {
  std::ifstream in(p); if (!in) throw std::runtime_error("cannot open addback plan");
  std::set<std::pair<Node,Node>> out; std::string line; std::getline(in,line);
  while (std::getline(in,line)) { if (line.empty()) continue; std::stringstream ss(line); std::string a,b;
    std::getline(ss,a,','); std::getline(ss,b,','); out.emplace(std::stoul(a),std::stoul(b)); }
  return out;
}
Adj intersection(const Adj& a, const Adj& b) {
  Adj out(a.size()); for (std::size_t u=0;u<a.size();++u) { const std::unordered_set<Node> keep(b[u].begin(),b[u].end());
    for (Node v:a[u]) if (keep.count(v)) out[u].push_back(v); } return out;
}
Adj augment(const Adj& base, const Adj& source, const std::set<std::pair<Node,Node>>* plan=nullptr) {
  Adj out=base; for (std::size_t u=0;u<source.size();++u) { std::unordered_set<Node> seen(out[u].begin(),out[u].end());
    for (Node v:source[u]) if ((!plan || plan->count({static_cast<Node>(u),v})) && seen.insert(v).second) out[u].push_back(v); } return out;
}
std::vector<Node> native_neighbors(const Index& index, Node node, int layer) {
  auto* raw=index.get_linklist_at_level(node,layer); const auto degree=index.getListCount(raw);
  const auto* ids=reinterpret_cast<const Node*>(raw+1); return {ids,ids+degree};
}
float distance(const Index& index, const void* query, Node node) {
  return index.fstdistfunc_(query,index.getDataByInternalId(node),index.dist_func_param_);
}
Result ordered(std::priority_queue<std::pair<float,hnswlib::labeltype>> heap) {
  Result out; while(!heap.empty()){out.emplace_back(heap.top().first,static_cast<std::uint32_t>(heap.top().second));heap.pop();}
  std::sort(out.begin(),out.end()); return out;
}
SearchResult custom_search(const Index& index, const Adj& adj, const void* query, std::size_t k, std::size_t ef) {
  using Queue=std::priority_queue<std::pair<float,Node>,std::vector<std::pair<float,Node>>,Index::CompareByFirst>;
  Node current=index.enterpoint_node_; float current_distance=distance(index,query,current); std::size_t upper=0,base=0;
  for(int layer=index.maxlevel_;layer>0;--layer){bool changed=true;while(changed){changed=false;for(Node candidate:native_neighbors(index,current,layer)){
    const float d=distance(index,query,candidate);++upper;if(d<current_distance){current_distance=d;current=candidate;changed=true;}}}}
  Queue top,candidates; const float entry=distance(index,query,current); float lower=entry; top.emplace(entry,current); candidates.emplace(-entry,current);
  std::vector<bool> visited(index.cur_element_count.load(),false); visited[current]=true; const auto search_ef=std::max(ef,k);
  while(!candidates.empty()){const auto item=candidates.top();const float d=-item.first;if(d>lower)break;candidates.pop();
    for(Node neighbor:adj[item.second]){if(visited[neighbor])continue;visited[neighbor]=true;const float nd=distance(index,query,neighbor);++base;
      if(top.size()<search_ef || lower>nd){candidates.emplace(-nd,neighbor);top.emplace(nd,neighbor);if(top.size()>search_ef)top.pop();if(!top.empty())lower=top.top().first;}}}
  while(top.size()>k)top.pop(); std::priority_queue<std::pair<float,hnswlib::labeltype>> external;
  while(!top.empty()){external.emplace(top.top().first,index.getExternalLabel(top.top().second));top.pop();}
  return {ordered(std::move(external)),upper+base+2};
}
std::size_t hits(const Result& r,const Truth& t,std::size_t q){std::set<std::uint32_t> expected;
  for(std::size_t i=0;i<t.k;++i)expected.insert(t.labels[q*t.k+i]);std::size_t h=0;for(auto& x:r)h+=expected.count(x.second);return h;}
void emit_mode(std::ofstream& out,const std::string& run,const std::string& mode,const Index& index,const Adj& adj,
               const Matrix& q,const Truth& t,const std::vector<std::size_t>& efs,const Index* native) {
  for(auto ef:efs){if(native)const_cast<Index*>(native)->setEf(ef);for(std::size_t qi=0;qi<q.rows;++qi){const auto* query=q.values.data()+qi*q.columns;
    const auto result=custom_search(index,adj,query,t.k,ef);if(native && ordered(native->searchKnn(query,t.k))!=result.result)
      throw std::runtime_error(mode+" custom adjacency diverged from native searchKnn");
    out<<run<<','<<mode<<','<<ef<<','<<qi<<','<<static_cast<double>(hits(result.result,t,qi))/t.k<<','<<result.ndc<<'\n';}}
}
} // namespace

int main(int argc,char** argv){try{
  if(argc!=13){std::cerr<<"usage: hnsw_d0_counterfactual_search ORIGINAL_INDEX PRIMARY_INDEX QUERIES TRUTH METRIC EFS RUN_ID ORIGINAL_EDGES PRIMARY_EDGES PLAN_DIR OUTPUT_CSV OUTPUT_META\n";return 2;}
  const auto q=read_matrix(argv[3]);const auto t=read_truth(argv[4]);if(q.rows!=500||t.rows!=500||t.k!=10)throw std::invalid_argument("requires frozen E0 500x10 search inputs");
  const std::string metric=argv[5];if(metric!="l2"&&metric!="ip")throw std::invalid_argument("metric must be l2 or ip");const auto efs=parse_efs(argv[6]);
  MetricSpace os(q.columns,metric=="ip"),ps(q.columns,metric=="ip");Index original(&os,argv[1],false),primary(&ps,argv[2],false);
  if(original.cur_element_count.load()!=10000||primary.cur_element_count.load()!=10000)throw std::invalid_argument("requires 10K indexes");
  const auto oa=read_edges(argv[8],10000),pa=read_edges(argv[9],10000);std::ofstream out(argv[11]);if(!out)throw std::runtime_error("cannot create output");
  out<<"run_id,mode,ef_search,query_id,recall,ndc\n";emit_mode(out,argv[7],"original",original,oa,q,t,efs,&original);emit_mode(out,argv[7],"primary",original,pa,q,t,efs,&primary);
  emit_mode(out,argv[7],"intersection",original,intersection(oa,pa),q,t,efs,nullptr);emit_mode(out,argv[7],"union",original,augment(pa,oa),q,t,efs,nullptr);
  const std::vector<std::string> names={"0p0","0p01","0p025","0p05","0p1","0p15","0p2","0p25"};
  for(const auto& name:names){const auto plan=read_plan(std::filesystem::path(argv[10])/("addback_"+name+".csv"));emit_mode(out,argv[7],"addback_"+name,original,augment(pa,oa,&plan),q,t,efs,nullptr);}
  std::ofstream meta(argv[12]);meta<<"{\n  \"status\": \"complete\",\n  \"native_original_exact\": true,\n  \"native_primary_exact\": true,\n  \"degree_budget_may_be_exceeded\": true,\n  \"new_ef_points\": false,\n  \"validation_dev_accessed\": false,\n  \"formal_test_members_accessed\": false\n}\n";
  std::cout<<"status=complete run_id="<<argv[7]<<"\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
