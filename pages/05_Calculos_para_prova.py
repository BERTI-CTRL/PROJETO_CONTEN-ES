from __future__ import annotations

from math import atan, cos, degrees, radians, tan

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from calculos_para_prova.circulo_de_mohr import calcular as calcular_mohr, desenhar
from calculos_para_prova.circulos_envoltoria import (
    calcular_tensoes_principais,
    desenhar as desenhar_circulos,
)
from calculos_para_prova.recalque_elastico_sapata import calcular as calcular_sapata
from calculos_para_prova.recalque_adensamento import (
    calcular_fator_tempo,
    calcular_recalque_primario,
    calcular_recalque_secundario,
    calcular_tempo_adensamento,
)
from calculos_para_prova.regressao_minimos_quadrados import calcular as calcular_regressao
from calculos_para_prova.perfil_tensoes import calcular_perfil
from calculos_para_prova.interpretacao_adensamento import (
    calcular_cv,
    calcular_indice_compressao,
    calcular_recalque_parcial,
)
from calculos_para_prova.ensaios_resistencia import reduzir_ensaio


st.set_page_config(page_title="Calculos para prova", page_icon="📐", layout="wide")
st.title("Calculos rapidos para prova")
st.caption("Valores e convencoes conforme os exemplos das aulas.")

aba_formulario, aba_sapata, aba_regressao, aba_mohr, aba_multiplos, aba_adensamento, aba_complementares, aba_areias_argilas = st.tabs(
    ["Formulário", "Recalque imediato", "Minimos quadrados", "Polo", "Circulos + envoltoria", "Adensamento", "Ensaios e tensões", "Areias e argilas"]
)

with aba_formulario:
    st.subheader("Formulário de equações")
    st.caption("Use como mapa antes de preencher as calculadoras. As letras e unidades abaixo seguem os campos das abas; `log₁₀` é decimal e `ln` é logaritmo natural. `Σ` indica soma, `π≈3,1416` e `arctan` é a tangente inversa.")
    with st.expander("Mecânica dos solos — índices, densidades e conversões", expanded=True):
        st.markdown("**1. Diagrama de fases.** `V` é o volume total; `Vₛ`, o volume dos sólidos; `Vᵥ`, o volume de vazios; `Vw`, o volume de água; e `Va`, o volume de ar. `M` é a massa total; `Ms`, a massa seca dos sólidos; `Mw`, a massa de água. `W`, `Ws` e `Ww` são os pesos correspondentes. O peso do ar é desprezado. Os índices `s`, `v`, `w` e `a` indicam sólidos, vazios, água e ar.")
        st.latex(r"V=V_s+V_v,\quad V_v=V_w+V_a,\quad W=W_s+W_w")

        st.markdown("**2. Índices de volume e água.** `e` é o índice de vazios; `n`, a porosidade; `Sr`, o grau de saturação; e `w`, o teor de umidade. `Gs` é a gravidade específica dos grãos (também chamada massa específica relativa): `ρs/ρw` compara a massa específica dos grãos com a da água. Por exemplo, `Gs=2,70` significa que os grãos têm massa específica 2,70 vezes a da água; `Gs` não tem unidade. `ρs` e `ρw` são as massas específicas dos grãos e da água; `γs` e `γw`, seus pesos específicos. Use `w` e `Sr` como frações: 20% = 0,20.")
        st.latex(r"e=\frac{V_v}{V_s},\quad n=\frac{V_v}{V}=\frac{e}{1+e},\quad e=\frac{n}{1-n}")
        st.latex(r"S_r=\frac{V_w}{V_v},\quad w=\frac{M_w}{M_s}=\frac{W_w}{W_s},\quad G_s=\frac{\rho_s}{\rho_w}=\frac{\gamma_s}{\gamma_w}")
        st.latex(r"w=\frac{S_r e}{G_s},\quad S_r=\frac{wG_s}{e},\quad \frac{V_a}{V_v}=1-S_r,\quad \frac{V_a}{V}=n(1-S_r)")

        st.markdown("**3. Densidade e peso específico.** `ρ=M/V` é a densidade natural (massa por volume; kg/m³ ou g/cm³); `γ=W/V` é o peso específico natural (peso por volume; kN/m³). `g≈9,81 m/s²` é a aceleração da gravidade. `ρd` e `γd` são densidade e peso específico secos; `ρsat` e `γsat`, saturados; `ρ′` e `γ′`, submersos. `ρw` e `γw` são os valores da água; adote `γw=9,81 kN/m³` ou o arredondamento da aula.")
        st.latex(r"\rho=\frac{M}{V},\quad \gamma=\frac{W}{V}=\rho g,\quad \rho_d=\frac{M_s}{V}=\frac{\rho}{1+w},\quad \gamma_d=\frac{W_s}{V}=\frac{\gamma}{1+w}")
        st.latex(r"\gamma_d=\gamma_w\frac{G_s}{1+e},\quad \gamma=\gamma_d(1+w)=\gamma_w\frac{G_s+S_r e}{1+e}")
        st.latex(r"\gamma_{sat}=\gamma_w\frac{G_s+e}{1+e},\quad \gamma'=\gamma_{sat}-\gamma_w=\gamma_w\frac{G_s-1}{1+e}")
        st.latex(r"\rho_d=\rho_w\frac{G_s}{1+e},\quad \rho_{sat}=\rho_w\frac{G_s+e}{1+e},\quad \rho'=\rho_{sat}-\rho_w")

        st.markdown("**4. Isolando incógnitas comuns.** Se o exercício der peso específico natural `γ`, teor de umidade `w` e gravidade específica dos grãos `Gs`, primeiro ache `γd`; depois encontre `e`, `n` e `Sr` pelas relações abaixo.")
        st.latex(r"\gamma_d=\frac{\gamma}{1+w},\quad e=\frac{G_s\gamma_w}{\gamma_d}-1,\quad n=\frac{e}{1+e},\quad S_r=\frac{wG_s}{e}")
        st.markdown("**Conversões rápidas.** Passe porcentagens para fração dividindo por 100. Para converter densidade em peso específico: `γ (kN/m³) = ρ (kg/m³) × 9,81 / 1000`; se `ρ` estiver em g/cm³, basta multiplicar por `9,81`. Use `γw = 9,81 kN/m³` (ou o valor arredondado adotado na aula). `1 MPa = 1000 kPa` e `1 kgf/cm² ≈ 98,07 kPa`.")
        st.markdown("**Exemplo de sequência.** Com `γ = 18 kN/m³`, `w = 20% = 0,20`, `Gs = 2,70` e `γw = 9,81 kN/m³`: `γd = 18/(1+0,20) = 15 kN/m³`; `e = 2,70×9,81/15 − 1 ≈ 0,766`; `n ≈ 0,434`; `Sr = 0,20×2,70/0,766 ≈ 0,705 = 70,5%`.")
        st.caption("A nomenclatura pode variar entre materiais: densidade natural/aparente costuma ser ρ=M/V; peso específico natural/aparente é γ=W/V. Não misture ρ (massa/volume) com γ (peso/volume), nem use porcentagem diretamente dentro das equações.")
    with st.expander("Recalque imediato — Steinbrenner"):
        st.markdown("**Ideia e símbolos.** `B` é o lado menor da sapata; `L`, o maior; `H`, a espessura compressível abaixo da base; `Δσ`, o acréscimo de tensão; `Eₛ`, o módulo de elasticidade médio do solo; `ν`, o coeficiente de Poisson; e `I_f`, o fator de embutimento lido na tabela da aula. `m′=L/B` é a razão entre os lados e `n′=2H/B` relaciona a espessura à meia largura. `A₀`, `A₁` e `A₂` são termos auxiliares geométricos; `F₁` e `F₂` são fatores parciais; juntos formam `Iₛ`, o fator de influência de Steinbrenner. Todos esses fatores são adimensionais. `B′=B/2` é a meia largura. No centro, `α=4` conta os quatro quadrantes iguais considerados. `Sₑ` é o recalque elástico/imediato calculado.")
        st.latex(r"m'=\frac{L}{B},\quad n'=\frac{H}{B/2}=\frac{2H}{B},\quad B'=\frac{B}{2},\quad \alpha=4")
        st.latex(r"A_0=m'\ln\!\left[\frac{(1+\sqrt{m'^2+1})\sqrt{m'^2+n'^2}}{m'(1+\sqrt{m'^2+n'^2+1})}\right]")
        st.latex(r"A_1=\ln\!\left[\frac{(m'+\sqrt{m'^2+1})\sqrt{1+n'^2}}{m'+\sqrt{m'^2+n'^2+1}}\right],\quad A_2=\frac{m'}{n'\sqrt{m'^2+n'^2+1}}")
        st.latex(r"F_1=\frac{A_0+A_1}{\pi},\quad F_2=\frac{n'}{2\pi}\arctan(A_2),\quad I_s=F_1+\frac{1-2\nu}{1-\nu}F_2")
        st.latex(r"S_e=\Delta\sigma\,(\alpha B')\frac{1-\nu^2}{E_s}I_sI_f=\Delta\sigma\,(2B)\frac{1-\nu^2}{E_s}I_sI_f")
        st.latex(r"S_{e,\mathrm{rígido}}\approx0.93\,S_{e,\mathrm{flexível}}\quad(\text{sapata quadrada})")
    with st.expander("Recalque primário por adensamento"):
        st.markdown("**Símbolos e escolha do trecho.** `σ′v0` é a tensão vertical efetiva inicial no centro da camada; `Δσ′v`, o acréscimo efetivo; `σ′vf=σ′v0+Δσ′v`, a tensão final; e `σ′vm`, a tensão de pré-adensamento (maior tensão efetiva já suportada). `Cr` é o índice de recompressão e `Cc`, o índice de compressão virgem, ambos obtidos da curva `e × log₁₀σ′`. `e₀` é o índice de vazios inicial; `H`, a espessura compressível; `Δe_r` e `Δe_v`, as variações de índice de vazios nos trechos `Cr` e `Cc`; e `Δe` sua soma. `S_c=ΔH` é o recalque primário. Abaixo de `σ′vm` usa-se `Cr`; acima dela, `Cc`.")
        st.latex(r"\sigma'_{vf}=\sigma'_{v0}+\Delta\sigma'_v,\qquad S_c=\Delta H=\frac{H}{1+e_0}\Delta e")
        st.latex(r"\sigma'_{vf}\leq\sigma'_{vm}:\quad\Delta e=C_r\log_{10}\!\left(\frac{\sigma'_{vf}}{\sigma'_{v0}}\right)")
        st.latex(r"\sigma'_{v0}<\sigma'_{vm}<\sigma'_{vf}:\quad\Delta e=C_r\log_{10}\!\left(\frac{\sigma'_{vm}}{\sigma'_{v0}}\right)+C_c\log_{10}\!\left(\frac{\sigma'_{vf}}{\sigma'_{vm}}\right)")
        st.latex(r"\sigma'_{v0}\geq\sigma'_{vm}:\quad\Delta e=C_c\log_{10}\!\left(\frac{\sigma'_{vf}}{\sigma'_{v0}}\right)")
    with st.expander("Recalque secundário"):
        st.markdown("**Símbolos e uso.** O recalque secundário `S_s` é a deformação lenta após o primário. `Cα` é a inclinação do trecho secundário no gráfico índice de vazios–logaritmo do tempo; `eₚ` é o índice de vazios ao fim do primário; `C′α=Cα/(1+eₚ)` é o índice secundário modificado. `H` é a espessura da camada, `t₁` o tempo ao fim do primário e `t₂` o tempo final analisado. Use a mesma unidade para os dois tempos e `t₂>t₁`.")
        st.latex(r"C'_\alpha=\frac{C_\alpha}{1+e_p},\qquad S_s=C'_\alpha H\log_{10}\!\left(\frac{t_2}{t_1}\right)")
    with st.expander("Tempo para o adensamento primário"):
        st.markdown("**Símbolos.** `U` é o grau médio de adensamento (fração ou porcentagem); `Tᵥ` é o fator tempo adimensional correspondente a `U`; `Cᵥ` é o coeficiente de adensamento do solo; `H_d` é o maior caminho de drenagem — `H/2` na dupla drenagem ou `H` na drenagem simples; `t` é o tempo decorrido. Use unidades compatíveis: com `Cᵥ` em m²/s e `H_d` em metros, `t` sai em segundos.")
        st.latex(r"T_v=\frac{C_vt}{H_d^2},\qquad t=\frac{T_vH_d^2}{C_v}")
        st.caption("Hd é o maior caminho de drenagem: H/2 para drenagem pelas duas faces e H para uma face. Com Cv em m²/s e Hd em metros, t sai em segundos.")
    with st.expander("Tensões verticais por camadas"):
        st.markdown("**Símbolos.** `i` identifica cada camada; `hᵢ` é a espessura do trecho considerado; `γᵢ` é seu peso específico (natural acima do nível d'água e saturado abaixo); `z` é a profundidade a partir da superfície; `zNA` é a profundidade do nível d'água; e `γw` é o peso específico da água. `σv(z)` é a tensão vertical total, `u(z)` a pressão neutra da água e `σ′v(z)` a tensão vertical efetiva, calculada por `σv−u`.")
        st.latex(r"\sigma_v(z)=\sum_i \gamma_i h_i,\quad u(z)=\gamma_w\max(z-z_{NA},0),\quad \sigma'_v(z)=\sigma_v(z)-u(z)")
        st.caption("Use γ em kN/m³ e profundidades em m; as tensões saem em kPa. Na tabela, cada camada pode ter pesos específicos diferentes.")
    with st.expander("Interpretação do ensaio de adensamento"):
        st.markdown("**Símbolos.** `Cc` é o índice de compressão da reta virgem e `Cr` o índice de recompressão/descarregamento no gráfico `e × log₁₀σ′`; `e₁` e `e₂` são os índices de vazios dos dois pontos, e `σ′₁` e `σ′₂` suas tensões efetivas. Os dois pontos de cada índice devem pertencer ao mesmo trecho aproximadamente reto. `Cv` é o coeficiente de adensamento; `t50` é o tempo para 50% de adensamento pelo método de Casagrande (`log t`), e `t90`, para 90% pelo método de Taylor (`√t`). `Tv,50` e `Tv,90` são os fatores tempo correspondentes; `Hd` é o caminho máximo de drenagem; `t` é o tempo medido. `U` é o grau médio de adensamento e `Sc,∞` o recalque primário final; `Sc(t)` é o recalque já ocorrido no instante `t`.")
        st.latex(r"C_c\ \text{ou}\ C_r=\frac{e_1-e_2}{\log_{10}(\sigma'_2/\sigma'_1)},\quad C_v=\frac{T_v H_d^2}{t},\quad T_{v,50}=0.197,\quad T_{v,90}=0.848")
        st.latex(r"S_c(t)=\frac{U}{100}S_{c,\infty}")
        st.caption("Digite σ′ em kPa, t50/t90 em minutos e Hd em metros; o programa converte minutos para segundos e mostra Cv em m²/s e cm²/s. Use U em porcentagem para o recalque parcial.")
    with st.expander("Redução de ensaio triaxial e compressão simples"):
        st.markdown("**Símbolos e ensaios.** `D` é o diâmetro inicial, `H₀` a altura, `Δh` o encurtamento e `P` a carga axial na ruptura; `εa=Δh/H₀` é a deformação axial. `A₀` é a área inicial e `Ac` a área corrigida; `εv` é a deformação volumétrica (positiva para contração). `σd` é a tensão desviadora; `σ₃` é a tensão confinante/principal menor total e `σ₁` a principal maior total. `u` é a poropressão medida na ruptura; o apóstrofo indica tensão efetiva (`σ′=σ−u`). `Su=σd/2` é a resistência não drenada quando `φu=0`; `qu` é a resistência à compressão simples, caso particular com `σ₃=0`. CU significa adensado não drenado, UU não adensado não drenado e CD adensado drenado; em CU/UU e RCS considera-se volume constante (`εv=0`), enquanto em CD se informa a variação volumétrica medida.")
        st.latex(r"A_0=\frac{\pi D^2}{4},\quad A_c=A_0\frac{1-\varepsilon_v}{1-\varepsilon_a},\quad \sigma_d=\frac{P}{A_c},\quad \sigma_1=\sigma_3+\sigma_d")
        st.latex(r"\sigma'_1=\sigma_1-u,\quad \sigma'_3=\sigma_3-u,\quad S_u=\frac{\sigma_d}{2}\ (\phi_u=0)")
        st.caption("Use D, H₀ e Δh em m, P em kN e σ₃/u em kPa; como 1 kN/m² = 1 kPa, as tensões calculadas saem em kPa.")
    with st.expander("Mínimos quadrados — envoltória de Mohr-Coulomb"):
        st.markdown("Nesta regressão, `xᵢ=σₙ` é a tensão normal do ensaio e `yᵢ=τᵢ` a tensão cisalhante medida; `n` é o número de ensaios (aqui não é a porosidade da seção de fases). `x̄` e `ȳ` são as médias. `SXX=Σ(xᵢ−x̄)²` mede a dispersão de x, `SYY=Σ(yᵢ−ȳ)²` a dispersão de y e `SXY=Σ(xᵢ−x̄)(yᵢ−ȳ)` como x e y variam juntos; `Σ` soma os termos de todos os ensaios. `a` é o coeficiente angular e `b` o intercepto da reta. O chapéu em `ŷᵢ` significa **valor estimado pela reta** para aquele `xᵢ`; `eᵢ=yᵢ−ŷᵢ` é o resíduo entre medição e estimativa. `SQT` é a variação total, `SQR` a explicada pela reta e `SQE` a soma dos resíduos ao quadrado. `R` é a correlação linear com sinal; `R²`, o coeficiente de determinação. Para Mohr–Coulomb, `φ` é o ângulo de atrito interno e `c` a coesão.")
        st.latex(r"\bar{x}=\frac{\sum x_i}{n},\quad\bar{y}=\frac{\sum y_i}{n},\quad S_{XX}=\sum(x_i-\bar{x})^2,\quad S_{XY}=\sum(x_i-\bar{x})(y_i-\bar{y})")
        st.latex(r"a=\frac{S_{XY}}{S_{XX}},\quad b=\bar{y}-a\bar{x},\quad \hat{y}_i=ax_i+b,\quad e_i=y_i-\hat{y}_i")
        st.markdown("**Siglas usadas como no material da aula:** `SQT` é a variação total; `SQR` é a parte explicada pela reta; `SQE` é a parte que sobra nos resíduos. Assim, `SQT=SQR+SQE`. `R` é a correlação linear (com sinal) e `R²` é a fração da variação de y explicada pelo ajuste.")
        st.latex(r"SYY=\sum(y_i-\bar{y})^2,\quad SQT=SYY,\quad SQR=\sum(\hat{y}_i-\bar{y})^2,\quad SQE=\sum(y_i-\hat{y}_i)^2")
        st.latex(r"SQT=SQR+SQE,\quad R=\frac{S_{XY}}{\sqrt{S_{XX}S_{YY}}},\quad R^2=\frac{SQR}{SQT}=1-\frac{SQE}{SQT}")
        st.latex(r"\tau=c+\sigma\tan\phi=a\sigma+b,\qquad a=\tan\phi,\quad b=c")
        st.caption("Para Mohr-Coulomb, use σ em x e τ em y: o coeficiente angular é tan(φ) e o intercepto no eixo τ é a coesão c. R² perto de 1 indica que a reta acompanha bem os pontos; não substitui a interpretação do ensaio.")
    with st.expander("Círculo de Mohr e método do polo"):
        st.markdown("**Símbolos e convenção.** `σ` é a tensão normal no eixo horizontal e `τ` a tensão cisalhante no eixo vertical; adote `τ` positivo para cima. `σv` é a tensão normal na face horizontal, `σh` na face vertical e `τh` o cisalhamento na face horizontal. `C` é a tensão normal no centro do círculo; `R` é o raio (também a tensão cisalhante máxima); `σ₁` e `σ₃` são as tensões principais maior e menor. `Mh` e `Mv` são os pontos que representam as faces horizontal e vertical. `P` é o polo, obtido pela interseção das linhas paralelas às faces conhecidas. `α` é o ângulo da reta pelo polo medido desde a horizontal, no sentido anti-horário; `Q` é o ponto onde essa reta encontra o círculo e fornece as tensões no plano escolhido. Na equação `τ=aσ+b`, `a=tan(α)` é a inclinação e `b` o intercepto. `uα=(cosα,sinα)` é o vetor unitário na direção da reta escolhida; `cos` e `sin` são cosseno e seno, e `·` indica produto escalar entre vetores.")
        st.latex(r"C=\frac{\sigma_v+\sigma_h}{2},\quad R=\sqrt{\left(\frac{\sigma_v-\sigma_h}{2}\right)^2+\tau_h^2},\quad \sigma_1=C+R,\quad \sigma_3=C-R")
        st.latex(r"M_h=(\sigma_v,\tau_h),\quad M_v=(\sigma_h,-\tau_h),\quad P=(\sigma_h,\tau_h),\quad (\sigma-C)^2+\tau^2=R^2")
        st.latex(r"\tau=a\sigma+b,\quad a=\tan\alpha,\quad b=\tau_P-a\sigma_P")
        st.latex(r"Q=P-2[(P-(C,0))\cdot(\cos\alpha,\sin\alpha)](\cos\alpha,\sin\alpha)")
    with st.expander("Círculos múltiplos e trajetória P-Q"):
        st.markdown("Cada círculo `i` representa um estágio do ensaio: `Cᵢ` é seu centro, `Rᵢ` o raio, `σ₁ᵢ=Cᵢ+Rᵢ` a tensão principal maior e `σ₃ᵢ=Cᵢ−Rᵢ` a menor. Na envoltória, `τf` é a tensão cisalhante de ruptura, `c` a coesão e `φ` o ângulo de atrito. No gráfico `p-q`, `pᵢ=Cᵢ` é a tensão normal média e `qᵢ=Rᵢ` a tensão desviadora; o topo de cada círculo vira o ponto `(pᵢ,qᵢ)`. A reta P-Q liga o primeiro e o último ponto ativo. `m` é seu coeficiente angular, `β=arctan(m)` o ângulo da reta, e `d` o intercepto em `q=mp+d`. P e Q aqui são nomes dos extremos da trajetória, não as cargas usadas na aba triaxial.")
        st.latex(r"C_i=\frac{\sigma_{1i}+\sigma_{3i}}{2},\quad R_i=\frac{\sigma_{1i}-\sigma_{3i}}{2},\quad (\sigma-C_i)^2+\tau^2=R_i^2")
        st.latex(r"p_i=C_i,\quad q_i=R_i,\quad q=mp+d,\quad m=\frac{q_Q-q_P}{p_Q-p_P},\quad \beta=\arctan(m),\quad d=q_P-mp_P")

with aba_sapata:
    st.subheader("Steinbrenner - recalque no centro")
    st.markdown(
        "**Roteiro.** (1) Informe `B`, o menor lado, `L`, o maior lado, e `H`, "
        "a espessura compressível abaixo da base. (2) A geometria gera `m′=L/B` "
        "e `n′=2H/B`; `A₀`, `A₁` e `A₂` são termos auxiliares, `F₁` e `F₂` fatores "
        "parciais, e `Iₛ` o fator de influência de Steinbrenner. (3) Informe o "
        "acréscimo de tensão `Δσ`, o módulo médio `Eₛ`, o "
        "coeficiente de Poisson `ν` e o fator de embutimento `I_f` lido na tabela "
        "da aula. `m′` e `n′` são razões sem unidade; `α=4` conta os quadrantes "
        "iguais no centro e `B′=B/2` é a meia largura. (4) A equação fornece `Sₑ`, "
        "o recalque elástico flexível no centro. O exemplo de conversão para "
        "fundação rígida vale apenas para sapata quadrada."
    )
    st.latex(r"m'=\frac{L}{B},\qquad n'=\frac{2H}{B}")
    st.latex(
        r"A_0=m'\ln\!\left[\frac{(1+\sqrt{m'^2+1})\sqrt{m'^2+n'^2}}"
        r"{m'(1+\sqrt{m'^2+n'^2+1})}\right]"
    )
    st.latex(
        r"A_1=\ln\!\left[\frac{(m'+\sqrt{m'^2+1})\sqrt{1+n'^2}}"
        r"{m'+\sqrt{m'^2+n'^2+1}}\right],\qquad{}"
        r"A_2=\frac{m'}{n'\sqrt{m'^2+n'^2+1}}"
    )
    st.latex(
        r"F_1=\frac{A_0+A_1}{\pi},\quad{}"
        r"F_2=\frac{n'}{2\pi}\arctan(A_2),\quad{}"
        r"I_s=F_1+\frac{1-2\nu}{1-\nu}F_2"
    )
    st.latex(
        r"S_e=\Delta\sigma\,(2B)\,\frac{1-\nu^2}{E_s}\,I_s I_f"
        r"\qquad (\text{centro: }\alpha=4,\ B'=B/2)"
    )
    st.caption(
        "Use kPa para Δσ e Es, metros para B, L e H; ν e If não têm unidade. "
        "A estimativa rígida 0,93 × Se só aparece para sapata quadrada."
    )
    c1, c2, c3 = st.columns(3)
    B = c1.number_input("B (m)", min_value=0.01, value=1.0, step=0.1)
    L = c2.number_input("L (m)", min_value=0.01, value=1.0, step=0.1)
    H = c3.number_input("H compressivel (m)", min_value=0.01, value=5.0, step=0.5)
    c1, c2, c3, c4 = st.columns(4)
    delta_sigma = c1.number_input("Delta sigma (kPa)", min_value=0.0, value=200.0, step=10.0)
    Es = c2.number_input("Es medio (kPa)", min_value=0.01, value=8400.0, step=100.0)
    nu = c3.number_input("Poisson nu", min_value=0.0, max_value=0.5, value=0.3, step=0.05)
    If = c4.number_input("Fator If", min_value=0.01, max_value=1.0, value=0.65, step=0.01)

    r = calcular_sapata(B, L, H, delta_sigma, Es, nu, If)
    st.write(f"m' = L/B = **{r['m']:.4f}**; n' = 2H/B = **{r['n']:.4f}**")
    st.write(
        f"A0 = **{r['A0']:.6f}** · A1 = **{r['A1']:.6f}** · "
        f"A2 = **{r['A2']:.6f}**"
    )
    st.write(
        f"F1 = **{r['F1']:.6f}** · F2 = **{r['F2']:.6f}** · "
        f"Is = **{r['Is']:.6f}** · If = **{If:.3f}**"
    )
    st.metric("Recalque flexivel no centro", f"{r['Se_mm']:.2f} mm")
    if r["Se_rigido_mm"] is not None:
        st.caption(f"Estimativa para fundacao rigida (0,93 x flexivel): {r['Se_rigido_mm']:.2f} mm")

with aba_regressao:
    st.subheader("Máxima e residual — envoltórias de Mohr-Coulomb")
    st.markdown(
        "**O que você vai preencher.** Cada linha é um ensaio: `σₙ` é a tensão "
        "normal aplicada; `τmáx` é o pico da curva de cisalhamento; `τres` é o "
        "patamar residual após grandes deslocamentos. O programa ajusta uma reta "
        "independente para máxima e outra para residual. A tabela começa com o "
        "exemplo dos slides 29–32; edite os valores ou acrescente ensaios."
    )
    st.markdown(
        "**Símbolos.** `n` é o número de ensaios; `x̄` e `ȳ` são as médias. "
        "`SXX` soma os desvios de x ao quadrado; `SXY` soma os produtos dos "
        "desvios de x e y. `a` é o coeficiente angular da reta e `b` o coeficiente "
        "linear. O chapéu em `ŷᵢ` significa valor estimado: é o y que a reta prevê "
        "para aquele `xᵢ`. O resíduo `eᵢ=yᵢ−ŷᵢ` compara a medida com a previsão; "
        "resíduo positivo deixa o ponto acima da reta e negativo, abaixo. O mesmo "
        "procedimento é repetido, uma vez para `τmáx` e outra para `τres`."
    )
    st.latex(
        r"\bar{x}=\frac{\sum x_i}{n},\quad \bar{y}=\frac{\sum y_i}{n},\quad{}"
        r"S_{XX}=\sum(x_i-\bar{x})^2,\quad{}"
        r"S_{XY}=\sum(x_i-\bar{x})(y_i-\bar{y})"
    )
    st.latex(
        r"a=\frac{S_{XY}}{S_{XX}},\quad b=\bar{y}-a\bar{x},\quad"
        r"\hat{y}_i=ax_i+b,\quad e_i=y_i-\hat{y}_i"
    )
    st.latex(
        r"SYY=\sum(y_i-\bar{y})^2,\quad SQT=SYY,\quad{}"
        r"SQR=\sum(\hat{y}_i-\bar{y})^2,\quad SQE=\sum(y_i-\hat{y}_i)^2"
    )
    st.latex(r"SQT=SQR+SQE,\qquad R^2=\frac{SQR}{SQT}=1-\frac{SQE}{SQT},\qquad R=\frac{S_{XY}}{\sqrt{S_{XX}S_{YY}}}")
    st.latex(r"\tau=c+\sigma\tan\phi=a\sigma+b,\qquad \phi=\arctan(a),\quad c=b")
    st.caption("Nesta tela seguimos as siglas do material: SQR é a variação explicada pela reta; SQE é a soma dos erros/resíduos ao quadrado; SQT é a variação total. R é a correlação linear (com sinal) e R² é a fração explicada pelo ajuste.")

    with st.expander("Exemplo resolvido dos slides 29–32 — máxima e residual", expanded=False):
        st.image(
            "assets/exemplo_ajuste_maxima_residual.png",
            caption="À esquerda, leia τmáx (pico) e τres (patamar final); à direita, ajuste uma reta separada para cada conjunto.",
            use_container_width=True,
        )
        st.markdown("**Como ler o gráfico da esquerda.** Cada curva corresponde a uma tensão normal `σₙ`. O ponto mais alto da curva fornece `τmáx`; o valor estabilizado no fim do deslocamento fornece `τres`. Registre os dois valores na linha dessa mesma tensão normal. No gráfico da direita, os dois conjuntos são ajustados separadamente.")
        x_aula = [25.0, 50.0, 100.0]
        y_aula = [37.5, 48.6111, 94.4444]
        y_res_aula = [26.3889, 45.8333, 87.5]
        exemplo_aula = calcular_regressao(x_aula, y_aula)
        exemplo_residual_aula = calcular_regressao(x_aula, y_res_aula)
        x_bar_aula, y_bar_aula = exemplo_aula["xm"], exemplo_aula["ym"]
        st.markdown("**1. Regressão dos picos.** Use `τmáx` = 37,5000, 48,6111 e 94,4444 kPa para `σₙ` = 25, 50 e 100 kPa. Calculamos uma média para cada coluna:")
        st.latex(rf"\bar x=(25+50+100)/3={x_bar_aula:.4f}\ \text{{kPa}},\qquad \bar y=(37.5000+48.6111+94.4444)/3={y_bar_aula:.4f}\ \text{{kPa}}")
        tabela_desvios = pd.DataFrame({
            "xᵢ = σₙ (kPa)": x_aula,
            "yᵢ = τ medida (kPa)": y_aula,
            "xᵢ − x̄": [x - x_bar_aula for x in x_aula],
            "yᵢ − ȳ": [y - y_bar_aula for y in y_aula],
            "(xᵢ − x̄)²": [(x - x_bar_aula) ** 2 for x in x_aula],
            "(xᵢ − x̄)(yᵢ − ȳ)": [(x - x_bar_aula) * (y - y_bar_aula) for x, y in zip(x_aula, y_aula)],
        })
        st.dataframe(tabela_desvios.round(4), hide_index=True, use_container_width=True)
        st.markdown("**2. Somas dos desvios.** A coluna `(xᵢ−x̄)²` soma `SXX`; a última coluna soma `SXY`. A inclinação vem da divisão `SXY/SXX` e a reta passa pelo ponto das médias, por isso `b=ȳ−a·x̄`.")
        sxx_soma_aula = "+".join(f"({x - x_bar_aula:.4f})^2" for x in x_aula)
        sxy_soma_aula = "+".join(f"({x - x_bar_aula:.4f})({y - y_bar_aula:.4f})" for x, y in zip(x_aula, y_aula))
        st.latex(rf"S_{{XX}}={sxx_soma_aula}={exemplo_aula['SXX']:.4f},\qquad S_{{XY}}={sxy_soma_aula}={exemplo_aula['SXY']:.4f}")
        st.latex(rf"S_{{XX}}={exemplo_aula['SXX']:.4f},\qquad S_{{XY}}={exemplo_aula['SXY']:.4f},\qquad a=S_{{XY}}/S_{{XX}}={exemplo_aula['a']:.5f}")
        st.latex(rf"b=\bar y-a\bar x={exemplo_aula['b']:.4f}\ \text{{kPa}},\qquad \hat y={exemplo_aula['a']:.5f}x+{exemplo_aula['b']:.4f}")
        st.markdown("**3. Valores previstos e erros.** Para cada `xᵢ`, substituímos na reta e encontramos `ŷᵢ`. Depois fazemos `eᵢ=yᵢ−ŷᵢ`; elevar cada resíduo ao quadrado evita que erros positivos e negativos se cancelem.")
        tabela_ajuste_aula = pd.DataFrame({
            "xᵢ = σₙ (kPa)": x_aula,
            "yᵢ medido (kPa)": y_aula,
            "ŷᵢ estimado (kPa)": exemplo_aula["ajustados"],
            "ŷᵢ − ȳ": [yhat - y_bar_aula for yhat in exemplo_aula["ajustados"]],
            "(ŷᵢ − ȳ)²": [(yhat - y_bar_aula) ** 2 for yhat in exemplo_aula["ajustados"]],
            "eᵢ = yᵢ − ŷᵢ (kPa)": exemplo_aula["residuos"],
            "eᵢ² (kPa²)": [e**2 for e in exemplo_aula["residuos"]],
        })
        st.dataframe(tabela_ajuste_aula.round(4), hide_index=True, use_container_width=True)
        sqe_soma_aula = "+".join(f"({e:.5f})^2" for e in exemplo_aula["residuos"])
        st.latex(rf"SQE=\sum e_i^2={sqe_soma_aula}={exemplo_aula['SQE']:.4f},\qquad SQT=SQR+SQE={exemplo_aula['SQT']:.4f}")
        st.markdown("**4. Qualidade do ajuste e parâmetros do solo.** `SQE` soma os `eᵢ²`; `SQR` soma a variação explicada pela reta; `SQT` é a variação total dos valores medidos. A última linha mostra que as siglas fecham e como a inclinação/intercepto viram `φ` e `c` na envoltória de Mohr-Coulomb.")
        st.latex(rf"SQR={exemplo_aula['SQR']:.4f},\quad SQE={exemplo_aula['SQE']:.4f},\quad SQT={exemplo_aula['SQT']:.4f},\quad R={exemplo_aula['R']:.4f},\quad R^2={exemplo_aula['R2']:.4f}")
        st.latex(rf"\phi=\arctan(a)={exemplo_aula['phi']:.2f}^\circ,\qquad c=b={exemplo_aula['c']:.3f}\ \text{{kPa}}")
        st.markdown("**5. Regressão dos valores residuais.** Mantemos os mesmos `σₙ` e trocamos y pelos valores do patamar `τres` = 26,3889, 45,8333 e 87,5000 kPa. Abaixo aparecem a reta e os parâmetros calculados para essa segunda série.")
        st.latex(rf"\tau_{{res}}={exemplo_residual_aula['a']:.5f}\,\sigma_n+{exemplo_residual_aula['b']:.4f},\qquad R={exemplo_residual_aula['R']:.5f},\quad R^2={exemplo_residual_aula['R2']:.5f}")
        st.latex(rf"\phi_{{res}}=\arctan(a)={exemplo_residual_aula['phi']:.2f}^\circ,\qquad c_{{res}}=b={exemplo_residual_aula['c']:.3f}\ \text{{kPa}}")

    dados = st.data_editor(
        pd.DataFrame(
            {
                "sigma_n (kPa)": [25.0, 50.0, 100.0],
                "tau_max (kPa)": [37.5, 48.6111, 94.4444],
                "tau_res (kPa)": [26.3889, 45.8333, 87.5],
            }
        ),
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="dados_regressao_maxima_residual",
    ).dropna()
    calcular_ambas = st.button("Ajustar reta máxima e residual", key="calcular_regressoes_max_res")
    if calcular_ambas and len(dados) >= 2:
        x = dados["sigma_n (kPa)"].tolist()
        y_max = dados["tau_max (kPa)"].tolist()
        y_res = dados["tau_res (kPa)"].tolist()
        try:
            ajuste_max = calcular_regressao(x, y_max)
            ajuste_res = calcular_regressao(x, y_res)
            st.markdown("### Resultados das duas retas")
            st.info(
                f"🔵 **Máxima:** τ = {ajuste_max['a']:.5f}·σₙ + {ajuste_max['b']:.4f}; "
                f"a={ajuste_max['a']:.5f}, b=c={ajuste_max['b']:.3f} kPa, "
                f"R={ajuste_max['R']:.5f}, R²={ajuste_max['R2']:.5f}, "
                f"φ={ajuste_max['phi']:.2f}°.\n\n"
                f"🟠 **Residual:** τ = {ajuste_res['a']:.5f}·σₙ + {ajuste_res['b']:.4f}; "
                f"a={ajuste_res['a']:.5f}, b=c={ajuste_res['b']:.3f} kPa, "
                f"R={ajuste_res['R']:.5f}, R²={ajuste_res['R2']:.5f}, "
                f"φ={ajuste_res['phi']:.2f}°."
            )
            resumo_ajustes = pd.DataFrame([
                {"Série": "Máxima", "a": ajuste_max["a"], "b = c (kPa)": ajuste_max["b"], "R": ajuste_max["R"], "R²": ajuste_max["R2"], "φ (°)": ajuste_max["phi"], "SQR": ajuste_max["SQR"], "SQE": ajuste_max["SQE"]},
                {"Série": "Residual", "a": ajuste_res["a"], "b = c (kPa)": ajuste_res["b"], "R": ajuste_res["R"], "R²": ajuste_res["R2"], "φ (°)": ajuste_res["phi"], "SQR": ajuste_res["SQR"], "SQE": ajuste_res["SQE"]},
            ])
            st.dataframe(resumo_ajustes.round(5), hide_index=True, use_container_width=True)

            x_inicio = min(0.0, min(x))
            x_fim = max(x) * 1.1 if max(x) > 0 else max(x)
            x_linha = [x_inicio + (x_fim - x_inicio) * i / 100 for i in range(101)]
            figura, eixo = plt.subplots(figsize=(12, 7))
            eixo.scatter(x, y_max, color="tab:blue", marker="o", s=80, label="τmáx medida")
            eixo.plot(x_linha, [ajuste_max["a"] * valor + ajuste_max["b"] for valor in x_linha], color="tab:blue", linewidth=2.5, label="Reta ajustada — máxima")
            eixo.scatter(x, y_res, color="tab:orange", marker="s", s=80, label="τres medida")
            eixo.plot(x_linha, [ajuste_res["a"] * valor + ajuste_res["b"] for valor in x_linha], color="tab:orange", linewidth=2.5, label="Reta ajustada — residual")
            eixo.set_title("Envoltórias ajustadas: resistência máxima e residual")
            eixo.set_xlabel("Tensão normal σₙ (kPa)")
            eixo.set_ylabel("Tensão cisalhante τ (kPa)")
            eixo.grid(True, alpha=0.3)
            eixo.legend(loc="best")
            st.pyplot(figura, use_container_width=True)
            plt.close(figura)

            with st.expander("Memória de cálculo das duas retas", expanded=False):
                for nome, y, ajuste in [("Máxima", y_max, ajuste_max), ("Residual", y_res, ajuste_res)]:
                    st.markdown(f"#### {nome}")
                    st.markdown("Calcule `x̄` e `ȳ`; some os desvios para obter `SXX` e `SXY`; divida para achar `a`; depois calcule `b=ȳ−a·x̄`. Com a reta, encontre `ŷᵢ`, os resíduos `eᵢ`, e por fim os coeficientes de ajuste.")
                    st.latex(rf"\bar x={ajuste['xm']:.5f},\quad \bar y={ajuste['ym']:.5f},\quad S_{{XX}}={ajuste['SXX']:.5f},\quad S_{{XY}}={ajuste['SXY']:.5f}")
                    st.latex(rf"a=\frac{{S_{{XY}}}}{{S_{{XX}}}}={ajuste['a']:.6f},\quad b=\bar y-a\bar x={ajuste['b']:.5f},\quad \hat y={ajuste['a']:.6f}\sigma_n+{ajuste['b']:.5f}")
                    tabela_residuos = pd.DataFrame({
                        "σₙ = xᵢ (kPa)": x,
                        "τ medida = yᵢ (kPa)": y,
                        "ŷᵢ estimado (kPa)": ajuste["ajustados"],
                        "eᵢ = yᵢ − ŷᵢ (kPa)": ajuste["residuos"],
                        "eᵢ² (kPa²)": [e**2 for e in ajuste["residuos"]],
                    })
                    st.dataframe(tabela_residuos.round(5), hide_index=True, use_container_width=True)
                    st.latex(rf"SQR={ajuste['SQR']:.5f},\quad SQE={ajuste['SQE']:.5f},\quad SQT={ajuste['SQT']:.5f},\quad R={ajuste['R']:.5f},\quad R^2={ajuste['R2']:.5f}")
                    st.latex(rf"\phi=\arctan(a)={ajuste['phi']:.2f}^\circ,\qquad c=b={ajuste['c']:.3f}\ \text{{kPa}}")
        except ZeroDivisionError:
            st.warning("Use pelo menos dois valores de σₙ diferentes e dados variáveis em τmáx e τres.")
    elif calcular_ambas:
        st.info("Informe pelo menos dois ensaios completos para ajustar as duas retas.")

with aba_mohr:
    st.subheader("Polo e tensao em um plano escolhido")
    st.markdown(
        "**Roteiro de desenho.** (1) Informe `σᵥ`, tensão normal na face horizontal; "
        "`σₕ`, tensão normal na face vertical; e `τₕ`, cisalhamento na face horizontal. "
        "(2) Com `τ` positivo para cima, marque `Mₕ=(σᵥ,τₕ)` e `Mᵥ=(σₕ,−τₕ)`; "
        "eles são as duas faces perpendiculares e ficam em extremos de um diâmetro. "
        "(3) O centro `C` é a média das tensões normais e o raio `R` é a distância "
        "do centro a qualquer um desses pontos. (4) O polo `P` é a interseção da "
        "horizontal que passa por `Mₕ` com a vertical que passa por `Mᵥ`. (5) Escolha "
        "`α`, o ângulo da reta que sai de `P`, medido desde a horizontal no sentido "
        "anti-horário; a outra interseção com o círculo é `Q`, que informa as tensões "
        "no plano escolhido. Na reta `τ=aσ+b`, `a=tan(α)` é a inclinação e `b` "
        "o intercepto. O parâmetro `t` na equação da reta indica distância ao "
        "longo dela (não é tempo). O arco marca `α` para conferência."
    )
    st.latex(r"C=\frac{\sigma_v+\sigma_h}{2},\qquad R=\sqrt{\left(\frac{\sigma_v-\sigma_h}{2}\right)^2+\tau_h^2}")
    st.latex(r"\sigma_1=C+R,\qquad \sigma_3=C-R")
    st.latex(r"M_h=(\sigma_v,\tau_h),\qquad M_v=(\sigma_h,-\tau_h),\qquad P=(\sigma_h,\tau_h)")
    st.latex(r"(\sigma-C)^2+\tau^2=R^2")
    st.latex(r"\mathbf{u}_\alpha=(\cos\alpha,\sin\alpha),\qquad Q=P-2\big[(P-(C,0))\cdot\mathbf{u}_\alpha\big]\mathbf{u}_\alpha")
    st.caption("Use kPa para σ e τ e graus para α. Os pontos Mₕ e Mᵥ ficam na circunferência; eles são os extremos de um diâmetro.")
    c1, c2, c3, c4 = st.columns(4)
    sigma_v = c1.number_input("σᵥ — normal na face horizontal (kPa)", value=400.0, step=10.0)
    sigma_h = c2.number_input("σₕ — normal na face vertical (kPa)", value=200.0, step=10.0)
    tau_h = c3.number_input("τₕ — cisalhamento na face horizontal (kPa)", value=80.0, step=10.0)
    angulo = c4.number_input("α — ângulo da reta a partir da horizontal (°)", min_value=0.0, max_value=360.0, value=45.0, step=5.0)

    r = calcular_mohr(sigma_v, sigma_h, tau_h, angulo)
    c1, c2, c3 = st.columns(3)
    c1.metric("Centro C", f"{r['C']:.1f} kPa")
    c2.metric("Raio R", f"{r['R']:.1f} kPa")
    c3.metric("σ₁ / σ₃", f"{r['sigma1']:.1f} / {r['sigma3']:.1f} kPa")
    c1, c2 = st.columns(2)
    c1.metric("Polo P = (σ, τ)", f"({r['polo'][0]:.1f}, {r['polo'][1]:.1f}) kPa")
    c2.metric("Ponto Q no plano", f"({r['ponto'][0]:.1f}, {r['ponto'][1]:.1f}) kPa")
    sigma_p, tau_p = r["polo"]
    st.markdown("**Equações numéricas para conferência**")
    st.latex(
        rf"(\sigma-{r['C']:.3f})^2+\tau^2={r['R']:.3f}^2"
        rf"\quad\Rightarrow\quad(\sigma-{r['C']:.3f})^2+\tau^2={r['R']**2:.3f}"
    )
    st.latex(
        rf"\sigma={sigma_p:.3f}+t\cos({angulo:.2f}^\circ),\qquad"
        rf"\tau={tau_p:.3f}+t\sin({angulo:.2f}^\circ)"
    )
    st.write(
        f"P = ({sigma_p:.3f}, {tau_p:.3f}) kPa; "
        f"Q = ({r['ponto'][0]:.3f}, {r['ponto'][1]:.3f}) kPa."
    )
    if abs(cos(radians(angulo))) < 1e-10:
        st.write(f"Reta vertical pelo polo: σ = {sigma_p:.5f} kPa; coeficiente angular e intercepto não definidos.")
    else:
        inclinacao_reta = tan(radians(angulo))
        intercepto_reta = tau_p - inclinacao_reta * sigma_p
        st.latex(r"\tau=a\sigma+b")
        st.latex(rf"\tau={inclinacao_reta:.5f}\,\sigma+({intercepto_reta:.5f})")
        st.write(f"Coeficiente angular a = {inclinacao_reta:.5f}; intercepto b = {intercepto_reta:.5f} kPa.")
    figura = desenhar(r)
    st.pyplot(figura, use_container_width=True)
    plt.close(figura)

with aba_multiplos:
    st.subheader("Círculos de Mohr, envoltória e trajetória P-Q")
    st.markdown(
        "**Como montar.** Ative até cinco círculos, na ordem dos estágios do ensaio. "
        "Digite o centro `Cᵢ` e o raio `Rᵢ` em kPa; se o enunciado der `σ₁` e `σ₃`, "
        "converta pelas fórmulas abaixo. A reta de ruptura usa a coesão `c` e o ângulo "
        "`φ`. No gráfico `p-q`, cada topo de círculo vira `(pᵢ,qᵢ)`: `pᵢ=Cᵢ` e `qᵢ=Rᵢ`. "
        "A reta P-Q liga o topo do primeiro ao topo do último círculo ativo; confira "
        "a inclinação `m`, o ângulo `β` e o intercepto `d` exibidos junto ao gráfico."
    )
    st.latex(
        r"C_i=\frac{\sigma_{1i}+\sigma_{3i}}{2},\quad{}"
        r"R_i=\frac{\sigma_{1i}-\sigma_{3i}}{2},\quad{}"
        r"\sigma_{1i}=C_i+R_i,\quad \sigma_{3i}=C_i-R_i"
    )
    st.latex(
        r"\tau_f=c+\sigma_n\tan\phi,\qquad{}"
        r"p_i=\frac{\sigma_{1i}+\sigma_{3i}}{2}=C_i,\quad{}"
        r"q_i=\frac{\sigma_{1i}-\sigma_{3i}}{2}=R_i"
    )
    st.caption(
        "À esquerda: círculos e envoltória em σ-τ. À direita: trajetória em p-q "
        "passando pelos topos; a linha tracejada liga o primeiro ponto P ao último Q. "
        "Use c e φ compatíveis com tensões totais ou efetivas dos círculos."
    )

    centros_padrao = [100.0, 150.0, 200.0, 250.0, 300.0]
    raios_padrao = [58.66, 83.66, 108.66, 133.66, 158.66]
    centros, raios = [], []
    for i in range(5):
        ativo = st.checkbox(f"Usar círculo {i + 1}", value=i < 3, key=f"usar_circulo_{i + 1}")
        c1, c2 = st.columns(2)
        if ativo:
            centro = c1.number_input(
                f"Centro C{i + 1} (kPa)", value=centros_padrao[i],
                step=10.0, key=f"centro_circulo_{i + 1}"
            )
            raio = c2.number_input(
                f"Raio R{i + 1} (kPa)", min_value=0.0,
                value=raios_padrao[i], step=10.0,
                key=f"raio_circulo_{i + 1}"
            )
            centros.append(centro)
            raios.append(raio)
        else:
            c1.write(f"Centro C{i + 1}: 0 kPa")
            c2.write(f"Raio R{i + 1}: 0 kPa")

    c1, c2 = st.columns(2)
    coesao = c1.number_input("Coesão c (kPa)", min_value=0.0, value=10.0, step=1.0)
    phi = c2.number_input("Ângulo de atrito φ (graus)", min_value=0.0, max_value=89.0, value=30.0, step=1.0)

    inclinacao = tan(radians(phi))
    st.markdown(
        f"**Equação da envoltória:** `τ_f = a·σ + b = {inclinacao:.5f}·σ + {coesao:.3f}` kPa. "
        f"Coeficiente angular `a = tan(φ) = {inclinacao:.5f}`; coeficiente linear "
        f"`b = c = {coesao:.3f} kPa`; ângulo `φ = {phi:.2f}°`."
    )

    if centros:
        linhas = []
        pontos_pq = []
        for i, (centro, raio) in enumerate(zip(centros, raios), start=1):
            sigma1, sigma3 = calcular_tensoes_principais(centro, raio)
            pontos_pq.append((centro, raio))
            linhas.append({"Círculo": i, "C_i (kPa)": centro, "R_i (kPa)": raio,
                           "σ1 (kPa)": sigma1, "σ3 (kPa)": sigma3,
                           "p_i (kPa)": centro, "q_i (kPa)": raio})
            st.latex(
                rf"(\sigma-C_{i})^2+\tau^2=R_{i}^2"
                rf"\quad\Rightarrow\quad(\sigma-{centro:.2f})^2+\tau^2={raio:.2f}^2"
            )
        st.dataframe(pd.DataFrame(linhas), hide_index=True, use_container_width=True)

        if len(pontos_pq) > 1:
            p_p, q_p = pontos_pq[0]
            p_q, q_q = pontos_pq[-1]
            if p_q != p_p:
                inclinacao_pq = (q_q - q_p) / (p_q - p_p)
                beta = degrees(atan(inclinacao_pq))
                intercepto_d = q_p - inclinacao_pq * p_p
                st.markdown("**Reta P-Q da trajetória de tensões**")
                st.latex(r"q=mp+d,\qquad m=\frac{q_Q-q_P}{p_Q-p_P},\qquad \beta=\arctan(m)")
                st.latex(rf"q={inclinacao_pq:.5f}\,p+({intercepto_d:.5f})")
                st.write(f"m = {inclinacao_pq:.5f}; β = {beta:.3f}°; d = {intercepto_d:.3f} kPa.")
            else:
                st.markdown(f"**Reta P-Q vertical:** `p = {p_p:.3f} kPa`; β = 90° e d não definido.")
        else:
            st.caption("É preciso ativar pelo menos dois círculos para calcular a reta P-Q.")

        c1, c2 = st.columns(2)
        mostrar_envoltoria = c1.selectbox("Envoltória no gráfico dos círculos", ["Mostrar", "Ocultar"])
        mostrar_pq = c2.selectbox("Reta P-Q no gráfico dos círculos", ["Mostrar", "Ocultar"])
        figura_mohr, figura_pq = desenhar_circulos(
            centros, raios, coesao, phi,
            mostrar_envoltoria == "Mostrar",
            mostrar_pq == "Mostrar",
        )
        st.pyplot(figura_mohr, use_container_width=True)
        st.pyplot(figura_pq, use_container_width=True)
        plt.close(figura_mohr)
        plt.close(figura_pq)
    else:
        st.info("Marque pelo menos um círculo para mostrar os resultados e os gráficos.")

with aba_adensamento:
    st.subheader("Recalques por adensamento")
    st.markdown(
        "**Qual parcela calcular?** O imediato/elástico ocorre logo após o carregamento "
        "e está na aba **Recalque imediato**. O primário ocorre enquanto se dissipa o "
        "excesso de poropressão. O secundário é a deformação adicional depois do fim "
        "do primário. Nesta aba, use tensões efetivas em kPa, espessuras em metros e "
        "logaritmo decimal. Leia primeiro o procedimento da subaba escolhida."
    )
    aba_primario, aba_secundario, aba_tempo = st.tabs(["Primário", "Secundário", "Tempo"])

    with aba_primario:
        st.markdown(
            "**Roteiro.** (1) Informe `H`, `e₀`, `Cr` e `Cc` do ensaio; `σ′v0` é a "
            "tensão efetiva antes da obra no centro da camada, `σ′vm` é a tensão de "
            "pré-adensamento e `Δσ′v` é o acréscimo efetivo causado pela carga. (2) "
            "O programa calcula `σ′vf=σ′v0+Δσ′v`. (3) Se o carregamento ficar abaixo "
            "de `σ′vm`, usa `Cr`; se passar por `σ′vm`, usa `Cr` no trecho até essa "
            "tensão e `Cc` no trecho acima; se a camada já começa normalmente "
            "adensada, usa `Cc` em todo o incremento. (4) Soma as variações de índice "
            "de vazios e converte em recalque por `ΔH=H·Δe/(1+e₀)`."
        )
        st.latex(r"\Delta H=\frac{H}{1+e_0}\,\Delta e")
        st.latex(r"\Delta e_{r}=C_r\log_{10}\!\left(\frac{\sigma'_{vf}}{\sigma'_{v0}}\right),\qquad \Delta e_{v}=C_c\log_{10}\!\left(\frac{\sigma'_{vf}}{\sigma'_{vm}}\right)")
        st.caption("Recompressão é o retorno a tensões já experimentadas pelo solo; compressão virgem é o trecho acima da máxima tensão efetiva passada. O resultado separa os trechos antes de somá-los.")
        c1, c2, c3 = st.columns(3)
        H_ad = c1.number_input("H — espessura compressível (m)", min_value=0.01, value=2.6, step=0.1)
        e0 = c2.number_input("e₀ — índice de vazios inicial", min_value=0.0, value=0.8, step=0.05)
        Cc = c3.number_input("Cc — índice de compressão", min_value=0.0, value=0.28, step=0.01)
        c1, c2, c3, c4 = st.columns(4)
        Cr = c1.number_input("Cr — índice de recompressão", min_value=0.0, value=0.05, step=0.01)
        sigma_v0 = c2.number_input("σ′v0 — tensão inicial (kPa)", min_value=0.01, value=127.0, step=5.0)
        sigma_vm = c3.number_input("σ′vm — pré-adensamento (kPa)", min_value=0.01, value=127.0, step=5.0)
        delta_sigma_ad = c4.number_input("Δσ′v — acréscimo (kPa)", min_value=0.0, value=46.5, step=5.0)

        r_ad = calcular_recalque_primario(H_ad, e0, Cc, Cr, sigma_v0, sigma_vm, delta_sigma_ad)
        sigma_final = r_ad["sigma_final"]
        st.write(f"Caso identificado: **{r_ad['caso']}**; σ′vf = σ′v0 + Δσ′v = **{sigma_final:.3f} kPa**.")
        if r_ad["delta_e_recompressao"]:
            if r_ad["caso"] == "Somente recompressão":
                st.markdown(f"**Trecho Cr (recompressão):** σ′v vai de {sigma_v0:.3f} a {sigma_final:.3f} kPa.")
                st.latex(rf"\Delta e=C_r\log_{{10}}\!\left(\frac{{{sigma_final:.3f}}}{{{sigma_v0:.3f}}}\right)={r_ad['delta_e']:.6f}")
            else:
                st.markdown(
                    f"**Trechos:** `Cr` de {sigma_v0:.3f} a {sigma_vm:.3f} kPa "
                    f"(Δσ′r = acréscimo de tensão efetiva no trecho Cr: "
                    f"{sigma_vm - sigma_v0:.3f} kPa), depois `Cc` de "
                    f"{sigma_vm:.3f} a {sigma_final:.3f} kPa "
                    f"(Δσ′c = acréscimo de tensão efetiva no trecho Cc: "
                    f"{sigma_final - sigma_vm:.3f} kPa)."
                )
                st.latex(rf"\Delta e_r=C_r\log_{{10}}\!\left(\frac{{{sigma_vm:.3f}}}{{{sigma_v0:.3f}}}\right)={r_ad['delta_e_recompressao']:.6f}")
                st.latex(rf"\Delta e_v=C_c\log_{{10}}\!\left(\frac{{{sigma_final:.3f}}}{{{sigma_vm:.3f}}}\right)={r_ad['delta_e_virgem']:.6f}")
        else:
            st.markdown(f"**Trecho Cc (compressão virgem):** σ′v vai de {sigma_v0:.3f} a {sigma_final:.3f} kPa.")
            st.latex(rf"\Delta e=C_c\log_{{10}}\!\left(\frac{{{sigma_final:.3f}}}{{{sigma_v0:.3f}}}\right)={r_ad['delta_e']:.6f}")
        st.latex(rf"\Delta H=\frac{{{H_ad:.3f}}}{{1+{e0:.3f}}}\times {r_ad['delta_e']:.6f}={r_ad['recalque_m']:.6f}\ \text{{m}}")
        st.metric("Recalque primário", f"{r_ad['recalque_mm']:.2f} mm")
        st.caption("O fator 0,93 para fundação rígida mostrado na aula vale para o recalque elástico/imediato; não é aplicado automaticamente ao recalque primário.")

    with aba_secundario:
        st.markdown(
            "**Roteiro.** (1) Use `H` da camada e `Cα` medido no trecho de compressão "
            "secundária do ensaio. (2) Informe `eₚ`, índice de vazios no fim do "
            "primário, e o programa calcula `C′α=Cα/(1+eₚ)`. (3) Informe `t₁`, fim "
            "do primário, e `t₂`, instante final desejado, usando a mesma unidade "
            "(por exemplo, anos nos dois). (4) A equação calcula apenas o recalque "
            "secundário entre esses instantes."
        )
        st.latex(r"C'_{\alpha}=\frac{C_{\alpha}}{1+e_p},\qquad S_s=C'_{\alpha}H\log_{10}\!\left(\frac{t_2}{t_1}\right)")
        c1, c2, c3 = st.columns(3)
        H_s = c1.number_input("H — espessura da camada (m)", min_value=0.01, value=2.6, step=0.1, key="H_secundario")
        Calpha = c2.number_input("Cα — índice de compressão secundária", min_value=0.0, value=0.02, step=0.005)
        ep = c3.number_input("ep — índice de vazios ao fim do primário", min_value=0.0, value=0.762, step=0.05)
        c1, c2 = st.columns(2)
        t1 = c1.number_input("t₁ — fim do primário (anos)", min_value=0.001, value=1.5, step=0.5)
        t2 = c2.number_input("t₂ — tempo final (anos)", min_value=0.001, value=5.0, step=0.5)
        if t2 > t1:
            r_sec = calcular_recalque_secundario(Calpha, H_s, ep, t1, t2)
            st.latex(rf"C'_\alpha=\frac{{{Calpha:.4f}}}{{1+{ep:.3f}}}={r_sec['Calpha_modificado']:.5f}")
            st.latex(rf"S_s={r_sec['Calpha_modificado']:.5f}\times {H_s:.3f}\times\log_{{10}}\!\left(\frac{{{t2:.3f}}}{{{t1:.3f}}}\right)={r_sec['recalque_m']:.6f}\ \text{{m}}")
            st.metric("Recalque secundário", f"{r_sec['recalque_mm']:.2f} mm")
            st.caption("Com os valores padrão do exemplo da aula, arredondar C′α para 0,011 dá 14,95 mm; usar o valor completo 0,01135 dá 15,43 mm.")
        else:
            st.info("t₂ precisa ser maior que t₁ para representar o período pós-primário.")

    with aba_tempo:
        st.markdown(
            "**Roteiro.** (1) Escolha o grau médio de adensamento `U` desejado, ou "
            "digite o `Tᵥ` tabelado. (2) Informe `H_d`, a distância máxima de drenagem: "
            "`H/2` quando há saída de água no topo e na base, ou `H` quando só uma face "
            "drena. (3) Informe `Cᵥ` do ensaio. (4) A equação calcula o tempo para "
            "atingir aquele U. A tabela abaixo foi montada pelas aproximações da aula; "
            "no campo percentual, o programa converte U para fração antes de calcular."
        )
        st.latex(r"T_v=\frac{C_vt}{H_d^2}\quad\Longrightarrow\quad t=\frac{T_vH_d^2}{C_v}")
        st.latex(r"T_v=\frac{\pi}{4}U^2\ (U\leq0{,}60),\qquad T_v=-0{,}9332\log_{10}(1-U)-0{,}0851\ (U>0{,}60)")
        st.caption("Nas expressões, U é fração: por exemplo, 50% = 0,50. Use Cv em m²/s e Hd em metros; o tempo sai em segundos.")
        with st.expander("Tabela de consulta: U médio × fator tempo Tᵥ", expanded=True):
            tabela_tempo = [
                {"U médio (%)": U, "Tᵥ": "∞" if U == 100 else f"{calcular_fator_tempo(U):.3f}"}
                for U in range(0, 100, 10)
            ]
            tabela_tempo.append({"U médio (%)": 100, "Tᵥ": "∞"})
            st.table(tabela_tempo)
            st.caption("Valores aproximados calculados pelas expressões da aula. 100% é um limite teórico: exige tempo infinito.")
        modo_Tv = st.radio("Como informar Tᵥ?", ["A partir de U médio", "Digitar Tᵥ"], horizontal=True)
        c1, c2, c3 = st.columns(3)
        if modo_Tv == "A partir de U médio":
            U_percentual = c1.number_input("U — grau médio de adensamento (%)", min_value=0.0, max_value=99.9, value=90.0, step=5.0)
            Tv = calcular_fator_tempo(U_percentual)
            c1.caption(f"Tᵥ calculado = {Tv:.4f}")
        else:
            Tv = c1.number_input("Tᵥ — fator tempo", min_value=0.0001, value=0.848, step=0.01)
        Hd = c2.number_input("H_d — caminho de drenagem (m)", min_value=0.01, value=4.0, step=0.1)
        Cv = c3.number_input("C_v (m²/s)", min_value=0.000000000001, value=0.000000084, step=0.00000001, format="%.10f")
        tempo = calcular_tempo_adensamento(Tv, Hd, Cv)
        st.latex(rf"t=\frac{{{Tv:.4f}\times {Hd:.3f}^2}}{{{Cv:.3e}}}={tempo['segundos']:.0f}\ \text{{s}}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Tempo", f"{tempo['segundos']:.0f} s")
        c2.metric("Dias", f"{tempo['dias']:.2f}")
        c3.metric("Anos", f"{tempo['anos']:.2f}")

with aba_complementares:
    st.subheader("Ensaios de solo e perfil de tensões")
    st.markdown("Escolha uma subaba. Cada uma mostra primeiro quais grandezas entram e depois a conta correspondente.")
    aba_perfil, aba_edometro, aba_resistencia = st.tabs(
        ["Tensões por camadas", "Ensaio de adensamento", "Triaxial e compressão simples"]
    )

    with aba_perfil:
        st.markdown(
            "**Procedimento.** Informe a espessura e os pesos específicos de cada camada. "
            "O programa usa `γnatural` acima do nível d'água e `γsat` abaixo dele; em "
            "cada profundidade soma os pesos dos trechos sobrejacentes. A pressão neutra "
            "hidrostática é `u=γw(z−zNA)` abaixo do nível d'água e zero acima. A tensão "
            "efetiva é a diferença `σ′v=σv−u`."
        )
        st.latex(r"\sigma_v(z)=\sum_i \gamma_i h_i,\qquad u(z)=\gamma_w\max(z-z_{NA},0),\qquad \sigma'_v(z)=\sigma_v(z)-u(z)")
        st.caption("Unidades: espessuras em m, pesos específicos em kN/m³ e tensões em kPa. Os valores iniciais da tabela são só um exemplo para substituir pelos dados da questão.")
        camadas_df = st.data_editor(
            pd.DataFrame({
                "hᵢ (m)": [2.0, 3.0],
                "γnatural (kN/m³)": [18.0, 19.0],
                "γsat (kN/m³)": [20.0, 20.5],
            }),
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            key="camadas_perfil_tensoes",
        ).dropna()
        c1, c2 = st.columns(2)
        nivel_agua = c1.number_input("zNA — profundidade do nível d'água (m)", min_value=0.0, value=1.0, step=0.25)
        gamma_agua = c2.number_input("γw — peso específico da água (kN/m³)", min_value=0.0, value=9.81, step=0.1)
        if not camadas_df.empty and (camadas_df["hᵢ (m)"] > 0).all():
            camadas = list(zip(
                camadas_df["hᵢ (m)"].astype(float),
                camadas_df["γnatural (kN/m³)"].astype(float),
                camadas_df["γsat (kN/m³)"].astype(float),
            ))
            perfil = calcular_perfil(camadas, nivel_agua, gamma_agua)
            resultado_perfil = pd.DataFrame(perfil).rename(columns={
                "sigma_v": "σv (kPa)", "u": "u (kPa)", "sigma_efetiva": "σ′v (kPa)"
            })
            st.dataframe(resultado_perfil.round(3), hide_index=True, use_container_width=True)
            figura, eixo = plt.subplots(figsize=(12, 7))
            profundidades = [linha["z (m)"] for linha in perfil]
            eixo.plot([linha["sigma_v"] for linha in perfil], profundidades, marker="o", label="σv total")
            eixo.plot([linha["u"] for linha in perfil], profundidades, marker="o", label="u neutra")
            eixo.plot([linha["sigma_efetiva"] for linha in perfil], profundidades, marker="o", label="σ′v efetiva")
            if nivel_agua <= sum(camadas_df["hᵢ (m)"].astype(float)):
                eixo.axhline(nivel_agua, color="tab:blue", linestyle="--", alpha=0.6, label="Nível d'água")
            eixo.invert_yaxis()
            eixo.set_xlabel("Tensão (kPa)")
            eixo.set_ylabel("Profundidade z (m)")
            eixo.set_title("Perfil de tensões verticais")
            eixo.grid(True, alpha=0.3)
            eixo.legend()
            st.pyplot(figura, use_container_width=True)
            plt.close(figura)
        else:
            st.info("Informe pelo menos uma camada com espessura maior que zero.")

    with aba_edometro:
        st.markdown(
            "**Procedimento.** Na curva `e × log σ′`, escolha dois pontos do ramo de "
            "recompressão para `Cr` e dois do trecho virgem para `Cc`; em cada par, o "
            "ponto 2 precisa ter maior tensão e menor índice de vazios. Para `Cv`, leia "
            "`t50` pelo método de Casagrande (`log t`) ou `t90` pelo método de Taylor "
            "(`√t`) e use o caminho máximo de drenagem `Hd`. No final, `U` multiplica o "
            "recalque primário final para estimar quanto já ocorreu."
        )
        st.latex(r"C_c\ \text{ou}\ C_r=\frac{e_1-e_2}{\log_{10}(\sigma'_2/\sigma'_1)},\qquad C_v=\frac{T_vH_d^2}{t},\qquad S_c(t)=\frac{U}{100}S_{c,\infty}")
        st.markdown("#### Índices `Cr` e `Cc` a partir de dois pontos")
        st.caption("Use tensões efetivas em kPa e índices de vazios sem unidade. Os campos começam zerados: preencha pontos pertencentes ao mesmo trecho reto do gráfico.")
        st.markdown("**Recompressão — `Cr`.** Ponto 1: menor σ′; ponto 2: maior σ′ no ramo de recompressão.")
        c1, c2, c3, c4 = st.columns(4)
        sigma_r1 = c1.number_input("σ′₁ Cr (kPa)", min_value=0.0, value=0.0, step=10.0, key="sigma_r1")
        e_r1 = c2.number_input("e₁ Cr", min_value=0.0, value=0.0, step=0.01, key="e_r1")
        sigma_r2 = c3.number_input("σ′₂ Cr (kPa)", min_value=0.0, value=0.0, step=10.0, key="sigma_r2")
        e_r2 = c4.number_input("e₂ Cr", min_value=0.0, value=0.0, step=0.01, key="e_r2")
        if sigma_r2 > sigma_r1 > 0 and e_r1 > e_r2:
            Cr_ensaio = calcular_indice_compressao(sigma_r1, e_r1, sigma_r2, e_r2)
            st.latex(rf"C_r=\frac{{{e_r1:.4f}-{e_r2:.4f}}}{{\log_{{10}}({sigma_r2:.3f}/{sigma_r1:.3f})}}={Cr_ensaio:.5f}")
        else:
            st.caption("Para calcular Cr, informe σ′₁ > 0, σ′₂ maior que σ′₁ e e₂ menor que e₁.")

        st.markdown("**Compressão virgem — `Cc`.** Use dois pontos do trecho reto de carregamento virgem.")
        c1, c2, c3, c4 = st.columns(4)
        sigma_c1 = c1.number_input("σ′₁ Cc (kPa)", min_value=0.0, value=0.0, step=10.0, key="sigma_c1")
        e_c1 = c2.number_input("e₁ Cc", min_value=0.0, value=0.0, step=0.01, key="e_c1")
        sigma_c2 = c3.number_input("σ′₂ Cc (kPa)", min_value=0.0, value=0.0, step=10.0, key="sigma_c2")
        e_c2 = c4.number_input("e₂ Cc", min_value=0.0, value=0.0, step=0.01, key="e_c2")
        if sigma_c2 > sigma_c1 > 0 and e_c1 > e_c2:
            Cc_ensaio = calcular_indice_compressao(sigma_c1, e_c1, sigma_c2, e_c2)
            st.latex(rf"C_c=\frac{{{e_c1:.4f}-{e_c2:.4f}}}{{\log_{{10}}({sigma_c2:.3f}/{sigma_c1:.3f})}}={Cc_ensaio:.5f}")
        else:
            st.caption("Para calcular Cc, informe σ′₁ > 0, σ′₂ maior que σ′₁ e e₂ menor que e₁.")

        st.markdown("#### Coeficiente de adensamento `Cv`")
        st.caption("O tempo do ensaio é informado em minutos; o cálculo converte para segundos. Para dupla drenagem, Hd é metade da altura média da amostra; para drenagem simples, é a altura média inteira.")
        c1, c2, c3 = st.columns(3)
        metodo_cv = c1.radio("Leitura usada", ["t50 — Casagrande", "t90 — Taylor"], index=1, horizontal=True)
        Tv_cv = 0.197 if metodo_cv.startswith("t50") else 0.848
        Hd_cv = c2.number_input("Hd — caminho de drenagem (m)", min_value=0.0, value=0.0098, step=0.001, format="%.4f", key="Hd_cv_ensaio")
        tempo_cv_min = c3.number_input("Tempo t50 ou t90 (min)", min_value=0.0, value=16.0, step=1.0, key="tempo_cv_ensaio")
        if Hd_cv > 0 and tempo_cv_min > 0:
            cv_ensaio = calcular_cv(Tv_cv, Hd_cv, tempo_cv_min)
            st.latex(rf"C_v=\frac{{T_vH_d^2}}{{t}}=\frac{{{Tv_cv:.3f}\times {Hd_cv:.4f}^2}}{{{tempo_cv_min:.2f}\times 60}}={cv_ensaio['Cv_m2_s']:.3e}\ \text{{m}}^2/\text{{s}}")
            c1, c2 = st.columns(2)
            c1.metric("Cv", f"{cv_ensaio['Cv_m2_s']:.3e} m²/s")
            c2.metric("Cv convertido", f"{cv_ensaio['Cv_cm2_s']:.3e} cm²/s")

        with st.expander("Conferência com a Lista 03 — questão 26"):
            st.markdown("A lista usa `Hᵢ=20 mm`, recalque no estágio `ΔH=0,80 mm`, dupla drenagem e `t90=16 min`. A altura média é `19,60 mm`; assim, `Hd=9,80 mm=0,0098 m`. Com `Tv90=0,848`, resulta `Cv≈8,48×10⁻⁸ m²/s` (ou `8,48×10⁻⁴ cm²/s`). Os valores iniciais da calculadora estão preenchidos com esse exemplo.")

        st.markdown("#### Recalque primário já ocorrido")
        st.latex(r"S_c(t)=\frac{U}{100}S_{c,\infty}")
        c1, c2 = st.columns(2)
        U_recalque = c1.number_input("U — grau médio de adensamento (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0, key="U_recalque_parcial")
        Sc_final = c2.number_input("Sc,∞ — recalque primário final (mm)", min_value=0.0, value=0.0, step=5.0, key="Sc_final_parcial")
        Sc_parcial = calcular_recalque_parcial(U_recalque, Sc_final)
        st.latex(rf"S_c(t)=\frac{{{U_recalque:.1f}}}{{100}}\times {Sc_final:.2f}={Sc_parcial:.2f}\ \text{{mm}}")
        st.metric("Recalque primário ocorrido", f"{Sc_parcial:.2f} mm")

    with aba_resistencia:
        st.markdown(
            "**Procedimento.** Informe a geometria inicial da amostra, o encurtamento "
            "e a carga axial na ruptura. O programa calcula a deformação axial, corrige "
            "a área transversal e divide a carga por essa área para obter `σd`. No "
            "triaxial, soma `σd` à tensão confinante `σ₃` para obter `σ₁`. Se a "
            "poropressão `u` foi medida no instante da ruptura, ela pode ser subtraída "
            "das tensões totais para obter as efetivas."
        )
        st.latex(r"\varepsilon_a=\frac{\Delta h}{H_0},\quad A_0=\frac{\pi D^2}{4},\quad A_c=A_0\frac{1-\varepsilon_v}{1-\varepsilon_a},\quad \sigma_d=\frac{P}{A_c}")
        st.latex(r"\sigma_1=\sigma_3+\sigma_d,\quad \sigma'_1=\sigma_1-u,\quad \sigma'_3=\sigma_3-u,\quad S_u=\frac{\sigma_d}{2}\ (\phi_u=0)")
        modo_ensaio = st.radio("Tipo de ensaio", ["Compressão simples (RCS)", "Triaxial"], horizontal=True, key="tipo_reducao_resistencia")
        nao_drenado = modo_ensaio.startswith("Compressão simples")
        if not nao_drenado:
            condicao = st.radio("Condição do cisalhamento", ["Não drenado (CU/UU)", "Drenado (CD)"], horizontal=True, key="condicao_reducao_triaxial")
            nao_drenado = condicao.startswith("Não drenado")
        else:
            st.caption("A compressão simples é o caso particular com σ₃=0; para solo saturado, considera-se ensaio não drenado e volume constante.")

        c1, c2, c3, c4 = st.columns(4)
        carga_kN = c1.number_input("P — carga axial na ruptura (kN)", min_value=0.0, value=0.137293, step=0.01, format="%.6f", key="P_resistencia")
        diametro_m = c2.number_input("D — diâmetro inicial (m)", min_value=0.0, value=0.05, step=0.005, format="%.3f", key="D_resistencia")
        altura_m = c3.number_input("H₀ — altura inicial (m)", min_value=0.0, value=0.10, step=0.01, format="%.3f", key="H0_resistencia")
        encurtamento_m = c4.number_input("Δh — encurtamento na ruptura (m)", min_value=0.0, value=0.0068, step=0.001, format="%.4f", key="dh_resistencia")

        if not nao_drenado:
            c1, c2 = st.columns(2)
            sigma_3 = c1.number_input("σ₃ — confinante (kPa)", min_value=0.0, value=150.0, step=10.0, key="sigma3_resistencia")
            epsilon_v_percentual = c2.number_input("εv — contração volumétrica medida (%)", min_value=-99.0, max_value=99.0, value=0.0, step=0.1, key="ev_resistencia")
            st.caption("Em CD, εv é a variação volumétrica medida, positiva para contração e negativa para dilatação. Em CU/UU e RCS, usa-se εv=0 por volume constante.")
        else:
            sigma_3 = 0.0 if modo_ensaio.startswith("Compressão simples") else st.number_input("σ₃ — confinante (kPa)", min_value=0.0, value=150.0, step=10.0, key="sigma3_nao_drenado")
            epsilon_v_percentual = 0.0
        medir_u = st.checkbox("Tenho u medido na ruptura e quero calcular tensões efetivas", value=False, key="medir_u_resistencia")
        u_ruptura = st.number_input("u — poropressão na ruptura (kPa)", value=0.0, step=5.0, key="u_resistencia") if medir_u else None

        if diametro_m > 0 and altura_m > encurtamento_m >= 0:
            epsilon_v = epsilon_v_percentual / 100
            reducao = reduzir_ensaio(
                diametro_m, altura_m, encurtamento_m, carga_kN, sigma_3,
                epsilon_v, u_ruptura,
            )
            st.latex(rf"\varepsilon_a=\frac{{{encurtamento_m:.5f}}}{{{altura_m:.4f}}}={reducao['deformacao_axial']:.5f},\quad A_0={reducao['area_inicial']:.6f}\ \text{{m}}^2,\quad A_c={reducao['area_corrigida']:.6f}\ \text{{m}}^2")
            st.latex(rf"\sigma_d=\frac{{{carga_kN:.5f}\ \text{{kN}}}}{{{reducao['area_corrigida']:.6f}\ \text{{m}}^2}}={reducao['sigma_d']:.2f}\ \text{{kPa}},\quad \sigma_1=\sigma_3+\sigma_d={reducao['sigma_1']:.2f}\ \text{{kPa}}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Área corrigida Ac", f"{reducao['area_corrigida']:.6f} m²")
            c2.metric("Tensão desviadora σd", f"{reducao['sigma_d']:.2f} kPa")
            c3.metric("Tensão principal maior σ₁", f"{reducao['sigma_1']:.2f} kPa")
            if nao_drenado:
                st.metric("Resistência não drenada Su = σd/2", f"{reducao['sigma_d'] / 2:.2f} kPa")
            if u_ruptura is not None:
                st.latex(rf"\sigma'_1={reducao['sigma_1']:.2f}-{u_ruptura:.2f}={reducao['sigma_1_efetiva']:.2f}\ \text{{kPa}},\qquad \sigma'_3={sigma_3:.2f}-{u_ruptura:.2f}={reducao['sigma_3_efetiva']:.2f}\ \text{{kPa}}")
                c1, c2 = st.columns(2)
                c1.metric("σ₁ efetiva", f"{reducao['sigma_1_efetiva']:.2f} kPa")
                c2.metric("σ₃ efetiva", f"{reducao['sigma_3_efetiva']:.2f} kPa")

        with st.expander("Conferência com a Lista 04 — questão 10"):
            st.markdown("A questão usa `D=5,0 cm`, `H₀=10,0 cm`, `P=14 kgf` e encurtamento `Δh=0,68 cm`. Daí `εa=0,068`, `A₀=19,635 cm²` e `Ac=19,635/(1−0,068)=21,068 cm²`. A tensão corrigida é `qu=14/21,068=0,6645 kgf/cm²`; para `φu=0`, `Su=qu/2=0,332 kgf/cm²≈32,57 kPa`. Os campos começam com esses mesmos dados convertidos para kN e m.")

with aba_areias_argilas:
    st.subheader("Resistência das areias e argilas")
    st.markdown(
        "Use esta aba para interpretar o formato das curvas dos slides. Os desenhos abaixo são "
        "recortes do material da aula; servem para reconhecer tendências, não para retirar valores "
        "numéricos de projeto. Em todos os gráficos, `εa` ou `ε₁` é a deformação axial, "
        "`σ₁−σ₃` é a tensão desviadora e `σ₃` é a tensão confinante."
    )
    aba_areias, aba_argilas, aba_condicoes = st.tabs(
        ["Areias", "Argilas", "Ensaios e trajetórias"]
    )

    with aba_areias:
        st.markdown("### Areia fofa: contração e endurecimento")
        st.markdown(
            "**Como ler:** acompanhe a curva `σ₁−σ₃` conforme cresce `εa`. Na areia fofa, "
            "a resistência mobilizada tende a subir gradualmente até um patamar, sem um pico "
            "pronunciado. A resposta volumétrica mostra redução de volume (contração). A tensão "
            "confinante `σ₃` maior desloca a curva para níveis de resistência maiores."
        )
        st.image(
            "assets/resistencia_areias_argilas/areia_fofa_curvas.png",
            caption="Aula 15–16, slide 2 — resposta típica de areia fofa.",
            use_container_width=True,
        )

        st.markdown("### Areia compacta: pico, amolecimento e dilatância")
        st.markdown(
            "A areia compacta mobiliza um **pico de resistência** em deformação menor. Depois "
            "do pico, `σ₁−σ₃` pode cair até um valor residual/estável: isso é amolecimento "
            "pós-pico. Durante o cisalhamento, a tendência de aumento de volume é a dilatância. "
            "A posição e a altura do pico dependem também do confinamento `σ₃`."
        )
        st.image(
            "assets/resistencia_areias_argilas/areia_compacta_curvas.png",
            caption="Aula 15–16, slide 8 — pico e resposta volumétrica da areia compacta.",
            use_container_width=True,
        )

        st.markdown("### Estado crítico: caminhos diferentes, mesmo estado final")
        st.markdown(
            "`e` é o índice de vazios, `ε₁` é a deformação axial e `ecrit` é o índice de vazios "
            "no estado crítico para as condições consideradas. Uma amostra inicialmente fofa "
            "(e maior) tende a diminuir `e`; uma amostra compacta (e menor) tende a aumentá-lo. "
            "Com cisalhamento continuado, os caminhos se aproximam do estado crítico, em que a "
            "deformação prossegue com volume e resistência aproximadamente constantes."
        )
        st.image(
            "assets/resistencia_areias_argilas/estado_critico_areias.png",
            caption="Aula 15–16, slide 17 — caminhos do índice de vazios em direção ao estado crítico.",
            use_container_width=True,
        )

    with aba_argilas:
        st.markdown("### Argila normalmente adensada (NA)")
        st.markdown(
            "`NA` significa normalmente adensada: a tensão efetiva atual é a maior tensão "
            "efetiva que a argila já suportou. No gráfico, a tensão desviadora `σ₁−σ₃` cresce "
            "com a deformação axial `εa` e tende a um patamar, sem um pico seguido de queda "
            "marcante. A curva superior corresponde ao maior confinamento `σ₃`; esse confinamento "
            "permite mobilizar maior tensão desviadora."
        )
        st.image(
            "assets/resistencia_areias_argilas/argila_normalmente_adensada.png",
            caption="Aula 15–16, slide 27 — tensão desviadora em argila normalmente adensada.",
            use_container_width=True,
        )

        st.markdown("### Argila sobreadensada (SA): pico e amolecimento")
        st.markdown(
            "`SA` significa sobreadensada. O índice `RSA` (razão de sobreadensamento, equivalente "
            "ao OCR usado em outros materiais) compara a tensão de pré-adensamento `σ′p` com a "
            "tensão efetiva de adensamento `σ′c`: `RSA=σ′p/σ′c`. Quanto maior a RSA, maior a "
            "memória de carregamento. A resposta pode ter pico seguido de queda; o gráfico "
            "normalizado também compara `((σ₁−σ₃)/σ₃)` entre confinamentos."
        )
        st.image(
            "assets/resistencia_areias_argilas/argila_sobreadensada_tensao_deformacao.png",
            caption="Aula 15–16, slide 31 — curvas de tensão desviadora e resposta normalizada da argila SA.",
            use_container_width=True,
        )
        st.markdown(
            "O gráfico volumétrico ajuda a interpretar a forma da curva: em SA pode haver uma "
            "pequena contração inicial e depois dilatação. A tendência dilatante fica mais "
            "evidente em sobreadensamento elevado e menor confinamento `σ₃`."
        )
        st.image(
            "assets/resistencia_areias_argilas/argila_sobreadensada_volume.png",
            caption="Aula 15–16, slide 32 — deformação volumétrica durante o cisalhamento da argila SA.",
            use_container_width=True,
        )

    with aba_condicoes:
        st.markdown("### Ensaio drenado (CD) e não drenado (CU)")
        st.markdown(
            "`CD` = adensado e drenado: a água pode sair durante o cisalhamento, então há "
            "variação de volume; no exemplo do slide, o solo contrai. `CU` = adensado e não "
            "drenado: a água não sai durante o cisalhamento, então o volume fica constante e "
            "pode surgir excesso de poropressão `Δu`. O desenho compara `σ₁−σ₃`, deformação, "
            "volume e poropressão. A forma e o sinal de `Δu` dependem do estado do solo: argila "
            "NA tende a gerar `Δu` positiva; argila muito SA pode gerar `Δu` negativa."
        )
        st.image(
            "assets/resistencia_areias_argilas/comparacao_CU_CD.png",
            caption="Aula 15–16, slide 39 — comparação esquemática entre CU e CD.",
            use_container_width=True,
        )
        st.caption("Tensões efetivas: σ′=σ−u. Assim, Δu positiva reduz as tensões principais efetivas; Δu negativa aumenta-as.")

        st.markdown("### Ensaio UU e resistência não drenada")
        st.markdown(
            "No ensaio `UU` (não adensado e não drenado), a representação idealizada em tensões "
            "totais tem círculos de Mohr com o mesmo raio e uma envoltória horizontal: `φu≈0`. "
            "A resistência não drenada é `Su=τu=(σ₁−σ₃)/2`. Esse `Su` descreve a resistência "
            "não drenada na condição do ensaio; o intercepto total aparente não deve ser "
            "interpretado automaticamente como coesão efetiva intrínseca."
        )
        st.image(
            "assets/resistencia_areias_argilas/circulos_UU.png",
            caption="Aula 15–16, slide 55 — círculos UU e envoltória horizontal idealizada.",
            use_container_width=True,
        )

        st.markdown("### Trajetória de tensões `p–q` e envoltória")
        st.markdown(
            "Cada círculo de Mohr pode ser representado pelo ponto do topo: `p=(σ₁+σ₃)/2` "
            "no eixo horizontal e `q=(σ₁−σ₃)/2` no vertical. Ligando os pontos de vários "
            "estágios obtém-se a trajetória `p–q`. Na convenção do material, a envoltória é "
            "`q=d+p tanβ`: `tanβ` é a inclinação, `β` seu ângulo com o eixo `p` e `d` o "
            "intercepto no eixo `q`. Para converter aos parâmetros de Mohr–Coulomb usados no "
            "slide: `sinφ′=tanβ` e `c′=d/cosφ′`. Use tensões efetivas ou totais de forma "
            "consistente em toda a trajetória."
        )
        st.image(
            "assets/resistencia_areias_argilas/trajetoria_pq.png",
            caption="Aula 15–16, slide 45 — representação e trajetória no plano p–q.",
            use_container_width=True,
        )
        st.image(
            "assets/resistencia_areias_argilas/envoltoria_pq.png",
            caption="Aula 15–16, slide 47 — reta de envoltória e relação com φ′ e c′.",
            use_container_width=True,
        )
