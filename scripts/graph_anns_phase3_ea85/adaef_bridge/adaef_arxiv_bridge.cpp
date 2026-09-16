#include "adaef_official_util_bridge.h"

#include <atomic>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>

namespace {

constexpr int k = 10;
constexpr int m = 16;
constexpr int ef_construction = 500;
constexpr int fixed_safe_ef = 200;
constexpr float target_recall = 0.95f;
constexpr float quantile_step = 0.001f;
constexpr size_t statics_length = 1 + 2 * m + (2 * m - 1) * (2 * m);

struct CountParams {
    hnswlib::DISTFUNC<float> base_function;
    void *base_parameter;
    std::atomic<long> *counter;
};

class CountingInnerProductSpace final : public hnswlib::SpaceInterface<float> {
  public:
    explicit CountingInnerProductSpace(size_t dimension)
        : base_(dimension), params_{base_.get_dist_func(), base_.get_dist_func_param(), &counter_} {}

    size_t get_data_size() override { return base_.get_data_size(); }
    hnswlib::DISTFUNC<float> get_dist_func() override { return &counted_distance; }
    void *get_dist_func_param() override { return &params_; }
    void reset() { counter_.store(0); }
    long count() const { return counter_.load(); }

  private:
    static float counted_distance(const void *left, const void *right, const void *parameter) {
        auto *params = const_cast<CountParams *>(static_cast<const CountParams *>(parameter));
        params->counter->fetch_add(1, std::memory_order_relaxed);
        return params->base_function(left, right, params->base_parameter);
    }

    hnswlib::InnerProductSpace base_;
    std::atomic<long> counter_{0};
    CountParams params_;
};

hnswdis::MatrixXf load_float_matrix(H5::H5File &file, const std::string &name) {
    H5::DataSet dataset = file.openDataSet(name);
    H5::DataSpace space = dataset.getSpace();
    hsize_t dims[2];
    space.getSimpleExtentDims(dims, nullptr);
    hnswdis::MatrixXf result(dims[0], dims[1]);
    dataset.read(result.data(), H5::PredType::NATIVE_FLOAT);
    return result;
}

hnswdis::MatrixXi load_int_matrix(H5::H5File &file, const std::string &name) {
    H5::DataSet dataset = file.openDataSet(name);
    H5::DataSpace space = dataset.getSpace();
    hsize_t dims[2];
    space.getSimpleExtentDims(dims, nullptr);
    hnswdis::MatrixXi result(dims[0], dims[1]);
    dataset.read(result.data(), H5::PredType::NATIVE_INT);
    return result;
}

double recall_at_10(std::priority_queue<std::pair<float, hnswlib::labeltype>> result,
                    const hnswdis::MatrixXi &truth, int row) {
    int matches = 0;
    while (!result.empty()) {
        const auto label = static_cast<int>(result.top().second);
        result.pop();
        for (int j = 0; j < k; ++j) {
            if (label == truth(row, j)) {
                ++matches;
                break;
            }
        }
    }
    return static_cast<double>(matches) / k;
}

void run_design(const std::string &bundle_path, const std::string &index_path,
                const std::string &adapter_path, const std::string &summary_path,
                int seed) {
    H5::H5File file(bundle_path, H5F_ACC_RDONLY);
    auto data = load_float_matrix(file, "train");
    auto queries = load_float_matrix(file, "design_queries");
    auto truth = load_int_matrix(file, "design_truth");
    auto data_ptr = std::make_shared<hnswdis::MatrixXf>(data);
    auto query_ptr = std::make_shared<hnswdis::MatrixXf>(queries);
    auto truth_ptr = std::make_shared<hnswdis::MatrixXi>(truth);
    auto space = std::make_shared<CountingInnerProductSpace>(data.cols());

    const auto build_start = std::chrono::steady_clock::now();
    auto index = std::make_shared<hnswlib::HierarchicalNSW<float>>(
        space.get(), data.rows(), m, ef_construction, seed);
    for (int i = 0; i < data.rows(); ++i) index->addPoint(data.row(i).data(), i);
    const double build_seconds = std::chrono::duration<double>(
                                     std::chrono::steady_clock::now() - build_start)
                                     .count();
    index->saveIndex(index_path);

    const auto offline_start = std::chrono::steady_clock::now();
    auto estimator = hnswdis::init_estimator("cd", data);
    hnswdis::EfAdapter adapter(index, data_ptr, k, "cd", target_recall, quantile_step,
                               statics_length, query_ptr, truth_ptr, estimator,
                               fixed_safe_ef);
    const double offline_seconds = std::chrono::duration<double>(
                                       std::chrono::steady_clock::now() - offline_start)
                                       .count();
    adapter.serialize(adapter_path);

    std::ofstream out(summary_path);
    out << std::fixed << std::setprecision(6)
        << "{\n"
        << "  \"status\": \"DESIGN_COMPLETE_EVALUATION_UNACCESSED\",\n"
        << "  \"seed\": " << seed << ",\n"
        << "  \"index_rows\": " << data.rows() << ",\n"
        << "  \"dimension\": " << data.cols() << ",\n"
        << "  \"design_queries\": " << queries.rows() << ",\n"
        << "  \"target_recall\": " << target_recall << ",\n"
        << "  \"k\": " << k << ",\n"
        << "  \"m\": " << m << ",\n"
        << "  \"ef_construction\": " << ef_construction << ",\n"
        << "  \"fixed_safe_ef\": " << fixed_safe_ef << ",\n"
        << "  \"statics_length\": " << statics_length << ",\n"
        << "  \"weighted_average_ef\": " << adapter.get_wae() << ",\n"
        << "  \"build_seconds\": " << build_seconds << ",\n"
        << "  \"offline_adapter_seconds\": " << offline_seconds << "\n"
        << "}\n";
}

void run_role(const std::string &bundle_path, const std::string &role,
              const std::string &index_path, const std::string &adapter_path,
              const std::string &output_path) {
    if (role != "certification" && role != "evaluation") {
        throw std::runtime_error("role must be certification or evaluation");
    }
    H5::H5File file(bundle_path, H5F_ACC_RDONLY);
    auto data = load_float_matrix(file, "train");
    auto queries = load_float_matrix(file, role + "_queries");
    auto truth = load_int_matrix(file, role + "_truth");
    auto space = std::make_shared<CountingInnerProductSpace>(data.cols());
    auto index = std::make_shared<hnswlib::HierarchicalNSW<float>>(space.get(), index_path);
    auto estimator = hnswdis::init_estimator("cd", data);
    hnswdis::ApproximatedScoreCalculator score_cal(estimator, quantile_step);
    hnswdis::EfAdapter adapter(adapter_path);
    hnswdis::Sketch sketch(adapter.get_ef_recall_estimators(), target_recall);
    const size_t raw_base_ef = std::max(static_cast<size_t>(adapter.get_wae()), static_cast<size_t>(k));

    std::ofstream out(output_path);
    out << "query_id,raw_action_ef,raw_recall,raw_distance_computations,raw_latency_ns,"
           "fixed_safe_ef,fixed_safe_recall,fixed_safe_distance_computations,fixed_safe_latency_ns\n";
    for (int i = 0; i < queries.rows(); ++i) {
        index->setEf(raw_base_ef);
        space->reset();
        const auto raw_start = std::chrono::steady_clock::now();
        auto raw = index->adaptiveSearchKnn(queries.row(i).data(), k, statics_length,
                                            score_cal, &sketch);
        const auto raw_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                                std::chrono::steady_clock::now() - raw_start)
                                .count();
        const long raw_distance = space->count();
        const size_t raw_action = std::max(raw_base_ef, sketch.estimate_ef2(raw.second));
        const double raw_recall = recall_at_10(std::move(raw.first), truth, i);

        index->setEf(fixed_safe_ef);
        space->reset();
        const auto fixed_start = std::chrono::steady_clock::now();
        auto fixed = index->searchKnn(queries.row(i).data(), k);
        const auto fixed_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                                  std::chrono::steady_clock::now() - fixed_start)
                                  .count();
        const long fixed_distance = space->count();
        const double fixed_recall = recall_at_10(std::move(fixed), truth, i);
        out << i << ',' << raw_action << ',' << raw_recall << ',' << raw_distance << ',' << raw_ns
            << ',' << fixed_safe_ef << ',' << fixed_recall << ',' << fixed_distance << ',' << fixed_ns
            << '\n';
    }
}

}  // namespace

int main(int argc, char **argv) {
    try {
        if (argc < 2) throw std::runtime_error("missing mode");
        const std::string mode = argv[1];
        if (mode == "design" && argc == 7) {
            run_design(argv[2], argv[3], argv[4], argv[5], std::stoi(argv[6]));
        } else if (mode == "run-role" && argc == 7) {
            run_role(argv[2], argv[3], argv[4], argv[5], argv[6]);
        } else {
            throw std::runtime_error(
                "usage: design BUNDLE INDEX ADAPTER SUMMARY SEED | "
                "run-role BUNDLE ROLE INDEX ADAPTER OUTPUT");
        }
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "ADA_EF_BRIDGE_ERROR: " << error.what() << '\n';
        return 2;
    }
}
