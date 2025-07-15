pragma circom 2.0.0;

// Poseidon2 简化实现，参数 t=3, d=5
template Poseidon2() {
    signal input inputs[2];  // t=3，rate=2，capacity=1
    signal output out;

    signal s[3];
    s[0] <== inputs[0];
    s[1] <== inputs[1];
    s[2] <== 0;

    var R_F = 8;
    var R_P = 57;
    var d = 5;

    var roundConstants[65][3];
    for (var i = 0; i < 65; i++) {
        for (var j = 0; j < 3; j++) {
            roundConstants[i][j] = i * 123 + j * 17; // 示例常数
        }
    }

    var MDS[3][3] = [
        [2, 3, 4],
        [1, 1, 1],
        [4, 3, 2]
    ];

    var totalRounds = R_F + R_P;
    signal state[totalRounds + 1][3];

    for (var i = 0; i < 3; i++) {
        state[0][i] <== s[i];
    }

    for (var r = 0; r < totalRounds; r++) {
        for (var i = 0; i < 3; i++) {
            state[r][i] += roundConstants[r][i];
        }

        if (r < R_F / 2 || r >= totalRounds - R_F / 2) {
            for (var i = 0; i < 3; i++) {
                state[r][i] <== state[r][i] ** d;
            }
        } else {
            state[r][0] <== state[r][0] ** d;
        }

        for (var i = 0; i < 3; i++) {
            var acc = 0;
            for (var j = 0; j < 3; j++) {
                acc += MDS[i][j] * state[r][j];
            }
            state[r + 1][i] <== acc;
        }
    }

    out <== state[totalRounds][0];
}
