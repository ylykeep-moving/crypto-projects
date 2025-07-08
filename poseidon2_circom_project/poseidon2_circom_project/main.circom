pragma circom 2.0.0;

include "poseidon2.circom";

template Main() {
    signal input preimage[2]; // 私有输入
    signal input hash_pub;    // 公共输入

    component h = Poseidon2();
    h.inputs[0] <== preimage[0];
    h.inputs[1] <== preimage[1];

    hash_pub === h.out;
}

component main = Main();
