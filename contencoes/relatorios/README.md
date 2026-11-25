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
