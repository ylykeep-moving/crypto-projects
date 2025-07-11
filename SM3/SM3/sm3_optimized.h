#ifndef SM3_OPTIMIZED_H
#define SM3_OPTIMIZED_H

#include <cstdint>
#include <cstring>
#include <vector>

using u8 = uint8_t;
using u32 = uint32_t;
using u64 = uint64_t;

#define ROTL(x, n) (((x) << (n)) | ((x) >> (32 - (n))))
#define P0(x) ((x) ^ ROTL((x), 9) ^ ROTL((x), 17))
#define P1(x) ((x) ^ ROTL((x), 15) ^ ROTL((x), 23))

inline u32 FF(u32 x, u32 y, u32 z, int j) {
    return (j < 16) ? (x ^ y ^ z) : ((x & y) | (x & z) | (y & z));
}

inline u32 GG(u32 x, u32 y, u32 z, int j) {
    return (j < 16) ? (x ^ y ^ z) : ((x & y) | (~x & z));
}

inline constexpr u32 Tj(int j) {
    return (j < 16) ? 0x79cc4519 : 0x7a879d8a;
}

inline void sm3_compress(u32 V[8], const u8 block[64]) {
    u32 W[68], W1[64];
    for (int i = 0; i < 16; ++i) {
        W[i] = (block[4 * i + 0] << 24) | (block[4 * i + 1] << 16) |
            (block[4 * i + 2] << 8) | block[4 * i + 3];
    }
    for (int i = 16; i < 68; ++i) {
        W[i] = P1(W[i - 16] ^ W[i - 9] ^ ROTL(W[i - 3], 15)) ^ ROTL(W[i - 13], 7) ^ W[i - 6];
    }
    for (int i = 0; i < 64; ++i)
        W1[i] = W[i] ^ W[i + 4];

    u32 A = V[0], B = V[1], C = V[2], D = V[3];
    u32 E = V[4], F = V[5], G = V[6], H = V[7];

    for (int j = 0; j < 64; ++j) {
        u32 SS1 = ROTL((ROTL(A, 12) + E + ROTL(Tj(j), j)) & 0xffffffff, 7);
        u32 SS2 = SS1 ^ ROTL(A, 12);
        u32 TT1 = (FF(A, B, C, j) + D + SS2 + W1[j]) & 0xffffffff;
        u32 TT2 = (GG(E, F, G, j) + H + SS1 + W[j]) & 0xffffffff;
        D = C;
        C = ROTL(B, 9);
        B = A;
        A = TT1;
        H = G;
        G = ROTL(F, 19);
        F = E;
        E = P0(TT2);
    }

    V[0] ^= A; V[1] ^= B; V[2] ^= C; V[3] ^= D;
    V[4] ^= E; V[5] ^= F; V[6] ^= G; V[7] ^= H;
}

inline std::vector<u8> sm3(const u8* msg, size_t len) {
    u32 V[8] = {
        0x7380166f, 0x4914b2b9,
        0x172442d7, 0xda8a0600,
        0xa96f30bc, 0x163138aa,
        0xe38dee4d, 0xb0fb0e4e
    };

    size_t pad_len = (56 - (len + 1) % 64 + 64) % 64;
    size_t total_len = len + 1 + pad_len + 8;
    std::vector<u8> padded(total_len, 0);
    memcpy(padded.data(), msg, len);
    padded[len] = 0x80;

    u64 bit_len = len * 8;
    for (int i = 0; i < 8; ++i)
        padded[total_len - 1 - i] = (bit_len >> (i * 8)) & 0xff;

    for (size_t i = 0; i < total_len; i += 64)
        sm3_compress(V, &padded[i]);

    std::vector<u8> digest(32);
    for (int i = 0; i < 8; ++i) {
        digest[i * 4 + 0] = (V[i] >> 24) & 0xff;
        digest[i * 4 + 1] = (V[i] >> 16) & 0xff;
        digest[i * 4 + 2] = (V[i] >> 8) & 0xff;
        digest[i * 4 + 3] = V[i] & 0xff;
    }
    return digest;
}

#endif
