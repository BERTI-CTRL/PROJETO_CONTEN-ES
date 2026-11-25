from __future__ import annotations

import json
from copy import deepcopy
from functools import partial
from typing import Any

import streamlit as st
from streamlit_local_storage import LocalStorage

from contencoes.cad.exportar_estaca_prancha_dxf import (
    gerar_dxf_cortina_em_balanco,
    gerar_dxf_cortina_ancorada,
)
from contencoes.calculos.calculos_estaca_prancha import (
    calcular_cortina_ancorada,
    calcular_cortina_em_balanco,
    carregar_exemplos_estaca_prancha,
    validar_entradas_cortina_ancorada,
    validar_entradas_cortina_em_balanco,
)
from contencoes.svg.svg_estaca_prancha import (
    gerar_svg_cortina_ancorada,
    gerar_svg_cortina_em_balanco,
)
from contencoes.visualizacao.visualizacao_estaca_prancha import (
    formatar_numero,
    mostrar_diagrama_pressao_cortina_em_balanco,
    mostrar_memoria_cortina_em_balanco,
    mostrar_diagrama_pressao_cortina_ancorada,
    mostrar_memoria_cortina_ancorada,
)

from contencoes.visualizacao.download_corte_dxf import mostrar_download_corte


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
    "peso_especifico_agua_kN_m3",
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

aba_balanco, aba_ancorada = st.tabs(
    ["1–3. Cortina em balanço", "4–6. Cortina ancorada"]
)

with aba_balanco:
    st.subheader("1. Entradas · solo granular homogêneo")
    download_balanco = st.container()
    croqui_balanco = st.empty()
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
        mostrar_download_corte(download_balanco, "cortina_em_balanco")
        st.error("Revise os dados antes de consultar a ficha.")
        for erro in erros_balanco:
            st.markdown(f"- {erro}")
    else:
        resultado_balanco = calcular_cortina_em_balanco(entradas_balanco)
        croqui_balanco.markdown(
            gerar_svg_cortina_em_balanco(entradas_balanco, resultado_balanco),
            unsafe_allow_html=True,
        )
        mostrar_download_corte(
            download_balanco, "cortina_em_balanco",
            partial(gerar_dxf_cortina_em_balanco, entradas_balanco, resultado_balanco),
        )
        st.divider()
        st.subheader("2. Resultados da ficha")
        colunas_resultado_balanco = st.columns(4)
        colunas_resultado_balanco[0].metric(
            "Coeficiente ativo, Kₐ",
            formatar_numero(resultado_balanco["coeficiente_ativo_rankine"], 3),
        )
        colunas_resultado_balanco[1].metric(
            "Passivo mobilizado, Kₚ,mob",
            formatar_numero(resultado_balanco["coeficiente_passivo_mobilizado"], 3),
        )
        colunas_resultado_balanco[2].metric(
            "Ficha teórica, f",
            f"{formatar_numero(resultado_balanco['ficha_teorica_m'])} m",
        )
        colunas_resultado_balanco[3].metric(
            "Ficha preliminar",
            f"{formatar_numero(resultado_balanco['ficha_preliminar_m'])} m",
        )
        st.caption(
            "A ficha teórica reproduz o equilíbrio de momentos da planilha; a ficha preliminar "
            "inclui o acréscimo prático informado."
        )
        st.subheader("3. Diagrama de pressões")
        st.caption("As pressões ativas e passivas aparecem em lados opostos do eixo zero.")
        mostrar_diagrama_pressao_cortina_em_balanco(resultado_balanco)
        mostrar_memoria_cortina_em_balanco(resultado_balanco)

with aba_ancorada:
    st.subheader("4. Entradas · duas camadas e ficha conhecida")
    download_ancorada = st.container()
    croqui_ancorada = st.empty()
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
        st.number_input(
            "Peso específico da água, γw (kN/m³)",
            min_value=0.0,
            step=0.1,
            key=_chave_widget("cortina_ancorada", "peso_especifico_agua_kN_m3"),
            help="Água no tardoz e lado escavado drenado. Use 0 para anular a parcela diferencial.",
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
        mostrar_download_corte(download_ancorada, "cortina_ancorada")
        st.error("Revise os dados antes de consultar os resultados.")
        for erro in erros_ancorada:
            st.markdown(f"- {erro}")
    else:
        resultado_ancorada = calcular_cortina_ancorada(entradas_ancorada)
        croqui_ancorada.markdown(
            gerar_svg_cortina_ancorada(entradas_ancorada, resultado_ancorada),
            unsafe_allow_html=True,
        )
        mostrar_download_corte(
            download_ancorada, "cortina_ancorada",
            partial(gerar_dxf_cortina_ancorada, entradas_ancorada, resultado_ancorada),
        )
        st.divider()
        st.subheader("5. Resultados da cortina ancorada")
        colunas_resultado_ancorada = st.columns(5)
        colunas_resultado_ancorada[0].metric(
            "Empuxo ativo do solo",
            f"{formatar_numero(resultado_ancorada['empuxo_ativo_total_kN_m'])} kN/m",
        )
        colunas_resultado_ancorada[1].metric(
            "Empuxo da água",
            f"{formatar_numero(resultado_ancorada['empuxo_hidrostatico_kN_m'])} kN/m",
        )
        colunas_resultado_ancorada[2].metric(
            "Passivo mobilizado",
            f"{formatar_numero(resultado_ancorada['empuxo_passivo_mobilizado_kN_m'])} kN/m",
        )
        colunas_resultado_ancorada[3].metric(
            "Força no tirante",
            f"{formatar_numero(resultado_ancorada['forca_tirante_kN_m'])} kN/m",
        )
        colunas_resultado_ancorada[4].metric(
            "FS ao tombamento",
            formatar_numero(resultado_ancorada["fator_seguranca_tombamento"], 3),
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

        st.subheader("6. Diagrama de pressões")
        st.caption(
            "A pressão passiva está limitada à ficha abaixo da escavação. "
            "A pressão diferencial da água atua do N.A. até a ponta, com o lado escavado drenado."
        )
        mostrar_diagrama_pressao_cortina_ancorada(resultado_ancorada)
        mostrar_memoria_cortina_ancorada(resultado_ancorada)

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
    "O modelo inclui o diferencial hidrostático com lado escavado drenado. Estabilidade global, deformações e dimensionamento estrutural estão fora do escopo."
)
