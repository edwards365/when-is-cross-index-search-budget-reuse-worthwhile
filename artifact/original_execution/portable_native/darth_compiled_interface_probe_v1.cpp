// Isolated positional transport probe. Not the historical native DARTH method.
#include <LightGBM/c_api.h>
#include <array>
#include <dlfcn.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>

static void check(int status) {
  if (status != 0) throw std::runtime_error(LGBM_GetLastError());
}

int main(int argc, char** argv) {
  try {
    if (argc != 2) throw std::runtime_error("require newly authored synthetic model path");
    std::ifstream input(argv[1], std::ios::binary);
    if (!input) throw std::runtime_error("synthetic model unavailable");
    const std::string text((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    if (text.size() > 65536) throw std::runtime_error("model size cap");
    BoosterHandle booster = nullptr;
    int iterations = 0;
    check(LGBM_BoosterLoadModelFromString(text.c_str(), &iterations, &booster));
    if (iterations != 11) throw std::runtime_error("require eleven authored stumps");
    Dl_info library{};
    if (!dladdr(reinterpret_cast<void*>(&LGBM_BoosterPredictForMatSingleRow), &library))
      throw std::runtime_error("library resolution unavailable");
    std::cout << "LIBRARY\t" << library.dli_fname << '\n';
    // Canonical trainer positions, followed by source-derived native array.
    for (int row = 0; row < 11; ++row) {
      std::array<double, 11> canonical{};
      canonical[row] = 1.0;
      int nstep = static_cast<int>(canonical[0]);
      int ndis = static_cast<int>(canonical[1]);
      int total_insertions = static_cast<int>(canonical[2]);
      float first_nn_dis = static_cast<float>(canonical[3]);
      float nn_dist = static_cast<float>(canonical[4]);
      float furthest_dist = static_cast<float>(canonical[5]);
      float avg_dist = static_cast<float>(canonical[6]);
      float variance = static_cast<float>(canonical[7]);
      float percentile_25 = static_cast<float>(canonical[8]);
      float median = static_cast<float>(canonical[9]);
      float percentile_75 = static_cast<float>(canonical[10]);
      const double data[11] = {
          (double)nstep,
          (double)ndis,
          (double)total_insertions,
          (double)first_nn_dis,
          nn_dist,
          avg_dist,
          furthest_dist,
          variance,
          median,
          percentile_25,
          percentile_75};
      // Prospective control only: never applied to the original method/model.
      constexpr int map[11] = {0, 1, 2, 3, 4, 6, 5, 7, 9, 8, 10};
      std::array<double, 11> restored{};
      for (int j = 0; j < 11; ++j) restored[j] = data[map[j]];
      const double* arms[3] = {canonical.data(), data, restored.data()};
      for (int arm = 0; arm < 3; ++arm) {
        for (int tree = 0; tree < 11; ++tree) {
          int64_t length = 0;
          double result = -999;
          check(LGBM_BoosterPredictForMatSingleRow(booster, arms[arm], C_API_DTYPE_FLOAT64,
                11, 1, C_API_PREDICT_NORMAL, tree, 1, "num_threads=1", &length, &result));
          if (length != 1) throw std::runtime_error("prediction length mismatch");
          std::cout << "PRED\t" << arm << '\t' << row << '\t' << tree << '\t' << result << '\n';
        }
      }
    }
    check(LGBM_BoosterFree(booster));
    return 0;
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
