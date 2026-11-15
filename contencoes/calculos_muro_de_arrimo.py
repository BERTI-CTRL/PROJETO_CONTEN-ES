"""Cálculos do Muro, sem dependência da interface.

Para acompanhar o arquivo: carregue o exemplo, valide as entradas e chame
``calcular_muro``. O cálculo principal é separado em trechos, empuxos e
estabilidade.
"""

from __future__ import annotations

from math import cos, radians, sin, sqrt, tan
from typing import Any


def carregar_exemplo_muro() -> tuple[dict[str, Any], list[dict[str, float]]]:
    """Retorna o caso-base da planilha de conferência."""
    entradas_muro = {
        "altura_muro_m": 6.30,
        "largura_base_m": 4.00,
        "largura_topo_m": 1.00,
        "peso_especifico_concreto_kN_m3": 22.0,
        "sobrecarga_kPa": 12.0,
        "coeficiente_atrito_base": 0.60,
        "tensao_admissivel_fundacao_kPa": 300.0,
        "fator_seguranca_minimo_tombamento": 1.50,
        "fator_seguranca_minimo_deslizamento": 1.50,
        "metodo_empuxo": "Rankine",
        "inclinacao_aterro_graus": 0.0,
        "atrito_solo_muro_graus": 0.0,
        "profundidade_nivel_agua_m": None,
        "peso_especifico_agua_kN_m3": 9.81,
    }
    camadas_solo = [
        {
            "espessura_m": 6.30,
            "peso_especifico_natural_kN_m3": 17.0,
            "peso_especifico_saturado_kN_m3": 17.0,
            "angulo_atrito_graus": 30.0,
            "coesao_kPa": 0.0,
        }
    ]
    return entradas_muro, camadas_solo


def _numero_finito(valor: Any) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and valor == valor and abs(valor) != float("inf")


def _valor_vazio(valor: Any) -> bool:
    return valor is None or valor == ""


def validar_entradas_muro(
    entradas_muro: dict[str, Any], camadas_solo: list[dict[str, Any]]
) -> list[str]:
    """Confere entradas e hipóteses do modelo adotado pela planilha."""
    erros: list[str] = []

    campos_positivos = {
        "altura_muro_m": "A altura do muro deve ser maior que zero.",
        "largura_base_m": "A largura da base deve ser maior que zero.",
        "largura_topo_m": "A largura do topo deve ser maior que zero.",
        "peso_especifico_concreto_kN_m3": "O peso específico do concreto deve ser maior que zero.",
        "tensao_admissivel_fundacao_kPa": "A tensão admissível deve ser maior que zero.",
        "fator_seguranca_minimo_tombamento": "O FS mínimo contra tombamento deve ser maior que zero.",
        "fator_seguranca_minimo_deslizamento": "O FS mínimo contra deslizamento deve ser maior que zero.",
        "peso_especifico_agua_kN_m3": "O peso específico da água deve ser maior que zero.",
    }
    for nome_campo, mensagem in campos_positivos.items():
        valor = entradas_muro.get(nome_campo)
        if not _numero_finito(valor) or valor <= 0:
            erros.append(mensagem)

    for nome_campo, descricao in (
        ("sobrecarga_kPa", "A sobrecarga"),
        ("coeficiente_atrito_base", "O coeficiente de atrito na base"),
    ):
        valor = entradas_muro.get(nome_campo)
        if not _numero_finito(valor) or valor < 0:
            erros.append(f"{descricao} não pode ser negativa.")

    altura_muro_m = entradas_muro.get("altura_muro_m")
    largura_base_m = entradas_muro.get("largura_base_m")
    largura_topo_m = entradas_muro.get("largura_topo_m")
    if all(_numero_finito(valor) for valor in (largura_base_m, largura_topo_m)):
        if largura_base_m <= largura_topo_m:
            erros.append("A largura da base deve ser maior que a largura do topo.")

    inclinacao_aterro_graus = entradas_muro.get("inclinacao_aterro_graus")
    atrito_solo_muro_graus = entradas_muro.get("atrito_solo_muro_graus")
    for valor, nome_campo in (
        (inclinacao_aterro_graus, "A inclinação do aterro"),
        (atrito_solo_muro_graus, "O atrito solo–muro"),
    ):
        if not _numero_finito(valor) or valor < 0 or valor >= 90:
            erros.append(f"{nome_campo} deve estar entre 0° e 90° (sem incluir 90°).")

    profundidade_nivel_agua_m = entradas_muro.get("profundidade_nivel_agua_m")
    peso_especifico_agua_kN_m3 = entradas_muro.get("peso_especifico_agua_kN_m3")
    if not _valor_vazio(profundidade_nivel_agua_m):
        if not _numero_finito(profundidade_nivel_agua_m):
            erros.append("Informe uma profundidade numérica para o N.A. ou deixe o campo vazio.")
        elif _numero_finito(altura_muro_m) and not 0 <= profundidade_nivel_agua_m <= altura_muro_m:
            erros.append("O N.A. deve estar entre o topo e a base do muro (0 ≤ z ≤ H).")

    camadas_validas: list[dict[str, Any]] = []
    encontrou_linha_vazia = False
    for indice_camada, camada_solo in enumerate(camadas_solo, start=1):
        espessura_m = camada_solo.get("espessura_m")
        peso_natural = camada_solo.get("peso_especifico_natural_kN_m3")
        peso_saturado = camada_solo.get("peso_especifico_saturado_kN_m3")
        angulo_atrito = camada_solo.get("angulo_atrito_graus")
        coesao = camada_solo.get("coesao_kPa")
        valores_camada = (espessura_m, peso_natural, peso_saturado, angulo_atrito, coesao)

        linha_vazia = all(_valor_vazio(valor) or valor == 0 for valor in valores_camada)
        if linha_vazia:
            encontrou_linha_vazia = True
            continue
        if encontrou_linha_vazia:
            erros.append(
                f"A Camada {indice_camada} foi preenchida depois de uma linha vazia; "
                "as camadas devem ser contínuas e estar em sequência."
            )
            encontrou_linha_vazia = False

        propriedades_numericas = {
            "espessura": espessura_m,
            "peso específico natural": peso_natural,
            "peso específico saturado": peso_saturado,
            "ângulo de atrito": angulo_atrito,
            "coesão": coesao,
        }
        for descricao, valor in propriedades_numericas.items():
            if not _numero_finito(valor):
                erros.append(f"Informe um valor numérico para {descricao} da Camada {indice_camada}.")

        if not all(_numero_finito(valor) for valor in valores_camada):
            continue
        if espessura_m <= 0:
            erros.append(f"A espessura da Camada {indice_camada} deve ser maior que zero.")
        if peso_natural <= 0 or peso_saturado <= 0:
            erros.append(f"Os pesos específicos da Camada {indice_camada} devem ser maiores que zero.")
        if angulo_atrito <= 0 or angulo_atrito >= 90:
            erros.append(f"O ângulo de atrito da Camada {indice_camada} deve estar entre 0° e 90°.")
        if coesao < 0:
            erros.append(f"A coesão da Camada {indice_camada} não pode ser negativa.")
        if espessura_m > 0 and peso_natural > 0 and peso_saturado > 0 and 0 < angulo_atrito < 90 and coesao >= 0:
            camadas_validas.append(camada_solo)

    if not camadas_validas:
        erros.append("Informe ao menos uma camada de solo completa.")
    elif _numero_finito(altura_muro_m):
        espessura_total_m = sum(camada["espessura_m"] for camada in camadas_validas)
        if abs(espessura_total_m - altura_muro_m) > 0.001:
            erros.append(
                f"A soma das camadas ({espessura_total_m:.3f} m) deve ser igual à altura do muro "
                f"({altura_muro_m:.3f} m), com tolerância de 0,001 m."
            )

    metodo_empuxo = entradas_muro.get("metodo_empuxo")
    if metodo_empuxo not in ("Rankine", "Coulomb"):
        erros.append("Selecione a teoria de empuxo Rankine ou Coulomb.")
    elif all(_numero_finito(valor) for valor in (inclinacao_aterro_graus, atrito_solo_muro_graus)):
        if metodo_empuxo == "Rankine":
            if abs(atrito_solo_muro_graus) > 1e-12:
                erros.append("Para Rankine, o atrito solo–muro deve ser igual a zero.")
            if abs(inclinacao_aterro_graus) > 1e-12:
                if len(camadas_validas) != 1:
                    erros.append("Rankine com aterro inclinado está limitado a uma camada de solo.")
                elif camadas_validas[0]["coesao_kPa"] != 0:
                    erros.append("Rankine com aterro inclinado exige coesão igual a zero.")
                elif inclinacao_aterro_graus >= camadas_validas[0]["angulo_atrito_graus"]:
                    erros.append("Para Rankine com aterro inclinado, β deve ser menor que φ.")
        elif len(camadas_validas) == 1:
            camada_unica = camadas_validas[0]
            if camada_unica["coesao_kPa"] != 0:
                erros.append("Coulomb está limitado a uma camada sem coesão (c = 0).")
            if inclinacao_aterro_graus >= camada_unica["angulo_atrito_graus"]:
                erros.append("Para Coulomb, β deve ser menor que φ.")
            if atrito_solo_muro_graus >= camada_unica["angulo_atrito_graus"]:
                erros.append("Para Coulomb, δ deve ser menor que φ.")
            if (
                inclinacao_aterro_graus > 0
                and not _valor_vazio(profundidade_nivel_agua_m)
                and _numero_finito(altura_muro_m)
                and _numero_finito(profundidade_nivel_agua_m)
                and 0 < profundidade_nivel_agua_m < altura_muro_m
            ):
                erros.append("Coulomb com aterro inclinado e N.A. parcial está fora do modelo direto da planilha.")
        else:
            erros.append("Coulomb está limitado a uma camada de solo.")

    if (
        _numero_finito(profundidade_nivel_agua_m)
        and _numero_finito(altura_muro_m)
        and profundidade_nivel_agua_m < altura_muro_m
        and _numero_finito(peso_especifico_agua_kN_m3)
    ):
        profundidade_acumulada_m = 0.0
        for indice_camada, camada_solo in enumerate(camadas_validas, start=1):
            profundidade_acumulada_m += camada_solo["espessura_m"]
            if (
                profundidade_acumulada_m > profundidade_nivel_agua_m
                and camada_solo["peso_especifico_saturado_kN_m3"] <= peso_especifico_agua_kN_m3
            ):
                erros.append(
                    f"O peso específico saturado da Camada {indice_camada} deve ser maior que γw "
                    "na parte abaixo do N.A."
                )

    return list(dict.fromkeys(erros))


def _coeficiente_empuxo_ativo(
    metodo_empuxo: str,
    angulo_atrito_graus: float,
    inclinacao_aterro_graus: float,
    atrito_solo_muro_graus: float,
) -> float:
    angulo_atrito_rad = radians(angulo_atrito_graus)
    inclinacao_aterro_rad = radians(inclinacao_aterro_graus)
    atrito_solo_muro_rad = radians(atrito_solo_muro_graus)

    if metodo_empuxo == "Coulomb":
        numerador = cos(angulo_atrito_rad) ** 2
        termo_raiz = (
            sin(angulo_atrito_rad + atrito_solo_muro_rad)
            * sin(angulo_atrito_rad - inclinacao_aterro_rad)
            / (cos(atrito_solo_muro_rad) * cos(inclinacao_aterro_rad))
        )
        return numerador / (cos(atrito_solo_muro_rad) * (1 + sqrt(termo_raiz)) ** 2)

    if abs(inclinacao_aterro_graus) <= 1e-12:
        return tan(radians(45.0 - angulo_atrito_graus / 2.0)) ** 2

    cosseno_aterro = cos(inclinacao_aterro_rad)
    raiz_termo_rankine = sqrt(cosseno_aterro**2 - cos(angulo_atrito_rad) ** 2)
    return cosseno_aterro * (cosseno_aterro - raiz_termo_rankine) / (
        cosseno_aterro + raiz_termo_rankine
    )


def _integrar_pressao_linear(
    pressao_superior_kPa: float, pressao_inferior_kPa: float, altura_trecho_m: float
) -> tuple[float, float]:
    """Integra a parcela compressiva e retorna força e braço desde a base do trecho."""
    if altura_trecho_m <= 0 or (pressao_superior_kPa <= 0 and pressao_inferior_kPa <= 0):
        return 0.0, 0.0

    if pressao_superior_kPa < 0 < pressao_inferior_kPa:
        altura_compressiva_m = (
            altura_trecho_m * pressao_inferior_kPa / (pressao_inferior_kPa - pressao_superior_kPa)
        )
        empuxo_kN_m = 0.5 * altura_trecho_m * pressao_inferior_kPa**2 / (
            pressao_inferior_kPa - pressao_superior_kPa
        )
        braco_desde_base_m = altura_compressiva_m / 3.0
    elif pressao_superior_kPa > 0 > pressao_inferior_kPa:
        altura_compressiva_m = (
            altura_trecho_m * pressao_superior_kPa / (pressao_superior_kPa - pressao_inferior_kPa)
        )
        empuxo_kN_m = 0.5 * altura_trecho_m * pressao_superior_kPa**2 / (
            pressao_superior_kPa - pressao_inferior_kPa
        )
        braco_desde_base_m = altura_trecho_m - altura_compressiva_m / 3.0
    else:
        empuxo_kN_m = (
            altura_trecho_m * (pressao_superior_kPa + pressao_inferior_kPa) / 2.0
        )
        soma_pressao_kPa = pressao_superior_kPa + pressao_inferior_kPa
        braco_desde_base_m = (
            altura_trecho_m
            * (2.0 * pressao_superior_kPa + pressao_inferior_kPa)
            / (3.0 * soma_pressao_kPa)
        )
    return empuxo_kN_m, braco_desde_base_m


def calcular_muro(entradas_muro: dict[str, Any], camadas_solo: list[dict[str, Any]]) -> dict[str, Any]:
    """Coordena o cálculo: trechos, esforços, estabilidade e gráficos."""
    erros_entrada = validar_entradas_muro(entradas_muro, camadas_solo)
    if erros_entrada:
        raise ValueError("Corrija as entradas antes de calcular: " + " ".join(erros_entrada))

    trechos = _criar_trechos_muro(entradas_muro, camadas_solo)
    empuxos = _somar_empuxos(trechos)
    resumo, verificacoes = _calcular_estabilidade(entradas_muro, empuxos)

    return {
        "resumo": resumo,
        "verificacoes": verificacoes,
        "trechos": trechos,
        "geometria_muro": _criar_geometria_muro(entradas_muro),
        "diagramas_pressao": _criar_diagramas_pressao(trechos),
    }


def _criar_trechos_muro(
    entradas_muro: dict[str, Any], camadas_solo: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Divide o perfil em trechos nas camadas e no nível d'água."""
    trechos = []
    profundidade_topo_camada_m = 0.0
    tensao_vertical_acumulada_kPa = 0.0
    profundidade_nivel_agua_m = entradas_muro["profundidade_nivel_agua_m"]

    for indice_camada, camada_solo in enumerate(camadas_solo, start=1):
        if camada_solo["espessura_m"] == 0:
            continue

        profundidade_base_camada_m = (
            profundidade_topo_camada_m + camada_solo["espessura_m"]
        )
        limites_trecho_m = [profundidade_topo_camada_m, profundidade_base_camada_m]
        if (
            profundidade_nivel_agua_m is not None
            and profundidade_topo_camada_m < profundidade_nivel_agua_m < profundidade_base_camada_m
        ):
            limites_trecho_m.insert(1, profundidade_nivel_agua_m)

        coeficiente_empuxo_ativo = _coeficiente_empuxo_ativo(
            entradas_muro["metodo_empuxo"],
            camada_solo["angulo_atrito_graus"],
            entradas_muro["inclinacao_aterro_graus"],
            entradas_muro["atrito_solo_muro_graus"],
        )
        for profundidade_superior_m, profundidade_inferior_m in zip(
            limites_trecho_m, limites_trecho_m[1:]
        ):
            trecho, tensao_vertical_acumulada_kPa = _calcular_trecho_muro(
                entradas_muro,
                camada_solo,
                indice_camada,
                coeficiente_empuxo_ativo,
                profundidade_superior_m,
                profundidade_inferior_m,
                tensao_vertical_acumulada_kPa,
            )
            trechos.append(trecho)

        profundidade_topo_camada_m = profundidade_base_camada_m

    return trechos


def _calcular_trecho_muro(
    entradas_muro: dict[str, Any],
    camada_solo: dict[str, Any],
    indice_camada: int,
    coeficiente_empuxo_ativo: float,
    profundidade_superior_m: float,
    profundidade_inferior_m: float,
    tensao_vertical_superior_kPa: float,
) -> tuple[dict[str, Any], float]:
    """Calcula pressões, empuxos e momentos em um trecho do perfil."""
    altura_trecho_m = profundidade_inferior_m - profundidade_superior_m
    profundidade_media_m = (profundidade_superior_m + profundidade_inferior_m) / 2.0
    profundidade_nivel_agua_m = entradas_muro["profundidade_nivel_agua_m"]
    peso_especifico_agua_kN_m3 = entradas_muro["peso_especifico_agua_kN_m3"]
    esta_abaixo_nivel_agua = (
        profundidade_nivel_agua_m is not None
        and profundidade_media_m >= profundidade_nivel_agua_m
    )

    if esta_abaixo_nivel_agua:
        peso_especifico_efetivo_kN_m3 = (
            camada_solo["peso_especifico_saturado_kN_m3"] - peso_especifico_agua_kN_m3
        )
        identificacao_trecho = f"Camada {indice_camada} / abaixo do N.A."
    else:
        peso_especifico_efetivo_kN_m3 = camada_solo["peso_especifico_natural_kN_m3"]
        identificacao_trecho = (
            f"Camada {indice_camada} / acima do N.A."
            if profundidade_nivel_agua_m is not None
            else f"Camada {indice_camada} / solo natural"
        )

    tensao_vertical_inferior_kPa = (
        tensao_vertical_superior_kPa + altura_trecho_m * peso_especifico_efetivo_kN_m3
    )
    raiz_coeficiente_ativo = sqrt(coeficiente_empuxo_ativo)
    pressao_solo_bruta_superior_kPa = (
        coeficiente_empuxo_ativo * tensao_vertical_superior_kPa
        - 2.0 * camada_solo["coesao_kPa"] * raiz_coeficiente_ativo
    )
    pressao_solo_bruta_inferior_kPa = (
        coeficiente_empuxo_ativo * tensao_vertical_inferior_kPa
        - 2.0 * camada_solo["coesao_kPa"] * raiz_coeficiente_ativo
    )
    pressao_solo_superior_kPa = max(0.0, pressao_solo_bruta_superior_kPa)
    pressao_solo_inferior_kPa = max(0.0, pressao_solo_bruta_inferior_kPa)
    pressao_sobrecarga_kPa = (
        coeficiente_empuxo_ativo * entradas_muro["sobrecarga_kPa"]
    )

    if profundidade_nivel_agua_m is None:
        pressao_agua_superior_kPa = 0.0
        pressao_agua_inferior_kPa = 0.0
    else:
        pressao_agua_superior_kPa = peso_especifico_agua_kN_m3 * max(
            profundidade_superior_m - profundidade_nivel_agua_m, 0.0
        )
        pressao_agua_inferior_kPa = peso_especifico_agua_kN_m3 * max(
            profundidade_inferior_m - profundidade_nivel_agua_m, 0.0
        )

    empuxo_solo_kN_m, braco_solo_no_trecho_m = _integrar_pressao_linear(
        pressao_solo_bruta_superior_kPa,
        pressao_solo_bruta_inferior_kPa,
        altura_trecho_m,
    )
    empuxo_sobrecarga_kN_m, braco_sobrecarga_no_trecho_m = _integrar_pressao_linear(
        pressao_sobrecarga_kPa, pressao_sobrecarga_kPa, altura_trecho_m
    )
    empuxo_agua_kN_m, braco_agua_no_trecho_m = _integrar_pressao_linear(
        pressao_agua_superior_kPa, pressao_agua_inferior_kPa, altura_trecho_m
    )

    altura_muro_m = entradas_muro["altura_muro_m"]
    braco_solo_ponta_m = (
        altura_muro_m - profundidade_inferior_m + braco_solo_no_trecho_m
        if empuxo_solo_kN_m > 0
        else 0.0
    )
    braco_sobrecarga_ponta_m = (
        altura_muro_m - profundidade_inferior_m + braco_sobrecarga_no_trecho_m
        if empuxo_sobrecarga_kN_m > 0
        else 0.0
    )
    braco_agua_ponta_m = (
        altura_muro_m - profundidade_inferior_m + braco_agua_no_trecho_m
        if empuxo_agua_kN_m > 0
        else 0.0
    )

    trecho = {
        "identificacao_trecho": identificacao_trecho,
        "profundidade_superior_m": profundidade_superior_m,
        "profundidade_inferior_m": profundidade_inferior_m,
        "altura_trecho_m": altura_trecho_m,
        "coeficiente_empuxo_ativo": coeficiente_empuxo_ativo,
        "peso_especifico_efetivo_kN_m3": peso_especifico_efetivo_kN_m3,
        "tensao_vertical_efetiva_superior_kPa": tensao_vertical_superior_kPa,
        "tensao_vertical_efetiva_inferior_kPa": tensao_vertical_inferior_kPa,
        "pressao_solo_bruta_superior_kPa": pressao_solo_bruta_superior_kPa,
        "pressao_solo_bruta_inferior_kPa": pressao_solo_bruta_inferior_kPa,
        "pressao_solo_superior_kPa": pressao_solo_superior_kPa,
        "pressao_solo_inferior_kPa": pressao_solo_inferior_kPa,
        "pressao_sobrecarga_kPa": pressao_sobrecarga_kPa,
        "pressao_agua_superior_kPa": pressao_agua_superior_kPa,
        "pressao_agua_inferior_kPa": pressao_agua_inferior_kPa,
        "empuxo_solo_kN_m": empuxo_solo_kN_m,
        "braco_empuxo_solo_ponta_m": braco_solo_ponta_m,
        "momento_empuxo_solo_ponta_kNm_m": empuxo_solo_kN_m * braco_solo_ponta_m,
        "empuxo_sobrecarga_kN_m": empuxo_sobrecarga_kN_m,
        "braco_empuxo_sobrecarga_ponta_m": braco_sobrecarga_ponta_m,
        "momento_empuxo_sobrecarga_ponta_kNm_m": (
            empuxo_sobrecarga_kN_m * braco_sobrecarga_ponta_m
        ),
        "empuxo_hidrostatico_kN_m": empuxo_agua_kN_m,
        "braco_empuxo_hidrostatico_ponta_m": braco_agua_ponta_m,
        "momento_empuxo_hidrostatico_ponta_kNm_m": empuxo_agua_kN_m * braco_agua_ponta_m,
    }
    return trecho, tensao_vertical_inferior_kPa


def _somar_empuxos(trechos: list[dict[str, Any]]) -> dict[str, float]:
    """Soma forças e momentos de solo, sobrecarga e água."""
    empuxo_solo_kN_m = sum(trecho["empuxo_solo_kN_m"] for trecho in trechos)
    empuxo_sobrecarga_kN_m = sum(trecho["empuxo_sobrecarga_kN_m"] for trecho in trechos)
    empuxo_agua_kN_m = sum(trecho["empuxo_hidrostatico_kN_m"] for trecho in trechos)
    momento_solo_kNm_m = sum(
        trecho["momento_empuxo_solo_ponta_kNm_m"] for trecho in trechos
    )
    momento_sobrecarga_kNm_m = sum(
        trecho["momento_empuxo_sobrecarga_ponta_kNm_m"] for trecho in trechos
    )
    momento_agua_kNm_m = sum(
        trecho["momento_empuxo_hidrostatico_ponta_kNm_m"] for trecho in trechos
    )

    return {
        "empuxo_solo_kN_m": empuxo_solo_kN_m,
        "braco_empuxo_solo_m": momento_solo_kNm_m / empuxo_solo_kN_m if empuxo_solo_kN_m else 0.0,
        "momento_solo_ponta_kNm_m": momento_solo_kNm_m,
        "empuxo_sobrecarga_kN_m": empuxo_sobrecarga_kN_m,
        "braco_sobrecarga_m": momento_sobrecarga_kNm_m / empuxo_sobrecarga_kN_m if empuxo_sobrecarga_kN_m else 0.0,
        "momento_sobrecarga_ponta_kNm_m": momento_sobrecarga_kNm_m,
        "empuxo_hidrostatico_kN_m": empuxo_agua_kN_m,
        "braco_hidrostatico_m": momento_agua_kNm_m / empuxo_agua_kN_m if empuxo_agua_kN_m else 0.0,
        "momento_hidrostatico_ponta_kNm_m": momento_agua_kNm_m,
    }


def _calcular_estabilidade(
    entradas_muro: dict[str, Any], empuxos: dict[str, float]
) -> tuple[dict[str, float], dict[str, Any]]:
    """Calcula peso do muro, fatores de segurança e tensões na base."""
    altura_muro_m = entradas_muro["altura_muro_m"]
    largura_base_m = entradas_muro["largura_base_m"]
    largura_topo_m = entradas_muro["largura_topo_m"]
    peso_especifico_concreto_kN_m3 = entradas_muro["peso_especifico_concreto_kN_m3"]
    atrito_solo_muro_graus = entradas_muro["atrito_solo_muro_graus"]
    metodo_empuxo = entradas_muro["metodo_empuxo"]

    empuxo_solo_kN_m = empuxos["empuxo_solo_kN_m"]
    empuxo_sobrecarga_kN_m = empuxos["empuxo_sobrecarga_kN_m"]
    empuxo_agua_kN_m = empuxos["empuxo_hidrostatico_kN_m"]
    momento_solo_kNm_m = empuxos["momento_solo_ponta_kNm_m"]
    momento_sobrecarga_kNm_m = empuxos["momento_sobrecarga_ponta_kNm_m"]
    momento_agua_kNm_m = empuxos["momento_hidrostatico_ponta_kNm_m"]

    componente_vertical_descendente_kN_m = (
        (empuxo_solo_kN_m + empuxo_sobrecarga_kN_m)
        * sin(radians(atrito_solo_muro_graus))
        if metodo_empuxo == "Coulomb"
        else 0.0
    )
    componente_horizontal_total_kN_m = (
        (empuxo_solo_kN_m + empuxo_sobrecarga_kN_m)
        * cos(radians(atrito_solo_muro_graus))
        + empuxo_agua_kN_m
    )
    momento_tombador_ponta_kNm_m = (
        (momento_solo_kNm_m + momento_sobrecarga_kNm_m)
        * cos(radians(atrito_solo_muro_graus))
        + momento_agua_kNm_m
    )

    largura_trecho_triangular_m = largura_base_m - largura_topo_m
    peso_trecho_triangular_kN_m = (
        0.5 * largura_trecho_triangular_m * altura_muro_m * peso_especifico_concreto_kN_m3
    )
    braco_trecho_triangular_m = 2.0 * largura_trecho_triangular_m / 3.0
    momento_trecho_triangular_kNm_m = (
        peso_trecho_triangular_kN_m * braco_trecho_triangular_m
    )
    peso_trecho_retangular_kN_m = (
        largura_topo_m * altura_muro_m * peso_especifico_concreto_kN_m3
    )
    braco_trecho_retangular_m = largura_base_m - largura_topo_m / 2.0
    momento_trecho_retangular_kNm_m = peso_trecho_retangular_kN_m * braco_trecho_retangular_m

    momento_vertical_empuxo_kNm_m = componente_vertical_descendente_kN_m * largura_base_m
    peso_muro_kN_m = peso_trecho_triangular_kN_m + peso_trecho_retangular_kN_m
    carga_vertical_total_kN_m = peso_muro_kN_m + componente_vertical_descendente_kN_m
    momento_estabilizador_total_kNm_m = (
        momento_trecho_triangular_kNm_m
        + momento_trecho_retangular_kNm_m
        + momento_vertical_empuxo_kNm_m
    )

    fator_seguranca_tombamento = (
        momento_estabilizador_total_kNm_m / momento_tombador_ponta_kNm_m
        if momento_tombador_ponta_kNm_m > 0
        else 0.0
    )
    fator_seguranca_deslizamento = (
        carga_vertical_total_kN_m
        * entradas_muro["coeficiente_atrito_base"]
        / componente_horizontal_total_kN_m
        if componente_horizontal_total_kN_m > 0
        else 0.0
    )
    posicao_resultante_desde_ponta_m = (
        (momento_estabilizador_total_kNm_m - momento_tombador_ponta_kNm_m)
        / carga_vertical_total_kN_m
        if carga_vertical_total_kN_m > 0
        else 0.0
    )
    excentricidade_resultante_m = largura_base_m / 2.0 - posicao_resultante_desde_ponta_m
    dados_base = _calcular_tensoes_base(
        largura_base_m,
        posicao_resultante_desde_ponta_m,
        excentricidade_resultante_m,
        carga_vertical_total_kN_m,
        entradas_muro["tensao_admissivel_fundacao_kPa"],
    )

    resumo = {
        **empuxos,
        "componente_horizontal_total_kN_m": componente_horizontal_total_kN_m,
        "componente_vertical_descendente_kN_m": componente_vertical_descendente_kN_m,
        "momento_tombador_ponta_kNm_m": momento_tombador_ponta_kNm_m,
        "peso_muro_kN_m": peso_muro_kN_m,
        "carga_vertical_total_kN_m": carga_vertical_total_kN_m,
        "momento_estabilizador_total_kNm_m": momento_estabilizador_total_kNm_m,
    }
    verificacoes = {
        "validade_entradas": "VÁLIDA",
        "fator_seguranca_tombamento": fator_seguranca_tombamento,
        "status_tombamento": (
            "ATENDE"
            if fator_seguranca_tombamento >= entradas_muro["fator_seguranca_minimo_tombamento"]
            else "REVER"
        ),
        "fator_seguranca_deslizamento": fator_seguranca_deslizamento,
        "status_deslizamento": (
            "ATENDE"
            if fator_seguranca_deslizamento >= entradas_muro["fator_seguranca_minimo_deslizamento"]
            else "REVER"
        ),
        "posicao_resultante_desde_ponta_m": posicao_resultante_desde_ponta_m,
        "excentricidade_resultante_m": excentricidade_resultante_m,
        **dados_base,
    }
    return resumo, verificacoes


def _calcular_tensoes_base(
    largura_base_m: float,
    posicao_resultante_desde_ponta_m: float,
    excentricidade_resultante_m: float,
    carga_vertical_total_kN_m: float,
    tensao_admissivel_fundacao_kPa: float,
) -> dict[str, Any]:
    """Define o regime de contato e as tensões transmitidas à fundação."""
    if not 0 <= posicao_resultante_desde_ponta_m <= largura_base_m:
        return {
            "regime_pressao_base": "FORA DA BASE",
            "tensao_maxima_base_kPa": None,
            "status_tensao_maxima_base": "BLOQUEADO",
            "tensao_minima_base_kPa": None,
            "fator_seguranca_tensao_admissivel": None,
        }

    if (
        posicao_resultante_desde_ponta_m < largura_base_m / 3.0
        or posicao_resultante_desde_ponta_m > 2.0 * largura_base_m / 3.0
    ):
        braco_ate_borda_m = min(
            posicao_resultante_desde_ponta_m,
            largura_base_m - posicao_resultante_desde_ponta_m,
        )
        tensao_maxima_base_kPa = 2.0 * carga_vertical_total_kN_m / (3.0 * braco_ate_borda_m)
        tensao_minima_base_kPa = 0.0
        regime_pressao_base = "TRIANGULAR"
    else:
        tensao_media_base_kPa = carga_vertical_total_kN_m / largura_base_m
        tensao_maxima_base_kPa = tensao_media_base_kPa * (
            1.0 + 6.0 * abs(excentricidade_resultante_m) / largura_base_m
        )
        tensao_minima_base_kPa = tensao_media_base_kPa * (
            1.0 - 6.0 * abs(excentricidade_resultante_m) / largura_base_m
        )
        regime_pressao_base = "TRAPEZOIDAL"

    return {
        "regime_pressao_base": regime_pressao_base,
        "tensao_maxima_base_kPa": tensao_maxima_base_kPa,
        "status_tensao_maxima_base": (
            "ATENDE" if tensao_maxima_base_kPa <= tensao_admissivel_fundacao_kPa else "REVER"
        ),
        "tensao_minima_base_kPa": tensao_minima_base_kPa,
        "fator_seguranca_tensao_admissivel": (
            tensao_admissivel_fundacao_kPa / tensao_maxima_base_kPa
        ),
    }


def _criar_diagramas_pressao(
    trechos: list[dict[str, Any]],
) -> dict[str, list[dict[str, float]]]:
    """Monta os pontos usados nos gráficos de pressão do aplicativo."""
    diagramas_pressao: dict[str, list[dict[str, float]]] = {
        "solo": [],
        "sobrecarga": [],
        "agua": [],
        "total": [],
    }
    for trecho in trechos:
        profundidade_superior_m = trecho["profundidade_superior_m"]
        profundidade_inferior_m = trecho["profundidade_inferior_m"]
        pontos_trecho = [(profundidade_superior_m, trecho["pressao_solo_superior_kPa"])]
        pressao_bruta_superior_kPa = trecho["pressao_solo_bruta_superior_kPa"]
        pressao_bruta_inferior_kPa = trecho["pressao_solo_bruta_inferior_kPa"]
        if pressao_bruta_superior_kPa < 0 < pressao_bruta_inferior_kPa:
            fracao_trecho = -pressao_bruta_superior_kPa / (
                pressao_bruta_inferior_kPa - pressao_bruta_superior_kPa
            )
            profundidade_pressao_nula_m = profundidade_superior_m + (
                trecho["altura_trecho_m"] * fracao_trecho
            )
            pontos_trecho.append((profundidade_pressao_nula_m, 0.0))
        pontos_trecho.append(
            (profundidade_inferior_m, trecho["pressao_solo_inferior_kPa"])
        )

        for profundidade_m, pressao_solo_kPa in pontos_trecho:
            fracao_trecho = (
                (profundidade_m - profundidade_superior_m) / trecho["altura_trecho_m"]
            )
            pressao_sobrecarga_kPa = trecho["pressao_sobrecarga_kPa"]
            pressao_agua_kPa = trecho["pressao_agua_superior_kPa"] + fracao_trecho * (
                trecho["pressao_agua_inferior_kPa"] - trecho["pressao_agua_superior_kPa"]
            )
            for nome_diagrama, pressao_kPa in (
                ("solo", pressao_solo_kPa),
                ("sobrecarga", pressao_sobrecarga_kPa),
                ("agua", pressao_agua_kPa),
                ("total", pressao_solo_kPa + pressao_sobrecarga_kPa + pressao_agua_kPa),
            ):
                diagramas_pressao[nome_diagrama].append(
                    {"profundidade_m": profundidade_m, "pressao_kPa": pressao_kPa}
                )

    return diagramas_pressao


def _criar_geometria_muro(entradas_muro: dict[str, Any]) -> list[dict[str, float]]:
    """Retorna os vértices da seção trapezoidal para o gráfico."""
    altura_muro_m = entradas_muro["altura_muro_m"]
    largura_base_m = entradas_muro["largura_base_m"]
    largura_topo_m = entradas_muro["largura_topo_m"]
    return [
        {"x_m": 0.0, "cota_y_m": 0.0},
        {"x_m": largura_base_m, "cota_y_m": 0.0},
        {"x_m": largura_base_m, "cota_y_m": altura_muro_m},
        {"x_m": largura_base_m - largura_topo_m, "cota_y_m": altura_muro_m},
        {"x_m": 0.0, "cota_y_m": 0.0},
    ]
