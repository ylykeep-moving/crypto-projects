# sm2.py

import os
import hashlib

# ==== 工具函数 ====
def mod_inv(a, p):
    if a == 0:
        raise ZeroDivisionError("逆元不存在")
    lm, hm = 1, 0
    low, high = a % p, p
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % p

def int_to_bytes(x: int, size: int = 32) -> bytes:
    return x.to_bytes(size, 'big')

def bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, 'big')

# ==== ECC 椭圆曲线基本运算 ====
def point_add(p, q, a, p_mod):
    if p == (0, 0): return q
    if q == (0, 0): return p
    if p[0] == q[0] and (p[1] != q[1] or p[1] == 0): return (0, 0)
    if p == q:
        l = (3 * p[0] ** 2 + a) * mod_inv(2 * p[1], p_mod) % p_mod
    else:
        l = (q[1] - p[1]) * mod_inv(q[0] - p[0], p_mod) % p_mod
    x3 = (l ** 2 - p[0] - q[0]) % p_mod
    y3 = (l * (p[0] - x3) - p[1]) % p_mod
    return (x3, y3)

def scalar_mult(k, point, a, p_mod):
    r = (0, 0)
    while k:
        if k & 1:
            r = point_add(r, point, a, p_mod)
        point = point_add(point, point, a, p_mod)
        k >>= 1
    return r

# ==== 哈希与 KDF ====
def sm3_hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()  # 模拟 SM3 哈希函数

def kdf(z: bytes, klen: int) -> bytes:
    ct = 1
    out = b''
    for _ in range((klen + 31) // 32):
        out += sm3_hash(z + ct.to_bytes(4, 'big'))
        ct += 1
    return out[:klen]

# ==== 签名算法 ====
def sm2_sign(m: bytes, dA: int, G, n, a, p):
    e = bytes_to_int(sm3_hash(m))
    while True:
        k = int.from_bytes(os.urandom(32), 'big') % n
        x1, y1 = scalar_mult(k, G, a, p)
        r = (e + x1) % n
        if r == 0 or r + k == n:
            continue
        s = (mod_inv(1 + dA, n) * (k - r * dA)) % n
        if s != 0:
            print(f"[签名] 消息哈希 e = {e}\n[签名] 随机数 k = {k}\n[签名] 椭圆曲线点 x1 = {x1}\n[签名] 签名 r = {r}\n[签名] 签名 s = {s}")
            return (r, s), k

def recover_private_key_from_k(r, s, k, n):
    numerator = (k - s) % n
    denominator = (s + r) % n
    d = (numerator * mod_inv(denominator, n)) % n
    return d

def sm2_verify(m: bytes, sig, PA, G, n, a, p):
    r, s = sig
    if not (1 <= r <= n - 1) or not (1 <= s <= n - 1):
        print("非法签名参数：r 或 s 超出范围")
        return False
    e = bytes_to_int(sm3_hash(m))
    t = (r + s) % n
    if t == 0:
        print("非法签名：t = r + s = 0")
        return False
    x1, y1 = point_add(scalar_mult(s, G, a, p), scalar_mult(t, PA, a, p), a, p)
    R = (e + x1) % n
    print(f"[验签] 消息哈希 e = {e}\n[验签] t = {t}\n[验签] 曲线计算点 x1 = {x1}\n[验签] 比较值 R = {R}")
    if R == r:
        return True
    else:
        print("验签失败：R ≠ r，签名无效")
        return False

# ==== 加解密 ====
def sm2_encrypt(m: bytes, PB, G, n, a, p):
    while True:
        k = int.from_bytes(os.urandom(32), 'big') % n
        C1 = scalar_mult(k, G, a, p)
        x2, y2 = scalar_mult(k, PB, a, p)
        t = kdf(int_to_bytes(x2) + int_to_bytes(y2), len(m))
        if int.from_bytes(t, 'big') == 0:
            continue
        C2 = bytes([_a ^ _b for _a, _b in zip(m, t)])
        C3 = sm3_hash(int_to_bytes(x2) + m + int_to_bytes(y2))
        print(f"[加密] k = {k}\n[加密] C1 点 = {C1}\n[加密] x2 = {x2}\n[加密] y2 = {y2}\n[加密] KDF 输出 t = {t.hex()}\n[加密] 哈希 C3 = {C3.hex()}")
        return (C1, C2, C3)

def sm2_decrypt(C1, C2, C3, dB, a, p):
    x2, y2 = scalar_mult(dB, C1, a, p)
    t = kdf(int_to_bytes(x2) + int_to_bytes(y2), len(C2))
    m = bytes([_a ^ _b for _a, _b in zip(C2, t)])
    u = sm3_hash(int_to_bytes(x2) + m + int_to_bytes(y2))
    print(f"[解密] x2 = {x2}\n[解密] y2 = {y2}\n[解密] KDF 输出 t = {t.hex()}\n[解密] C3 原值 = {C3.hex()}\n[解密] 验证哈希 u = {u.hex()}")
    return m if u == C3 else None

# ==== 模拟伪造中本聪签名攻击 ====
def forge_satoshi_signature():
    print("\n开始伪造中本聪签名...")
    # 模拟已知签名
    msg = b"I am Satoshi Nakamoto"
    known_r = 87993629357076412329543462576260527804912866891737981634610483213702502590249
    known_s = 53189040076505381807140350955043051312163133848419319151433791773226909049615
    known_k = 49360727606617547445418304344580212473651321772478762018268480842476497577007

    # 恢复私钥
    forged_d = recover_private_key_from_k(known_r, known_s, known_k, n)
    print(f"[伪造攻击] 恢复出的私钥 d_satoshi = {forged_d}")

    # 使用伪造私钥签名新消息
    fake_msg = b"I donate all my coins to OpenAI!"
    (fake_r, fake_s), _ = sm2_sign(fake_msg, forged_d, G, n, a, p)
    fake_PA = scalar_mult(forged_d, G, a, p)

    # 验证伪造签名
    if sm2_verify(fake_msg, (fake_r, fake_s), fake_PA, G, n, a, p):
        print("伪造签名验证通过，中本聪被伪造！")
    else:
        print("伪造失败")

# ==== 测试入口 ====
if __name__ == '__main__':
    print("开始运行 SM2 测试")
    p = int("FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF", 16)
    a = int("FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC", 16)
    b = int("28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93", 16)
    G = (
        int("32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7", 16),
        int("BC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0", 16)
    )
    n = int("FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123", 16)
    dA = 0x128B2FA8BD433C6C068C8D803DFF7979
    PA = scalar_mult(dA, G, a, p)
    msg = b"hello sm2"

    print("\n【步骤一】签名消息...")
    (r, s), k = sm2_sign(msg, dA, G, n, a, p)

    print("\n【步骤二】验证签名...")
    assert sm2_verify(msg, (r, s), PA, G, n, a, p)
    print("签名验证通过")

    print("\n【步骤三】已知 k 恢复私钥...")
    recovered_dA = recover_private_key_from_k(r, s, k, n)
    print(f"[私钥恢复] 原始 dA = {dA}\n[私钥恢复] 恢复 dA = {recovered_dA}")
    assert recovered_dA == dA
    print("私钥成功从签名恢复")

    print("\n【步骤四】加密消息...")
    C1, C2, C3 = sm2_encrypt(msg, PA, G, n, a, p)

    print("\n【步骤五】解密消息...")
    m_dec = sm2_decrypt(C1, C2, C3, dA, a, p)
    assert m_dec == msg
    print("加解密成功")

    forge_satoshi_signature()
