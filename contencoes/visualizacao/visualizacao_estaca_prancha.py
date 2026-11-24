"""Diagramas de pressão e memórias exibidos na página de estaca-prancha."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import streamlit as st


def formatar_numero(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")



def mostrar_diagrama_pressao_cortina_em_balanco(resultado: dict[str, Any]) -> None:
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


def mostrar_memoria_cortina_em_balanco(resultado: dict[str, Any]) -> None:
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
            {"Grandeza": "Kₐ · coeficiente ativo", "Valor": formatar_numero(resultado["coeficiente_ativo_rankine"], 3), "Unidade": "—"},
            {"Grandeza": "Kₚ · coeficiente passivo", "Valor": formatar_numero(resultado["coeficiente_passivo_rankine"], 3), "Unidade": "—"},
            {"Grandeza": "Kₚ mobilizado", "Valor": formatar_numero(resultado["coeficiente_passivo_mobilizado"], 3), "Unidade": "—"},
            {"Grandeza": "Razão cúbica r", "Valor": formatar_numero(resultado["razao_cubica"], 3), "Unidade": "—"},
            {"Grandeza": "Ficha teórica f", "Valor": formatar_numero(resultado["ficha_teorica_m"]), "Unidade": "m"},
            {"Grandeza": "Ficha preliminar com acréscimo", "Valor": formatar_numero(resultado["ficha_preliminar_m"]), "Unidade": "m"},
            {"Grandeza": "Momento ativo sobre a ponta", "Valor": formatar_numero(resultado["momento_ativo_sobre_ponta_kNm_m"]), "Unidade": "kN·m/m"},
            {"Grandeza": "Momento passivo sobre a ponta", "Valor": formatar_numero(resultado["momento_passivo_sobre_ponta_kNm_m"]), "Unidade": "kN·m/m"},
            {"Grandeza": "Resíduo do equilíbrio", "Valor": formatar_numero(resultado["residuo_equilibrio_momentos_kNm_m"], 6), "Unidade": "kN·m/m"},
        ]
        st.dataframe(linhas_memoria, hide_index=True, width="stretch")
        st.caption(
            "O equilíbrio considera o passivo mobilizado indicado. O acréscimo prático é aplicado "
            "depois da ficha teórica e não altera o cálculo do equilíbrio."
        )



def mostrar_diagrama_pressao_cortina_ancorada(resultado: dict[str, Any]) -> None:
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


def mostrar_memoria_cortina_ancorada(resultado: dict[str, Any]) -> None:
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
                "Empuxo (kN/m)": formatar_numero(parcela["empuxo_kN_m"]),
                "Braço assinado (m)": formatar_numero(parcela["braco_assinado_m"]),
                "Momento assinado (kN·m/m)": formatar_numero(
                    parcela["momento_assinado_kNm_m"]
                ),
            }
            for parcela in resultado["empuxo_ativo_por_parcela"]
        ]
        linhas_empuxos.extend(
            [
                {
                    "Parcela": "Empuxo ativo total",
                    "Empuxo (kN/m)": formatar_numero(
                        resultado["empuxo_ativo_total_kN_m"]
                    ),
                    "Braço assinado (m)": None,
                    "Momento assinado (kN·m/m)": formatar_numero(
                        resultado["momento_ativo_resultante_kNm_m"]
                    ),
                },
                {
                    "Parcela": "Empuxo passivo mobilizado",
                    "Empuxo (kN/m)": formatar_numero(
                        resultado["empuxo_passivo_mobilizado_kN_m"]
                    ),
                    "Braço assinado (m)": formatar_numero(
                        resultado["braco_passivo_em_relacao_ancoragem_m"]
                    ),
                    "Momento assinado (kN·m/m)": formatar_numero(
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
                "Pressão ativa (kPa)": formatar_numero(
                    resultado["pressao_ativa_no_topo_kPa"]
                ),
            },
            {
                "Ponto do perfil": "N.A.",
                "Profundidade (m)": resultado["diagrama_pressao"]["ativo"][1]["profundidade_m"],
                "Pressão ativa (kPa)": formatar_numero(
                    resultado["pressao_ativa_no_na_kPa"]
                ),
            },
            {
                "Ponto do perfil": "Fundo da escavação",
                "Profundidade (m)": resultado["profundidade_escavacao_abaixo_superficie_m"],
                "Pressão ativa (kPa)": formatar_numero(
                    resultado["pressao_ativa_no_fundo_escavacao_kPa"]
                ),
            },
            {
                "Ponto do perfil": "Ponta da cortina",
                "Profundidade (m)": resultado["profundidade_ponta_abaixo_superficie_m"],
                "Pressão ativa (kPa)": formatar_numero(
                    resultado["pressao_ativa_na_ponta_kPa"]
                ),
            },
        ]
        st.markdown("**Pressão ativa nos níveis principais**")
        st.dataframe(pressao_lateral, hide_index=True, width="stretch")
