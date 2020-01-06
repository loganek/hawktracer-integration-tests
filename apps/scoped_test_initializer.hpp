#ifndef HAWKTRACER_INTEGRATION_TESTS_SCOPED_TEST_INITIALIZER_HPP
#define HAWKTRACER_INTEGRATION_TESTS_SCOPED_TEST_INITIALIZER_HPP

#include <hawktracer.h>

#include <string>
#include <variant>

template<class... Ts> struct overload : Ts... { using Ts::operator()...; };
template<class... Ts> overload(Ts...) -> overload<Ts...>;

class ScopedTestInitializer
{
    struct TCPListenerInfo
    {
        int port;
    };

    struct FileListenerInfo
    {
        std::string file_path;
    };
    using ListenerInfo = std::variant<TCPListenerInfo, FileListenerInfo>;

public:
    ScopedTestInitializer(int argc, char** argv);
    ~ScopedTestInitializer();

private:
    static ListenerInfo get_listener_info(int argc, char** argv);

    void _init_listener(const ListenerInfo& listener_info);
    void _destroy_listener();

    std::variant<HT_FileDumpListener*, HT_TCPListener*> _listener;
    HT_Timeline* _timeline;
};

void slow_down_s(size_t seconds);
void slow_down_us(size_t useconds);

#endif /* HAWKTRACER_INTEGRATION_TESTS_SCOPED_TEST_INITIALIZER_HPP */