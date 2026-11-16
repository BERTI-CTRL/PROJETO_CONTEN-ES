# Projeto de contenções

Ferramenta didática para acompanhar e conferir os cálculos de contenções vistos
em aula. O projeto implementa o muro trapezoidal de gravidade e a estabilidade
de taludes circulares; Estaca-prancha e Estruturas escoradas estão “Em construção”.

## Estrutura do projeto

- `app.py`: página inicial.
- `pages/01_Muro_de_Arrimo.py`: interface do muro, campos, gráficos e memória de cálculo.
- `contencoes/calculos_muro_de_arrimo.py`: validações e cálculos do muro em Python puro.
- `pages/04_Estabilidade_de_Taludes.py`: interface, dados, gráficos e memória das fatias.
- `contencoes/calculos_estabilidade_taludes.py`: geometria e cálculos de Fellenius em Python puro.

O prefixo numérico do arquivo da página determina sua ordem na navegação do
Streamlit. Cada estrutura terá seu módulo de cálculo na pasta `contencoes/`,
com um nome que identifica o tipo de estrutura. As páginas 2 e 3 ficam
reservadas para as próximas etapas.

## Executar localmente

Requer Python 3.11 e [uv](https://docs.astral.sh/uv/).

```powershell
uv sync
uv run streamlit run app.py
```

As entradas do Muro e do Talude são salvas automaticamente no armazenamento
local do navegador. Elas voltam ao abrir a respectiva página no mesmo navegador
e dispositivo. A limpeza dos dados do navegador apaga esse rascunho; para outro
dispositivo, os valores precisam ser preenchidos novamente.

## Publicar no Streamlit Community Cloud

Depois de enviar o repositório para o GitHub:

1. Crie um aplicativo em [Streamlit Community Cloud](https://share.streamlit.io/).
2. Selecione o repositório, a branch e `app.py` como arquivo de entrada.
3. Nas configurações avançadas, escolha Python 3.11.

O `pyproject.toml` e `uv.lock` registram as dependências para instalação. O
código desta fase ainda não foi publicado e não há um endereço público.

## Estabilidade de taludes

A página `04_Estabilidade_de_Taludes.py` calcula a estabilidade de superfícies
circulares pelo método das fatias de Fellenius. Compara dez círculos que passam
pelos pontos de saída e entrada indicados; os raios podem ser editados e o
menor FS válido é identificado. O perfil permite inclinação variável do terreno
a montante, face H:V editável, crista, pé e terreno inferior. Inclui sobrecarga
uniforme na crista, N.A. horizontal, até duas camadas horizontais e de 4 a 50
fatias. O exemplo inicial reproduz os dados da aba Talude: H = 8 m, H:V = 1,5,
β = 0°, h₁ = 3 m, zNA = 7,8 m e FS crítico de referência ≈ 1,358.

O resultado depende dos raios candidatos e da discretização. O modelo não
inclui Bishop, superfícies não circulares, sismo, fluxo não hidrostático ou
busca automática dos pontos de entrada e saída. Não representa uma verificação
de projeto geotécnico nem aplica um limite universal para o fator de segurança.

## Escopo do muro

O módulo do muro reproduz as hipóteses da planilha e das aulas para conferência
acadêmica. Não inclui empuxo passivo à frente do muro ou dimensionamento
estrutural do concreto armado; não substitui projeto executivo.
