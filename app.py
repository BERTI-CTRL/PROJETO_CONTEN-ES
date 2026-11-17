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
    .hero-contencoes p {color: #e0ece8; margin: 0; max-width: 980px; font-size: 1.04rem; line-height: 1.55;}
    .cartao-estrutura {
        min-height: 250px;
        padding: 1.25rem 1.35rem;
        border: 1px solid #e2e8e5;
        border-radius: 18px;
        background: #ffffff;
        box-shadow: 0 8px 24px rgba(25, 52, 44, 0.055);
        margin-bottom: 0.6rem;
    }
    .cartao-estrutura h3 {margin: 0.35rem 0 0.45rem; color: #17374c;}
    .cartao-estrutura p {color: #687a80; margin: 0; font-size: 0.95rem;}
    .cartao-estrutura ul {color: #46575e; margin: 0.8rem 0 0; padding-left: 1.2rem; line-height: 1.55; font-size: 0.9rem;}
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
            Aplicação didática para explorar quatro sistemas de contenção. Informe os dados,
            acompanhe os croquis e diagramas, consulte como os resultados foram calculados
            e compare seus cenários com as planilhas e referências das aulas.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.subheader("O que você pode fazer")
st.caption(
    "Cada módulo reúne campos de entrada, resultados, representações gráficas e uma memória para acompanhar as hipóteses do cálculo."
)

paginas_projeto = [
    {
        "arquivo": "pages/01_Muro_de_Arrimo.py",
        "titulo": "🧱 Muro de arrimo",
        "descricao": "Avalie um muro de gravidade com seção trapezoidal e solo retido em camadas.",
        "recursos": [
            "Empuxos de solo, sobrecarga e água pelos métodos disponíveis.",
            "Verificações de tombamento, deslizamento e tensões na base.",
            "Croqui, diagramas, memória de cálculo e exportação CAD.",
        ],
        "botao": "Abrir módulo de muro",
        "icone": "🧱",
    },
    {
        "arquivo": "pages/02_Estaca_Prancha.py",
        "titulo": "▥ Estaca-prancha",
        "descricao": "Compare dois modelos de cortina: em balanço e ancorada.",
        "recursos": [
            "Ficha teórica e ficha preliminar para o caso em balanço.",
            "Pressões ativa e passiva, esforços e força no tirante.",
            "Perfil, diagramas e memória para conferir os resultados.",
        ],
        "botao": "Abrir módulo de estaca-prancha",
        "icone": "📐",
    },
    {
        "arquivo": "pages/03_Escoradas.py",
        "titulo": "⌁ Estruturas escoradas",
        "descricao": "Explore estimativas para escavações com níveis de escoras.",
        "recursos": [
            "Envoltórias de pressão aparente e carga estimada por escora.",
            "Verificação de ruptura de fundo em argila não drenada.",
            "Estabilidade hidráulica pelo critério de Graux e profundidade crítica de corte.",
        ],
        "botao": "Abrir módulo de escoradas",
        "icone": "🏗️",
    },
    {
        "arquivo": "pages/04_Estabilidade_de_Taludes.py",
        "titulo": "◢ Estabilidade de taludes",
        "descricao": "Analise superfícies circulares pelo método das fatias de Fellenius.",
        "recursos": [
            "Compare fatores de segurança dos raios candidatos e da malha de centros.",
            "Inspecione o perfil, as fatias e a memória de cálculo.",
            "Escolha um círculo válido para visualizar e exportar em CAD.",
        ],
        "botao": "Abrir módulo de taludes",
        "icone": "⛰️",
    },
]

for inicio_linha in range(0, len(paginas_projeto), 2):
    colunas = st.columns(2, gap="large")
    for coluna, pagina in zip(colunas, paginas_projeto[inicio_linha : inicio_linha + 2]):
        with coluna:
            itens_recursos = "".join(
                f"<li>{recurso}</li>" for recurso in pagina["recursos"]
            )
            st.markdown(
                f"""
                <div class="cartao-estrutura">
                    <div class="etiqueta-disponivel">● MÓDULO DISPONÍVEL</div>
                    <h3>{pagina['titulo']}</h3>
                    <p>{pagina['descricao']}</p>
                    <ul>{itens_recursos}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.page_link(
                pagina["arquivo"],
                label=pagina["botao"],
                icon=pagina["icone"],
                use_container_width=True,
            )

st.divider()
st.markdown(
    "**Como usar o projeto:** escolha um módulo, preencha os dados e acompanhe as figuras, "
    "resultados e memória de cálculo. Os exemplos podem ser restaurados em cada página e "
    "os dados são salvos neste navegador. Os métodos e limites adotados são descritos junto "
    "aos respectivos cálculos."
)
st.markdown("### Planilha de referência")
st.markdown(
    "Consulte a planilha usada como referência para acompanhar os cálculos do projeto."
)
st.link_button(
    "Abrir planilha de referência",
    "https://docs.google.com/spreadsheets/d/1hEL-d3-Uf1JkWKGu8rqwnLtDs7i2Cu2nXm7pedB8DSA/edit?usp=sharing",
    icon="📊",
)
