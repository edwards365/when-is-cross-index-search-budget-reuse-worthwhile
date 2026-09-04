#include "hnswlib/hnswlib.h"
#include <fstream>
#include <iostream>
#include <random>
#include <string>
int main(int argc,char**argv){
 if(argc!=6){std::cerr<<"usage: cals_id_roundtrip_audit INDEX DIM BUILD N OUTPUT\n";return 2;}
 hnswlib::L2Space space(std::stoul(argv[2]));hnswlib::HierarchicalNSW<float> idx(&space,argv[1],false);size_t n=std::stoull(argv[4]);std::mt19937_64 rng(991);std::uniform_int_distribution<uint64_t>d(0,idx.cur_element_count-1);std::ofstream o(argv[5]);o<<"build_id,sample_id,internal_tableint,external_label,roundtrip_internal,roundtrip_external,internal_external_internal_ok,external_internal_external_ok\n";
 for(size_t i=0;i<n;i++){auto in=(hnswlib::tableint)d(rng);auto ex=idx.getExternalLabel(in);auto it=idx.label_lookup_.find(ex);if(it==idx.label_lookup_.end())return 3;auto in2=it->second;auto ex2=idx.getExternalLabel(in2);o<<argv[3]<<','<<i<<','<<in<<','<<ex<<','<<in2<<','<<ex2<<','<<(in==in2)<<','<<(ex==ex2)<<'\n';}
 return 0;
}
