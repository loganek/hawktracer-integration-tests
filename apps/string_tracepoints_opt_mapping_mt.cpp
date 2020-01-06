#include <cstdio>
#include <string>

#include "test_helper.hpp"

static void string_tracepoints_opt_mapping_mt()
{
    HT_G_TRACE_OPT_STATIC("hello_world()");
    
    slow_down_us(3);

    for (int i = 0; i < 100; i++)
    {
        HT_G_TRACE_OPT_STATIC("iteration");
        printf("2 * %d = %d\n", i, 2*i);

        slow_down_us(3);

        std::string txt = "Iteration (mod 10): " + std::to_string(i % 10);
        HT_G_TRACE_OPT_DYNAMIC(txt.c_str());
        printf("text: %s\n", txt.c_str());
    
        slow_down_us(3);
    }
}

DEFINE_TEST(string_tracepoints_opt_mapping_mt)
