"""Cálculos didáticos de cortinas de estacas-prancha.

Os dois casos reproduzem as hipóteses e os exemplos da planilha de referência.
Este módulo não depende do Streamlit nem de bibliotecas de gráficos.
"""

from __future__ import annotations

from math import isfinite, radians, sin
from typing import Any


def carregar_exemplos_estaca_prancha() -> dict[str, dict[str, float]]:
    """Retorna os dados preenchidos dos dois exemplos da planilha."""
    return {
        "cortina_em_balanco": {
            "altura_livre_escavacao_m": 5.0,
            "peso_especifico_solo_kN_m3": 18.0,
            "angulo_atrito_solo_graus": 30.0,
            "percentual_passivo_mobilizado": 100.0 * (2.0 / 3.0),
            "percentual_acrescimo_ficha": 20.0,
        },
        "cortina_ancorada": {
            "sobrecarga_superficie_kPa": 12.0,
            "espessura_camada_superior_ate_na_m": 3.0,
            "peso_especifico_solo_superior_kN_m3": 17.0,
            "peso_especifico_solo_submerso_kN_m3": 12.0,
            "profundidade_na_ate_escavacao_m": 4.0,
            "ficha_abaixo_escavacao_m": 3.5,
            "angulo_atrito_solo_graus": 30.0,
            "altura_ancoragem_acima_na_m": 0.9,
            "percentual_passivo_mobilizado": 100.0,
            "fator_seguranca_minimo_tombamento": 1.5,
            "peso_especifico_agua_kN_m3": 9.81,
        },
    }


def _numero_finito(valor: Any) -> bool:
    return (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and isfinite(valor)
    )


def _coeficientes_rankine(angulo_atrito_solo_graus: float) -> tuple[float, float]:
    seno_atrito = sin(radians(angulo_atrito_solo_graus))
    coeficiente_ativo = (1.0 - seno_atrito) / (1.0 + seno_atrito)
    coeficiente_passivo = (1.0 + seno_atrito) / (1.0 - seno_atrito)
    return coeficiente_ativo, coeficiente_passivo


def validar_entradas_cortina_em_balanco(entradas: dict[str, Any]) -> list[str]:
    """Valida as entradas do exemplo de cortina em balanço."""
    erros: list[str] = []
    campos_positivos = {
        "altura_livre_escavacao_m": "A altura livre da escavação deve ser maior que zero.",
        "peso_especifico_solo_kN_m3": "O peso específico do solo deve ser maior que zero.",
        "angulo_atrito_solo_graus": "O ângulo de atrito deve ser maior que zero.",
    }
    for campo, mensagem in campos_positivos.items():
        valor = entradas.get(campo)
        if not _numero_finito(valor) or valor <= 0:
            erros.append(mensagem)

    angulo_atrito_solo_graus = entradas.get("angulo_atrito_solo_graus")
    if _numero_finito(angulo_atrito_solo_graus) and angulo_atrito_solo_graus >= 90:
        erros.append("O ângulo de atrito deve ser menor que 90°.")

    for campo, nome in (
        ("percentual_passivo_mobilizado", "A fração de passivo mobilizado"),
        ("percentual_acrescimo_ficha", "O acréscimo prático da ficha"),
    ):
        valor = entradas.get(campo)
        limite_superior = 100.0 if campo == "percentual_passivo_mobilizado" else None
        if not _numero_finito(valor) or valor < 0 or (
            limite_superior is not None and valor > limite_superior
        ):
            mensagem_limite = "entre 0% e 100%" if limite_superior else "não pode ser negativo"
            erros.append(f"{nome} {mensagem_limite}.")
    if _numero_finito(entradas.get("percentual_passivo_mobilizado")) and entradas[
        "percentual_passivo_mobilizado"
    ] == 0:
        erros.append("A fração de passivo mobilizado deve ser maior que zero.")

    if not erros and _numero_finito(angulo_atrito_solo_graus):
        coeficiente_ativo, coeficiente_passivo = _coeficientes_rankine(
            angulo_atrito_solo_graus
        )
        coeficiente_passivo_mobilizado = (
            coeficiente_passivo * entradas["percentual_passivo_mobilizado"] / 100.0
        )
        if coeficiente_passivo_mobilizado <= coeficiente_ativo:
            erros.append(
                "O passivo mobilizado precisa superar o ativo para existir uma ficha finita "
                "neste equilíbrio simplificado."
            )

    return list(dict.fromkeys(erros))


def calcular_cortina_em_balanco(entradas: dict[str, Any]) -> dict[str, Any]:
    """Calcula a ficha teórica pelo equilíbrio cúbico de momentos de Rankine."""
    altura_livre_escavacao_m = entradas["altura_livre_escavacao_m"]
    peso_especifico_solo_kN_m3 = entradas["peso_especifico_solo_kN_m3"]
    angulo_atrito_solo_graus = entradas["angulo_atrito_solo_graus"]
    percentual_passivo_mobilizado = entradas["percentual_passivo_mobilizado"]
    percentual_acrescimo_ficha = entradas["percentual_acrescimo_ficha"]

    coeficiente_ativo_rankine, coeficiente_passivo_rankine = _coeficientes_rankine(
        angulo_atrito_solo_graus
    )
    fracao_passivo_mobilizado = percentual_passivo_mobilizado / 100.0
    coeficiente_passivo_mobilizado = (
        coeficiente_passivo_rankine * fracao_passivo_mobilizado
    )
    razao_cubica = (
        coeficiente_ativo_rankine / coeficiente_passivo_mobilizado
    ) ** (1.0 / 3.0)
    ficha_teorica_m = altura_livre_escavacao_m * razao_cubica / (1.0 - razao_cubica)
    ficha_preliminar_m = ficha_teorica_m * (1.0 + percentual_acrescimo_ficha / 100.0)
    profundidade_ponta_m = altura_livre_escavacao_m + ficha_teorica_m

    empuxo_ativo_kN_m = (
        0.5
        * coeficiente_ativo_rankine
        * peso_especifico_solo_kN_m3
        * profundidade_ponta_m**2
    )
    empuxo_passivo_mobilizado_kN_m = (
        0.5
        * coeficiente_passivo_mobilizado
        * peso_especifico_solo_kN_m3
        * ficha_teorica_m**2
    )
    momento_ativo_sobre_ponta_kNm_m = empuxo_ativo_kN_m * profundidade_ponta_m / 3.0
    momento_passivo_sobre_ponta_kNm_m = (
        empuxo_passivo_mobilizado_kN_m * ficha_teorica_m / 3.0
    )

    return {
        "coeficiente_ativo_rankine": coeficiente_ativo_rankine,
        "coeficiente_passivo_rankine": coeficiente_passivo_rankine,
        "fracao_passivo_mobilizado": fracao_passivo_mobilizado,
        "coeficiente_passivo_mobilizado": coeficiente_passivo_mobilizado,
        "razao_cubica": razao_cubica,
        "ficha_teorica_m": ficha_teorica_m,
        "ficha_preliminar_m": ficha_preliminar_m,
        "profundidade_ponta_m": profundidade_ponta_m,
        "empuxo_ativo_kN_m": empuxo_ativo_kN_m,
        "empuxo_passivo_mobilizado_kN_m": empuxo_passivo_mobilizado_kN_m,
        "momento_ativo_sobre_ponta_kNm_m": momento_ativo_sobre_ponta_kNm_m,
        "momento_passivo_sobre_ponta_kNm_m": momento_passivo_sobre_ponta_kNm_m,
        "residuo_equilibrio_momentos_kNm_m": (
            momento_passivo_sobre_ponta_kNm_m - momento_ativo_sobre_ponta_kNm_m
        ),
        "diagrama_pressao": {
            "ativo": [
                {"profundidade_m": 0.0, "pressao_kPa": 0.0},
                {"profundidade_m": profundidade_ponta_m, "pressao_kPa": (
                    coeficiente_ativo_rankine
                    * peso_especifico_solo_kN_m3
                    * profundidade_ponta_m
                )},
            ],
            "passivo_mobilizado": [
                {"profundidade_m": altura_livre_escavacao_m, "pressao_kPa": 0.0},
                {"profundidade_m": profundidade_ponta_m, "pressao_kPa": (
                    coeficiente_passivo_mobilizado
                    * peso_especifico_solo_kN_m3
                    * ficha_teorica_m
                )},
            ],
        },
    }


def validar_entradas_cortina_ancorada(entradas: dict[str, Any]) -> list[str]:
    """Valida as entradas do caso ancorado e suas hipóteses da planilha."""
    erros: list[str] = []
    campos_positivos = {
        "espessura_camada_superior_ate_na_m": "A espessura da camada superior deve ser maior que zero.",
        "peso_especifico_solo_superior_kN_m3": "O peso específico da camada superior deve ser maior que zero.",
        "peso_especifico_solo_submerso_kN_m3": "O peso específico submerso deve ser maior que zero.",
        "ficha_abaixo_escavacao_m": "A ficha abaixo da escavação deve ser maior que zero.",
        "angulo_atrito_solo_graus": "O ângulo de atrito deve ser maior que zero.",
        "fator_seguranca_minimo_tombamento": "O fator de segurança mínimo deve ser maior que zero.",
    }
    for campo, mensagem in campos_positivos.items():
        valor = entradas.get(campo)
        if not _numero_finito(valor) or valor <= 0:
            erros.append(mensagem)

    angulo_atrito_solo_graus = entradas.get("angulo_atrito_solo_graus")
    if _numero_finito(angulo_atrito_solo_graus) and angulo_atrito_solo_graus >= 90:
        erros.append("O ângulo de atrito deve ser menor que 90°.")

    for campo, nome in (
        ("sobrecarga_superficie_kPa", "A sobrecarga"),
        ("profundidade_na_ate_escavacao_m", "A profundidade do N.A. até a escavação"),
        ("altura_ancoragem_acima_na_m", "A altura da ancoragem acima do N.A."),
    ):
        valor = entradas.get(campo)
        if not _numero_finito(valor) or valor < 0:
            erros.append(f"{nome} não pode ser negativa.")

    percentual_passivo_mobilizado = entradas.get("percentual_passivo_mobilizado")
    if (
        not _numero_finito(percentual_passivo_mobilizado)
        or percentual_passivo_mobilizado <= 0
        or percentual_passivo_mobilizado > 100
    ):
        erros.append("A fração de passivo mobilizado deve estar entre 0% e 100%.")

    altura_ancoragem_acima_na_m = entradas.get("altura_ancoragem_acima_na_m")
    espessura_camada_superior_ate_na_m = entradas.get(
        "espessura_camada_superior_ate_na_m"
    )
    if (
        _numero_finito(altura_ancoragem_acima_na_m)
        and _numero_finito(espessura_camada_superior_ate_na_m)
        and altura_ancoragem_acima_na_m > espessura_camada_superior_ate_na_m
    ):
        erros.append("A ancoragem deve ficar entre a superfície e o nível d’água.")

    peso_agua = entradas.get("peso_especifico_agua_kN_m3", 9.81)
    if not _numero_finito(peso_agua) or peso_agua < 0:
        erros.append("O peso específico da água deve ser finito e não negativo.")

    return list(dict.fromkeys(erros))


def calcular_cortina_ancorada(entradas: dict[str, Any]) -> dict[str, Any]:
    """Calcula empuxos, força no tirante e FS do exemplo de cortina ancorada."""
    sobrecarga_superficie_kPa = entradas["sobrecarga_superficie_kPa"]
    espessura_camada_superior_ate_na_m = entradas[
        "espessura_camada_superior_ate_na_m"
    ]
    peso_especifico_solo_superior_kN_m3 = entradas[
        "peso_especifico_solo_superior_kN_m3"
    ]
    peso_especifico_solo_submerso_kN_m3 = entradas[
        "peso_especifico_solo_submerso_kN_m3"
    ]
    profundidade_na_ate_escavacao_m = entradas["profundidade_na_ate_escavacao_m"]
    ficha_abaixo_escavacao_m = entradas["ficha_abaixo_escavacao_m"]
    angulo_atrito_solo_graus = entradas["angulo_atrito_solo_graus"]
    altura_ancoragem_acima_na_m = entradas["altura_ancoragem_acima_na_m"]
    percentual_passivo_mobilizado = entradas["percentual_passivo_mobilizado"]
    fator_seguranca_minimo_tombamento = entradas[
        "fator_seguranca_minimo_tombamento"
    ]

    coeficiente_ativo_rankine, coeficiente_passivo_rankine = _coeficientes_rankine(
        angulo_atrito_solo_graus
    )
    fracao_passivo_mobilizado = percentual_passivo_mobilizado / 100.0
    profundidade_na_ate_ponta_m = (
        profundidade_na_ate_escavacao_m + ficha_abaixo_escavacao_m
    )
    profundidade_escavacao_abaixo_superficie_m = (
        espessura_camada_superior_ate_na_m + profundidade_na_ate_escavacao_m
    )
    profundidade_ponta_abaixo_superficie_m = (
        profundidade_escavacao_abaixo_superficie_m + ficha_abaixo_escavacao_m
    )

    pressao_ativa_no_na_kPa = coeficiente_ativo_rankine * (
        sobrecarga_superficie_kPa
        + peso_especifico_solo_superior_kN_m3
        * espessura_camada_superior_ate_na_m
    )
    pressao_ativa_no_topo_kPa = (
        coeficiente_ativo_rankine * sobrecarga_superficie_kPa
    )
    pressao_ativa_no_fundo_escavacao_kPa = pressao_ativa_no_na_kPa + (
        coeficiente_ativo_rankine
        * peso_especifico_solo_submerso_kN_m3
        * profundidade_na_ate_escavacao_m
    )
    pressao_ativa_na_ponta_kPa = pressao_ativa_no_na_kPa + (
        coeficiente_ativo_rankine
        * peso_especifico_solo_submerso_kN_m3
        * profundidade_na_ate_ponta_m
    )

    empuxo_ativo_retangulo_sobrecarga_kN_m = (
        coeficiente_ativo_rankine
        * sobrecarga_superficie_kPa
        * espessura_camada_superior_ate_na_m
    )
    empuxo_ativo_triangulo_camada_superior_kN_m = (
        0.5
        * coeficiente_ativo_rankine
        * peso_especifico_solo_superior_kN_m3
        * espessura_camada_superior_ate_na_m**2
    )
    empuxo_ativo_retangulo_abaixo_na_kN_m = (
        pressao_ativa_no_na_kPa * profundidade_na_ate_ponta_m
    )
    empuxo_ativo_triangulo_abaixo_na_kN_m = (
        0.5
        * coeficiente_ativo_rankine
        * peso_especifico_solo_submerso_kN_m3
        * profundidade_na_ate_ponta_m**2
    )
    parcelas_empuxo_ativo = [
        {
            "parcela": "E₁ · retângulo da sobrecarga",
            "empuxo_kN_m": empuxo_ativo_retangulo_sobrecarga_kN_m,
            "braco_assinado_m": (
                altura_ancoragem_acima_na_m
                - espessura_camada_superior_ate_na_m / 2.0
            ),
        },
        {
            "parcela": "E₂ · triângulo da camada superior",
            "empuxo_kN_m": empuxo_ativo_triangulo_camada_superior_kN_m,
            "braco_assinado_m": (
                altura_ancoragem_acima_na_m
                - espessura_camada_superior_ate_na_m / 3.0
            ),
        },
        {
            "parcela": "E₃ · retângulo abaixo do N.A.",
            "empuxo_kN_m": empuxo_ativo_retangulo_abaixo_na_kN_m,
            "braco_assinado_m": (
                altura_ancoragem_acima_na_m + profundidade_na_ate_ponta_m / 2.0
            ),
        },
        {
            "parcela": "E₄ · triângulo abaixo do N.A.",
            "empuxo_kN_m": empuxo_ativo_triangulo_abaixo_na_kN_m,
            "braco_assinado_m": (
                altura_ancoragem_acima_na_m
                + 2.0 * profundidade_na_ate_ponta_m / 3.0
            ),
        },
    ]
    for parcela in parcelas_empuxo_ativo:
        parcela["momento_assinado_kNm_m"] = (
            parcela["empuxo_kN_m"] * parcela["braco_assinado_m"]
        )

    empuxo_ativo_total_kN_m = sum(
        parcela["empuxo_kN_m"] for parcela in parcelas_empuxo_ativo
    )
    peso_agua = entradas.get("peso_especifico_agua_kN_m3", 9.81)
    pressao_agua_na_ponta_kPa = peso_agua * profundidade_na_ate_ponta_m
    empuxo_agua_kN_m = 0.5 * pressao_agua_na_ponta_kPa * profundidade_na_ate_ponta_m
    braco_agua_m = altura_ancoragem_acima_na_m + 2.0 * profundidade_na_ate_ponta_m / 3.0
    momento_agua_kNm_m = empuxo_agua_kN_m * braco_agua_m
    momento_solo_kNm_m = sum(
        parcela["momento_assinado_kNm_m"] for parcela in parcelas_empuxo_ativo
    )
    momento_ativo_resultante_kNm_m = momento_solo_kNm_m + momento_agua_kNm_m
    coeficiente_passivo_mobilizado = (
        coeficiente_passivo_rankine * fracao_passivo_mobilizado
    )
    empuxo_passivo_teorico_kN_m = (
        0.5
        * coeficiente_passivo_rankine
        * peso_especifico_solo_submerso_kN_m3
        * ficha_abaixo_escavacao_m**2
    )
    empuxo_passivo_mobilizado_kN_m = (
        empuxo_passivo_teorico_kN_m * fracao_passivo_mobilizado
    )
    forca_tirante_kN_m = (
        empuxo_ativo_total_kN_m + empuxo_agua_kN_m - empuxo_passivo_mobilizado_kN_m
    )
    braco_passivo_em_relacao_ancoragem_m = (
        altura_ancoragem_acima_na_m
        + profundidade_na_ate_escavacao_m
        + 2.0 * ficha_abaixo_escavacao_m / 3.0
    )
    momento_passivo_resistente_kNm_m = (
        empuxo_passivo_mobilizado_kN_m * braco_passivo_em_relacao_ancoragem_m
    )
    fator_seguranca_tombamento = (
        momento_passivo_resistente_kNm_m / momento_ativo_resultante_kNm_m
        if momento_ativo_resultante_kNm_m > 0
        else None
    )

    avisos: list[str] = []
    if forca_tirante_kN_m < 0:
        avisos.append(
            "A força calculada no tirante ficou negativa; reveja a combinação, pois o tirante trabalha à tração."
        )
    if fator_seguranca_tombamento is None:
        avisos.append("Não foi possível obter um momento ativo resultante positivo para calcular o FS.")
        status_tombamento = "REVER"
    elif fator_seguranca_tombamento >= fator_seguranca_minimo_tombamento and not avisos:
        status_tombamento = "ATENDE"
    else:
        status_tombamento = "REVER"
        if fator_seguranca_tombamento < fator_seguranca_minimo_tombamento:
            avisos.append(
                "O FS calculado está abaixo do mínimo informado para esta conferência."
            )

    return {
        "coeficiente_ativo_rankine": coeficiente_ativo_rankine,
        "coeficiente_passivo_rankine": coeficiente_passivo_rankine,
        "coeficiente_passivo_mobilizado": coeficiente_passivo_mobilizado,
        "profundidade_na_ate_ponta_m": profundidade_na_ate_ponta_m,
        "profundidade_escavacao_abaixo_superficie_m": profundidade_escavacao_abaixo_superficie_m,
        "profundidade_ponta_abaixo_superficie_m": profundidade_ponta_abaixo_superficie_m,
        "pressao_ativa_no_topo_kPa": pressao_ativa_no_topo_kPa,
        "pressao_ativa_no_na_kPa": pressao_ativa_no_na_kPa,
        "pressao_ativa_no_fundo_escavacao_kPa": pressao_ativa_no_fundo_escavacao_kPa,
        "pressao_ativa_na_ponta_kPa": pressao_ativa_na_ponta_kPa,
        "pressao_passiva_mobilizada_na_ponta_kPa": (
            coeficiente_passivo_mobilizado
            * peso_especifico_solo_submerso_kN_m3
            * ficha_abaixo_escavacao_m
        ),
        "empuxo_ativo_total_kN_m": empuxo_ativo_total_kN_m,
        "empuxo_hidrostatico_kN_m": empuxo_agua_kN_m,
        "braco_hidrostatico_m": braco_agua_m,
        "momento_hidrostatico_kNm_m": momento_agua_kNm_m,
        "momento_ativo_solo_kNm_m": momento_solo_kNm_m,
        "empuxo_ativo_por_parcela": parcelas_empuxo_ativo,
        "empuxo_passivo_teorico_kN_m": empuxo_passivo_teorico_kN_m,
        "empuxo_passivo_mobilizado_kN_m": empuxo_passivo_mobilizado_kN_m,
        "forca_tirante_kN_m": forca_tirante_kN_m,
        "momento_ativo_resultante_kNm_m": momento_ativo_resultante_kNm_m,
        "braco_passivo_em_relacao_ancoragem_m": braco_passivo_em_relacao_ancoragem_m,
        "momento_passivo_resistente_kNm_m": momento_passivo_resistente_kNm_m,
        "fator_seguranca_tombamento": fator_seguranca_tombamento,
        "status_tombamento": status_tombamento,
        "avisos": avisos,
        "diagrama_pressao": {
            "ativo": [
                {"profundidade_m": 0.0, "pressao_kPa": pressao_ativa_no_topo_kPa},
                {
                    "profundidade_m": espessura_camada_superior_ate_na_m,
                    "pressao_kPa": pressao_ativa_no_na_kPa,
                },
                {
                    "profundidade_m": profundidade_escavacao_abaixo_superficie_m,
                    "pressao_kPa": pressao_ativa_no_fundo_escavacao_kPa,
                },
                {
                    "profundidade_m": profundidade_ponta_abaixo_superficie_m,
                    "pressao_kPa": pressao_ativa_na_ponta_kPa,
                },
            ],
            "hidrostatico": [
                {"profundidade_m": espessura_camada_superior_ate_na_m, "pressao_kPa": 0.0},
                {
                    "profundidade_m": profundidade_ponta_abaixo_superficie_m,
                    "pressao_kPa": pressao_agua_na_ponta_kPa,
                },
            ],
            "passivo_mobilizado": [
                {
                    "profundidade_m": profundidade_escavacao_abaixo_superficie_m,
                    "pressao_kPa": 0.0,
                },
                {
                    "profundidade_m": profundidade_ponta_abaixo_superficie_m,
                    "pressao_kPa": (
                        coeficiente_passivo_mobilizado
                        * peso_especifico_solo_submerso_kN_m3
                        * ficha_abaixo_escavacao_m
                    ),
                },
            ],
        },
    }
