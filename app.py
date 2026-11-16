import streamlit as st


st.set_page_config(
    page_title="Contenções | Início",
    page_icon="⛰️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    .hero-contencoes {
        padding: 2.4rem 2.6rem;
        border-radius: 22px;
        color: #f7faf8;
        background: linear-gradient(120deg, #12314a 0%, #176452 100%);
        box-shadow: 0 16px 38px rgba(18, 49, 74, 0.16);
        margin-bottom: 1.4rem;
    }
    .hero-contencoes .sobretitulo {
        color: #b8e4cf;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .hero-contencoes h1 {color: #ffffff; margin: 0.5rem 0; font-size: 2.6rem;}
    .hero-contencoes p {color: #e0ece8; margin: 0; max-width: 780px; font-size: 1.04rem;}
    .cartao-estrutura {
        min-height: 172px;
        padding: 1.25rem 1.35rem;
        border: 1px solid #e2e8e5;
        border-radius: 18px;
        background: #ffffff;
        box-shadow: 0 8px 24px rgba(25, 52, 44, 0.055);
    }
    .cartao-estrutura h3 {margin: 0.35rem 0 0.45rem; color: #17374c;}
    .cartao-estrutura p {color: #687a80; margin: 0; font-size: 0.95rem;}
    .etiqueta-disponivel {color: #18745d; font-weight: 700; font-size: 0.8rem;}
    .etiqueta-futura {color: #87939a; font-weight: 700; font-size: 0.8rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="hero-contencoes">
        <div class="sobretitulo">Ferramenta de conferência · Geotecnia</div>
        <h1>Projeto de contenções</h1>
        <p>
            Uma memória de cálculo clara para acompanhar os exercícios das aulas,
            comparar resultados com a planilha e guardar seus cenários no navegador.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.subheader("Escolha uma estrutura")
st.caption(
    "Os módulos de Muro, Estaca-prancha e Estabilidade de Taludes estão disponíveis."
)

coluna_muro, coluna_estaca, coluna_escorada, coluna_talude = st.columns(4, gap="medium")

with coluna_muro:
    st.markdown(
        """
        <div class="cartao-estrutura">
            <div class="etiqueta-disponivel">● DISPONÍVEL</div>
            <h3>🧱 Muro de arrimo</h3>
            <p>Empuxos, tombamento, deslizamento e tensões na base.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link(
        "pages/01_Muro_de_Arrimo.py",
        label="Abrir cálculo do muro",
        icon="🧱",
        use_container_width=True,
    )

with coluna_estaca:
    st.markdown(
        """
        <div class="cartao-estrutura">
            <div class="etiqueta-disponivel">● DISPONÍVEL</div>
            <h3>▥ Estaca-prancha</h3>
            <p>Ficha em balanço e cortina ancorada.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link(
        "pages/02_Estaca_Prancha.py",
        label="Abrir cálculo da estaca-prancha",
        icon="▥",
        use_container_width=True,
    )

with coluna_escorada:
    st.markdown(
        """
        <div class="cartao-estrutura">
            <div class="etiqueta-futura">EM CONSTRUÇÃO</div>
            <h3>⌁ Estruturas escoradas</h3>
            <p>Etapas de escavação e esforços nas escoras.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with coluna_talude:
    st.markdown(
        """
        <div class="cartao-estrutura">
            <div class="etiqueta-disponivel">● DISPONÍVEL</div>
            <h3>◢ Estabilidade de taludes</h3>
            <p>Superfícies circulares por fatias e busca do FS crítico.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link(
        "pages/04_Estabilidade_de_Taludes.py",
        label="Abrir cálculo do talude",
        icon="◢",
        use_container_width=True,
    )

st.divider()
st.markdown(
    "**Uso didático:** os cálculos seguem as hipóteses da planilha e das aulas de referência. "
    "Confira em cada página os métodos e limites incluídos."
)
