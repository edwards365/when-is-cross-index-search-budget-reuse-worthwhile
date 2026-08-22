#include "narhnsw/resistance.hpp"

#include <algorithm>
#include <cmath>
#include <queue>
#include <stdexcept>

namespace narhnsw {
namespace {

Matrix inverse(Matrix a) {
    const std::size_t n = a.size();
    Matrix augmented(n, std::vector<double>(2 * n, 0.0));
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = 0; j < n; ++j) augmented[i][j] = a[i][j];
        augmented[i][n + i] = 1.0;
    }
    for (std::size_t column = 0; column < n; ++column) {
        std::size_t pivot = column;
        for (std::size_t row = column + 1; row < n; ++row) {
            if (std::abs(augmented[row][column]) > std::abs(augmented[pivot][column])) pivot = row;
        }
        if (std::abs(augmented[pivot][column]) < 1e-14) throw std::runtime_error("singular matrix");
        std::swap(augmented[pivot], augmented[column]);
        const double scale = augmented[column][column];
        for (double& value : augmented[column]) value /= scale;
        for (std::size_t row = 0; row < n; ++row) {
            if (row == column) continue;
            const double factor = augmented[row][column];
            for (std::size_t j = 0; j < 2 * n; ++j) augmented[row][j] -= factor * augmented[column][j];
        }
    }
    Matrix result(n, std::vector<double>(n));
    for (std::size_t i = 0; i < n; ++i)
        for (std::size_t j = 0; j < n; ++j) result[i][j] = augmented[i][n + j];
    return result;
}

void validate(const Matrix& weights) {
    const std::size_t n = weights.size();
    if (n == 0) throw std::invalid_argument("empty graph");
    for (std::size_t i = 0; i < n; ++i) {
        if (weights[i].size() != n) throw std::invalid_argument("weights must be square");
        for (std::size_t j = 0; j < n; ++j) {
            if (!std::isfinite(weights[i][j]) || weights[i][j] < 0.0)
                throw std::invalid_argument("weights must be finite and nonnegative");
            if (std::abs(weights[i][j] - weights[j][i]) > 1e-12)
                throw std::invalid_argument("weights must be symmetric");
        }
    }
    std::vector<bool> seen(n, false);
    std::queue<std::size_t> frontier;
    seen[0] = true;
    frontier.push(0);
    while (!frontier.empty()) {
        const auto u = frontier.front();
        frontier.pop();
        for (std::size_t v = 0; v < n; ++v) {
            if (weights[u][v] > 0.0 && !seen[v]) {
                seen[v] = true;
                frontier.push(v);
            }
        }
    }
    if (std::find(seen.begin(), seen.end(), false) != seen.end())
        throw std::invalid_argument("exact C++ reference requires a connected graph");
}

}  // namespace

Matrix effective_resistance(const Matrix& weights) {
    validate(weights);
    const std::size_t n = weights.size();
    Matrix shifted(n, std::vector<double>(n, 1.0 / static_cast<double>(n)));
    for (std::size_t i = 0; i < n; ++i) {
        double degree = 0.0;
        for (std::size_t j = 0; j < n; ++j) degree += weights[i][j];
        shifted[i][i] += degree;
        for (std::size_t j = 0; j < n; ++j) shifted[i][j] -= weights[i][j];
    }
    Matrix shifted_inverse = inverse(std::move(shifted));
    Matrix result(n, std::vector<double>(n));
    for (std::size_t i = 0; i < n; ++i)
        for (std::size_t j = 0; j < n; ++j)
            result[i][j] = std::max(0.0, shifted_inverse[i][i] + shifted_inverse[j][j] -
                                             2.0 * shifted_inverse[i][j]);
    return result;
}

Matrix edge_leverage(const Matrix& weights, const Matrix& resistance) {
    if (weights.size() != resistance.size()) throw std::invalid_argument("shape mismatch");
    Matrix result = weights;
    for (std::size_t i = 0; i < weights.size(); ++i) {
        if (weights[i].size() != resistance[i].size()) throw std::invalid_argument("shape mismatch");
        for (std::size_t j = 0; j < weights.size(); ++j) result[i][j] *= resistance[i][j];
    }
    return result;
}

}  // namespace narhnsw

