#include "narhnsw/resistance.hpp"

#include <iostream>

int main() {
    const narhnsw::Matrix path{{0, 1, 0}, {1, 0, 1}, {0, 1, 0}};
    const auto resistance = narhnsw::effective_resistance(path);
    std::cout << "R(0,2)=" << resistance[0][2] << '\n';
    return resistance[0][2] > 1.999 && resistance[0][2] < 2.001 ? 0 : 1;
}

