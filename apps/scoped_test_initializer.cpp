#include "scoped_test_initializer.hpp"

#include <cstring>
#include <stdexcept>
#include <chrono>
#include <thread>

ScopedTestInitializer::ListenerInfo ScopedTestInitializer::get_listener_info(int argc, char** argv)
{
    for (int i = 0; i < argc - 1; i++)
    {
        if (strcmp(argv[i], "--file") == 0)
        {
            return FileListenerInfo{argv[i+1]};
        }
        if (strcmp(argv[i], "--port") == 0)
        {
            return TCPListenerInfo{std::stoi(argv[i+1])};
        }
    }

    throw std::runtime_error("unable to find listener info");
}


ScopedTestInitializer::ScopedTestInitializer(int argc, char** argv)
{
    ht_init(argc, argv);
    _timeline = ht_global_timeline_get();

    _init_listener(get_listener_info(argc, argv));
}

void ScopedTestInitializer::_init_listener(const ListenerInfo& listener_info)
{
    HT_ErrorCode error;
    std::visit(overload {
        [this, &error] (const TCPListenerInfo& info) { 
            auto l = ht_tcp_listener_create(info.port, 1024, &error); 
            ht_timeline_register_listener(_timeline, ht_tcp_listener_callback, l);
            slow_down_s(2); // wait to establish connection. This can be moved to tcp listener as parameter
            _listener = l;
        },
        [this, &error] (const FileListenerInfo& info) {
            auto l = ht_file_dump_listener_create(info.file_path.c_str(), 1024, &error);
            ht_timeline_register_listener(_timeline, ht_file_dump_listener_callback, l);
            _listener = l;
        }
    }, listener_info);

    if (error != HT_ERR_OK)
    {
        throw std::runtime_error("Failed to create listener. Error code: " + std::to_string(error));
    }
}

void ScopedTestInitializer::_destroy_listener()
{
    HT_ErrorCode error;
    std::visit(overload {
        [this] (HT_TCPListener* listener) { ht_tcp_listener_destroy(listener); },
        [this] (HT_FileDumpListener* listener) { ht_file_dump_listener_destroy(listener); }
    }, _listener);
}

ScopedTestInitializer::~ScopedTestInitializer()
{
    ht_timeline_flush(_timeline);
    _destroy_listener();
    ht_timeline_unregister_all_listeners(_timeline);
    ht_deinit();
}

void slow_down_s(size_t seconds)
{
    slow_down_us(seconds * 1000000);
}

void slow_down_us(size_t useconds)
{
    std::this_thread::sleep_for(std::chrono::microseconds(useconds));
}