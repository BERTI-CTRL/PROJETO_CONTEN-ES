"""Método das fatias de Fellenius para a aba Talude da planilha de aula."""

from __future__ import annotations

import math
from typing import Any


INCREMENTOS_RAIOS_PADRAO_M = [0.0, 0.5, 1.5, 2.5, 3.5, 5.5, 7.5, 11.5, 15.5, 19.5]


def carregar_exemplo_talude() -> dict[str, Any]:
    """Carrega os dados do exemplo preenchido na aba Talude."""
    entradas = {
        "altura_talude_m": 8.0,
        "relacao_horizontal_vertical_face": 1.5,
        "inclinacao_terreno_montante_graus": 0.0,
        "distancia_crista_entrada_m": 3.0,
        "espessura_camada_superior_m": 3.0,
        "profundidade_nivel_agua_abaixo_crista_m": 7.8,
        "sobrecarga_crista_kPa": 0.0,
        "quantidade_fatias": 20,
        "peso_especifico_agua_kN_m3": 9.81,
        "distancia_pe_saida_m": 0.5,
        "limite_x_grafico_minimo_m": -4.0,
        "limite_x_grafico_maximo_m": 18.0,
        "peso_especifico_natural_camada_superior_kN_m3": 18.0,
        "peso_especifico_saturado_camada_superior_kN_m3": 20.0,
        "coesao_efetiva_camada_superior_kPa": 10.0,
        "angulo_atrito_efetivo_camada_superior_graus": 30.0,
        "peso_especifico_natural_camada_inferior_kN_m3": 19.0,
        "peso_especifico_saturado_camada_inferior_kN_m3": 21.0,
        "coesao_efetiva_camada_inferior_kPa": 5.0,
        "angulo_atrito_efetivo_camada_inferior_graus": 28.0,
    }
    geometria = _calcular_geometria_entrada(entradas)
    entradas["raios_candidatos_m"] = _gerar_raios_padrao(geometria)
    return entradas


def calcular_geometria_talude(entradas_talude: dict[str, Any]) -> dict[str, float | None]:
    """Retorna as cotas e distâncias da geometria adotada na planilha."""
    return _calcular_geometria_entrada(entradas_talude)


def gerar_raios_candidatos_padrao(entradas_talude: dict[str, Any]) -> list[float]:
    """Gera dez raios a partir de d/2, seguindo o espaçamento do exemplo."""
    geometria = _calcular_geometria_entrada(entradas_talude)
    return _gerar_raios_padrao(geometria)


def validar_entradas_talude(entradas_talude: dict[str, Any]) -> list[str]:
    erros: list[str] = []
    campos_numericos = (
        "altura_talude_m",
        "relacao_horizontal_vertical_face",
        "inclinacao_terreno_montante_graus",
        "distancia_crista_entrada_m",
        "espessura_camada_superior_m",
        "sobrecarga_crista_kPa",
        "quantidade_fatias",
        "peso_especifico_agua_kN_m3",
        "distancia_pe_saida_m",
        "limite_x_grafico_minimo_m",
        "limite_x_grafico_maximo_m",
        "peso_especifico_natural_camada_superior_kN_m3",
        "peso_especifico_saturado_camada_superior_kN_m3",
        "coesao_efetiva_camada_superior_kPa",
        "angulo_atrito_efetivo_camada_superior_graus",
        "peso_especifico_natural_camada_inferior_kN_m3",
        "peso_especifico_saturado_camada_inferior_kN_m3",
        "coesao_efetiva_camada_inferior_kPa",
        "angulo_atrito_efetivo_camada_inferior_graus",
    )
    for campo in campos_numericos:
        try:
            valor = float(entradas_talude[campo])
        except (KeyError, TypeError, ValueError, OverflowError):
            erros.append(f"Informe um valor numérico para {campo.replace('_', ' ')}.")
            continue
        if not math.isfinite(valor):
            erros.append(f"O valor de {campo.replace('_', ' ')} precisa ser finito.")

    profundidade_nivel_agua_m = entradas_talude.get(
        "profundidade_nivel_agua_abaixo_crista_m"
    )
    if profundidade_nivel_agua_m is not None:
        try:
            profundidade_nivel_agua_m = float(profundidade_nivel_agua_m)
        except (TypeError, ValueError, OverflowError):
            erros.append("A profundidade do N.A. precisa ser um número ou ficar vazia.")
        else:
            if not math.isfinite(profundidade_nivel_agua_m):
                erros.append("A profundidade do N.A. precisa ser finita.")
            elif profundidade_nivel_agua_m < 0:
                erros.append("A profundidade do N.A. abaixo da crista não pode ser negativa.")

    raios_candidatos = entradas_talude.get("raios_candidatos_m")
    if not isinstance(raios_candidatos, list) or len(raios_candidatos) != 10:
        erros.append("Informe dez raios candidatos para comparar as superfícies circulares.")
    else:
        for indice_raio, raio_m in enumerate(raios_candidatos, start=1):
            try:
                raio_numero = float(raio_m)
            except (TypeError, ValueError, OverflowError):
                erros.append(f"O raio R{indice_raio:02d} precisa ser numérico.")
                continue
            if not math.isfinite(raio_numero) or raio_numero <= 0:
                erros.append(f"O raio R{indice_raio:02d} precisa ser positivo e finito.")

    if erros:
        return erros

    altura_talude_m = float(entradas_talude["altura_talude_m"])
    relacao_horizontal_vertical_face = float(
        entradas_talude["relacao_horizontal_vertical_face"]
    )
    inclinacao_montante_graus = float(
        entradas_talude["inclinacao_terreno_montante_graus"]
    )
    profundidade_camada_superior_m = float(entradas_talude["espessura_camada_superior_m"])

    if altura_talude_m <= 0:
        erros.append("A altura do talude precisa ser maior que zero.")
    if relacao_horizontal_vertical_face <= 0:
        erros.append("A relação horizontal/vertical da face precisa ser maior que zero.")
    if not -45 <= inclinacao_montante_graus <= 45:
        erros.append("A inclinação do terreno a montante deve ficar entre −45° e 45°.")
    if (
        relacao_horizontal_vertical_face > 0
        and float(entradas_talude["distancia_crista_entrada_m"])
        < -relacao_horizontal_vertical_face * altura_talude_m
    ):
        erros.append("O ponto de entrada não pode ficar abaixo do pé do talude.")
    if altura_talude_m > 0 and relacao_horizontal_vertical_face > 0:
        coordenada_x_entrada_m = (
            relacao_horizontal_vertical_face * altura_talude_m
            + float(entradas_talude["distancia_crista_entrada_m"])
        )
        distancia_pe_saida_m = float(entradas_talude["distancia_pe_saida_m"])
        if coordenada_x_entrada_m >= 0 and distancia_pe_saida_m >= 0:
            cota_entrada_m = _cota_terreno(coordenada_x_entrada_m, entradas_talude)
            if math.hypot(coordenada_x_entrada_m + distancia_pe_saida_m, cota_entrada_m) <= 1e-9:
                erros.append("Os pontos de entrada e saída precisam ser diferentes.")
    if not 0 < profundidade_camada_superior_m < altura_talude_m:
        erros.append("A camada superior precisa ter espessura maior que zero e menor que H.")
    if float(entradas_talude["sobrecarga_crista_kPa"]) < 0:
        erros.append("A sobrecarga uniforme não pode ser negativa.")
    if not 4 <= int(float(entradas_talude["quantidade_fatias"])) <= 50:
        erros.append("Use entre 4 e 50 fatias, como permite a planilha.")
    if float(entradas_talude["quantidade_fatias"]) != int(
        float(entradas_talude["quantidade_fatias"])
    ):
        erros.append("A quantidade de fatias precisa ser um número inteiro.")
    if float(entradas_talude["peso_especifico_agua_kN_m3"]) <= 0:
        erros.append("O peso específico da água precisa ser maior que zero.")
    if float(entradas_talude["distancia_pe_saida_m"]) < 0:
        erros.append("A distância do pé à saída não pode ser negativa.")
    if float(entradas_talude["limite_x_grafico_minimo_m"]) >= float(
        entradas_talude["limite_x_grafico_maximo_m"]
    ):
        erros.append("O limite mínimo de x do gráfico precisa ser menor que o máximo.")

    for nome_camada, sufixo_camada in (("superior", "superior"), ("inferior", "inferior")):
        peso_natural = float(
            entradas_talude[f"peso_especifico_natural_camada_{sufixo_camada}_kN_m3"]
        )
        peso_saturado = float(
            entradas_talude[f"peso_especifico_saturado_camada_{sufixo_camada}_kN_m3"]
        )
        coesao_efetiva = float(
            entradas_talude[f"coesao_efetiva_camada_{sufixo_camada}_kPa"]
        )
        angulo_atrito = float(
            entradas_talude[f"angulo_atrito_efetivo_camada_{sufixo_camada}_graus"]
        )
        if peso_natural <= 0 or peso_saturado <= 0:
            erros.append(f"Os pesos específicos da camada {nome_camada} precisam ser positivos.")
        if peso_saturado < peso_natural:
            erros.append(f"O peso saturado da camada {nome_camada} não pode ser menor que o natural.")
        if coesao_efetiva < 0:
            erros.append(f"A coesão da camada {nome_camada} não pode ser negativa.")
        if not 0 <= angulo_atrito < 90:
            erros.append(f"O ângulo de atrito da camada {nome_camada} deve ficar entre 0° e 90°.")
    return erros


def calcular_estabilidade_talude(entradas_talude: dict[str, Any]) -> dict[str, Any]:
    """Avalia os dez círculos candidatos pelo método de Fellenius."""
    erros = validar_entradas_talude(entradas_talude)
    if erros:
        raise ValueError(" ".join(erros))

    geometria = _calcular_geometria_entrada(entradas_talude)
    circulos = []
    for indice_raio, raio_m in enumerate(entradas_talude["raios_candidatos_m"], start=1):
        circulos.append(
            _calcular_circulo(
                entradas_talude,
                geometria,
                float(raio_m),
                f"R{indice_raio:02d}",
            )
        )

    circulos_validos = [circulo for circulo in circulos if circulo["situacao"] == "VÁLIDO"]
    circulo_critico = (
        min(circulos_validos, key=lambda circulo: circulo["fator_seguranca"])
        if circulos_validos
        else None
    )
    return {
        "geometria": geometria,
        "perfil_terreno": _criar_perfil_para_grafico(entradas_talude),
        "circulos": circulos,
        "circulo_critico": circulo_critico,
        "resumo": {
            "quantidade_circulos_validos": len(circulos_validos),
            "fator_seguranca_critico": (
                circulo_critico["fator_seguranca"] if circulo_critico else None
            ),
            "resistencia_total_kN_m": (
                circulo_critico["resistencia_total_kN_m"] if circulo_critico else None
            ),
            "forca_mobilizada_total_kN_m": (
                circulo_critico["forca_mobilizada_total_kN_m"] if circulo_critico else None
            ),
        },
    }


def _calcular_geometria_entrada(entradas_talude: dict[str, Any]) -> dict[str, float | None]:
    altura_talude_m = float(entradas_talude["altura_talude_m"])
    relacao_horizontal_vertical_face = float(
        entradas_talude["relacao_horizontal_vertical_face"]
    )
    comprimento_horizontal_face_m = altura_talude_m * relacao_horizontal_vertical_face
    distancia_crista_entrada_m = float(entradas_talude["distancia_crista_entrada_m"])
    coordenada_x_entrada_m = comprimento_horizontal_face_m + distancia_crista_entrada_m
    cota_entrada_m = _cota_terreno(coordenada_x_entrada_m, entradas_talude)
    distancia_pe_saida_m = float(entradas_talude["distancia_pe_saida_m"])
    distancia_entre_entrada_e_saida_m = math.hypot(
        coordenada_x_entrada_m + distancia_pe_saida_m, cota_entrada_m
    )
    profundidade_nivel_agua_m = entradas_talude.get(
        "profundidade_nivel_agua_abaixo_crista_m"
    )
    cota_nivel_agua_m = (
        None
        if profundidade_nivel_agua_m is None
        else altura_talude_m - float(profundidade_nivel_agua_m)
    )
    return {
        "comprimento_horizontal_face_m": comprimento_horizontal_face_m,
        "inclinacao_face_graus": math.degrees(
            math.atan(1 / relacao_horizontal_vertical_face)
        ),
        "coordenada_x_entrada_m": coordenada_x_entrada_m,
        "cota_entrada_m": cota_entrada_m,
        "distancia_entre_entrada_e_saida_m": distancia_entre_entrada_e_saida_m,
        "cota_interface_camadas_m": altura_talude_m
        - float(entradas_talude["espessura_camada_superior_m"]),
        "cota_nivel_agua_m": cota_nivel_agua_m,
    }


def _gerar_raios_padrao(geometria: dict[str, Any]) -> list[float]:
    raio_minimo_m = geometria["distancia_entre_entrada_e_saida_m"] / 2
    return [raio_minimo_m + incremento for incremento in INCREMENTOS_RAIOS_PADRAO_M]


def _cota_terreno(x_m: float, entradas_talude: dict[str, Any]) -> float:
    if x_m <= 0:
        return 0.0
    comprimento_horizontal_face_m = (
        float(entradas_talude["altura_talude_m"])
        * float(entradas_talude["relacao_horizontal_vertical_face"])
    )
    if x_m <= comprimento_horizontal_face_m:
        return x_m / float(entradas_talude["relacao_horizontal_vertical_face"])
    altura_talude_m = float(entradas_talude["altura_talude_m"])
    inclinacao_montante_rad = math.radians(
        float(entradas_talude["inclinacao_terreno_montante_graus"])
    )
    return altura_talude_m + (x_m - comprimento_horizontal_face_m) * math.tan(
        inclinacao_montante_rad
    )


def _calcular_circulo(
    entradas_talude: dict[str, Any],
    geometria: dict[str, Any],
    raio_m: float,
    identificacao_circulo: str,
) -> dict[str, Any]:
    distancia_entrada_saida_m = geometria["distancia_entre_entrada_e_saida_m"]
    if raio_m < distancia_entrada_saida_m / 2:
        return {
            "identificacao": identificacao_circulo,
            "raio_m": raio_m,
            "x_saida_m": -float(entradas_talude["distancia_pe_saida_m"]),
            "x_entrada_m": geometria["coordenada_x_entrada_m"],
            "centro_x_m": None,
            "centro_y_m": None,
            "fator_seguranca": None,
            "resistencia_total_kN_m": None,
            "forca_mobilizada_total_kN_m": None,
            "situacao": "RAIO < d/2",
            "fatias": [],
        }

    altura_centro_m = math.sqrt(
        raio_m**2 - (distancia_entrada_saida_m / 2) ** 2
    )
    coordenada_x_entrada_m = geometria["coordenada_x_entrada_m"]
    cota_entrada_m = geometria["cota_entrada_m"]
    distancia_pe_saida_m = float(entradas_talude["distancia_pe_saida_m"])
    centro_x_m = (coordenada_x_entrada_m - distancia_pe_saida_m) / 2 - (
        cota_entrada_m / distancia_entrada_saida_m
    ) * altura_centro_m
    centro_y_m = cota_entrada_m / 2 + (
        (coordenada_x_entrada_m + distancia_pe_saida_m) / distancia_entrada_saida_m
    ) * altura_centro_m
    fatias = _criar_fatias(entradas_talude, geometria, centro_x_m, centro_y_m, raio_m)

    situacoes_fatias = {fatia["situacao"] for fatia in fatias}
    resistencia_total_kN_m = sum(
        fatia["forca_resistente_kN_m"] or 0.0 for fatia in fatias
    )
    forca_mobilizada_total_kN_m = sum(
        fatia["forca_mobilizada_kN_m"] for fatia in fatias
    )
    if "FORA DO MACIÇO" in situacoes_fatias:
        situacao = "FORA DO MACIÇO"
    elif "N EFETIVA NEGATIVA" in situacoes_fatias:
        situacao = "N′ < 0"
    elif forca_mobilizada_total_kN_m <= 0.001:
        situacao = "Fmob ≤ 0"
    elif len(fatias) != int(entradas_talude["quantidade_fatias"]):
        situacao = "REVER FATIAS"
    else:
        situacao = "VÁLIDO"

    fator_seguranca = (
        resistencia_total_kN_m / forca_mobilizada_total_kN_m
        if situacao == "VÁLIDO"
        else None
    )
    return {
        "identificacao": identificacao_circulo,
        "raio_m": raio_m,
        "x_saida_m": -distancia_pe_saida_m,
        "x_entrada_m": coordenada_x_entrada_m,
        "centro_x_m": centro_x_m,
        "centro_y_m": centro_y_m,
        "fator_seguranca": fator_seguranca,
        "resistencia_total_kN_m": resistencia_total_kN_m,
        "forca_mobilizada_total_kN_m": forca_mobilizada_total_kN_m,
        "situacao": situacao,
        "fatias": fatias,
    }


def _criar_fatias(
    entradas_talude: dict[str, Any],
    geometria: dict[str, Any],
    centro_x_m: float,
    centro_y_m: float,
    raio_m: float,
) -> list[dict[str, Any]]:
    quantidade_fatias = int(entradas_talude["quantidade_fatias"])
    distancia_pe_saida_m = float(entradas_talude["distancia_pe_saida_m"])
    coordenada_x_entrada_m = geometria["coordenada_x_entrada_m"]
    largura_total_m = coordenada_x_entrada_m + distancia_pe_saida_m
    passo_horizontal_m = largura_total_m / quantidade_fatias
    fatias = []

    for indice_fatia in range(quantidade_fatias):
        x_inicial_m = -distancia_pe_saida_m + indice_fatia * passo_horizontal_m
        x_final_m = x_inicial_m + passo_horizontal_m
        x_medio_m = (x_inicial_m + x_final_m) / 2
        cota_topo_inicial_m = _cota_terreno(x_inicial_m, entradas_talude)
        cota_topo_final_m = _cota_terreno(x_final_m, entradas_talude)
        cota_topo_media_m = _cota_terreno(x_medio_m, entradas_talude)
        cota_base_inicial_m = _cota_base_circular(centro_x_m, centro_y_m, raio_m, x_inicial_m)
        cota_base_final_m = _cota_base_circular(centro_x_m, centro_y_m, raio_m, x_final_m)
        cota_base_media_m = _cota_base_circular(centro_x_m, centro_y_m, raio_m, x_medio_m)
        if cota_base_inicial_m is None or cota_base_final_m is None or cota_base_media_m is None:
            fatias.append(_fatia_fora(indice_fatia + 1, x_inicial_m, x_final_m))
            continue

        angulo_inicial_graus = _angulo_raio_graus(x_inicial_m, centro_x_m, raio_m)
        angulo_final_graus = _angulo_raio_graus(x_final_m, centro_x_m, raio_m)
        variacao_angular_rad = abs(math.radians(angulo_final_graus - angulo_inicial_graus))
        comprimento_arco_m = raio_m * variacao_angular_rad
        angulo_medio_graus = (angulo_inicial_graus + angulo_final_graus) / 2
        angulo_medio_rad = math.radians(angulo_medio_graus)
        profundidade_media_m = cota_topo_media_m - cota_base_media_m

        if profundidade_media_m <= 0:
            fatias.append(
                _fatia_fora(
                    indice_fatia + 1,
                    x_inicial_m,
                    x_final_m,
                    cota_topo_media_m,
                    cota_base_media_m,
                    angulo_inicial_graus,
                    angulo_final_graus,
                    variacao_angular_rad,
                    comprimento_arco_m,
                    angulo_medio_graus,
                )
            )
            continue

        areas = _calcular_areas_fatia(
            entradas_talude,
            geometria,
            x_final_m - x_inicial_m,
            cota_topo_inicial_m,
            cota_topo_final_m,
            cota_base_inicial_m,
            cota_base_final_m,
        )
        sobrecarga_fatia_kN_m = float(entradas_talude["sobrecarga_crista_kPa"]) * max(
            0.0,
            min(x_final_m, coordenada_x_entrada_m)
            - max(x_inicial_m, geometria["comprimento_horizontal_face_m"]),
        )
        peso_fatia_kN_m = (
            areas["area_camada_superior_nao_saturada_m2"]
            * float(entradas_talude["peso_especifico_natural_camada_superior_kN_m3"])
            + areas["area_camada_superior_saturada_m2"]
            * float(entradas_talude["peso_especifico_saturado_camada_superior_kN_m3"])
            + areas["area_camada_inferior_nao_saturada_m2"]
            * float(entradas_talude["peso_especifico_natural_camada_inferior_kN_m3"])
            + areas["area_camada_inferior_saturada_m2"]
            * float(entradas_talude["peso_especifico_saturado_camada_inferior_kN_m3"])
            + sobrecarga_fatia_kN_m
        )
        profundidade_nivel_agua_m = entradas_talude.get(
            "profundidade_nivel_agua_abaixo_crista_m"
        )
        if profundidade_nivel_agua_m is None:
            pressao_neutra_kPa = 0.0
        else:
            pressao_neutra_kPa = float(entradas_talude["peso_especifico_agua_kN_m3"]) * max(
                0.0, float(geometria["cota_nivel_agua_m"]) - cota_base_media_m
            )

        comprimento_camada_inferior_m = _comprimento_arco_camada_inferior(
            centro_x_m,
            centro_y_m,
            raio_m,
            x_inicial_m,
            x_final_m,
            geometria["cota_interface_camadas_m"],
        )
        comprimento_camada_superior_m = max(
            0.0, comprimento_arco_m - comprimento_camada_inferior_m
        )
        forca_normal_efetiva_kN_m = (
            peso_fatia_kN_m * math.cos(angulo_medio_rad)
            - pressao_neutra_kPa * comprimento_arco_m
        )
        if forca_normal_efetiva_kN_m < 0:
            situacao_fatia = "N EFETIVA NEGATIVA"
            forca_resistente_kN_m = None
        else:
            situacao_fatia = "OK"
            fracao_camada_superior = comprimento_camada_superior_m / comprimento_arco_m
            fracao_camada_inferior = comprimento_camada_inferior_m / comprimento_arco_m
            resistencia_atrito = forca_normal_efetiva_kN_m * (
                fracao_camada_superior
                * math.tan(
                    math.radians(
                        float(entradas_talude["angulo_atrito_efetivo_camada_superior_graus"])
                    )
                )
                + fracao_camada_inferior
                * math.tan(
                    math.radians(
                        float(entradas_talude["angulo_atrito_efetivo_camada_inferior_graus"])
                    )
                )
            )
            forca_resistente_kN_m = (
                float(entradas_talude["coesao_efetiva_camada_superior_kPa"])
                * comprimento_camada_superior_m
                + float(entradas_talude["coesao_efetiva_camada_inferior_kPa"])
                * comprimento_camada_inferior_m
                + resistencia_atrito
            )

        fatias.append(
            {
                "numero_fatia": indice_fatia + 1,
                "x_inicial_m": x_inicial_m,
                "x_final_m": x_final_m,
                "x_medio_m": x_medio_m,
                "cota_topo_m": cota_topo_media_m,
                "cota_base_m": cota_base_media_m,
                "angulo_base_inicial_graus": angulo_inicial_graus,
                "angulo_base_final_graus": angulo_final_graus,
                "variacao_angular_rad": variacao_angular_rad,
                "comprimento_arco_m": comprimento_arco_m,
                "angulo_base_medio_graus": angulo_medio_graus,
                "comprimento_camada_superior_m": comprimento_camada_superior_m,
                "comprimento_camada_inferior_m": comprimento_camada_inferior_m,
                **areas,
                "peso_fatia_kN_m": peso_fatia_kN_m,
                "pressao_neutra_kPa": pressao_neutra_kPa,
                "forca_normal_efetiva_kN_m": forca_normal_efetiva_kN_m,
                "forca_resistente_kN_m": forca_resistente_kN_m,
                "forca_mobilizada_kN_m": peso_fatia_kN_m * math.sin(angulo_medio_rad),
                "situacao": situacao_fatia,
            }
        )
    return fatias


def _criar_perfil_para_grafico(entradas_talude: dict[str, Any]) -> list[dict[str, float]]:
    x_minimo_m = float(entradas_talude["limite_x_grafico_minimo_m"])
    x_maximo_m = float(entradas_talude["limite_x_grafico_maximo_m"])
    comprimento_horizontal_face_m = (
        float(entradas_talude["altura_talude_m"])
        * float(entradas_talude["relacao_horizontal_vertical_face"])
    )
    coordenadas_x = sorted(
        {
            x_minimo_m,
            x_maximo_m,
            0.0,
            comprimento_horizontal_face_m,
        }
    )
    return [
        {"x_m": x_m, "cota_y_m": _cota_terreno(x_m, entradas_talude)}
        for x_m in coordenadas_x
    ]


def _cota_base_circular(
    centro_x_m: float, centro_y_m: float, raio_m: float, x_m: float
) -> float | None:
    radicando = raio_m**2 - (x_m - centro_x_m) ** 2
    if radicando < -1e-8:
        return None
    return centro_y_m - math.sqrt(max(0.0, radicando))


def _angulo_raio_graus(x_m: float, centro_x_m: float, raio_m: float) -> float:
    seno_angulo = max(-1.0, min(1.0, (x_m - centro_x_m) / raio_m))
    return math.degrees(math.asin(seno_angulo))


def _comprimento_arco_camada_inferior(
    centro_x_m: float,
    centro_y_m: float,
    raio_m: float,
    x_inicial_m: float,
    x_final_m: float,
    cota_interface_m: float,
) -> float:
    distancia_centro_interface_m = centro_y_m - cota_interface_m
    if distancia_centro_interface_m < 0:
        return raio_m * abs(
            math.radians(
                _angulo_raio_graus(x_final_m, centro_x_m, raio_m)
                - _angulo_raio_graus(x_inicial_m, centro_x_m, raio_m)
            )
        )
    if distancia_centro_interface_m >= raio_m:
        return 0.0

    metade_largura_interface_m = math.sqrt(
        raio_m**2 - distancia_centro_interface_m**2
    )
    x_inferior_m = max(x_inicial_m, centro_x_m - metade_largura_interface_m)
    x_superior_m = min(x_final_m, centro_x_m + metade_largura_interface_m)
    if x_superior_m <= x_inferior_m:
        return 0.0
    variacao_angular_rad = math.asin(
        (x_superior_m - centro_x_m) / raio_m
    ) - math.asin((x_inferior_m - centro_x_m) / raio_m)
    return raio_m * variacao_angular_rad


def _calcular_areas_fatia(
    entradas_talude: dict[str, Any],
    geometria: dict[str, Any],
    largura_fatia_m: float,
    cota_topo_inicial_m: float,
    cota_topo_final_m: float,
    cota_base_inicial_m: float,
    cota_base_final_m: float,
) -> dict[str, float]:
    cota_interface_m = geometria["cota_interface_camadas_m"]
    cota_nivel_agua_m = geometria["cota_nivel_agua_m"]
    limite_agua_para_area_m = (
        -math.inf if cota_nivel_agua_m is None else cota_nivel_agua_m
    )

    def calcular_areas_na_borda(
        cota_topo_m: float, cota_base_m: float
    ) -> tuple[float, float, float, float]:
        espessura_superior_total_m = max(
            0.0, cota_topo_m - max(cota_base_m, cota_interface_m)
        )
        espessura_superior_nao_saturada_m = max(
            0.0,
            cota_topo_m
            - max(cota_base_m, cota_interface_m, limite_agua_para_area_m),
        )
        espessura_inferior_total_m = max(
            0.0, min(cota_topo_m, cota_interface_m) - cota_base_m
        )
        espessura_inferior_nao_saturada_m = max(
            0.0,
            min(cota_topo_m, cota_interface_m)
            - max(cota_base_m, limite_agua_para_area_m),
        )
        return (
            espessura_superior_nao_saturada_m,
            max(0.0, espessura_superior_total_m - espessura_superior_nao_saturada_m),
            espessura_inferior_nao_saturada_m,
            max(0.0, espessura_inferior_total_m - espessura_inferior_nao_saturada_m),
        )

    areas_borda_inicial = calcular_areas_na_borda(
        cota_topo_inicial_m, cota_base_inicial_m
    )
    areas_borda_final = calcular_areas_na_borda(cota_topo_final_m, cota_base_final_m)
    fator_area_trapezio = largura_fatia_m / 2

    return {
        "area_camada_superior_nao_saturada_m2": fator_area_trapezio
        * (areas_borda_inicial[0] + areas_borda_final[0]),
        "area_camada_superior_saturada_m2": fator_area_trapezio
        * (areas_borda_inicial[1] + areas_borda_final[1]),
        "area_camada_inferior_nao_saturada_m2": fator_area_trapezio
        * (areas_borda_inicial[2] + areas_borda_final[2]),
        "area_camada_inferior_saturada_m2": fator_area_trapezio
        * (areas_borda_inicial[3] + areas_borda_final[3]),
    }


def _fatia_fora(
    numero_fatia: int,
    x_inicial_m: float,
    x_final_m: float,
    cota_topo_m: float | None = None,
    cota_base_m: float | None = None,
    angulo_inicial_graus: float | None = None,
    angulo_final_graus: float | None = None,
    variacao_angular_rad: float = 0.0,
    comprimento_arco_m: float = 0.0,
    angulo_medio_graus: float | None = None,
) -> dict[str, Any]:
    return {
        "numero_fatia": numero_fatia,
        "x_inicial_m": x_inicial_m,
        "x_final_m": x_final_m,
        "x_medio_m": (x_inicial_m + x_final_m) / 2,
        "cota_topo_m": cota_topo_m,
        "cota_base_m": cota_base_m,
        "angulo_base_inicial_graus": angulo_inicial_graus,
        "angulo_base_final_graus": angulo_final_graus,
        "variacao_angular_rad": variacao_angular_rad,
        "comprimento_arco_m": comprimento_arco_m,
        "angulo_base_medio_graus": angulo_medio_graus,
        "comprimento_camada_superior_m": 0.0,
        "comprimento_camada_inferior_m": 0.0,
        "area_camada_superior_nao_saturada_m2": 0.0,
        "area_camada_superior_saturada_m2": 0.0,
        "area_camada_inferior_nao_saturada_m2": 0.0,
        "area_camada_inferior_saturada_m2": 0.0,
        "peso_fatia_kN_m": 0.0,
        "pressao_neutra_kPa": 0.0,
        "forca_normal_efetiva_kN_m": None,
        "forca_resistente_kN_m": None,
        "forca_mobilizada_kN_m": 0.0,
        "situacao": "FORA DO MACIÇO",
    }
