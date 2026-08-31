#include "hnswlib/hnswlib.h"
#include "narhnsw/hnsw_query_tracer.hpp"
#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
template<class T>T scalar(std::ifstream& in){T v{};in.read(reinterpret_cast<char*>(&v),sizeof(v));if(!in)throw std::runtime_error("short input");return v;}
struct Matrix{std::size_t rows{},cols{};std::vector<float> values;};
struct Truth{std::size_t rows{},k{};std::vector<std::uint32_t> labels;};
Matrix matrix(const std::filesystem::path& p){std::ifstream in(p,std::ios::binary);if(!in)throw std::runtime_error("cannot open matrix");Matrix m;m.rows=scalar<std::uint64_t>(in);m.cols=scalar<std::uint64_t>(in);m.values.resize(m.rows*m.cols);in.read(reinterpret_cast<char*>(m.values.data()),m.values.size()*sizeof(float));if(!in)throw std::runtime_error("short matrix");return m;}
Truth truth(const std::filesystem::path& p){std::ifstream in(p,std::ios::binary);if(!in)throw std::runtime_error("cannot open truth");Truth t;t.rows=scalar<std::uint64_t>(in);t.k=scalar<std::uint64_t>(in);t.labels.resize(t.rows*t.k);in.read(reinterpret_cast<char*>(t.labels.data()),t.labels.size()*sizeof(std::uint32_t));if(!in)throw std::runtime_error("short truth");return t;}
std::vector<std::size_t> parse_efs(const std::string& raw){std::vector<std::size_t> out;std::stringstream s(raw);std::string x;while(std::getline(s,x,','))out.push_back(std::stoul(x));return out;}
double recall(const hnswlib::HierarchicalNSW<float>& index,const std::vector<hnswlib::tableint>& internal,const std::set<std::uint32_t>& expected){std::size_t hits=0;for(auto id:internal)hits+=expected.count(static_cast<std::uint32_t>(index.getExternalLabel(id)));return static_cast<double>(hits)/expected.size();}
}

int main(int argc,char** argv){try{
 if(argc!=9){std::cerr<<"usage: INDEX QUERIES TRUTH EFS LIMIT TAU BUILD_ID OUTPUT_PREFIX\n";return 2;}
 auto queries=matrix(argv[2]);auto expected=truth(argv[3]);auto grid=parse_efs(argv[4]);auto limit=std::min(queries.rows,std::stoul(argv[5]));double tau=std::stod(argv[6]);std::string build=argv[7];std::filesystem::path prefix=argv[8];
 if(queries.rows!=expected.rows||expected.k!=10)throw std::runtime_error("query/truth mismatch");hnswlib::L2Space space(queries.cols);hnswlib::HierarchicalNSW<float> index(&space,argv[1],false);
 std::ofstream checkpoints(prefix.string()+"_checkpoints.csv"),edges(prefix.string()+"_introduction_edges.csv"),endpoints(prefix.string()+"_endpoints.csv");
 checkpoints<<"build_id,query_row,ef,expansion_count,recall_at_10,safe,top_k_internal\n";edges<<"build_id,query_row,ef,event_index,expansion_count,source_internal,target_internal,source_label,target_label,before_first_safe\n";endpoints<<"build_id,query_row,ef,first_safe_expansion,endpoint_feasible,total_expansions\n";
 for(std::size_t qi=0;qi<limit;++qi){std::set<std::uint32_t> truthset(expected.labels.begin()+qi*expected.k,expected.labels.begin()+(qi+1)*expected.k);for(auto ef:grid){const float* q=queries.values.data()+qi*queries.cols;auto trace=narhnsw::HnswQueryTracer<float>::search(index,q,10,ef,qi);std::size_t first=0;bool feasible=false;for(const auto& cp:trace.checkpoints){double r=recall(index,cp.top_k_internal,truthset);if(!feasible&&r>=tau){first=cp.expansion_count;feasible=true;}checkpoints<<build<<','<<qi<<','<<ef<<','<<cp.expansion_count<<','<<r<<','<<(r>=tau)<<",\"";for(std::size_t j=0;j<cp.top_k_internal.size();++j){if(j)checkpoints<<';';checkpoints<<cp.top_k_internal[j];}checkpoints<<"\"\n";}std::size_t expansions=0;for(const auto& e:trace.events){if(e.phase=="base"&&e.event=="expanded")++expansions;if(e.phase=="base"&&e.event=="enqueued")edges<<build<<','<<qi<<','<<ef<<','<<e.event_index<<','<<expansions<<','<<e.source<<','<<e.target<<','<<index.getExternalLabel(e.source)<<','<<index.getExternalLabel(e.target)<<','<<(feasible&&expansions<=first)<<'\n';}endpoints<<build<<','<<qi<<','<<ef<<',';if(feasible)endpoints<<first;endpoints<<','<<feasible<<','<<trace.base_expansions<<'\n';}}
 std::cout<<"status=complete build="<<build<<" queries="<<limit<<" efs="<<grid.size()<<'\n';return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
