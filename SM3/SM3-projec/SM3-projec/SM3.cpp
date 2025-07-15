// Part C: SM3 Merkle Tree + 叶子存在性证明
#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <cstdint>
#include <array>
#include <chrono>
#include <functional>

using namespace std;

// ==================== SM3 实现 ====================
inline uint32_t rotate_left(uint32_t x, int n) {
    return (x << n) | (x >> (32 - n));
}
inline uint32_t P0(uint32_t x) { return x ^ rotate_left(x, 9) ^ rotate_left(x, 17); }
inline uint32_t P1(uint32_t x) { return x ^ rotate_left(x, 15) ^ rotate_left(x, 23); }
inline uint32_t FF(uint32_t x, uint32_t y, uint32_t z, int j) {
    return (j < 16) ? (x ^ y ^ z) : ((x & y) | (x & z) | (y & z));
}
inline uint32_t GG(uint32_t x, uint32_t y, uint32_t z, int j) {
    return (j < 16) ? (x ^ y ^ z) : ((x & y) | (~x & z));
}
const array<uint32_t, 64> T = [] {
    array<uint32_t, 64> t{};
    for (int j = 0; j < 64; ++j)
        t[j] = (j < 16) ? rotate_left(0x79CC4519, j) : rotate_left(0x7A879D8A, j);
    return t;
    }();

vector<uint8_t> pad(const vector<uint8_t>& msg, uint64_t len_bits) {
    vector<uint8_t> padded(msg);
    padded.push_back(0x80);
    while ((padded.size() * 8 + 64) % 512 != 0)
        padded.push_back(0x00);
    for (int i = 7; i >= 0; --i)
        padded.push_back((len_bits >> (i * 8)) & 0xff);
    return padded;
}

vector<uint32_t> parse_block(const vector<uint8_t>& b) {
    vector<uint32_t> W(68);
    for (int i = 0; i < 16; i++)
        W[i] = (b[i * 4] << 24) | (b[i * 4 + 1] << 16) | (b[i * 4 + 2] << 8) | b[i * 4 + 3];
    for (int i = 16; i < 68; i++)
        W[i] = P1(W[i - 16] ^ W[i - 9] ^ rotate_left(W[i - 3], 15)) ^
        rotate_left(W[i - 13], 7) ^ W[i - 6];
    return W;
}

vector<uint32_t> compute_W1(const vector<uint32_t>& W) {
    vector<uint32_t> W1(64);
    for (int i = 0; i < 64; i++) W1[i] = W[i] ^ W[i + 4];
    return W1;
}

vector<uint32_t> CF(const vector<uint32_t>& V, const vector<uint8_t>& B) {
    auto W = parse_block(B);
    auto W1 = compute_W1(W);
    uint32_t A0 = V[0], A1 = V[1], A2 = V[2], A3 = V[3];
    uint32_t A4 = V[4], A5 = V[5], A6 = V[6], A7 = V[7];
    for (int j = 0; j < 64; ++j) {
        uint32_t SS1 = rotate_left((rotate_left(A0, 12) + A4 + T[j]) & 0xFFFFFFFF, 7);
        uint32_t SS2 = SS1 ^ rotate_left(A0, 12);
        uint32_t TT1 = (FF(A0, A1, A2, j) + A3 + SS2 + W1[j]) & 0xFFFFFFFF;
        uint32_t TT2 = (GG(A4, A5, A6, j) + A7 + SS1 + W[j]) & 0xFFFFFFFF;
        A3 = A2; A2 = rotate_left(A1, 9); A1 = A0; A0 = TT1;
        A7 = A6; A6 = rotate_left(A5, 19); A5 = A4; A4 = P0(TT2);
    }
    return { A0 ^ V[0], A1 ^ V[1], A2 ^ V[2], A3 ^ V[3],
            A4 ^ V[4], A5 ^ V[5], A6 ^ V[6], A7 ^ V[7] };
}

string sm3_full(const vector<uint8_t>& msg) {
    vector<uint8_t> padded = pad(msg, msg.size() * 8);
    size_t n = padded.size() / 64;
    vector<uint32_t> V = { 0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
                          0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E };
    for (size_t i = 0; i < n; i++) {
        vector<uint8_t> block(padded.begin() + i * 64, padded.begin() + (i + 1) * 64);
        V = CF(V, block);
    }
    ostringstream oss;
    for (auto v : V) oss << hex << setw(8) << setfill('0') << v;
    return oss.str();
}

// ==================== Merkle 树构造 ====================
struct MerkleNode {
    string hash;
    MerkleNode* left;
    MerkleNode* right;
    MerkleNode(string h) : hash(h), left(nullptr), right(nullptr) {}
    MerkleNode(MerkleNode* l, MerkleNode* r) : left(l), right(r) {
        string concat = l->hash + (r ? r->hash : "");
        vector<uint8_t> data(concat.begin(), concat.end());
        hash = sm3_full(data);
    }
};

MerkleNode* build_merkle_tree(vector<string>& leaves) {
    vector<MerkleNode*> nodes;
    for (auto& leaf : leaves) {
        vector<uint8_t> data(leaf.begin(), leaf.end());
        nodes.push_back(new MerkleNode(sm3_full(data)));
    }
    while (nodes.size() > 1) {
        vector<MerkleNode*> next;
        for (size_t i = 0; i < nodes.size(); i += 2) {
            MerkleNode* l = nodes[i];
            MerkleNode* r = (i + 1 < nodes.size()) ? nodes[i + 1] : nullptr;
            next.push_back(new MerkleNode(l, r));
        }
        nodes = move(next);
    }
    return nodes.front();
}

vector<pair<string, bool>> get_proof(MerkleNode* root, const string& target_hash) {
    vector<pair<string, bool>> proof;
    function<bool(MerkleNode*)> dfs = [&](MerkleNode* node) -> bool {
        if (!node) return false;
        if (!node->left && !node->right && node->hash == target_hash) return true;
        if (node->left && dfs(node->left)) {
            if (node->right) proof.emplace_back(node->right->hash, true);
            return true;
        }
        if (node->right && dfs(node->right)) {
            proof.emplace_back(node->left->hash, false);
            return true;
        }
        return false;
        };
    dfs(root);
    return proof;
}

string verify_proof(string leaf_hash, const vector<pair<string, bool>>& proof) {
    for (auto& p : proof) {
        vector<uint8_t> data;
        if (p.second) {  // sibling on right
            data.insert(data.end(), leaf_hash.begin(), leaf_hash.end());
            data.insert(data.end(), p.first.begin(), p.first.end());
        }
        else {
            data.insert(data.end(), p.first.begin(), p.first.end());
            data.insert(data.end(), leaf_hash.begin(), leaf_hash.end());
        }
        leaf_hash = sm3_full(data);
    }
    return leaf_hash;
}

// ========== 生成存在性/不存在性证明 ==========
vector<pair<string, bool>> get_proof(MerkleNode* root, const string& target_hash, bool& found) {
    vector<pair<string, bool>> path;
    function<bool(MerkleNode*)> dfs = [&](MerkleNode* node) -> bool {
        if (!node) return false;
        if (!node->left && !node->right) {
            if (node->hash == target_hash) {
                found = true;
                return true;
            }
            return false;
        }
        if (node->left && dfs(node->left)) {
            if (node->right) path.emplace_back(node->right->hash, true);
            return true;
        }
        if (node->right && dfs(node->right)) {
            if (node->left) path.emplace_back(node->left->hash, false);
            return true;
        }
        return false;
        };
    found = false;
    dfs(root);
    return path;
}

string verify_merkle_proof(string leaf_hash, const vector<pair<string, bool>>& proof) {
    for (auto& p : proof) {
        vector<uint8_t> data;
        if (p.second) {
            data.insert(data.end(), leaf_hash.begin(), leaf_hash.end());
            data.insert(data.end(), p.first.begin(), p.first.end());
        }
        else {
            data.insert(data.end(), p.first.begin(), p.first.end());
            data.insert(data.end(), leaf_hash.begin(), leaf_hash.end());
        }
        leaf_hash = sm3_full(data);
    }
    return leaf_hash;
}

int main() {
    const int N = 100000;
    vector<string> leaves;
    for (int i = 0; i < N; ++i)
        leaves.push_back("leaf" + to_string(i));

    auto start = chrono::high_resolution_clock::now();
    MerkleNode* root = build_merkle_tree(leaves);
    auto end = chrono::high_resolution_clock::now();
    cout << "Merkle Root: " << root->hash << endl;
    cout << "Build time: " << chrono::duration<double>(end - start).count() << "s\n";

    // ==== 存在性验证 ====
    int idx = 54321;
    vector<uint8_t> data(leaves[idx].begin(), leaves[idx].end());
    string hash = sm3_full(data);
    bool found;
    auto proof = get_proof(root, hash, found);
    string result = verify_merkle_proof(hash, proof);
    cout << "[测试存在性] Index: " << idx << endl;
    cout << (found && result == root->hash ? "[OK] 存在性验证成功\n" : "[FAIL] 存在性验证失败\n");

    // ==== 不存在性验证 ====
    string fake = "nonexistent_leaf";
    vector<uint8_t> fake_data(fake.begin(), fake.end());
    string fake_hash = sm3_full(fake_data);
    auto fake_proof = get_proof(root, fake_hash, found);
    string fake_result = verify_merkle_proof(fake_hash, fake_proof);
    cout << "\n[测试不存在性] 输入: " << fake << endl;
    if (!found)
        cout << "[OK] 不存在性验证成功：目标哈希未在树中\n";
    else if (fake_result != root->hash)
        cout << "[OK] 不存在性验证成功：哈希路径不一致\n";
    else
        cout << "[FAIL] 不存在性验证失败：伪造路径通过\n";

    return 0;
}
