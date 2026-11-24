from __future__ import annotations

import json
from copy import deepcopy
from html import escape
from math import ceil
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from streamlit_local_storage import LocalStorage

from contencoes.calculos_estaca_prancha import (
    calcular_cortina_ancorada,
    calcular_cortina_em_balanco,
    carregar_exemplos_estaca_prancha,
    validar_entradas_cortina_ancorada,
    validar_entradas_cortina_em_balanco,
)


st.set_page_config(page_title="Estaca-prancha | Contenções", page_icon="📐", layout="wide")

CHAVE_ARMAZENAMENTO_NAVEGADOR = "projeto_contencoes_estaca_prancha_v1"
CHAVE_ESTADO_DA_SESSAO = "dados_estaca_prancha_preservados_na_sessao"
CAMPOS_CORTINA_EM_BALANCO = (
    "altura_livre_escavacao_m",
    "peso_especifico_solo_kN_m3",
    "angulo_atrito_solo_graus",
    "percentual_passivo_mobilizado",
    "percentual_acrescimo_ficha",
)
CAMPOS_CORTINA_ANCORADA = (
    "sobrecarga_superficie_kPa",
    "espessura_camada_superior_ate_na_m",
    "peso_especifico_solo_superior_kN_m3",
    "peso_especifico_solo_submerso_kN_m3",
    "profundidade_na_ate_escavacao_m",
    "ficha_abaixo_escavacao_m",
    "angulo_atrito_solo_graus",
    "altura_ancoragem_acima_na_m",
    "percentual_passivo_mobilizado",
    "fator_seguranca_minimo_tombamento",
)


def _chave_widget(nome_caso: str, nome_campo: str) -> str:
    return f"estaca_{nome_caso}_{nome_campo}"


def _normalizar_dados_salvos(dados_salvos: Any) -> dict[str, dict[str, float]]:
    dados = carregar_exemplos_estaca_prancha()
    if not isinstance(dados_salvos, dict):
        return dados

    for nome_caso, campos_caso in (
        ("cortina_em_balanco", CAMPOS_CORTINA_EM_BALANCO),
        ("cortina_ancorada", CAMPOS_CORTINA_ANCORADA),
    ):
        valores_salvos = dados_salvos.get(nome_caso)
        if isinstance(valores_salvos, dict):
            for nome_campo in campos_caso:
                valor = valores_salvos.get(nome_campo)
                if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                    dados[nome_caso][nome_campo] = valor
    return dados


def _aplicar_dados_aos_widgets(dados: dict[str, dict[str, float]]) -> None:
    for nome_caso, campos_caso in (
        ("cortina_em_balanco", CAMPOS_CORTINA_EM_BALANCO),
        ("cortina_ancorada", CAMPOS_CORTINA_ANCORADA),
    ):
        for nome_campo in campos_caso:
            st.session_state[_chave_widget(nome_caso, nome_campo)] = dados[nome_caso][
                nome_campo
            ]


def _restaurar_exemplos() -> None:
    _aplicar_dados_aos_widgets(carregar_exemplos_estaca_prancha())


def _capturar_dados_dos_widgets() -> dict[str, dict[str, Any]]:
    dados: dict[str, dict[str, Any]] = {}
    for nome_caso, campos_caso in (
        ("cortina_em_balanco", CAMPOS_CORTINA_EM_BALANCO),
        ("cortina_ancorada", CAMPOS_CORTINA_ANCORADA),
    ):
        dados[nome_caso] = {
            nome_campo: st.session_state.get(_chave_widget(nome_caso, nome_campo))
            for nome_campo in campos_caso
        }
    return dados


def _formatar_numero(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _svg_texto(
    x: float,
    y: float,
    texto: str,
    *,
    tamanho: int = 16,
    peso: int = 400,
    ancora: str = "start",
    cor: str = "#26383f",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{ancora}" '
        f'font-family="sans-serif" font-size="{tamanho}" font-weight="{peso}" '
        f'fill="{cor}">{escape(texto)}</text>'
    )


def _svg_linha(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    cor: str = "#46565d",
    largura: float = 2,
    tracejado: str | None = None,
) -> str:
    tracejado_svg = f' stroke-dasharray="{tracejado}"' if tracejado else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{cor}" stroke-width="{largura:.1f}"{tracejado_svg} />'
    )


def _svg_cota_vertical(x: float, y1: float, y2: float, texto: str) -> str:
    topo, base = sorted((y1, y2))
    meio = (topo + base) / 2
    if base - topo < 18:
        return (
            _svg_linha(x, topo, x, base, cor="#34566a", largura=1.5)
            + _svg_texto(x - 10, meio - 5, texto, tamanho=14, ancora="end", cor="#244c62")
        )
    return "".join(
        (
            _svg_linha(x, topo + 7, x, base - 7, cor="#34566a", largura=1.5),
            f'<path d="M {x - 5:.1f} {topo + 8:.1f} L {x:.1f} {topo:.1f} '
            f'L {x + 5:.1f} {topo + 8:.1f} M {x - 5:.1f} {base - 8:.1f} '
            f'L {x:.1f} {base:.1f} L {x + 5:.1f} {base - 8:.1f}" '
            'fill="none" stroke="#34566a" stroke-width="1.5" />',
            _svg_texto(x - 10, meio + 5, texto, tamanho=14, ancora="end", cor="#244c62"),
        )
    )


def _svg_painel(x: float, y: float, linhas: list[str], *, largura: float = 265) -> str:
    altura = 24 + 23 * len(linhas)
    partes = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{largura:.1f}" height="{altura:.1f}" '
        'rx="8" fill="#fffdf8" stroke="#cbbfa8" stroke-width="1" />'
    ]
    for indice, texto in enumerate(linhas):
        partes.append(
            _svg_texto(
                x + 12,
                y + 22 + 23 * indice,
                texto,
                tamanho=14 if indice else 15,
                peso=500 if indice == 0 else 400,
            )
        )
    return "".join(partes)


def _mostrar_perfil_cortina_em_balanco(
    entradas: dict[str, Any], resultado: dict[str, Any]
) -> None:
    altura_m = float(entradas["altura_livre_escavacao_m"])
    ficha_teorica_m = float(resultado["ficha_teorica_m"])
    ficha_preliminar_m = float(resultado["ficha_preliminar_m"])
    profundidade_ponta_m = altura_m + ficha_preliminar_m
    escala = min(34.0, 350.0 / max(profundidade_ponta_m, 0.1))
    x_parede = 430.0
    y_superficie = 68.0
    y_escavacao = y_superficie + altura_m * escala
    y_ponta_teorica = y_escavacao + ficha_teorica_m * escala
    y_ponta_preliminar = y_escavacao + ficha_preliminar_m * escala
    altura_svg = max(450, ceil(y_ponta_preliminar + 120))
    percentual_passivo = float(entradas["percentual_passivo_mobilizado"])
    percentual_acrescimo = float(entradas["percentual_acrescimo_ficha"])
    partes = [
        f'<svg role="img" aria-label="Croqui dinâmico da cortina em balanço" '
        f'viewBox="0 0 1000 {altura_svg}" style="display:block;width:100%;height:auto">',
        "<title>Cortina em balanço com valores informados</title>",
        "<desc>Geometria da escavação e da estaca-prancha, com ficha teórica, ficha preliminar e parâmetros do solo.</desc>",
        f'<rect x="{x_parede + 10:.1f}" y="{y_superficie:.1f}" width="500" '
        f'height="{y_ponta_preliminar - y_superficie:.1f}" fill="#f1e2c4" />',
        f'<rect x="55" y="{y_escavacao:.1f}" width="{x_parede - 65:.1f}" '
        f'height="{y_ponta_preliminar - y_escavacao:.1f}" fill="#dceaf0" />',
        _svg_linha(x_parede, y_superficie, 940, y_superficie, cor="#176452", largura=3),
        _svg_linha(60, y_escavacao, x_parede - 10, y_escavacao, cor="#687a80", largura=2.5, tracejado="8 5"),
        f'<rect x="{x_parede - 9:.1f}" y="{y_superficie:.1f}" width="18" '
        f'height="{y_ponta_preliminar - y_superficie:.1f}" rx="2" fill="#87949a" stroke="#34434a" stroke-width="2" />',
        _svg_texto(82, y_escavacao - 12, "Escavação", tamanho=15, peso=500),
        _svg_texto(500, y_superficie + 28, "Solo retido · camada homogênea", tamanho=16, peso=500),
        _svg_cota_vertical(165, y_superficie, y_escavacao, f"h = {_formatar_numero(altura_m)} m"),
        _svg_cota_vertical(255, y_escavacao, y_ponta_teorica, f"f teórica = {_formatar_numero(ficha_teorica_m)} m"),
        _svg_cota_vertical(350, y_escavacao, y_ponta_preliminar, f"f preliminar = {_formatar_numero(ficha_preliminar_m)} m"),
    ]
    if y_ponta_preliminar - y_ponta_teorica > 5:
        partes.extend(
            (
                _svg_linha(390, y_ponta_teorica, x_parede - 11, y_ponta_teorica, cor="#34566a", largura=1.5, tracejado="5 4"),
                _svg_texto(x_parede + 22, y_ponta_teorica + 5, "Ponta teórica", tamanho=13, cor="#244c62"),
            )
        )
    partes.extend(
        (
            f'<circle cx="{x_parede:.1f}" cy="{y_ponta_preliminar:.1f}" r="5" fill="#34434a" />',
            _svg_painel(
                650,
                y_superficie + 52,
                [
                    "Parâmetros do solo",
                    f"γ = {_formatar_numero(float(entradas['peso_especifico_solo_kN_m3']))} kN/m³",
                    f"φ = {_formatar_numero(float(entradas['angulo_atrito_solo_graus']), 1)}°",
                ],
                largura=270,
            ),
            _svg_painel(
                650,
                y_superficie + 145,
                [
                    "Parâmetros de cálculo",
                    f"Passivo mobilizado = {_formatar_numero(percentual_passivo, 1)}% de Kₚ",
                    f"Acréscimo prático da ficha = +{_formatar_numero(percentual_acrescimo, 1)}%",
                ],
                largura=270,
            ),
            f'<text x="55" y="{y_ponta_preliminar + 48:.1f}" font-family="sans-serif" font-size="13" fill="#52646b">Vista esquemática · dimensões verticais cotadas</text>',
            "</svg>",
        )
    )
    st.html("".join(partes))


def _mostrar_diagrama_pressao_cortina_em_balanco(resultado: dict[str, Any]) -> None:
    figura_pressao = go.Figure()
    for chave_diagrama, nome_diagrama, cor_diagrama in (
        ("ativo", "Ativo · solo retido", "#c34b3c"),
        ("passivo_mobilizado", "Passivo mobilizado · frente da ficha", "#3e8dc1"),
    ):
        pontos = resultado["diagrama_pressao"][chave_diagrama]
        sinal_pressao = 1.0 if chave_diagrama == "ativo" else -1.0
        figura_pressao.add_trace(
            go.Scatter(
                x=[sinal_pressao * ponto["pressao_kPa"] for ponto in pontos],
                y=[ponto["profundidade_m"] for ponto in pontos],
                mode="lines+markers",
                line={"color": cor_diagrama, "width": 3},
                marker={"size": 7},
                fill="tozerox",
                fillcolor=(
                    "rgba(195, 75, 60, 0.12)"
                    if chave_diagrama == "ativo"
                    else "rgba(62, 141, 193, 0.15)"
                ),
                name=nome_diagrama,
                hovertemplate="z = %{y:.2f} m<br>Pressão = %{customdata:.2f} kPa<extra></extra>",
                customdata=[ponto["pressao_kPa"] for ponto in pontos],
            )
        )
    figura_pressao.add_vline(x=0, line_color="#829096", line_width=1)
    figura_pressao.update_layout(
        title="Pressões laterais por profundidade",
        height=440,
        margin={"l": 65, "r": 25, "t": 55, "b": 170},
        xaxis_title="Pressão (kPa) · ativa à direita, passiva à esquerda",
        yaxis_title="Profundidade abaixo da superfície (m)",
        legend={"orientation": "h", "x": 0, "xanchor": "left", "y": -0.28, "yanchor": "top"},
        hovermode="closest",
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_pressao.update_yaxes(
        range=[resultado["profundidade_ponta_m"], 0], zeroline=False
    )
    st.plotly_chart(figura_pressao, width="stretch", theme=None)


def _mostrar_memoria_cortina_em_balanco(resultado: dict[str, Any]) -> None:
    with st.expander("Como foi calculada a ficha", expanded=True):
        st.latex(
            r"K_a=\frac{1-\sin\varphi}{1+\sin\varphi}"
            r"\qquad K_p=\frac{1+\sin\varphi}{1-\sin\varphi}"
        )
        st.latex(
            r"K_{p,mob}=K_p\,r_p"
            r"\qquad r=\left(\frac{K_a}{K_{p,mob}}\right)^{1/3}"
        )
        st.latex(
            r"K_{p,mob}f^3=K_a(h+f)^3"
            r"\qquad f=\frac{r\,h}{1-r}"
            r"\qquad f_{preliminar}=f(1+m_f)"
        )
        linhas_memoria = [
            {"Grandeza": "Kₐ · coeficiente ativo", "Valor": _formatar_numero(resultado["coeficiente_ativo_rankine"], 3), "Unidade": "—"},
            {"Grandeza": "Kₚ · coeficiente passivo", "Valor": _formatar_numero(resultado["coeficiente_passivo_rankine"], 3), "Unidade": "—"},
            {"Grandeza": "Kₚ mobilizado", "Valor": _formatar_numero(resultado["coeficiente_passivo_mobilizado"], 3), "Unidade": "—"},
            {"Grandeza": "Razão cúbica r", "Valor": _formatar_numero(resultado["razao_cubica"], 3), "Unidade": "—"},
            {"Grandeza": "Ficha teórica f", "Valor": _formatar_numero(resultado["ficha_teorica_m"]), "Unidade": "m"},
            {"Grandeza": "Ficha preliminar com acréscimo", "Valor": _formatar_numero(resultado["ficha_preliminar_m"]), "Unidade": "m"},
            {"Grandeza": "Momento ativo sobre a ponta", "Valor": _formatar_numero(resultado["momento_ativo_sobre_ponta_kNm_m"]), "Unidade": "kN·m/m"},
            {"Grandeza": "Momento passivo sobre a ponta", "Valor": _formatar_numero(resultado["momento_passivo_sobre_ponta_kNm_m"]), "Unidade": "kN·m/m"},
            {"Grandeza": "Resíduo do equilíbrio", "Valor": _formatar_numero(resultado["residuo_equilibrio_momentos_kNm_m"], 6), "Unidade": "kN·m/m"},
        ]
        st.dataframe(linhas_memoria, hide_index=True, width="stretch")
        st.caption(
            "O equilíbrio considera o passivo mobilizado indicado. O acréscimo prático é aplicado "
            "depois da ficha teórica e não altera o cálculo do equilíbrio."
        )


def _mostrar_perfil_cortina_ancorada(
    entradas: dict[str, Any], resultado: dict[str, Any]
) -> None:
    profundidade_na_m = float(entradas["espessura_camada_superior_ate_na_m"])
    profundidade_escavacao_m = float(resultado["profundidade_escavacao_abaixo_superficie_m"])
    profundidade_ponta_m = float(resultado["profundidade_ponta_abaixo_superficie_m"])
    profundidade_ancoragem_m = profundidade_na_m - float(entradas["altura_ancoragem_acima_na_m"])
    profundidade_d_m = float(entradas["profundidade_na_ate_escavacao_m"])
    ficha_m = float(entradas["ficha_abaixo_escavacao_m"])
    profundidade_total_m = profundidade_na_m + profundidade_d_m + ficha_m
    escala = min(34.0, 370.0 / max(profundidade_total_m, 0.1))
    x_parede = 430.0
    y_superficie = 68.0
    y_na = y_superficie + profundidade_na_m * escala
    y_escavacao = y_superficie + profundidade_escavacao_m * escala
    y_ponta = y_superficie + profundidade_ponta_m * escala
    y_ancoragem = y_superficie + profundidade_ancoragem_m * escala
    altura_svg = max(470, ceil(y_ponta + 190))
    sobrecarga = float(entradas["sobrecarga_superficie_kPa"])
    partes = [
        f'<svg role="img" aria-label="Croqui dinâmico da cortina ancorada" '
        f'viewBox="0 0 1000 {altura_svg}" style="display:block;width:100%;height:auto">',
        "<title>Cortina ancorada com valores informados</title>",
        "<desc>Perfil com sobrecarga, nível d’água, escavação, tirante, camadas do solo e cotas inseridas.</desc>",
        f'<rect x="{x_parede + 10:.1f}" y="{y_superficie:.1f}" width="500" '
        f'height="{y_na - y_superficie:.1f}" fill="#f1e2c4" />',
        f'<rect x="{x_parede + 10:.1f}" y="{y_na:.1f}" width="500" '
        f'height="{y_ponta - y_na:.1f}" fill="#dceaf0" />',
        f'<rect x="55" y="{y_escavacao:.1f}" width="{x_parede - 65:.1f}" '
        f'height="{y_ponta - y_escavacao:.1f}" fill="#dceaf0" />',
        _svg_linha(x_parede, y_superficie, 940, y_superficie, cor="#176452", largura=3),
        _svg_linha(x_parede, y_na, 940, y_na, cor="#287b9c", largura=2, tracejado="8 5"),
        _svg_linha(60, y_escavacao, x_parede - 10, y_escavacao, cor="#687a80", largura=2.5, tracejado="8 5"),
        f'<rect x="{x_parede - 9:.1f}" y="{y_superficie:.1f}" width="18" '
        f'height="{y_ponta - y_superficie:.1f}" rx="2" fill="#87949a" stroke="#34434a" stroke-width="2" />',
        _svg_linha(x_parede + 10, y_ancoragem, 655, y_ancoragem, cor="#d99028", largura=4),
        f'<rect x="649" y="{y_ancoragem - 8:.1f}" width="8" height="16" fill="#d99028" />',
        _svg_texto(674, y_ancoragem - 12, "Tirante", tamanho=15, peso=500),
        _svg_texto(795, y_na + 5, "N.A.", tamanho=14, peso=500, cor="#176b88"),
        _svg_texto(70, y_escavacao - 12, "Fundo da escavação", tamanho=14, peso=500),
        _svg_texto(520, y_superficie + 43, "Solo natural", tamanho=15, peso=500),
        _svg_texto(520, y_na + 35, "Solo submerso", tamanho=15, peso=500),
        _svg_cota_vertical(140, y_superficie, y_na, f"H₁ = {_formatar_numero(profundidade_na_m)} m"),
        _svg_cota_vertical(220, y_na, y_escavacao, f"D = {_formatar_numero(profundidade_d_m)} m"),
        _svg_cota_vertical(300, y_escavacao, y_ponta, f"f = {_formatar_numero(ficha_m)} m"),
        _svg_cota_vertical(380, y_ancoragem, y_na, f"hₐ = {_formatar_numero(float(entradas['altura_ancoragem_acima_na_m']))} m"),
    ]
    if sobrecarga > 0:
        for x_seta in (520, 585, 650, 715, 780, 845):
            partes.extend(
                (
                    _svg_linha(x_seta, y_superficie - 26, x_seta, y_superficie - 5, cor="#287b9c", largura=1.8),
                    f'<path d="M {x_seta - 5} {y_superficie - 11} L {x_seta} {y_superficie - 4} '
                    f'L {x_seta + 5} {y_superficie - 11}" fill="none" stroke="#287b9c" stroke-width="1.8" />',
                )
            )
    partes.extend(
        (
            _svg_texto(680, y_superficie - 34, f"q = {_formatar_numero(sobrecarga)} kPa", tamanho=15, peso=500, ancora="middle", cor="#176b88"),
            _svg_painel(
                650,
                y_ponta + 35,
                [
                    "Parâmetros do solo e verificação",
                    f"γ₁ = {_formatar_numero(float(entradas['peso_especifico_solo_superior_kN_m3']))} · γ₂ = {_formatar_numero(float(entradas['peso_especifico_solo_submerso_kN_m3']))} kN/m³",
                    f"φ = {_formatar_numero(float(entradas['angulo_atrito_solo_graus']), 1)}° · Kₚ mobilizado = {_formatar_numero(float(entradas['percentual_passivo_mobilizado']), 1)}%",
                    f"FS mínimo ao tombamento = {_formatar_numero(float(entradas['fator_seguranca_minimo_tombamento']), 2)}",
                ],
                largura=300,
            ),
            "</svg>",
        )
    )
    st.html("".join(partes))


def _mostrar_diagrama_pressao_cortina_ancorada(resultado: dict[str, Any]) -> None:
    figura_pressao = go.Figure()
    for chave_diagrama, nome_diagrama, cor_diagrama, sinal_pressao, preenchimento in (
        ("ativo", "Ativo · face posterior", "#c34b3c", 1.0, "rgba(195, 75, 60, 0.12)"),
        (
            "passivo_mobilizado",
            "Passivo mobilizado · face frontal",
            "#3e8dc1",
            -1.0,
            "rgba(62, 141, 193, 0.15)",
        ),
    ):
        pontos = resultado["diagrama_pressao"][chave_diagrama]
        figura_pressao.add_trace(
            go.Scatter(
                x=[sinal_pressao * ponto["pressao_kPa"] for ponto in pontos],
                y=[ponto["profundidade_m"] for ponto in pontos],
                mode="lines+markers",
                line={"color": cor_diagrama, "width": 3},
                marker={"size": 7},
                fill="tozerox",
                fillcolor=preenchimento,
                name=nome_diagrama,
                customdata=[ponto["pressao_kPa"] for ponto in pontos],
                hovertemplate="z = %{y:.2f} m<br>Pressão = %{customdata:.2f} kPa<extra></extra>",
            )
        )
    figura_pressao.add_vline(x=0, line_color="#829096", line_width=1)
    figura_pressao.update_layout(
        title="Pressões laterais · ativa e passiva mobilizada",
        height=470,
        margin={"l": 65, "r": 25, "t": 55, "b": 170},
        xaxis_title="Pressão (kPa) · ativa à direita, passiva à esquerda",
        yaxis_title="Profundidade abaixo da superfície (m)",
        legend={"orientation": "h", "x": 0, "xanchor": "left", "y": -0.26, "yanchor": "top"},
        hovermode="closest",
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_pressao.update_yaxes(
        range=[resultado["profundidade_ponta_abaixo_superficie_m"], 0],
        zeroline=False,
    )
    st.plotly_chart(figura_pressao, width="stretch", theme=None)


def _mostrar_memoria_cortina_ancorada(resultado: dict[str, Any]) -> None:
    with st.expander("Memória de empuxos, momentos e tirante", expanded=True):
        st.latex(
            r"K_a=\frac{1-\sin\varphi}{1+\sin\varphi}"
            r"\qquad K_p=\frac{1+\sin\varphi}{1-\sin\varphi}"
        )
        st.latex(
            r"p_{a,NA}=K_a(q+\gamma_1H_1)"
            r"\qquad p_{a,ponta}=p_{a,NA}+K_a\gamma_2(D+f)"
        )
        st.latex(
            r"E_1=K_aqH_1\quad E_2=\frac{K_a\gamma_1H_1^2}{2}"
            r"\quad E_3=p_{a,NA}(D+f)"
            r"\quad E_4=\frac{K_a\gamma_2(D+f)^2}{2}"
        )
        st.latex(
            r"A=E_a-E_{p,mob}"
            r"\qquad FS_{tombamento}=\frac{M_p}{M_a}"
        )
        st.caption(
            "Os braços acima da ancoragem ficam negativos; os braços abaixo ficam positivos. "
            "O sinal é mantido na soma dos momentos ativos."
        )

        linhas_empuxos = [
            {
                "Parcela": parcela["parcela"],
                "Empuxo (kN/m)": _formatar_numero(parcela["empuxo_kN_m"]),
                "Braço assinado (m)": _formatar_numero(parcela["braco_assinado_m"]),
                "Momento assinado (kN·m/m)": _formatar_numero(
                    parcela["momento_assinado_kNm_m"]
                ),
            }
            for parcela in resultado["empuxo_ativo_por_parcela"]
        ]
        linhas_empuxos.extend(
            [
                {
                    "Parcela": "Empuxo ativo total",
                    "Empuxo (kN/m)": _formatar_numero(
                        resultado["empuxo_ativo_total_kN_m"]
                    ),
                    "Braço assinado (m)": None,
                    "Momento assinado (kN·m/m)": _formatar_numero(
                        resultado["momento_ativo_resultante_kNm_m"]
                    ),
                },
                {
                    "Parcela": "Empuxo passivo mobilizado",
                    "Empuxo (kN/m)": _formatar_numero(
                        resultado["empuxo_passivo_mobilizado_kN_m"]
                    ),
                    "Braço assinado (m)": _formatar_numero(
                        resultado["braco_passivo_em_relacao_ancoragem_m"]
                    ),
                    "Momento assinado (kN·m/m)": _formatar_numero(
                        resultado["momento_passivo_resistente_kNm_m"]
                    ),
                },
            ]
        )
        st.dataframe(linhas_empuxos, hide_index=True, width="stretch")

        pressao_lateral = [
            {
                "Ponto do perfil": "Superfície",
                "Profundidade (m)": 0.0,
                "Pressão ativa (kPa)": _formatar_numero(
                    resultado["pressao_ativa_no_topo_kPa"]
                ),
            },
            {
                "Ponto do perfil": "N.A.",
                "Profundidade (m)": resultado["diagrama_pressao"]["ativo"][1]["profundidade_m"],
                "Pressão ativa (kPa)": _formatar_numero(
                    resultado["pressao_ativa_no_na_kPa"]
                ),
            },
            {
                "Ponto do perfil": "Fundo da escavação",
                "Profundidade (m)": resultado["profundidade_escavacao_abaixo_superficie_m"],
                "Pressão ativa (kPa)": _formatar_numero(
                    resultado["pressao_ativa_no_fundo_escavacao_kPa"]
                ),
            },
            {
                "Ponto do perfil": "Ponta da cortina",
                "Profundidade (m)": resultado["profundidade_ponta_abaixo_superficie_m"],
                "Pressão ativa (kPa)": _formatar_numero(
                    resultado["pressao_ativa_na_ponta_kPa"]
                ),
            },
        ]
        st.markdown("**Pressão ativa nos níveis principais**")
        st.dataframe(pressao_lateral, hide_index=True, width="stretch")


armazenamento_local = LocalStorage(key="armazenamento_contencoes")
aviso_armazenamento = None
if "dados_estaca_prancha_inicializados" not in st.session_state:
    texto_salvo = armazenamento_local.getItem(CHAVE_ARMAZENAMENTO_NAVEGADOR)
    try:
        dados_salvos = json.loads(texto_salvo) if isinstance(texto_salvo, str) else texto_salvo
    except (json.JSONDecodeError, TypeError):
        dados_salvos = None
        aviso_armazenamento = (
            "O rascunho salvo não pôde ser lido; carreguei os exemplos da planilha."
        )
    dados_iniciais = _normalizar_dados_salvos(dados_salvos)
    _aplicar_dados_aos_widgets(dados_iniciais)
    st.session_state[CHAVE_ESTADO_DA_SESSAO] = dados_iniciais
    st.session_state["dados_estaca_prancha_inicializados"] = True
else:
    dados_da_sessao = st.session_state.get(CHAVE_ESTADO_DA_SESSAO)
    chaves_widget = [
        _chave_widget(nome_caso, nome_campo)
        for nome_caso, campos_caso in (
            ("cortina_em_balanco", CAMPOS_CORTINA_EM_BALANCO),
            ("cortina_ancorada", CAMPOS_CORTINA_ANCORADA),
        )
        for nome_campo in campos_caso
    ]
    if isinstance(dados_da_sessao, dict) and any(
        chave not in st.session_state for chave in chaves_widget
    ):
        _aplicar_dados_aos_widgets(_normalizar_dados_salvos(dados_da_sessao))


st.markdown("<style>.block-container{padding-top:1.5rem;padding-bottom:3rem}</style>", unsafe_allow_html=True)
st.title("▥ Estaca-prancha")
st.caption(
    "Dois casos de Rankine para conferência didática: cortina em balanço em solo granular "
    "e cortina ancorada com ficha conhecida."
)
st.info(
    "Use esta página para analisar uma estaca-prancha em balanço ou uma cortina ancorada. "
    "Informe geometria e solo para conferir a ficha, as pressões e as forças no tirante, "
    "com perfil, diagramas e memória do cálculo."
)
if aviso_armazenamento:
    st.warning(aviso_armazenamento)
with st.expander("Sobre o salvamento dos dados"):
    st.write(
        "Os valores ficam neste navegador e voltam ao reabrir a página no mesmo dispositivo. "
        "A limpeza dos dados do navegador apaga esse rascunho."
    )

coluna_restaurar, coluna_exemplo = st.columns([1, 2])
with coluna_restaurar:
    st.button(
        "Restaurar exemplos da planilha",
        on_click=_restaurar_exemplos,
        use_container_width=True,
    )
with coluna_exemplo:
    st.caption(
        "Balanço: h = 5 m, γ = 18 kN/m³, φ = 30° · "
        "Ancorada: q = 12 kPa, D = 4 m, f = 3,5 m, φ = 30°."
    )

aba_balanco, aba_ancorada = st.tabs(["Cortina em balanço", "Cortina ancorada"])

with aba_balanco:
    st.subheader("Entradas · solo granular homogêneo")
    entradas_balanco_preview = _capturar_dados_dos_widgets()["cortina_em_balanco"]
    erros_balanco_preview = validar_entradas_cortina_em_balanco(entradas_balanco_preview)
    resultado_balanco_preview = None
    if not erros_balanco_preview:
        resultado_balanco_preview = calcular_cortina_em_balanco(entradas_balanco_preview)
        st.markdown("**Croqui da cortina com as entradas aplicadas**")
        _mostrar_perfil_cortina_em_balanco(
            entradas_balanco_preview,
            resultado_balanco_preview,
        )
    else:
        st.info("O croqui aparece quando os dados da cortina forem válidos.")
    colunas_entrada_balanco = st.columns(3)
    with colunas_entrada_balanco[0]:
        st.number_input(
            "Altura livre da escavação, h (m)",
            min_value=0.01,
            step=0.1,
            key=_chave_widget("cortina_em_balanco", "altura_livre_escavacao_m"),
        )
        st.number_input(
            "Peso específico do solo, γ (kN/m³)",
            min_value=0.01,
            step=0.5,
            key=_chave_widget("cortina_em_balanco", "peso_especifico_solo_kN_m3"),
        )
    with colunas_entrada_balanco[1]:
        st.number_input(
            "Ângulo de atrito, φ (°)",
            min_value=0.01,
            max_value=89.9,
            step=1.0,
            key=_chave_widget("cortina_em_balanco", "angulo_atrito_solo_graus"),
        )
        st.number_input(
            "Percentual do passivo mobilizado (%)",
            min_value=0.1,
            max_value=100.0,
            step=0.1,
            format="%.1f",
            key=_chave_widget("cortina_em_balanco", "percentual_passivo_mobilizado"),
        )
    with colunas_entrada_balanco[2]:
        st.number_input(
            "Acréscimo prático na ficha (%)",
            min_value=0.0,
            step=1.0,
            key=_chave_widget("cortina_em_balanco", "percentual_acrescimo_ficha"),
        )
        st.caption("O exemplo usa 2/3 do passivo teórico e acrescenta 20% à ficha calculada.")

    entradas_balanco = {
        nome_campo: st.session_state[_chave_widget("cortina_em_balanco", nome_campo)]
        for nome_campo in CAMPOS_CORTINA_EM_BALANCO
    }
    erros_balanco = validar_entradas_cortina_em_balanco(entradas_balanco)
    if erros_balanco:
        st.error("Revise os dados antes de consultar a ficha.")
        for erro in erros_balanco:
            st.markdown(f"- {erro}")
    else:
        resultado_balanco = resultado_balanco_preview or calcular_cortina_em_balanco(entradas_balanco)
        st.divider()
        st.subheader("Resultados da ficha")
        colunas_resultado_balanco = st.columns(4)
        colunas_resultado_balanco[0].metric(
            "Coeficiente ativo, Kₐ",
            _formatar_numero(resultado_balanco["coeficiente_ativo_rankine"], 3),
        )
        colunas_resultado_balanco[1].metric(
            "Passivo mobilizado, Kₚ,mob",
            _formatar_numero(resultado_balanco["coeficiente_passivo_mobilizado"], 3),
        )
        colunas_resultado_balanco[2].metric(
            "Ficha teórica, f",
            f"{_formatar_numero(resultado_balanco['ficha_teorica_m'])} m",
        )
        colunas_resultado_balanco[3].metric(
            "Ficha preliminar",
            f"{_formatar_numero(resultado_balanco['ficha_preliminar_m'])} m",
        )
        st.caption(
            "A ficha teórica reproduz o equilíbrio de momentos da planilha; a ficha preliminar "
            "inclui o acréscimo prático informado."
        )
        st.subheader("Perfil e ficha")
        st.caption(
            "Solo retido à direita; a ficha f começa no fundo da escavação. "
            "Desenho esquemático, sem escala horizontal."
        )
        _mostrar_perfil_cortina_em_balanco(entradas_balanco, resultado_balanco)
        st.subheader("Diagrama de pressões")
        st.caption("As pressões ativas e passivas aparecem em lados opostos do eixo zero.")
        _mostrar_diagrama_pressao_cortina_em_balanco(resultado_balanco)
        _mostrar_memoria_cortina_em_balanco(resultado_balanco)

with aba_ancorada:
    st.subheader("Entradas · duas camadas e ficha conhecida")
    entradas_ancorada_preview = _capturar_dados_dos_widgets()["cortina_ancorada"]
    erros_ancorada_preview = validar_entradas_cortina_ancorada(entradas_ancorada_preview)
    resultado_ancorada_preview = None
    if not erros_ancorada_preview:
        resultado_ancorada_preview = calcular_cortina_ancorada(entradas_ancorada_preview)
        st.markdown("**Croqui da cortina com as entradas aplicadas**")
        _mostrar_perfil_cortina_ancorada(
            entradas_ancorada_preview,
            resultado_ancorada_preview,
        )
    else:
        st.info("O croqui aparece quando os dados da cortina ancorada forem válidos.")
    colunas_entrada_ancorada = st.columns(3)
    with colunas_entrada_ancorada[0]:
        st.number_input(
            "Sobrecarga na superfície, q (kPa)",
            min_value=0.0,
            step=1.0,
            key=_chave_widget("cortina_ancorada", "sobrecarga_superficie_kPa"),
        )
        st.number_input(
            "Espessura da camada superior até o N.A., H₁ (m)",
            min_value=0.01,
            step=0.1,
            key=_chave_widget("cortina_ancorada", "espessura_camada_superior_ate_na_m"),
        )
        st.number_input(
            "Peso específico acima do N.A., γ₁ (kN/m³)",
            min_value=0.01,
            step=0.5,
            key=_chave_widget("cortina_ancorada", "peso_especifico_solo_superior_kN_m3"),
        )
        st.number_input(
            "Peso específico submerso, γ₂ (kN/m³)",
            min_value=0.01,
            step=0.5,
            key=_chave_widget("cortina_ancorada", "peso_especifico_solo_submerso_kN_m3"),
        )
    with colunas_entrada_ancorada[1]:
        st.number_input(
            "Profundidade do N.A. até a escavação, D (m)",
            min_value=0.0,
            step=0.1,
            key=_chave_widget("cortina_ancorada", "profundidade_na_ate_escavacao_m"),
        )
        st.number_input(
            "Ficha abaixo da escavação, f (m)",
            min_value=0.01,
            step=0.1,
            key=_chave_widget("cortina_ancorada", "ficha_abaixo_escavacao_m"),
        )
        st.number_input(
            "Ângulo de atrito, φ (°)",
            min_value=0.01,
            max_value=89.9,
            step=1.0,
            key=_chave_widget("cortina_ancorada", "angulo_atrito_solo_graus"),
        )
    with colunas_entrada_ancorada[2]:
        st.number_input(
            "Altura da ancoragem acima do N.A., hₐ (m)",
            min_value=0.0,
            step=0.1,
            key=_chave_widget("cortina_ancorada", "altura_ancoragem_acima_na_m"),
        )
        st.number_input(
            "Percentual do passivo mobilizado (%)",
            min_value=0.1,
            max_value=100.0,
            step=1.0,
            key=_chave_widget("cortina_ancorada", "percentual_passivo_mobilizado"),
        )
        st.number_input(
            "FS mínimo contra tombamento",
            min_value=0.01,
            step=0.1,
            key=_chave_widget("cortina_ancorada", "fator_seguranca_minimo_tombamento"),
        )
        st.caption(
            "A ancoragem fica acima do N.A.; γ₂ já é o peso específico submerso. "
            "O ângulo φ é igual nas duas camadas."
        )

    entradas_ancorada = {
        nome_campo: st.session_state[_chave_widget("cortina_ancorada", nome_campo)]
        for nome_campo in CAMPOS_CORTINA_ANCORADA
    }
    erros_ancorada = validar_entradas_cortina_ancorada(entradas_ancorada)
    if erros_ancorada:
        st.error("Revise os dados antes de consultar os resultados.")
        for erro in erros_ancorada:
            st.markdown(f"- {erro}")
    else:
        resultado_ancorada = resultado_ancorada_preview or calcular_cortina_ancorada(entradas_ancorada)
        st.divider()
        st.subheader("Resultados da cortina ancorada")
        colunas_resultado_ancorada = st.columns(4)
        colunas_resultado_ancorada[0].metric(
            "Empuxo ativo total",
            f"{_formatar_numero(resultado_ancorada['empuxo_ativo_total_kN_m'])} kN/m",
        )
        colunas_resultado_ancorada[1].metric(
            "Passivo mobilizado",
            f"{_formatar_numero(resultado_ancorada['empuxo_passivo_mobilizado_kN_m'])} kN/m",
        )
        colunas_resultado_ancorada[2].metric(
            "Força no tirante",
            f"{_formatar_numero(resultado_ancorada['forca_tirante_kN_m'])} kN/m",
        )
        colunas_resultado_ancorada[3].metric(
            "FS ao tombamento",
            _formatar_numero(resultado_ancorada["fator_seguranca_tombamento"], 3),
            resultado_ancorada["status_tombamento"],
        )
        if resultado_ancorada["status_tombamento"] == "ATENDE":
            st.success("O FS calculado atende ao mínimo informado.")
        else:
            st.warning(
                "REVER: confira o equilíbrio do tirante e compare o FS com o mínimo informado."
            )
        for aviso in resultado_ancorada["avisos"]:
            st.caption(aviso)

        st.subheader("Perfil, escavação e nível d’água")
        st.caption(
            "Solo retido à direita, escavação à esquerda e tirante acima do N.A. "
            "O desenho é esquemático e não representa escala horizontal."
        )
        _mostrar_perfil_cortina_ancorada(
            entradas_ancorada,
            resultado_ancorada,
        )
        st.subheader("Diagrama de pressões")
        st.caption(
            "A pressão passiva está limitada à ficha abaixo da escavação. "
            "O exemplo não considera diferencial hidrostático entre as faces."
        )
        _mostrar_diagrama_pressao_cortina_ancorada(resultado_ancorada)
        _mostrar_memoria_cortina_ancorada(resultado_ancorada)

        if resultado_ancorada["avisos"]:
            st.warning("Confira as hipóteses do exercício antes de interpretar os resultados.")

dados_formulario = _capturar_dados_dos_widgets()
st.session_state[CHAVE_ESTADO_DA_SESSAO] = deepcopy(dados_formulario)
armazenamento_local.setItem(
    CHAVE_ARMAZENAMENTO_NAVEGADOR,
    json.dumps(dados_formulario, ensure_ascii=False),
    key="salvar_entradas_estaca_prancha",
)

st.caption(
    "Limites desta fase: Rankine, solo sem coesão, superfície horizontal e duas camadas no caso ancorado. "
    "Não inclui diferencial hidrostático, estabilidade global, deformações ou dimensionamento da cortina e do tirante."
)
