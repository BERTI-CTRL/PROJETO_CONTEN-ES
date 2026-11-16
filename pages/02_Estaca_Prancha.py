from __future__ import annotations

import json
from copy import deepcopy
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


def _mostrar_perfil_cortina_em_balanco(
    altura_livre_escavacao_m: float, resultado: dict[str, Any]
) -> None:
    profundidade_ponta_m = resultado["profundidade_ponta_m"]
    figura_perfil = go.Figure()
    figura_perfil.add_shape(
        type="rect",
        x0=0.08,
        x1=6.5,
        y0=-profundidade_ponta_m,
        y1=0,
        fillcolor="rgba(217, 144, 40, 0.14)",
        line={"width": 0},
        layer="below",
    )
    figura_perfil.add_shape(
        type="rect",
        x0=-3.8,
        x1=-0.08,
        y0=-profundidade_ponta_m,
        y1=-altura_livre_escavacao_m,
        fillcolor="rgba(62, 141, 193, 0.15)",
        line={"width": 0},
        layer="below",
    )
    figura_perfil.add_shape(
        type="line",
        x0=0,
        x1=0,
        y0=0,
        y1=-profundidade_ponta_m,
        line={"color": "#17374c", "width": 5},
    )
    figura_perfil.add_shape(
        type="line",
        x0=0,
        x1=6.5,
        y0=0,
        y1=0,
        line={"color": "#176452", "width": 3},
    )
    figura_perfil.add_shape(
        type="line",
        x0=-3.8,
        x1=0,
        y0=-altura_livre_escavacao_m,
        y1=-altura_livre_escavacao_m,
        line={"color": "#687a80", "width": 3, "dash": "dash"},
    )
    figura_perfil.add_annotation(
        x=3.4,
        y=-0.5,
        text="Solo retido",
        showarrow=False,
        bgcolor="rgba(255,255,255,0.78)",
    )
    figura_perfil.add_annotation(
        x=-2.0,
        y=-altura_livre_escavacao_m - 0.35,
        text="Fundo escavado",
        showarrow=False,
        bgcolor="rgba(255,255,255,0.78)",
    )
    figura_perfil.add_annotation(
        x=0.35,
        y=-profundidade_ponta_m,
        text="Ponta · f",
        showarrow=False,
        xanchor="left",
    )
    figura_perfil.update_layout(
        title="Perfil esquemático da cortina em balanço",
        height=460,
        margin={"l": 65, "r": 25, "t": 60, "b": 35},
        xaxis={"visible": False, "range": [-4.2, 7.0]},
        yaxis={
            "title": "Cota em relação à superfície (m)",
            "range": [-profundidade_ponta_m - 0.8, 1.0],
            "zeroline": False,
        },
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    st.plotly_chart(figura_perfil, width="stretch", theme=None)


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
    profundidade_escavacao_m = resultado["profundidade_escavacao_abaixo_superficie_m"]
    profundidade_ponta_m = resultado["profundidade_ponta_abaixo_superficie_m"]
    profundidade_na_m = entradas["espessura_camada_superior_ate_na_m"]
    profundidade_ancoragem_m = profundidade_na_m - entradas[
        "altura_ancoragem_acima_na_m"
    ]

    figura_perfil = go.Figure()
    figura_perfil.add_shape(
        type="rect",
        x0=0.08,
        x1=6.5,
        y0=-profundidade_na_m,
        y1=0,
        fillcolor="rgba(217, 144, 40, 0.16)",
        line={"width": 0},
        layer="below",
    )
    figura_perfil.add_shape(
        type="rect",
        x0=0.08,
        x1=6.5,
        y0=-profundidade_ponta_m,
        y1=-profundidade_na_m,
        fillcolor="rgba(62, 141, 193, 0.12)",
        line={"width": 0},
        layer="below",
    )
    figura_perfil.add_shape(
        type="rect",
        x0=-3.8,
        x1=-0.08,
        y0=-profundidade_ponta_m,
        y1=-profundidade_escavacao_m,
        fillcolor="rgba(62, 141, 193, 0.15)",
        line={"width": 0},
        layer="below",
    )
    figura_perfil.add_shape(
        type="line",
        x0=0,
        x1=0,
        y0=0,
        y1=-profundidade_ponta_m,
        line={"color": "#17374c", "width": 5},
    )
    for cota_m, inicio_x, fim_x, cor, estilo in (
        (0.0, 0.0, 6.5, "#176452", "solid"),
        (-profundidade_na_m, 0.0, 6.5, "#3e8dc1", "dash"),
        (-profundidade_escavacao_m, -3.8, 0.0, "#687a80", "dash"),
    ):
        figura_perfil.add_shape(
            type="line",
            x0=inicio_x,
            x1=fim_x,
            y0=cota_m,
            y1=cota_m,
            line={"color": cor, "width": 2, "dash": estilo},
        )
    figura_perfil.add_shape(
        type="line",
        x0=0,
        x1=4.0,
        y0=-profundidade_ancoragem_m,
        y1=-profundidade_ancoragem_m,
        line={"color": "#d99028", "width": 4},
    )
    for x_m, y_m, texto in (
        (3.4, -0.45, "Solo natural"),
        (3.4, -profundidade_na_m - 0.35, "Solo submerso · γ₂"),
        (3.7, -profundidade_na_m + 0.18, "N.A."),
        (-2.0, -profundidade_escavacao_m + 0.2, "Fundo escavado"),
        (2.8, -profundidade_ancoragem_m - 0.28, "Tirante"),
        (0.35, -profundidade_ponta_m, "Ponta · f"),
    ):
        figura_perfil.add_annotation(
            x=x_m,
            y=y_m,
            text=texto,
            showarrow=False,
            xanchor="left" if x_m > 0 else "center",
            bgcolor="rgba(255,255,255,0.82)",
        )
    figura_perfil.update_layout(
        title="Perfil da cortina ancorada",
        height=500,
        margin={"l": 65, "r": 25, "t": 60, "b": 35},
        xaxis={"visible": False, "range": [-4.2, 7.0]},
        yaxis={
            "title": "Cota em relação à superfície (m)",
            "range": [-profundidade_ponta_m - 0.8, 1.0],
            "zeroline": False,
        },
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    st.plotly_chart(figura_perfil, width="stretch", theme=None)


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
        resultado_balanco = calcular_cortina_em_balanco(entradas_balanco)
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
        _mostrar_perfil_cortina_em_balanco(
            entradas_balanco["altura_livre_escavacao_m"], resultado_balanco
        )
        st.subheader("Diagrama de pressões")
        st.caption("As pressões ativas e passivas aparecem em lados opostos do eixo zero.")
        _mostrar_diagrama_pressao_cortina_em_balanco(resultado_balanco)
        _mostrar_memoria_cortina_em_balanco(resultado_balanco)

with aba_ancorada:
    st.subheader("Entradas · duas camadas e ficha conhecida")
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
        resultado_ancorada = calcular_cortina_ancorada(entradas_ancorada)
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
        _mostrar_perfil_cortina_ancorada(entradas_ancorada, resultado_ancorada)
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
