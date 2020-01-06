cmake_minimum_required(VERSION 3.10)

set(LIB_VERSION "master" CACHE STRING "HawkTracer library version")
set(LIB_PATH "" CACHE STRING "HawkTracer library path")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(hawktracer.cmake)

add_library(utils scoped_test_initializer.cpp)
target_link_libraries(utils hawktracer)

function(define_test test_name)
    set(test_target "test_${test_name}")
    add_executable(${test_target} ${test_name}.cpp)
    target_link_libraries(${test_target} hawktracer utils)
    install(TARGETS ${test_target} RUNTIME DESTINATION bin)
endfunction(define_test)

define_test(string_tracepoints_no_mapping_single_thread)
define_test(string_tracepoints_opt_mapping_mt)
