"""Exporta a seção do muro, diagramas de pressão e resumo para DXF."""

from __future__ import annotations

from io import StringIO
from math import tan, radians
from typing import Any

import ezdxf


def gerar_desenho_muro_dxf(
    entradas_muro: dict[str, Any],
    camadas_solo: list[dict[str, Any]],
    resultado_muro: dict[str, Any],
) -> bytes:
    """Gera um desenho em metros usando os resultados já calculados pelo aplicativo."""
    documento = ezdxf.new("R2010", setup=True, units=6)
    espaco_modelo = documento.modelspace()
    _criar_camadas(documento, camadas_solo)

    _desenhar_secao_muro(espaco_modelo, entradas_muro, camadas_solo, resultado_muro)
    coordenadas_diagrama_pressao = _desenhar_diagrama_pressao(
        espaco_modelo, entradas_muro, resultado_muro
    )
    _desenhar_diagrama_pressao_base(
        espaco_modelo, entradas_muro, resultado_muro, coordenadas_diagrama_pressao
    )
    _desenhar_cotas(espaco_modelo, entradas_muro)
    _adicionar_resumo(espaco_modelo, entradas_muro, camadas_solo, resultado_muro)

    arquivo_texto = StringIO()
    documento.write(arquivo_texto)
    return documento.encode(arquivo_texto.getvalue())


def _criar_camadas(
    documento: ezdxf.document.Drawing, camadas_solo: list[dict[str, Any]]
) -> None:
    camadas_desenho = {
        "MURO": (8, "CONTINUOUS"),
        "ATERRO": (3, "CONTINUOUS"),
        "INTERFACES_SOLO": (30, "DASHED"),
        "NIVEL_AGUA": (5, "DASHDOT"),
        "EIXOS_DIAGRAMAS": (7, "CONTINUOUS"),
        "PRESSAO_SOLO": (3, "CONTINUOUS"),
        "PRESSAO_SOBRECARGA": (2, "DASHED"),
        "PRESSAO_AGUA": (5, "DASHDOT"),
        "PRESSAO_TOTAL": (1, "CONTINUOUS"),
        "PRESSAO_BASE": (6, "CONTINUOUS"),
        "COTAS": (2, "CONTINUOUS"),
        "RESUMO": (7, "CONTINUOUS"),
    }
    for nome_camada, (cor, tipo_linha) in camadas_desenho.items():
        documento.layers.new(nome_camada, dxfattribs={"color": cor, "linetype": tipo_linha})
    cores_solo_natural = (30, 50, 94, 130, 170, 210)
    cores_solo_saturado = (151, 152, 153, 154, 155, 156)
    for indice_camada, camada_solo in enumerate(camadas_solo, start=1):
        if float(camada_solo["espessura_m"]) <= 0:
            continue
        indice_cor = (indice_camada - 1) % len(cores_solo_natural)
        documento.layers.new(
            f"SOLO_CAMADA_{indice_camada:02d}_NATURAL",
            dxfattribs={"color": cores_solo_natural[indice_cor]},
        )
        documento.layers.new(
            f"SOLO_CAMADA_{indice_camada:02d}_SATURADA",
            dxfattribs={"color": cores_solo_saturado[indice_cor]},
        )


def _desenhar_secao_muro(
    espaco_modelo: Any,
    entradas_muro: dict[str, Any],
    camadas_solo: list[dict[str, Any]],
    resultado_muro: dict[str, Any],
) -> None:
    altura_muro_m = float(entradas_muro["altura_muro_m"])
    largura_base_m = float(entradas_muro["largura_base_m"])
    largura_topo_m = float(entradas_muro["largura_topo_m"])
    x_tardoz_topo_m = largura_base_m - largura_topo_m
    extensao_aterro_m = max(2.0, altura_muro_m * 0.6)
    x_limite_aterro_m = x_tardoz_topo_m - extensao_aterro_m
    inclinacao_aterro_rad = radians(float(entradas_muro["inclinacao_aterro_graus"]))
    cota_aterro_limite_m = altura_muro_m + (
        x_tardoz_topo_m - x_limite_aterro_m
    ) * tan(inclinacao_aterro_rad)
    profundidade_nivel_agua_m = entradas_muro.get("profundidade_nivel_agua_m")
    _hachurar_camadas_solo(
        espaco_modelo,
        camadas_solo,
        altura_muro_m,
        x_limite_aterro_m,
        x_tardoz_topo_m,
        cota_aterro_limite_m,
        profundidade_nivel_agua_m,
    )
    espaco_modelo.add_line(
        (x_limite_aterro_m, cota_aterro_limite_m),
        (x_tardoz_topo_m, altura_muro_m),
        dxfattribs={"layer": "ATERRO"},
    )
    _adicionar_texto(
        espaco_modelo,
        "SUPERFICIE DO ATERRO",
        (x_limite_aterro_m, cota_aterro_limite_m + 0.15),
        max(0.16, altura_muro_m * 0.025),
        "ATERRO",
    )

    profundidade_acumulada_m = 0.0
    for indice_camada, camada_solo in enumerate(camadas_solo, start=1):
        espessura_camada_m = float(camada_solo["espessura_m"])
        if espessura_camada_m <= 0:
            continue
        cota_meio_camada_m = altura_muro_m - profundidade_acumulada_m - espessura_camada_m / 2
        _adicionar_texto(
            espaco_modelo,
            f"CAMADA {indice_camada}",
            (x_limite_aterro_m + 0.15, cota_meio_camada_m),
            max(0.16, altura_muro_m * 0.025),
            "INTERFACES_SOLO",
        )
        profundidade_acumulada_m += espessura_camada_m
        if profundidade_acumulada_m >= altura_muro_m - 1e-9:
            continue
        cota_interface_m = altura_muro_m - profundidade_acumulada_m
        x_tardoz_interface_m = x_tardoz_topo_m * cota_interface_m / altura_muro_m
        espaco_modelo.add_line(
            (x_limite_aterro_m, cota_interface_m),
            (x_tardoz_interface_m, cota_interface_m),
            dxfattribs={"layer": "INTERFACES_SOLO"},
        )

    if profundidade_nivel_agua_m is not None:
        cota_nivel_agua_m = altura_muro_m - float(profundidade_nivel_agua_m)
        x_tardoz_nivel_agua_m = x_tardoz_topo_m * cota_nivel_agua_m / altura_muro_m
        espaco_modelo.add_line(
            (x_limite_aterro_m, cota_nivel_agua_m),
            (x_tardoz_nivel_agua_m, cota_nivel_agua_m),
            dxfattribs={"layer": "NIVEL_AGUA"},
        )
        _adicionar_texto(
            espaco_modelo,
            "N.A.",
            (x_limite_aterro_m + 0.15, cota_nivel_agua_m + 0.12),
            max(0.17, altura_muro_m * 0.028),
            "NIVEL_AGUA",
        )

    _adicionar_texto(
        espaco_modelo,
        "CONCRETO",
        (largura_base_m - largura_topo_m * 0.75, altura_muro_m * 0.48),
        max(0.17, altura_muro_m * 0.03),
        "MURO",
    )
    vertices_muro = [
        (ponto["x_m"], ponto["cota_y_m"])
        for ponto in resultado_muro["geometria_muro"][:-1]
    ]
    espaco_modelo.add_lwpolyline(
        vertices_muro, close=True, dxfattribs={"layer": "MURO"}
    )


def _hachurar_camadas_solo(
    espaco_modelo: Any,
    camadas_solo: list[dict[str, Any]],
    altura_muro_m: float,
    x_limite_aterro_m: float,
    x_tardoz_topo_m: float,
    cota_aterro_limite_m: float,
    profundidade_nivel_agua_m: float | None,
) -> None:
    """Preenche cada estrato e separa visualmente as zonas acima/abaixo do N.A."""
    profundidade_acumulada_m = 0.0
    for indice_camada, camada_solo in enumerate(camadas_solo, start=1):
        espessura_m = float(camada_solo["espessura_m"])
        if espessura_m <= 0:
            continue
        profundidade_superior_m = profundidade_acumulada_m
        profundidade_inferior_m = min(
            altura_muro_m, profundidade_superior_m + espessura_m
        )
        profundidade_acumulada_m += espessura_m
        if profundidade_superior_m >= altura_muro_m:
            continue

        cortes = [profundidade_superior_m, profundidade_inferior_m]
        if profundidade_nivel_agua_m is not None:
            profundidade_agua_m = float(profundidade_nivel_agua_m)
            if profundidade_superior_m < profundidade_agua_m < profundidade_inferior_m:
                cortes.insert(1, profundidade_agua_m)

        for profundidade_topo_m, profundidade_base_m in zip(cortes, cortes[1:]):
            zona_saturada = (
                profundidade_nivel_agua_m is not None
                and (profundidade_topo_m + profundidade_base_m) / 2
                >= float(profundidade_nivel_agua_m)
            )
            sufixo_zona = "SATURADA" if zona_saturada else "NATURAL"
            cota_topo_m = altura_muro_m - profundidade_topo_m
            cota_base_m = altura_muro_m - profundidade_base_m
            x_tardoz_topo_m_local = x_tardoz_topo_m * cota_topo_m / altura_muro_m
            x_tardoz_base_m_local = x_tardoz_topo_m * cota_base_m / altura_muro_m
            cota_superficie_topo_m = (
                cota_aterro_limite_m
                if profundidade_topo_m == 0
                else cota_topo_m
            )
            vertices_faixa = [
                (x_limite_aterro_m, cota_superficie_topo_m),
                (x_tardoz_topo_m_local, cota_topo_m),
                (x_tardoz_base_m_local, cota_base_m),
                (x_limite_aterro_m, cota_base_m),
            ]
            nome_camada_dxf = (
                f"SOLO_CAMADA_{indice_camada:02d}_{sufixo_zona}"
            )
            hachura_solo = espaco_modelo.add_hatch(
                dxfattribs={"layer": nome_camada_dxf}
            )
            hachura_solo.set_solid_fill(color=256)
            hachura_solo.paths.add_polyline_path(vertices_faixa, is_closed=True)


def _desenhar_diagrama_pressao(
    espaco_modelo: Any, entradas_muro: dict[str, Any], resultado_muro: dict[str, Any]
) -> tuple[float, float, float]:
    altura_muro_m = float(entradas_muro["altura_muro_m"])
    largura_base_m = float(entradas_muro["largura_base_m"])
    diagramas_pressao = resultado_muro["diagramas_pressao"]
    pressao_maxima_kPa = max(
        ponto["pressao_kPa"] for ponto in diagramas_pressao["total"]
    )
    largura_diagrama_m = max(3.0, altura_muro_m * 0.8)
    escala_pressao_m_por_kPa = (
        largura_diagrama_m / pressao_maxima_kPa if pressao_maxima_kPa > 0 else 0.0
    )
    x_inicio_diagrama_m = largura_base_m + max(2.5, altura_muro_m * 0.35)
    y_base_pressao_m = -2.0
    altura_texto_m = max(0.16, altura_muro_m * 0.025)

    espaco_modelo.add_line(
        (x_inicio_diagrama_m, altura_muro_m),
        (x_inicio_diagrama_m, 0.0),
        dxfattribs={"layer": "EIXOS_DIAGRAMAS"},
    )
    espaco_modelo.add_line(
        (x_inicio_diagrama_m, altura_muro_m),
        (x_inicio_diagrama_m + largura_diagrama_m, altura_muro_m),
        dxfattribs={"layer": "EIXOS_DIAGRAMAS"},
    )
    _adicionar_texto(
        espaco_modelo,
        "DIAGRAMA DE PRESSOES (kPa)",
        (x_inicio_diagrama_m, altura_muro_m + 0.75),
        altura_texto_m * 1.2,
        "EIXOS_DIAGRAMAS",
    )
    if pressao_maxima_kPa > 0:
        _adicionar_texto(
            espaco_modelo,
            f"{pressao_maxima_kPa:.1f}",
            (x_inicio_diagrama_m + largura_diagrama_m, altura_muro_m + 0.1),
            altura_texto_m,
            "EIXOS_DIAGRAMAS",
        )

    estilos_diagrama = (
        ("solo", "PRESSAO_SOLO"),
        ("sobrecarga", "PRESSAO_SOBRECARGA"),
        ("agua", "PRESSAO_AGUA"),
        ("total", "PRESSAO_TOTAL"),
    )
    for nome_diagrama, nome_camada in estilos_diagrama:
        pontos_diagrama = [
            (
                x_inicio_diagrama_m + ponto["pressao_kPa"] * escala_pressao_m_por_kPa,
                altura_muro_m - ponto["profundidade_m"],
            )
            for ponto in diagramas_pressao[nome_diagrama]
        ]
        espaco_modelo.add_lwpolyline(
            pontos_diagrama, dxfattribs={"layer": nome_camada}
        )

    x_legenda_m = x_inicio_diagrama_m
    y_legenda_m = y_base_pressao_m - 0.5
    for indice_legenda, (rotulo, nome_camada) in enumerate(
        (
            ("Solo", "PRESSAO_SOLO"),
            ("Sobrecarga", "PRESSAO_SOBRECARGA"),
            ("Agua", "PRESSAO_AGUA"),
            ("Total", "PRESSAO_TOTAL"),
        )
    ):
        x_legenda_atual_m = x_legenda_m + indice_legenda * max(1.6, altura_muro_m * 0.35)
        espaco_modelo.add_line(
            (x_legenda_atual_m, y_legenda_m),
            (x_legenda_atual_m + 0.45, y_legenda_m),
            dxfattribs={"layer": nome_camada},
        )
        _adicionar_texto(
            espaco_modelo,
            rotulo,
            (x_legenda_atual_m + 0.5, y_legenda_m - 0.05),
            altura_texto_m * 0.82,
            nome_camada,
        )
    return x_inicio_diagrama_m, largura_diagrama_m, y_base_pressao_m


def _desenhar_diagrama_pressao_base(
    espaco_modelo: Any,
    entradas_muro: dict[str, Any],
    resultado_muro: dict[str, Any],
    coordenadas_diagrama_pressao: tuple[float, float, float],
) -> None:
    verificacoes = resultado_muro["verificacoes"]
    tensao_maxima_kPa = verificacoes["tensao_maxima_base_kPa"]
    if tensao_maxima_kPa is None:
        return

    x_diagrama_m, largura_diagrama_m, y_base_pressao_m = coordenadas_diagrama_pressao
    largura_base_m = float(entradas_muro["largura_base_m"])
    tensao_minima_kPa = float(verificacoes["tensao_minima_base_kPa"])
    excentricidade_m = float(verificacoes["excentricidade_resultante_m"])
    regime_pressao_base = verificacoes["regime_pressao_base"]
    if regime_pressao_base == "TRIANGULAR":
        if float(verificacoes["posicao_resultante_desde_ponta_m"]) <= largura_base_m / 2:
            tensao_ponta_kPa, tensao_tardoz_kPa = float(tensao_maxima_kPa), 0.0
        else:
            tensao_ponta_kPa, tensao_tardoz_kPa = 0.0, float(tensao_maxima_kPa)
    else:
        tensao_media_kPa = float(resultado_muro["resumo"]["carga_vertical_total_kN_m"]) / largura_base_m
        tensao_ponta_kPa = tensao_media_kPa * (1 + 6 * excentricidade_m / largura_base_m)
        tensao_tardoz_kPa = tensao_media_kPa * (1 - 6 * excentricidade_m / largura_base_m)

    escala_tensao_m_por_kPa = 1.7 / float(tensao_maxima_kPa) if tensao_maxima_kPa > 0 else 0.0
    y_inicio_diagrama_m = y_base_pressao_m - 1.0
    x_inicio_diagrama_m = x_diagrama_m
    x_final_diagrama_m = x_inicio_diagrama_m + largura_diagrama_m
    espaco_modelo.add_line(
        (x_inicio_diagrama_m, y_inicio_diagrama_m),
        (x_final_diagrama_m, y_inicio_diagrama_m),
        dxfattribs={"layer": "EIXOS_DIAGRAMAS"},
    )
    espaco_modelo.add_lwpolyline(
        [
            (x_inicio_diagrama_m, y_inicio_diagrama_m),
            (x_inicio_diagrama_m, y_inicio_diagrama_m - tensao_ponta_kPa * escala_tensao_m_por_kPa),
            (x_final_diagrama_m, y_inicio_diagrama_m - tensao_tardoz_kPa * escala_tensao_m_por_kPa),
            (x_final_diagrama_m, y_inicio_diagrama_m),
        ],
        dxfattribs={"layer": "PRESSAO_BASE"},
    )
    _adicionar_texto(
        espaco_modelo,
        f"PRESSAO DE CONTATO NA BASE ({regime_pressao_base.lower()})",
        (x_inicio_diagrama_m, y_inicio_diagrama_m - 2.15),
        0.17,
        "PRESSAO_BASE",
    )
    _adicionar_texto(
        espaco_modelo,
        f"Ponta: {tensao_ponta_kPa:.1f} kPa",
        (x_inicio_diagrama_m, y_inicio_diagrama_m - 2.45),
        0.14,
        "PRESSAO_BASE",
    )
    _adicionar_texto(
        espaco_modelo,
        f"Tardoz: {tensao_tardoz_kPa:.1f} kPa (qmin={tensao_minima_kPa:.1f})",
        (x_inicio_diagrama_m + largura_diagrama_m * 0.45, y_inicio_diagrama_m - 2.45),
        0.14,
        "PRESSAO_BASE",
    )


def _desenhar_cotas(espaco_modelo: Any, entradas_muro: dict[str, Any]) -> None:
    altura_muro_m = float(entradas_muro["altura_muro_m"])
    largura_base_m = float(entradas_muro["largura_base_m"])
    largura_topo_m = float(entradas_muro["largura_topo_m"])
    x_tardoz_topo_m = largura_base_m - largura_topo_m
    escala_cota_m = max(0.16, altura_muro_m * 0.03)
    estilo_cota = {
        "dimtxt": escala_cota_m,
        "dimasz": escala_cota_m * 0.8,
        "dimexo": escala_cota_m * 0.25,
        "dimexe": escala_cota_m * 0.5,
        "dimgap": escala_cota_m * 0.3,
        "dimdec": 2,
        "dimlfac": 1,
        "dimtad": 1,
    }
    espaco_modelo.add_linear_dim(
        base=(0.0, -escala_cota_m * 3.0),
        p1=(0.0, 0.0),
        p2=(largura_base_m, 0.0),
        angle=0,
        override=estilo_cota,
        dxfattribs={"layer": "COTAS"},
    ).render()
    espaco_modelo.add_linear_dim(
        base=(-escala_cota_m * 3.0, 0.0),
        p1=(0.0, 0.0),
        p2=(0.0, altura_muro_m),
        angle=90,
        override=estilo_cota,
        dxfattribs={"layer": "COTAS"},
    ).render()
    espaco_modelo.add_linear_dim(
        base=(0.0, altura_muro_m + escala_cota_m * 2.5),
        p1=(x_tardoz_topo_m, altura_muro_m),
        p2=(largura_base_m, altura_muro_m),
        angle=0,
        override=estilo_cota,
        dxfattribs={"layer": "COTAS"},
    ).render()


def _adicionar_resumo(
    espaco_modelo: Any,
    entradas_muro: dict[str, Any],
    camadas_solo: list[dict[str, Any]],
    resultado_muro: dict[str, Any],
) -> None:
    altura_muro_m = float(entradas_muro["altura_muro_m"])
    largura_base_m = float(entradas_muro["largura_base_m"])
    resumo = resultado_muro["resumo"]
    verificacoes = resultado_muro["verificacoes"]
    x_inicio_resumo_m = min(0.0, resultado_muro["geometria_muro"][0]["x_m"]) - max(
        2.0, altura_muro_m * 0.4
    )
    x_diagrama_pressao_m = largura_base_m + max(2.5, altura_muro_m * 0.35)
    largura_resumo_m = max(26.0, x_diagrama_pressao_m + max(3.0, altura_muro_m * 0.8) - x_inicio_resumo_m)
    altura_texto_m = max(0.12, altura_muro_m * 0.02)
    y_atual_m = -max(6.0, altura_muro_m * 0.9)
    altura_titulo_m = altura_texto_m * 1.7
    topo_quadro_m = y_atual_m + altura_titulo_m + 0.55
    _adicionar_texto(
        espaco_modelo,
        "RESUMO DO MURO",
        (x_inicio_resumo_m, y_atual_m),
        altura_titulo_m,
        "RESUMO",
    )
    y_atual_m -= altura_titulo_m + 0.25

    secoes_resumo = _criar_secoes_resumo(
        entradas_muro, camadas_solo, resultado_muro
    )
    for titulo_secao, linhas_secao in secoes_resumo:
        _adicionar_texto(
            espaco_modelo,
            titulo_secao,
            (x_inicio_resumo_m, y_atual_m),
            altura_texto_m * 1.3,
            "RESUMO",
        )
        y_atual_m -= altura_texto_m * 1.65
        espaco_modelo.add_line(
            (x_inicio_resumo_m, y_atual_m),
            (x_inicio_resumo_m + largura_resumo_m, y_atual_m),
            dxfattribs={"layer": "RESUMO"},
        )
        y_atual_m -= altura_texto_m * 0.45
        espaco_modelo.add_mtext(
            "\\P".join(linhas_secao),
            dxfattribs={
                "insert": (x_inicio_resumo_m, y_atual_m),
                "char_height": altura_texto_m,
                "width": largura_resumo_m,
                "layer": "RESUMO",
            },
        )
        y_atual_m -= altura_texto_m * (len(linhas_secao) * 1.55 + 1.0)

    altura_quadro_m = topo_quadro_m - (y_atual_m - 0.2)
    espaco_modelo.add_lwpolyline(
        [
            (x_inicio_resumo_m - 0.35, y_atual_m - 0.2),
            (x_inicio_resumo_m + largura_resumo_m + 0.35, y_atual_m - 0.2),
            (x_inicio_resumo_m + largura_resumo_m + 0.35, y_atual_m + altura_quadro_m),
            (x_inicio_resumo_m - 0.35, y_atual_m + altura_quadro_m),
        ],
        close=True,
        dxfattribs={"layer": "RESUMO"},
    )


def _criar_secoes_resumo(
    entradas_muro: dict[str, Any],
    camadas_solo: list[dict[str, Any]],
    resultado_muro: dict[str, Any],
) -> list[tuple[str, list[str]]]:
    resumo = resultado_muro["resumo"]
    verificacoes = resultado_muro["verificacoes"]
    altura_muro_m = float(entradas_muro["altura_muro_m"])
    camadas_ativas = [camada for camada in camadas_solo if float(camada["espessura_m"]) > 0]
    if entradas_muro.get("profundidade_nivel_agua_m") is None:
        texto_nivel_agua = "sem N.A."
    else:
        texto_nivel_agua = (
            f"N.A. a {float(entradas_muro['profundidade_nivel_agua_m']):.2f} m do topo"
        )

    linhas_geometria = [
        f"H={altura_muro_m:.2f} m; base b={float(entradas_muro['largura_base_m']):.2f} m; topo t={float(entradas_muro['largura_topo_m']):.2f} m; concreto gamma_c={float(entradas_muro['peso_especifico_concreto_kN_m3']):.2f} kN/m3.",
        f"Teoria: {entradas_muro['metodo_empuxo']}; aterro beta={float(entradas_muro['inclinacao_aterro_graus']):.2f} graus; atrito solo-muro delta={float(entradas_muro['atrito_solo_muro_graus']):.2f} graus; sobrecarga q={float(entradas_muro['sobrecarga_kPa']):.2f} kPa.",
        f"{texto_nivel_agua}; peso especifico da agua gamma_w={float(entradas_muro['peso_especifico_agua_kN_m3']):.2f} kN/m3; atrito na base f={float(entradas_muro['coeficiente_atrito_base']):.3f}.",
        "Layers do solo: SOLO_CAMADA_nn_NATURAL e SOLO_CAMADA_nn_SATURADA; cores diferenciadas por camada.",
    ]
    for indice_camada, camada in enumerate(camadas_ativas, start=1):
        linhas_geometria.append(
            f"Camada {indice_camada}: espessura={float(camada['espessura_m']):.2f} m; gamma natural/saturado={float(camada['peso_especifico_natural_kN_m3']):.2f}/{float(camada['peso_especifico_saturado_kN_m3']):.2f} kN/m3; phi={float(camada['angulo_atrito_graus']):.2f} graus; c={float(camada['coesao_kPa']):.2f} kPa."
        )

    linhas_empuxo = [
        f"Solo: E={float(resumo['empuxo_solo_kN_m']):.3f} kN/m; braco medio={float(resumo['braco_empuxo_solo_m']):.3f} m; M na ponta={float(resumo['momento_solo_ponta_kNm_m']):.3f} kN.m/m.",
        f"Sobrecarga: E={float(resumo['empuxo_sobrecarga_kN_m']):.3f} kN/m; braco medio={float(resumo['braco_sobrecarga_m']):.3f} m; M na ponta={float(resumo['momento_sobrecarga_ponta_kNm_m']):.3f} kN.m/m.",
        f"Agua: E={float(resumo['empuxo_hidrostatico_kN_m']):.3f} kN/m; braco medio={float(resumo['braco_hidrostatico_m']):.3f} m; M na ponta={float(resumo['momento_hidrostatico_ponta_kNm_m']):.3f} kN.m/m.",
        f"Resultante horizontal total={float(resumo['componente_horizontal_total_kN_m']):.3f} kN/m; componente vertical descendente={float(resumo['componente_vertical_descendente_kN_m']):.3f} kN/m.",
    ]
    if verificacoes["tensao_maxima_base_kPa"] is None:
        texto_tensoes = "resultante fora da base; tensoes de contato nao calculadas"
    else:
        texto_tensoes = (
            f"Pressao maxima na base sigma_max={float(verificacoes['tensao_maxima_base_kPa']):.2f} kPa; "
            f"sigma_min={float(verificacoes['tensao_minima_base_kPa']):.2f} kPa; "
            f"admissivel={float(entradas_muro['tensao_admissivel_fundacao_kPa']):.2f} kPa; "
            f"FS tensao={float(verificacoes['fator_seguranca_tensao_admissivel']):.3f}."
        )
    linhas_estabilidade = [
        f"Peso do muro={float(resumo['peso_muro_kN_m']):.3f} kN/m; carga vertical V={float(resumo['carga_vertical_total_kN_m']):.3f} kN/m.",
        f"Momento estabilizador={float(resumo['momento_estabilizador_total_kNm_m']):.3f} kN.m/m; momento tombador={float(resumo['momento_tombador_ponta_kNm_m']):.3f} kN.m/m.",
        f"FS contra tombamento={float(verificacoes['fator_seguranca_tombamento']):.3f} ({verificacoes['status_tombamento']}; minimo {float(entradas_muro['fator_seguranca_minimo_tombamento']):.2f}); FS contra deslizamento={float(verificacoes['fator_seguranca_deslizamento']):.3f} ({verificacoes['status_deslizamento']}; minimo {float(entradas_muro['fator_seguranca_minimo_deslizamento']):.2f}).",
        f"Resultante desde a ponta x_R={float(verificacoes['posicao_resultante_desde_ponta_m']):.3f} m; excentricidade e={float(verificacoes['excentricidade_resultante_m']):.3f} m; contato {verificacoes['regime_pressao_base']}; {texto_tensoes}",
    ]
    linhas_trechos = [
        "Trecho | z superior/inferior (m) | Ka | p solo sup./inf. (kPa) | p q (kPa) | p agua sup./inf. (kPa) | E solo/braco/M | E q/braco/M | E agua/braco/M"
    ]
    for trecho in resultado_muro["trechos"]:
        linhas_trechos.append(
            f"{trecho['identificacao_trecho']} | {float(trecho['profundidade_superior_m']):.2f}/{float(trecho['profundidade_inferior_m']):.2f} | {float(trecho['coeficiente_empuxo_ativo']):.4f} | {float(trecho['pressao_solo_superior_kPa']):.2f}/{float(trecho['pressao_solo_inferior_kPa']):.2f} | {float(trecho['pressao_sobrecarga_kPa']):.2f} | {float(trecho['pressao_agua_superior_kPa']):.2f}/{float(trecho['pressao_agua_inferior_kPa']):.2f} | {float(trecho['empuxo_solo_kN_m']):.2f}/{float(trecho['braco_empuxo_solo_ponta_m']):.2f}/{float(trecho['momento_empuxo_solo_ponta_kNm_m']):.2f} | {float(trecho['empuxo_sobrecarga_kN_m']):.2f}/{float(trecho['braco_empuxo_sobrecarga_ponta_m']):.2f}/{float(trecho['momento_empuxo_sobrecarga_ponta_kNm_m']):.2f} | {float(trecho['empuxo_hidrostatico_kN_m']):.2f}/{float(trecho['braco_empuxo_hidrostatico_ponta_m']):.2f}/{float(trecho['momento_empuxo_hidrostatico_ponta_kNm_m']):.2f}"
        )
    linhas_trechos.append(
        "Pressao lateral: p_total = p_solo + p_sobrecarga + p_agua; momentos de empuxo medidos desde a ponta da base."
    )
    return [
        ("GEOMETRIA E HIPOTESES", linhas_geometria),
        ("EMPuxos E MOMENTOS", linhas_empuxo),
        ("ESTABILIDADE E FUNDACAO", linhas_estabilidade),
        ("RESULTADOS POR TRECHO", linhas_trechos),
    ]


def _adicionar_texto(
    espaco_modelo: Any,
    texto: str,
    ponto_insercao: tuple[float, float],
    altura_texto_m: float,
    nome_camada: str,
) -> None:
    espaco_modelo.add_text(
        texto,
        dxfattribs={
            "insert": ponto_insercao,
            "height": altura_texto_m,
            "layer": nome_camada,
        },
    )
