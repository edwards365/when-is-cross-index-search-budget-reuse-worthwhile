#include "hnswlib/hnswlib.h"
#include "hnswlib/space_l2.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
int main(int argc,char**argv){
  if(argc!=5){std::cerr<<"usage: cals_registry_resolve INDEX DIM INTERNAL_CSV OUTPUT_CSV\n";return 2;}
  hnswlib::L2Space space(std::stoul(argv[2])); hnswlib::HierarchicalNSW<float> index(&space,argv[1],false);
  std::ifstream in(argv[3]); std::ofstream out(argv[4]); if(!in||!out)return 1;
  out<<"external_label,internal_tableint,build_id\n"; std::string line; int n=0;
  while(std::getline(in,line)){if(line.empty()||line=="portal_id")continue; auto id=(hnswlib::tableint)std::stoul(line); if(id>=index.cur_element_count) return 3; out<<index.getExternalLabel(id)<<","<<id<<","<<argv[1]<<"\n"; ++n;}
  std::cout<<"resolved="<<n<<"\n"; return 0;
}
