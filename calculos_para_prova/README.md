# Cálculos para prova

Os módulos desta pasta contêm cálculos didáticos de geotecnia. A página de
interface correspondente foi retirada da navegação pública do Streamlit.

O conteúdo anteriormente apresentado nessa página reunia abas de formulário de equações,
recalque imediato de sapata,
regressao linear, polo do circulo de Mohr, varios circulos com envoltoria e
trajetoria `p-q`, adensamento primario/secundario e `Ensaios e tensoes`.
A aba `Areias e argilas` reúne recortes dos slides e explica as curvas de
areias fofas/compactas, estado crítico, argilas NA/SA, ensaios CU/UU e trajetórias
`p-q`.

As formulas e o procedimento aparecem no inicio de cada aba. Na sapata,
`B` e a menor dimensao, `L` a maior, `H` a camada compressivel, `Delta sigma`
o acrescimo de tensao, `Es` o modulo medio, `nu` o coeficiente de Poisson e
`If` o fator lido na tabela da aula. O recalque e calculado no centro.

Na regressao, cada linha e um par `sigma_n` (tensao normal) e `tau_p`
(cisalhamento no pico); a pagina mostra o ajuste manual por `SXX` e `SXY`,
residuos, `SQR`, `R` e `R^2`. No polo, informe as tensoes nas faces horizontal
e vertical e o angulo da reta. Na aba de varios circulos, informe centro `C_i`
e raio `R_i` de cada circulo e a coesao `c` e o angulo de atrito `phi` da
envoltoria. Use unidades coerentes e a mesma convencao de tensoes em todos os
dados. Na aba Adensamento, o primario compara a tensao final com a de
pre-adensamento e combina `Cr` e `Cc` quando a tensao cruza esse limite. O
secundario usa `C_alpha`, o indice de vazios no fim do primario e os tempos `t1`
e `t2`, na mesma unidade. A subaba Tempo calcula `t = Tv * Hd^2 / Cv`; use `Cv`
em m2/s, `Hd` em metros e o fator `Tv` da tabela/ábaco. O formulário também
resume relações entre índice de vazios, porosidade, saturação, umidade, Gs,
densidade e peso específico.

Em `Ensaios e tensoes`, a subaba `Tensoes por camadas` soma `gamma * h` por
trecho e calcula a pressao neutra hidrostatica e a tensao efetiva. `Ensaio de
adensamento` calcula `Cc` e `Cr` com dois pontos de cada ramo, `Cv` por `t50` ou
`t90` e o recalque parcial `U * Sc_final`. `Triaxial e compressao simples`
corrige a area da amostra, calcula a tensao desviadora e as tensoes principais;
se for medida, a poropressao permite exibir as tensoes efetivas.
