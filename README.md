# Projeto de contenções

Ferramenta didática para acompanhar e conferir os cálculos de contenções vistos
em aula. A primeira fase implementa o muro trapezoidal de gravidade; as outras
estruturas aparecem como “Em construção”.

## Estrutura do projeto

- `app.py`: página inicial.
- `pages/01_Muro_de_Arrimo.py`: interface do muro, campos, gráficos e memória de cálculo.
- `contencoes/calculos_muro_de_arrimo.py`: validações e cálculos do muro em Python puro.

O prefixo numérico do arquivo da página determina sua ordem na navegação do
Streamlit. Cada estrutura terá seu módulo de cálculo na pasta `contencoes/`,
com um nome que identifica o tipo de estrutura. Nesta fase, só existe o cálculo
do muro; os demais módulos serão criados quando cada etapa começar.

## Executar localmente

Requer Python 3.11 e [uv](https://docs.astral.sh/uv/).

```powershell
uv sync
uv run streamlit run app.py
```

As entradas do muro são salvas automaticamente no armazenamento local do
navegador. Elas voltam ao abrir a página no mesmo navegador e dispositivo. A
limpeza dos dados do navegador apaga esse rascunho; para outro dispositivo, os
valores precisam ser preenchidos novamente.

## Publicar no Streamlit Community Cloud

Depois de enviar o repositório para o GitHub:

1. Crie um aplicativo em [Streamlit Community Cloud](https://share.streamlit.io/).
2. Selecione o repositório, a branch e `app.py` como arquivo de entrada.
3. Nas configurações avançadas, escolha Python 3.11.

O `pyproject.toml` e `uv.lock` registram as dependências para instalação. O
código desta fase ainda não foi publicado e não há um endereço público.

## Escopo desta fase

O módulo reproduz as hipóteses da planilha e das aulas para conferência
acadêmica. Não inclui ruptura global do maciço, empuxo passivo à frente do muro
ou dimensionamento estrutural do concreto armado; não substitui projeto
executivo.
