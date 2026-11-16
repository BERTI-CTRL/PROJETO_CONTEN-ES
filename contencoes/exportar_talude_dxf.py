"""Gera um desenho DXF do perfil e do círculo crítico do talude."""

from __future__ import annotations

from io import StringIO
from typing import Any

import ezdxf


def gerar_desenho_talude_dxf(
    entradas_talude: dict[str, Any], resultado_talude: dict[str, Any], circulo: dict[str, Any]
) -> bytes:
    """Monta o perfil em metros e inclui as principais cotas e resultados."""
    documento = ezdxf.new("R2010", setup=True, units=6)
    espaco_modelo = documento.modelspace()

    camadas_desenho = {
        "TERRENO": (3, "CONTINUOUS"),
        "CAMADAS": (30, "DASHED"),
        "NIVEL_AGUA": (5, "DASHDOT"),
        "CIRCULO_CRITICO": (1, "CONTINUOUS"),
        "CENTRO_CIRCULO": (7, "CONTINUOUS"),
        "COTAS": (2, "CONTINUOUS"),
        "MEMORIAL": (7, "CONTINUOUS"),
    }
    for nome_camada, (cor, tipo_linha) in camadas_desenho.items():
        documento.layers.new(nome_camada, dxfattribs={"color": cor, "linetype": tipo_linha})

    pontos_perfil = resultado_talude["perfil_terreno"]
    espaco_modelo.add_lwpolyline(
        [(ponto["x_m"], ponto["cota_y_m"]) for ponto in pontos_perfil],
        dxfattribs={"layer": "TERRENO"},
    )

    x_minimo_m = float(entradas_talude["limite_x_grafico_minimo_m"])
    x_maximo_m = float(entradas_talude["limite_x_grafico_maximo_m"])
    cota_interface_m = float(resultado_talude["geometria"]["cota_interface_camadas_m"])
    espaco_modelo.add_line(
        (x_minimo_m, cota_interface_m),
        (x_maximo_m, cota_interface_m),
        dxfattribs={"layer": "CAMADAS"},
    )
    espaco_modelo.add_text(
        "Interface das camadas",
        dxfattribs={
            "insert": (x_minimo_m + 0.25, cota_interface_m + 0.12),
            "height": max(0.18, float(entradas_talude["altura_talude_m"]) * 0.025),
            "layer": "CAMADAS",
        },
    )

    cota_nivel_agua_m = resultado_talude["geometria"]["cota_nivel_agua_m"]
    if cota_nivel_agua_m is not None:
        espaco_modelo.add_line(
            (x_minimo_m, cota_nivel_agua_m),
            (x_maximo_m, cota_nivel_agua_m),
            dxfattribs={"layer": "NIVEL_AGUA"},
        )
        espaco_modelo.add_text(
            "Nivel d'agua",
            dxfattribs={
                "insert": (x_minimo_m + 0.25, cota_nivel_agua_m + 0.12),
                "height": max(0.18, float(entradas_talude["altura_talude_m"]) * 0.025),
                "layer": "NIVEL_AGUA",
            },
        )

    x_saida_m = float(circulo["x_saida_m"])
    x_entrada_m = float(circulo["x_entrada_m"])
    centro_x_m = float(circulo["centro_x_m"])
    centro_y_m = float(circulo["centro_y_m"])
    raio_m = float(circulo["raio_m"])
    quantidade_pontos_arco = 121
    pontos_arco = []
    for indice_ponto in range(quantidade_pontos_arco):
        coordenada_x_m = x_saida_m + indice_ponto * (x_entrada_m - x_saida_m) / (
            quantidade_pontos_arco - 1
        )
        radicando_arco = max(0.0, raio_m**2 - (coordenada_x_m - centro_x_m) ** 2)
        coordenada_y_m = centro_y_m - radicando_arco**0.5
        pontos_arco.append((coordenada_x_m, coordenada_y_m))
    espaco_modelo.add_lwpolyline(
        pontos_arco, dxfattribs={"layer": "CIRCULO_CRITICO"}
    )
    espaco_modelo.add_circle(
        (centro_x_m, centro_y_m),
        max(0.025, raio_m * 0.008),
        dxfattribs={"layer": "CENTRO_CIRCULO"},
    )
    espaco_modelo.add_line(
        (centro_x_m - raio_m * 0.015, centro_y_m),
        (centro_x_m + raio_m * 0.015, centro_y_m),
        dxfattribs={"layer": "CENTRO_CIRCULO"},
    )
    espaco_modelo.add_line(
        (centro_x_m, centro_y_m - raio_m * 0.015),
        (centro_x_m, centro_y_m + raio_m * 0.015),
        dxfattribs={"layer": "CENTRO_CIRCULO"},
    )

    altura_talude_m = float(entradas_talude["altura_talude_m"])
    comprimento_horizontal_face_m = float(
        resultado_talude["geometria"]["comprimento_horizontal_face_m"]
    )
    coordenada_x_crista_m = comprimento_horizontal_face_m
    coordenada_x_entrada_geometria_m = float(
        resultado_talude["geometria"]["coordenada_x_entrada_m"]
    )
    cota_entrada_m = float(resultado_talude["geometria"]["cota_entrada_m"])
    escala_cota_m = max(0.18, altura_talude_m * 0.035)
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
        base=(0.0, -escala_cota_m * 2.5),
        p1=(0.0, 0.0),
        p2=(comprimento_horizontal_face_m, altura_talude_m),
        angle=0,
        override=estilo_cota,
        dxfattribs={"layer": "COTAS"},
    ).render()
    espaco_modelo.add_linear_dim(
        base=(-escala_cota_m * 2.5, 0.0),
        p1=(0.0, 0.0),
        p2=(0.0, altura_talude_m),
        angle=90,
        override=estilo_cota,
        dxfattribs={"layer": "COTAS"},
    ).render()
    espaco_modelo.add_linear_dim(
        base=(0.0, altura_talude_m + escala_cota_m * 2.5),
        p1=(coordenada_x_crista_m, altura_talude_m),
        p2=(coordenada_x_entrada_geometria_m, cota_entrada_m),
        angle=0,
        override=estilo_cota,
        dxfattribs={"layer": "COTAS"},
    ).render()

    memorial_x_m = x_maximo_m + max(3.0, altura_talude_m * 0.6)
    memorial_y_m = altura_talude_m + max(2.0, altura_talude_m * 0.35)
    altura_texto_m = max(0.22, altura_talude_m * 0.035)

    def adicionar_linha_memorial(texto: str, indice_linha: int, altura: float | None = None) -> None:
        espaco_modelo.add_text(
            texto,
            dxfattribs={
                "insert": (memorial_x_m, memorial_y_m - indice_linha * altura_texto_m * 1.7),
                "height": altura or altura_texto_m,
                "layer": "MEMORIAL",
            },
        )

    adicionar_linha_memorial("TALUDE - MEMORIAL RESUMIDO", 0, altura_texto_m * 1.25)
    adicionar_linha_memorial("Metodo: Fellenius (fatias ordinarias)", 1)
    adicionar_linha_memorial(f"Circulo critico: {circulo['identificacao']}", 2)
    adicionar_linha_memorial(f"Fator de seguranca: {circulo['fator_seguranca']:.3f}", 3)
    adicionar_linha_memorial(f"Raio R: {raio_m:.3f} m", 4)
    adicionar_linha_memorial(f"Centro C: ({centro_x_m:.3f}; {centro_y_m:.3f}) m", 5)
    adicionar_linha_memorial(
        f"Soma resistente: {circulo['resistencia_total_kN_m']:.2f} kN/m", 6
    )
    adicionar_linha_memorial(
        f"Soma mobilizada: {circulo['forca_mobilizada_total_kN_m']:.2f} kN/m", 7
    )
    adicionar_linha_memorial("FS = soma resistente / soma mobilizada", 8)
    adicionar_linha_memorial(
        f"Geometria: H={altura_talude_m:.2f} m; face H/V={float(entradas_talude['relacao_horizontal_vertical_face']):.2f}", 10
    )
    adicionar_linha_memorial(
        f"Camada 1: gamma={float(entradas_talude['peso_especifico_natural_camada_superior_kN_m3']):.1f}/{float(entradas_talude['peso_especifico_saturado_camada_superior_kN_m3']):.1f} kN/m3; c'={float(entradas_talude['coesao_efetiva_camada_superior_kPa']):.1f} kPa; phi'={float(entradas_talude['angulo_atrito_efetivo_camada_superior_graus']):.1f} graus", 11
    )
    adicionar_linha_memorial(
        f"Camada 2: gamma={float(entradas_talude['peso_especifico_natural_camada_inferior_kN_m3']):.1f}/{float(entradas_talude['peso_especifico_saturado_camada_inferior_kN_m3']):.1f} kN/m3; c'={float(entradas_talude['coesao_efetiva_camada_inferior_kPa']):.1f} kPa; phi'={float(entradas_talude['angulo_atrito_efetivo_camada_inferior_graus']):.1f} graus", 12
    )
    if entradas_talude.get("profundidade_nivel_agua_abaixo_crista_m") is None:
        texto_nivel_agua = "Nivel d'agua: nao informado"
    else:
        texto_nivel_agua = (
            "Nivel d'agua: "
            f"{float(entradas_talude['profundidade_nivel_agua_abaixo_crista_m']):.2f} m abaixo da crista"
        )
    adicionar_linha_memorial(texto_nivel_agua, 13)
    adicionar_linha_memorial(
        f"Sobrecarga q={float(entradas_talude['sobrecarga_crista_kPa']):.2f} kPa; fatias={int(entradas_talude['quantidade_fatias'])}",
        14,
    )
    adicionar_linha_memorial(
        "Desenho didatico; confirmar convencoes e criterio do projeto.", 16
    )

    arquivo_texto = StringIO()
    documento.write(arquivo_texto)
    return documento.encode(arquivo_texto.getvalue())
