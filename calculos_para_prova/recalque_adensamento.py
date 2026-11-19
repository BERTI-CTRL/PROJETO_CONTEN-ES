"""Recalques primário e secundário por adensamento unidimensional."""

from math import log10, pi


def calcular_recalque_primario(H, e0, Cc, Cr, sigma_v0, sigma_vm, delta_sigma):
    """Calcula o recalque primário e identifica recompressão/virgem."""
    sigma_final = sigma_v0 + delta_sigma

    if sigma_v0 < sigma_vm and sigma_final <= sigma_vm:
        delta_e_recompressao = Cr * log10(sigma_final / sigma_v0)
        delta_e_virgem = 0.0
        caso = "Somente recompressão"
    elif sigma_v0 < sigma_vm < sigma_final:
        delta_e_recompressao = Cr * log10(sigma_vm / sigma_v0)
        delta_e_virgem = Cc * log10(sigma_final / sigma_vm)
        caso = "Recompressão e compressão virgem"
    else:
        delta_e_recompressao = 0.0
        delta_e_virgem = Cc * log10(sigma_final / sigma_v0)
        caso = "Somente compressão virgem (normalmente adensada)"

    delta_e = delta_e_recompressao + delta_e_virgem
    recalque_m = H * delta_e / (1 + e0)
    return {
        "sigma_final": sigma_final,
        "delta_e_recompressao": delta_e_recompressao,
        "delta_e_virgem": delta_e_virgem,
        "delta_e": delta_e,
        "caso": caso,
        "recalque_m": recalque_m,
        "recalque_mm": recalque_m * 1000,
    }


def calcular_recalque_secundario(Calpha, H, ep, t1, t2):
    """Calcula o recalque secundário usando o índice modificado C'alpha."""
    Calpha_modificado = Calpha / (1 + ep)
    recalque_m = Calpha_modificado * H * log10(t2 / t1)
    return {
        "Calpha_modificado": Calpha_modificado,
        "recalque_m": recalque_m,
        "recalque_mm": recalque_m * 1000,
    }


def calcular_tempo_adensamento(Tv, Hd, Cv):
    """Tempo de adensamento em segundos, dias e anos (Cv em m²/s)."""
    tempo_s = Tv * Hd**2 / Cv
    return {
        "segundos": tempo_s,
        "dias": tempo_s / (24 * 60 * 60),
        "anos": tempo_s / (365.25 * 24 * 60 * 60),
    }


def calcular_fator_tempo(U_percentual):
    """Estima Tv pelas aproximações da aula para o grau médio U (em %)."""
    U = U_percentual / 100
    if U_percentual <= 60:
        return pi / 4 * U**2
    return -0.9332 * log10(1 - U) - 0.0851
