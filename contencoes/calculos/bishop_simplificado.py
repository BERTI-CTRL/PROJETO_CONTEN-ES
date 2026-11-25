"""Iteração de Bishop Simplificado sobre as fatias de um círculo."""

import math
from typing import Any

TOLERANCIA_BISHOP = 0.0001
MAX_ITERACOES_BISHOP = 20


def calcular_bishop(circulo: dict[str, Any], entradas: dict[str, Any]) -> dict[str, Any]:
    fatias = circulo["fatias"]
    if not fatias or any(f["situacao"] == "FORA DO MACIÇO" for f in fatias):
        return _resultado("GEOMETRIA INVÁLIDA")

    c1 = entradas["coesao_efetiva_camada_superior_kPa"]
    c2 = entradas["coesao_efetiva_camada_inferior_kPa"]
    tan1 = math.tan(math.radians(entradas["angulo_atrito_efetivo_camada_superior_graus"]))
    tan2 = math.tan(math.radians(entradas["angulo_atrito_efetivo_camada_inferior_graus"]))
    parcelas = []
    mobilizacao = 0.0
    for fatia in fatias:
        l1 = fatia["comprimento_camada_superior_m"]
        l2 = fatia["comprimento_camada_inferior_m"]
        comprimento = l1 + l2
        if comprimento <= 0:
            return _resultado("GEOMETRIA INVÁLIDA")
        coesao = (l1 * c1 + l2 * c2) / comprimento
        tan_phi = (l1 * tan1 + l2 * tan2) / comprimento
        largura = fatia["x_final_m"] - fatia["x_inicial_m"]
        peso = fatia["peso_fatia_kN_m"]
        u = fatia["pressao_neutra_kPa"]
        alfa = math.radians(fatia["angulo_base_medio_graus"])
        parcelas.append((
            coesao * largura + (peso - u * largura) * tan_phi,
            math.cos(alfa),
            math.sin(alfa) * tan_phi,
        ))
        mobilizacao += peso * math.sin(alfa)

    if not math.isfinite(mobilizacao) or mobilizacao <= 0:
        return _resultado("ERRO NUMÉRICO")

    fs = 1.5
    historico = []
    primeira_convergencia = None
    for iteracao in range(1, MAX_ITERACOES_BISHOP + 1):
        resistencia = 0.0
        for numerador, cosseno, sen_alfa_tan_phi in parcelas:
            m_alfa = cosseno + sen_alfa_tan_phi / fs
            if abs(m_alfa) < 1e-12:
                return _resultado("ERRO NUMÉRICO", historico)
            resistencia += numerador / m_alfa
        novo_fs = resistencia / mobilizacao
        if not math.isfinite(novo_fs) or novo_fs <= 0:
            return _resultado("ERRO NUMÉRICO", historico)
        residuo = abs(novo_fs - fs)
        historico.append({"iteracao": iteracao, "fs": novo_fs, "residuo": residuo})
        if primeira_convergencia is None and residuo <= TOLERANCIA_BISHOP:
            primeira_convergencia = iteracao
        fs = novo_fs

    # A planilha publica a última iteração e informa a primeira que atingiu a tolerância.
    if historico[-1]["residuo"] > TOLERANCIA_BISHOP:
        return _resultado("NÃO CONVERGIU", historico)
    return _resultado("CONVERGIU", historico, fs, primeira_convergencia)


def _resultado(situacao, historico=None, fs=None, iteracoes=None):
    return {
        "situacao": situacao,
        "fator_seguranca": fs,
        "iteracoes": iteracoes,
        "historico": historico if historico is not None else [],
    }
