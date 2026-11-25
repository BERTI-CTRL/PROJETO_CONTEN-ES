"""Gera um memorial PDF didático em LaTeX para o cálculo do muro de arrimo.

O arquivo .tex produzido é autocontido e mantém os desenhos TikZ editáveis para
reaproveitamento em outros relatórios. O PDF também inclui uma animação opcional
do diagrama de pressões; o desenho estático equivalente vem antes dela.
"""

from __future__ import annotations

import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


_DIRETORIO_TEMPLATE = Path(__file__).parent / "templates"
_TEMPLATE_LATEX = "muro_arrimo.tex.j2"


class ErroGeracaoRelatorio(RuntimeError):
    """Erro legível quando o motor LaTeX não consegue compilar o relatório."""


def _numero(valor: float | int | None, casas: int = 2) -> str:
    if valor is None:
        return "não informado"
    texto = f"{float(valor):,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _numero_tex(valor: float | int | None, casas: int = 2) -> str:
    if valor is None:
        return r"\text{não informado}"
    return f"{float(valor):.{casas}f}".replace(".", r"{,}")


def _decimal_tikz(valor: float) -> str:
    """TikZ espera ponto como separador decimal nas coordenadas."""
    return f"{float(valor):.5f}"


def _texto_tex(valor: Any) -> str:
    texto = str(valor)
    substituicoes = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(substituicoes.get(caractere, caractere) for caractere in texto)


def _formula_ka(metodo: str, entradas: dict[str, Any], camada: dict[str, Any], ka: float) -> str:
    phi = _numero_tex(camada["angulo_atrito_graus"], 2)
    beta = _numero_tex(entradas["inclinacao_aterro_graus"], 2)
    delta = _numero_tex(entradas["atrito_solo_muro_graus"], 2)
    if metodo == "Rankine" and abs(float(entradas["inclinacao_aterro_graus"])) < 1e-10:
        return (
            rf"K_a=\tan^2\!\left(45^\circ-\frac{{{phi}^\circ}}{{2}}\right)"
            rf"={_numero_tex(ka, 4)}"
        )
    if metodo == "Rankine":
        return (
            rf"K_a=\frac{{\cos\beta\left(\cos\beta-"
            rf"\sqrt{{\cos^2\beta-\cos^2\varphi}}\right)}}"
            rf"{{\cos\beta+\sqrt{{\cos^2\beta-\cos^2\varphi}}}}"
            rf",\quad\beta={beta}^\circ,\;\varphi={phi}^\circ"
            rf"\quad\Longrightarrow\quad K_a={_numero_tex(ka, 4)}"
        )
    return (
        rf"K_a=\frac{{\cos^2\varphi}}{{\cos\delta\left(1+"
        rf"\sqrt{{\frac{{\sin(\varphi+\delta)\sin(\varphi-\beta)}}"
        rf"{{\cos\delta\cos\beta}}}}\right)^2}}"
        rf",\quad\varphi={phi}^\circ,\;\delta={delta}^\circ,\;\beta={beta}^\circ"
        rf"\quad\Longrightarrow\quad K_a={_numero_tex(ka, 4)}"
    )


def _integracao_pressao(
    pressao_sup: float,
    pressao_inf: float,
    altura: float,
    empuxo: float,
    braco_global: float,
    profundidade_inf: float,
    altura_muro: float,
) -> dict[str, str]:
    """Reproduz os ramos trapezoidal, triangular e de corte por tração do cálculo."""
    p1 = _numero_tex(pressao_sup, 2)
    p2 = _numero_tex(pressao_inf, 2)
    h = _numero_tex(altura, 2)
    if altura <= 0 or (pressao_sup <= 0 and pressao_inf <= 0):
        formula = rf"E=0\quad\text{{(pressões sem parcela compressiva no trecho)}}"
        braco_local = 0.0
        formula_centroide = r"y_{local}=0\,\mathrm{m}"
    elif pressao_sup < 0 < pressao_inf:
        h_comp = altura * pressao_inf / (pressao_inf - pressao_sup)
        formula = (
            rf"h_c=\frac{{h p_2}}{{p_2-p_1}}=\frac{{{h}\times{p2}}}"
            rf"{{{p2}-({p1})}}={_numero_tex(h_comp, 3)}\,\mathrm{{m}},\quad"
            rf"E=\frac{{h p_2^2}}{{2(p_2-p_1)}}="
            rf"\frac{{{h}\times({p2})^2}}{{2[{p2}-({p1})]}}="
            rf"{_numero_tex(empuxo, 3)}\,\mathrm{{kN/m}}"
        )
        braco_local = h_comp / 3.0
        formula_centroide = (
            rf"y_{{local}}=\frac{{h_c}}3="
            rf"\frac{{{_numero_tex(h_comp, 3)}}}3="
            rf"{_numero_tex(braco_local, 3)}\,\mathrm{{m}}"
        )
    elif pressao_sup > 0 > pressao_inf:
        h_comp = altura * pressao_sup / (pressao_sup - pressao_inf)
        formula = (
            rf"h_c=\frac{{h p_1}}{{p_1-p_2}}=\frac{{{h}\times{p1}}}"
            rf"{{{p1}-({p2})}}={_numero_tex(h_comp, 3)}\,\mathrm{{m}},\quad"
            rf"E=\frac{{h p_1^2}}{{2(p_1-p_2)}}="
            rf"\frac{{{h}\times({p1})^2}}{{2[{p1}-({p2})]}}="
            rf"{_numero_tex(empuxo, 3)}\,\mathrm{{kN/m}}"
        )
        braco_local = altura - h_comp / 3.0
        formula_centroide = (
            rf"y_{{local}}=h-\frac{{h_c}}3={h}-"
            rf"\frac{{{_numero_tex(h_comp, 3)}}}3="
            rf"{_numero_tex(braco_local, 3)}\,\mathrm{{m}}"
        )
    else:
        soma = pressao_sup + pressao_inf
        if abs(soma) < 1e-12:
            braco_local = altura / 2.0
            formula = rf"E=\frac{{h(p_1+p_2)}}2=0\quad\text{{(diagrama simétrico)}}"
            formula_centroide = rf"y_{{local}}=\frac{{h}}2={_numero_tex(braco_local, 3)}\,\mathrm{{m}}"
        else:
            braco_local = altura * (2.0 * pressao_sup + pressao_inf) / (3.0 * soma)
            formula = (
                rf"E=\frac{{h(p_1+p_2)}}2="
                rf"\frac{{{h}({p1}+{p2})}}2="
                rf"{_numero_tex(empuxo, 3)}\,\mathrm{{kN/m}}"
            )
            formula_centroide = (
                rf"y_{{local}}=\frac{{h(2p_1+p_2)}}{{3(p_1+p_2)}}="
                rf"\frac{{{h}[2({p1})+({p2})]}}{{3[({p1})+({p2})]}}="
                rf"{_numero_tex(braco_local, 3)}\,\mathrm{{m}}"
            )
    braco_global_calculado = max(0.0, altura_muro - profundidade_inf) + braco_local
    return {
        "formula_empuxo": formula,
        "braco_local_formula": formula_centroide,
        "formula_braco_global": (
            rf"y=H-z_{{inf}}+y_{{local}}="
            rf"{_numero_tex(altura_muro, 2)}-{_numero_tex(profundidade_inf, 2)}"
            rf"+{_numero_tex(braco_local, 3)}={_numero_tex(braco_global_calculado, 3)}\,\mathrm{{m}}"
        ),
        "formula_momento": (
            rf"M=Ey={_numero_tex(empuxo, 3)}\times{_numero_tex(braco_global, 3)}="
            rf"{_numero_tex(empuxo * braco_global, 3)}\,\mathrm{{kN\cdot m/m}}"
        ),
    }


def _pressao_em_cada_trecho(
    entradas: dict[str, Any], camadas: list[dict[str, Any]], resultado: dict[str, Any]
) -> list[dict[str, Any]]:
    h = float(entradas["altura_muro_m"])
    z_na = entradas.get("profundidade_nivel_agua_m")
    gamma_w = float(entradas["peso_especifico_agua_kN_m3"])
    contexto: list[dict[str, Any]] = []
    for trecho in resultado["trechos"]:
        busca = re.search(r"Camada\s+(\d+)", trecho["identificacao_trecho"])
        indice_camada = int(busca.group(1)) if busca else 1
        camada = camadas[indice_camada - 1]
        z1 = float(trecho["profundidade_superior_m"])
        z2 = float(trecho["profundidade_inferior_m"])
        altura = float(trecho["altura_trecho_m"])
        ka = float(trecho["coeficiente_empuxo_ativo"])
        coesao = float(camada["coesao_kPa"])
        sigma1 = float(trecho["tensao_vertical_efetiva_superior_kPa"])
        sigma2 = float(trecho["tensao_vertical_efetiva_inferior_kPa"])
        gamma_eff = float(trecho["peso_especifico_efetivo_kN_m3"])
        metodo = _formula_ka(entradas["metodo_empuxo"], entradas, camada, ka)
        psoil1_raw = float(trecho["pressao_solo_bruta_superior_kPa"])
        psoil2_raw = float(trecho["pressao_solo_bruta_inferior_kPa"])
        psoil1 = float(trecho["pressao_solo_superior_kPa"])
        psoil2 = float(trecho["pressao_solo_inferior_kPa"])
        pq = float(trecho["pressao_sobrecarga_kPa"])
        uw1 = float(trecho["pressao_agua_superior_kPa"])
        uw2 = float(trecho["pressao_agua_inferior_kPa"])
        ptotal1 = psoil1 + pq + uw1
        ptotal2 = psoil2 + pq + uw2

        zna1 = 0.0 if z_na is None else max(0.0, z1 - float(z_na))
        zna2 = 0.0 if z_na is None else max(0.0, z2 - float(z_na))
        integracoes = {
            "solo": _integracao_pressao(
                psoil1_raw, psoil2_raw, altura,
                float(trecho["empuxo_solo_kN_m"]),
                float(trecho["braco_empuxo_solo_ponta_m"]), z2, h,
            ),
            "sobrecarga": _integracao_pressao(
                pq, pq, altura,
                float(trecho["empuxo_sobrecarga_kN_m"]),
                float(trecho["braco_empuxo_sobrecarga_ponta_m"]), z2, h,
            ),
            "agua": _integracao_pressao(
                uw1, uw2, altura,
                float(trecho["empuxo_hidrostatico_kN_m"]),
                float(trecho["braco_empuxo_hidrostatico_ponta_m"]), z2, h,
            ),
        }
        contexto.append({
            "nome": _texto_tex(trecho["identificacao_trecho"]),
            "camada": indice_camada,
            "material": camada,
            "z_sup": _numero_tex(z1),
            "z_inf": _numero_tex(z2),
            "h_trecho": _numero_tex(altura),
            "gamma_eff": _numero_tex(gamma_eff),
            "sigma_sup": _numero_tex(sigma1),
            "sigma_inf": _numero_tex(sigma2),
            "ka": _numero_tex(ka, 4),
            "formula_ka": metodo,
            "gamma_eff_substituicao": (
                rf"\gamma'={_numero_tex(float(camada['peso_especifico_natural_kN_m3']))}"
                rf"\,\mathrm{{kN/m^3}}"
                if z_na is None or (z_na is not None and (z1 + z2) / 2 < float(z_na))
                else rf"\gamma'=\gamma_{{sat}}-\gamma_w="
                     rf"{_numero_tex(float(camada['peso_especifico_saturado_kN_m3']))}"
                     rf"-{_numero_tex(gamma_w)}={_numero_tex(gamma_eff)}\,\mathrm{{kN/m^3}}"
            ),
            "sigma_formula": (
                rf"\sigma'_{{v,inf}}=\sigma'_{{v,sup}}+\gamma'\Delta z="
                rf"{_numero_tex(sigma1)}+{_numero_tex(gamma_eff)}"
                rf"\times({_numero_tex(z2)}-{_numero_tex(z1)})="
                rf"{_numero_tex(sigma2)}\,\mathrm{{kPa}}"
            ),
            "coesao": _numero_tex(coesao),
            "p_solo_bruto_sup": _numero_tex(psoil1_raw),
            "p_solo_bruto_inf": _numero_tex(psoil2_raw),
            "p_solo_sup": _numero_tex(psoil1),
            "p_solo_inf": _numero_tex(psoil2),
            "p_q": _numero_tex(pq),
            "q": _numero_tex(float(entradas["sobrecarga_kPa"])),
            "u_sup": _numero_tex(uw1),
            "u_inf": _numero_tex(uw2),
            "gamma_w": _numero_tex(gamma_w),
            "z_na": _numero_tex(z_na) if z_na is not None else None,
            "prof_agua_sup": _numero_tex(zna1),
            "prof_agua_inf": _numero_tex(zna2),
            "p_total_sup": _numero_tex(ptotal1),
            "p_total_inf": _numero_tex(ptotal2),
            "integracoes": integracoes,
        })
    return contexto


def _tikz_geometria(
    entradas: dict[str, Any], camadas: list[dict[str, Any]], resultado: dict[str, Any]
) -> str:
    h = float(entradas["altura_muro_m"])
    b = float(entradas["largura_base_m"])
    t = float(entradas["largura_topo_m"])
    beta = math.radians(float(entradas["inclinacao_aterro_graus"]))
    x_back_top = b - t
    comprimento_solo = min(0.8 * h, 0.8 * h / max(math.tan(beta), 1e-6))
    x_left = x_back_top - comprimento_solo
    y_ground_left = h + (x_back_top - x_left) * math.tan(beta)
    z_na = entradas.get("profundidade_nivel_agua_m")
    y_na = h - float(z_na) if z_na is not None else None
    dimensao = min(12.5 / max(b + comprimento_solo, 1e-9), 7.6 / max(y_ground_left, h))

    comandos = [
        rf"\begin{{tikzpicture}}[x={_decimal_tikz(dimensao)}cm,y={_decimal_tikz(dimensao)}cm,>=Stealth]",
        r"\tikzset{solo/.style={draw=black!55,fill=brown!17}, agua/.style={draw=none,fill=cyan!19}, muro/.style={draw=black!80,fill=gray!35,line width=1.2pt}}",
        r"\fill[solo] "
        + f"({_decimal_tikz(x_left)},{_decimal_tikz(y_ground_left)}) -- "
        + f"({_decimal_tikz(x_back_top)},{_decimal_tikz(h)}) -- (0,0) -- "
        + f"({_decimal_tikz(x_left)},0) -- cycle;",
    ]
    if y_na is not None and 0 <= y_na <= h:
        x_back_na = x_back_top * y_na / h
        comandos.append(
            rf"\fill[agua] ({_decimal_tikz(x_left)},{_decimal_tikz(y_na)}) -- "
            + f"({_decimal_tikz(x_back_na)},{_decimal_tikz(y_na)}) -- (0,0) -- "
            + f"({_decimal_tikz(x_left)},0) -- cycle;"
        )
    profundidade = 0.0
    for indice, camada in enumerate(camadas, start=1):
        espessura = float(camada["espessura_m"])
        if espessura <= 0:
            continue
        profundidade += espessura
        if profundidade >= h:
            continue
        y_interface = h - profundidade
        x_interface = x_back_top * y_interface / h
        comandos.append(
            rf"\draw[black!55,dashed] ({_decimal_tikz(x_left)},{_decimal_tikz(y_interface)}) -- "
            + f"({_decimal_tikz(x_interface)},{_decimal_tikz(y_interface)});"
        )
        comandos.append(
            rf"\node[font=\small,fill=white,fill opacity=.78,text opacity=1,inner sep=1pt] "
            + f"at ({_decimal_tikz(x_left + 0.31 * (x_interface - x_left))},{_decimal_tikz(y_interface + 0.18)}) "
            + r"{\strut Camada " + str(indice) + "};"
        )
    if y_na is not None and 0 <= y_na <= h:
        comandos.append(
            rf"\draw[cyan!55!black,very thick,densely dashed] ({_decimal_tikz(x_left)},{_decimal_tikz(y_na)}) -- "
            + f"({_decimal_tikz(x_back_top * y_na / h)},{_decimal_tikz(y_na)});"
        )
        comandos.append(
            rf"\node[anchor=east,font=\small,text=cyan!40!black] at ({_decimal_tikz(x_left)},{_decimal_tikz(y_na)}) {{N.A.}};"
        )
    comandos.append(
        rf"\fill[muro] (0,0) -- ({_decimal_tikz(b)},0) -- "
        + f"({_decimal_tikz(b)},{_decimal_tikz(h)}) -- "
        + f"({_decimal_tikz(x_back_top)},{_decimal_tikz(h)}) -- cycle;"
    )
    comandos.append(
        rf"\draw[black!75,very thick] ({_decimal_tikz(x_left)},{_decimal_tikz(y_ground_left)}) -- "
        + f"({_decimal_tikz(x_back_top)},{_decimal_tikz(h)});"
    )
    # Aterro e q ficam a montante (lado esquerdo) da face inclinada.
    if float(entradas["sobrecarga_kPa"]) > 0:
        for frac in (0.22, 0.42, 0.62, 0.82):
            x = x_left + (x_back_top - x_left) * frac
            y = h + (x_back_top - x) * math.tan(beta)
            comandos.append(
                rf"\draw[orange!85!black,->,thick] ({_decimal_tikz(x)},{_decimal_tikz(y + 0.55)}) -- "
                + f"({_decimal_tikz(x)},{_decimal_tikz(y + 0.06)});"
            )
        xq = (x_left + x_back_top) / 2
        yq = h + (x_back_top - xq) * math.tan(beta)
        comandos.append(
            rf"\node[anchor=south,font=\small,text=orange!60!black] at ({_decimal_tikz(xq)},{_decimal_tikz(yq + .58)}) "
            + rf"{{$q={_numero_tex(float(entradas['sobrecarga_kPa']))}\,\mathrm{{kPa}}$}};"
        )
    # Cotas principais, com setas em ambos os sentidos.
    comandos.extend([
        rf"\draw[<->,>=Stealth] ({_decimal_tikz(x_left - .4)},{_decimal_tikz(0)}) -- "
        + f"({_decimal_tikz(x_left - .4)},{_decimal_tikz(h)}) node[midway,left,font=\\small] {{$H={_numero_tex(h)}\\,\\mathrm{{m}}$}};",
        rf"\draw[<->,>=Stealth] (0,-.35) -- ({_decimal_tikz(b)},-.35) node[midway,below,font=\small] "
        + rf"{{$b={_numero_tex(b)}\,\mathrm{{m}}$}};",
        rf"\draw[<->,>=Stealth] ({_decimal_tikz(x_back_top)},{_decimal_tikz(h + .3)}) -- "
        + f"({_decimal_tikz(b)},{_decimal_tikz(h + .3)}) node[midway,above,font=\\small] {{$t={_numero_tex(t)}\\,\\mathrm{{m}}$}};",
        r"\node[below left,font=\small] at (0,0) {Ponta};",
        r"\node[below right,font=\small] at (" + _decimal_tikz(b) + r",0) {Calcanhar};",
        r"\end{tikzpicture}",
    ])
    return "\n".join(comandos)


def _tikz_diagrama_pressao(
    entradas: dict[str, Any], resultado: dict[str, Any], nome: str, cor: str
) -> str:
    h = float(entradas["altura_muro_m"])
    conjuntos: list[tuple[float, float, float, float]] = []
    chaves = {
        "solo": ("pressao_solo_superior_kPa", "pressao_solo_inferior_kPa"),
        "sobrecarga": ("pressao_sobrecarga_kPa", "pressao_sobrecarga_kPa"),
        "agua": ("pressao_agua_superior_kPa", "pressao_agua_inferior_kPa"),
        "total": (None, None),
    }
    for trecho in resultado["trechos"]:
        z1 = float(trecho["profundidade_superior_m"])
        z2 = float(trecho["profundidade_inferior_m"])
        if nome == "total":
            p1 = float(trecho["pressao_solo_superior_kPa"] + trecho["pressao_sobrecarga_kPa"] + trecho["pressao_agua_superior_kPa"])
            p2 = float(trecho["pressao_solo_inferior_kPa"] + trecho["pressao_sobrecarga_kPa"] + trecho["pressao_agua_inferior_kPa"])
        else:
            k1, k2 = chaves[nome]
            p1, p2 = float(trecho[k1]), float(trecho[k2])
        conjuntos.append((z1, z2, max(0.0, p1), max(0.0, p2)))
    max_pressao = max((max(p1, p2) for _, _, p1, p2 in conjuntos), default=1.0)
    max_pressao = max(max_pressao, 1e-6)
    largura = 4.3
    escala = largura / max_pressao
    linhas = [
        rf"\begin{{tikzpicture}}[x=1cm,y=0.85cm,>=Stealth]",
        rf"\draw[->] (0,-.35) -- (0,{_decimal_tikz(h + .5)}) node[above] {{$z$}};",
        rf"\draw[->] (0,-.35) -- ({_decimal_tikz(largura + .45)},-.35) node[right] {{Pressão (kPa)}};",
        rf"\foreach \y/\lab in {{0/0,{_decimal_tikz(h / 2)}/{_numero(h / 2)}, {_decimal_tikz(h)}/{_numero(h)}}} "
        rf"\draw[gray!25] (0,\y) -- ({_decimal_tikz(largura)},\y) node[left=2pt,font=\scriptsize] {{\lab}};",
    ]
    for z1, z2, p1, p2 in conjuntos:
        y1, y2 = h - z1, h - z2
        x1, x2 = p1 * escala, p2 * escala
        linhas.append(
            rf"\fill[{cor},opacity=.12] (0,{_decimal_tikz(y1)}) -- "
            + f"({_decimal_tikz(x1)},{_decimal_tikz(y1)}) -- "
            + f"({_decimal_tikz(x2)},{_decimal_tikz(y2)}) -- (0,{_decimal_tikz(y2)}) -- cycle;"
        )
        linhas.append(
            rf"\draw[{cor},line width=1.25pt] (0,{_decimal_tikz(y1)}) -- "
            + f"({_decimal_tikz(x1)},{_decimal_tikz(y1)}) -- ({_decimal_tikz(x2)},{_decimal_tikz(y2)}) -- "
            + f"(0,{_decimal_tikz(y2)});"
        )
    linhas.append(r"\end{tikzpicture}")
    return "\n".join(linhas)


def _animacao_pressao(entradas: dict[str, Any], resultado: dict[str, Any]) -> str:
    """Cria quatro quadros LaTeX que mostram a soma dos diagramas de pressão."""
    h = float(entradas["altura_muro_m"])
    chaves = ("solo", "sobrecarga", "agua", "total")
    cores = {"solo": "blue!70!black", "sobrecarga": "orange!90!black", "agua": "cyan!60!black", "total": "red!80!black"}
    rótulos = {"solo": "Solo", "sobrecarga": "Sobrecarga", "agua": "Água", "total": "Pressão total"}
    frames: list[str] = []
    for indice, chave in enumerate(chaves):
        camadas_ativas = chaves[:indice + 1]
        ytop = h + 0.5
        quadro = [
            r"\begin{tikzpicture}[x=1cm,y=.8cm,>=Stealth]",
            rf"\draw[->] (0,0) -- (0,{_decimal_tikz(ytop)}) node[above] {{Cota}};",
            r"\draw[->] (0,0) -- (5.1,0) node[right] {Pressão};",
        ]
        for camada in camadas_ativas:
            codigo = _tikz_diagrama_pressao(entradas, resultado, camada, cores[camada])
            # O desenho da própria figura traz eixos; recortamos somente os preenchimentos.
            comandos = [linha for linha in codigo.splitlines() if "\\fill[" in linha or "\\draw[" in linha and "--" in linha]
            quadro.extend(comandos)
        quadro.append(
            rf"\node[anchor=west,font=\large\bfseries] at (0,{_decimal_tikz(h + .85)}) "
            + rf"{{Etapa {indice + 1}: {rótulos[chave]}}};"
        )
        quadro.append(r"\end{tikzpicture}")
        frames.append("\n".join(quadro))
    return "\n\\newframe\n".join(frames)


def _tikz_verificacoes(
    entradas: dict[str, Any], resultado: dict[str, Any]
) -> str:
    resumo = resultado["resumo"]
    checks = resultado["verificacoes"]
    fatores = [
        float(checks["fator_seguranca_tombamento"]),
        float(checks["fator_seguranca_deslizamento"]),
        float(checks["fator_seguranca_tensao_admissivel"] or 0.0),
        float(entradas["fator_seguranca_minimo_tombamento"]),
        float(entradas["fator_seguranca_minimo_deslizamento"]),
        1.0,
    ]
    limite = max(max(fatores) * 1.18, 2.0)
    largura_cm = 5.2
    fator_escala = largura_cm / limite
    dados = [
        ("Tombamento", fatores[0], fatores[3], checks["status_tombamento"]),
        ("Deslizamento", fatores[1], fatores[4], checks["status_deslizamento"]),
        (
            "Tensão admissível",
            fatores[2],
            1.0,
            checks["status_tensao_maxima_base"],
        ),
    ]
    cores = {"ATENDE": "green!55!black", "REVER": "red!65!black", "BLOQUEADO": "gray!65"}
    linhas = [
        r"\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth]",
        rf"\draw[->] (0,.25) -- ({_decimal_tikz(largura_cm + .4)},.25) node[right] {{Fator calculado}};",
    ]
    for indice, (rotulo, valor, alvo, status) in enumerate(dados):
        y = 2.4 - indice * 0.95
        cor = cores.get(status, "gray!65")
        comprimento = max(0.0, valor) * fator_escala
        alvo_x = alvo * fator_escala
        linhas.extend([
            rf"\node[anchor=east,font=\small] at (-.12,{_decimal_tikz(y + .15)}) {{{rotulo}}};",
            rf"\fill[{cor},opacity=.82] (0,{_decimal_tikz(y)}) rectangle ({_decimal_tikz(comprimento)},{_decimal_tikz(y + .3)});",
            rf"\draw[dashed,red!70!black] ({_decimal_tikz(alvo_x)},{_decimal_tikz(y - .08)}) -- "
            + f"({_decimal_tikz(alvo_x)},{_decimal_tikz(y + .4)});",
            rf"\node[anchor=west,font=\scriptsize] at ({_decimal_tikz(comprimento + .05)},{_decimal_tikz(y + .15)}) "
            + rf"{{$FS={_numero_tex(valor, 3)}$ · {status}}};",
            rf"\node[font=\tiny,text=red!70!black] at ({_decimal_tikz(alvo_x)},{_decimal_tikz(y - .18)}) "
            + rf"{{limite {_numero_tex(alvo, 2)}}};",
        ])
    linhas.append(r"\end{tikzpicture}")
    return "\n".join(linhas)


def montar_relatorio_muro_tex(
    entradas_muro: dict[str, Any],
    camadas_solo: list[dict[str, Any]],
    resultado_muro: dict[str, Any],
    nome_projeto: str = "Estudo de muro de arrimo",
) -> str:
    """Renderiza o .tex autocontido do relatório; útil também para edição manual."""
    h = float(entradas_muro["altura_muro_m"])
    b = float(entradas_muro["largura_base_m"])
    t = float(entradas_muro["largura_topo_m"])
    resumo = resultado_muro["resumo"]
    verificacoes = resultado_muro["verificacoes"]
    camadas = [c for c in camadas_solo if float(c["espessura_m"]) > 0]
    mapa_ka: dict[int, float] = {}
    for trecho in resultado_muro["trechos"]:
        busca = re.search(r"Camada\s+(\d+)", trecho["identificacao_trecho"])
        if busca:
            mapa_ka[int(busca.group(1))] = float(trecho["coeficiente_empuxo_ativo"])
    camadas_contexto = []
    for indice, camada in enumerate(camadas_solo, start=1):
        if float(camada["espessura_m"]) <= 0:
            continue
        camadas_contexto.append({
            "indice": indice,
            "espessura": _numero_tex(float(camada["espessura_m"])),
            "gamma_nat": _numero_tex(float(camada["peso_especifico_natural_kN_m3"])),
            "gamma_sat": _numero_tex(float(camada["peso_especifico_saturado_kN_m3"])),
            "coesao": _numero_tex(float(camada["coesao_kPa"])),
            "phi": _numero_tex(float(camada["angulo_atrito_graus"])),
            "ka": _numero_tex(mapa_ka.get(indice), 4),
            "ka_formula": _formula_ka(entradas_muro["metodo_empuxo"], entradas_muro, camada, mapa_ka.get(indice, 0.0)),
        })
    trechos = _pressao_em_cada_trecho(entradas_muro, camadas_solo, resultado_muro)
    fs_tombamento_min = float(entradas_muro["fator_seguranca_minimo_tombamento"])
    fs_deslizamento_min = float(entradas_muro["fator_seguranca_minimo_deslizamento"])
    gamma_c = float(entradas_muro["peso_especifico_concreto_kN_m3"])
    b_tri = b - t
    area_tri = 0.5 * b_tri * h
    area_ret = t * h
    peso_tri = area_tri * gamma_c
    peso_ret = area_ret * gamma_c
    x_tri = 2.0 * b_tri / 3.0
    x_ret = b - t / 2.0
    momento_tri = peso_tri * x_tri
    momento_ret = peso_ret * x_ret
    resumo_contexto = {
        key: _numero_tex(value, 3)
        for key, value in resumo.items()
        if isinstance(value, (int, float))
    }
    verificacoes_contexto = {
        key: _numero_tex(value, 3) if value is not None else None
        for key, value in verificacoes.items()
        if isinstance(value, (int, float)) or value is None
    }
    contexto = {
        "nome_projeto": _texto_tex(nome_projeto),
        "metodo": _texto_tex(entradas_muro["metodo_empuxo"]),
        "entradas": {
            "H": _numero_tex(h), "b": _numero_tex(b), "t": _numero_tex(t),
            "gamma_c": _numero_tex(gamma_c),
            "q": _numero_tex(float(entradas_muro["sobrecarga_kPa"])),
            "beta": _numero_tex(float(entradas_muro["inclinacao_aterro_graus"])),
            "delta": _numero_tex(float(entradas_muro["atrito_solo_muro_graus"])),
            "atrito_base": _numero_tex(float(entradas_muro["coeficiente_atrito_base"]), 3),
            "qadm": _numero_tex(float(entradas_muro["tensao_admissivel_fundacao_kPa"])),
            "fs_tomb_min": _numero_tex(fs_tombamento_min),
            "fs_des_min": _numero_tex(fs_deslizamento_min),
            "z_na": _numero_tex(entradas_muro.get("profundidade_nivel_agua_m")) if entradas_muro.get("profundidade_nivel_agua_m") is not None else None,
            "gamma_w": _numero_tex(float(entradas_muro["peso_especifico_agua_kN_m3"])),
        },
        "camadas": camadas_contexto,
        "trechos": trechos,
        "resumo": resumo_contexto,
        "checks": verificacoes_contexto,
        "status": {
            "tombamento": _texto_tex(verificacoes["status_tombamento"]),
            "deslizamento": _texto_tex(verificacoes["status_deslizamento"]),
            "tensao": _texto_tex(verificacoes["status_tensao_maxima_base"]),
            "regime": _texto_tex(verificacoes["regime_pressao_base"]),
        },
        "numero_camadas": len(camadas_contexto),
        "numero_trechos": len(trechos),
        "geometria_tikz": _tikz_geometria(entradas_muro, camadas_solo, resultado_muro),
        "diagrama_total_tikz": _tikz_diagrama_pressao(entradas_muro, resultado_muro, "total", "red!80!black"),
        "diagrama_solo_tikz": _tikz_diagrama_pressao(entradas_muro, resultado_muro, "solo", "blue!70!black"),
        "diagrama_q_tikz": _tikz_diagrama_pressao(entradas_muro, resultado_muro, "sobrecarga", "orange!90!black"),
        "diagrama_agua_tikz": _tikz_diagrama_pressao(entradas_muro, resultado_muro, "agua", "cyan!60!black"),
        "animacao_pressao": _animacao_pressao(entradas_muro, resultado_muro),
        "verificacoes_tikz": _tikz_verificacoes(entradas_muro, resultado_muro),
        "triangulo": {
            "base": _numero_tex(b_tri), "area": _numero_tex(area_tri),
            "gamma": _numero_tex(gamma_c), "peso": _numero_tex(peso_tri),
            "braco": _numero_tex(x_tri), "momento": _numero_tex(momento_tri),
        },
        "retangulo": {
            "area": _numero_tex(area_ret), "gamma": _numero_tex(gamma_c),
            "peso": _numero_tex(peso_ret), "braco": _numero_tex(x_ret),
            "momento": _numero_tex(momento_ret),
        },
        "data_relatorio": r"\today",
        "pressao_admissivel": _numero_tex(float(entradas_muro["tensao_admissivel_fundacao_kPa"])),
    }
    engine = Environment(
        loader=FileSystemLoader(_DIRETORIO_TEMPLATE),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return engine.get_template(_TEMPLATE_LATEX).render(**contexto)


def compilar_relatorio_muro_pdf(codigo_tex: str, timeout_s: int = 90) -> bytes:
    """Compila o fonte LaTeX em PDF sem shell escape ou escrita fora da pasta temporária."""
    compiladores = [
        (nome, caminho)
        for nome in ("pdflatex", "lualatex", "tectonic")
        if (caminho := shutil.which(nome)) is not None
    ]
    if not compiladores:
        raise ErroGeracaoRelatorio(
            "Nenhum compilador LaTeX (pdflatex, lualatex ou Tectonic) está instalado neste servidor. "
            "O arquivo .tex pode ser baixado e compilado no MiKTeX ou TeX Live."
        )
    with tempfile.TemporaryDirectory(prefix="relatorio-muro-") as diretorio_temp:
        raiz_temp = Path(diretorio_temp)
        arquivo_tex = raiz_temp / "relatorio_muro_arrimo.tex"
        arquivo_pdf = raiz_temp / "relatorio_muro_arrimo.pdf"
        arquivo_tex.write_text(codigo_tex, encoding="utf-8")
        erros_compilacao: list[str] = []
        for nome_compilador, executavel in compiladores:
            if nome_compilador == "tectonic":
                comando = [
                    executavel, "--keep-logs", "--reruns", "1", "--outdir",
                    str(raiz_temp), arquivo_tex.name,
                ]
                quantidade_passadas = 1
            else:
                comando = [
                    executavel,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    arquivo_tex.name,
                ]
                quantidade_passadas = 2
            log_final = ""
            sucesso = True
            for _ in range(quantidade_passadas):
                try:
                    processo = subprocess.run(
                        comando,
                        cwd=raiz_temp,
                        capture_output=True,
                        text=True,
                        timeout=timeout_s,
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    sucesso = False
                    log_final = f"Tempo limite de {timeout_s} s excedido no compilador {nome_compilador}."
                    break
                log_final = (processo.stdout + "\n" + processo.stderr)[-12000:]
                if processo.returncode != 0:
                    sucesso = False
                    break
            if sucesso and arquivo_pdf.is_file():
                return arquivo_pdf.read_bytes()
            linhas_log = "\n".join(log_final.splitlines()[-28:])
            erros_compilacao.append(f"--- {nome_compilador} ---\n{linhas_log}")
        detalhes = "\n".join(erros_compilacao)
        raise ErroGeracaoRelatorio(
            "A compilação do relatório falhou nos motores LaTeX disponíveis. "
            "O arquivo .tex continua disponível para compilação manual.\n" + detalhes
        )


def gerar_relatorio_muro_arrimo(
    entradas_muro: dict[str, Any],
    camadas_solo: list[dict[str, Any]],
    resultado_muro: dict[str, Any],
    nome_projeto: str = "Estudo de muro de arrimo",
) -> tuple[bytes, bytes]:
    """Retorna ``(pdf, fonte_tex)`` para download no aplicativo ou uso externo."""
    codigo_tex = montar_relatorio_muro_tex(
        entradas_muro, camadas_solo, resultado_muro, nome_projeto
    )
    arquivo_pdf = compilar_relatorio_muro_pdf(codigo_tex)
    return arquivo_pdf, codigo_tex.encode("utf-8")
