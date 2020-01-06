#ifndef HAWKTRACER_INTEGRATION_TESTS_SCOPED_TEST_HELPER_HPP
#define HAWKTRACER_INTEGRATION_TESTS_SCOPED_TEST_HELPER_HPP

#include "scoped_test_initializer.hpp"

#define DEFINE_TEST(TEST_NAME) \
    int main(int argc, char** argv) { \
        ScopedTestInitializer s(argc, argv); \
        TEST_NAME(); \
        return 0; \
    }

#endif /* HAWKTRACER_INTEGRATION_TESTS_SCOPED_TEST_HELPER_HPP */