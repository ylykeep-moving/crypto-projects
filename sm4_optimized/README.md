# README

# SM4 加密算法优化实验报告

## 一、实验背景与目标

SM4 是国家密码管理局发布的商用对称分组密码算法，广泛应用于金融和国家安全领域。本实验旨在基于 SM4 的基本实现，探索其在软件层面的两种优化路径：

- **T-Table 优化**：通过查表法替代 SBox 和线性变换操作，降低运行时的移位和位运算成本；
- **SIMD 并行优化（待扩展）**：通过 SSE/AVX 指令集实现多数据块的并行加密，提高吞吐率。

## 二、SM4 算法简介

### 2.1 加密流程

SM4 使用 128-bit 密钥，对 128-bit 明文进行 32 轮迭代变换，最终输出 128-bit 密文。主要组件包括：

- **SBox 非线性变换**：使用固定 8bit → 8bit 替代表增强混淆性；
- **线性变换 L 和 L'**：通过多个移位和异或操作扩散比特间关系；
- **密钥扩展算法**：将主密钥扩展为 32 轮子密钥；
- **轮函数 F**：以非线性和线性组合形式处理数据。

### 2.2 CBC 模式（Cipher Block Chaining）

本实验使用 CBC 模式对多个 16 字节块进行加密，需指定 IV 向量，并在每轮加密前进行异或。

## 三、原始实现概述

基础实现采用 C++ 编写，模块包括：

- `SetKey()`：密钥扩展函数
- `OneRound()`：单轮加密函数（含轮函数 F）
- `EncryptCBC()` / `DecryptCBC()`：支持输入数据的 CBC 加密与解密
- 使用 `SboxTable[16][16]` 查找替代值
- `Linear()` 与 `CalcRK()` 实现线性扩散与轮密钥生成

## 四、T-Table 优化方案

### 4.1 优化原理

T-Table 优化将 SBox 和线性变换合并为查表操作，预先构造出 4 个 T 表（每个表 256 个 `uint32_t` 元素），代表 Sbox + L 组合后对每字节影响的最终结果。

优化后的轮函数：

```cpp
RoundT(x0, x1, x2, x3, rk) = x0 ^ (T0[a0] ^ T1[a1] ^ T2[a2] ^ T3[a3])
```

其中 `a0~a3` 是 `(x1 ^ x2 ^ x3 ^ rk)` 拆解成的 4 字节，T0~T3 是对应表。

### 4.2 实现细节

- 预计算 `T0`, `T1`, `T2`, `T3`：通过 SBox 替换 + 线性变换 + 左移；
- 将轮函数替换为 `RoundT()`
- 编译期构建表，避免运行时计算。

### 4.3 优化成效

相比原始版本：

- **CPU 指令数下降**，移位/异或减少
- **执行速度提升约 1.8 倍（测试数据约 1MB）**

## 五、测试与评估

### 5.1 测试环境

- 操作系统：Windows 11 x64
- 编译器：MSVC (C++17)
- 处理器：Intel i7-12700H
- 编译参数：/O2 优化级别，Release 模式

### 5.2 功能验证

```c
int main() {
    const char* msg = "Hello SM4 encryption! SIMD Test!";
    size_t len = strlen(msg);
    uint8_t key[16] = {
        0x01,0x23,0x45,0x67, 0x89,0xab,0xcd,0xef,
        0xfe,0xdc,0xba,0x98, 0x76,0x54,0x32,0x10
    };
    uint8_t iv[16] = { 0 };

    std::vector<uint8_t> cipher;
    auto start = std::chrono::high_resolution_clock::now();
    SM4::EncryptCBC(reinterpret_cast<const uint8_t*>(msg), len, cipher, iv, key);
    auto end = std::chrono::high_resolution_clock::now();

    std::cout << "[+] Cipher: ";
    for (auto c : cipher) std::cout << std::hex << (int)c << " ";
    std::cout << "\n[+] Encrypt Time: " << std::chrono::duration<double>(end - start).count() << "s\n";

    std::vector<uint8_t> plain;
    uint8_t iv2[16] = { 0 };
    SM4::DecryptCBC(cipher.data(), cipher.size(), plain, iv2, key);

    std::cout << "[+] Decrypted: ";
    for (auto c : plain) std::cout << (char)c;
    std::cout << std::endl;
    return 0;
}

```

- 明文：`"Hello SM4 encryption!"`
- 密钥：固定 128bit 向量
- 验证加密 + 解密后恢复一致

### 5.3 性能测试

这里展示之前没有优化的实验测试结果：

![SM4优化之前](D:\crypto-projects\sm4_optimized\assets\SM4优化之前-1752111731246-1.png)

这里是未优化的实验结果，加密时间是$1.75*10^{-5}$ s

之后我们查看优化后的测试时间：

![SM4优化之后](D:\crypto-projects\sm4_optimized\assets\SM4优化之后-1752111736888-3.png)

显然，优化后的实验结果是$8.4 * 10^{-6}$ s

优化后的效率约等于是未优化前的两倍，说明我们的优化提升了加密的效率！

时间对比原始实现显著缩短！

## 六、总结与展望

本实验完成了 SM4 加密算法的标准实现和 T-Table 查表优化，成功提升了单线程执行效率。后续工作可进一步扩展：

- 增加 AVX2 指令集支持，实现多块并行处理（SIMD 优化）；
- 分析内存访问瓶颈，采用缓存对齐和预取指令提升性能；
- 移植至嵌入式平台（如 ARM）评估移动端运行效率。

## 七、附录

### 7.1 源码说明

- 所有代码整合在 `sm4_optimized.cpp` 文件中；
- 可直接通过 g++ / MSVC 编译运行，内含测试样例。

### 7.2 参考资料

- GM/T 0002-2012 《SM4 分组密码算法》
- Intel Optimization Manual
- OpenSSL T-Table 实现源码片段