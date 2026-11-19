"""Recalque elastico no centro de uma sapata retangular (Steinbrenner)."""

from math import atan, log, pi, sqrt


def calcular_m(B, L):
    return L / B


def calcular_n(B, H):
    return 2 * H / B


def calcular_A0(m, n):
    r1 = sqrt(m**2 + 1)
    r3 = sqrt(m**2 + n**2)
    r4 = sqrt(m**2 + n**2 + 1)
    return m * log(((1 + r1) * r3) / (m * (1 + r4)))


def calcular_A1(m, n):
    r1 = sqrt(m**2 + 1)
    r2 = sqrt(1 + n**2)
    r4 = sqrt(m**2 + n**2 + 1)
    return log(((m + r1) * r2) / (m + r4))


def calcular_A2(m, n):
    r4 = sqrt(m**2 + n**2 + 1)
    return m / (n * r4)


def calcular_F1(A0, A1):
    return (A0 + A1) / pi


def calcular_F2(n, A2):
    return n / (2 * pi) * atan(A2)


def calcular_Is(F1, F2, nu):
    return F1 + (1 - 2 * nu) / (1 - nu) * F2


def calcular_Se(delta_sigma, B, Es, Is, If, nu):
    return delta_sigma * 2 * B * (1 - nu**2) / Es * Is * If


def calcular(B, L, H, delta_sigma, Es, nu, If):
    """Junta os termos do recalque elastico no centro da sapata."""
    m = calcular_m(B, L)
    n = calcular_n(B, H)
    A0 = calcular_A0(m, n)
    A1 = calcular_A1(m, n)
    A2 = calcular_A2(m, n)
    F1 = calcular_F1(A0, A1)
    F2 = calcular_F2(n, A2)
    Is = calcular_Is(F1, F2, nu)
    Se = calcular_Se(delta_sigma, B, Es, Is, If, nu)

    return {
        "m": m, "n": n, "A0": A0, "A1": A1, "A2": A2,
        "F1": F1, "F2": F2, "Is": Is, "If": If,
        "Se_m": Se, "Se_mm": Se * 1000,
        "Se_rigido_mm": 0.93 * Se * 1000 if B == L else None,
    }
