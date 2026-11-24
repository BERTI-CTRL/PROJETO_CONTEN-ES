"""Cálculos didáticos da aba Escoradas da planilha de referência."""

from __future__ import annotations

import math
from typing import Any


MODELOS_ENVOLTORIA = (
    "Areia — Terzaghi-Peck (1967)",
    "Argila mole/média — Terzaghi-Peck (1967)",
    "Argila dura/fissurada — Terzaghi-Peck (1967)",
)


def carregar_exemplos_escoradas() -> dict[str, dict[str, Any]]:
    """Retorna os exemplos numéricos já preenchidos na planilha."""
    return {
        "pressao_aparente": {
            "tipo_solo": MODELOS_ENVOLTORIA[0],
            "altura_escavacao_m": 6.0,
            "sobrecarga_superficie_kPa": 12.0,
            "peso_especifico_solo_kN_m3": 20.0,
            "angulo_atrito_solo_graus": 30.0,
            "coesao_nao_drenada_kPa": 50.0,
            "coeficiente_empirico_argila": 1.0,
            "quantidade_niveis_escora": 2,
            "espacamento_longitudinal_escoras_m": 1.3,
            "profundidade_nivel_agua_m": 6.0,
            "peso_especifico_agua_kN_m3": 9.81,
        },
        "ruptura_fundo": {
            "altura_escavacao_m": 6.0,
            "largura_escavacao_m": 8.0,
            "peso_especifico_solo_kN_m3": 18.0,
            "coesao_nao_drenada_kPa": 50.0,
            "fator_seguranca_minimo": 1.5,
        },
        "graux": {
            "altura_escavacao_m": 5.0,
            "diferenca_carga_agua_m": 3.5,
            "ficha_abaixo_fundo_m": 4.7,
            "peso_especifico_natural_kN_m3": 18.0,
            "peso_especifico_submerso_kN_m3": 11.0,
            "angulo_atrito_solo_graus": 30.0,
            "peso_especifico_agua_kN_m3": 10.0,
            "fator_seguranca_minimo": 1.5,
        },
        "froehlich": {
            "peso_especifico_solo_kN_m3": 16.0,
            "coesao_solo_kPa": 10.0,
            "angulo_atrito_solo_graus": 0.0,
            "altura_escavacao_m": 6.0,
        },
    }


def _numero_finito(valor: Any) -> bool:
    return (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and math.isfinite(valor)
    )


def _validar_numeros(
    entradas: dict[str, Any],
    campos: tuple[tuple[str, str, float], ...],
) -> list[str]:
    erros = []
    for nome_campo, nome_exibicao, valor_minimo in campos:
        valor = entradas.get(nome_campo)
        if not _numero_finito(valor):
            erros.append(f"Informe um valor numérico finito para {nome_exibicao}.")
        elif valor < valor_minimo:
            erros.append(f"{nome_exibicao} deve ser maior ou igual a {valor_minimo:g}.")
    return erros


def validar_pressao_aparente(entradas: dict[str, Any]) -> list[str]:
    erros = _validar_numeros(
        entradas,
        (
            ("altura_escavacao_m", "a altura da escavação", 0.01),
            ("sobrecarga_superficie_kPa", "a sobrecarga", 0.0),
            ("peso_especifico_solo_kN_m3", "o peso específico do solo", 0.01),
            ("angulo_atrito_solo_graus", "o ângulo de atrito", 0.0),
            ("coesao_nao_drenada_kPa", "a coesão não drenada", 0.0),
            ("coeficiente_empirico_argila", "o coeficiente m da argila", 0.01),
            ("quantidade_niveis_escora", "o número de níveis de escoras", 1),
            ("espacamento_longitudinal_escoras_m", "o espaçamento entre escoras", 0.01),
            ("profundidade_nivel_agua_m", "a profundidade do nível d'água", 0.0),
            ("peso_especifico_agua_kN_m3", "o peso específico da água", 0.01),
        ),
    )
    angulo_atrito = entradas.get("angulo_atrito_solo_graus")
    if _numero_finito(angulo_atrito) and angulo_atrito >= 90:
        erros.append("O ângulo de atrito deve ser menor que 90°.")
    if entradas.get("tipo_solo") not in MODELOS_ENVOLTORIA:
        erros.append("Selecione um dos modelos de envoltória disponíveis.")
    quantidade_escoras = entradas.get("quantidade_niveis_escora")
    if _numero_finito(quantidade_escoras) and quantidade_escoras != int(quantidade_escoras):
        erros.append("O número de níveis de escoras precisa ser inteiro.")

    if not erros and entradas["tipo_solo"] == MODELOS_ENVOLTORIA[1]:
        coeficiente_modificado = 1.0 - (
            entradas["coeficiente_empirico_argila"]
            * 4.0
            * entradas["coesao_nao_drenada_kPa"]
            / (
                entradas["peso_especifico_solo_kN_m3"]
                * entradas["altura_escavacao_m"]
            )
        )
        if coeficiente_modificado <= 0:
            erros.append(
                "Para argila mole/média, o coeficiente ativo modificado precisa ser positivo. "
                "Revise γ, H, cu e m."
            )
    return erros


def calcular_pressao_aparente(entradas: dict[str, Any]) -> dict[str, Any]:
    """Calcula envoltória, resultantes e força aproximada em cada escora."""
    erros = validar_pressao_aparente(entradas)
    if erros:
        raise ValueError(" ".join(erros))

    altura_escavacao_m = entradas["altura_escavacao_m"]
    peso_especifico_solo_kN_m3 = entradas["peso_especifico_solo_kN_m3"]
    tipo_solo = entradas["tipo_solo"]
    coeficiente_ativo_rankine = math.tan(
        math.radians(45.0 - entradas["angulo_atrito_solo_graus"] / 2.0)
    ) ** 2
    coeficiente_ativo_modificado = None

    if tipo_solo == MODELOS_ENVOLTORIA[0]:
        pressao_aparente_maxima_kPa = (
            0.65
            * (
                peso_especifico_solo_kN_m3 * altura_escavacao_m
                + entradas["sobrecarga_superficie_kPa"]
            )
            * coeficiente_ativo_rankine
        )
        area_relativa_envoltoria = 1.0
    elif tipo_solo == MODELOS_ENVOLTORIA[1]:
        coeficiente_ativo_modificado = 1.0 - (
            entradas["coeficiente_empirico_argila"]
            * 4.0
            * entradas["coesao_nao_drenada_kPa"]
            / (peso_especifico_solo_kN_m3 * altura_escavacao_m)
        )
        pressao_aparente_maxima_kPa = (
            entradas["coeficiente_empirico_argila"]
            * peso_especifico_solo_kN_m3
            * altura_escavacao_m
            * max(0.0, coeficiente_ativo_modificado)
        )
        area_relativa_envoltoria = 0.75
    else:
        # O valor 0,20γH reproduz a fórmula da planilha. A aula também mostra
        # uma faixa de 0,28γH a 0,40γH para a argila dura/fissurada.
        pressao_aparente_maxima_kPa = 0.2 * peso_especifico_solo_kN_m3 * altura_escavacao_m
        area_relativa_envoltoria = 0.75

    resultante_aparente_kN_m = (
        pressao_aparente_maxima_kPa
        * altura_escavacao_m
        * area_relativa_envoltoria
    )
    profundidade_agua_no_corte_m = max(
        altura_escavacao_m - entradas["profundidade_nivel_agua_m"], 0.0
    )
    resultante_hidrostatica_kN_m = (
        0.5
        * entradas["peso_especifico_agua_kN_m3"]
        * profundidade_agua_no_corte_m**2
    )
    resultante_total_kN_m = resultante_aparente_kN_m + resultante_hidrostatica_kN_m
    if resultante_total_kN_m > 0:
        braco_resultante_desde_fundo_m = (
            resultante_aparente_kN_m * altura_escavacao_m / 2.0
            + resultante_hidrostatica_kN_m * profundidade_agua_no_corte_m / 3.0
        ) / resultante_total_kN_m
    else:
        braco_resultante_desde_fundo_m = 0.0
    forca_axial_aproximada_por_escora_kN = (
        resultante_total_kN_m
        * entradas["espacamento_longitudinal_escoras_m"]
        / entradas["quantidade_niveis_escora"]
    )

    transicao_m = 0.25 * altura_escavacao_m
    diagrama_pressao_aparente = []
    for indice_ponto in range(41):
        profundidade_m = altura_escavacao_m * indice_ponto / 40.0
        if tipo_solo == MODELOS_ENVOLTORIA[0]:
            pressao_kPa = pressao_aparente_maxima_kPa
        else:
            fator_envoltoria = min(
                1.0,
                profundidade_m / transicao_m,
                (altura_escavacao_m - profundidade_m) / transicao_m,
            )
            pressao_kPa = pressao_aparente_maxima_kPa * max(0.0, fator_envoltoria)
        diagrama_pressao_aparente.append(
            {"profundidade_m": profundidade_m, "pressao_kPa": pressao_kPa}
        )

    diagrama_pressao_agua = []
    if profundidade_agua_no_corte_m > 0:
        profundidade_inicio_agua_m = entradas["profundidade_nivel_agua_m"]
        for indice_ponto in range(21):
            profundidade_m = profundidade_inicio_agua_m + (
                profundidade_agua_no_corte_m * indice_ponto / 20.0
            )
            diagrama_pressao_agua.append(
                {
                    "profundidade_m": profundidade_m,
                    "pressao_kPa": entradas["peso_especifico_agua_kN_m3"]
                    * (profundidade_m - profundidade_inicio_agua_m),
                }
            )

    return {
        "coeficiente_ativo_rankine": coeficiente_ativo_rankine,
        "coeficiente_ativo_modificado": coeficiente_ativo_modificado,
        "pressao_aparente_maxima_kPa": pressao_aparente_maxima_kPa,
        "resultante_aparente_kN_m": resultante_aparente_kN_m,
        "resultante_hidrostatica_kN_m": resultante_hidrostatica_kN_m,
        "resultante_total_kN_m": resultante_total_kN_m,
        "braco_resultante_desde_fundo_m": braco_resultante_desde_fundo_m,
        "forca_axial_aproximada_por_escora_kN": forca_axial_aproximada_por_escora_kN,
        "profundidade_agua_no_corte_m": profundidade_agua_no_corte_m,
        "diagrama_pressao_aparente": diagrama_pressao_aparente,
        "diagrama_pressao_agua": diagrama_pressao_agua,
    }


def validar_ruptura_fundo(entradas: dict[str, Any]) -> list[str]:
    return _validar_numeros(
        entradas,
        (
            ("altura_escavacao_m", "a altura da escavação", 0.01),
            ("largura_escavacao_m", "a largura da escavação", 0.01),
            ("peso_especifico_solo_kN_m3", "o peso específico do solo", 0.01),
            ("coesao_nao_drenada_kPa", "a coesão não drenada", 0.0),
            ("fator_seguranca_minimo", "o fator de segurança mínimo", 0.01),
        ),
    )


def calcular_ruptura_fundo(entradas: dict[str, Any]) -> dict[str, Any]:
    """Aplica a expressão simplificada de Terzaghi usada na planilha."""
    erros = validar_ruptura_fundo(entradas)
    if erros:
        raise ValueError(" ".join(erros))

    altura_escavacao_m = entradas["altura_escavacao_m"]
    largura_escavacao_m = entradas["largura_escavacao_m"]
    peso_especifico_solo_kN_m3 = entradas["peso_especifico_solo_kN_m3"]
    coesao_nao_drenada_kPa = entradas["coesao_nao_drenada_kPa"]
    tensao_vertical_solicitante_kPa = (
        peso_especifico_solo_kN_m3 * altura_escavacao_m
        - (2.0 / largura_escavacao_m)
        * altura_escavacao_m
        * coesao_nao_drenada_kPa
    )
    resistencia_nao_drenada_kPa = 5.7 * coesao_nao_drenada_kPa
    # A planilha retorna zero quando a tensão solicitante não é positiva.
    fator_seguranca = (
        resistencia_nao_drenada_kPa / tensao_vertical_solicitante_kPa
        if tensao_vertical_solicitante_kPa > 0
        else 0.0
    )
    denominador_profundidade_critica = (
        peso_especifico_solo_kN_m3
        - 2.0 * coesao_nao_drenada_kPa / largura_escavacao_m
    )
    profundidade_critica_m = (
        resistencia_nao_drenada_kPa / denominador_profundidade_critica
        if denominador_profundidade_critica > 0
        else None
    )
    return {
        "tensao_vertical_solicitante_kPa": tensao_vertical_solicitante_kPa,
        "resistencia_nao_drenada_kPa": resistencia_nao_drenada_kPa,
        "fator_seguranca": fator_seguranca,
        "profundidade_critica_m": profundidade_critica_m,
        "status": (
            "ATENDE"
            if tensao_vertical_solicitante_kPa > 0
            and fator_seguranca >= entradas["fator_seguranca_minimo"]
            else "REVER"
        ),
        "tensao_solicitante_fora_do_dominio": tensao_vertical_solicitante_kPa <= 0,
    }


def validar_graux(entradas: dict[str, Any]) -> list[str]:
    erros = _validar_numeros(
        entradas,
        (
            ("altura_escavacao_m", "a altura da escavação", 0.01),
            ("diferenca_carga_agua_m", "a diferença de carga d'água", 0.0),
            ("ficha_abaixo_fundo_m", "a ficha abaixo do fundo", 0.01),
            ("peso_especifico_natural_kN_m3", "o peso específico natural", 0.01),
            ("peso_especifico_submerso_kN_m3", "o peso específico submerso", 0.01),
            ("angulo_atrito_solo_graus", "o ângulo de atrito", 0.0),
            ("peso_especifico_agua_kN_m3", "o peso específico da água", 0.01),
            ("fator_seguranca_minimo", "o fator de segurança mínimo", 0.01),
        ),
    )
    angulo_atrito = entradas.get("angulo_atrito_solo_graus")
    if _numero_finito(angulo_atrito) and angulo_atrito >= 90:
        erros.append("O ângulo de atrito deve ser menor que 90°.")
    elif _numero_finito(angulo_atrito) and angulo_atrito >= 0:
        try:
            math.exp(math.pi * math.tan(math.radians(angulo_atrito)))
        except OverflowError:
            erros.append(
                "O ângulo informado deixa Nq fora do limite numérico da expressão de Graux. "
                "Revise o valor de φ."
            )
    return erros


def calcular_graux(entradas: dict[str, Any]) -> dict[str, Any]:
    """Calcula o fator de segurança hidráulico simplificado da planilha."""
    erros = validar_graux(entradas)
    if erros:
        raise ValueError(" ".join(erros))

    diferenca_carga_agua_m = entradas["diferenca_carga_agua_m"]
    ficha_abaixo_fundo_m = entradas["ficha_abaixo_fundo_m"]
    comprimento_percolacao_m = diferenca_carga_agua_m + 2.0 * ficha_abaixo_fundo_m
    gradiente_hidraulico = diferenca_carga_agua_m / comprimento_percolacao_m
    tensao_exterior_kPa = (
        max(entradas["altura_escavacao_m"] - diferenca_carga_agua_m, 0.0)
        * entradas["peso_especifico_natural_kN_m3"]
        + (diferenca_carga_agua_m + ficha_abaixo_fundo_m)
        * (
            entradas["peso_especifico_submerso_kN_m3"]
            + gradiente_hidraulico * entradas["peso_especifico_agua_kN_m3"]
        )
    )
    tensao_interior_kPa = ficha_abaixo_fundo_m * max(
        entradas["peso_especifico_submerso_kN_m3"]
        - gradiente_hidraulico * entradas["peso_especifico_agua_kN_m3"],
        0.0,
    )
    tangente_atrito = math.tan(math.radians(entradas["angulo_atrito_solo_graus"]))
    fator_capacidade_carga_nq = (
        math.tan(math.radians(45.0 + entradas["angulo_atrito_solo_graus"] / 2.0)) ** 2
        * math.exp(math.pi * tangente_atrito)
    )
    fator_seguranca = (
        tensao_interior_kPa * fator_capacidade_carga_nq / tensao_exterior_kPa
        if tensao_exterior_kPa > 0
        else 0.0
    )
    return {
        "comprimento_percolacao_m": comprimento_percolacao_m,
        "gradiente_hidraulico": gradiente_hidraulico,
        "tensao_exterior_kPa": tensao_exterior_kPa,
        "tensao_interior_kPa": tensao_interior_kPa,
        "fator_capacidade_carga_nq": fator_capacidade_carga_nq,
        "fator_seguranca": fator_seguranca,
        "status": (
            "ATENDE"
            if fator_seguranca >= entradas["fator_seguranca_minimo"]
            else "REVER"
        ),
    }


def validar_froehlich(entradas: dict[str, Any]) -> list[str]:
    erros = _validar_numeros(
        entradas,
        (
            ("peso_especifico_solo_kN_m3", "o peso específico do solo", 0.01),
            ("coesao_solo_kPa", "a coesão do solo", 0.0),
            ("angulo_atrito_solo_graus", "o ângulo de atrito", 0.0),
            ("altura_escavacao_m", "a altura da escavação", 0.0),
        ),
    )
    angulo_atrito = entradas.get("angulo_atrito_solo_graus")
    if _numero_finito(angulo_atrito) and angulo_atrito >= 90:
        erros.append("O ângulo de atrito deve ser menor que 90°.")
    return erros


def calcular_froehlich(entradas: dict[str, Any]) -> dict[str, Any]:
    """Calcula a altura crítica teórica de um corte vertical sem suporte."""
    erros = validar_froehlich(entradas)
    if erros:
        raise ValueError(" ".join(erros))

    altura_critica_m = (
        4.0
        * entradas["coesao_solo_kPa"]
        / entradas["peso_especifico_solo_kN_m3"]
        * math.tan(math.radians(45.0 + entradas["angulo_atrito_solo_graus"] / 2.0))
    )
    return {
        "altura_critica_m": altura_critica_m,
        "altura_escavacao_m": entradas["altura_escavacao_m"],
        "status": (
            "H ≤ Hcr · limite teórico atendido"
            if entradas["altura_escavacao_m"] <= altura_critica_m
            else "H > Hcr · escoramento necessário"
        ),
    }
