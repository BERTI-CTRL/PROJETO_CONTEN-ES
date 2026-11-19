"""Indices de compressibilidade e Cv a partir de pontos do ensaio edometrico."""

from math import log10


def calcular_indice_compressao(sigma_1, e_1, sigma_2, e_2):
    """Calcula Cc ou Cr entre dois pontos, com sigma_2 > sigma_1."""
    return (e_1 - e_2) / log10(sigma_2 / sigma_1)


def calcular_cv(Tv, Hd, tempo_minutos):
    """Calcula Cv em m²/s; Hd esta em m e o tempo de leitura em minutos."""
    tempo_segundos = tempo_minutos * 60
    cv = Tv * Hd**2 / tempo_segundos
    return {"tempo_s": tempo_segundos, "Cv_m2_s": cv, "Cv_cm2_s": cv * 10_000}


def calcular_recalque_parcial(U_percentual, recalque_primario_final):
    """Estima o recalque primario acumulado para o grau medio U."""
    return (U_percentual / 100) * recalque_primario_final
