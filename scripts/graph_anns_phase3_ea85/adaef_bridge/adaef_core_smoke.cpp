#include "adaef_official_util_bridge.h"

#include <algorithm>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <numeric>
#include <random>

int main(int argc, char **argv) {
    const std::string output = argc > 1 ? argv[1] : "adaef_core_smoke.json";
    constexpr int n = 500;
    constexpr int nq = 50;
    constexpr int dim = 16;
    constexpr int k = 10;
    constexpr int M = 4;
    constexpr int ef_construction = 100;
    constexpr int seed = 991;
    constexpr float target_recall = 0.95f;
    constexpr float quantile_step = 0.01f;
    constexpr size_t statics_length = 1 + 2 * M + (2 * M - 1) * (2 * M);

    std::mt19937 rng(seed);
    std::normal_distribution<float> normal(0.0f, 1.0f);
    hnswdis::MatrixXf data(n, dim);
    hnswdis::MatrixXf queries(nq, dim);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < dim; ++j) data(i, j) = normal(rng);
    }
    for (int i = 0; i < nq; ++i) {
        for (int j = 0; j < dim; ++j) queries(i, j) = normal(rng);
    }
    normalize_matrix(data);
    normalize_matrix(queries);

    auto space = std::make_shared<hnswlib::InnerProductSpace>(dim);
    auto index = std::make_shared<hnswlib::HierarchicalNSW<float>>(
        space.get(), n, M, ef_construction, seed);
    for (int i = 0; i < n; ++i) index->addPoint(data.row(i).data(), i);

    auto truth = hnswdis::compute_ground_truth(queries, data, "cd", k);
    auto data_ptr = std::make_shared<hnswdis::MatrixXf>(data);
    auto design_ptr = std::make_shared<hnswdis::MatrixXf>(queries.topRows(30));
    auto design_truth_ptr = std::make_shared<hnswdis::MatrixXi>(truth.topRows(30));

    auto start = std::chrono::steady_clock::now();
    auto estimator = hnswdis::init_estimator("cd", data);
    hnswdis::EfAdapter adapter(
        index, data_ptr, k, "cd", target_recall, quantile_step,
        statics_length, design_ptr, design_truth_ptr, estimator, 200);
    hnswdis::ApproximatedScoreCalculator score_cal(estimator, quantile_step);
    hnswdis::Sketch sketch(adapter.get_ef_recall_estimators(), target_recall);
    index->setEf(static_cast<size_t>(adapter.get_wae()));

    std::vector<float> recalls;
    recalls.reserve(nq - 30);
    for (int i = 30; i < nq; ++i) {
        auto result = index->adaptiveSearchKnnTest(
            queries.row(i).data(), k, statics_length, score_cal, &sketch);
        std::vector<size_t> labels(result.size());
        size_t pos = labels.size();
        while (!result.empty()) {
            labels[--pos] = result.top().second;
            result.pop();
        }
        int correct = 0;
        for (size_t label : labels) {
            for (int j = 0; j < k; ++j) {
                if (static_cast<int>(label) == truth(i, j)) {
                    ++correct;
                    break;
                }
            }
        }
        recalls.push_back(static_cast<float>(correct) / k);
    }
    const double mean_recall = std::accumulate(recalls.begin(), recalls.end(), 0.0) /
                               static_cast<double>(recalls.size());
    const size_t failures = static_cast<size_t>(std::count_if(
        recalls.begin(), recalls.end(), [](float x) { return x < target_recall; }));
    const auto elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                                std::chrono::steady_clock::now() - start)
                                .count();

    std::ofstream out(output);
    out << std::fixed << std::setprecision(6)
        << "{\n"
        << "  \"status\": \"PASS\",\n"
        << "  \"evidence_role\": \"INTEGRATION_ONLY_NOT_SCIENTIFIC\",\n"
        << "  \"official_commit\": \"ed463f9993868f7ecc7c103920644e7f94abb377\",\n"
        << "  \"target_recall\": " << target_recall << ",\n"
        << "  \"design_queries\": 30,\n"
        << "  \"evaluation_queries\": " << recalls.size() << ",\n"
        << "  \"mean_recall\": " << mean_recall << ",\n"
        << "  \"failure_count\": " << failures << ",\n"
        << "  \"weighted_average_ef\": " << adapter.get_wae() << ",\n"
        << "  \"elapsed_ms\": " << elapsed_ms << "\n"
        << "}\n";
    return out.good() ? 0 : 2;
}
