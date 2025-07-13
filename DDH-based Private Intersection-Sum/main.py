import random
from hashlib import sha256
from phe import paillier
import secrets
from typing import List, Tuple

# -------------------- 协议参数设置 -------------------- #

# 一个大素数 p，用于模拟群 G（DDH 假设所在群）
p = 2 ** 521 - 1

# 将标识符哈希到群元素
def hash_to_group(identifier: str) -> int:
    h = sha256(identifier.encode()).digest()  # 进行 SHA256 哈希
    return int.from_bytes(h, 'big') % p       # 转为整数并取模 p

# 打乱数据并返回原始索引
def shuffle_with_indices(data):
    indices = list(range(len(data)))
    random.shuffle(indices)
    return [data[i] for i in indices], indices

# 反打乱数据
def unshuffle(data, indices):
    unshuffled = [None] * len(data)
    for i, idx in enumerate(indices):
        unshuffled[idx] = data[i]
    return unshuffled

# -------------------- 双方参与者类定义 -------------------- #

class Party1:
    """模拟 P1，持有纯标识符集合"""
    def __init__(self, identifiers: List[str]):
        self.V = identifiers                      # P1 的输入集合
        self.k1 = secrets.randbelow(p - 1) + 1    # 随机生成私钥 k1
        self.Z = None                             # 存放 P2 返回的 Z
        self.public_key = None                    # 同态加密公钥
        self.intersection_indices = []

    def receive_public_key(self, pk):
        self.public_key = pk  # 获取 Paillier 公钥

    def round1_send_hashed(self):
        # 对每个标识符进行哈希并做幂运算 H(vi)^k1
        self.V_hashed = [pow(hash_to_group(v), self.k1, p) for v in self.V]
        self.V_hashed, self.shuffle_idx = shuffle_with_indices(self.V_hashed)  # 打乱顺序
        return self.V_hashed

    def round3_compute_intersection_sum(self, data_from_p2: List[Tuple[int, paillier.EncryptedNumber]]):
        # 接收 P2 的密文数据，找出与 Z 相同的元素，并同态求和
        result = []
        for w_hashed, enc_t in data_from_p2:
            hw = pow(w_hashed, self.k1, p)
            if hw in self.Z:
                result.append(enc_t)
        self.intersection_size = len(result)
        if result:
            s = result[0]
            for r in result[1:]:
                s += r  # 同态加法
            return s
        return self.public_key.encrypt(0)  # 如果交集为空，返回加密的 0

    def receive_Z(self, Z):
        self.Z = Z  # 接收来自 P2 的 Z = H(vi)^{k1k2}


class Party2:
    """模拟 P2，持有标识符 + 值对"""
    def __init__(self, items: List[Tuple[str, int]]):
        self.W = items
        self.k2 = secrets.randbelow(p - 1) + 1                    # 私钥 k2
        self.public_key, self.private_key = paillier.generate_paillier_keypair()  # 同态加密密钥对

    def get_public_key(self):
        return self.public_key

    def round2_process_and_send(self, hashed_from_p1: List[int]) -> Tuple[List[int], List[Tuple[int, paillier.EncryptedNumber]]]:
        # 计算 H(vi)^k1k2
        Z = [pow(h, self.k2, p) for h in hashed_from_p1]

        # 对自己输入 (wi, ti) 做处理，计算 H(wi)^k2 和加密的 ti
        processed = []
        for w, t in self.W:
            hw = pow(hash_to_group(w), self.k2, p)
            ct = self.public_key.encrypt(t)  # 同态加密
            processed.append((hw, ct))

        processed, _ = shuffle_with_indices(processed)  # 打乱顺序
        return Z, processed

    def round3_decrypt_sum(self, encrypted_sum: paillier.EncryptedNumber):
        return self.private_key.decrypt(encrypted_sum)  # 解密最终结果

# -------------------- 协议运行模拟 -------------------- #

def run_ddh_psi_sum():
    # 输入数据
    p1_input = ['alice', 'bob', 'carol', 'dave']                    # P1 拥有标识符
    p2_input = [('bob', 10), ('carol', 20), ('eve', 30)]            # P2 拥有标识符+值对

    # 初始化两方
    P1 = Party1(p1_input)
    P2 = Party2(p2_input)

    # Round 0: 公钥交换
    pk = P2.get_public_key()
    P1.receive_public_key(pk)

    # Round 1: P1 对每个标识符哈希并加密后发送
    round1_msg = P1.round1_send_hashed()

    # Round 2: P2 接收并返回 Z 和加密数据
    Z, enc_data = P2.round2_process_and_send(round1_msg)
    P1.receive_Z(Z)

    # Round 3: P1 找交集并求和（加密）
    encrypted_sum = P1.round3_compute_intersection_sum(enc_data)

    # 最终由 P2 解密得到结果
    total = P2.round3_decrypt_sum(encrypted_sum)

    print("交集求和值 (Intersection sum):", total)
    print("交集大小 (Intersection size):", P1.intersection_size)


if __name__ == '__main__':
    run_ddh_psi_sum()
