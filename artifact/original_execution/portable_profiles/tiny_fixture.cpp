// Synthetic delivery test only, not an experimental graph constructor.
#include "hnswlib/hnswlib.h"
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
int main(int argc,char**argv) {
  if(argc!=4) return 2;
  std::unique_ptr<hnswlib::SpaceInterface<float>> space;
  if(std::string(argv[2])=="l2") space.reset(new hnswlib::L2Space(4));
  else if(std::string(argv[2])=="ip") space.reset(new hnswlib::InnerProductSpace(4));
  else return 2;
  hnswlib::HierarchicalNSW<float> graph(space.get(),32,16,100,719);
  std::ifstream in(argv[1],std::ios::binary);
  for(size_t i=0;i<32;++i){float v[4];in.read(reinterpret_cast<char*>(v),sizeof(v));if(!in)return 1;graph.addPoint(v,i);}
  if(in.peek()!=std::char_traits<char>::eof())return 1;
  graph.saveIndex(argv[3]);return 0;
}
