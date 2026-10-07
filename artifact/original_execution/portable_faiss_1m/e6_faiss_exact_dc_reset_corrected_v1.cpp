// New measurement adapter. No graph construction, distance arithmetic, or policy changes.
#include <faiss/IndexHNSW.h>
#include <faiss/IndexIDMap.h>
#include <faiss/impl/DistanceComputer.h>
#include <faiss/index_io.h>
#include <faiss/utils/utils.h>
#include <omp.h>
#include <unistd.h>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

using faiss::idx_t;
template<class T> void put(std::ostream& f,const T& x){f.write(reinterpret_cast<const char*>(&x),sizeof x);if(!f)throw std::runtime_error("output write");}
template<class T> T get(std::istream& f){T x;f.read(reinterpret_cast<char*>(&x),sizeof x);if(!f)throw std::runtime_error("input read");return x;}
struct Ledger {
    std::ostream* trace=nullptr; const std::vector<idx_t>* ids=nullptr;
    int32_t ef=0,q=0; uint64_t scalar=0,batch=0;
    void record(idx_t i,float d,int32_t kind){
        if(!std::isfinite(d)||i<0||(ids&&size_t(i)>=ids->size()))throw std::runtime_error("distance/id invalid");
        if(trace){put(*trace,ef);put(*trace,q);put(*trace,kind);idx_t raw=(*ids)[i];put(*trace,raw);put(*trace,d);}
    }
};
struct CountDC : faiss::DistanceComputer {
    std::unique_ptr<faiss::DistanceComputer> inner; Ledger& l;
    CountDC(faiss::DistanceComputer* p,Ledger& v):inner(p),l(v){}
    void set_query(const float* x) override {inner->set_query(x);}
    float operator()(idx_t i) override {float d=(*inner)(i);++l.scalar;l.record(i,d,1);return d;}
    void distances_batch_4(idx_t a,idx_t b,idx_t c,idx_t d,float& x,float& y,float& z,float& w) override {
        inner->distances_batch_4(a,b,c,d,x,y,z,w);++l.batch;
        l.record(a,x,4);l.record(b,y,4);l.record(c,z,4);l.record(d,w,4);
    }
    float symmetric_dis(idx_t,idx_t) override {throw std::runtime_error("unexpected stored-stored distance during query search");}
};
struct CountStorage : faiss::Index {
    faiss::Index& original; Ledger& ledger;
    CountStorage(faiss::Index& i,Ledger& l):Index(i.d,i.metric_type),original(i),ledger(l){ntotal=i.ntotal;is_trained=i.is_trained;metric_arg=i.metric_arg;}
    faiss::DistanceComputer* get_distance_computer() const override {return new CountDC(original.get_distance_computer(),ledger);}
    void reset() override {throw std::runtime_error("measurement cannot reset");}
    void add(idx_t,const float*) override {throw std::runtime_error("measurement cannot add");}
    void search(idx_t,const float*,idx_t,float*,idx_t*,const faiss::SearchParameters*) const override {throw std::runtime_error("storage search unexpected");}
    void reconstruct(idx_t i,float* x) const override {original.reconstruct(i,x);}
};
struct FakeDC : faiss::DistanceComputer {
    uint64_t calls=0,batches=0;const float* query=nullptr;
    void set_query(const float* q) override{query=q;}
    float operator()(idx_t i) override{++calls;return float(i)+*query;}
    void distances_batch_4(idx_t a,idx_t b,idx_t c,idx_t d,float& w,float& x,float& y,float& z) override{
        ++batches;w=float(a)+*query;x=float(b)+*query;y=float(c)+*query;z=float(d)+*query;
    }
    float symmetric_dis(idx_t,idx_t) override{return 0;}
};
void controls(){
    Ledger l;auto* f=new FakeDC;CountDC dc(f,l);float q=-2;dc.set_query(&q);
    if(dc(1)!=-1)throw std::runtime_error("scalar delegation");
    float a,b,c,d;dc.distances_batch_4(0,1,2,3,a,b,c,d);
    if(a!=-2||b!=-1||c!=0||d!=1||l.scalar!=1||l.batch!=1||f->calls!=1||f->batches!=1)throw std::runtime_error("batch must delegate once without scalar replacement/double counting");
    bool rejected=false;try{dc.symmetric_dis(0,1);}catch(const std::runtime_error&){rejected=true;}
    if(!rejected)throw std::runtime_error("stored-stored reject");
    std::cout<<"NEW_EXACT_DC_DELEGATION_CONTROLS_PASS version "<<FAISS_VERSION_MAJOR<<'.'<<FAISS_VERSION_MINOR<<'.'<<FAISS_VERSION_PATCH<<" options "<<faiss::get_compile_options()<<std::endl;
    sleep(1); // permits independent runtime-map/affinity observation; not a timing run.
}
int main(int argc,char** argv){try{
    omp_set_num_threads(1);
    if(argc==2&&std::string(argv[1])=="controls"){controls();return 0;}
    if(argc!=6)throw std::runtime_error("index query.fbin ef-comma-list output-prefix events|none");
    if(FAISS_VERSION_MAJOR!=1||FAISS_VERSION_MINOR!=8||FAISS_VERSION_PATCH!=0)throw std::runtime_error("header version");
    std::unique_ptr<faiss::Index> owned(faiss::read_index(argv[1]));
    auto* mapped=dynamic_cast<faiss::IndexIDMap2*>(owned.get());
    auto* core=mapped?dynamic_cast<faiss::IndexHNSWFlat*>(mapped->index):nullptr;
    if(!core||mapped->ntotal!=core->ntotal||mapped->id_map.size()!=size_t(core->ntotal))throw std::runtime_error("exact index type/cardinality");
    std::ifstream input(argv[2],std::ios::binary);uint32_t n=get<uint32_t>(input),dim=get<uint32_t>(input);
    if((n!=500&&n!=1000)||int(dim)!=core->d)throw std::runtime_error("registered query shape");
    std::vector<float> q(size_t(n)*dim);input.read(reinterpret_cast<char*>(q.data()),q.size()*4);
    if(!input||input.peek()!=EOF)throw std::runtime_error("query EOF");
    for(float x:q)if(!std::isfinite(x))throw std::runtime_error("query finite");
    std::vector<int32_t> actions;std::string s=argv[3];size_t p=0;
    while(p<s.size()){size_t end=s.find(',',p);std::string a=s.substr(p,end-p);int v=std::stoi(a);if(v<16||v>4096||(v&(v-1)))throw std::runtime_error("registered action");actions.push_back(v);if(end==std::string::npos)break;p=end+1;}
    if(actions.empty())throw std::runtime_error("no action");
    std::string prefix=argv[4];std::ifstream existing(prefix+".responses.bin");if(existing.good())throw std::runtime_error("exclusive response");
    std::ofstream responses(prefix+".responses.bin",std::ios::binary);responses.write("E6RS",4);put(responses,n);put(responses,dim);
    const bool events=std::string(argv[5])=="events";if(!events&&std::string(argv[5])!="none")throw std::runtime_error("trace mode");
    std::ofstream trace;
    if(events){std::ifstream old(prefix+".events.bin");if(old.good())throw std::runtime_error("exclusive trace");trace.open(prefix+".events.bin",std::ios::binary);trace.write("E6EV",4);put(trace,n);put(trace,dim);}
    Ledger l;l.ids=&mapped->id_map;l.trace=events?&trace:nullptr;CountStorage proxy(*core->storage,l);
    faiss::Index* old=core->storage;core->storage=&proxy;
    struct Restore{faiss::IndexHNSW& c;faiss::Index* s;~Restore(){c.storage=s;}} restore{*core,old};
    std::cout<<"COUNT_RUNTIME_READY "<<faiss::get_compile_options()<<" ntotal "<<core->ntotal<<" metric "<<core->metric_type<<std::endl;sleep(1);
    for(int32_t ef:actions){core->hnsw.efSearch=ef;
        for(uint32_t i=0;i<n;++i){l.ef=ef;l.q=int32_t(i);l.scalar=l.batch=0;float distances[10];idx_t labels[10];
            mapped->search(1,q.data()+size_t(i)*dim,10,distances,labels);
            uint64_t count=l.scalar+4*l.batch;if(!count)throw std::runtime_error("no calls");
            put(responses,l.ef);put(responses,l.q);put(responses,l.scalar);put(responses,l.batch);put(responses,count);
            for(idx_t x:labels){if(x<0)throw std::runtime_error("invalid returned ID");put(responses,x);}
            for(float x:distances){if(!std::isfinite(x))throw std::runtime_error("invalid returned score");put(responses,x);}
        }
        std::cout<<"action "<<ef<<" queries "<<n<<std::endl;
    }
    responses.close();if(events)trace.close();std::cout<<"NEW_MEASUREMENT_COMPLETE_NOT_LATENCY"<<std::endl;
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}
