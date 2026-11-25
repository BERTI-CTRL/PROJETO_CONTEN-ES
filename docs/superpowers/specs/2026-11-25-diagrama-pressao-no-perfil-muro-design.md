# Diagrama de pressões junto ao perfil do muro

## Intenção

Reunir o segundo desenho de resultados do muro de arrimo e o diagrama de pressões laterais num único quadro. A leitura deve relacionar cada pressão à cota correspondente sem cobrir o muro, as camadas ou seus rótulos.

## Abordagens consideradas

1. **Painel lateral à direita — recomendada.** Perfil e camadas ocupam a região esquerda; as curvas de pressão ocupam uma região reservada à direita. Ambos compartilham as cotas, e o painel de pressão usa seu próprio eixo horizontal em kPa. Preserva a geometria e permite comparar diretamente a altura de atuação.
2. **Sobrepor as curvas ao perfil.** Mantém um único sistema de eixos, mas mistura metros de geometria com kPa e pode cobrir as camadas; não atende ao requisito de manter o solo desobstruído.
3. **Manter dois gráficos empilhados.** Conserva a apresentação atual, mas não aproxima visualmente perfil e pressão e ocupa mais altura na página.

## Escopo escolhido

- Aplicar a primeira abordagem somente ao segundo desenho, em resultados.
- Manter o croqui compacto no topo da página sem alterações.
- Usar painel próprio para solo, sobrecarga, água e pressão total, com escala em kPa e eixo vertical alinhado à cota do perfil.
- Não desenhar as curvas sobre as áreas preenchidas do muro ou do aterro; manter os rótulos das camadas legíveis.
- Remover o gráfico de pressão empilhado após integrá-lo ao quadro, evitando duplicação.
- Preservar os dados, cálculos, exportações CAD/PDF e demais controles atuais.

## Critérios de aceitação

- O segundo desenho mostra o muro e as camadas à esquerda e as quatro curvas de pressão à direita.
- Uma cota no painel de pressão corresponde à mesma cota no perfil.
- Nenhuma curva de pressão ou legenda invade as camadas.
- O croqui compacto do topo permanece como está.
- A alteração fica limitada à visualização de resultados do muro.

## Verificação prevista

Conferir a compilação Python e inspecionar o desenho com o exemplo da página, verificando alinhamento vertical, legibilidade e ausência de sobreposição com as camadas.
