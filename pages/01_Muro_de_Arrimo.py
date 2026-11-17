from __future__ import annotations

import json
import math
from copy import deepcopy
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from streamlit_local_storage import LocalStorage

from contencoes.calculos_muro_de_arrimo import (
    calcular_muro,
    carregar_exemplo_muro,
    validar_entradas_muro,
)
from contencoes.exportar_muro_arrimo_dxf import gerar_desenho_muro_dxf


st.set_page_config(page_title="Muro de arrimo | Contenções", page_icon="🧱", layout="wide")

CHAVE_ARMAZENAMENTO_NAVEGADOR = "projeto_contencoes_muro_v1"
CHAVE_ESTADO_DA_SESSAO = "dados_muro_preservados_na_sessao"
QUANTIDADE_MAXIMA_CAMADAS = 6
CAMPOS_ENTRADA = [
    "altura_muro_m", "largura_base_m", "largura_topo_m",
    "peso_especifico_concreto_kN_m3", "sobrecarga_kPa",
    "coeficiente_atrito_base", "tensao_admissivel_fundacao_kPa",
    "fator_seguranca_minimo_tombamento", "fator_seguranca_minimo_deslizamento",
    "metodo_empuxo", "inclinacao_aterro_graus", "atrito_solo_muro_graus",
    "profundidade_nivel_agua_m", "peso_especifico_agua_kN_m3",
]
CAMPOS_CAMADA = [
    "espessura_m", "peso_especifico_natural_kN_m3",
    "peso_especifico_saturado_kN_m3", "angulo_atrito_graus", "coesao_kPa",
]
ROTULOS_CAMADA = [
    "Espessura (m)", "γ natural (kN/m³)", "γ saturado (kN/m³)", "φ (°)", "c (kPa)",
]


def _chave_camada(indice_camada: int, campo_camada: str) -> str:
    return f"camada_{indice_camada + 1}_{campo_camada}"


def _dados_padrao() -> dict[str, Any]:
    entradas_padrao, camadas_padrao = carregar_exemplo_muro()
    camadas_completas = deepcopy(camadas_padrao)
    while len(camadas_completas) < QUANTIDADE_MAXIMA_CAMADAS:
        camadas_completas.append({campo: 0.0 for campo in CAMPOS_CAMADA})
    return {"entradas_muro": entradas_padrao, "camadas_solo": camadas_completas}


def _normalizar_dados(dados_salvos: Any) -> dict[str, Any]:
    dados = _dados_padrao()
    if not isinstance(dados_salvos, dict):
        return dados
    if isinstance(dados_salvos.get("entradas_muro"), dict):
        for campo in CAMPOS_ENTRADA:
            if campo in dados_salvos["entradas_muro"]:
                dados["entradas_muro"][campo] = dados_salvos["entradas_muro"][campo]
    camadas_salvas = dados_salvos.get("camadas_solo")
    if isinstance(camadas_salvas, list):
        for indice, camada_salva in enumerate(camadas_salvas[:QUANTIDADE_MAXIMA_CAMADAS]):
            if isinstance(camada_salva, dict):
                for campo in CAMPOS_CAMADA:
                    if campo in camada_salva:
                        dados["camadas_solo"][indice][campo] = camada_salva[campo]
    return dados


def _aplicar_dados_dos_widgets(dados: dict[str, Any]) -> None:
    for campo in CAMPOS_ENTRADA:
        st.session_state[campo] = dados["entradas_muro"][campo]
    for indice, camada in enumerate(dados["camadas_solo"]):
        for campo in CAMPOS_CAMADA:
            st.session_state[_chave_camada(indice, campo)] = camada[campo]


def _restaurar_exemplo() -> None:
    _aplicar_dados_dos_widgets(_dados_padrao())


def _capturar_dados_dos_widgets() -> dict[str, Any]:
    entradas = {campo: st.session_state.get(campo) for campo in CAMPOS_ENTRADA}
    camadas = [
        {campo: st.session_state.get(_chave_camada(indice, campo), 0.0) for campo in CAMPOS_CAMADA}
        for indice in range(QUANTIDADE_MAXIMA_CAMADAS)
    ]
    return {"entradas_muro": entradas, "camadas_solo": camadas}


def _formatar_numero(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _mostrar_graficos(
    resultado_muro: dict[str, Any],
    entradas_muro: dict[str, Any],
    camadas_solo: list[dict[str, Any]],
) -> None:
    altura_muro_m = float(entradas_muro["altura_muro_m"])
    largura_base_m = float(entradas_muro["largura_base_m"])
    largura_topo_m = float(entradas_muro["largura_topo_m"])
    x_tardoz_topo_m = largura_base_m - largura_topo_m
    x_limite_solo_m = x_tardoz_topo_m - max(2.0, altura_muro_m * 0.6)
    inclinacao_aterro_rad = math.radians(
        float(entradas_muro["inclinacao_aterro_graus"])
    )
    cota_superficie_limite_m = altura_muro_m + (
        x_tardoz_topo_m - x_limite_solo_m
    ) * math.tan(inclinacao_aterro_rad)
    profundidade_nivel_agua_m = entradas_muro.get("profundidade_nivel_agua_m")

    geometria_muro = resultado_muro["geometria_muro"]
    figura_geometria = go.Figure()
    cores_solo_natural = (
        "#d6c29a", "#cdb48a", "#c3a77d", "#b99970", "#ae8b67", "#a37f5f"
    )
    cores_solo_saturado = (
        "#9fc8d5", "#8dbbc9", "#7eafc1", "#70a2b9", "#6396b0", "#568aa7"
    )
    profundidade_acumulada_m = 0.0
    for indice_camada, camada_solo in enumerate(camadas_solo, start=1):
        espessura_camada_m = float(camada_solo["espessura_m"])
        if espessura_camada_m <= 0 or profundidade_acumulada_m >= altura_muro_m:
            continue
        profundidade_topo_camada_m = profundidade_acumulada_m
        profundidade_base_camada_m = min(
            altura_muro_m, profundidade_topo_camada_m + espessura_camada_m
        )
        profundidade_acumulada_m += espessura_camada_m
        profundidades_divisao_m = [
            profundidade_topo_camada_m,
            profundidade_base_camada_m,
        ]
        if profundidade_nivel_agua_m is not None:
            profundidade_agua_m = float(profundidade_nivel_agua_m)
            if (
                profundidade_topo_camada_m
                < profundidade_agua_m
                < profundidade_base_camada_m
            ):
                profundidades_divisao_m.insert(1, profundidade_agua_m)

        for profundidade_topo_faixa_m, profundidade_base_faixa_m in zip(
            profundidades_divisao_m, profundidades_divisao_m[1:]
        ):
            zona_saturada = (
                profundidade_nivel_agua_m is not None
                and (profundidade_topo_faixa_m + profundidade_base_faixa_m) / 2
                >= float(profundidade_nivel_agua_m)
            )
            cota_topo_m = altura_muro_m - profundidade_topo_faixa_m
            cota_base_m = altura_muro_m - profundidade_base_faixa_m
            x_tardoz_topo_faixa_m = x_tardoz_topo_m * cota_topo_m / altura_muro_m
            x_tardoz_base_faixa_m = x_tardoz_topo_m * cota_base_m / altura_muro_m
            cota_superficie_topo_faixa_m = (
                cota_superficie_limite_m
                if profundidade_topo_faixa_m == 0
                else cota_topo_m
            )
            nome_zona = "saturada" if zona_saturada else "natural"
            paleta_solo = cores_solo_saturado if zona_saturada else cores_solo_natural
            indice_cor = (indice_camada - 1) % len(paleta_solo)
            figura_geometria.add_trace(
                go.Scatter(
                    x=[
                        x_limite_solo_m,
                        x_tardoz_topo_faixa_m,
                        x_tardoz_base_faixa_m,
                        x_limite_solo_m,
                        x_limite_solo_m,
                    ],
                    y=[
                        cota_superficie_topo_faixa_m,
                        cota_topo_m,
                        cota_base_m,
                        cota_base_m,
                        cota_superficie_topo_faixa_m,
                    ],
                    fill="toself",
                    fillcolor=paleta_solo[indice_cor],
                    line={"color": "rgba(80, 74, 64, 0.45)", "width": 1},
                    mode="lines",
                    name=f"Camada {indice_camada} · {nome_zona}",
                    showlegend=False,
                    hovertemplate=(
                        f"Camada {indice_camada} · zona {nome_zona}<br>"
                        f"γ natural: {float(camada_solo['peso_especifico_natural_kN_m3']):.2f} kN/m³<br>"
                        f"γ saturado: {float(camada_solo['peso_especifico_saturado_kN_m3']):.2f} kN/m³<br>"
                        f"φ: {float(camada_solo['angulo_atrito_graus']):.2f}° · "
                        f"c: {float(camada_solo['coesao_kPa']):.2f} kPa<extra></extra>"
                    ),
                )
            )

        profundidade_meio_camada_m = (
            profundidade_topo_camada_m + profundidade_base_camada_m
        ) / 2
        cota_meio_camada_m = altura_muro_m - profundidade_meio_camada_m
        x_meio_camadas_m = x_limite_solo_m + (
            x_tardoz_topo_m * cota_meio_camada_m / altura_muro_m
            - x_limite_solo_m
        ) * 0.38
        figura_geometria.add_annotation(
            x=x_meio_camadas_m,
            y=cota_meio_camada_m,
            text=f"Camada {indice_camada} · φ={float(camada_solo['angulo_atrito_graus']):.1f}°",
            showarrow=False,
            font={"size": 11, "color": "#26343a"},
            bgcolor="rgba(255,255,255,0.55)",
        )

    figura_geometria.add_trace(
        go.Scatter(
            x=[None], y=[None], mode="markers",
            marker={"symbol": "square", "size": 10, "color": cores_solo_natural[0]},
            name="Solo natural",
        )
    )
    if float(entradas_muro["sobrecarga_kPa"]) > 0:
        for numero_seta in range(4):
            x_seta_m = x_limite_solo_m + (numero_seta + 1) * (
                x_tardoz_topo_m - x_limite_solo_m
            ) / 5
            cota_superficie_seta_m = altura_muro_m + (
                x_tardoz_topo_m - x_seta_m
            ) * math.tan(inclinacao_aterro_rad)
            figura_geometria.add_annotation(
                x=x_seta_m,
                y=cota_superficie_seta_m,
                ax=x_seta_m,
                ay=cota_superficie_seta_m + max(0.45, altura_muro_m * 0.1),
                text="",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
                arrowwidth=2,
                arrowcolor="#c56d16",
            )
        figura_geometria.add_annotation(
            x=x_limite_solo_m + (x_tardoz_topo_m - x_limite_solo_m) / 2,
            y=cota_superficie_limite_m + max(0.6, altura_muro_m * 0.12),
            text=f"Sobrecarga q = {float(entradas_muro['sobrecarga_kPa']):.1f} kPa",
            showarrow=False,
            font={"size": 12, "color": "#9a4d08"},
            bgcolor="rgba(255,255,255,0.85)",
        )
    figura_geometria.add_trace(
        go.Scatter(
            x=[None], y=[None], mode="markers",
            marker={"symbol": "square", "size": 10, "color": cores_solo_saturado[0]},
            name="Solo saturado",
        )
    )

    figura_geometria.add_trace(
        go.Scatter(
            x=[ponto["x_m"] for ponto in geometria_muro],
            y=[ponto["cota_y_m"] for ponto in geometria_muro],
            fill="toself",
            fillcolor="rgba(38, 111, 91, 0.22)",
            line={"color": "#176452", "width": 3},
            mode="lines",
            name="Muro de concreto",
            hovertemplate="Muro de concreto<extra></extra>",
        )
    )
    figura_geometria.add_trace(
        go.Scatter(
            x=[x_limite_solo_m, x_tardoz_topo_m],
            y=[cota_superficie_limite_m, altura_muro_m],
            mode="lines",
            line={"color": "#765b35", "width": 3},
            name="Superfície do aterro",
            hovertemplate="Superfície do aterro<extra></extra>",
        )
    )
    profundidade_acumulada_m = 0.0
    for camada_solo in camadas_solo:
        profundidade_acumulada_m += float(camada_solo["espessura_m"])
        if profundidade_acumulada_m >= altura_muro_m:
            continue
        cota_interface_m = altura_muro_m - profundidade_acumulada_m
        figura_geometria.add_trace(
            go.Scatter(
            x=[
                x_limite_solo_m,
                x_tardoz_topo_m * cota_interface_m / altura_muro_m,
            ],
                y=[cota_interface_m, cota_interface_m],
                mode="lines",
                line={"color": "#584c3a", "width": 1.5, "dash": "dash"},
                name="Interface entre camadas",
                showlegend=False,
                hovertemplate="Interface entre camadas<extra></extra>",
            )
        )
    if profundidade_nivel_agua_m is not None:
        cota_nivel_agua_m = altura_muro_m - float(profundidade_nivel_agua_m)
        if 0 <= cota_nivel_agua_m <= altura_muro_m:
            figura_geometria.add_trace(
                go.Scatter(
                    x=[
                        x_limite_solo_m,
                        x_tardoz_topo_m * cota_nivel_agua_m / altura_muro_m,
                    ],
                    y=[cota_nivel_agua_m, cota_nivel_agua_m],
                    mode="lines",
                    line={"color": "#1479a6", "width": 3, "dash": "dashdot"},
                    name="Nível d’água",
                    hovertemplate="Nível d’água<extra></extra>",
                )
            )
            figura_geometria.add_annotation(
                x=x_limite_solo_m,
                y=cota_nivel_agua_m,
                text="N.A.",
                showarrow=False,
                xshift=20,
                yshift=10,
                font={"size": 11, "color": "#075d82"},
                bgcolor="rgba(255,255,255,0.7)",
            )
    figura_geometria.update_layout(
        title="Perfil do muro e das camadas de solo",
        height=400,
        margin={"l": 18, "r": 18, "t": 55, "b": 30},
        xaxis_title="Largura (m)",
        yaxis_title="Cota (m)",
        legend={"orientation": "h", "y": -0.24},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_geometria.update_yaxes(
        range=[0, max(altura_muro_m * 1.08, cota_superficie_limite_m * 1.08)],
        zeroline=False,
    )
    figura_geometria.update_xaxes(
        range=[x_limite_solo_m - 0.5, largura_base_m + 0.5],
        autorange="reversed",
        zeroline=False,
        scaleanchor="y",
        scaleratio=1,
    )

    figura_pressao = go.Figure()
    estilos_diagrama = (
        ("solo", "Solo", "#176452", "dash"),
        ("sobrecarga", "Sobrecarga", "#d99028", "dot"),
        ("agua", "Água", "#3e8dc1", "dash"),
        ("total", "Total", "#17374c", "solid"),
    )
    for chave, nome, cor, estilo in estilos_diagrama:
        pontos = resultado_muro["diagramas_pressao"][chave]
        figura_pressao.add_trace(
            go.Scatter(
                x=[ponto["pressao_kPa"] for ponto in pontos],
                y=[ponto["profundidade_m"] for ponto in pontos],
                mode="lines",
                line={"color": cor, "width": 3 if chave == "total" else 2, "dash": estilo},
                name=nome,
            )
        )
    figura_pressao.update_layout(
        title="Pressões atrás do muro",
        height=400,
        margin={"l": 18, "r": 18, "t": 55, "b": 30},
        xaxis_title="Pressão horizontal (kPa)",
        yaxis_title="Profundidade a partir do topo (m)",
        legend={"orientation": "h", "y": -0.24},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_pressao.update_yaxes(range=[altura_muro_m, 0], zeroline=False)
    figura_pressao.update_xaxes(rangemode="tozero", zeroline=True, zerolinecolor="#9ba9ac")

    coluna_geometria, coluna_pressao = st.columns(2)
    with coluna_geometria:
        st.plotly_chart(figura_geometria, width="stretch", theme=None)
    with coluna_pressao:
        st.plotly_chart(figura_pressao, width="stretch", theme=None)


def _mostrar_memoria_calculo(resultado_muro: dict[str, Any]) -> None:
    resumo = resultado_muro["resumo"]
    verificacoes = resultado_muro["verificacoes"]
    with st.expander("Memória de cálculo e grandezas intermediárias"):
        st.markdown("**Pressões laterais consideradas**")
        st.latex(r"\sigma'_v=\sum\gamma_{natural}\,\Delta z_{acima}+\sum(\gamma_{sat}-\gamma_w)\,\Delta z_{abaixo}")
        st.latex(r"p_{solo}=\max(0,\,K_a\sigma'_v-2c\sqrt{K_a})\qquad p_q=K_aq\qquad u=\gamma_w\max(0,z-z_{NA})")
        if st.session_state["metodo_empuxo"] == "Rankine":
            if st.session_state["inclinacao_aterro_graus"] == 0:
                st.latex(r"K_a=\tan^2\left(45^\circ-\frac{\varphi}{2}\right)")
            else:
                st.latex(r"K_a=\frac{\cos\beta\left(\cos\beta-\sqrt{\cos^2\beta-\cos^2\varphi}\right)}{\cos\beta+\sqrt{\cos^2\beta-\cos^2\varphi}}")
        else:
            st.latex(r"K_a=\frac{\cos^2\varphi}{\cos\delta\left(1+\sqrt{\frac{\sin(\varphi+\delta)\sin(\varphi-\beta)}{\cos\delta\cos\beta}}\right)^2}")

        st.markdown("**Estabilidade e contato na base**")
        st.latex(r"FS_{tombamento}=\frac{\sum M_{estabilizadores}}{\sum M_{tombadores}}\qquad FS_{deslizamento}=\frac{Vf}{H_{total}}")
        st.latex(r"x_R=\frac{M_{estabilizador}-M_{tombador}}{V}\qquad e=\frac{b}{2}-x_R")
        st.latex(r"\sigma_{max,min}=\frac{V}{b}\left(1\pm\frac{6|e|}{b}\right)\quad\text{se } |e|\le\frac{b}{6}")

        grandezas_intermediarias = [
            {"Grandeza": "Peso do muro", "Valor": _formatar_numero(resumo["peso_muro_kN_m"]), "Unidade": "kN/m"},
            {"Grandeza": "Carga vertical total na base", "Valor": _formatar_numero(resumo["carga_vertical_total_kN_m"]), "Unidade": "kN/m"},
            {"Grandeza": "Componente horizontal total", "Valor": _formatar_numero(resumo["componente_horizontal_total_kN_m"]), "Unidade": "kN/m"},
            {"Grandeza": "Componente vertical descendente", "Valor": _formatar_numero(resumo["componente_vertical_descendente_kN_m"]), "Unidade": "kN/m"},
            {"Grandeza": "Momento estabilizador total", "Valor": _formatar_numero(resumo["momento_estabilizador_total_kNm_m"]), "Unidade": "kN·m/m"},
            {"Grandeza": "Momento tombador na ponta", "Valor": _formatar_numero(resumo["momento_tombador_ponta_kNm_m"]), "Unidade": "kN·m/m"},
            {"Grandeza": "Resultante desde a ponta", "Valor": _formatar_numero(verificacoes["posicao_resultante_desde_ponta_m"]), "Unidade": "m"},
            {"Grandeza": "Excentricidade", "Valor": _formatar_numero(verificacoes["excentricidade_resultante_m"]), "Unidade": "m"},
            {"Grandeza": "Regime de pressão", "Valor": verificacoes["regime_pressao_base"], "Unidade": "—"},
        ]
        st.dataframe(grandezas_intermediarias, hide_index=True, width="stretch")
        st.caption(
            "Na convenção da planilha, Coulomb é decomposto em componentes horizontal e vertical; "
            "a parcela vertical descendente atua na largura da base."
        )


def _mostrar_tabela_trechos(trechos: list[dict[str, Any]]) -> None:
    linhas_tabela = [
        {
            "Trecho": trecho["identificacao_trecho"],
            "z sup. (m)": trecho["profundidade_superior_m"],
            "z inf. (m)": trecho["profundidade_inferior_m"],
            "Kₐ": trecho["coeficiente_empuxo_ativo"],
            "σ'v sup. (kPa)": trecho["tensao_vertical_efetiva_superior_kPa"],
            "σ'v inf. (kPa)": trecho["tensao_vertical_efetiva_inferior_kPa"],
            "p solo sup. (kPa)": trecho["pressao_solo_superior_kPa"],
            "p solo inf. (kPa)": trecho["pressao_solo_inferior_kPa"],
            "p sobrecarga (kPa)": trecho["pressao_sobrecarga_kPa"],
            "p água sup. (kPa)": trecho["pressao_agua_superior_kPa"],
            "p água inf. (kPa)": trecho["pressao_agua_inferior_kPa"],
            "E solo (kN/m)": trecho["empuxo_solo_kN_m"],
            "braço solo (m)": trecho["braco_empuxo_solo_ponta_m"],
            "M solo (kN·m/m)": trecho["momento_empuxo_solo_ponta_kNm_m"],
            "E q (kN/m)": trecho["empuxo_sobrecarga_kN_m"],
            "E água (kN/m)": trecho["empuxo_hidrostatico_kN_m"],
        }
        for trecho in trechos
    ]
    st.dataframe(linhas_tabela, hide_index=True, width="stretch")


armazenamento_local = LocalStorage(key="armazenamento_contencoes")
aviso_armazenamento = None
if "dados_muro_inicializados" not in st.session_state:
    texto_salvo = armazenamento_local.getItem(CHAVE_ARMAZENAMENTO_NAVEGADOR)
    try:
        dados_salvos = json.loads(texto_salvo) if isinstance(texto_salvo, str) else texto_salvo
    except (json.JSONDecodeError, TypeError):
        dados_salvos = None
        aviso_armazenamento = "O rascunho salvo não pôde ser lido; carreguei o exemplo da planilha."
    dados_iniciais = _normalizar_dados(dados_salvos)
    _aplicar_dados_dos_widgets(dados_iniciais)
    st.session_state[CHAVE_ESTADO_DA_SESSAO] = dados_iniciais
    st.session_state["dados_muro_inicializados"] = True
else:
    dados_da_sessao = st.session_state.get(CHAVE_ESTADO_DA_SESSAO)
    todas_chaves_widget = CAMPOS_ENTRADA + [
        _chave_camada(indice, campo)
        for indice in range(QUANTIDADE_MAXIMA_CAMADAS)
        for campo in CAMPOS_CAMADA
    ]
    if isinstance(dados_da_sessao, dict) and any(chave not in st.session_state for chave in todas_chaves_widget):
        _aplicar_dados_dos_widgets(dados_da_sessao)


st.markdown("<style>.block-container{padding-top:1.5rem;padding-bottom:3rem}</style>", unsafe_allow_html=True)
st.title("🧱 Muro de arrimo")
st.caption(
    "Muro trapezoidal de gravidade · cálculo por metro de comprimento · "
    "salvamento automático neste navegador."
)
if aviso_armazenamento:
    st.warning(aviso_armazenamento)
with st.expander("Sobre o salvamento dos dados"):
    st.write(
        "Os valores ficam no armazenamento local deste navegador e voltam ao reabrir a página. "
        "Não são compartilhados entre dispositivos e podem ser apagados ao limpar os dados do navegador."
    )

coluna_botao, coluna_referencia = st.columns([1, 2])
with coluna_botao:
    st.button("Restaurar exemplo da planilha", on_click=_restaurar_exemplo, use_container_width=True)
with coluna_referencia:
    st.caption("Exemplo da planilha: H = 6 m · b = 4 m · q = 10 kPa · N.A. a 2 m · duas camadas")

with st.container(border=True):
    st.subheader("Geometria, ações e fundação")
    coluna_geometria, coluna_acoes, coluna_fundacao = st.columns(3)
    with coluna_geometria:
        st.number_input("Altura do muro, H (m)", min_value=0.0, step=0.10, key="altura_muro_m")
        st.number_input("Largura da base, b (m)", min_value=0.0, step=0.10, key="largura_base_m")
        st.number_input("Largura do topo, t (m)", min_value=0.0, step=0.10, key="largura_topo_m")
        st.number_input(
            "Peso específico do concreto, γc (kN/m³)",
            min_value=0.0,
            step=0.5,
            key="peso_especifico_concreto_kN_m3",
        )
    with coluna_acoes:
        st.number_input("Sobrecarga uniforme, q (kPa)", min_value=0.0, step=1.0, key="sobrecarga_kPa")
        st.selectbox("Teoria de empuxo", ["Rankine", "Coulomb"], key="metodo_empuxo")
        st.number_input(
            "Inclinação do aterro, β (°)",
            min_value=0.0,
            max_value=89.9,
            step=1.0,
            key="inclinacao_aterro_graus",
        )
        st.number_input(
            "Atrito solo–muro, δ (°)",
            min_value=0.0,
            max_value=89.9,
            step=1.0,
            key="atrito_solo_muro_graus",
        )
    with coluna_fundacao:
        st.number_input("Atrito na base, f (—)", min_value=0.0, step=0.05, key="coeficiente_atrito_base")
        st.number_input(
            "Tensão admissível da fundação (kPa)",
            min_value=0.0,
            step=10.0,
            key="tensao_admissivel_fundacao_kPa",
        )
        st.number_input(
            "FS mínimo contra tombamento",
            min_value=0.0,
            step=0.1,
            key="fator_seguranca_minimo_tombamento",
        )
        st.number_input(
            "FS mínimo contra deslizamento",
            min_value=0.0,
            step=0.1,
            key="fator_seguranca_minimo_deslizamento",
        )

with st.container(border=True):
    st.subheader("Nível d’água")
    coluna_nivel_agua, coluna_peso_agua = st.columns(2)
    with coluna_nivel_agua:
        st.number_input(
            "Profundidade do N.A. a partir do topo (m)",
            min_value=0.0,
            value=None,
            step=0.10,
            placeholder="Vazio = sem água",
            key="profundidade_nivel_agua_m",
        )
    with coluna_peso_agua:
        st.number_input(
            "Peso específico da água, γw (kN/m³)",
            min_value=0.0,
            step=0.1,
            key="peso_especifico_agua_kN_m3",
        )

with st.container(border=True):
    st.subheader("Perfil do solo retido")
    st.caption(
        "Preencha as camadas em sequência, do topo para baixo. Deixe as que não usar zeradas; "
        "a soma das espessuras deve ser igual à altura do muro."
    )
    for indice_camada in range(QUANTIDADE_MAXIMA_CAMADAS):
        with st.expander(f"Camada {indice_camada + 1}", expanded=(indice_camada == 0)):
            colunas_camadas = st.columns(5)
            for indice_campo, (campo_camada, rotulo_campo) in enumerate(
                zip(CAMPOS_CAMADA, ROTULOS_CAMADA)
            ):
                with colunas_camadas[indice_campo]:
                    st.number_input(
                        rotulo_campo,
                        min_value=0.0,
                        step=1.0 if campo_camada == "angulo_atrito_graus" else 0.1,
                        key=_chave_camada(indice_camada, campo_camada),
                    )

dados_formulario = _capturar_dados_dos_widgets()
st.session_state[CHAVE_ESTADO_DA_SESSAO] = deepcopy(dados_formulario)
armazenamento_local.setItem(
    CHAVE_ARMAZENAMENTO_NAVEGADOR,
    json.dumps(dados_formulario, ensure_ascii=False),
    key="salvar_entradas_muro",
)

camadas_solo = dados_formulario["camadas_solo"]
entradas_muro = dados_formulario["entradas_muro"]
erros_entrada = validar_entradas_muro(entradas_muro, camadas_solo)

if erros_entrada:
    st.error("Revise os dados antes de consultar os resultados.")
    for erro in erros_entrada:
        st.markdown(f"- {erro}")
else:
    resultado_muro = calcular_muro(entradas_muro, camadas_solo)
    resumo = resultado_muro["resumo"]
    verificacoes = resultado_muro["verificacoes"]
    st.divider()
    st.subheader("Resultados principais")
    colunas_metricas = st.columns(4)
    colunas_metricas[0].metric(
        "FS contra tombamento",
        _formatar_numero(verificacoes["fator_seguranca_tombamento"], 3),
        verificacoes["status_tombamento"],
    )
    colunas_metricas[1].metric(
        "FS contra deslizamento",
        _formatar_numero(verificacoes["fator_seguranca_deslizamento"], 3),
        verificacoes["status_deslizamento"],
    )
    colunas_metricas[2].metric(
        "Tensão máxima na base",
        f"{_formatar_numero(verificacoes['tensao_maxima_base_kPa'])} kPa",
        verificacoes["status_tensao_maxima_base"],
    )
    colunas_metricas[3].metric(
        "Tensão mínima na base",
        f"{_formatar_numero(verificacoes['tensao_minima_base_kPa'])} kPa",
        verificacoes["regime_pressao_base"],
    )

    todos_checks_atendem = (
        verificacoes["status_tombamento"] == "ATENDE"
        and verificacoes["status_deslizamento"] == "ATENDE"
        and verificacoes["status_tensao_maxima_base"] == "ATENDE"
        and verificacoes["regime_pressao_base"] != "FORA DA BASE"
    )
    if todos_checks_atendem:
        st.success("O caso atende aos checks de estabilidade incluídos nesta fase.")
    else:
        st.warning("Um ou mais checks precisam de revisão. Confira os limites e a memória de cálculo.")

    _mostrar_graficos(resultado_muro, entradas_muro, camadas_solo)

    arquivo_dxf_muro = gerar_desenho_muro_dxf(
        entradas_muro, camadas_solo, resultado_muro
    )
    st.download_button(
        "Baixar desenho CAD do muro (.dxf)",
        data=arquivo_dxf_muro,
        file_name="muro_de_arrimo.dxf",
        mime="application/dxf",
        help="Inclui o muro cotado, camadas de solo preenchidas, nível d'água, diagramas de pressão e resumo dos resultados.",
        key="baixar_dxf_muro_arrimo",
    )
    st.caption(
        "O DXF separa cada camada de solo e suas zonas natural/saturada em layers, "
        "para você poder conferir, ocultar ou editar no AutoCAD."
    )

    with st.expander("Empuxos resultantes", expanded=True):
        colunas_empuxos = st.columns(4)
        colunas_empuxos[0].metric(
            "Solo", f"{_formatar_numero(resumo['empuxo_solo_kN_m'])} kN/m"
        )
        colunas_empuxos[1].metric(
            "Sobrecarga", f"{_formatar_numero(resumo['empuxo_sobrecarga_kN_m'])} kN/m"
        )
        colunas_empuxos[2].metric(
            "Água", f"{_formatar_numero(resumo['empuxo_hidrostatico_kN_m'])} kN/m"
        )
        colunas_empuxos[3].metric(
            "Resultante desde a ponta",
            f"{_formatar_numero(verificacoes['posicao_resultante_desde_ponta_m'])} m",
            f"e = {_formatar_numero(verificacoes['excentricidade_resultante_m'])} m",
        )

    with st.expander("Pressões e empuxos por trecho", expanded=True):
        _mostrar_tabela_trechos(resultado_muro["trechos"])

    _mostrar_memoria_calculo(resultado_muro)
    st.caption(
        "Limites desta fase: não inclui ruptura global, empuxo passivo à frente do muro "
        "ou dimensionamento estrutural do concreto armado."
    )
