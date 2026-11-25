from __future__ import annotations

import json
import hashlib
import math
from copy import deepcopy
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from streamlit_local_storage import LocalStorage

from contencoes.calculos.calculos_muro_de_arrimo import (
    calcular_muro,
    carregar_exemplo_muro,
    validar_entradas_muro,
)
from contencoes.cad.exportar_muro_arrimo_dxf import gerar_desenho_muro_dxf
from contencoes.visualizacao.memorias_passo_a_passo import montar_memorial_passo_a_passo_muro
from contencoes.relatorios.gerar_relatorio_muro_arrimo import (
    ErroGeracaoRelatorio,
    montar_relatorio_muro_tex,
    compilar_relatorio_muro_pdf,
)


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


def _preencher_seis_camadas_padrao() -> None:
    entradas_exemplo, camadas_exemplo = carregar_exemplo_muro()
    altura_muro_m = float(
        st.session_state.get("altura_muro_m", entradas_exemplo["altura_muro_m"]) or 0.0
    )
    if altura_muro_m <= 0:
        camadas = [
            {campo: 0.0 for campo in CAMPOS_CAMADA}
            for _ in range(QUANTIDADE_MAXIMA_CAMADAS)
        ]
    else:
        espessura_padrao_m = round(
            altura_muro_m / QUANTIDADE_MAXIMA_CAMADAS, 2
        )
        camadas = []
        for indice in range(QUANTIDADE_MAXIMA_CAMADAS):
            propriedades = deepcopy(camadas_exemplo[indice % len(camadas_exemplo)])
            propriedades["espessura_m"] = (
                altura_muro_m - espessura_padrao_m * (QUANTIDADE_MAXIMA_CAMADAS - 1)
                if indice == QUANTIDADE_MAXIMA_CAMADAS - 1
                else espessura_padrao_m
            )
            propriedades["espessura_m"] = round(propriedades["espessura_m"], 2)
            camadas.append(propriedades)
    for indice, camada in enumerate(camadas):
        for campo in CAMPOS_CAMADA:
            st.session_state[_chave_camada(indice, campo)] = camada[campo]


def _limpar_para_uma_camada() -> None:
    entradas_exemplo, camadas_exemplo = carregar_exemplo_muro()
    altura_muro_m = float(
        st.session_state.get("altura_muro_m", entradas_exemplo["altura_muro_m"]) or 0.0
    )
    primeira_camada = deepcopy(camadas_exemplo[0])
    primeira_camada["espessura_m"] = altura_muro_m
    if altura_muro_m <= 0:
        primeira_camada = {campo: 0.0 for campo in CAMPOS_CAMADA}
    camadas = [primeira_camada] + [
        {campo: 0.0 for campo in CAMPOS_CAMADA}
        for _ in range(QUANTIDADE_MAXIMA_CAMADAS - 1)
    ]
    for indice, camada in enumerate(camadas):
        for campo in CAMPOS_CAMADA:
            st.session_state[_chave_camada(indice, campo)] = camada[campo]


def _capturar_dados_dos_widgets() -> dict[str, Any]:
    entradas = {campo: st.session_state.get(campo) for campo in CAMPOS_ENTRADA}
    camadas = [
        {campo: st.session_state.get(_chave_camada(indice, campo), 0.0) for campo in CAMPOS_CAMADA}
        for indice in range(QUANTIDADE_MAXIMA_CAMADAS)
    ]
    return {"entradas_muro": entradas, "camadas_solo": camadas}


def _assinatura_documentos(dados: dict[str, Any]) -> str:
    serializado = json.dumps(dados, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def _formatar_numero(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _mostrar_selo_status(coluna: Any, status: str) -> None:
    if status == "ATENDE":
        cor_texto = "#6ee7b7"
        cor_fundo = "rgba(16, 185, 129, 0.16)"
        simbolo = "✓"
    elif status in {"REVER", "BLOQUEADO", "FORA DA BASE"}:
        cor_texto = "#fca5a5"
        cor_fundo = "rgba(239, 68, 68, 0.18)"
        simbolo = "!"
    else:
        cor_texto = "#bfdbfe"
        cor_fundo = "rgba(59, 130, 246, 0.16)"
        simbolo = "·"
    coluna.markdown(
        f'<span style="display:inline-block;padding:2px 9px;border-radius:999px;'
        f'background:{cor_fundo};color:{cor_texto};font-size:0.78rem;font-weight:600">'
        f'{simbolo}&nbsp; {status}</span>',
        unsafe_allow_html=True,
    )


def _mostrar_resumo_principal(verificacoes: dict[str, Any]) -> None:
    st.subheader("Resumo da estabilidade")
    colunas_metricas = st.columns(4)
    colunas_metricas[0].metric(
        "FS contra tombamento",
        _formatar_numero(verificacoes["fator_seguranca_tombamento"], 3),
    )
    _mostrar_selo_status(colunas_metricas[0], verificacoes["status_tombamento"])
    colunas_metricas[1].metric(
        "FS contra deslizamento",
        _formatar_numero(verificacoes["fator_seguranca_deslizamento"], 3),
    )
    _mostrar_selo_status(colunas_metricas[1], verificacoes["status_deslizamento"])
    colunas_metricas[2].metric(
        "Tensão máxima na base",
        f"{_formatar_numero(verificacoes['tensao_maxima_base_kPa'])} kPa",
    )
    _mostrar_selo_status(colunas_metricas[2], verificacoes["status_tensao_maxima_base"])
    colunas_metricas[3].metric(
        "Tensão mínima na base",
        f"{_formatar_numero(verificacoes['tensao_minima_base_kPa'])} kPa",
    )
    _mostrar_selo_status(colunas_metricas[3], verificacoes["regime_pressao_base"])

    todos_checks_atendem = (
        verificacoes["status_tombamento"] == "ATENDE"
        and verificacoes["status_deslizamento"] == "ATENDE"
        and verificacoes["status_tensao_maxima_base"] == "ATENDE"
        and verificacoes["regime_pressao_base"] != "FORA DA BASE"
    )
    if todos_checks_atendem:
        st.success("O caso atende aos checks de estabilidade incluídos nesta fase.")
    else:
        st.error("Um ou mais checks não atendem ou estão bloqueados. Confira os limites e a memória de cálculo.")


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
        for numero_seta in range(7):
            x_seta_m = x_limite_solo_m + (numero_seta + 1) * (
                x_tardoz_topo_m - x_limite_solo_m
            ) / 8
            cota_superficie_seta_m = altura_muro_m + (
                x_tardoz_topo_m - x_seta_m
            ) * math.tan(inclinacao_aterro_rad)
            comprimento_seta_m = max(0.45, altura_muro_m * 0.1)
            figura_geometria.add_annotation(
                x=x_seta_m,
                y=cota_superficie_seta_m,
                ax=x_seta_m,
                ay=cota_superficie_seta_m + comprimento_seta_m,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                text="",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.1,
                arrowwidth=2.4,
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
        title={
            "text": "SEÇÃO DO MURO E DO TERRENO<sup>   ·   perfil estratigráfico</sup>",
            "x": 0.03,
            "font": {"size": 19, "color": "#17374c"},
        },
        height=560,
        margin={"l": 55, "r": 35, "t": 75, "b": 70},
        xaxis_title="← muro                         tardoz / aterro →",
        yaxis_title="Cota (m)",
        legend={"orientation": "h", "y": -0.18, "x": 0.03},
        paper_bgcolor="#f8fafb",
        plot_bgcolor="#f8fafb",
        font={"family": "Arial, sans-serif", "color": "#344b5a", "size": 12},
        hoverlabel={"bgcolor": "white", "font_size": 13},
    )
    figura_geometria.update_yaxes(
        range=[0, max(altura_muro_m * 1.08, cota_superficie_limite_m * 1.08)],
        zeroline=False,
        gridcolor="#dce5e9",
        ticks="outside",
        showline=True,
        linecolor="#82949d",
    )
    figura_geometria.update_xaxes(
        range=[x_limite_solo_m - 0.5, largura_base_m + 0.5],
        autorange="reversed",
        zeroline=False,
        scaleanchor="y",
        scaleratio=1,
        showgrid=False,
        showline=True,
        linecolor="#82949d",
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
        height=430,
        margin={"l": 18, "r": 18, "t": 55, "b": 30},
        xaxis_title="Pressão horizontal (kPa)",
        yaxis_title="Profundidade a partir do topo (m)",
        legend={"orientation": "h", "y": -0.24},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura_pressao.update_yaxes(range=[altura_muro_m, 0], zeroline=False)
    figura_pressao.update_xaxes(rangemode="tozero", zeroline=True, zerolinecolor="#9ba9ac")

    st.markdown(
        "**Seção esquemática** · Muro à esquerda; tardoz, aterro e camadas à direita. "
        "As setas indicam a sobrecarga uniforme."
    )
    st.plotly_chart(
        _montar_esquema_referencia(resultado_muro, entradas_muro, camadas_solo),
        width="stretch",
        theme=None,
    )
    st.plotly_chart(figura_pressao, width="stretch", theme=None)


def _montar_esquema_referencia(
    resultado_muro: dict[str, Any],
    entradas_muro: dict[str, Any],
    camadas_solo: list[dict[str, Any]],
) -> go.Figure:
    """Desenha a seção no padrão da referência: muro à esquerda e solo à direita."""
    altura_muro_m = float(entradas_muro["altura_muro_m"])
    largura_base_m = float(entradas_muro["largura_base_m"])
    largura_topo_m = float(entradas_muro["largura_topo_m"])
    extensao_solo_m = max(2.2, altura_muro_m * 0.55)
    x_limite_solo_m = largura_base_m + extensao_solo_m
    inclinacao_aterro_rad = math.radians(
        float(entradas_muro["inclinacao_aterro_graus"])
    )
    cota_superficie_lateral_m = altura_muro_m + extensao_solo_m * math.tan(
        inclinacao_aterro_rad
    )
    nivel_agua_m = entradas_muro.get("profundidade_nivel_agua_m")
    figura = go.Figure()
    cores_naturais = ("#eadfc8", "#dfceb0", "#d4bd9b", "#c9ac87", "#be9b74", "#b38b66")
    cores_saturadas = ("#c5dce5", "#b4d1dd", "#a4c6d5", "#94bbcd", "#84b0c5", "#74a5bd")

    profundidade_acumulada_m = 0.0
    for indice, camada in enumerate(camadas_solo, start=1):
        espessura_m = float(camada["espessura_m"])
        if espessura_m <= 0 or profundidade_acumulada_m >= altura_muro_m:
            continue
        topo_m = profundidade_acumulada_m
        base_m = min(altura_muro_m, topo_m + espessura_m)
        profundidade_acumulada_m += espessura_m
        cortes = [topo_m, base_m]
        if nivel_agua_m is not None and topo_m < float(nivel_agua_m) < base_m:
            cortes.insert(1, float(nivel_agua_m))
        for profundidade_topo_m, profundidade_base_m in zip(cortes, cortes[1:]):
            saturada = nivel_agua_m is not None and (
                profundidade_topo_m + profundidade_base_m
            ) / 2 >= float(nivel_agua_m)
            y_topo_m = altura_muro_m - profundidade_topo_m
            y_base_m = altura_muro_m - profundidade_base_m
            cor = (cores_saturadas if saturada else cores_naturais)[
                (indice - 1) % len(cores_naturais)
            ]
            y_superficie_extremo_m = (
                cota_superficie_lateral_m if profundidade_topo_m == 0 else y_topo_m
            )
            figura.add_trace(go.Scatter(
                x=[largura_base_m, x_limite_solo_m, x_limite_solo_m, largura_base_m, largura_base_m],
                y=[y_topo_m, y_superficie_extremo_m if profundidade_topo_m == 0 else y_topo_m, y_base_m, y_base_m, y_topo_m],
                fill="toself", fillcolor=cor,
                line={"color": "#807766", "width": 1}, mode="lines",
                showlegend=False,
                hovertemplate=(f"Camada {indice}<br>γ natural={float(camada['peso_especifico_natural_kN_m3']):.1f} kN/m³"
                    f"<br>γ saturado={float(camada['peso_especifico_saturado_kN_m3']):.1f} kN/m³"
                    f"<br>φ={float(camada['angulo_atrito_graus']):.1f}° · c={float(camada['coesao_kPa']):.1f} kPa<extra></extra>"),
            ))
        y_meio_m = altura_muro_m - (topo_m + base_m) / 2
        espessura_visivel_m = base_m - topo_m
        if espessura_visivel_m < 0.45:
            texto_camada = f"C{indice}"
            tamanho_fonte_camada = 8
        elif espessura_visivel_m < 1.1:
            texto_camada = (
                f"C{indice} · γ {float(camada['peso_especifico_natural_kN_m3']):.0f}"
                f" · φ {float(camada['angulo_atrito_graus']):.0f}°"
            )
            tamanho_fonte_camada = 8
        else:
            texto_camada = (
                f"CAMADA {indice}<br>γ={float(camada['peso_especifico_natural_kN_m3']):.1f}"
                f" · φ={float(camada['angulo_atrito_graus']):.1f}°"
            )
            tamanho_fonte_camada = 9
        figura.add_annotation(
            x=largura_base_m + extensao_solo_m * 0.74,
            y=y_meio_m,
            text=texto_camada,
            showarrow=False,
            font={"size": tamanho_fonte_camada, "color": "#34434a"},
            bgcolor="rgba(255,255,255,0.78)",
            bordercolor="rgba(91,108,113,0.5)",
            borderwidth=0.5,
            borderpad=2,
        )

    trechos_pressao = resultado_muro.get("trechos", [])
    pressao_total_por_trecho: list[tuple[float, float, float]] = []
    for trecho in trechos_pressao:
        pressao_superior_kPa = (
            float(trecho["pressao_solo_superior_kPa"])
            + float(trecho["pressao_sobrecarga_kPa"])
            + float(trecho["pressao_agua_superior_kPa"])
        )
        pressao_inferior_kPa = (
            float(trecho["pressao_solo_inferior_kPa"])
            + float(trecho["pressao_sobrecarga_kPa"])
            + float(trecho["pressao_agua_inferior_kPa"])
        )
        profundidade_meio_m = (
            float(trecho["profundidade_superior_m"])
            + float(trecho["profundidade_inferior_m"])
        ) / 2
        pressao_meio_kPa = max(0.0, (pressao_superior_kPa + pressao_inferior_kPa) / 2)
        pressao_total_por_trecho.append(
            (
                profundidade_meio_m,
                pressao_meio_kPa,
                max(pressao_superior_kPa, pressao_inferior_kPa),
            )
        )

    pressao_maxima_kPa = max(
        (item[2] for item in pressao_total_por_trecho), default=0.0
    )
    if pressao_maxima_kPa > 0:
        comprimento_maximo_seta_m = min(0.62, extensao_solo_m * 0.28)
        x_ponta_seta_m = largura_base_m + 0.08
        x_linhas_pressao: list[float | None] = []
        y_linhas_pressao: list[float | None] = []
        x_pontas_pressao: list[float] = []
        y_pontas_pressao: list[float] = []
        dados_hover_pressao: list[list[float]] = []
        for (
            profundidade_m,
            pressao_meio_kPa,
            pressao_referencia_kPa,
        ) in pressao_total_por_trecho:
            cota_m = altura_muro_m - profundidade_m
            fracao_pressao = pressao_referencia_kPa / pressao_maxima_kPa
            x_cauda_seta_m = (
                x_ponta_seta_m
                + 0.12
                + comprimento_maximo_seta_m * fracao_pressao
            )
            x_linhas_pressao.extend((x_cauda_seta_m, x_ponta_seta_m, None))
            y_linhas_pressao.extend((cota_m, cota_m, None))
            x_pontas_pressao.append(x_ponta_seta_m)
            y_pontas_pressao.append(cota_m)
            dados_hover_pressao.append([profundidade_m, pressao_meio_kPa])
        figura.add_trace(go.Scatter(
            x=x_linhas_pressao,
            y=y_linhas_pressao,
            mode="lines",
            line={"color": "#bd5146", "width": 2},
            hoverinfo="skip",
            showlegend=False,
        ))
        figura.add_trace(go.Scatter(
            x=x_pontas_pressao,
            y=y_pontas_pressao,
            mode="markers",
            marker={"symbol": "triangle-left", "size": 8, "color": "#bd5146"},
            customdata=dados_hover_pressao,
            hovertemplate=(
                "Pressão lateral total<br>z = %{customdata[0]:.2f} m"
                "<br>pₕ ≈ %{customdata[1]:.2f} kPa<extra></extra>"
            ),
            showlegend=False,
        ))

    figura.add_trace(go.Scatter(
        x=[p["x_m"] for p in resultado_muro["geometria_muro"]],
        y=[p["cota_y_m"] for p in resultado_muro["geometria_muro"]],
        fill="toself", fillcolor="#b9b8b1", line={"color": "#303a3c", "width": 2.5},
        mode="lines", name="Muro de concreto", hovertemplate="Muro de concreto<extra></extra>",
    ))
    figura.add_trace(go.Scatter(
        x=[largura_base_m, x_limite_solo_m],
        y=[altura_muro_m, cota_superficie_lateral_m], mode="lines",
        line={"color": "#33434a", "width": 2}, name="Superfície do aterro",
    ))
    figura.add_trace(go.Scatter(
        x=[largura_base_m, largura_base_m], y=[0, altura_muro_m], mode="lines",
        line={"color": "#303a3c", "width": 2.5}, showlegend=False,
    ))
    if nivel_agua_m is not None:
        cota_agua_m = altura_muro_m - float(nivel_agua_m)
        figura.add_trace(go.Scatter(
            x=[largura_base_m, x_limite_solo_m], y=[cota_agua_m, cota_agua_m],
            mode="lines", line={"color": "#177ba0", "width": 2, "dash": "dash"},
            name="Nível d’água",
        ))
        figura.add_annotation(x=x_limite_solo_m, y=cota_agua_m, text="N.A.", showarrow=False,
                              xshift=-24, font={"color": "#126b89", "size": 12})
    carga_q_kPa = float(entradas_muro["sobrecarga_kPa"])
    if carga_q_kPa > 0:
        posicoes_setas_m = []
        hastes_x = []
        hastes_y = []
        for indice_seta in range(8):
            x_seta_m = largura_base_m + (indice_seta + 0.5) * extensao_solo_m / 8
            y_superficie_m = altura_muro_m + (
                x_seta_m - largura_base_m
            ) * math.tan(inclinacao_aterro_rad)
            posicoes_setas_m.append((x_seta_m, y_superficie_m))
            hastes_x.extend((x_seta_m, x_seta_m, None))
            hastes_y.extend((y_superficie_m + 0.8, y_superficie_m + 0.12, None))
        figura.add_trace(go.Scatter(
            x=hastes_x, y=hastes_y, mode="lines",
            line={"color": "#2678b8", "width": 2.5},
            hoverinfo="skip", showlegend=False,
        ))
        figura.add_trace(go.Scatter(
            x=[posicao[0] for posicao in posicoes_setas_m],
            y=[posicao[1] + 0.12 for posicao in posicoes_setas_m],
            mode="markers",
            marker={"symbol": "triangle-down", "size": 11, "color": "#2678b8"},
            hoverinfo="skip", showlegend=False,
        ))
        figura.add_annotation(
            x=largura_base_m + extensao_solo_m / 2,
            y=cota_superficie_lateral_m + 1.0,
            text=f"Sobrecarga uniforme  q = {carga_q_kPa:.1f} kN/m²",
            showarrow=False, font={"size": 13, "color": "#225b86"},
        )
    figura.add_annotation(
        x=largura_base_m + extensao_solo_m * 0.78,
        y=altura_muro_m + extensao_solo_m * 0.78 * math.tan(inclinacao_aterro_rad),
        text=f"β = {float(entradas_muro['inclinacao_aterro_graus']):.1f}°",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#765b35",
        ax=38,
        ay=-35,
        font={"size": 11, "color": "#765b35"},
        bgcolor="rgba(255,255,255,0.88)",
    )
    figura.add_annotation(
        x=largura_base_m,
        y=altura_muro_m * 0.62,
        text=f"δ = {float(entradas_muro['atrito_solo_muro_graus']):.1f}°",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#7256a3",
        ax=42,
        ay=-5,
        font={"size": 11, "color": "#7256a3"},
        bgcolor="rgba(255,255,255,0.88)",
    )

    geometria = resultado_muro["verificacoes"]
    for y in (0,):
        figura.add_shape(type="line", x0=-0.5, x1=x_limite_solo_m + 0.4, y0=y, y1=y,
                         line={"color": "#66777b", "width": 1})
    figura.add_annotation(
        x=largura_base_m / 2,
        y=0,
        text=f"b = {largura_base_m:.2f} m",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#17374c",
        ax=0,
        ay=34,
        font={"size": 12, "color": "#17374c"},
    )
    figura.add_annotation(
        x=largura_base_m - largura_topo_m / 2,
        y=altura_muro_m,
        text=f"t = {largura_topo_m:.2f} m",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#17374c",
        ax=0,
        ay=-32,
        font={"size": 11, "color": "#17374c"},
    )
    x_cota_altura_m = -0.34
    figura.add_shape(
        type="line",
        x0=x_cota_altura_m,
        x1=x_cota_altura_m,
        y0=0,
        y1=altura_muro_m,
        line={"color": "#17374c", "width": 1.5},
    )
    for cota_extremo_m in (0.0, altura_muro_m):
        figura.add_shape(
            type="line",
            x0=x_cota_altura_m - 0.09,
            x1=x_cota_altura_m + 0.09,
            y0=cota_extremo_m,
            y1=cota_extremo_m,
            line={"color": "#17374c", "width": 1.5},
        )
    figura.add_annotation(
        x=x_cota_altura_m - 0.12,
        y=altura_muro_m / 2,
        text=f"H = {altura_muro_m:.2f} m",
        textangle=-90,
        showarrow=False,
        font={"size": 11, "color": "#17374c"},
        bgcolor="rgba(251,252,253,0.85)",
    )
    figura.add_annotation(x=largura_base_m + extensao_solo_m / 2, y=-0.55,
        text=f"f = {float(entradas_muro['coeficiente_atrito_base']):.2f}  ·  qadm = {float(entradas_muro['tensao_admissivel_fundacao_kPa']):.0f} kPa",
        showarrow=False, font={"size": 11, "color": "#485a61"})
    figura.add_annotation(x=largura_base_m * 0.48, y=altura_muro_m * 0.48,
        text=f"MURO DE CONCRETO<br>γc = {float(entradas_muro['peso_especifico_concreto_kN_m3']):.1f} kN/m³",
        showarrow=False, font={"size": 12, "color": "#303a3c"})
    figura.update_layout(
        title={"text": "SEÇÃO ESQUEMÁTICA · MURO DE ARRIMO", "x": 0.03},
        height=560, margin={"l": 70, "r": 35, "t": 70, "b": 55},
        paper_bgcolor="#fbfcfd", plot_bgcolor="#fbfcfd",
        xaxis={"range": [-0.8, x_limite_solo_m + 0.5], "title": "Seção transversal (m)", "showgrid": False, "zeroline": False},
        yaxis={
            "range": [-0.9, cota_superficie_lateral_m + 1.8],
            "title": "Cota (m)",
            "gridcolor": "#e3e9ec",
            "zeroline": False,
            "automargin": True,
        },
        autosize=True,
        showlegend=False,
    )
    return figura


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
st.info(
    "Nesta página, informe a geometria do muro, as camadas de solo, o nível d’água e as ações. "
    "O app calcula empuxos, tombamento, deslizamento e tensões na base; apresenta o croqui, "
    "a memória de cálculo e o desenho CAD para baixar."
)

# O botão do topo usa os valores atuais preservados no estado da sessão/navegador.
# Os arquivos ficam em cache até qualquer entrada mudar, para que baixar o PDF ou
# o DXF não dispare a compilação LaTeX outra vez.
dados_documentos_topo = _capturar_dados_dos_widgets()
erros_documentos_topo = validar_entradas_muro(
    dados_documentos_topo["entradas_muro"], dados_documentos_topo["camadas_solo"]
)
assinatura_documentos_topo = _assinatura_documentos(dados_documentos_topo)
pacote_documentos_topo = st.session_state.get("pacote_documentos_muro_topo")
if (
    isinstance(pacote_documentos_topo, dict)
    and pacote_documentos_topo.get("assinatura") != assinatura_documentos_topo
):
    st.session_state.pop("pacote_documentos_muro_topo", None)
    pacote_documentos_topo = None

coluna_gerar_documentos, coluna_texto_geracao = st.columns([1.15, 2.5], vertical_alignment="center")
with coluna_gerar_documentos:
    clicou_gerar_documentos = st.button(
        "Gerar CAD e relatório",
        type="primary",
        use_container_width=True,
        key="gerar_cad_relatorio_muro_topo",
        help="Usa as entradas atuais para preparar o DXF, o PDF didático e a fonte LaTeX/TikZ.",
    )
with coluna_texto_geracao:
    st.caption("Disponível no topo para gerar os arquivos sem rolar até o fim dos resultados.")

if clicou_gerar_documentos:
    if erros_documentos_topo:
        st.error("Corrija os dados do muro antes de gerar os arquivos: " + " ".join(erros_documentos_topo))
    else:
        entradas_topo = dados_documentos_topo["entradas_muro"]
        camadas_topo = dados_documentos_topo["camadas_solo"]
        with st.spinner("Calculando o muro e montando o CAD e o memorial em LaTeX..."):
            resultado_topo = calcular_muro(entradas_topo, camadas_topo)
            arquivo_dxf_topo = gerar_desenho_muro_dxf(
                entradas_topo, camadas_topo, resultado_topo
            )
            fonte_tex_topo = montar_relatorio_muro_tex(
                entradas_topo, camadas_topo, resultado_topo
            ).encode("utf-8")
            erro_pdf_topo = None
            try:
                arquivo_pdf_topo = compilar_relatorio_muro_pdf(fonte_tex_topo.decode("utf-8"))
            except ErroGeracaoRelatorio as erro:
                arquivo_pdf_topo = None
                erro_pdf_topo = str(erro)
            st.session_state["pacote_documentos_muro_topo"] = {
                "assinatura": assinatura_documentos_topo,
                "dxf": arquivo_dxf_topo,
                "pdf": arquivo_pdf_topo,
                "tex": fonte_tex_topo,
                "erro_pdf": erro_pdf_topo,
            }
            pacote_documentos_topo = st.session_state["pacote_documentos_muro_topo"]

if isinstance(pacote_documentos_topo, dict):
    st.success("Arquivos preparados com os valores atuais do muro.")
    colunas_download_topo = st.columns(3)
    colunas_download_topo[0].download_button(
        "Baixar CAD (.dxf)",
        data=pacote_documentos_topo["dxf"],
        file_name="muro_de_arrimo.dxf",
        mime="application/dxf",
        key="baixar_dxf_muro_arrimo_topo",
        use_container_width=True,
    )
    if pacote_documentos_topo["pdf"] is not None:
        colunas_download_topo[1].download_button(
            "Baixar relatório didático (.pdf)",
            data=pacote_documentos_topo["pdf"],
            file_name="memorial_didatico_muro_de_arrimo.pdf",
            mime="application/pdf",
            key="baixar_relatorio_muro_arrimo_topo",
            use_container_width=True,
        )
    else:
        colunas_download_topo[1].warning(
            "O PDF não compilou neste servidor; baixe a fonte .tex e compile no MiKTeX ou TeX Live."
        )
    colunas_download_topo[2].download_button(
        "Baixar fonte LaTeX/TikZ (.tex)",
        data=pacote_documentos_topo["tex"],
        file_name="memorial_didatico_muro_de_arrimo.tex",
        mime="application/x-tex",
        key="baixar_fonte_tex_muro_arrimo_topo",
        use_container_width=True,
    )
    if pacote_documentos_topo.get("erro_pdf"):
        with st.expander("Detalhes da compilação do PDF"):
            st.code(pacote_documentos_topo["erro_pdf"], language="text")

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
    dados_croqui = _capturar_dados_dos_widgets()
    entradas_croqui = dados_croqui["entradas_muro"]
    camadas_croqui = dados_croqui["camadas_solo"]
    erros_croqui = validar_entradas_muro(entradas_croqui, camadas_croqui)
    resultado_croqui = None
    if not erros_croqui:
        resultado_croqui = calcular_muro(entradas_croqui, camadas_croqui)
        coluna_croqui, coluna_simbolos = st.columns([2.2, 1], vertical_alignment="center")
        with coluna_croqui:
            st.markdown("**Croqui do muro e dos parâmetros inseridos**")
            figura_croqui = _montar_esquema_referencia(
                resultado_croqui, entradas_croqui, camadas_croqui
            )
            figura_croqui.update_layout(
                height=500,
                margin={"l": 55, "r": 20, "t": 55, "b": 45},
            )
            st.plotly_chart(
                figura_croqui,
                width="stretch",
                theme=None,
                config={"displayModeBar": False, "responsive": True},
            )
            st.caption(
                "As setas vermelhas mostram a pressão lateral total sobre o muro; "
                "passe o cursor para ver profundidade e pressão aproximada."
            )
        with coluna_simbolos:
            st.markdown("**Referências do croqui**")
            st.markdown(
                "**Geometria e terreno**\n"
                f"- H: altura do muro = {_formatar_numero(entradas_croqui['altura_muro_m'])} m\n"
                f"- b: largura da base = {_formatar_numero(entradas_croqui['largura_base_m'])} m\n"
                f"- t: largura do topo = {_formatar_numero(entradas_croqui['largura_topo_m'])} m\n"
                f"- β: inclinação do aterro = {_formatar_numero(entradas_croqui['inclinacao_aterro_graus'], 1)}°\n\n"
                "**Ações e contato**\n"
                f"- q: sobrecarga = {_formatar_numero(entradas_croqui['sobrecarga_kPa'])} kPa\n"
                f"- δ: atrito solo–muro = {_formatar_numero(entradas_croqui['atrito_solo_muro_graus'], 1)}°\n"
                f"- N.A.: profundidade = {_formatar_numero(entradas_croqui['profundidade_nivel_agua_m'])} m\n"
                f"- γw: peso específico da água = {_formatar_numero(entradas_croqui['peso_especifico_agua_kN_m3'])} kN/m³\n"
                f"- Teoria de empuxo: {entradas_croqui['metodo_empuxo']}\n\n"
                "**Materiais e fundação**\n"
                f"- γc: peso específico do concreto = {_formatar_numero(entradas_croqui['peso_especifico_concreto_kN_m3'])} kN/m³\n"
                f"- f: atrito na base = {_formatar_numero(entradas_croqui['coeficiente_atrito_base'], 2)}\n"
                f"- qadm: tensão admissível = {_formatar_numero(entradas_croqui['tensao_admissivel_fundacao_kPa'])} kPa\n"
                f"- FS mínimo: tombamento = {_formatar_numero(entradas_croqui['fator_seguranca_minimo_tombamento'], 2)}; "
                f"deslizamento = {_formatar_numero(entradas_croqui['fator_seguranca_minimo_deslizamento'], 2)}\n"
                "- Camadas: espessura, γ natural/saturado, φ e c conforme os campos abaixo."
            )
    else:
        st.info("O croqui aparece quando os campos formarem uma geometria e um perfil de solo válidos.")

    if resultado_croqui is not None:
        st.divider()
        _mostrar_resumo_principal(resultado_croqui["verificacoes"])

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
            help=(
                "β define uma única superfície do aterro. Em Rankine, o Kₐ é calculado "
                "com o φ de cada camada; exige c = 0 e β < φ em todas as camadas."
            ),
        )
        st.caption(
            "β vale para todo o perfil; Rankine calcula Kₐ com o φ de cada camada. "
            "Para Coulomb, este modelo ainda requer uma camada."
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
    coluna_seis_camadas, coluna_uma_camada, coluna_dica_camadas = st.columns(
        [1.15, 1.2, 2.2], vertical_alignment="center"
    )
    with coluna_seis_camadas:
        st.button(
            "Preencher 6 camadas padrão",
            on_click=_preencher_seis_camadas_padrao,
            use_container_width=True,
            key="preencher_seis_camadas_muro",
            help=(
                "Divide a altura do muro igualmente entre seis camadas e alterna os dois "
                "perfis de solo do exemplo da planilha."
            ),
        )
    with coluna_uma_camada:
        st.button(
            "Manter somente 1 camada",
            on_click=_limpar_para_uma_camada,
            use_container_width=True,
            key="limpar_camadas_muro",
            help="Atribui toda a altura à Camada 1 e zera as Camadas 2 a 6.",
        )
    with coluna_dica_camadas:
        st.caption(
            "Os valores-padrão são editáveis; a altura total continua igual a H."
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
    resultado_muro = resultado_croqui or calcular_muro(entradas_muro, camadas_solo)
    resumo = resultado_muro["resumo"]
    verificacoes = resultado_muro["verificacoes"]

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
    with st.expander("Memorial passo a passo · como fazer o cálculo à mão"):
        st.markdown(
            montar_memorial_passo_a_passo_muro(
                entradas_muro, camadas_solo, resultado_muro
            )
        )
