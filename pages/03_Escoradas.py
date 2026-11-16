from __future__ import annotations

import json
import math
from copy import deepcopy
from typing import Any

import plotly.graph_objects as go
import streamlit as st
from streamlit_local_storage import LocalStorage

from contencoes.calculos_escoradas import (
    MODELOS_ENVOLTORIA,
    calcular_froehlich,
    calcular_graux,
    calcular_pressao_aparente,
    calcular_ruptura_fundo,
    carregar_exemplos_escoradas,
    validar_froehlich,
    validar_graux,
    validar_pressao_aparente,
    validar_ruptura_fundo,
)


st.set_page_config(page_title="Escoradas | Contenções", page_icon="🏗️", layout="wide")

CHAVE_ARMAZENAMENTO_NAVEGADOR = "projeto_contencoes_escoradas_v1"
CHAVE_ESTADO_DA_SESSAO = "dados_escoradas_preservados_na_sessao"
CAMPOS_POR_CASO = {
    nome_caso: tuple(dados_caso)
    for nome_caso, dados_caso in carregar_exemplos_escoradas().items()
}


def _chave_widget(nome_caso: str, nome_campo: str) -> str:
    return f"escoradas_{nome_caso}_{nome_campo}"


def _normalizar_dados_salvos(dados_salvos: Any) -> dict[str, dict[str, Any]]:
    dados = carregar_exemplos_escoradas()
    if not isinstance(dados_salvos, dict):
        return dados

    for nome_caso, nomes_campos in CAMPOS_POR_CASO.items():
        valores_caso = dados_salvos.get(nome_caso)
        if not isinstance(valores_caso, dict):
            continue
        for nome_campo in nomes_campos:
            valor = valores_caso.get(nome_campo)
            if nome_campo == "tipo_solo":
                if valor in MODELOS_ENVOLTORIA:
                    dados[nome_caso][nome_campo] = valor
            elif (
                isinstance(valor, (int, float))
                and not isinstance(valor, bool)
                and math.isfinite(valor)
            ):
                dados[nome_caso][nome_campo] = valor
    return dados


def _aplicar_dados_aos_widgets(dados: dict[str, dict[str, Any]]) -> None:
    for nome_caso, nomes_campos in CAMPOS_POR_CASO.items():
        for nome_campo in nomes_campos:
            st.session_state[_chave_widget(nome_caso, nome_campo)] = dados[nome_caso][nome_campo]


def _restaurar_exemplos() -> None:
    _aplicar_dados_aos_widgets(carregar_exemplos_escoradas())


def _capturar_dados_dos_widgets() -> dict[str, dict[str, Any]]:
    return {
        nome_caso: {
            nome_campo: st.session_state.get(_chave_widget(nome_caso, nome_campo))
            for nome_campo in nomes_campos
        }
        for nome_caso, nomes_campos in CAMPOS_POR_CASO.items()
    }


def _formatar_numero(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _mostrar_erros(erros: list[str]) -> None:
    st.error("Revise os dados antes de consultar o resultado.")
    for erro in erros:
        st.markdown(f"- {erro}")


def _mostrar_grafico_pressao(
    pontos: list[dict[str, float]],
    altura_escavacao_m: float,
    titulo: str,
    cor: str,
    cor_preenchimento: str,
) -> None:
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=[ponto["pressao_kPa"] for ponto in pontos],
            y=[ponto["profundidade_m"] for ponto in pontos],
            mode="lines",
            line={"color": cor, "width": 3},
            fill="tozerox",
            fillcolor=cor_preenchimento,
            hovertemplate="Pressão: %{x:.2f} kPa<br>Profundidade: %{y:.2f} m<extra></extra>",
            showlegend=False,
        )
    )
    figura.update_layout(
        title=titulo,
        height=390,
        margin={"l": 70, "r": 25, "t": 55, "b": 55},
        xaxis_title="Pressão horizontal (kPa)",
        yaxis_title="Profundidade abaixo da superfície (m)",
        hovermode="closest",
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    figura.update_xaxes(rangemode="tozero", showgrid=True, gridcolor="#e8eeeb")
    figura.update_yaxes(range=[altura_escavacao_m, 0], showgrid=True, gridcolor="#e8eeeb")
    st.plotly_chart(figura, width="stretch", theme=None)


armazenamento_local = LocalStorage(key="armazenamento_contencoes")
aviso_armazenamento = None
if "dados_escoradas_inicializados" not in st.session_state:
    texto_salvo = armazenamento_local.getItem(CHAVE_ARMAZENAMENTO_NAVEGADOR)
    try:
        dados_salvos = json.loads(texto_salvo) if isinstance(texto_salvo, str) else texto_salvo
    except (json.JSONDecodeError, TypeError):
        dados_salvos = None
        aviso_armazenamento = "O rascunho salvo não pôde ser lido; carreguei os exemplos da planilha."
    dados_iniciais = _normalizar_dados_salvos(dados_salvos)
    _aplicar_dados_aos_widgets(dados_iniciais)
    st.session_state[CHAVE_ESTADO_DA_SESSAO] = dados_iniciais
    st.session_state["dados_escoradas_inicializados"] = True
else:
    dados_da_sessao = st.session_state.get(CHAVE_ESTADO_DA_SESSAO)
    chaves_widget = [
        _chave_widget(nome_caso, nome_campo)
        for nome_caso, nomes_campos in CAMPOS_POR_CASO.items()
        for nome_campo in nomes_campos
    ]
    if isinstance(dados_da_sessao, dict) and any(
        chave not in st.session_state for chave in chaves_widget
    ):
        _aplicar_dados_aos_widgets(_normalizar_dados_salvos(dados_da_sessao))


st.markdown("<style>.block-container{padding-top:1.5rem;padding-bottom:3rem}</style>", unsafe_allow_html=True)
st.title("⌁ Estruturas escoradas")
st.caption(
    "Envoltórias de Terzaghi–Peck, força aproximada nas escoras e três verificações "
    "geotécnicas simplificadas da planilha."
)
if aviso_armazenamento:
    st.warning(aviso_armazenamento)
with st.expander("Sobre o salvamento dos dados"):
    st.write(
        "As entradas ficam neste navegador e voltam ao reabrir a página no mesmo dispositivo. "
        "A limpeza dos dados do navegador apaga esse rascunho; os valores não são sincronizados entre dispositivos."
    )

coluna_botao_exemplo, coluna_referencia = st.columns([1, 2])
with coluna_botao_exemplo:
    st.button(
        "Restaurar exemplos da planilha",
        on_click=_restaurar_exemplos,
        use_container_width=True,
    )
with coluna_referencia:
    st.caption(
        "Pressões em areia: H = 6 m, q = 12 kPa, γ = 20 kN/m³, φ = 30°. "
        "As outras verificações carregam seus exemplos da planilha."
    )

aba_pressao, aba_fundo, aba_graux, aba_froehlich = st.tabs(
    ["Pressões e escoras", "Ruptura de fundo", "Critério de Graux", "Profundidade crítica"]
)

with aba_pressao:
    st.subheader("Pressão aparente e carga por escora")
    colunas_entrada = st.columns(3)
    with colunas_entrada[0]:
        st.selectbox(
            "Tipo de solo e modelo de pressão",
            MODELOS_ENVOLTORIA,
            key=_chave_widget("pressao_aparente", "tipo_solo"),
        )
        st.number_input(
            "Altura da escavação, H (m)",
            min_value=0.01,
            step=0.1,
            key=_chave_widget("pressao_aparente", "altura_escavacao_m"),
        )
        st.number_input(
            "Sobrecarga uniforme na superfície, q (kPa)",
            min_value=0.0,
            step=1.0,
            key=_chave_widget("pressao_aparente", "sobrecarga_superficie_kPa"),
        )
        st.number_input(
            "Peso específico do solo, γ (kN/m³)",
            min_value=0.01,
            step=0.5,
            key=_chave_widget("pressao_aparente", "peso_especifico_solo_kN_m3"),
        )
    with colunas_entrada[1]:
        st.number_input(
            "Ângulo de atrito do solo, φ (°)",
            min_value=0.0,
            max_value=89.9,
            step=1.0,
            key=_chave_widget("pressao_aparente", "angulo_atrito_solo_graus"),
        )
        st.number_input(
            "Coesão não drenada da argila, cu (kPa)",
            min_value=0.0,
            step=1.0,
            key=_chave_widget("pressao_aparente", "coesao_nao_drenada_kPa"),
        )
        st.number_input(
            "Coeficiente empírico da argila, m",
            min_value=0.01,
            step=0.1,
            key=_chave_widget("pressao_aparente", "coeficiente_empirico_argila"),
        )
        st.number_input(
            "Níveis de escoras, n",
            min_value=1,
            max_value=20,
            step=1,
            key=_chave_widget("pressao_aparente", "quantidade_niveis_escora"),
            help="Número de níveis horizontais que dividem a resultante no modelo simplificado.",
        )
    with colunas_entrada[2]:
        st.number_input(
            "Espaçamento longitudinal entre escoras, e (m)",
            min_value=0.01,
            step=0.1,
            key=_chave_widget("pressao_aparente", "espacamento_longitudinal_escoras_m"),
            help="Largura tributária de parede considerada para cada escora.",
        )
        st.number_input(
            "Profundidade do nível d'água desde a superfície, zNA (m)",
            min_value=0.0,
            step=0.1,
            key=_chave_widget("pressao_aparente", "profundidade_nivel_agua_m"),
            help="zNA = H significa que o nível d'água está no fundo da escavação e não gera pressão no corte.",
        )
        st.number_input(
            "Peso específico da água, γw (kN/m³)",
            min_value=0.01,
            step=0.1,
            key=_chave_widget("pressao_aparente", "peso_especifico_agua_kN_m3"),
        )
        st.caption(
            "A força por escora divide igualmente a resultante pela quantidade de níveis e pela faixa e."
        )

    entradas_pressao = {
        nome_campo: st.session_state[_chave_widget("pressao_aparente", nome_campo)]
        for nome_campo in CAMPOS_POR_CASO["pressao_aparente"]
    }
    erros_pressao = validar_pressao_aparente(entradas_pressao)
    if erros_pressao:
        _mostrar_erros(erros_pressao)
    else:
        resultado_pressao = calcular_pressao_aparente(entradas_pressao)
        st.divider()
        colunas_resultados = st.columns(5)
        colunas_resultados[0].metric(
            "Pressão aparente máxima",
            f"{_formatar_numero(resultado_pressao['pressao_aparente_maxima_kPa'])} kPa",
        )
        colunas_resultados[1].metric(
            "Resultante aparente por metro",
            f"{_formatar_numero(resultado_pressao['resultante_aparente_kN_m'])} kN/m",
        )
        colunas_resultados[2].metric(
            "Resultante da água no corte",
            f"{_formatar_numero(resultado_pressao['resultante_hidrostatica_kN_m'])} kN/m",
        )
        colunas_resultados[3].metric(
            "Resultante horizontal total",
            f"{_formatar_numero(resultado_pressao['resultante_total_kN_m'])} kN/m",
        )
        colunas_resultados[4].metric(
            "Força axial aproximada por escora",
            f"{_formatar_numero(resultado_pressao['forca_axial_aproximada_por_escora_kN'])} kN",
        )
        st.caption(
            "Braço da resultante total desde o fundo: "
            f"{_formatar_numero(resultado_pressao['braco_resultante_desde_fundo_m'])} m. "
            "A estimativa adota divisão igual da carga entre os níveis de escoras."
        )

        with st.expander("Memória de cálculo da pressão aparente"):
            st.latex(r"K_a=\tan^2\left(45^\circ-\frac{\varphi}{2}\right)")
            if entradas_pressao["tipo_solo"] == MODELOS_ENVOLTORIA[0]:
                st.latex(r"p_{max}=0{,}65(\gamma H+q)K_a \qquad E_{app}=p_{max}H")
            elif entradas_pressao["tipo_solo"] == MODELOS_ENVOLTORIA[1]:
                st.latex(
                    r"K_{a,mod}=1-m\frac{4c_u}{\gamma H}"
                    r"\qquad p_{max}=m\gamma H\max(0,K_{a,mod})"
                )
                st.latex(r"E_{app}=0{,}75p_{max}H")
            else:
                st.latex(r"p_{max}=0{,}20\gamma H \qquad E_{app}=0{,}75p_{max}H")
            st.latex(
                r"E_w=\frac{\gamma_w(H-z_{NA})_+^2}{2}"
                r"\qquad E=E_{app}+E_w"
            )
            st.latex(
                r"y_R=\frac{E_{app}H/2+E_w(H-z_{NA})_+/3}{E}"
                r"\qquad N=\frac{Ee}{n}"
            )
            linhas_memoria = [
                {"Grandeza": "Coeficiente ativo de Rankine, Ka", "Valor": _formatar_numero(resultado_pressao["coeficiente_ativo_rankine"], 4), "Unidade": "—"},
                {"Grandeza": "Coeficiente ativo modificado da argila, Ka,mod", "Valor": _formatar_numero(resultado_pressao["coeficiente_ativo_modificado"], 4), "Unidade": "—"},
                {"Grandeza": "Resultante aparente, Eapp", "Valor": _formatar_numero(resultado_pressao["resultante_aparente_kN_m"]), "Unidade": "kN/m"},
                {"Grandeza": "Resultante hidrostática, Ew", "Valor": _formatar_numero(resultado_pressao["resultante_hidrostatica_kN_m"]), "Unidade": "kN/m"},
                {"Grandeza": "Resultante horizontal total, E", "Valor": _formatar_numero(resultado_pressao["resultante_total_kN_m"]), "Unidade": "kN/m"},
                {"Grandeza": "Braço desde o fundo, yR", "Valor": _formatar_numero(resultado_pressao["braco_resultante_desde_fundo_m"]), "Unidade": "m"},
                {"Grandeza": "Força aproximada em cada escora, N", "Valor": _formatar_numero(resultado_pressao["forca_axial_aproximada_por_escora_kN"]), "Unidade": "kN"},
            ]
            st.dataframe(linhas_memoria, hide_index=True, width="stretch")
            st.caption(
                "Areia: diagrama retangular. Argilas: transições lineares de 0,25H no topo e na base "
                "com patamar central de 0,50H, conforme a planilha."
            )
            if entradas_pressao["tipo_solo"] == MODELOS_ENVOLTORIA[2]:
                st.warning(
                    "Diferença de referência: a planilha usa pmax = 0,20γH para argila dura/fissurada. "
                    "O slide 14 das aulas também apresenta uma faixa de 0,28γH a 0,40γH no patamar. "
                    "O resultado segue a fórmula da planilha."
                )

        st.subheader("Envoltória de pressão aparente do solo")
        st.caption("Este gráfico mostra somente a parcela do solo; a pressão da água aparece em separado abaixo.")
        _mostrar_grafico_pressao(
            resultado_pressao["diagrama_pressao_aparente"],
            entradas_pressao["altura_escavacao_m"],
            "Pressão aparente do solo",
            "#c34b3c",
            "rgba(195, 75, 60, 0.14)",
        )
        st.subheader("Pressão hidrostática no trecho escavado")
        if resultado_pressao["diagrama_pressao_agua"]:
            st.caption("A distribuição triangular começa no nível d'água e termina no fundo da escavação.")
            _mostrar_grafico_pressao(
                resultado_pressao["diagrama_pressao_agua"],
                entradas_pressao["altura_escavacao_m"],
                "Pressão da água",
                "#3182a8",
                "rgba(49, 130, 168, 0.16)",
            )
        else:
            st.info("zNA está no fundo ou abaixo dele; não há pressão hidrostática dentro do corte.")

with aba_fundo:
    st.subheader("Ruptura de fundo em argila não drenada")
    st.caption("Modelo de Terzaghi para o mecanismo simplificado mostrado nas aulas.")
    colunas_entrada_fundo = st.columns(5)
    for coluna, (rotulo, campo, minimo, passo) in zip(
        colunas_entrada_fundo,
        (
            ("Altura da escavação, H (m)", "altura_escavacao_m", 0.01, 0.1),
            ("Largura da escavação, B (m)", "largura_escavacao_m", 0.01, 0.1),
            ("Peso específico do solo, γ (kN/m³)", "peso_especifico_solo_kN_m3", 0.01, 0.5),
            ("Coesão não drenada, cu (kPa)", "coesao_nao_drenada_kPa", 0.0, 1.0),
            ("FS mínimo de referência", "fator_seguranca_minimo", 0.01, 0.1),
        ),
    ):
        coluna.number_input(
            rotulo,
            min_value=minimo,
            step=passo,
            key=_chave_widget("ruptura_fundo", campo),
        )
    entradas_fundo = {
        nome_campo: st.session_state[_chave_widget("ruptura_fundo", nome_campo)]
        for nome_campo in CAMPOS_POR_CASO["ruptura_fundo"]
    }
    erros_fundo = validar_ruptura_fundo(entradas_fundo)
    if erros_fundo:
        _mostrar_erros(erros_fundo)
    else:
        resultado_fundo = calcular_ruptura_fundo(entradas_fundo)
        colunas_resultado_fundo = st.columns(4)
        colunas_resultado_fundo[0].metric(
            "Tensão solicitante no fundo, σz",
            f"{_formatar_numero(resultado_fundo['tensao_vertical_solicitante_kPa'])} kPa",
        )
        colunas_resultado_fundo[1].metric(
            "Resistência adotada, σr = 5,7cu",
            f"{_formatar_numero(resultado_fundo['resistencia_nao_drenada_kPa'])} kPa",
        )
        colunas_resultado_fundo[2].metric(
            "Fator de segurança, FS",
            _formatar_numero(resultado_fundo["fator_seguranca"]),
            resultado_fundo["status"],
        )
        colunas_resultado_fundo[3].metric(
            "Profundidade crítica, Hcr",
            f"{_formatar_numero(resultado_fundo['profundidade_critica_m'])} m",
        )
        if resultado_fundo["tensao_solicitante_fora_do_dominio"]:
            st.warning(
                "A tensão solicitante ficou menor ou igual a zero. A planilha retorna FS = 0 nesse caso; "
                "esse valor é um marcador de revisão, não um fator de segurança físico válido."
            )
        with st.expander("Memória de cálculo da ruptura de fundo"):
            st.latex(r"\sigma_z=\gamma H-\frac{2}{B}Hc_u")
            st.latex(r"\sigma_r=5{,}7c_u \qquad FS=\frac{\sigma_r}{\sigma_z}")
            st.latex(r"H_{cr}=\frac{5{,}7c_u}{\gamma-2c_u/B}")
            st.dataframe(
                [
                    {"Grandeza": "σz · tensão solicitante no fundo", "Valor": _formatar_numero(resultado_fundo["tensao_vertical_solicitante_kPa"]), "Unidade": "kPa"},
                    {"Grandeza": "σr · resistência do solo não drenado", "Valor": _formatar_numero(resultado_fundo["resistencia_nao_drenada_kPa"]), "Unidade": "kPa"},
                    {"Grandeza": "FS · razão entre resistência e solicitação", "Valor": _formatar_numero(resultado_fundo["fator_seguranca"]), "Unidade": "—"},
                    {"Grandeza": "Hcr · profundidade crítica de fundo", "Valor": _formatar_numero(resultado_fundo["profundidade_critica_m"]), "Unidade": "m"},
                ],
                hide_index=True,
                width="stretch",
            )
            st.caption("A expressão não considera efeitos tridimensionais nem água.")

with aba_graux:
    st.subheader("Sifonamento e estabilidade hidráulica · Graux")
    st.caption("Modelo simplificado de percolação ao longo da ficha e equilíbrio no fundo.")
    colunas_entrada_graux = st.columns(4)
    for coluna, (rotulo, campo, minimo, passo) in zip(
        colunas_entrada_graux,
        (
            ("Altura escavada, H (m)", "altura_escavacao_m", 0.01, 0.1),
            ("Diferença de carga d'água, Z (m)", "diferenca_carga_agua_m", 0.0, 0.1),
            ("Ficha abaixo do fundo, D (m)", "ficha_abaixo_fundo_m", 0.01, 0.1),
            ("Peso específico natural, γn (kN/m³)", "peso_especifico_natural_kN_m3", 0.01, 0.5),
        ),
    ):
        coluna.number_input(rotulo, min_value=minimo, step=passo, key=_chave_widget("graux", campo))
    colunas_entrada_graux_2 = st.columns(4)
    for coluna, (rotulo, campo, minimo, passo) in zip(
        colunas_entrada_graux_2,
        (
            ("Peso específico submerso, γsub (kN/m³)", "peso_especifico_submerso_kN_m3", 0.01, 0.5),
            ("Ângulo de atrito, φ (°)", "angulo_atrito_solo_graus", 0.0, 1.0),
            ("Peso específico da água, γw (kN/m³)", "peso_especifico_agua_kN_m3", 0.01, 0.1),
            ("FS mínimo de referência", "fator_seguranca_minimo", 0.01, 0.1),
        ),
    ):
        coluna.number_input(
            rotulo,
            min_value=minimo,
            max_value=89.9 if campo == "angulo_atrito_solo_graus" else None,
            step=passo,
            key=_chave_widget("graux", campo),
        )
    entradas_graux = {
        nome_campo: st.session_state[_chave_widget("graux", nome_campo)]
        for nome_campo in CAMPOS_POR_CASO["graux"]
    }
    erros_graux = validar_graux(entradas_graux)
    if erros_graux:
        _mostrar_erros(erros_graux)
    else:
        resultado_graux = calcular_graux(entradas_graux)
        colunas_resultado_graux = st.columns(4)
        colunas_resultado_graux[0].metric(
            "Comprimento de percolação, L",
            f"{_formatar_numero(resultado_graux['comprimento_percolacao_m'])} m",
        )
        colunas_resultado_graux[1].metric(
            "Gradiente hidráulico médio, i",
            _formatar_numero(resultado_graux["gradiente_hidraulico"], 3),
        )
        colunas_resultado_graux[2].metric(
            "Fator de capacidade de carga, Nq",
            _formatar_numero(resultado_graux["fator_capacidade_carga_nq"], 2),
        )
        colunas_resultado_graux[3].metric(
            "Fator de segurança hidráulico, FS",
            _formatar_numero(resultado_graux["fator_seguranca"]),
            resultado_graux["status"],
        )
        with st.expander("Memória de cálculo do critério de Graux"):
            st.latex(r"L=Z+2D \qquad i=\frac{Z}{L}")
            st.latex(r"\sigma_e=(H-Z)_+\gamma_n+(Z+D)(\gamma_{sub}+i\gamma_w)")
            st.latex(r"\sigma_i=D(\gamma_{sub}-i\gamma_w)_+")
            st.latex(
                r"N_q=\tan^2\left(45^\circ+\frac{\varphi}{2}\right)"
                r"e^{\pi\tan\varphi}"
                r"\qquad FS=\frac{\sigma_iN_q}{\sigma_e}"
            )
            st.dataframe(
                [
                    {"Grandeza": "σe · tensão solicitante exterior", "Valor": _formatar_numero(resultado_graux["tensao_exterior_kPa"]), "Unidade": "kPa"},
                    {"Grandeza": "σi · tensão efetiva interior", "Valor": _formatar_numero(resultado_graux["tensao_interior_kPa"]), "Unidade": "kPa"},
                    {"Grandeza": "Nq · fator de capacidade de carga", "Valor": _formatar_numero(resultado_graux["fator_capacidade_carga_nq"], 3), "Unidade": "—"},
                    {"Grandeza": "FS · fator de segurança hidráulico", "Valor": _formatar_numero(resultado_graux["fator_seguranca"]), "Unidade": "—"},
                ],
                hide_index=True,
                width="stretch",
            )
        st.info(
            "Diferença no exemplo da aula (φ = 30°): a fórmula da planilha resulta em "
            "Nq ≈ 18,40 e FS ≈ 5,14; o slide 34 informa Nq ≈ 20,3 e FS ≈ 5,7. "
            "Este resultado segue a fórmula usada na planilha."
        )

with aba_froehlich:
    st.subheader("Profundidade crítica de corte vertical sem suporte")
    st.caption("Expressão teórica de Fröhlich; compara a altura informada com Hcr.")
    colunas_entrada_froehlich = st.columns(4)
    for coluna, (rotulo, campo, minimo, passo) in zip(
        colunas_entrada_froehlich,
        (
            ("Peso específico do solo, γ (kN/m³)", "peso_especifico_solo_kN_m3", 0.01, 0.5),
            ("Coesão do solo, c (kPa)", "coesao_solo_kPa", 0.0, 1.0),
            ("Ângulo de atrito, φ (°)", "angulo_atrito_solo_graus", 0.0, 1.0),
            ("Altura avaliada, H (m)", "altura_escavacao_m", 0.0, 0.1),
        ),
    ):
        coluna.number_input(
            rotulo,
            min_value=minimo,
            max_value=89.9 if campo == "angulo_atrito_solo_graus" else None,
            step=passo,
            key=_chave_widget("froehlich", campo),
        )
    entradas_froehlich = {
        nome_campo: st.session_state[_chave_widget("froehlich", nome_campo)]
        for nome_campo in CAMPOS_POR_CASO["froehlich"]
    }
    erros_froehlich = validar_froehlich(entradas_froehlich)
    if erros_froehlich:
        _mostrar_erros(erros_froehlich)
    else:
        resultado_froehlich = calcular_froehlich(entradas_froehlich)
        colunas_resultado_froehlich = st.columns(3)
        colunas_resultado_froehlich[0].metric(
            "Profundidade crítica teórica, Hcr",
            f"{_formatar_numero(resultado_froehlich['altura_critica_m'])} m",
        )
        colunas_resultado_froehlich[1].metric(
            "Altura de escavação avaliada, H",
            f"{_formatar_numero(resultado_froehlich['altura_escavacao_m'])} m",
        )
        colunas_resultado_froehlich[2].metric("Condição", resultado_froehlich["status"])
        with st.expander("Memória de cálculo de Fröhlich"):
            st.latex(r"H_{cr}=\frac{4c}{\gamma}\tan\left(45^\circ+\frac{\varphi}{2}\right)")
            st.markdown(
                "Se **H ≤ Hcr**, a altura fica dentro do limite teórico do modelo. "
                "Se **H > Hcr**, o modelo indica necessidade de escoramento."
            )
            st.caption(
                "Para solo sem coesão (c = 0), esta expressão fornece Hcr = 0. "
                "Não considera água, sobrecargas nem outras condições do maciço."
            )

dados_formulario = _capturar_dados_dos_widgets()
st.session_state[CHAVE_ESTADO_DA_SESSAO] = deepcopy(dados_formulario)
armazenamento_local.setItem(
    CHAVE_ARMAZENAMENTO_NAVEGADOR,
    json.dumps(dados_formulario, ensure_ascii=False),
    key="salvar_entradas_escoradas",
)

st.divider()
st.caption(
    "Limites: cargas distribuídas igualmente entre níveis de escoras; não inclui dimensionamento "
    "estrutural nem flambagem. As verificações de fundo, Graux e Fröhlich são separadas e seguem "
    "as hipóteses simplificadas da planilha e das aulas."
)
