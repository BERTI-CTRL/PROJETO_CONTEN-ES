# Projeto de contenções

Ferramenta didática para acompanhar e conferir os cálculos de contenções vistos
em aula. O projeto implementa o muro trapezoidal de gravidade, dois casos de
estaca-prancha, estruturas escoradas e estabilidade de taludes circulares.

## Estrutura do projeto

- `app.py`: página inicial.
- `pages/01_Muro_de_Arrimo.py`: interface do muro, campos, gráficos e memória de cálculo.
- `pages/02_Estaca_Prancha.py`: interface dos casos em balanço e ancorado.
- `pages/03_Escoradas.py`: interface das pressões aparentes e verificações de fundo.
- `pages/04_Estabilidade_de_Taludes.py`: interface, dados, gráficos e memória das fatias.
- `contencoes/calculos/`: fórmulas e validações das quatro estruturas em Python puro.
- `contencoes/svg/`: geração dos croquis vetoriais de estaca-prancha e escoradas.
- `contencoes/cad/`: exportação de desenhos DXF de muros e taludes.
- `contencoes/visualizacao/`: módulos de apresentação de gráficos e memórias de cálculo.

O prefixo numérico do arquivo da página determina sua ordem na navegação do
Streamlit.

## Executar localmente

Requer Python 3.11 e [uv](https://docs.astral.sh/uv/).

```powershell
uv sync
uv run streamlit run app.py
```

Cada página carrega o exemplo da planilha na primeira visita e tem um botão para
restaurá-lo; dados já salvos no navegador são preservados.
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
  empuxo hidrostático diferencial, força no tirante e fator de segurança ao
  tombamento em relação à ancoragem.

O exemplo em balanço resulta em ficha teórica de aproximadamente **6,12 m** e
ficha preliminar de **7,34 m**. Com os valores padrão da ancorada, o empuxo ativo
do solo é **307,50 kN/m**, o passivo mobilizado é **220,50 kN/m** e a parcela
da água é **275,91 kN/m**. A força no tirante fica em **362,91 kN/m**, com
FS de **0,529**. O modelo da planilha atual considera água no tardoz até a ponta
e o lado escavado drenado. Para anular o diferencial, use γw = 0.

Os modelos usam Rankine, solo sem coesão e superfície horizontal. Não incluem
estabilidade global, deformações ou dimensionamento estrutural da cortina e do
tirante, e não substituem projeto geotécnico.

## Estabilidade de taludes

A página `04_Estabilidade_de_Taludes.py` calcula a estabilidade de superfícies
circulares por Fellenius e Bishop Simplificado. Compara dez círculos que passam
pelos pontos de saída e entrada indicados. Os raios são editáveis e cada método
identifica seu menor FS válido. A malha de centros usa Fellenius. O perfil
permite inclinação variável do terreno a montante, face H:V editável, crista,
pé e terreno inferior. Inclui sobrecarga
uniforme na crista, N.A. horizontal, até duas camadas horizontais e de 4 a 50
fatias. O exemplo padrão do app usa H = 8 m, H:V = 1,5, β = 0°,
h₁ = 3 m, zNA = 7,8 m e 20 fatias. A camada 1 usa γ/γsat = 18/20 kN/m³,
c′ = 10 kPa e φ′ = 30°; a camada 2 usa 20/21 kN/m³, c′ = 5 kPa e φ′ = 30°.
Nesse exemplo, o crítico por Fellenius tem FS ≈ **1,446**, raio ≈ **14,221 m** e centro
(x, y) ≈ **(2,098 m; 13,982 m)**.

O resultado depende dos raios candidatos e da discretização. O modelo não
inclui superfícies não circulares, sismo, fluxo não hidrostático ou
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

O exemplo de conferência usa H = 6 m, base = 4 m, topo = 1 m, γc = 24 kN/m³,
sobrecarga de 10 kPa, atrito na base de 0,80, N.A. a 2 m e duas camadas de 3 m
(18/20 kN/m³, φ = 30°; 19/21 kN/m³, φ = 25°). Ele resulta em FS de tombamento
**2,487**, FS de deslizamento **1,419**, tensão máxima **150,14 kPa** e tensão
mínima **29,86 kPa**. O deslizamento fica marcado para revisão frente ao mínimo
de 1,50.
