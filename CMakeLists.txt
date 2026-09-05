cmake_minimum_required(VERSION 3.20)
project(narhnsw VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(narhnsw_core cpp/src/resistance.cpp)
target_include_directories(narhnsw_core PUBLIC cpp/include)
if(MSVC)
  target_compile_options(narhnsw_core PRIVATE /W4 /permissive-)
else()
  target_compile_options(narhnsw_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(narhnsw_smoke cpp/src/main.cpp)
target_link_libraries(narhnsw_smoke PRIVATE narhnsw_core)

add_executable(hnsw_instrumented_smoke cpp/src/hnsw_instrumented_smoke.cpp)
target_include_directories(hnsw_instrumented_smoke PRIVATE cpp/include third_party/hnswlib)

add_executable(hnsw_apply_selection_plan cpp/src/hnsw_apply_selection_plan.cpp)
target_include_directories(hnsw_apply_selection_plan PRIVATE cpp/include third_party/hnswlib)

add_executable(hnsw_gate_a_benchmark cpp/src/hnsw_gate_a_benchmark.cpp)
target_include_directories(hnsw_gate_a_benchmark PRIVATE cpp/include third_party/hnswlib)

add_executable(hnsw_record_candidates cpp/src/hnsw_record_candidates.cpp)
target_include_directories(hnsw_record_candidates PRIVATE cpp/include third_party/hnswlib)

add_executable(hnsw_r0_trace_existing cpp/src/hnsw_r0_trace_existing.cpp)
target_include_directories(hnsw_r0_trace_existing PRIVATE cpp/include third_party/hnswlib)

add_executable(hnsw_replay_layer0_plan cpp/src/hnsw_replay_layer0_plan.cpp)
target_include_directories(hnsw_replay_layer0_plan PRIVATE cpp/include third_party/hnswlib)

add_executable(hnsw_e0_evaluate_index cpp/src/hnsw_e0_evaluate_index.cpp)
add_executable(icba_o4_bridge cpp/src/icba_o4_bridge.cpp)
add_executable(cals_mechanical_smoke cpp/src/cals_mechanical_smoke.cpp)
add_executable(cals_registry_resolve cpp/src/cals_registry_resolve.cpp)
target_include_directories(cals_registry_resolve PRIVATE cpp/include third_party/hnswlib)
add_executable(cals_semantic_reaudit cpp/src/cals_semantic_reaudit.cpp)
target_include_directories(cals_semantic_reaudit PRIVATE cpp/include third_party/hnswlib)
add_executable(cals_fixed_portal_runner cpp/src/cals_fixed_portal_runner.cpp)
target_include_directories(cals_fixed_portal_runner PRIVATE cpp/include third_party/hnswlib)

add_executable(bn_apd_observable_trace cpp/src/bn_apd_observable_trace.cpp)
target_include_directories(bn_apd_observable_trace PRIVATE cpp/include third_party/hnswlib)
add_executable(cals_id_roundtrip_audit cpp/src/cals_id_roundtrip_audit.cpp)
target_include_directories(cals_id_roundtrip_audit PRIVATE cpp/include third_party/hnswlib)
target_include_directories(cals_mechanical_smoke PRIVATE cpp/include third_party/hnswlib)
target_include_directories(icba_o4_bridge PRIVATE cpp/include third_party/hnswlib)
target_include_directories(hnsw_e0_evaluate_index PRIVATE cpp/include third_party/hnswlib)

add_executable(hnsw_d0_compare_indexes cpp/src/hnsw_d0_compare_indexes.cpp)
target_include_directories(hnsw_d0_compare_indexes PRIVATE cpp/include third_party/hnswlib)

add_executable(hnsw_d0_counterfactual_search cpp/src/hnsw_d0_counterfactual_search.cpp)
target_include_directories(hnsw_d0_counterfactual_search PRIVATE cpp/include third_party/hnswlib)

add_executable(hnsw_sgdr_gate_o_search cpp/src/hnsw_sgdr_gate_o_search.cpp)
target_include_directories(hnsw_sgdr_gate_o_search PRIVATE cpp/include third_party/hnswlib)

enable_testing()
add_executable(test_resistance_cpp tests/cpp/test_resistance.cpp)
target_link_libraries(test_resistance_cpp PRIVATE narhnsw_core)
add_test(NAME resistance_cpp COMMAND test_resistance_cpp)
add_executable(test_hnsw_selected_connector tests/cpp/test_hnsw_selected_connector.cpp)
target_include_directories(test_hnsw_selected_connector PRIVATE cpp/include third_party/hnswlib)
add_test(NAME hnsw_selected_connector_cpp COMMAND test_hnsw_selected_connector)
add_test(NAME hnsw_instrumented_cpp COMMAND hnsw_instrumented_smoke)
