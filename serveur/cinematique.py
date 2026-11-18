"""Modèle géométrique direct du bras (même modèle DH que web/js/cinematique.js)."""

import math

# Denavit-Hartenberg modifié : (alpha, a, d, offset), longueurs en mètres
DH = [
    (0.0, 0.0, 0.22075, -math.pi / 2),
    (math.pi / 2, 0.0, 0.0, math.pi / 2),
    (0.0, 0.22152, 0.0, math.pi / 2),
    (math.pi / 2, 0.0, 0.228, 0.0),
    (-math.pi / 2, 0.0, 0.0, 0.0),
    (math.pi / 2, 0.0, 0.203, math.pi),
]


def _mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _lien(alpha, a, d, theta):
    ca, sa, ct, st = math.cos(alpha), math.sin(alpha), math.cos(theta), math.sin(theta)
    return [
        [ct, -st, 0, a],
        [st * ca, ct * ca, -sa, -sa * d],
        [st * sa, ct * sa, ca, ca * d],
        [0, 0, 0, 1],
    ]


def position_outil(q):
    """Position (x, y, z) de l'extrémité en mm pour des angles q en degrés."""
    T = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    for (alpha, a, d, offset), angle in zip(DH, q):
        T = _mul(T, _lien(alpha, a, d, math.radians(angle) + offset))
    return T[0][3] * 1000, T[1][3] * 1000, T[2][3] * 1000
