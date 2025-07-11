#include <iostream>
#include <iomanip>
#include <chrono>
#include "sm3_optimized.h"

int main() {
    const size_t msg_size = 4 * 1024 * 1024;  // 每条消息大小：4MB
    const int loops = 50;                     // 重复处理 50 次，总量 200MB

    std::vector<u8> msg(msg_size, 0x61);      // 填充内容 'a'

    // 功能验证
    auto digest = sm3((const u8*)"abc", 3);
    std::cout << "SM3(\"abc\") = ";
    for (auto b : digest)
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)b;
    std::cout << std::endl;

    // 性能测试
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < loops; ++i) {
        volatile auto hash = sm3(msg.data(), msg_size);
    }
    auto end = std::chrono::high_resolution_clock::now();

    double seconds = std::chrono::duration<double>(end - start).count();
    double total_mb = (double)(msg_size * loops) / (1024 * 1024);
    double throughput = total_mb / seconds;

    std::cout << "SM3 throughput: " << throughput << " MB/s" << std::endl;
    return 0;
}
