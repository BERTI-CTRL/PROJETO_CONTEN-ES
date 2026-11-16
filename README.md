# Projeto de contenções

Ferramenta didática para acompanhar e conferir os cálculos de contenções vistos
em aula. O projeto implementa o muro trapezoidal de gravidade, dois casos de
estaca-prancha, estruturas escoradas e estabilidade de taludes circulares.

## Estrutura do projeto

- `app.py`: página inicial.
- `pages/01_Muro_de_Arrimo.py`: interface do muro, campos, gráficos e memória de cálculo.
- `contencoes/calculos_muro_de_arrimo.py`: validações e cálculos do muro em Python puro.
- `pages/02_Estaca_Prancha.py`: interface dos casos em balanço e ancorado.
- `contencoes/calculos_estaca_prancha.py`: validações, empuxos e equilíbrio das cortinas em Python puro.
- `pages/03_Escoradas.py`: interface das pressões aparentes e verificações de fundo.
- `contencoes/calculos_escoradas.py`: fórmulas e validações da aba Escoradas em Python puro.
- `pages/04_Estabilidade_de_Taludes.py`: interface, dados, gráficos e memória das fatias.
- `contencoes/calculos_estabilidade_taludes.py`: geometria e cálculos de Fellenius em Python puro.

O prefixo numérico do arquivo da página determina sua ordem na navegação do
Streamlit.

## Executar localmente

Requer Python 3.11 e [uv](https://docs.astral.sh/uv/).

```powershell
uv sync
uv run streamlit run app.py
```

As entradas das quatro estruturas são salvas automaticamente no armazenamento
local do navegador. Elas voltam ao abrir a respectiva página no mesmo navegador
e dispositivo. A limpeza dos dados do navegador apaga esse rascunho; para outro
dispositivo, os valores precisam ser preenchidos novamente.

## Publicar no Streamlit Community Cloud

Depois de enviar o repositório para o GitHub:

1. Crie um aplicativo em [Streamlit Community Cloud](https://share.streamlit.io/).
2. Selecione o repositório, a branch e `app.py` como arquivo de entrada.
3. Nas configurações avançadas, escolha Python 3.11.

O `pyproject.toml` e `uv.lock` registram as dependências para instalação. O
repositório no GitHub não publica a aplicação sozinho; configure o Streamlit
Community Cloud para criar um endereço acessível ao professor.

## Estaca-prancha

A página 2 contém dois casos baseados na aba Estaca-prancha da planilha:

- **Cortina em balanço:** solo granular homogêneo, coeficientes de Rankine,
  fração mobilizada do empuxo passivo e acréscimo prático sobre a ficha teórica.
- **Cortina ancorada:** ficha conhecida, duas camadas, sobrecarga, nível d’água,
  força no tirante e fator de segurança ao tombamento em relação à ancoragem.

O exemplo em balanço resulta em ficha teórica de aproximadamente **6,12 m** e
ficha preliminar de **7,34 m**. O exemplo ancorado resulta em empuxo ativo de
**307,50 kN/m**, passivo mobilizado de **220,50 kN/m**, força no tirante de
**87,00 kN/m** e FS de aproximadamente **1,15**, classificado como “REVER” para
FS mínimo de 1,50. O caso ancorado adota o peso específico submerso informado
na planilha e não calcula diferencial hidrostático entre as faces.

Os modelos usam Rankine, solo sem coesão e superfície horizontal. Não incluem
estabilidade global, deformações ou dimensionamento estrutural da cortina e do
tirante, e não substituem projeto geotécnico.

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

## Estruturas escoradas

A página 3 reproduz os quatro módulos da aba Escoradas:

- envoltórias aparentes de Terzaghi–Peck para areia, argila mole/média e argila
  dura/fissurada, com resultantes do solo e da água, braço total e força axial
  aproximada por escora;
- verificação simplificada de ruptura de fundo em argila não drenada pelo método
  de Terzaghi;
- estabilidade hidráulica simplificada pelo critério de Graux;
- profundidade crítica de corte vertical não suportado pela expressão de Fröhlich.

Os exemplos reproduzem pmax = **28,60 kPa**, Eapp = **171,60 kN/m** e força
aproximada por escora de **111,54 kN** para areia; FS = **8,64** para ruptura de
fundo; FS = **5,14** para Graux; e Hcr = **2,50 m** para Fröhlich. No exemplo de
Graux com φ = 30°, a expressão da planilha resulta em Nq ≈ 18,40 e FS ≈ 5,14,
enquanto o slide 34 informa aproximadamente 20,3 e 5,7. A página segue a
fórmula da planilha e mostra essa diferença junto ao resultado.

Para argila dura/fissurada, a planilha usa pmax = 0,20γH; o slide 14 também
apresenta uma faixa de 0,28γH a 0,40γH no patamar. O módulo segue o valor da
planilha e avisa sobre a divergência quando esse modelo é selecionado. As
distribuições de carga entre níveis de escora são iguais e aproximadas. Não há
dimensionamento estrutural ou verificação de flambagem das escoras, nem efeitos
tridimensionais, água ou análise global nas verificações simplificadas de fundo.

## Escopo do muro

O módulo do muro reproduz as hipóteses da planilha e das aulas para conferência
acadêmica. Não inclui empuxo passivo à frente do muro ou dimensionamento
estrutural do concreto armado; não substitui projeto executivo.
