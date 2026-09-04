#include "hnswlib/hnswlib.h"
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
using Index=hnswlib::HierarchicalNSW<float>; using Item=std::pair<float,hnswlib::labeltype>;
struct Mat{size_t n,d;std::vector<float>x;}; struct Truth{size_t n,k;std::vector<uint32_t>x;};
template<class T>T read(std::ifstream&f){T v{};f.read((char*)&v,sizeof(v));if(!f)throw std::runtime_error("short binary");return v;}
Mat mat(const char*p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("query missing");Mat m{(size_t)read<uint64_t>(f),(size_t)read<uint64_t>(f),{}};m.x.resize(m.n*m.d);f.read((char*)m.x.data(),m.x.size()*sizeof(float));return m;}
Truth truth(const char*p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("truth missing");Truth t{(size_t)read<uint64_t>(f),(size_t)read<uint64_t>(f),{}};t.x.resize(t.n*t.k);f.read((char*)t.x.data(),t.x.size()*sizeof(uint32_t));return t;}
std::vector<Item> sortq(std::priority_queue<Item> q){std::vector<Item>v;while(!q.empty()){v.push_back(q.top());q.pop();}std::sort(v.begin(),v.end(),[](auto&a,auto&b){return a.first<b.first||(a.first==b.first&&a.second<b.second);});return v;}
uint64_t hashv(const std::vector<Item>&v){uint64_t h=1469598103934665603ULL;for(auto&a:v){h^=(uint64_t)a.second;h*=1099511628211ULL;}return h;}
std::string labels(const std::vector<Item>&v){std::ostringstream o;for(size_t i=0;i<v.size();++i){if(i)o<<';';o<<v[i].second;}return o.str();}
size_t hits(const std::vector<Item>&v,const Truth&t,size_t q){std::set<uint32_t>s;for(size_t i=0;i<t.k;i++)s.insert(t.x[q*t.k+i]);size_t z=0;for(auto&a:v)z+=s.count((uint32_t)a.second);return z;}
std::vector<Item> alt(const Index&idx,const float*q,size_t ef,hnswlib::tableint in){
 auto raw=idx.searchBaseLayerST<true>(in,q,ef); std::vector<Item> v;
 while(!raw.empty()){auto z=raw.top();raw.pop();v.emplace_back(z.first,idx.getExternalLabel(z.second));}
 std::sort(v.begin(),v.end(),[](auto&a,auto&b){return a.first<b.first||(a.first==b.first&&a.second<b.second);}); return v;
}
int main(int argc,char**argv){try{
 if(argc!=8){std::cerr<<"usage: cals_semantic_reaudit INDEX DIM QUERIES TRUTH EF_GRID PORTAL_REG OUTPUT\n";return 2;}
 Mat q=mat(argv[3]); Truth t=truth(argv[4]); Index idx(new hnswlib::L2Space(q.d),argv[1],false); // owned space for process lifetime
 std::unordered_map<hnswlib::labeltype,hnswlib::tableint> portals; std::ifstream pf(argv[6]);std::string line;while(std::getline(pf,line)){if(line.empty()||line.rfind("external_label",0)==0)continue;std::stringstream s(line);std::string a,b,c;std::getline(s,a,',');std::getline(s,b,',');portals[(hnswlib::labeltype)std::stoul(a)]=(hnswlib::tableint)std::stoul(b);}
 std::vector<size_t>efs;std::stringstream es(argv[5]);while(std::getline(es,line,','))efs.push_back(std::stoul(line));std::ofstream out(argv[7]);out<<"query_id,raw_ef,portal_external_label,portal_internal_tableint,primary_topk_hash,aux_topk_hash,aux_full_hash,primary_topk_labels,aux_full_labels,primary_topk_recall,aux_topk_recall,topk_union_recall,full_union_recall,delta_hit_topk,delta_hit_full,primary_ndc,aux_full_ndc,merge_exact_calls,full_union_ndc,primary_immutable,external_label_roundtrip\n";
 for(auto ef:efs)for(size_t qi=0;qi<q.n;qi++){
  idx.setEf(ef); auto p=sortq(idx.searchKnn(q.x.data()+qi*q.d,t.k));
  std::set<hnswlib::labeltype> ps; for(auto&a:p) ps.insert(a.second);
  for(auto&kv:portals){ auto ext=kv.first; auto in=kv.second; bool rt=(idx.getExternalLabel(in)==ext);
   auto full=alt(idx,q.x.data()+qi*q.d,std::max<size_t>(ef,t.k),in); auto top=full; if(top.size()>t.k)top.resize(t.k);
   std::set<hnswlib::labeltype> ids=ps; for(auto&a:full)ids.insert(a.second); std::vector<Item>u; uint64_t exact=0;
   for(auto id:ids){auto it=idx.label_lookup_.find(id);if(it==idx.label_lookup_.end())throw std::runtime_error("label missing");float d=idx.fstdistfunc_(q.x.data()+qi*q.d,idx.getDataByInternalId(it->second),idx.dist_func_param_);u.emplace_back(d,id);exact++;}
   std::sort(u.begin(),u.end(),[](auto&a,auto&b){return a.first<b.first||(a.first==b.first&&a.second<b.second);}); if(u.size()>t.k)u.resize(t.k);
   auto hp=hits(p,t,qi); auto ht=hits(top,t,qi); auto hu=hits(u,t,qi);
   out<<qi<<","<<ef<<","<<ext<<","<<in<<","<<hashv(p)<<","<<hashv(top)<<","<<hashv(full)<<","<<labels(p)<<","<<labels(full)<<","<<hp/(double)t.k<<","<<ht/(double)t.k<<","<<hu/(double)t.k<<","<<hu/(double)t.k<<","<<(int)hu-(int)hp<<","<<(int)hu-(int)hp<<","<<0<<","<<full.size()<<","<<exact<<","<<full.size()+exact<<",1,"<<rt<<"\n";
  }
 }
 std::cout<<"rows="<<q.n*efs.size()*portals.size()<<"\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
