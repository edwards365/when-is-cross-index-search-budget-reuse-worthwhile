#include <H5Cpp.h>
#include <omp.h>
#include "hnswlib/adaptive_ef.h"

#include <atomic>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr size_t k = 10;
constexpr size_t dim = 768;
constexpr size_t expected_base = 1342143;
constexpr int m = 16;
constexpr int ef_construction = 500;
constexpr int ef_upper_bound = 2400;
constexpr int endpoint_ef = 2400;
constexpr float target_recall = 0.95f;
constexpr float quantile_step = 0.001f;
constexpr size_t statistics_length = 1025;

struct CountParams {
    size_t dimension;
    hnswlib::DISTFUNC<float> base_function;
    void *base_parameter;
    std::atomic<long> *counter;
};

class CountingInnerProductSpace final : public hnswlib::SpaceInterface<float> {
  public:
    explicit CountingInnerProductSpace(size_t dimension)
        : base_(dimension), params_{dimension, base_.get_dist_func(), base_.get_dist_func_param(), &counter_} {}
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

template <typename Scalar>
std::vector<Scalar> load_vector(H5::H5File &file, const std::string &name, const H5::PredType &type) {
    H5::DataSet dataset = file.openDataSet(name);
    H5::DataSpace space = dataset.getSpace();
    if (space.getSimpleExtentNdims() != 1) throw std::runtime_error(name + " is not rank 1");
    hsize_t size = 0;
    space.getSimpleExtentDims(&size, nullptr);
    std::vector<Scalar> result(size);
    dataset.read(result.data(), type);
    return result;
}

hnswdis::MatrixXf load_float_matrix(H5::H5File &file, const std::string &name) {
    H5::DataSet dataset = file.openDataSet(name);
    H5::DataSpace space = dataset.getSpace();
    hsize_t shape[2];
    if (space.getSimpleExtentNdims() != 2) throw std::runtime_error(name + " is not rank 2");
    space.getSimpleExtentDims(shape, nullptr);
    hnswdis::MatrixXf result(shape[0], shape[1]);
    dataset.read(result.data(), H5::PredType::NATIVE_FLOAT);
    return result;
}

hnswdis::MatrixXi load_int_matrix(H5::H5File &file, const std::string &name) {
    H5::DataSet dataset = file.openDataSet(name);
    H5::DataSpace space = dataset.getSpace();
    hsize_t shape[2];
    if (space.getSimpleExtentNdims() != 2) throw std::runtime_error(name + " is not rank 2");
    space.getSimpleExtentDims(shape, nullptr);
    hnswdis::MatrixXi result(shape[0], shape[1]);
    dataset.read(result.data(), H5::PredType::NATIVE_INT);
    return result;
}

void refuse_existing(const std::string &path) {
    if (std::filesystem::exists(path)) throw std::runtime_error("refusing existing output: " + path);
}

std::vector<long long> ordered_labels(std::priority_queue<std::pair<float, hnswlib::labeltype>> heap) {
    std::vector<long long> labels(heap.size());
    while (!heap.empty()) {
        labels[heap.size() - 1] = static_cast<long long>(heap.top().second);
        heap.pop();
    }
    return labels;
}

double recall(const std::vector<long long> &labels, const hnswdis::MatrixXi &truth, int row) {
    int hits = 0;
    for (long long label : labels) {
        for (int j = 0; j < truth.cols(); ++j) {
            if (label == truth(row, j)) { ++hits; break; }
        }
    }
    return static_cast<double>(hits) / static_cast<double>(k);
}

std::string join(const std::vector<long long> &values) {
    std::ostringstream out;
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) out << ';';
        out << values[i];
    }
    return out.str();
}

void build_design(const std::string &bundle_path, const std::string &index_path,
                  const std::string &adapter_path, const std::string &summary_path,
                  int seed, const std::string &history) {
    refuse_existing(index_path);
    refuse_existing(adapter_path);
    refuse_existing(summary_path);
    H5::H5File file(bundle_path, H5F_ACC_RDONLY);
    auto data = load_float_matrix(file, "train");
    auto raw_ids = load_vector<long long>(file, "raw_ids", H5::PredType::NATIVE_LLONG);
    const std::string order_name = history == "random" ? "order_seed" + std::to_string(seed) + "_random" : "order_norm_ascending";
    if (history != "random" && history != "norm_ascending") throw std::runtime_error("invalid history");
    auto order = load_vector<unsigned long long>(file, order_name, H5::PredType::NATIVE_ULLONG);
    auto queries = load_float_matrix(file, "source_design_queries");
    auto truth = load_int_matrix(file, "source_design_truth");
    if (data.rows() != expected_base || data.cols() != dim || raw_ids.size() != expected_base
            || order.size() != expected_base || queries.rows() != 500 || queries.cols() != dim
            || truth.rows() != 500 || truth.cols() != k) throw std::runtime_error("frozen shape mismatch");
    std::vector<unsigned char> seen(expected_base, 0);
    for (auto position : order) {
        if (position >= expected_base || seen[position]) throw std::runtime_error("invalid insertion order");
        seen[position] = 1;
    }
    auto data_ptr = std::make_shared<hnswdis::MatrixXf>(std::move(data));
    auto query_ptr = std::make_shared<hnswdis::MatrixXf>(std::move(queries));
    auto truth_ptr = std::make_shared<hnswdis::MatrixXi>(std::move(truth));
    auto space = std::make_shared<CountingInnerProductSpace>(dim);
    auto index = std::make_shared<hnswlib::HierarchicalNSW<float>>(space.get(), expected_base, m, ef_construction, seed);
    const auto build_start = std::chrono::steady_clock::now();
    for (size_t i = 0; i < order.size(); ++i) {
        const size_t position = static_cast<size_t>(order[i]);
        index->addPoint(data_ptr->row(position).data(), static_cast<hnswlib::labeltype>(raw_ids[position]));
        if ((i + 1) % 100000 == 0) std::cout << "inserted=" << (i + 1) << '/' << order.size() << std::endl;
    }
    const double build_seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - build_start).count();
    if (index->getCurrentElementCount() != expected_base) throw std::runtime_error("index count mismatch");
    index->saveIndex(index_path);
    auto estimator = hnswdis::init_estimator("cd", *data_ptr);
    const auto adapter_start = std::chrono::steady_clock::now();
    hnswdis::EfAdapter adapter(index, data_ptr, k, "cd", target_recall, quantile_step,
                               statistics_length, query_ptr, truth_ptr, estimator, ef_upper_bound);
    const double adapter_seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - adapter_start).count();
    adapter.serialize(adapter_path);
    hnswdis::EfAdapter reloaded(adapter_path);
    if (reloaded.get_wae() != adapter.get_wae()) throw std::runtime_error("adapter reload mismatch");
    std::ofstream out(summary_path, std::ios::out | std::ios::trunc);
    out << std::fixed << std::setprecision(6)
        << "{\n  \"status\": \"DESIGN_COMPLETE_TARGET_ROLES_UNACCESSED\",\n"
        << "  \"seed\": " << seed << ",\n  \"history\": \"" << history << "\",\n"
        << "  \"base_rows\": " << expected_base << ",\n  \"dimension\": " << dim << ",\n"
        << "  \"source_design_queries\": 500,\n  \"M\": " << m << ",\n"
        << "  \"ef_construction\": " << ef_construction << ",\n"
        << "  \"ef_upper_bound\": " << ef_upper_bound << ",\n"
        << "  \"weighted_average_ef\": " << adapter.get_wae() << ",\n"
        << "  \"build_seconds_exploratory_only\": " << build_seconds << ",\n"
        << "  \"adapter_seconds\": " << adapter_seconds << ",\n"
        << "  \"forbidden_roles_accessed\": []\n}\n";
}

void run_role(const std::string &bundle_path, const std::string &role,
              const std::string &index_path, const std::string &adapter_path,
              const std::string &output_path, size_t limit) {
    if (role != "source_design" && role != "target_selection" && role != "target_certification" && role != "target_evaluation")
        throw std::runtime_error("invalid role");
    refuse_existing(output_path);
    H5::H5File file(bundle_path, H5F_ACC_RDONLY);
    auto data = load_float_matrix(file, "train");
    auto queries = load_float_matrix(file, role + "_queries");
    auto truth = load_int_matrix(file, role + "_truth");
    auto query_ids = load_vector<long long>(file, role + "_query_ids", H5::PredType::NATIVE_LLONG);
    if (data.rows() != expected_base || data.cols() != dim || queries.cols() != dim
            || queries.rows() != truth.rows() || queries.rows() != static_cast<int>(query_ids.size())
            || truth.cols() != k || limit == 0 || limit > static_cast<size_t>(queries.rows()))
        throw std::runtime_error("role shape/limit mismatch");
    auto space = std::make_shared<CountingInnerProductSpace>(dim);
    auto index = std::make_shared<hnswlib::HierarchicalNSW<float>>(space.get(), index_path);
    if (index->getCurrentElementCount() != expected_base) throw std::runtime_error("loaded index count mismatch");
    auto estimator = hnswdis::init_estimator("cd", data);
    hnswdis::ApproximatedScoreCalculator score_cal(estimator, quantile_step);
    hnswdis::EfAdapter adapter(adapter_path);
    hnswdis::Sketch sketch(adapter.get_ef_recall_estimators(), target_recall);
    const size_t raw_base_ef = std::max(static_cast<size_t>(adapter.get_wae()), k);
    if (raw_base_ef > ef_upper_bound) throw std::runtime_error("adapter base ef exceeds frozen bound");
    std::ofstream out(output_path, std::ios::out | std::ios::trunc);
    out << "query_id,raw_action_ef,raw_score,raw_recall,raw_ndc,raw_topk,endpoint_ef,endpoint_recall,endpoint_ndc,endpoint_topk\n";
    for (size_t i = 0; i < limit; ++i) {
        index->setEf(raw_base_ef);
        space->reset();
        auto adaptive = index->adaptiveSearchKnn(queries.row(i).data(), k, statistics_length, score_cal, &sketch);
        const long raw_ndc = space->count();
        const size_t raw_action = std::max(raw_base_ef, sketch.estimate_ef2(adaptive.second));
        if (raw_action < k || raw_action > ef_upper_bound) throw std::runtime_error("adaptive action outside frozen bound");
        auto raw_labels = ordered_labels(std::move(adaptive.first));
        index->setEf(endpoint_ef);
        space->reset();
        auto endpoint_labels = ordered_labels(index->searchKnn(queries.row(i).data(), k));
        const long endpoint_ndc = space->count();
        if (raw_labels.size() != k || endpoint_labels.size() != k || raw_ndc <= 0 || endpoint_ndc <= 0)
            throw std::runtime_error("invalid native response");
        out << query_ids[i] << ',' << raw_action << ',' << adaptive.second << ','
            << recall(raw_labels, truth, i) << ',' << raw_ndc << ',' << join(raw_labels) << ','
            << endpoint_ef << ',' << recall(endpoint_labels, truth, i) << ',' << endpoint_ndc << ','
            << join(endpoint_labels) << '\n';
    }
}

}  // namespace

int main(int argc, char **argv) {
    try {
        if (argc < 2) throw std::runtime_error("missing mode");
        const std::string mode = argv[1];
        if (mode == "build-design" && argc == 8) {
            build_design(argv[2], argv[3], argv[4], argv[5], std::stoi(argv[6]), argv[7]);
        } else if (mode == "run-role" && argc == 8) {
            run_role(argv[2], argv[3], argv[4], argv[5], argv[6], std::stoull(argv[7]));
        } else {
            throw std::runtime_error("usage: build-design BUNDLE INDEX ADAPTER SUMMARY SEED HISTORY | run-role BUNDLE ROLE INDEX ADAPTER OUTPUT LIMIT");
        }
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "E2_ADAEF_ERROR: " << error.what() << '\n';
        return 2;
    }
}
