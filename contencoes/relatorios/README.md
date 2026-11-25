# Relatórios didáticos

O pacote gera relatórios vetoriais em LaTeX/PDF a partir das mesmas entradas e
resultados usados pelo aplicativo. O template inicial é
`templates/muro_arrimo.tex.j2`; os desenhos são TikZ dentro do próprio `.tex`,
para que possam ser copiados e editados em outros documentos.

## Muro de arrimo

```python
from contencoes.calculos.calculos_muro_de_arrimo import calcular_muro
from contencoes.relatorios.gerar_relatorio_muro_arrimo import (
    gerar_relatorio_muro_arrimo,
)

resultado = calcular_muro(entradas_muro, camadas_solo)
pdf, fonte_tex = gerar_relatorio_muro_arrimo(
    entradas_muro, camadas_solo, resultado
)
```

O retorno contém o PDF e a fonte `.tex`. O compilador é encontrado em tempo de
execução: `pdflatex`, `lualatex` ou Tectonic. Para o Streamlit Community Cloud,
as dependências de sistema ficam em `packages.txt` na raiz do repositório.

O relatório detalha dados, geometria, coeficientes de empuxo, tensões, pressões,
integrações por trecho, forças e momentos, tombamento, deslizamento e contato na
fundação. Também inclui croqui, diagramas vetoriais, gráfico comparativo,
animação opcional no PDF e uma seção de escopo/limitações.

## Estabilidade de taludes

A página de taludes prepara um DXF, um relatório PDF e a fonte LaTeX/TikZ com
as entradas atuais e o círculo selecionado. O relatório explica Fellenius e
Bishop Simplificado, inclui o croqui cotado, compara os círculos candidatos,
mostra a sequência de iterações de Bishop e apresenta as geometrias e forças
de cada fatia. Se o compilador PDF não estiver disponível, a fonte `.tex`
permanece disponível para download.

## Estaca-prancha

Cada caso da página (cortina em balanço ou ancorada) prepara seu próprio DXF,
relatório PDF didático e fonte LaTeX/TikZ com os valores atuais. Os relatórios
incluem entradas, perfil cotado, diagrama de pressões, memória do cálculo e
limites do modelo. Se o servidor não tiver um compilador LaTeX, a fonte `.tex`
continua disponível para compilação local.
