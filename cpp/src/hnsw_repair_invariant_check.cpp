#include "hnswlib/hnswlib.h"
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

namespace {
using Index=hnswlib::HierarchicalNSW<float>;
std::vector<hnswlib::tableint> neighbors(const Index& x,hnswlib::tableint n,int layer=0){auto* raw=x.get_linklist_at_level(n,layer);auto degree=x.getListCount(raw);auto* ids=reinterpret_cast<const hnswlib::tableint*>(raw+1);return {ids,ids+degree};}
void mix(std::uint64_t& h,std::uint64_t v){for(int b=0;b<8;++b){h^=(v>>(8*b))&255U;h*=1099511628211ULL;}}
std::uint64_t hash_layer(const Index& x,int lower){std::uint64_t h=1469598103934665603ULL;for(hnswlib::tableint n=0;n<x.cur_element_count.load();++n){int first=lower?0:1;for(int layer=first;layer<=x.element_levels_[n];++layer){mix(h,n);mix(h,layer);auto a=neighbors(x,n,layer);mix(h,a.size());for(auto t:a)mix(h,t);}}return h;}
struct Basic{bool degree=true,ids=true,self=true,duplicate=true;std::vector<std::vector<hnswlib::tableint>> out,undirected;};
Basic inspect(const Index& x){Basic b;b.out.resize(x.cur_element_count.load());b.undirected.resize(x.cur_element_count.load());for(hnswlib::tableint n=0;n<x.cur_element_count.load();++n){b.out[n]=neighbors(x,n);b.degree=b.degree&&b.out[n].size()<=x.maxM0_;std::set<hnswlib::tableint> seen;for(auto t:b.out[n]){b.ids=b.ids&&t<x.cur_element_count.load();b.self=b.self&&t!=n;b.duplicate=b.duplicate&&seen.insert(t).second;if(t<x.cur_element_count.load()&&t!=n){b.undirected[n].push_back(t);b.undirected[t].push_back(n);}}}return b;}
std::size_t reachable(const std::vector<std::vector<hnswlib::tableint>>& a,hnswlib::tableint start){std::vector<char> seen(a.size());std::queue<hnswlib::tableint> q;q.push(start);seen[start]=1;std::size_t count=0;while(!q.empty()){auto n=q.front();q.pop();++count;for(auto t:a[n])if(!seen[t]){seen[t]=1;q.push(t);}}return count;}
std::vector<std::pair<std::uint32_t,std::uint32_t>> protected_edges(const std::filesystem::path& p){std::ifstream in(p);if(!in)throw std::runtime_error("cannot open selection audit");std::vector<std::pair<std::uint32_t,std::uint32_t>> r;std::string line;std::getline(in,line);while(std::getline(in,line)){auto p1=line.find(','),p2=line.find(',',p1+1),p3=line.find(',',p2+1);if(p1==std::string::npos||p2==std::string::npos)continue;if(line.substr(p2+1,p3-p2-1)=="mandatory")r.emplace_back(std::stoul(line.substr(0,p1)),std::stoul(line.substr(p1+1,p2-p1-1)));}return r;}
}
int main(int argc,char** argv){try{if(argc!=5){std::cerr<<"usage: BASE STABLE SELECTION_AUDIT OUTPUT\n";return 2;}hnswlib::L2Space space(128);Index base(&space,argv[1],false),stable(&space,argv[2],false);auto basic=inspect(stable);auto weak=reachable(basic.undirected,stable.enterpoint_node_);auto directed=reachable(basic.out,stable.enterpoint_node_);auto protected_list=protected_edges(argv[3]);std::size_t survived=0;for(auto [slabel,tlabel]:protected_list){auto s=stable.label_lookup_.at(slabel),t=stable.label_lookup_.at(tlabel);auto a=neighbors(stable,s);survived+=std::find(a.begin(),a.end(),t)!=a.end();}std::filesystem::path roundtrip=std::string(argv[4])+".roundtrip.bin";stable.saveIndex(roundtrip.string());Index loaded(&space,roundtrip.string(),false);bool serial=hash_layer(stable,1)==hash_layer(loaded,1)&&hash_layer(stable,0)==hash_layer(loaded,0);std::filesystem::remove(roundtrip);bool upper=hash_layer(base,0)==hash_layer(stable,0);bool entry=base.enterpoint_node_==stable.enterpoint_node_;std::ofstream out(argv[4]);out<<"invariant,value,required,status\n";auto emit=[&](const std::string& n,bool v){out<<n<<','<<v<<",1,"<<(v?"PASS":"FAIL")<<'\n';};emit("upper_layers_unchanged",upper);emit("entry_point_unchanged",entry);emit("degree_cap",basic.degree);emit("valid_ids",basic.ids);emit("no_self_loops",basic.self);emit("no_duplicate_edges",basic.duplicate);emit("weak_connected",weak==stable.cur_element_count.load());emit("directed_entry_reachability",directed==stable.cur_element_count.load());emit("serialization_roundtrip",serial);emit("protected_survival",survived==protected_list.size());std::cout<<"weak="<<weak<<" directed="<<directed<<" protected="<<survived<<'/'<<protected_list.size()<<" upper="<<upper<<" entry="<<entry<<" serial="<<serial<<'\n';return upper&&entry&&basic.degree&&basic.ids&&basic.self&&basic.duplicate&&weak==stable.cur_element_count.load()&&directed==stable.cur_element_count.load()&&serial&&survived==protected_list.size()?0:1;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
