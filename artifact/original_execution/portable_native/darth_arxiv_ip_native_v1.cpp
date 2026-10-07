#include <faiss/IndexHNSW.h>
#include <faiss/IndexFlat.h>
#include <faiss/index_io.h>
#include <faiss/impl/DeclarativeRecall.h>
#include <omp.h>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <vector>
#include <cmath>
#include <stdexcept>
#include <set>
#include <limits>

template<class T> void read(std::ifstream& f,T* p,size_t n) {
  f.read(reinterpret_cast<char*>(p),n*sizeof(T));
  if(!f) throw std::runtime_error("short binary input");
}
std::vector<float> fbin(const char* path,uint32_t rows,uint32_t dim) {
  std::ifstream f(path,std::ios::binary); uint32_t h[2];read(f,h,2);
  if(h[0]!=rows||h[1]!=dim)throw std::runtime_error("input shape");
  std::vector<float> x(size_t(rows)*dim);read(f,x.data(),x.size());
  if(f.peek()!=EOF)throw std::runtime_error("trailing input");
  for(float v:x)if(!std::isfinite(v))throw std::runtime_error("nonfinite vector");
  return x;
}
void controls() {
  float base[]={2,0,.1f,0};float q[]={1,0,-1,0};
  faiss::IndexHNSWFlat index(2,16,faiss::METRIC_INNER_PRODUCT);
  index.add(2,base);float score[4];faiss::idx_t ids[4];index.search(2,q,2,score,ids);
  if(ids[0]!=0||ids[2]!=1||std::fabs(score[0]-2)>1e-6||std::fabs(score[2]+.1f)>1e-6)
    throw std::runtime_error("genuine unnormalized native IP control");
  float nd[]={-3,-2,-1},gt[]={-3,-2,-1};faiss::idx_t label[]={0,1,2};
  faiss::DeclarativeRecallDataManager m(nd,label,label,gt,1,2,3,q,nullptr,base,2,label,3);
  if(m.get_furthest_dist_of_query(0)!=-1||m.get_nearest_dist_of_query(0)!=-3||
     m.get_avg_dist_of_query(0)!=-2||m.get_percentile_of_query(0,.5)!=-2||m.get_recallk(0)!=1)
    throw std::runtime_error("negative-distance feature control");
  nd[0]=0;nd[1]=-0.f;nd[2]=0;
  if(m.get_furthest_dist_of_query(0)!=0)throw std::runtime_error("zero feature control");
  std::cout<<"NEW_IP_AND_NEGATIVE_FEATURE_CONTROLS_PASS\n";
}
int main(int argc,char**argv)try {
  omp_set_num_threads(1);
  if(argc==2&&std::string(argv[1])=="--controls"){controls();return 0;}
  // mode, immutable base.fbin, role queries.fbin, role truth.bin, output prefix,
  // saved index path, model path (source uses literal NONE), query count.
  if(argc!=9)throw std::runtime_error("exact argument count");
  bool source=std::string(argv[1])=="source";
  if(!source&&std::string(argv[1])!="role")throw std::runtime_error("mode");
  uint32_t nq=std::stoul(argv[8]),dim=768,n=1342143,k=10;
  if(nq!=500&&nq!=1000)throw std::runtime_error("role count");
  auto base=fbin(argv[2],n,dim),queries=fbin(argv[3],nq,dim);
  std::ifstream tf(argv[4],std::ios::binary);uint32_t h[2];read(tf,h,2);
  if(h[0]!=nq||h[1]!=k)throw std::runtime_error("truth shape");
  std::vector<uint32_t> ti(nq*k);read(tf,ti.data(),ti.size());
  std::vector<float> truth(nq*k);read(tf,truth.data(),truth.size());
  if(tf.peek()!=EOF)throw std::runtime_error("truth EOF");
  std::vector<faiss::idx_t> gt(ti.begin(),ti.end());
  for(size_t i=0;i<gt.size();i++)if(gt[i]<0||gt[i]>=n||!std::isfinite(truth[i]))throw std::runtime_error("truth value");
  std::unique_ptr<faiss::IndexHNSWFlat> index;
  if(source){
    index.reset(new faiss::IndexHNSWFlat(dim,16,faiss::METRIC_INNER_PRODUCT));
    index->hnsw.efConstruction=100;index->hnsw.efSearch=200;
    index->add(n,base.data());faiss::write_index(index.get(),argv[6]);
  }else{
    faiss::Index* raw=faiss::read_index(argv[6]);
    auto ptr=dynamic_cast<faiss::IndexHNSWFlat*>(raw);
    if(!ptr){delete raw;throw std::runtime_error("index type");}index.reset(ptr);
    if(index->metric_type!=faiss::METRIC_INNER_PRODUCT||index->d!=dim||index->ntotal!=n)
      throw std::runtime_error("saved IP index identity");
    index->hnsw.efSearch=200;
  }
  std::cout<<"GENUINE_IP base="<<n<<" dim="<<dim<<" nq="<<nq<<" k=10 M=16 efC=100 efS=200\n"<<std::flush;
  std::vector<float> scores(nq*k);std::vector<faiss::idx_t> ids(nq*k);
  std::string csv=std::string(argv[5])+".csv";
  faiss::DeclarativeRecallDataManager m(scores.data(),ids.data(),gt.data(),truth.data(),nq,dim,k,
    queries.data(),const_cast<char*>(csv.c_str()),base.data(),n,gt.data(),k);
  if(source){
    faiss::DeclarativeRecallDataCollectorHNSW collector(m,5);collector.init_log_file();
    index->search_declarative_recall_data_generation(nq,queries.data(),k,scores.data(),ids.data(),collector);
    collector.close_log_file();
  }else{
    faiss::DARTHPredictorHNSW predictor(m,.95,1000,100,false,argv[7]);predictor.init_log_file();
    index->search_DARTH(nq,queries.data(),k,scores.data(),ids.data(),predictor);predictor.close_log_file();
  }
  // Native public API scores are dot products after HNSW negation is reversed.
  std::ofstream out(std::string(argv[5])+".returned.bin",std::ios::binary);
  out.write(reinterpret_cast<char*>(h),sizeof(h));
  for(size_t i=0;i<ids.size();i++)if(ids[i]<0||ids[i]>=n||!std::isfinite(scores[i]))throw std::runtime_error("invalid returned row");
  out.write(reinterpret_cast<char*>(ids.data()),ids.size()*sizeof(ids[0]));
  out.write(reinterpret_cast<char*>(scores.data()),scores.size()*sizeof(scores[0]));out.close();
  if(!out)throw std::runtime_error("returned write");
  double sum=0;for(uint32_t qi=0;qi<nq;qi++)sum+=m.get_recallk(qi);
  std::cout<<"NATIVE_RETURNED_COMPLETE count="<<ids.size()<<" meanRecall="<<sum/nq<<"\n";
  return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
