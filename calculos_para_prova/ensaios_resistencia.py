"""Reducao basica de ensaio triaxial e compressao simples."""

from math import pi


def calcular_area_inicial(diametro):
    """Area inicial circular em m², com diametro em m."""
    return pi * diametro**2 / 4


def calcular_area_corrigida(area_inicial, deformacao_axial, deformacao_volumetrica=0.0):
    """Area na ruptura; deformacoes de compressao sao positivas."""
    return area_inicial * (1 - deformacao_volumetrica) / (1 - deformacao_axial)


def calcular_tensao_desviadora(carga, area_corrigida):
    """Carga em kN / area em m² resulta em tensão em kPa."""
    return carga / area_corrigida


def reduzir_ensaio(diametro, altura_inicial, encurtamento, carga, sigma_3=0.0,
                   deformacao_volumetrica=0.0, u_ruptura=None):
    """Calcula área, tensão desviadora e tensões principais na ruptura.

    Geometria em m, carga em kN e tensões em kPa. Para CU/UU/RCS,
    deformacao_volumetrica=0 (volume constante). Para CD, informe a
    deformacao volumetrica medida, positiva para contracao.
    """
    area_inicial = calcular_area_inicial(diametro)
    deformacao_axial = encurtamento / altura_inicial
    area_corrigida = calcular_area_corrigida(
        area_inicial, deformacao_axial, deformacao_volumetrica
    )
    sigma_d = calcular_tensao_desviadora(carga, area_corrigida)
    sigma_1 = sigma_3 + sigma_d

    resultado = {
        "area_inicial": area_inicial,
        "deformacao_axial": deformacao_axial,
        "area_corrigida": area_corrigida,
        "sigma_d": sigma_d,
        "sigma_1": sigma_1,
        "sigma_3": sigma_3,
        "u_ruptura": u_ruptura,
    }
    if u_ruptura is not None:
        resultado["sigma_1_efetiva"] = sigma_1 - u_ruptura
        resultado["sigma_3_efetiva"] = sigma_3 - u_ruptura
    return resultado
