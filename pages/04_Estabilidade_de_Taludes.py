from __future__ import annotations

import json
import math
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from streamlit_local_storage import LocalStorage

from contencoes.calculos_estabilidade_taludes import (
    calcular_estabilidade_talude,
    calcular_geometria_talude,
    carregar_exemplo_talude,
    gerar_raios_candidatos_padrao,
    validar_entradas_talude,
)
from contencoes.exportar_talude_dxf import gerar_desenho_talude_dxf


st.set_page_config(page_title="Talude | Contenções", page_icon="⛰️", layout="wide")

CHAVE_ARMAZENAMENTO_NAVEGADOR = "projeto_contencoes_talude_v1"
CHAVE_ESTADO_DA_SESSAO = "dados_talude_preservados_na_sessao"
CAMPOS_FORMULARIO = [
    "altura_talude_m",
    "relacao_horizontal_vertical_face",
    "inclinacao_terreno_montante_graus",
    "distancia_crista_entrada_m",
    "espessura_camada_superior_m",
    "profundidade_nivel_agua_abaixo_crista_m",
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
]
CHAVES_RAIOS_CANDIDATOS = [f"raio_candidato_{indice:02d}_m" for indice in range(1, 11)]


def _normalizar_dados(dados_salvos: Any) -> dict[str, Any]:
    dados_padrao = carregar_exemplo_talude()
    if not isinstance(dados_salvos, dict):
        return dados_padrao

    for campo, valor_padrao in dados_padrao.items():
        if campo not in dados_salvos:
            continue
        valor_salvo = dados_salvos[campo]
        try:
            if campo == "raios_candidatos_m":
                if isinstance(valor_salvo, list) and len(valor_salvo) == 10:
                    dados_padrao[campo] = [float(valor) for valor in valor_salvo]
            elif valor_padrao is None:
                dados_padrao[campo] = None if valor_salvo is None else float(valor_salvo)
            elif isinstance(valor_padrao, int):
                dados_padrao[campo] = int(float(valor_salvo))
            else:
                dados_padrao[campo] = float(valor_salvo)
        except (TypeError, ValueError, OverflowError):
            continue
    return dados_padrao


def _aplicar_dados_dos_widgets(dados_talude: dict[str, Any]) -> None:
    for campo in CAMPOS_FORMULARIO:
        st.session_state[campo] = dados_talude[campo]
    for chave_raio, raio_m in zip(CHAVES_RAIOS_CANDIDATOS, dados_talude["raios_candidatos_m"]):
        st.session_state[chave_raio] = raio_m


def _restaurar_exemplo() -> None:
    _aplicar_dados_dos_widgets(carregar_exemplo_talude())


def _regenerar_raios_padrao() -> None:
    entradas_atualizadas = _capturar_dados_dos_widgets()
    raios_padrao = gerar_raios_candidatos_padrao(entradas_atualizadas)
    for chave_raio, raio_m in zip(CHAVES_RAIOS_CANDIDATOS, raios_padrao):
        st.session_state[chave_raio] = raio_m


def _capturar_dados_dos_widgets() -> dict[str, Any]:
    entradas = {campo: st.session_state.get(campo) for campo in CAMPOS_FORMULARIO}
    entradas["raios_candidatos_m"] = [
        st.session_state.get(chave_raio, 0.0) for chave_raio in CHAVES_RAIOS_CANDIDATOS
    ]
    return entradas


def _formatar_numero(valor: float | None, casas_decimais: int = 3) -> str:
    if valor is None:
        return "—"
    return f"{valor:,.{casas_decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _configuracao_download_png(nome_arquivo: str) -> dict[str, Any]:
    return {
        "displaylogo": False,
        "toImageButtonOptions": {
            "format": "png",
            "filename": nome_arquivo,
            "scale": 2,
        },
    }


def _mostrar_croqui_entrada_talude(
    entradas_talude: dict[str, Any],
    geometria: dict[str, Any],
    circulo: dict[str, Any] | None,
) -> None:
    """Desenha um croqui esquemático que acompanha os dados da geometria."""
    altura = float(entradas_talude["altura_talude_m"])
    relacao_face = float(entradas_talude["relacao_horizontal_vertical_face"])
    largura_face = altura * relacao_face
    x_saida = -float(entradas_talude["distancia_pe_saida_m"])
    x_entrada = float(geometria["coordenada_x_entrada_m"])
    x_min = min(x_saida, -altura * 0.55, 0.0) - max(altura * 0.08, 0.5)
    x_max = max(largura_face, x_entrada) + max(altura * 0.55, 2.0)
    y_min = -altura * 0.22
    y_max = max(altura, float(geometria["cota_entrada_m"])) + altura * 0.8
    if geometria["cota_nivel_agua_m"] is not None:
        y_min = min(y_min, float(geometria["cota_nivel_agua_m"]) - altura * 0.05)
    if circulo and circulo.get("centro_x_m") is not None:
        y_min = min(y_min, min(_coordenadas_arco_y(circulo)) - altura * 0.05)
        y_max = max(y_max, float(circulo["centro_y_m"]) + altura * 0.22)

    def cota_terreno(x: float) -> float:
        if x <= 0:
            return 0.0
        if x <= largura_face:
            return x / relacao_face
        return altura + (x - largura_face) * math.tan(
            math.radians(float(entradas_talude["inclinacao_terreno_montante_graus"]))
        )

    coordenadas_x = [x_min + (x_max - x_min) * indice / 80 for indice in range(81)]
    coordenadas_y = [cota_terreno(x) for x in coordenadas_x]
    y_interface = float(geometria["cota_interface_camadas_m"])
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=[x_min, *coordenadas_x, x_max, x_min],
            y=[y_min, *coordenadas_y, y_min, y_min],
            mode="lines",
            line={"width": 0},
            fill="toself",
            fillcolor="#f4ead8",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    cruzamentos_interface = []
    for indice in range(len(coordenadas_x) - 1):
        x1, x2 = coordenadas_x[indice], coordenadas_x[indice + 1]
        y1, y2 = coordenadas_y[indice], coordenadas_y[indice + 1]
        if (y1 - y_interface) * (y2 - y_interface) < 0:
            cruzamentos_interface.append(
                x1 + (y_interface - y1) * (x2 - x1) / (y2 - y1)
            )
    x_inicio_superior = (
        cruzamentos_interface[0]
        if coordenadas_y[0] < y_interface and cruzamentos_interface
        else x_min
    )
    x_fim_superior = (
        cruzamentos_interface[-1]
        if coordenadas_y[-1] < y_interface and cruzamentos_interface
        else x_max
    )
    indices_superior = [
        indice
        for indice, (x, y) in enumerate(zip(coordenadas_x, coordenadas_y))
        if x_inicio_superior <= x <= x_fim_superior and y >= y_interface
    ]
    if indices_superior:
        figura.add_trace(
            go.Scatter(
                x=[
                    x_inicio_superior,
                    *[coordenadas_x[i] for i in indices_superior],
                    x_fim_superior,
                    x_inicio_superior,
                ],
                y=[
                    y_interface,
                    *[coordenadas_y[i] for i in indices_superior],
                    y_interface,
                    y_interface,
                ],
                mode="lines",
                line={"width": 0},
                fill="toself",
                fillcolor="#dceaf0",
                hoverinfo="skip",
                showlegend=False,
            )
        )

    figura.add_trace(
        go.Scatter(
            x=coordenadas_x,
            y=coordenadas_y,
            mode="lines",
            line={"color": "#398e79", "width": 3},
            hoverinfo="skip",
            showlegend=False,
        )
    )
    figura.add_hline(y=y_interface, line_color="#d99028", line_width=1.5, line_dash="dash")
    cota_agua = geometria["cota_nivel_agua_m"]
    if cota_agua is not None:
        figura.add_hline(
            y=float(cota_agua),
            line_color="#438fbd",
            line_width=1.5,
            line_dash="dash",
        )

    if circulo and circulo.get("centro_x_m") is not None:
        numero_fatias = int(entradas_talude["quantidade_fatias"])
        passo = (x_entrada - x_saida) / numero_fatias
        x_arco = [
            x_saida + (x_entrada - x_saida) * indice / 80 for indice in range(81)
        ]
        y_arco = [_cota_arco(circulo, x) for x in x_arco]
        figura.add_trace(
            go.Scatter(
                x=x_arco,
                y=y_arco,
                mode="lines",
                line={"color": "#bd5948", "width": 2.5},
                hoverinfo="skip",
                showlegend=False,
            )
        )
        x_fatias, y_fatias = [], []
        for indice in range(numero_fatias + 1):
            x_fatia = x_saida + indice * passo
            y_base = _cota_arco(circulo, x_fatia)
            x_fatias.extend([x_fatia, x_fatia, None])
            y_fatias.extend([y_base, cota_terreno(x_fatia), None])
        figura.add_trace(
            go.Scatter(
                x=x_fatias,
                y=y_fatias,
                mode="lines",
                line={"color": "#82918f", "width": 1},
                hoverinfo="skip",
                showlegend=False,
            )
        )
        figura.add_trace(
            go.Scatter(
                x=[circulo["centro_x_m"]],
                y=[circulo["centro_y_m"]],
                mode="markers+text",
                text=["C"],
                textposition="top right",
                marker={"color": "#17374c", "size": 6},
                hoverinfo="skip",
                showlegend=False,
            )
        )

    sobrecarga = float(entradas_talude["sobrecarga_crista_kPa"])
    if sobrecarga > 0:
        largura_crista = max(0.0, x_entrada - largura_face)
        pontos_carga = (
            [
                largura_face + largura_crista * fracao
                for fracao in (0.2, 0.5, 0.8)
            ]
            if largura_crista > 0.1
            else [largura_face - altura * 0.12, largura_face, largura_face + altura * 0.12]
        )
        for x_carga in pontos_carga:
            figura.add_annotation(
                x=x_carga,
                y=altura,
                text="",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1.5,
                arrowcolor="#c45a4b",
                ax=0,
                ay=-24,
            )

    def indicar_dimensao(
        x_inicio: float,
        y_inicio: float,
        x_fim: float,
        y_fim: float,
        rotulo: str,
        cor: str = "#17374c",
        deslocamento_rotulo: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        figura.add_annotation(
            x=x_fim,
            y=y_fim,
            ax=x_inicio,
            ay=y_inicio,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            text="",
            showarrow=True,
            arrowhead=2,
            startarrowhead=2,
            arrowsize=1,
            startarrowsize=1,
            arrowwidth=1.2,
            arrowcolor=cor,
        )
        figura.add_annotation(
            x=(x_inicio + x_fim) / 2 + deslocamento_rotulo[0],
            y=(y_inicio + y_fim) / 2 + deslocamento_rotulo[1],
            text=f"<b>{rotulo}</b>",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=cor,
            borderwidth=1,
            borderpad=3,
            font={"color": cor, "size": 11},
        )

    x_cota_h = x_min + altura * 0.18
    indicar_dimensao(x_cota_h, 0, x_cota_h, altura, f"H = {altura:g} m", deslocamento_rotulo=(-0.45, 0))
    indicar_dimensao(
        x_saida,
        -altura * 0.09,
        0,
        -altura * 0.09,
        f"Lᵦ = {float(entradas_talude['distancia_pe_saida_m']):g} m",
        deslocamento_rotulo=(0, -altura * 0.09),
    )
    indicar_dimensao(
        largura_face,
        altura + altura * 0.16,
        x_entrada,
        altura + altura * 0.16,
        f"a = {float(entradas_talude['distancia_crista_entrada_m']):g} m",
        deslocamento_rotulo=(0, altura * 0.07),
    )
    indicar_dimensao(
        largura_face,
        y_interface,
        largura_face,
        altura,
        f"h₁ = {float(entradas_talude['espessura_camada_superior_m']):g} m",
        cor="#9b6b20",
        deslocamento_rotulo=(-altura * 0.8, 0),
    )

    beta = float(entradas_talude["inclinacao_terreno_montante_graus"])
    x_beta = largura_face + max(0.45 * (x_entrada - largura_face), altura * 0.18)
    figura.add_annotation(
        x=x_beta,
        y=cota_terreno(x_beta),
        text=f"β = {beta:g}°",
        showarrow=True,
        arrowhead=2,
        ax=30,
        ay=-28,
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="#398e79",
        borderpad=3,
        font={"color": "#176452", "size": 11},
    )
    x_face_label = largura_face * 0.5
    figura.add_annotation(
        x=x_face_label,
        y=cota_terreno(x_face_label) * 0.5,
        text=f"<b>Face H:V = {relacao_face:g}:1</b>",
        showarrow=False,
        textangle=-math.degrees(math.atan(1 / relacao_face)),
        font={"color": "#17374c", "size": 10},
        bgcolor="rgba(255,255,255,0.8)",
    )

    if cota_agua is not None:
        x_cota_agua = -altura * 0.2
        indicar_dimensao(
            x_cota_agua,
            altura,
            x_cota_agua,
            float(cota_agua),
            f"zNA = {float(entradas_talude['profundidade_nivel_agua_abaixo_crista_m']):g} m",
            cor="#367da8",
            deslocamento_rotulo=(-0.55, 0),
        )
        figura.add_annotation(
            x=x_max - altura * 0.08,
            y=float(cota_agua),
            text=f"N.A. · γw = {float(entradas_talude['peso_especifico_agua_kN_m3']):g} kN/m³",
            showarrow=True,
            arrowhead=2,
            ax=-45,
            ay=-24,
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="#438fbd",
            borderpad=3,
            font={"color": "#367da8", "size": 10},
        )
    else:
        figura.add_annotation(
            x=x_max - altura * 0.1,
            y=altura * 0.2,
            text=f"Sem N.A. · γw = {float(entradas_talude['peso_especifico_agua_kN_m3']):g} kN/m³",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.9)",
            font={"color": "#367da8", "size": 10},
        )

    largura_crista = max(0.0, x_entrada - largura_face)
    x_rotulo_camada = largura_face + largura_crista * 0.62
    figura.add_annotation(
        x=x_rotulo_camada,
        y=y_interface + float(entradas_talude["espessura_camada_superior_m"]) * 0.5,
        text="Camada 1",
        showarrow=False,
        font={"color": "#367da8", "size": 10},
    )
    figura.add_annotation(
        x=x_rotulo_camada,
        y=y_interface - min(altura * 0.08, y_interface * 0.35),
        text="Camada 2",
        showarrow=False,
        font={"color": "#815f32", "size": 10},
    )

    if sobrecarga > 0:
        figura.add_annotation(
            x=sum(pontos_carga) / len(pontos_carga),
            y=altura + altura * 0.5,
            text=f"<b>q = {sobrecarga:g} kPa</b>",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=28,
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="#bd5948",
            borderpad=3,
            font={"color": "#bd5948", "size": 11},
        )
    else:
        figura.add_annotation(
            x=largura_face,
            y=altura + altura * 0.5,
            text="q = 0 kPa",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.9)",
            font={"color": "#bd5948", "size": 10},
        )

    if circulo and circulo.get("centro_x_m") is not None:
        x_centro = float(circulo["centro_x_m"])
        y_centro = float(circulo["centro_y_m"])
        indicar_dimensao(
            x_centro,
            y_centro,
            x_saida,
            0,
            f"R = {float(circulo['raio_m']):g} m",
            cor="#bd5948",
            deslocamento_rotulo=(0, -altura * 0.08),
        )

    x_meio_fatias = (x_saida + x_entrada) / 2
    figura.add_annotation(
        x=x_meio_fatias,
        y=cota_terreno(x_meio_fatias),
        text=f"n = {int(entradas_talude['quantidade_fatias'])} fatias",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-34,
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="#82918f",
        borderpad=3,
        font={"color": "#596a77", "size": 10},
    )

    figura.add_annotation(
        x=x_saida,
        y=0,
        text="Saída",
        showarrow=True,
        arrowhead=2,
        ax=-20,
        ay=28,
        font={"color": "#bd5948", "size": 10},
    )
    figura.add_annotation(
        x=x_entrada,
        y=float(geometria["cota_entrada_m"]),
        text=f"Entrada E ({x_entrada:g}; {float(geometria['cota_entrada_m']):g}) m",
        showarrow=True,
        arrowhead=2,
        ax=45,
        ay=-24,
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="#bd5948",
        borderpad=3,
        font={"color": "#bd5948", "size": 9},
    )
    figura.add_annotation(
        x=largura_face,
        y=altura,
        text="Crista",
        showarrow=True,
        arrowhead=2,
        ax=24,
        ay=-28,
        bgcolor="rgba(255,255,255,0.92)",
        font={"color": "#17374c", "size": 9},
    )
    coluna_figura, coluna_simbolos = st.columns([2.35, 1], vertical_alignment="center")
    with coluna_figura:
        st.markdown("**Croqui da geometria e dos parâmetros inseridos**")
        figura.update_layout(
            height=520,
            margin={"l": 8, "r": 8, "t": 12, "b": 8},
            showlegend=False,
            hovermode=False,
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        figura.update_xaxes(range=[x_min, x_max], visible=False, zeroline=False)
        figura.update_yaxes(
            range=[y_min, y_max], visible=False, zeroline=False, scaleanchor="x", scaleratio=1
        )
        st.plotly_chart(
            figura,
            width="stretch",
            theme=None,
            config={"displayModeBar": False, "responsive": True},
        )
    with coluna_simbolos:
        raios_candidatos = " · ".join(
            _formatar_numero(float(raio), 2)
            for raio in entradas_talude["raios_candidatos_m"]
        )
        parametros_camadas = []
        for numero, sufixo in ((1, "superior"), (2, "inferior")):
            parametros_camadas.append(
                f"**Camada {numero}** · γnat/γsat = "
                f"{float(entradas_talude[f'peso_especifico_natural_camada_{sufixo}_kN_m3']):g}/"
                f"{float(entradas_talude[f'peso_especifico_saturado_camada_{sufixo}_kN_m3']):g} kN/m³ · "
                f"c′ = {float(entradas_talude[f'coesao_efetiva_camada_{sufixo}_kPa']):g} kPa · "
                f"φ′ = {float(entradas_talude[f'angulo_atrito_efetivo_camada_{sufixo}_graus']):g}°"
            )
        if circulo and circulo.get("fatias"):
            fatia_referencia = circulo["fatias"][len(circulo["fatias"]) // 2]
            texto_fatia = (
                f"Fatia {int(fatia_referencia['numero_fatia'])}: "
                f"Wᵢ = {float(fatia_referencia['peso_fatia_kN_m']):g} kN/m · "
                f"αᵢ = {float(fatia_referencia['angulo_base_medio_graus']):g}° · "
                f"ΔLᵢ = {float(fatia_referencia['comprimento_arco_m']):g} m · "
                f"uᵢ = {float(fatia_referencia['pressao_neutra_kPa']):g} kPa"
            )
            texto_circulo = (
                f"R = {float(circulo['raio_m']):g} m · "
                f"C = ({float(circulo['centro_x_m']):g}; {float(circulo['centro_y_m']):g}) m · "
                f"FS = {float(circulo['fator_seguranca']):g}"
            )
        else:
            texto_fatia = "Sem fatia de referência disponível."
            texto_circulo = "Sem círculo crítico válido."
        st.markdown(
            "**Referências e valores**\n\n"
            "**GEOMETRIA**\n\n"
            "H: altura · H:V: face · β: terreno a montante · a: crista–entrada · "
            "Lᵦ: pé–saída · h₁: camada superior · zNA: profundidade do N.A. · "
            f"γw = {float(entradas_talude['peso_especifico_agua_kN_m3']):g} kN/m³\n\n"
            "**SOLO**\n\n"
            f"{parametros_camadas[0]}\n\n{parametros_camadas[1]}\n\n"
            "γnat/γsat: pesos específicos natural/saturado · c′: coesão · φ′: atrito.\n\n"
            "**CÍRCULO E FATIAS**\n\n"
            f"{texto_circulo}\n\n{texto_fatia}\n\n"
            f"n = {int(entradas_talude['quantidade_fatias'])} fatias · FS: fator de segurança.\n\n"
            f"**Raios candidatos (m)**\n\n{raios_candidatos}"
        )
    st.caption(
        "As setas indicam dimensões e pontos; os valores detalhados ficam no painel ao lado. "
        "O arco e o raio representam o círculo crítico calculado, quando disponível. "
        f"A janela dos gráficos abaixo vai de x = {float(entradas_talude['limite_x_grafico_minimo_m']):g} "
        f"a {float(entradas_talude['limite_x_grafico_maximo_m']):g} m, com extensão até a entrada "
        "se o limite máximo informado não a incluir."
    )


def _cota_terreno_grafico(x_m: float, entradas_talude: dict[str, Any]) -> float:
    altura_talude_m = float(entradas_talude["altura_talude_m"])
    relacao_horizontal_vertical_face = float(
        entradas_talude["relacao_horizontal_vertical_face"]
    )
    comprimento_face_m = altura_talude_m * relacao_horizontal_vertical_face
    if x_m <= 0:
        return 0.0
    if x_m <= comprimento_face_m:
        return x_m / relacao_horizontal_vertical_face
    return altura_talude_m + (x_m - comprimento_face_m) * math.tan(
        math.radians(float(entradas_talude["inclinacao_terreno_montante_graus"]))
    )


def _cota_arco(circulo: dict[str, Any], x_m: float) -> float:
    radicando = circulo["raio_m"] ** 2 - (x_m - circulo["centro_x_m"]) ** 2
    return circulo["centro_y_m"] - math.sqrt(max(0.0, radicando))


def _mostrar_grafico_geometria(
    entradas_talude: dict[str, Any], resultado_talude: dict[str, Any], circulo_selecionado: dict[str, Any] | None
) -> None:
    figura_geometria = go.Figure()
    pontos_perfil = resultado_talude["perfil_terreno"]
    coordenadas_perfil_x = [ponto["x_m"] for ponto in pontos_perfil]
    coordenadas_perfil_y = [ponto["cota_y_m"] for ponto in pontos_perfil]
    figura_geometria.add_trace(
        go.Scatter(
            x=coordenadas_perfil_x,
            y=coordenadas_perfil_y,
            mode="lines",
            line={"color": "#176452", "width": 4},
            fill="tozeroy",
            fillcolor="rgba(38, 111, 91, 0.14)",
            name="Terreno",
        )
    )

    x_minimo_m = float(entradas_talude["limite_x_grafico_minimo_m"])
    x_maximo_m = max(
        float(entradas_talude["limite_x_grafico_maximo_m"]),
        float(resultado_talude["geometria"]["coordenada_x_entrada_m"]),
    )
    cota_interface_m = resultado_talude["geometria"]["cota_interface_camadas_m"]
    figura_geometria.add_trace(
        go.Scatter(
            x=[x_minimo_m, x_maximo_m],
            y=[cota_interface_m, cota_interface_m],
            mode="lines",
            line={"color": "#d99028", "width": 2, "dash": "dash"},
            name="Interface das camadas",
        )
    )
    cota_nivel_agua_m = resultado_talude["geometria"]["cota_nivel_agua_m"]
    if cota_nivel_agua_m is not None:
        figura_geometria.add_trace(
            go.Scatter(
                x=[x_minimo_m, x_maximo_m],
                y=[cota_nivel_agua_m, cota_nivel_agua_m],
                mode="lines",
                line={"color": "#3e8dc1", "width": 2, "dash": "dashdot"},
                name="Nível d’água",
            )
        )

    busca_centros = resultado_talude.get("busca_centros")
    circulo_critico_malha = (
        busca_centros.get("circulo_critico") if busca_centros else None
    )
    if busca_centros and circulo_critico_malha:
        valores_fs_malha = [
            valor
            for linha in busca_centros["fatores_seguranca_minimos"]
            for valor in linha
            if valor is not None
        ]
        if valores_fs_malha:
            fs_minimo_malha = min(valores_fs_malha)
            fs_maximo_malha = max(valores_fs_malha)
            passo_contorno = max(0.05, (fs_maximo_malha - fs_minimo_malha) / 8)
            fim_contorno = max(fs_maximo_malha, fs_minimo_malha + passo_contorno)
            figura_geometria.add_trace(
                go.Contour(
                    x=busca_centros["coordenadas_x_m"],
                    y=busca_centros["coordenadas_y_m"],
                    z=busca_centros["fatores_seguranca_minimos"],
                    name="Linhas de mesmo FS",
                    showscale=False,
                    connectgaps=False,
                    contours={
                        "start": fs_minimo_malha,
                        "end": fim_contorno,
                        "size": passo_contorno,
                        "coloring": "none",
                        "showlabels": True,
                        "labelfont": {"size": 10, "color": "#334e68"},
                    },
                    line={"color": "#54799a", "width": 1.2},
                    hovertemplate="Centro (x<sub>c</sub>, y<sub>c</sub>) = (%{x:.2f}, %{y:.2f}) m<br>FS mínimo neste centro = %{z:.3f}<extra></extra>",
                )
            )

            centros_x_malha: list[float] = []
            centros_y_malha: list[float] = []
            textos_centros_malha: list[str] = []
            for indice_y, linha_fs in enumerate(
                busca_centros["fatores_seguranca_minimos"]
            ):
                for indice_x, fator_seguranca in enumerate(linha_fs):
                    if fator_seguranca is None:
                        continue
                    centros_x_malha.append(
                        busca_centros["coordenadas_x_m"][indice_x]
                    )
                    centros_y_malha.append(
                        busca_centros["coordenadas_y_m"][indice_y]
                    )
                    textos_centros_malha.append(
                        f"{fator_seguranca:.2f}"
                    )
            figura_geometria.add_trace(
                go.Scatter(
                    x=centros_x_malha,
                    y=centros_y_malha,
                    mode="markers+text",
                    marker={"color": "#54799a", "size": 5, "opacity": 0.7},
                    text=textos_centros_malha,
                    textposition="top center",
                    textfont={"size": 9, "color": "#c34b3c"},
                    name="FS mínimo por centro",
                    hovertemplate="Centro (%{x:.2f}, %{y:.2f}) m<br>FS mínimo = %{text}<extra></extra>",
                )
            )

            figura_geometria.add_trace(
                go.Scatter(
                    x=[circulo_critico_malha["centro_x_m"]],
                    y=[circulo_critico_malha["centro_y_m"]],
                    mode="markers",
                    marker={
                        "color": "#15803d",
                        "size": 13,
                        "symbol": "star",
                        "line": {"color": "white", "width": 1},
                    },
                    name="FS mínimo da malha",
                    hovertemplate=(
                        "FS mínimo da malha = "
                        f"{circulo_critico_malha['fator_seguranca']:.3f}"
                        "<br>R = %{customdata:.2f} m"
                        "<br>Centro (%{x:.2f}, %{y:.2f}) m<extra></extra>"
                    ),
                    customdata=[circulo_critico_malha["raio_m"]],
                )
            )

            quantidade_pontos_arco = 121
            x_arco_malha = [
                circulo_critico_malha["x_saida_m"]
                + indice
                * (
                    circulo_critico_malha["x_entrada_m"]
                    - circulo_critico_malha["x_saida_m"]
                )
                / (quantidade_pontos_arco - 1)
                for indice in range(quantidade_pontos_arco)
            ]
            figura_geometria.add_trace(
                go.Scatter(
                    x=x_arco_malha,
                    y=[_cota_arco(circulo_critico_malha, x_m) for x_m in x_arco_malha],
                    mode="lines",
                    line={"color": "#15803d", "width": 3, "dash": "dash"},
                    name=(
                        "Superfície crítica da malha · "
                        f"FS = {circulo_critico_malha['fator_seguranca']:.3f}"
                    ),
                    hovertemplate=(
                        "Superfície crítica da malha"
                        f"<br>FS = {circulo_critico_malha['fator_seguranca']:.3f}"
                        f"<br>R = {circulo_critico_malha['raio_m']:.2f} m"
                        "<br>x = %{x:.2f} m; y = %{y:.2f} m<extra></extra>"
                    ),
                )
            )
            x_meio_arco_critico = (
                circulo_critico_malha["x_saida_m"]
                + circulo_critico_malha["x_entrada_m"]
            ) / 2
            figura_geometria.add_annotation(
                x=x_meio_arco_critico,
                y=_cota_arco(circulo_critico_malha, x_meio_arco_critico),
                text=(
                    "FS mínimo na malha = "
                    f"{circulo_critico_malha['fator_seguranca']:.3f}"
                ),
                showarrow=True,
                arrowcolor="#15803d",
                arrowwidth=1.5,
                arrowhead=2,
                ax=90,
                ay=-55,
                font={"color": "#15803d", "size": 12},
                bgcolor="rgba(255,255,255,0.88)",
                bordercolor="#15803d",
                borderwidth=1,
            )

    comprimento_horizontal_face_m = resultado_talude["geometria"][
        "comprimento_horizontal_face_m"
    ]
    x_saida_m = -float(entradas_talude["distancia_pe_saida_m"])
    x_entrada_m = resultado_talude["geometria"]["coordenada_x_entrada_m"]
    figura_geometria.add_trace(
        go.Scatter(
            x=[x_saida_m, comprimento_horizontal_face_m, x_entrada_m],
            y=[0.0, float(entradas_talude["altura_talude_m"]), resultado_talude["geometria"]["cota_entrada_m"]],
            mode="markers",
            marker={"color": ["#c34b3c", "#17374c", "#c34b3c"], "size": 9},
            hovertext=["Saída", "Crista", "Entrada"],
            name="Pontos principais",
            hovertemplate="%{hovertext}<br>x = %{x:.2f} m<br>y = %{y:.2f} m<extra></extra>",
        )
    )

    if circulo_selecionado and circulo_selecionado["centro_x_m"] is not None:
        quantidade_pontos = 121
        coordenadas_arco_x = [
            x_saida_m + indice * (x_entrada_m - x_saida_m) / (quantidade_pontos - 1)
            for indice in range(quantidade_pontos)
        ]
        coordenadas_arco_y = [
            _cota_arco(circulo_selecionado, x_m) for x_m in coordenadas_arco_x
        ]
        figura_geometria.add_trace(
            go.Scatter(
                x=coordenadas_arco_x,
                y=coordenadas_arco_y,
                mode="lines",
                line={"color": "#c34b3c", "width": 3},
                name=f"Superfície {circulo_selecionado['identificacao']}",
            )
        )

        numero_fatias = int(entradas_talude["quantidade_fatias"])
        largura_total_m = x_entrada_m + float(entradas_talude["distancia_pe_saida_m"])
        passo_horizontal_m = largura_total_m / numero_fatias
        coordenadas_fatias_x: list[float | None] = []
        coordenadas_fatias_y: list[float | None] = []
        for indice_fatia in range(numero_fatias + 1):
            x_fatia_m = x_saida_m + indice_fatia * passo_horizontal_m
            coordenadas_fatias_x.extend([x_fatia_m, x_fatia_m, None])
            coordenadas_fatias_y.extend(
                [_cota_arco(circulo_selecionado, x_fatia_m), _cota_terreno_grafico(x_fatia_m, entradas_talude), None]
            )
        figura_geometria.add_trace(
            go.Scatter(
                x=coordenadas_fatias_x,
                y=coordenadas_fatias_y,
                mode="lines",
                line={"color": "#80918f", "width": 1},
                name="Fatias verticais",
                hoverinfo="skip",
            )
        )

        coordenadas_centro_x = circulo_selecionado["centro_x_m"]
        coordenadas_centro_y = circulo_selecionado["centro_y_m"]
        cota_saida_m = 0.0
        cota_entrada_m = resultado_talude["geometria"]["cota_entrada_m"]
        figura_geometria.add_trace(
            go.Scatter(
                x=[coordenadas_centro_x, x_saida_m, None, coordenadas_centro_x, x_entrada_m],
                y=[coordenadas_centro_y, cota_saida_m, None, coordenadas_centro_y, cota_entrada_m],
                mode="lines",
                line={"color": "#596a77", "width": 1.5, "dash": "dot"},
                name="Raios até a saída e a entrada",
            )
        )
        figura_geometria.add_trace(
            go.Scatter(
                x=[coordenadas_centro_x],
                y=[coordenadas_centro_y],
                mode="markers",
                marker={"color": "#17374c", "size": 9, "symbol": "x"},
                name="Centro C",
                hovertemplate="Centro C<br>x = %{x:.2f} m<br>y = %{y:.2f} m<extra></extra>",
            )
        )

    maior_cota_m = max(coordenadas_perfil_y + [0.0])
    if circulo_selecionado and circulo_selecionado["centro_y_m"] is not None:
        maior_cota_m = max(maior_cota_m, circulo_selecionado["centro_y_m"])
    if busca_centros and circulo_critico_malha:
        cotas_centros_malha_validos = [
            busca_centros["coordenadas_y_m"][indice_y]
            for indice_y, linha_fs in enumerate(
                busca_centros["fatores_seguranca_minimos"]
            )
            if any(fator_seguranca is not None for fator_seguranca in linha_fs)
        ]
        if cotas_centros_malha_validos:
            maior_cota_m = max(maior_cota_m, max(cotas_centros_malha_validos))
    menor_cota_m = min(coordenadas_perfil_y + [0.0])
    if circulo_selecionado and circulo_selecionado["centro_y_m"] is not None:
        menor_cota_m = min(menor_cota_m, *_coordenadas_arco_y(circulo_selecionado))
    faixa_x_grafico_m = max(1.0, x_maximo_m - x_minimo_m)
    limite_y_minimo_m = menor_cota_m - 0.05 * max(1.0, maior_cota_m)
    limite_y_maximo_m = maior_cota_m * 1.1 + 0.1
    faixa_y_grafico_m = max(1.0, limite_y_maximo_m - limite_y_minimo_m)
    altura_area_grafico_px = 700 * faixa_y_grafico_m / faixa_x_grafico_m
    altura_figura_px = min(1450, max(620, int(290 + altura_area_grafico_px)))

    figura_geometria.update_layout(
        title="Perfil, superfícies de ruptura e linhas de mesmo FS",
        height=altura_figura_px,
        margin={"l": 55, "r": 25, "t": 65, "b": 225},
        xaxis_title="Distância horizontal x (m), origem no pé do talude",
        yaxis_title="Cota y (m)",
        legend={
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": -0.28,
            "yanchor": "top",
        },
        hovermode="closest",
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_geometria.update_xaxes(
        range=[x_minimo_m, x_maximo_m],
        zeroline=False,
        scaleanchor="y",
        scaleratio=1,
        constrain="domain",
    )
    figura_geometria.update_yaxes(
        range=[limite_y_minimo_m, limite_y_maximo_m]
    )
    st.plotly_chart(
        figura_geometria,
        width="stretch",
        theme=None,
        config=_configuracao_download_png("perfil_talude"),
    )
    if circulo_critico_malha:
        st.caption(
            "As linhas de mesmo FS interpolam a busca em malha: em cada centro, "
            "foi avaliado o menor FS entre os raios candidatos informados. "
            f"Estrela verde: menor FS encontrado na malha ({circulo_critico_malha['fator_seguranca']:.3f}, "
            f"R = {circulo_critico_malha['raio_m']:.2f} m). A busca complementa a comparação "
            "dos círculos candidatos exibida acima."
        )


def _coordenadas_arco_y(circulo: dict[str, Any]) -> list[float]:
    x_saida_m = circulo["x_saida_m"]
    x_entrada_m = circulo["x_entrada_m"]
    coordenadas_x = [
        x_saida_m + indice * (x_entrada_m - x_saida_m) / 50 for indice in range(51)
    ]
    return [_cota_arco(circulo, x_m) for x_m in coordenadas_x]


def _mostrar_grafico_fator_raio(
    circulos: list[dict[str, Any]], identificacao_critica: str | None, fs_maximo_grafico: float
) -> None:
    circulos_validos = sorted(
        (circulo for circulo in circulos if circulo["situacao"] == "VÁLIDO"),
        key=lambda circulo: circulo["raio_m"],
    )
    figura_fs_raio = go.Figure()
    cores_pontos = [
        "#c34b3c" if circulo["identificacao"] == identificacao_critica else "#176452"
        for circulo in circulos_validos
    ]
    textos_pontos = [
        f"{circulo['identificacao']} · crítico"
        if circulo["identificacao"] == identificacao_critica
        else circulo["identificacao"]
        for circulo in circulos_validos
    ]
    figura_fs_raio.add_trace(
        go.Scatter(
            x=[circulo["raio_m"] for circulo in circulos_validos],
            y=[circulo["fator_seguranca"] for circulo in circulos_validos],
            mode="markers",
            marker={"color": cores_pontos, "size": 10, "line": {"color": "white", "width": 1}},
            text=textos_pontos,
            name="Círculos válidos",
            hovertemplate="%{text}<br>R = %{x:.3f} m<br>FS = %{y:.3f}<extra></extra>",
        )
    )
    figura_fs_raio.update_layout(
        title="Comparação do fator de segurança por raio",
        height=440,
        margin={"l": 18, "r": 18, "t": 55, "b": 35},
        xaxis_title="Raio R (m)",
        yaxis_title="Fator de segurança, FS",
        showlegend=False,
        hovermode="closest",
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_fs_raio.update_yaxes(range=[0, fs_maximo_grafico], rangemode="tozero")
    st.plotly_chart(
        figura_fs_raio,
        width="stretch",
        theme=None,
        config=_configuracao_download_png("fator_seguranca_por_raio"),
    )


def _mostrar_grafico_angulos(fatias: list[dict[str, Any]]) -> None:
    numeros_fatias = [fatia["numero_fatia"] for fatia in fatias]
    angulos_iniciais = [fatia["angulo_base_inicial_graus"] for fatia in fatias]
    angulos_finais = [fatia["angulo_base_final_graus"] for fatia in fatias]
    figura_angulos = go.Figure()
    figura_angulos.add_trace(
        go.Scatter(
            x=numeros_fatias,
            y=angulos_iniciais,
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    figura_angulos.add_trace(
        go.Scatter(
            x=numeros_fatias,
            y=angulos_finais,
            mode="lines",
            line={"color": "#d99028", "width": 1},
            fill="tonexty",
            fillcolor="rgba(217, 144, 40, 0.18)",
            name="Faixa entre α₁ e α₂",
            customdata=list(zip(angulos_iniciais, angulos_finais)),
            hovertemplate="Fatia %{x}<br>α₁: %{customdata[0]:.2f}°<br>α₂: %{customdata[1]:.2f}°<extra></extra>",
        )
    )
    figura_angulos.add_trace(
        go.Scatter(
            x=numeros_fatias,
            y=[fatia["angulo_base_medio_graus"] for fatia in fatias],
            mode="lines+markers",
            name="α médio usado no cálculo",
            line={"color": "#176452", "width": 3},
            marker={"size": 7},
            hovertemplate="Fatia %{x}<br>α médio: %{y:.2f}°<extra></extra>",
        )
    )
    figura_angulos.add_hline(y=0, line_color="#829096", line_dash="dash", line_width=1)
    figura_angulos.update_layout(
        title="Inclinação da base de cada fatia",
        height=420,
        margin={"l": 55, "r": 25, "t": 55, "b": 170},
        xaxis_title="Número da fatia, da saída à entrada",
        yaxis_title="Ângulo da base α (°)",
        hovermode="closest",
        legend={"orientation": "h", "x": 0, "xanchor": "left", "y": -0.30, "yanchor": "top"},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_angulos.update_xaxes(dtick=1)
    st.plotly_chart(
        figura_angulos,
        width="stretch",
        theme=None,
        config=_configuracao_download_png("angulos_das_fatias"),
    )


def _mostrar_grafico_componentes_normais(fatias: list[dict[str, Any]]) -> None:
    numeros_fatias = [fatia["numero_fatia"] for fatia in fatias]
    figura_normais = go.Figure()
    for campo, nome, cor in (
        ("forca_normal_total_kN_m", "W cos α · normal total", "#58758a"),
        ("resultante_pressao_neutra_kN_m", "u ΔL · efeito da água", "#3e8dc1"),
        ("forca_normal_efetiva_kN_m", "N′ · normal efetiva", "#176452"),
    ):
        valores = [fatia[campo] for fatia in fatias]
        cores = (
            ["#c34b3c" if valor is not None and valor < 0 else cor for valor in valores]
            if campo == "forca_normal_efetiva_kN_m"
            else cor
        )
        figura_normais.add_trace(
            go.Bar(
                x=numeros_fatias,
                y=valores,
                name=nome,
                marker_color=cores,
                hovertemplate="Fatia %{x}<br>" + nome + ": %{y:.2f} kN/m<extra></extra>",
            )
        )
    figura_normais.update_layout(
        title="Como a água altera a força normal em cada fatia",
        height=440,
        margin={"l": 55, "r": 25, "t": 55, "b": 185},
        barmode="group",
        xaxis_title="Número da fatia, da saída à entrada",
        yaxis_title="Força (kN/m)",
        hovermode="closest",
        legend={"orientation": "h", "x": 0, "xanchor": "left", "y": -0.34, "yanchor": "top"},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_normais.update_xaxes(dtick=1)
    figura_normais.add_hline(y=0, line_color="#829096", line_dash="dash", line_width=1)
    st.plotly_chart(
        figura_normais,
        width="stretch",
        theme=None,
        config=_configuracao_download_png("componentes_forca_normal"),
    )


def _mostrar_grafico_forcas_por_fatia(fatias: list[dict[str, Any]]) -> None:
    numeros_fatias = [fatia["numero_fatia"] for fatia in fatias]
    valores_mobilizados = [fatia["forca_mobilizada_kN_m"] for fatia in fatias]
    figura_forcas = go.Figure()
    figura_forcas.add_trace(
        go.Bar(
            x=numeros_fatias,
            y=[fatia["forca_resistente_kN_m"] for fatia in fatias],
            name="F_R · força resistente",
            marker_color="#176452",
            hovertemplate="Fatia %{x}<br>F_R: %{y:.2f} kN/m<extra></extra>",
        )
    )
    figura_forcas.add_trace(
        go.Bar(
            x=numeros_fatias,
            y=valores_mobilizados,
            name="F_mob · força mobilizada",
            marker_color=[
                "#c34b3c" if valor < 0 else "#d99028" for valor in valores_mobilizados
            ],
            hovertemplate="Fatia %{x}<br>F_mob: %{y:.2f} kN/m<extra></extra>",
        )
    )
    figura_forcas.update_layout(
        title="Forças resistentes e mobilizadas por fatia",
        height=440,
        margin={"l": 55, "r": 25, "t": 55, "b": 170},
        barmode="group",
        xaxis_title="Número da fatia, da saída à entrada",
        yaxis_title="Força (kN/m)",
        hovermode="closest",
        legend={"orientation": "h", "x": 0, "xanchor": "left", "y": -0.30, "yanchor": "top"},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_forcas.update_xaxes(dtick=1)
    figura_forcas.add_hline(y=0, line_color="#829096", line_dash="dash", line_width=1)
    st.plotly_chart(
        figura_forcas,
        width="stretch",
        theme=None,
        config=_configuracao_download_png("forcas_por_fatia"),
    )


def _mostrar_tabela_fatias(fatias: list[dict[str, Any]]) -> None:
    tabelas = (
        (
            "Posição",
            "x é medido na horizontal, com origem no pé do talude; as cotas são medidas a partir do pé.",
            {
                "numero_fatia": "Fatia",
                "x_inicial_m": "x inicial (m)",
                "x_final_m": "x final (m)",
                "x_medio_m": "x médio (m)",
                "cota_topo_m": "Cota do terreno (m)",
                "cota_base_m": "Cota da base no meio (m)",
            },
        ),
        (
            "Ângulos e base",
            "α₁ e α₂ são os ângulos no começo e no fim da base; ΔL é o comprimento curvo da base.",
            {
                "numero_fatia": "Fatia",
                "angulo_base_inicial_graus": "α₁ · início (°)",
                "angulo_base_final_graus": "α₂ · fim (°)",
                "angulo_base_medio_graus": "α médio (°)",
                "variacao_angular_rad": "Δα (rad)",
                "comprimento_arco_m": "ΔL · arco da base (m)",
                "comprimento_camada_superior_m": "L₁ · base na camada 1 (m)",
                "comprimento_camada_inferior_m": "L₂ · base na camada 2 (m)",
            },
        ),
        (
            "Áreas e peso",
            "A₁/A₂ são áreas dentro de cada camada; W soma o peso do solo e a sobrecarga daquela fatia.",
            {
                "numero_fatia": "Fatia",
                "area_camada_superior_nao_saturada_m2": "A₁ não saturada (m²)",
                "area_camada_superior_saturada_m2": "A₁ saturada (m²)",
                "area_camada_inferior_nao_saturada_m2": "A₂ não saturada (m²)",
                "area_camada_inferior_saturada_m2": "A₂ saturada (m²)",
                "sobrecarga_fatia_kN_m": "q · largura na fatia (kN/m)",
                "peso_fatia_kN_m": "W · peso total (kN/m)",
            },
        ),
        (
            "Forças",
            "As forças são por metro de largura do talude. ‘—’ significa que aquela parcela não é calculada.",
            {
                "numero_fatia": "Fatia",
                "forca_normal_total_kN_m": "W cos α (kN/m)",
                "pressao_neutra_kPa": "u · pressão da água (kPa)",
                "resultante_pressao_neutra_kN_m": "u ΔL (kN/m)",
                "forca_normal_efetiva_kN_m": "N′ (N-linha) · normal efetiva (kN/m)",
                "forca_resistente_coesao_kN_m": "Parcela de coesão (kN/m)",
                "forca_resistente_atrito_kN_m": "Parcela de atrito (kN/m)",
                "forca_resistente_kN_m": "F_R · resistente (kN/m)",
                "forca_mobilizada_kN_m": "F_mob · mobilizada (kN/m)",
                "situacao": "Situação da fatia",
            },
        ),
    )
    abas_tabela = st.tabs([titulo for titulo, _, _ in tabelas])
    for aba, (_, explicacao, nomes_colunas) in zip(abas_tabela, tabelas):
        with aba:
            st.caption(explicacao)
            linhas_tabela = [
                {nome_coluna: fatia.get(campo) for campo, nome_coluna in nomes_colunas.items()}
                for fatia in fatias
            ]
            st.dataframe(linhas_tabela, hide_index=True, width="stretch", height=440)


def _mostrar_diagnostico_circulo(circulo: dict[str, Any]) -> None:
    if circulo["situacao"] == "VÁLIDO":
        return

    fatias = circulo["fatias"]
    fatias_normais_negativas = [
        fatia for fatia in fatias if fatia["situacao"] == "N EFETIVA NEGATIVA"
    ]
    st.warning(
        f"O {circulo['identificacao']} não tem FS válido: {circulo['situacao']}. "
        "Veja o motivo antes de comparar este círculo com os válidos."
    )
    if circulo["situacao"] == "RAIO < d/2":
        st.info("Para passar pelos pontos de entrada e saída, o raio precisa ser pelo menos d/2.")
    elif circulo["situacao"] == "FORA DO MACIÇO":
        numeros_fatias_fora = [
            str(fatia["numero_fatia"])
            for fatia in fatias
            if fatia["situacao"] == "FORA DO MACIÇO"
        ]
        st.info(
            "A superfície ficou acima do terreno ou fora do solo nas fatias: "
            + (", ".join(numeros_fatias_fora) if numeros_fatias_fora else "geometria do círculo")
            + "."
        )
    elif circulo["situacao"] == "Fmob ≤ 0":
        st.info("A soma assinada das forças mobilizadas não é positiva; o FS não é definido nesse sentido.")
    if fatias_normais_negativas:
        lista_fatias = ", ".join(str(fatia["numero_fatia"]) for fatia in fatias_normais_negativas)
        quantidade_fatias_validas = sum(fatia["situacao"] == "OK" for fatia in fatias)
        resistencia_parcial = circulo["soma_forcas_resistentes_diagnostica_kN_m"]
        mobilizacao_diagnostica = circulo["soma_forcas_mobilizadas_diagnostica_kN_m"]
        st.info(
            f"N′ (lido ‘N linha’) ficou negativo. Fatias afetadas: {lista_fatias}. "
            "A conta exigiria tração na base, que o solo não resiste. "
            "Por isso a planilha e o Python deixam o FS em branco."
        )
        for fatia in fatias_normais_negativas:
            st.write(
                f"Fatia {fatia['numero_fatia']}: W cos α = "
                f"{_formatar_numero(fatia['forca_normal_total_kN_m'], 2)} − u ΔL = "
                f"{_formatar_numero(fatia['resultante_pressao_neutra_kN_m'], 2)} = "
                f"N′ = {_formatar_numero(fatia['forca_normal_efetiva_kN_m'], 2)} kN/m; "
                f"F_R não calculada; F_mob = "
                f"{_formatar_numero(fatia['forca_mobilizada_kN_m'], 2)} kN/m."
            )
        st.caption(
            f"Só para diagnóstico: ΣF_R das {quantidade_fatias_validas} fatias válidas = "
            f"{_formatar_numero(resistencia_parcial, 2)} kN/m; ΣF_mob das {len(fatias)} fatias = "
            f"{_formatar_numero(mobilizacao_diagnostica, 2)} kN/m. "
            "Como as somas usam conjuntos diferentes de fatias, a divisão não é um FS válido."
        )


def _mostrar_memoria_calculo() -> None:
    with st.expander("Guia de símbolos e equações"):
        st.markdown(
            "**Geometria:** H é a altura; H:V é a relação horizontal/vertical da face; "
            "β é a inclinação do terreno a montante; a é a distância da crista até a entrada; "
            "Lb é a distância do pé até a saída; xE e yE são as coordenadas da entrada; "
            "R é o raio; d é a distância entre entrada e saída."
        )
        st.markdown(
            "**Solo e água:** h₁ é a espessura da camada 1; γ é o peso específico natural ou saturado; "
            "c′ é a coesão efetiva; φ′ é o ângulo de atrito efetivo; q é a sobrecarga; "
            "zNA é a profundidade do N.A. abaixo da crista."
        )
        st.markdown(
            "**Como ler as colunas:** W é o peso da fatia; α é a inclinação da base; "
            "u é a pressão da água na base; ΔL é o comprimento curvo da base; "
            "L₁ e L₂ são os trechos da base em cada camada. Todas as forças são por metro de largura."
        )
        st.markdown(
            "**N′ (N linha):** força normal efetiva na base, depois de descontar a água. "
            "**F_R:** força resistente, formada pelas parcelas de coesão e atrito. "
            "**F_mob:** força que tende a movimentar a fatia. FS só é exibido quando todas as fatias do círculo são válidas."
        )
        st.markdown("**Geometria e divisão em fatias**")
        st.latex(r"x_E = (H:V)\,H+a \qquad d=\sqrt{(x_E+L_b)^2+y_E^2}")
        st.latex(r"\alpha_{1,i}=\sin^{-1}\!\left(\frac{x_{1,i}-x_c}{R}\right) \qquad \alpha_{2,i}=\sin^{-1}\!\left(\frac{x_{2,i}-x_c}{R}\right)")
        st.latex(r"\alpha_i=\frac{\alpha_{1,i}+\alpha_{2,i}}{2} \qquad \Delta\alpha_i=|\operatorname{rad}(\alpha_{2,i}-\alpha_{1,i})| \qquad \Delta L_i=R\,\Delta\alpha_i")
        st.markdown("**Peso e força normal**")
        st.latex(r"W_i=\sum_j(\gamma_{j,nat}A_{j,nat}+\gamma_{j,sat}A_{j,sat})+q\,b_{q,i}")
        st.latex(r"y_{NA}=H-z_{NA} \qquad u_i=\gamma_w\max(0;y_{NA}-y_{base,i})")
        st.latex(r"N'_i=W_i\cos\alpha_i-u_i\Delta L_i")
        st.markdown("**Resistência, movimento e fator de segurança**")
        st.latex(r"F_{coesao,i}=c'_1L_{1,i}+c'_2L_{2,i}")
        st.latex(r"F_{atrito,i}=N'_i\left(\frac{L_{1,i}}{\Delta L_i}\tan\varphi'_1+\frac{L_{2,i}}{\Delta L_i}\tan\varphi'_2\right)")
        st.latex(r"F_{R,i}=F_{coesao,i}+F_{atrito,i} \qquad F_{mob,i}=W_i\sin\alpha_i")
        st.latex(r"FS=\frac{\sum_i F_{R,i}}{\sum_i F_{mob,i}}")
        st.markdown(
            "O sinal de α é mantido na força mobilizada. Se N′ ficar negativo em uma fatia, "
            "o círculo é marcado como inválido e não recebe FS, como na aba Talude da planilha. "
            "O N.A. é horizontal; deixe o campo vazio para não considerar água."
        )


armazenamento_local = LocalStorage(key="armazenamento_taludes")
aviso_armazenamento = None
if "dados_talude_inicializados" not in st.session_state:
    texto_salvo = armazenamento_local.getItem(CHAVE_ARMAZENAMENTO_NAVEGADOR)
    try:
        dados_salvos = json.loads(texto_salvo) if isinstance(texto_salvo, str) else texto_salvo
    except (json.JSONDecodeError, TypeError):
        dados_salvos = None
        aviso_armazenamento = "O rascunho salvo não pôde ser lido; carreguei o exemplo da planilha."
    dados_iniciais = _normalizar_dados(dados_salvos)
    _aplicar_dados_dos_widgets(dados_iniciais)
    st.session_state[CHAVE_ESTADO_DA_SESSAO] = dados_iniciais
    st.session_state["dados_talude_inicializados"] = True
else:
    dados_da_sessao = st.session_state.get(CHAVE_ESTADO_DA_SESSAO)
    if isinstance(dados_da_sessao, dict) and any(
        campo not in st.session_state for campo in CAMPOS_FORMULARIO + CHAVES_RAIOS_CANDIDATOS
    ):
        _aplicar_dados_dos_widgets(dados_da_sessao)


st.markdown("<style>.block-container{padding-top:1.5rem;padding-bottom:3rem}</style>", unsafe_allow_html=True)
st.title("◢ Estabilidade de taludes")
st.caption(
    "Método das fatias de Fellenius · superfície circular · até duas camadas · "
    "cálculo por metro de largura."
)
st.info(
    "Informe a geometria, água e parâmetros do solo para comparar os raios circulares pelo método "
    "de Fellenius. Veja o FS de cada círculo, a busca complementar em malha, as fatias e o perfil; "
    "o CAD pode ser baixado para o círculo selecionado."
)
if aviso_armazenamento:
    st.warning(aviso_armazenamento)
with st.expander("Sobre o salvamento dos dados"):
    st.write(
        "As entradas ficam no armazenamento local deste navegador e na sessão. "
        "Elas voltam ao reabrir esta página no mesmo navegador e dispositivo; "
        "não são sincronizadas entre dispositivos."
    )

coluna_botao_exemplo, coluna_referencia = st.columns([1, 2])
with coluna_botao_exemplo:
    st.button("Restaurar exemplo da planilha", on_click=_restaurar_exemplo, use_container_width=True)
with coluna_referencia:
    st.caption("Exemplo: H = 8 m · H:V = 1,5 · N.A. a 7,8 m da crista · 20 fatias")

with st.container(border=True):
    st.subheader("Geometria, água e discretização")
    entradas_atuais_croqui = _capturar_dados_dos_widgets()
    resultado_croqui = None
    if not validar_entradas_talude(entradas_atuais_croqui):
        resultado_croqui = calcular_estabilidade_talude(entradas_atuais_croqui)
        _mostrar_croqui_entrada_talude(
            entradas_atuais_croqui,
            resultado_croqui["geometria"],
            resultado_croqui["circulo_critico"],
        )
    colunas_geometria = st.columns(4)
    colunas_geometria[0].number_input(
        "Altura do talude, H (m)", min_value=0.1, step=0.1, key="altura_talude_m"
    )
    colunas_geometria[1].number_input(
        "Face H:V (horizontal/vertical)", min_value=0.01, step=0.1,
        key="relacao_horizontal_vertical_face",
    )
    colunas_geometria[2].number_input(
        "Terreno a montante, β (°)", min_value=-45.0, max_value=45.0, step=1.0,
        key="inclinacao_terreno_montante_graus",
    )
    colunas_geometria[3].number_input(
        "Distância da crista à entrada, a (m)", step=0.1,
        key="distancia_crista_entrada_m",
        help="Positiva depois da crista; negativa sobre a face do talude.",
    )
    colunas_geometria_2 = st.columns(4)
    colunas_geometria_2[0].number_input(
        "Espessura da camada 1, h₁ (m)", min_value=0.01, step=0.1,
        max_value=1000.0,
        key="espessura_camada_superior_m",
    )
    colunas_geometria_2[1].number_input(
        "N.A. abaixo da crista, zNA (m)", min_value=0.0, step=0.1, value=None,
        placeholder="Vazio = sem N.A.", key="profundidade_nivel_agua_abaixo_crista_m",
    )
    colunas_geometria_2[2].number_input(
        "Sobrecarga na crista, q (kPa)", min_value=0.0, step=1.0,
        key="sobrecarga_crista_kPa",
    )
    colunas_geometria_2[3].number_input(
        "Número de fatias", min_value=4, max_value=50, step=1, key="quantidade_fatias"
    )
    colunas_geometria_3 = st.columns(4)
    colunas_geometria_3[0].number_input(
        "Peso específico da água, γw (kN/m³)", min_value=0.1, step=0.1,
        key="peso_especifico_agua_kN_m3",
    )
    colunas_geometria_3[1].number_input(
        "Distância pé–saída, Lb (m)", min_value=0.0, step=0.1,
        key="distancia_pe_saida_m",
    )
    colunas_geometria_3[2].number_input(
        "X mínimo do gráfico (m)", step=0.5, key="limite_x_grafico_minimo_m"
    )
    colunas_geometria_3[3].number_input(
        "X máximo do gráfico (m)", step=0.5, key="limite_x_grafico_maximo_m"
    )

entradas_formulario = _capturar_dados_dos_widgets()
erros_formulario_geometria = validar_entradas_talude(entradas_formulario)
if not erros_formulario_geometria:
    geometria_entrada = calcular_geometria_talude(entradas_formulario)
    st.caption(
        f"Face θ = {_formatar_numero(geometria_entrada['inclinacao_face_graus'], 2)}° · "
        f"ponto de entrada: xE = {_formatar_numero(geometria_entrada['coordenada_x_entrada_m'], 3)} m, "
        f"yE = {_formatar_numero(geometria_entrada['cota_entrada_m'], 3)} m · "
        f"d = {_formatar_numero(geometria_entrada['distancia_entre_entrada_e_saida_m'], 3)} m"
    )

with st.container(border=True):
    st.subheader("Propriedades das camadas")
    st.caption("A camada 1 fica acima da interface; a camada 2 fica abaixo. Para solo homogêneo, repita os parâmetros nas duas camadas.")
    coluna_camada_superior, coluna_camada_inferior = st.columns(2)
    with coluna_camada_superior:
        st.markdown("**Camada 1**")
        entradas_superior = st.columns(4)
        entradas_superior[0].number_input(
            "γ natural (kN/m³)", min_value=0.1, step=0.5,
            key="peso_especifico_natural_camada_superior_kN_m3",
        )
        entradas_superior[1].number_input(
            "γ saturado (kN/m³)", min_value=0.1, step=0.5,
            key="peso_especifico_saturado_camada_superior_kN_m3",
        )
        entradas_superior[2].number_input(
            "c′ (kPa)", min_value=0.0, step=1.0,
            key="coesao_efetiva_camada_superior_kPa",
        )
        entradas_superior[3].number_input(
            "φ′ (°)", min_value=0.0, max_value=89.9, step=1.0,
            key="angulo_atrito_efetivo_camada_superior_graus",
        )
    with coluna_camada_inferior:
        st.markdown("**Camada 2**")
        entradas_inferior = st.columns(4)
        entradas_inferior[0].number_input(
            "γ natural (kN/m³)", min_value=0.1, step=0.5,
            key="peso_especifico_natural_camada_inferior_kN_m3",
        )
        entradas_inferior[1].number_input(
            "γ saturado (kN/m³)", min_value=0.1, step=0.5,
            key="peso_especifico_saturado_camada_inferior_kN_m3",
        )
        entradas_inferior[2].number_input(
            "c′ (kPa)", min_value=0.0, step=1.0,
            key="coesao_efetiva_camada_inferior_kPa",
        )
        entradas_inferior[3].number_input(
            "φ′ (°)", min_value=0.0, max_value=89.9, step=1.0,
            key="angulo_atrito_efetivo_camada_inferior_graus",
        )

with st.expander("Raios candidatos (gerados a partir de d/2; editáveis)"):
    st.caption("Os raios do exemplo da planilha usam incrementos diferentes. Gere novamente após mudar a geometria, ou ajuste cada raio.")
    st.button("Gerar raios padrão para esta geometria", on_click=_regenerar_raios_padrao)
    colunas_raios = st.columns(5)
    for indice_raio, chave_raio in enumerate(CHAVES_RAIOS_CANDIDATOS):
        with colunas_raios[indice_raio % 5]:
            st.number_input(
                f"R{indice_raio + 1:02d} (m)", min_value=0.0, step=0.5,
                key=chave_raio,
            )

entradas_talude = _capturar_dados_dos_widgets()
st.session_state[CHAVE_ESTADO_DA_SESSAO] = entradas_talude
armazenamento_local.setItem(
    CHAVE_ARMAZENAMENTO_NAVEGADOR,
    json.dumps(entradas_talude, ensure_ascii=False),
    key="salvar_entradas_talude",
)

erros_entrada = validar_entradas_talude(entradas_talude)
if erros_entrada:
    st.error("Revise as entradas antes de consultar os resultados.")
    for erro in erros_entrada:
        st.markdown(f"- {erro}")
else:
    resultado_talude = resultado_croqui or calcular_estabilidade_talude(entradas_talude)
    circulos = resultado_talude["circulos"]
    circulo_critico = resultado_talude["circulo_critico"]
    opcoes_circulos = ["Crítico"] + [circulo["identificacao"] for circulo in circulos]
    identificacao_desenho = st.selectbox(
        "Círculo para analisar",
        opcoes_circulos,
        key="identificacao_circulo_desenho_talude",
        help="Escolha um candidato para ver seu perfil, suas fatias e os motivos de invalidação.",
    )
    if identificacao_desenho == "Crítico":
        circulo_desenhado = circulo_critico
    else:
        circulo_desenhado = next(
            circulo
            for circulo in circulos
            if circulo["identificacao"] == identificacao_desenho
        )

    st.divider()
    st.subheader("Comparação dos círculos candidatos")
    linhas_circulos = [
        {
            "ID": circulo["identificacao"],
            "Raio R (m)": circulo["raio_m"],
            "Centro x_c (m)": circulo["centro_x_m"],
            "Centro y_c (m)": circulo["centro_y_m"],
            "FS · Fellenius": _formatar_numero(circulo["fator_seguranca"], 3),
            "Σ F_R válida (kN/m)": _formatar_numero(circulo["resistencia_total_kN_m"], 2),
            "Σ F_mob válida (kN/m)": _formatar_numero(circulo["forca_mobilizada_total_kN_m"], 2),
            "Situação": circulo["situacao"],
        }
        for circulo in circulos
    ]
    st.dataframe(linhas_circulos, hide_index=True, width="stretch")
    st.caption(
        "Só círculos com situação VÁLIDO recebem FS e somatórios totais. "
        "Selecione um círculo inválido para ver a fatia e o motivo; ele não entra no gráfico FS × raio."
    )

    if circulo_critico:
        colunas_resultado = st.columns(4)
        colunas_resultado[0].metric(
            "FS crítico · Fellenius", _formatar_numero(circulo_critico["fator_seguranca"])
        )
        colunas_resultado[1].metric(
            "Raio crítico", f"{_formatar_numero(circulo_critico['raio_m'])} m"
        )
        colunas_resultado[2].metric(
            "Centro x_c", f"{_formatar_numero(circulo_critico['centro_x_m'])} m"
        )
        colunas_resultado[3].metric(
            "Centro y_c", f"{_formatar_numero(circulo_critico['centro_y_m'])} m"
        )
        if circulo_desenhado and circulo_desenhado["situacao"] == "VÁLIDO":
            arquivo_dxf_talude = gerar_desenho_talude_dxf(
                entradas_talude, resultado_talude, circulo_desenhado
            )
            st.download_button(
                "Baixar CAD do círculo selecionado (.dxf)",
                data=arquivo_dxf_talude,
                file_name=(
                    f"perfil_talude_{circulo_desenhado['identificacao'].lower()}.dxf"
                ),
                mime="application/dxf",
                help="O DXF usa o círculo escolhido no campo 'Círculo para analisar'. Inclui o perfil, as fatias e a memória completa.",
                key="baixar_dxf_circulo_selecionado_talude",
            )
            st.caption(
                "No DXF, a camada AREA_CONFERENCIA contém uma polilinha fechada por fatia. "
                "Use AREA > Objeto e compare com Atotal de cada fatia no memorial."
            )
        elif circulo_desenhado:
            st.info(
                "O CAD fica disponível para círculos válidos. Este raio foi marcado como "
                f"{circulo_desenhado['situacao']} e não entra no cálculo do FS crítico."
            )
    else:
        st.warning("Nenhum dos raios candidatos produziu um círculo válido. Ajuste os raios ou a geometria.")

    if circulo_desenhado:
        _mostrar_diagnostico_circulo(circulo_desenhado)
        st.subheader(f"Perfil e círculo · {circulo_desenhado['identificacao']}")
        _mostrar_grafico_geometria(entradas_talude, resultado_talude, circulo_desenhado)

        st.subheader("Fator de segurança por raio")
        st.caption(
            "Cada ponto representa um dos raios candidatos válidos; o gráfico não liga os pontos "
            "porque são círculos discretos, não uma curva contínua. O ponto vermelho marca o círculo crítico. "
            "Passe o mouse no gráfico para baixar PNG."
        )
        limite_fs_grafico = st.slider(
            "Limite superior do eixo FS", min_value=1.0, max_value=20.0, value=5.0, step=0.5
        )
        _mostrar_grafico_fator_raio(
            circulos,
            circulo_critico["identificacao"] if circulo_critico else None,
            limite_fs_grafico,
        )

        if circulo_desenhado["fatias"]:
            st.subheader(f"Gráficos por fatia · {circulo_desenhado['identificacao']}")
            st.caption(
                "Cada gráfico mostra uma parte do cálculo. Use o ícone de câmera ao passar o mouse "
                "sobre qualquer gráfico para baixar sua imagem PNG."
            )
            with st.expander("Ângulos e forças em gráficos separados", expanded=False):
                st.markdown("**Ângulos da base**")
                st.caption("α₁ e α₂ marcam o início e o fim da base; α médio é usado nas forças.")
                _mostrar_grafico_angulos(circulo_desenhado["fatias"])
                st.markdown("**Componentes da força normal**")
                st.caption("N′ = W cos α − u ΔL. Barras vermelhas indicam N′ negativo.")
                _mostrar_grafico_componentes_normais(circulo_desenhado["fatias"])
                st.markdown("**Forças resistentes e mobilizadas**")
                st.caption(
                    "F_R resiste ao movimento; F_mob tende a movimentar a fatia. "
                    "F_mob negativa aparece em vermelho e atua contra o sentido adotado."
                )
                _mostrar_grafico_forcas_por_fatia(circulo_desenhado["fatias"])

            st.subheader(f"Memória das fatias · {circulo_desenhado['identificacao']}")
            _mostrar_tabela_fatias(circulo_desenhado["fatias"])
        else:
            st.info("Este raio é menor que d/2; não existe círculo para dividir em fatias.")
    _mostrar_memoria_calculo()
    st.caption(
        "Escopo: ruptura circular por Fellenius, N.A. horizontal e até duas camadas. "
        "Não inclui Bishop, superfícies não circulares, sismo, fluxo não hidrostático "
        "ou busca automática dos pontos de entrada e saída."
    )
