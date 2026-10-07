#pragma once

#include <cstddef>
#include <vector>

namespace narhnsw {

using Matrix = std::vector<std::vector<double>>;

// Exact resistance for a connected, undirected, nonnegative small graph.
// Uses the identity L^+ = (L + J/n)^-1 - J/n and Gauss-Jordan inversion.
Matrix effective_resistance(const Matrix& weights);
Matrix edge_leverage(const Matrix& weights, const Matrix& resistance);

}  // namespace narhnsw

