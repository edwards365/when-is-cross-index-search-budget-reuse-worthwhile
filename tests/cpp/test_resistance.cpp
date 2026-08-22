#include "narhnsw/resistance.hpp"

#include <cmath>
#include <iostream>

int main() {
    const narhnsw::Matrix path{{0, 2, 0}, {2, 0, 4}, {0, 4, 0}};
    const auto resistance = narhnsw::effective_resistance(path);
    const auto leverage = narhnsw::edge_leverage(path, resistance);
    if (std::abs(resistance[0][2] - 0.75) > 1e-10) return 1;
    if (std::abs(leverage[0][1] - 1.0) > 1e-10) return 2;
    if (std::abs(leverage[1][2] - 1.0) > 1e-10) return 3;
    std::cout << "weighted path resistance and bridge leverage verified\n";
    return 0;
}

