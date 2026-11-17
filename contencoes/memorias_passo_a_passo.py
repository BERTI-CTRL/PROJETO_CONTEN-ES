"""Monta memoriais didáticos em Markdown a partir dos resultados calculados."""

from __future__ import annotations

from typing import Any


def _numero(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{float(valor):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _latex_numero(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return r"\text{não calculado}"
    return f"{float(valor):.{casas}f}".replace(".", r"{,}")


def montar_memorial_passo_a_passo_muro(
    entradas_muro: dict[str, Any],
    camadas_solo: list[dict[str, Any]],
    resultado_muro: dict[str, Any],
) -> str:
    """Explica o caminho manual equivalente ao cálculo de muro implementado."""
    altura = float(entradas_muro["altura_muro_m"])
    base = float(entradas_muro["largura_base_m"])
    topo = float(entradas_muro["largura_topo_m"])
    gamma_concreto = float(entradas_muro["peso_especifico_concreto_kN_m3"])
    gamma_agua = float(entradas_muro["peso_especifico_agua_kN_m3"])
    resumo = resultado_muro["resumo"]
    verificacoes = resultado_muro["verificacoes"]
    trechos = resultado_muro["trechos"]
    camadas_ativas = [
        (indice, camada)
        for indice, camada in enumerate(camadas_solo, start=1)
        if float(camada["espessura_m"]) > 0
    ]

    linhas = [
        "### Dados do caso",
        f"Método: **{entradas_muro['metodo_empuxo']}** · "
        f"$H={_numero(altura)}\,\mathrm{{m}}$ · "
        f"$b={_numero(base)}\,\mathrm{{m}}$ · "
        f"$t={_numero(topo)}\,\mathrm{{m}}$ · "
        f"$q={_numero(entradas_muro['sobrecarga_kPa'])}\,\mathrm{{kPa}}$ · "
        f"$\\beta={_numero(entradas_muro['inclinacao_aterro_graus'])}^\\circ$ · "
        f"$\\delta={_numero(entradas_muro['atrito_solo_muro_graus'])}^\\circ$.",
        "As contas abaixo são por metro de comprimento do muro. Profundidades $z$ são medidas a partir do topo.",
        "",
        "### 1. Coeficiente de empuxo ativo",
    ]

    if entradas_muro["metodo_empuxo"] == "Rankine":
        if abs(float(entradas_muro["inclinacao_aterro_graus"])) <= 1e-12:
            linhas.append(
                r"Para aterro horizontal, usa-se $K_a=\tan^2(45^\circ-\varphi/2)$ em cada camada."
            )
        else:
            linhas.append(
                r"Para Rankine com aterro inclinado, usa-se "
                r"$K_a=\dfrac{\cos\beta\left(\cos\beta-\sqrt{\cos^2\beta-\cos^2\varphi}\right)}"
                r"{\cos\beta+\sqrt{\cos^2\beta-\cos^2\varphi}}$."
            )
    else:
        linhas.append(
            r"Para Coulomb, usa-se "
            r"$K_a=\dfrac{\cos^2\varphi}{\cos\delta\left(1+\sqrt{"
            r"\dfrac{\sin(\varphi+\delta)\sin(\varphi-\beta)}{"
            r"\cos\delta\cos\beta}}\right)^2}$."
        )
    for indice, camada in camadas_ativas:
        trecho_camada = next(
            (
                trecho
                for trecho in trechos
                if trecho["identificacao_trecho"].startswith(f"Camada {indice} /")
            ),
            None,
        )
        ka = trecho_camada["coeficiente_empuxo_ativo"] if trecho_camada else None
        linhas.append(
            f"- **Camada {indice}:** $\\varphi={_numero(camada['angulo_atrito_graus'])}^\\circ$; "
            f"$K_{{a,{indice}}}={_latex_numero(ka, 4)}$."
        )

    linhas.extend(
        [
            "",
            "### 2. Tensões e pressões em cada trecho",
            r"A tensão vertical efetiva é acumulada camada a camada: "
            r"$\sigma'_{v,2}=\sigma'_{v,1}+\gamma'\Delta z$, com "
            r"$\gamma'=\gamma_{nat}$ acima do N.A. e "
            r"$\gamma'=\gamma_{sat}-\gamma_w$ abaixo dele.",
            r"Em cada trecho, o modelo calcula "
            r"$p_s=\max(0,K_a\sigma'_v-2c\sqrt{K_a})$, "
            r"$p_q=K_aq$ e $u=\gamma_w\max(z-z_{NA},0)$; "
            r"a pressão lateral total é $p=p_s+p_q+u$.",
            "",
            "| Trecho | $z_{sup}/z_{inf}$ (m) | $\\gamma'$ (kN/m³) | "
            "$\\sigma'_{v,sup}/\\sigma'_{v,inf}$ (kPa) | $K_a$ | "
            "$p_{s,sup}/p_{s,inf}$ (kPa) | $p_q$ (kPa) | $u_{sup}/u_{inf}$ (kPa) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for trecho in trechos:
        linhas.append(
            "| {nome} | {z1}/{z2} | {gamma} | {sv1}/{sv2} | {ka} | {ps1}/{ps2} | {pq} | {u1}/{u2} |".format(
                nome=trecho["identificacao_trecho"],
                z1=_numero(trecho["profundidade_superior_m"]),
                z2=_numero(trecho["profundidade_inferior_m"]),
                gamma=_numero(trecho["peso_especifico_efetivo_kN_m3"]),
                sv1=_numero(trecho["tensao_vertical_efetiva_superior_kPa"]),
                sv2=_numero(trecho["tensao_vertical_efetiva_inferior_kPa"]),
                ka=_numero(trecho["coeficiente_empuxo_ativo"], 4),
                ps1=_numero(trecho["pressao_solo_superior_kPa"]),
                ps2=_numero(trecho["pressao_solo_inferior_kPa"]),
                pq=_numero(trecho["pressao_sobrecarga_kPa"]),
                u1=_numero(trecho["pressao_agua_superior_kPa"]),
                u2=_numero(trecho["pressao_agua_inferior_kPa"]),
            )
        )

    linhas.extend(
        [
            "",
            "### 3. Integração das pressões",
            r"Em cada trecho, a área do diagrama de pressão fornece o empuxo: "
            r"$E_i=\int p(z)\,dz$ (trapézio ou triângulo, conforme os valores nas extremidades). "
            r"O braço é medido até a ponta da base e $M_i=E_i\,y_i$.",
            "",
            "| Trecho | $E_s$ (kN/m) | braço $y_s$ (m) | $M_s$ (kN·m/m) | "
            "$E_q$ (kN/m) | braço $y_q$ (m) | $M_q$ (kN·m/m) | "
            "$E_w$ (kN/m) | braço $y_w$ (m) | $M_w$ (kN·m/m) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for trecho in trechos:
        linhas.append(
            "| {nome} | {es} | {ys} | {ms} | {eq} | {yq} | {mq} | {ew} | {yw} | {mw} |".format(
                nome=trecho["identificacao_trecho"],
                es=_numero(trecho["empuxo_solo_kN_m"]),
                ys=_numero(trecho["braco_empuxo_solo_ponta_m"]),
                ms=_numero(trecho["momento_empuxo_solo_ponta_kNm_m"]),
                eq=_numero(trecho["empuxo_sobrecarga_kN_m"]),
                yq=_numero(trecho["braco_empuxo_sobrecarga_ponta_m"]),
                mq=_numero(trecho["momento_empuxo_sobrecarga_ponta_kNm_m"]),
                ew=_numero(trecho["empuxo_hidrostatico_kN_m"]),
                yw=_numero(trecho["braco_empuxo_hidrostatico_ponta_m"]),
                mw=_numero(trecho["momento_empuxo_hidrostatico_ponta_kNm_m"]),
            )
        )
    linhas.append(
        f"**Somas:** $E_s={_numero(resumo['empuxo_solo_kN_m'])}$ kN/m, "
        f"$E_q={_numero(resumo['empuxo_sobrecarga_kN_m'])}$ kN/m, "
        f"$E_w={_numero(resumo['empuxo_hidrostatico_kN_m'])}$ kN/m; "
        f"$M_s={_numero(resumo['momento_solo_ponta_kNm_m'])}$, "
        f"$M_q={_numero(resumo['momento_sobrecarga_ponta_kNm_m'])}$ e "
        f"$M_w={_numero(resumo['momento_hidrostatico_ponta_kNm_m'])}$ kN·m/m."
    )

    largura_triangular = base - topo
    peso_triangular = 0.5 * largura_triangular * altura * gamma_concreto
    braco_triangular = 2.0 * largura_triangular / 3.0
    peso_retangular = topo * altura * gamma_concreto
    braco_retangular = base - topo / 2.0
    momento_triangular_peso = peso_triangular * braco_triangular
    momento_retangular_peso = peso_retangular * braco_retangular
    v_descendente = float(resumo["componente_vertical_descendente_kN_m"])
    h_total = float(resumo["componente_horizontal_total_kN_m"])
    m_tombador = float(resumo["momento_tombador_ponta_kNm_m"])
    m_estabilizador = float(resumo["momento_estabilizador_total_kNm_m"])
    fs_tombamento = float(verificacoes["fator_seguranca_tombamento"])
    fs_deslizamento = float(verificacoes["fator_seguranca_deslizamento"])

    linhas.extend(
        [
            "",
            "### 4. Peso próprio, forças e momentos",
            r"A seção trapezoidal é decomposta em um retângulo e um triângulo: "
            r"$W_{ret}=tH\gamma_c$ e $W_{tri}=\frac{(b-t)H\gamma_c}{2}$. "
            r"Os braços desde a ponta são $x_{ret}=b-t/2$ e $x_{tri}=2(b-t)/3$.",
            "",
            f"- $W_{{ret}}={_numero(peso_retangular)}\\,\\mathrm{{kN/m}}$; "
            f"$x_{{ret}}={_numero(braco_retangular)}\\,\\mathrm{{m}}$.",
            f"- $W_{{tri}}={_numero(peso_triangular)}\\,\\mathrm{{kN/m}}$; "
            f"$x_{{tri}}={_numero(braco_triangular)}\\,\\mathrm{{m}}$.",
            f"Momentos dos pesos: $M_{{tri}}=W_{{tri}}x_{{tri}}="
            f"{_numero(peso_triangular)}\\times{_numero(braco_triangular)}$ e "
            f"$M_{{ret}}=W_{{ret}}x_{{ret}}="
            f"{_numero(peso_retangular)}\\times{_numero(braco_retangular)}$ kN·m/m.",
            f"$M_{{est}}=M_{{tri}}+M_{{ret}}+V_db="
            f"{_numero(momento_triangular_peso)}+{_numero(momento_retangular_peso)}+"
            f"{_numero(v_descendente)}\\times{_numero(base)}="
            f"{_numero(m_estabilizador)}$ kN·m/m.",
            f"- Peso do muro $W={_numero(resumo['peso_muro_kN_m'])}\\,\\mathrm{{kN/m}}$; "
            f"parcela vertical descendente de Coulomb $V_d={_numero(v_descendente)}\\,\\mathrm{{kN/m}}$; "
            f"carga vertical total $V=W+V_d={_numero(resumo['carga_vertical_total_kN_m'])}\\,\\mathrm{{kN/m}}$.",
            r"Para Coulomb, $H_{tot}=(E_s+E_q)\cos\delta+E_w$ e "
            r"$V_d=(E_s+E_q)\sin\delta$. O momento tombador é "
            r"$M_{tomb}=(M_s+M_q)\cos\delta+M_w$; o momento estabilizador soma "
            r"os momentos dos pesos e $V_db$.",
            f"- $H_{{tot}}={_numero(h_total)}\\,\\mathrm{{kN/m}}$; "
            f"$M_{{tomb}}={_numero(m_tombador)}\\,\\mathrm{{kN\\cdot m/m}}$; "
            f"$M_{{est}}={_numero(m_estabilizador)}\\,\\mathrm{{kN\\cdot m/m}}$.",
            "",
            "### 5. Verificações de estabilidade",
            r"$FS_{tomb}=M_{est}/M_{tomb}$ e "
            r"$FS_{desl}=Vf/H_{tot}$, em que $f$ é o coeficiente de atrito na base.",
            f"- $FS_{{tomb}}={_numero(m_estabilizador)}\\/{_numero(m_tombador)}="
            f"{_numero(fs_tombamento, 3)}$ · **{verificacoes['status_tombamento']}** "
            f"(mínimo informado: {_numero(entradas_muro['fator_seguranca_minimo_tombamento'], 2)}).",
            f"- $FS_{{desl}}={_numero(resumo['carga_vertical_total_kN_m'])}"
            f"\\times {_numero(entradas_muro['coeficiente_atrito_base'], 3)}"
            f"\\/{_numero(h_total)}={_numero(fs_deslizamento, 3)}$ · "
            f"**{verificacoes['status_deslizamento']}** "
            f"(mínimo informado: {_numero(entradas_muro['fator_seguranca_minimo_deslizamento'], 2)}).",
            "",
            "### 6. Resultante e tensões de contato",
            r"A posição da resultante é $x_R=(M_{est}-M_{tomb})/V$ e "
            r"a excentricidade é $e=b/2-x_R$.",
            f"- $x_R={_numero(verificacoes['posicao_resultante_desde_ponta_m'])}\\,\\mathrm{{m}}$; "
            f"$e={_numero(verificacoes['excentricidade_resultante_m'])}\\,\\mathrm{{m}}$; "
            f"regime: **{verificacoes['regime_pressao_base']}**.",
        ]
    )

    sigma_max = verificacoes["tensao_maxima_base_kPa"]
    sigma_min = verificacoes["tensao_minima_base_kPa"]
    if sigma_max is None:
        linhas.append(
            "A resultante caiu fora da largura da base; por isso o programa bloqueia as tensões de contato."
        )
    elif verificacoes["regime_pressao_base"] == "TRIANGULAR":
        linhas.extend(
            [
                r"Como o contato é triangular, $\sigma_{min}=0$ e "
                r"$\sigma_{max}=2V/[3\min(x_R,b-x_R)]$.",
                f"$\\sigma_{{max}}={_latex_numero(resumo['carga_vertical_total_kN_m'])}"
                f"\\times2/[3\\min({_latex_numero(verificacoes['posicao_resultante_desde_ponta_m'])};"
                f"{_latex_numero(base - float(verificacoes['posicao_resultante_desde_ponta_m']))})]"
                f"={_latex_numero(sigma_max)}\\,\\mathrm{{kPa}}$; "
                f"$\\sigma_{{min}}={_latex_numero(sigma_min)}\\,\\mathrm{{kPa}}$.",
            ]
        )
    else:
        linhas.extend(
            [
                r"Como o contato é trapezoidal, $\sigma_{max,min}=\frac{V}{b}"
                r"\left(1\pm\frac{6|e|}{b}\right)$.",
                f"$\\sigma_{{max}}={_numero(sigma_max)}\\,\\mathrm{{kPa}}$; "
                f"$\\sigma_{{min}}={_numero(sigma_min)}\\,\\mathrm{{kPa}}$.",
            ]
        )
    linhas.append(
        f"Tensão admissível informada: {_numero(entradas_muro['tensao_admissivel_fundacao_kPa'])} kPa · "
        f"FS em relação à tensão admissível: {_numero(verificacoes['fator_seguranca_tensao_admissivel'], 3)} · "
        f"**{verificacoes['status_tensao_maxima_base']}**."
    )
    linhas.extend(
        [
            "",
            "> **Limite do modelo:** este memorial reproduz as hipóteses implementadas no app. "
            "Ele não inclui ruptura global, empuxo passivo à frente do muro nem dimensionamento estrutural do concreto.",
        ]
    )
    return "\n\n".join(linhas)


def montar_memorial_passo_a_passo_talude(
    entradas_talude: dict[str, Any],
    resultado_talude: dict[str, Any],
    circulo_selecionado: dict[str, Any] | None,
) -> str:
    """Explica a geometria e as contas de Fellenius para o círculo selecionado."""
    geometria = resultado_talude["geometria"]
    circulos = resultado_talude["circulos"]
    circulo_critico = resultado_talude["circulo_critico"]
    busca_centros = resultado_talude.get("busca_centros")
    face_m = float(geometria["comprimento_horizontal_face_m"])
    x_entrada_m = float(geometria["coordenada_x_entrada_m"])
    y_entrada_m = float(geometria["cota_entrada_m"])
    x_saida_m = -float(entradas_talude["distancia_pe_saida_m"])
    distancia_m = float(geometria["distancia_entre_entrada_e_saida_m"])
    quantidade_fatias = int(entradas_talude["quantidade_fatias"])

    linhas = [
        "### 1. Geometria e pontos de ruptura",
        r"A crista fica em $x_c=H(H{:}V)$; o ponto de entrada é "
        r"$x_E=x_c+a$ e $y_E=H+(x_E-x_c)\tan\beta$. "
        r"A saída fica em $x_S=-L_b$, $y_S=0$.",
        f"- $x_c={_numero(face_m)}$ m; $E=({_numero(x_entrada_m)}; {_numero(y_entrada_m)})$ m; "
        f"$S=({_numero(x_saida_m)}; 0)$ m.",
        r"A distância da corda é $d=\sqrt{(x_E-x_S)^2+(y_E-y_S)^2}="
        f"{_numero(distancia_m)}\\,\\mathrm{{m}}$.",
        "",
        "### 2. Círculos avaliados",
        "A tabela mostra os raios informados; somente candidatos válidos recebem FS.",
        "",
        "| Círculo | $R$ (m) | Centro $C=(x_c,y_c)$ (m) | Situação | FS · Fellenius |",
        "|---|---:|---:|---|---:|",
    ]
    for circulo in circulos:
        centro = (
            f"({_numero(circulo['centro_x_m'])}; {_numero(circulo['centro_y_m'])})"
            if circulo["centro_x_m"] is not None
            else "—"
        )
        linhas.append(
            f"| {circulo['identificacao']} | {_numero(circulo['raio_m'])} | {centro} | "
            f"{circulo['situacao']} | {_numero(circulo['fator_seguranca'], 3)} |"
        )

    if circulo_critico:
        linhas.append(
            f"**Menor FS entre os raios candidatos:** {circulo_critico['identificacao']}, "
            f"$R={_numero(circulo_critico['raio_m'])}$ m, "
            f"$FS={_numero(circulo_critico['fator_seguranca'], 3)}$."
        )
    else:
        linhas.append("Nenhum raio candidato foi válido; não há FS crítico para esse conjunto.")
    if busca_centros:
        circulo_malha = busca_centros.get("circulo_critico")
        if circulo_malha:
            linhas.append(
                f"**Busca complementar na malha de centros:** menor FS = "
                f"{_numero(circulo_malha['fator_seguranca'], 3)} em "
                f"$C=({_numero(circulo_malha['centro_x_m'])}; "
                f"{_numero(circulo_malha['centro_y_m'])})$ m, "
                f"com $R={_numero(circulo_malha['raio_m'])}$ m. "
                "Esse mínimo é da malha e é mostrado separadamente do menor FS dos círculos candidatos."
            )

    if circulo_selecionado is None:
        linhas.extend(
            [
                "",
                "### 3. Círculo selecionado",
                "Não há um círculo válido selecionado para detalhar as fatias.",
            ]
        )
        return "\n\n".join(linhas)

    raio = float(circulo_selecionado["raio_m"])
    centro_x = circulo_selecionado["centro_x_m"]
    centro_y = circulo_selecionado["centro_y_m"]
    linhas.extend(
        [
            "",
            f"### 3. Círculo selecionado · {circulo_selecionado['identificacao']}",
            f"Situação: **{circulo_selecionado['situacao']}** · raio $R={_numero(raio)}$ m.",
        ]
    )
    if centro_x is None or centro_y is None:
        linhas.append("Como $R<d/2$, não existe geometria circular que ligue a saída à entrada.")
        return "\n\n".join(linhas)

    meia_corda = distancia_m / 2.0
    altura_centro = max(0.0, raio**2 - meia_corda**2) ** 0.5
    linhas.extend(
        [
            r"A altura entre o meio da corda e o centro é "
            r"$h_c=\sqrt{R^2-(d/2)^2}$.",
            f"$h_c=\\sqrt{{{_numero(raio)}^2-({_numero(meia_corda)})^2}}="
            f"{_numero(altura_centro)}\\,\\mathrm{{m}}$.",
            r"O centro calculado pelo app é "
            r"$x_O=(x_E-L_b)/2-(y_E/d)h_c$ e "
            r"$y_O=y_E/2+((x_E+L_b)/d)h_c$.",
            f"Resultado: $C=({_numero(centro_x)}; {_numero(centro_y)})$ m.",
            "",
            "### 4. Divisão em fatias e peso",
            f"A largura horizontal entre saída e entrada é $x_E-x_S={_numero(x_entrada_m - x_saida_m)}$ m. "
            f"Com $n={quantidade_fatias}$, $\\Delta x=({_numero(x_entrada_m - x_saida_m)})/{quantidade_fatias}="
            f"{_numero((x_entrada_m - x_saida_m) / quantidade_fatias)}$ m.",
            r"Para cada fatia, o app aproxima as áreas por trapézios entre terreno, arco circular, "
            r"interface das camadas e N.A. O peso por metro de largura é "
            r"$A_{ij}=\frac{\Delta x}{2}(h_{j,e}+h_{j,d})$, "
            r"$W_i=\sum_j\gamma_jA_{ij}+Q_i$, com $Q_i=q\,b_{q,i}$ na parte da fatia sob a sobrecarga.",
            (
                f"A cota do N.A. é $y_{{NA}}=H-z_{{NA}}="
                f"{_numero(geometria['cota_nivel_agua_m'])}$ m. "
                if geometria["cota_nivel_agua_m"] is not None
                else "Sem N.A. informado, $u_i=0$ em todas as fatias."
            ),
            r"Com N.A. informado, $u_i=\gamma_w\max(0,y_{NA}-y_{base,i})$, "
            r"avaliado na cota média da base da fatia.",
            "",
            "### 5. Forças em cada fatia",
            r"O ângulo médio da base vem dos raios nas bordas; o comprimento da base é "
            r"$\Delta L_i=R|\Delta\theta_i|$. As forças seguem "
            r"$N_i=W_i\cos\alpha_i$, $U_i=u_i\Delta L_i$, "
            r"$N'_i=N_i-U_i$ e $F_{mob,i}=W_i\sin\alpha_i$.",
            r"Para as duas camadas, a resistência é "
            r"$F_{R,i}=c'_1L_{1,i}+c'_2L_{2,i}+N'_i\left["
            r"\frac{L_{1,i}}{\Delta L_i}\tan\varphi'_1+"
            r"\frac{L_{2,i}}{\Delta L_i}\tan\varphi'_2\right]$.",
            "Abaixo, cada linha substitui os valores calculados para a fatia selecionada.",
            "",
        ]
    )

    gamma1n = float(entradas_talude["peso_especifico_natural_camada_superior_kN_m3"])
    gamma1s = float(entradas_talude["peso_especifico_saturado_camada_superior_kN_m3"])
    gamma2n = float(entradas_talude["peso_especifico_natural_camada_inferior_kN_m3"])
    gamma2s = float(entradas_talude["peso_especifico_saturado_camada_inferior_kN_m3"])
    c1 = float(entradas_talude["coesao_efetiva_camada_superior_kPa"])
    c2 = float(entradas_talude["coesao_efetiva_camada_inferior_kPa"])
    phi1 = float(entradas_talude["angulo_atrito_efetivo_camada_superior_graus"])
    phi2 = float(entradas_talude["angulo_atrito_efetivo_camada_inferior_graus"])

    for fatia in circulo_selecionado["fatias"]:
        indice = fatia["numero_fatia"]
        a1n = fatia["area_camada_superior_nao_saturada_m2"]
        a1s = fatia["area_camada_superior_saturada_m2"]
        a2n = fatia["area_camada_inferior_nao_saturada_m2"]
        a2s = fatia["area_camada_inferior_saturada_m2"]
        q_fatia = float(fatia["sobrecarga_fatia_kN_m"])
        termos_peso = " + ".join(
            (
                f"{_latex_numero(gamma1n)}\\times{_latex_numero(a1n)}",
                f"{_latex_numero(gamma1s)}\\times{_latex_numero(a1s)}",
                f"{_latex_numero(gamma2n)}\\times{_latex_numero(a2n)}",
                f"{_latex_numero(gamma2s)}\\times{_latex_numero(a2s)}",
                _latex_numero(q_fatia),
            )
        )
        alpha = fatia["angulo_base_medio_graus"]
        delta_l = fatia["comprimento_arco_m"]
        u = fatia["pressao_neutra_kPa"]
        n_total = fatia["forca_normal_total_kN_m"]
        u_total = fatia["resultante_pressao_neutra_kN_m"]
        n_efetiva = fatia["forca_normal_efetiva_kN_m"]
        resistencia = fatia["forca_resistente_kN_m"]
        mobilizada = fatia["forca_mobilizada_kN_m"]
        linhas.extend(
            [
                f"**Fatia {indice} — {fatia['situacao']}** · "
                f"$y_{{base}}={_numero(fatia['cota_base_m'])}$ m · "
                f"$\\alpha={_numero(alpha)}^\\circ$ · $\\Delta L={_numero(delta_l)}$ m.",
                f"$W_{{{indice}}}={termos_peso}={_latex_numero(fatia['peso_fatia_kN_m'])}\\,\\mathrm{{kN/m}}$.",
            ]
        )
        if n_total is None:
            linhas.append("A base circular não intercepta o terreno nesta fatia; as forças não entram no FS.")
            continue
        linhas.append(
            f"$N_{{{indice}}}=W\\cos\\alpha={_latex_numero(fatia['peso_fatia_kN_m'])}"
            f"\\cos({_latex_numero(alpha)}^\\circ)={_latex_numero(n_total)}$ kN/m; "
            f"$U_{{{indice}}}=u\\Delta L={_latex_numero(u)}\\times{_latex_numero(delta_l)}"
            f"={_latex_numero(u_total)}$ kN/m; "
            f"$N'_{{{indice}}}=N-U={_latex_numero(n_efetiva)}$ kN/m."
        )
        if resistencia is not None:
            l1 = fatia["comprimento_camada_superior_m"]
            l2 = fatia["comprimento_camada_inferior_m"]
            fr_coesao = fatia["forca_resistente_coesao_kN_m"]
            fr_atrito = fatia["forca_resistente_atrito_kN_m"]
            linhas.append(
                f"$F_{{R,{indice}}}=c'_1L_1+c'_2L_2+F_{{\\varphi}}="
                f"({_latex_numero(c1)}\\times{_latex_numero(l1)}+"
                f"{_latex_numero(c2)}\\times{_latex_numero(l2)})+"
                f"{_latex_numero(fr_atrito)}={_latex_numero(resistencia)}$ kN/m "
                f"(coesão: {_numero(fr_coesao)}; atrito: {_numero(fr_atrito)} kN/m)."
            )
            linhas.append(
                f"$F_{{\\varphi,{indice}}}=N'[(L_1/\\Delta L)\\tan\\varphi'_1+"
                f"(L_2/\\Delta L)\\tan\\varphi'_2]="
                f"{_latex_numero(n_efetiva)}[({_latex_numero(l1)}/"
                f"{_latex_numero(delta_l)})\\tan({_latex_numero(phi1)}^\\circ)+"
                f"({_latex_numero(l2)}/{_latex_numero(delta_l)})"
                f"\\tan({_latex_numero(phi2)}^\\circ)]="
                f"{_latex_numero(fr_atrito)}$ kN/m."
            )
        else:
            linhas.append(
                "Como $N'<0$, a fatia é marcada como inválida e a resistência não é usada no FS."
            )
        linhas.append(
            f"$F_{{mob,{indice}}}=W\\sin\\alpha="
            f"{_latex_numero(fatia['peso_fatia_kN_m'])}"
            f"\\sin({_latex_numero(alpha)}^\\circ)={_latex_numero(mobilizada)}$ kN/m."
        )

    if circulo_selecionado["situacao"] == "VÁLIDO":
        resistencia_total = float(circulo_selecionado["resistencia_total_kN_m"])
        mobilizacao_total = float(circulo_selecionado["forca_mobilizada_total_kN_m"])
        fs = float(circulo_selecionado["fator_seguranca"])
        linhas.extend(
            [
                "",
                "### 6. Fator de segurança",
                r"Somam-se as forças resistentes e mobilizadas de todas as fatias válidas: "
                r"$FS=\sum F_{R,i}/\sum F_{mob,i}$.",
                f"$FS={_numero(resistencia_total)}\\/{_numero(mobilizacao_total)}="
                f"{_numero(fs, 3)}$ para **{circulo_selecionado['identificacao']}**.",
            ]
        )
    else:
        linhas.extend(
            [
                "",
                "### 6. Fator de segurança",
                "Este círculo não recebe FS porque não atende aos critérios geométricos ou de força das fatias. "
                f"Motivo informado pelo cálculo: **{circulo_selecionado['situacao']}**.",
                f"Somas diagnósticas: $\\sum F_R={_numero(circulo_selecionado['soma_forcas_resistentes_diagnostica_kN_m'])}$ kN/m; "
                f"$\\sum F_{{mob}}={_numero(circulo_selecionado['soma_forcas_mobilizadas_diagnostica_kN_m'])}$ kN/m. "
                "Essas somas não devem ser tratadas como FS válido.",
            ]
        )

    linhas.extend(
        [
            "",
            "> **Escopo:** o resultado segue a discretização e as hipóteses do app: Fellenius, "
            "superfície circular, N.A. horizontal e até duas camadas. A malha complementa a comparação "
            "dos raios e não representa uma busca automática irrestrita de todas as superfícies possíveis.",
        ]
    )
    return "\n\n".join(linhas)
