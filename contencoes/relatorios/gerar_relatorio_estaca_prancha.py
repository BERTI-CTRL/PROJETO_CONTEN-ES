"""Monta memoriais didaticos em LaTeX/PDF para estacas-prancha.

O modulo organiza os valores calculados pela pagina e desenha o perfil e as
pressões correspondentes. Ele nao repete os calculos de engenharia.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


_DIRETORIO_TEMPLATES = Path(__file__).parent / "templates"
_NOME_TEMPLATE = "estaca_prancha.tex.j2"


class ErroGeracaoRelatorioEstacaPrancha(RuntimeError):
    """Erro legivel quando nao ha compilador LaTeX ou a compilacao falha."""


def _numero(valor: float | int | None, casas: int = 2) -> str:
    """Formata um numero com separadores usados em portugues."""
    if valor is None:
        return "--"
    texto = f"{float(valor):,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _numero_tex(valor: float | int | None, casas: int = 2) -> str:
    """Formata valores numericos dentro de uma expressao matematica TeX."""
    if valor is None:
        return r"\text{--}"
    return f"{float(valor):.{casas}f}".replace(".", r"{,}")


def _decimal_tikz(valor: float) -> str:
    """TikZ usa ponto decimal nas coordenadas, mesmo no relatorio em portugues."""
    return f"{float(valor):.5f}"


def _escapar_tex(texto: Any) -> str:
    """Evita que texto comum seja interpretado como comando LaTeX."""
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
    return "".join(substituicoes.get(caractere, caractere) for caractere in str(texto))


def _tikz_perfil(
    tipo_cortina: str, entradas: dict[str, Any], resultado: dict[str, Any]
) -> str:
    """Desenha a cortina, as cotas e os parametros do caso selecionado."""
    if tipo_cortina == "cortina_em_balanco":
        altura = float(entradas["altura_livre_escavacao_m"])
        ficha_teorica = float(resultado["ficha_teorica_m"])
        ficha_preliminar = float(resultado["ficha_preliminar_m"])
        profundidade_total = altura + ficha_preliminar
        escala_vertical = 6.5 / max(profundidade_total, 0.01)
        return rf"""\begin{{tikzpicture}}[x=1cm,y={_decimal_tikz(escala_vertical)}cm,>=Stealth,
    every node/.style={{font=\small}}]
\fill[areia] (0,0) rectangle (3.0,-{_decimal_tikz(profundidade_total)});
\fill[azulclaro] (-1.8,-{_decimal_tikz(altura)}) rectangle (0,-{_decimal_tikz(profundidade_total)});
\draw[very thick,gray!75!black] (0,0) -- (0,-{_decimal_tikz(profundidade_total)});
\draw[thick,laranja] (0,0) -- (3.0,0) node[above right] {{Solo retido}};
\draw[thick,azul] (-1.8,-{_decimal_tikz(altura)}) -- (0,-{_decimal_tikz(altura)});
\node[above,fill=white,inner sep=1pt,font=\scriptsize,text=azul]
    at (-0.9,-{_decimal_tikz(altura)}) {{Escavação}};
\draw[dashed,azulagua] (0,-{_decimal_tikz(altura + ficha_teorica)}) -- (3.0,-{_decimal_tikz(altura + ficha_teorica)});
\node[font=\scriptsize,anchor=west,text=azulagua] at (0.08,-{_decimal_tikz(altura + ficha_teorica)}) {{$f_{{teo}}$}};
\draw[<->,azul,line width=.8pt] (3.45,0) -- (3.45,-{_decimal_tikz(altura)})
    node[midway,right,font=\scriptsize] {{$h={_numero_tex(altura)}\,\mathrm{{m}}$}};
\draw[<->,azulagua,line width=.8pt] (4.05,-{_decimal_tikz(altura)}) -- (4.05,-{_decimal_tikz(altura + ficha_teorica)})
    node[pos=.12,right,font=\scriptsize] {{$f_{{teo}}={_numero_tex(ficha_teorica)}\,\mathrm{{m}}$}};
\draw[<->,laranja,line width=.8pt] (6.0,-{_decimal_tikz(altura)}) -- (6.0,-{_decimal_tikz(profundidade_total)})
    node[midway,right,font=\scriptsize] {{$f_{{preliminar}}={_numero_tex(ficha_preliminar)}\,\mathrm{{m}}$}};
\end{{tikzpicture}}"""

    h1 = float(entradas["espessura_camada_superior_ate_na_m"])
    profundidade_escavacao = float(resultado["profundidade_escavacao_abaixo_superficie_m"])
    profundidade_ponta = float(resultado["profundidade_ponta_abaixo_superficie_m"])
    profundidade_ancoragem = h1 - float(entradas["altura_ancoragem_acima_na_m"])
    escala_vertical = 6.5 / max(profundidade_ponta, 0.01)
    profundidade_na_escavacao = profundidade_escavacao - h1
    ficha = float(entradas["ficha_abaixo_escavacao_m"])
    altura_ancoragem = float(entradas["altura_ancoragem_acima_na_m"])
    q = float(entradas["sobrecarga_superficie_kPa"])
    setas_sobrecarga = ""
    if q > 0:
        setas_sobrecarga = "\n".join(
            rf"\draw[->,laranja,thick] ({x},0.48) -- ({x},0.06);"
            for x in (0.6, 1.25, 1.9, 2.55)
        )
    return rf"""\begin{{tikzpicture}}[x=1cm,y={_decimal_tikz(escala_vertical)}cm,>=Stealth,
    every node/.style={{font=\small}}]
\fill[areia] (0,0) rectangle (3.0,-{_decimal_tikz(profundidade_ponta)});
\fill[azulclaro] (-1.8,-{_decimal_tikz(profundidade_escavacao)}) rectangle (0,-{_decimal_tikz(profundidade_ponta)});
\draw[very thick,gray!75!black] (0,0) -- (0,-{_decimal_tikz(profundidade_ponta)});
\draw[thick,laranja] (0,0) -- (3.0,0) node[above right] {{Solo retido}};
\draw[dashed,azulagua] (0,-{_decimal_tikz(h1)}) -- (3.0,-{_decimal_tikz(h1)})
    node[above right,font=\scriptsize] {{N.A.}};
\draw[thick,azul] (-1.8,-{_decimal_tikz(profundidade_escavacao)}) -- (0,-{_decimal_tikz(profundidade_escavacao)});
\node[above,fill=white,inner sep=1pt,font=\scriptsize,text=azul]
    at (-0.9,-{_decimal_tikz(profundidade_escavacao)}) {{Escavação}};
\draw[very thick,marrom] (0,-{_decimal_tikz(profundidade_ancoragem)}) -- (1.65,-{_decimal_tikz(profundidade_ancoragem)})
    node[right,font=\scriptsize] {{Tirante}};
{setas_sobrecarga}
\node[above,font=\scriptsize,text=laranja] at (1.55,0.48) {{$q={_numero_tex(q)}\,\mathrm{{kPa}}$}};
\draw[<->,azulagua,line width=.8pt] (-2.3,0) -- (-2.3,-{_decimal_tikz(h1)})
    node[midway,left,font=\scriptsize] {{$H_1={_numero_tex(h1)}\,\mathrm{{m}}$}};
\draw[<->,azul,line width=.8pt] (-1.65,-{_decimal_tikz(h1)}) -- (-1.65,-{_decimal_tikz(profundidade_escavacao)})
    node[midway,left,font=\scriptsize] {{$D={_numero_tex(profundidade_na_escavacao)}\,\mathrm{{m}}$}};
\draw[<->,laranja,line width=.8pt] (-0.95,-{_decimal_tikz(profundidade_escavacao)}) -- (-0.95,-{_decimal_tikz(profundidade_ponta)})
    node[midway,left,font=\scriptsize] {{$f={_numero_tex(ficha)}\,\mathrm{{m}}$}};
\draw[<->,marrom,line width=.8pt] (-0.55,-{_decimal_tikz(h1)}) -- (-0.55,-{_decimal_tikz(profundidade_ancoragem)})
    node[midway,left,fill=white,inner sep=1pt,font=\scriptsize] {{$h_a={_numero_tex(altura_ancoragem)}\,\mathrm{{m}}$}};
\end{{tikzpicture}}"""


def _tikz_diagrama_pressao(
    resultado: dict[str, Any], tipo_cortina: str
) -> tuple[str, list[dict[str, str]]]:
    """Desenha as pressoes do resultado com uma escala comum e cria a legenda."""
    if tipo_cortina == "cortina_em_balanco":
        series = [
            ("ativo", "Pressão ativa", "vermelho", 1.0),
            ("passivo_mobilizado", "Passivo mobilizado", "azul", -1.0),
        ]
        profundidade_total = float(resultado["profundidade_ponta_m"])
    else:
        series = [
            ("ativo", "Solo ativo", "vermelho", 1.0),
            ("hidrostatico", "Água diferencial", "verdeagua", 1.0),
            ("passivo_mobilizado", "Passivo mobilizado", "azul", -1.0),
        ]
        profundidade_total = float(resultado["profundidade_ponta_abaixo_superficie_m"])

    diagrama = resultado["diagrama_pressao"]
    pressoes = [
        float(ponto["pressao_kPa"])
        for chave, _, _, _ in series
        for ponto in diagrama.get(chave, [])
    ]
    pressao_maxima = max(pressoes, default=1.0)
    pressao_maxima = max(pressao_maxima, 1.0)
    escala_horizontal = 2.3 / pressao_maxima
    escala_vertical = 6.2 / max(profundidade_total, 0.01)
    comandos = [
        rf"\begin{{tikzpicture}}[x={_decimal_tikz(escala_horizontal)}cm,y={_decimal_tikz(escala_vertical)}cm,>=Stealth,",
        r"    every node/.style={font=\scriptsize}]",
        rf"\draw[->,gray!80] (-{_decimal_tikz(pressao_maxima * 1.12)},0) -- ({_decimal_tikz(pressao_maxima * 1.12)},0) node[right] {{$p$ (kPa)}};",
        rf"\draw[->,gray!80] (0,0.25) -- (0,-{_decimal_tikz(profundidade_total * 1.08)}) node[below left] {{$z$ (m)}};",
    ]
    legenda = []
    cores = {"vermelho": "vermelho", "azul": "azul", "verdeagua": "verdeagua"}
    for chave, nome, cor, sinal in series:
        pontos = diagrama.get(chave, [])
        if not pontos:
            continue
        coordenadas = [
            (
                sinal * float(ponto["pressao_kPa"]),
                -float(ponto["profundidade_m"]),
            )
            for ponto in pontos
        ]
        caminho = " -- ".join(
            f"({_decimal_tikz(x)},{_decimal_tikz(y)})" for x, y in coordenadas
        )
        primeiro_y = _decimal_tikz(coordenadas[0][1])
        ultimo_y = _decimal_tikz(coordenadas[-1][1])
        comandos.append(
            rf"\fill[{cores[cor]},opacity=.13] (0,{primeiro_y}) -- {caminho} -- (0,{ultimo_y}) -- cycle;"
        )
        comandos.append(rf"\draw[{cores[cor]},line width=1.6pt] {caminho};")
        legenda.append({"nome": _escapar_tex(nome), "cor": cores[cor]})
    comandos.append(r"\end{tikzpicture}")
    return "\n".join(comandos), legenda


def _linha_entrada(rotulo: str, valor: Any, unidade: str) -> dict[str, str]:
    """Prepara uma linha segura para a tabela de entradas do memorial."""
    return {
        "rotulo": _escapar_tex(rotulo),
        "valor": _escapar_tex(f"{_numero(valor)} {unidade}".strip()),
    }


def _bloco_calculo(titulo: str, explicacao: str, equacoes: list[str]) -> dict[str, Any]:
    return {
        "titulo": _escapar_tex(titulo),
        "explicacao": _escapar_tex(explicacao),
        "equacoes": equacoes,
    }


def _montar_contexto_balanco(
    entradas: dict[str, Any], resultado: dict[str, Any], nome_projeto: str
) -> dict[str, Any]:
    h = float(entradas["altura_livre_escavacao_m"])
    gamma = float(entradas["peso_especifico_solo_kN_m3"])
    phi = float(entradas["angulo_atrito_solo_graus"])
    percentual_passivo = float(entradas["percentual_passivo_mobilizado"])
    acrescimo = float(entradas["percentual_acrescimo_ficha"])
    ka = float(resultado["coeficiente_ativo_rankine"])
    kp = float(resultado["coeficiente_passivo_rankine"])
    kp_mobilizado = float(resultado["coeficiente_passivo_mobilizado"])
    razao = float(resultado["razao_cubica"])
    ficha = float(resultado["ficha_teorica_m"])
    ficha_preliminar = float(resultado["ficha_preliminar_m"])
    profundidade_ponta = float(resultado["profundidade_ponta_m"])

    equacao_ka = (
        rf"K_a=\frac{{1-\sin\varphi}}{{1+\sin\varphi}}"
        rf"=\frac{{1-\sin({_numero_tex(phi)}^\circ)}}{{1+\sin({_numero_tex(phi)}^\circ)}}"
        rf"={_numero_tex(ka, 4)}"
    )
    equacao_kp = (
        rf"K_p=\frac{{1+\sin\varphi}}{{1-\sin\varphi}}"
        rf"=\frac{{1+\sin({_numero_tex(phi)}^\circ)}}{{1-\sin({_numero_tex(phi)}^\circ)}}"
        rf"={_numero_tex(kp, 4)},\qquad "
        rf"K_{{p,mob}}=K_p\frac{{{_numero_tex(percentual_passivo)}}}{{100}}"
        rf"={_numero_tex(kp_mobilizado, 4)}"
    )
    equacao_razao = (
        rf"r=\left(\frac{{K_a}}{{K_{{p,mob}}}}\right)^{{1/3}}"
        rf"=\left(\frac{{{_numero_tex(ka, 4)}}}{{{_numero_tex(kp_mobilizado, 4)}}}\right)^{{1/3}}"
        rf"={_numero_tex(razao, 4)}"
    )
    equacao_ficha = (
        rf"f=\frac{{rh}}{{1-r}}"
        rf"=\frac{{{_numero_tex(razao, 4)}\times{_numero_tex(h)}}}"
        rf"{{1-{_numero_tex(razao, 4)}}}"
        rf"={_numero_tex(ficha)}\,\mathrm{{m}}"
    )
    equacao_acrescimo = (
        rf"f_{{preliminar}}=f\left(1+\frac{{m_f}}{{100}}\right)"
        rf"={_numero_tex(ficha)}\left(1+\frac{{{_numero_tex(acrescimo)}}}{{100}}\right)"
        rf"={_numero_tex(ficha_preliminar)}\,\mathrm{{m}}"
    )
    empuxo_ativo = float(resultado["empuxo_ativo_kN_m"])
    empuxo_passivo = float(resultado["empuxo_passivo_mobilizado_kN_m"])
    momento_ativo = float(resultado["momento_ativo_sobre_ponta_kNm_m"])
    momento_passivo = float(resultado["momento_passivo_sobre_ponta_kNm_m"])
    residuo = float(resultado["residuo_equilibrio_momentos_kNm_m"])
    equacao_empuxos = (
        rf"E_a=\frac{{K_a\gamma(h+f)^2}}{{2}}"
        rf"=\frac{{{_numero_tex(ka, 4)}\times{_numero_tex(gamma)}"
        rf"\times({_numero_tex(profundidade_ponta)})^2}}{{2}}"
        rf"={_numero_tex(empuxo_ativo)}\,\mathrm{{kN/m}}"
    )
    equacao_empuxo_passivo = (
        rf"E_{{p,mob}}=\frac{{K_{{p,mob}}\gamma f^2}}{{2}}"
        rf"=\frac{{{_numero_tex(kp_mobilizado, 4)}\times{_numero_tex(gamma)}"
        rf"\times({_numero_tex(ficha)})^2}}{{2}}"
        rf"={_numero_tex(empuxo_passivo)}\,\mathrm{{kN/m}}"
    )
    equacao_momentos = (
        rf"M_a=E_a\frac{{h+f}}{{3}}={_numero_tex(momento_ativo)}"
        rf"\quad M_p=E_{{p,mob}}\frac{{f}}{{3}}={_numero_tex(momento_passivo)}"
        rf"\quad M_p-M_a={_numero_tex(residuo, 5)}\,\mathrm{{kN\cdot m/m}}"
    )

    pressao_tikz, legenda_pressao = _tikz_diagrama_pressao(
        resultado, "cortina_em_balanco"
    )
    return {
        "nome_projeto": _escapar_tex(nome_projeto),
        "caso": "Cortina em balanço",
        "subtitulo": "Equilíbrio de momentos de Rankine em solo granular homogêneo",
        "resumo_capa": _escapar_tex(
            f"Ficha teórica {_numero(ficha)} m · ficha preliminar "
            f"{_numero(ficha_preliminar)} m · altura escavada {_numero(h)} m"
        ),
        "destaques": [
            {"rotulo": _escapar_tex("Ficha teórica"), "valor": _escapar_tex(f"{_numero(ficha)} m")},
            {"rotulo": _escapar_tex("Ficha preliminar"), "valor": _escapar_tex(f"{_numero(ficha_preliminar)} m")},
            {"rotulo": _escapar_tex("Resíduo de momentos"), "valor": _escapar_tex(f"{_numero(residuo, 5)} kN·m/m")},
        ],
        "explicacao_modelo": _escapar_tex(
            "O modelo representa uma cortina em balanço sem tirante. O empuxo ativo atua "
            "no trecho retido; o passivo mobilizado atua à frente da ficha. A profundidade "
            "teórica é obtida pelo equilíbrio de momentos em torno da ponta."
        ),
        "interpretacao_resultado": _escapar_tex(
            f"O equilíbrio calculou ficha teórica de {_numero(ficha)} m. "
            f"Com o acréscimo informado, a ficha preliminar é {_numero(ficha_preliminar)} m. "
            "A ficha preliminar é uma estimativa do modelo didático; o relatório não representa "
            "uma verificação completa da segurança ou do dimensionamento da cortina."
        ),
        "entradas": [
            _linha_entrada("Altura livre da escavação, h", h, "m"),
            _linha_entrada("Peso específico do solo, gama", gamma, "kN/m³"),
            _linha_entrada("Ângulo de atrito, phi", phi, "graus"),
            _linha_entrada("Passivo mobilizado", percentual_passivo, "% de Kp"),
            _linha_entrada("Acréscimo prático da ficha", acrescimo, "%"),
        ],
        "croqui_tikz": _tikz_perfil("cortina_em_balanco", entradas, resultado),
        "pressao_tikz": pressao_tikz,
        "legenda_pressao": legenda_pressao,
        "blocos_calculo": [
            _bloco_calculo(
                "1. Coeficientes de empuxo",
                "O ângulo de atrito define os coeficientes ativo e passivo de Rankine. "
                "A fração informada reduz o passivo teórico mobilizado à frente da ficha.",
                [equacao_ka, equacao_kp],
            ),
            _bloco_calculo(
                "2. Ficha teórica e acréscimo prático",
                "O equilíbrio de momentos em torno da ponta fornece a ficha teórica. "
                "O acréscimo prático é aplicado depois e não altera esse equilíbrio.",
                [equacao_razao, equacao_ficha, equacao_acrescimo],
            ),
            _bloco_calculo(
                "3. Conferência do equilíbrio",
                "Os empuxos triangulares são multiplicados pelos braços de seus centroides. "
                "O resíduo próximo de zero confirma o equilíbrio usado para obter a ficha teórica.",
                [equacao_empuxos, equacao_empuxo_passivo, equacao_momentos],
            ),
        ],
        "tabelas": [],
        "avisos": [],
        "hipoteses": [
            "Método de Rankine, terreno horizontal e solo granular homogêneo sem coesão.",
            "O equilíbrio considera a parcela passiva mobilizada indicada pelo usuário.",
            "O acréscimo prático aumenta a ficha preliminar, sem alterar a ficha teórica calculada.",
            "Não são avaliados estabilidade global, deformações, ancoragens ou dimensionamento estrutural.",
        ],
    }


def _montar_contexto_ancorada(
    entradas: dict[str, Any], resultado: dict[str, Any], nome_projeto: str
) -> dict[str, Any]:
    q = float(entradas["sobrecarga_superficie_kPa"])
    h1 = float(entradas["espessura_camada_superior_ate_na_m"])
    gamma1 = float(entradas["peso_especifico_solo_superior_kN_m3"])
    gamma2 = float(entradas["peso_especifico_solo_submerso_kN_m3"])
    profundidade_na_escavacao = float(entradas["profundidade_na_ate_escavacao_m"])
    ficha = float(entradas["ficha_abaixo_escavacao_m"])
    phi = float(entradas["angulo_atrito_solo_graus"])
    altura_ancoragem = float(entradas["altura_ancoragem_acima_na_m"])
    percentual_passivo = float(entradas["percentual_passivo_mobilizado"])
    gamma_agua = float(entradas.get("peso_especifico_agua_kN_m3", 9.81))
    ka = float(resultado["coeficiente_ativo_rankine"])
    kp = float(resultado["coeficiente_passivo_rankine"])
    kp_mobilizado = float(resultado["coeficiente_passivo_mobilizado"])
    profundidade_na_ponta = float(resultado["profundidade_na_ate_ponta_m"])
    profundidade_escavacao = float(resultado["profundidade_escavacao_abaixo_superficie_m"])
    profundidade_ponta = float(resultado["profundidade_ponta_abaixo_superficie_m"])

    pressao_na = float(resultado["pressao_ativa_no_na_kPa"])
    pressao_fundo = float(resultado["pressao_ativa_no_fundo_escavacao_kPa"])
    pressao_ponta = float(resultado["pressao_ativa_na_ponta_kPa"])
    pressao_topo = float(resultado["pressao_ativa_no_topo_kPa"])
    empuxos_ativos = resultado["empuxo_ativo_por_parcela"]
    por_nome = {parcela["parcela"].split(" · ")[0]: parcela for parcela in empuxos_ativos}
    e1 = por_nome["E₁"]["empuxo_kN_m"]
    e2 = por_nome["E₂"]["empuxo_kN_m"]
    e3 = por_nome["E₃"]["empuxo_kN_m"]
    e4 = por_nome["E₄"]["empuxo_kN_m"]
    ew = float(resultado["empuxo_hidrostatico_kN_m"])
    ep_teorico = float(resultado["empuxo_passivo_teorico_kN_m"])
    ep_mobilizado = float(resultado["empuxo_passivo_mobilizado_kN_m"])
    empuxo_ativo_total = float(resultado["empuxo_ativo_total_kN_m"])
    momento_ativo = float(resultado["momento_ativo_resultante_kNm_m"])
    momento_passivo = float(resultado["momento_passivo_resistente_kNm_m"])
    forca_tirante = float(resultado["forca_tirante_kN_m"])
    fs_tombamento = resultado["fator_seguranca_tombamento"]

    equacao_ka = (
        rf"K_a=\frac{{1-\sin({_numero_tex(phi)}^\circ)}}{{1+\sin({_numero_tex(phi)}^\circ)}}"
        rf"={_numero_tex(ka, 4)},\qquad "
        rf"K_p=\frac{{1+\sin({_numero_tex(phi)}^\circ)}}{{1-\sin({_numero_tex(phi)}^\circ)}}"
        rf"={_numero_tex(kp, 4)}"
    )
    equacao_pressao = (
        rf"p_{{a,NA}}=K_a(q+\gamma_1H_1)"
        rf"={_numero_tex(ka, 4)}({_numero_tex(q)}+{_numero_tex(gamma1)}\times{_numero_tex(h1)})"
        rf"={_numero_tex(pressao_na)}\,\mathrm{{kPa}}"
    )
    equacao_pressao_topo = (
        rf"p_{{a,topo}}=K_aq={_numero_tex(ka, 4)}\times{_numero_tex(q)}"
        rf"={_numero_tex(pressao_topo)}\,\mathrm{{kPa}}"
    )
    equacao_pressao_escavacao = (
        rf"p_{{a,esc}}=p_{{a,NA}}+K_a\gamma_2D"
        rf"={_numero_tex(pressao_na)}+{_numero_tex(ka, 4)}\times{_numero_tex(gamma2)}"
        rf"\times{_numero_tex(profundidade_na_escavacao)}"
        rf"={_numero_tex(pressao_fundo)}\,\mathrm{{kPa}}"
    )
    equacao_pressao_ponta = (
        rf"p_{{a,ponta}}=p_{{a,NA}}+K_a\gamma_2(D+f)"
        rf"={_numero_tex(pressao_na)}+{_numero_tex(ka, 4)}\times{_numero_tex(gamma2)}"
        rf"\times{_numero_tex(profundidade_na_ponta)}"
        rf"={_numero_tex(pressao_ponta)}\,\mathrm{{kPa}}"
    )
    equacoes_parcelas = [
        rf"E_1=K_aqH_1={_numero_tex(e1)}\,\mathrm{{kN/m}}",
        rf"E_2=\frac{{K_a\gamma_1H_1^2}}{{2}}={_numero_tex(e2)}\,\mathrm{{kN/m}}",
        rf"E_3=p_{{a,NA}}(D+f)={_numero_tex(e3)}\,\mathrm{{kN/m}}",
        rf"E_4=\frac{{K_a\gamma_2(D+f)^2}}{{2}}={_numero_tex(e4)}\,\mathrm{{kN/m}}",
    ]
    equacao_agua = (
        rf"E_w=\frac{{\gamma_w(D+f)^2}}{{2}}"
        rf"=\frac{{{_numero_tex(gamma_agua)}\times({_numero_tex(profundidade_na_ponta)})^2}}{{2}}"
        rf"={_numero_tex(ew)}\,\mathrm{{kN/m}}"
    )
    equacao_passivo = (
        rf"K_{{p,mob}}=K_p\frac{{{_numero_tex(percentual_passivo)}}}{{100}}"
        rf"={_numero_tex(kp_mobilizado, 4)},\qquad "
        rf"E_{{p,teo}}=\frac{{K_p\gamma_2f^2}}{{2}}={_numero_tex(ep_teorico)}"
        rf"\,\mathrm{{kN/m}},\quad E_{{p,mob}}={_numero_tex(ep_mobilizado)}\,\mathrm{{kN/m}}"
    )
    equacao_tirante = (
        rf"T=E_a+E_w-E_{{p,mob}}"
        rf"={_numero_tex(empuxo_ativo_total)}+{_numero_tex(ew)}-{_numero_tex(ep_mobilizado)}"
        rf"={_numero_tex(forca_tirante)}\,\mathrm{{kN/m}}"
    )
    equacao_fs = (
        rf"FS_{{tombamento}}=\frac{{M_p}}{{M_a}}"
        rf"=\frac{{{_numero_tex(momento_passivo)}}}{{{_numero_tex(momento_ativo)}}}"
        rf"={_numero_tex(fs_tombamento, 3)}"
    )

    linhas_tabela = []
    for parcela in empuxos_ativos:
        nome_parcela = parcela["parcela"].replace("E₁", "E1").replace("E₂", "E2").replace("E₃", "E3").replace("E₄", "E4")
        linhas_tabela.append([
            _escapar_tex(nome_parcela),
            _numero(parcela["empuxo_kN_m"]),
            _numero(parcela["braco_assinado_m"]),
            _numero(parcela["momento_assinado_kNm_m"]),
        ])
    linhas_tabela.extend([
        ["Empuxo ativo total do solo", _numero(empuxo_ativo_total), "--", _numero(resultado["momento_ativo_solo_kNm_m"])],
        ["Água diferencial", _numero(ew), _numero(resultado["braco_hidrostatico_m"]), _numero(resultado["momento_hidrostatico_kNm_m"])],
        ["Solo e água · resultante atuante", _numero(empuxo_ativo_total + ew), "--", _numero(momento_ativo)],
        ["Passivo mobilizado", _numero(ep_mobilizado), _numero(resultado["braco_passivo_em_relacao_ancoragem_m"]), _numero(momento_passivo)],
    ])

    status = str(resultado["status_tombamento"])
    fs_minimo = float(entradas["fator_seguranca_minimo_tombamento"])
    pressao_tikz, legenda_pressao = _tikz_diagrama_pressao(
        resultado, "cortina_ancorada"
    )
    destaques = [
        {"rotulo": _escapar_tex("Força no tirante"), "valor": _escapar_tex(f"{_numero(forca_tirante)} kN/m")},
        {"rotulo": _escapar_tex("FS ao tombamento"), "valor": _escapar_tex(f"{_numero(fs_tombamento, 3)} · {status}")},
        {"rotulo": _escapar_tex("Passivo mobilizado"), "valor": _escapar_tex(f"{_numero(ep_mobilizado)} kN/m")},
    ]
    return {
        "nome_projeto": _escapar_tex(nome_projeto),
        "caso": "Cortina ancorada",
        "subtitulo": "Empuxos, equilíbrio do tirante e verificação simplificada ao tombamento",
        "resumo_capa": _escapar_tex(
            f"Força no tirante {_numero(forca_tirante)} kN/m · "
            f"FS ao tombamento {_numero(fs_tombamento, 3)} · {status}"
        ),
        "destaques": destaques,
        "explicacao_modelo": _escapar_tex(
            "A cortina é analisada com camada superior até o nível d’água e solo submerso "
            "abaixo dele. O equilíbrio de momentos é escrito em relação à ancoragem; o lado "
            "escavado é considerado drenado para calcular a pressão hidrostática diferencial."
        ),
        "interpretacao_resultado": _escapar_tex(
            f"A força calculada no tirante é {_numero(forca_tirante)} kN/m. "
            f"O fator de segurança ao tombamento é {_numero(fs_tombamento, 3)}, "
            f"comparado ao mínimo informado de {_numero(fs_minimo)}. "
            "A condição indicada considera apenas o equilíbrio simplificado deste modelo."
        ),
        "entradas": [
            _linha_entrada("Sobrecarga na superfície, q", q, "kPa"),
            _linha_entrada("Espessura da camada superior até o N.A., H1", h1, "m"),
            _linha_entrada("Peso específico acima do N.A., gamma1", gamma1, "kN/m³"),
            _linha_entrada("Peso específico submerso, gamma2", gamma2, "kN/m³"),
            _linha_entrada("Profundidade do N.A. até a escavação, D", profundidade_na_escavacao, "m"),
            _linha_entrada("Ficha abaixo da escavação, f", ficha, "m"),
            _linha_entrada("Ângulo de atrito, phi", phi, "graus"),
            _linha_entrada("Altura da ancoragem acima do N.A., ha", altura_ancoragem, "m"),
            _linha_entrada("Passivo mobilizado", percentual_passivo, "% de Kp"),
            _linha_entrada("Peso específico da água, gamma w", gamma_agua, "kN/m³"),
            _linha_entrada("FS mínimo ao tombamento", entradas["fator_seguranca_minimo_tombamento"], ""),
        ],
        "croqui_tikz": _tikz_perfil("cortina_ancorada", entradas, resultado),
        "pressao_tikz": pressao_tikz,
        "legenda_pressao": legenda_pressao,
        "blocos_calculo": [
            _bloco_calculo(
                "1. Coeficientes e pressões ativas",
                "O modelo usa Rankine e divide o perfil no nível d’água. Acima dele usa gamma1; abaixo, gamma2 já representa o peso específico submerso.",
                [equacao_ka, equacao_pressao_topo, equacao_pressao, equacao_pressao_escavacao, equacao_pressao_ponta],
            ),
            _bloco_calculo(
                "2. Empuxos do solo e da água",
                "As áreas dos diagramas de pressão fornecem os empuxos. O braço de cada parcela é medido em relação à ancoragem; os sinais das parcelas acima e abaixo dela são mantidos na soma.",
                [*equacoes_parcelas, equacao_agua, equacao_passivo],
            ),
            _bloco_calculo(
                "3. Tirante e fator de segurança",
                "A força no tirante fecha o equilíbrio horizontal simplificado. O fator ao tombamento compara o momento resistente do passivo mobilizado com o momento atuante do solo e da água.",
                [equacao_tirante, equacao_fs],
            ),
        ],
        "tabelas": [{
            "titulo": _escapar_tex("Empuxos e momentos considerados"),
            "colunas": [_escapar_tex(texto) for texto in ("Parcela", "Empuxo (kN/m)", "Braço (m)", "Momento (kN·m/m)")],
            "formato": "Xrrr",
            "linhas": linhas_tabela,
        }],
        "avisos": [_escapar_tex(aviso) for aviso in resultado.get("avisos", [])],
        "status": _escapar_tex(status),
        "hipoteses": [
            "Método de Rankine, superfície horizontal e solo sem coesão; phi é igual nas duas camadas.",
            "A camada superior termina no nível d’água; gamma2 é o peso específico submerso abaixo dele.",
            "A pressão hidrostática diferencial considera o lado escavado drenado.",
            "O passivo é reduzido pela porcentagem mobilizada informada pelo usuário.",
            "Não são avaliados estabilidade global, deformações, dimensionamento do tirante ou dimensionamento estrutural da cortina.",
        ],
    }


def montar_relatorio_estaca_prancha_tex(
    entradas: dict[str, Any],
    resultado: dict[str, Any],
    tipo_cortina: str,
    nome_projeto: str | None = None,
) -> str:
    """Monta a fonte TeX para um dos dois casos calculados pela pagina."""
    if tipo_cortina == "cortina_em_balanco":
        nome_padrao = "Estudo de cortina em balanço"
        contexto = _montar_contexto_balanco(
            entradas, resultado, nome_projeto or nome_padrao
        )
    elif tipo_cortina == "cortina_ancorada":
        nome_padrao = "Estudo de cortina ancorada"
        contexto = _montar_contexto_ancorada(
            entradas, resultado, nome_projeto or nome_padrao
        )
    else:
        raise ValueError(f"Tipo de cortina desconhecido: {tipo_cortina}")

    ambiente = Environment(
        loader=FileSystemLoader(_DIRETORIO_TEMPLATES),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    contexto["data_relatorio"] = r"\today"
    return ambiente.get_template(_NOME_TEMPLATE).render(**contexto)


def compilar_relatorio_estaca_prancha_pdf(
    codigo_tex: str, timeout_s: int = 90
) -> bytes:
    """Compila a fonte TeX em PDF sem shell escape e em pasta temporaria."""
    compiladores = [
        (nome, shutil.which(nome))
        for nome in ("pdflatex", "lualatex", "tectonic")
    ]
    compiladores = [(nome, caminho) for nome, caminho in compiladores if caminho]
    if not compiladores:
        raise ErroGeracaoRelatorioEstacaPrancha(
            "Nenhum compilador LaTeX (pdflatex, lualatex ou Tectonic) está instalado. "
            "A fonte .tex pode ser baixada e compilada no MiKTeX ou TeX Live."
        )

    with tempfile.TemporaryDirectory(prefix="relatorio-estaca-prancha-") as diretorio_temp:
        pasta_temp = Path(diretorio_temp)
        arquivo_tex = pasta_temp / "relatorio_estaca_prancha.tex"
        arquivo_pdf = pasta_temp / "relatorio_estaca_prancha.pdf"
        arquivo_tex.write_text(codigo_tex, encoding="utf-8")
        erros_compilacao = []
        for nome, executavel in compiladores:
            if nome == "tectonic":
                comando = [executavel, "--keep-logs", "--reruns", "1", "--outdir", str(pasta_temp), arquivo_tex.name]
                passadas = 1
            else:
                comando = [executavel, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", arquivo_tex.name]
                passadas = 2
            log_final = ""
            sucesso = True
            for _ in range(passadas):
                try:
                    processo = subprocess.run(
                        comando,
                        cwd=pasta_temp,
                        capture_output=True,
                        stdin=subprocess.DEVNULL,
                        text=True,
                        timeout=timeout_s,
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    sucesso = False
                    log_final = f"Tempo limite de {timeout_s} s excedido no compilador {nome}."
                    break
                log_final = (processo.stdout + "\n" + processo.stderr)[-12000:]
                if processo.returncode != 0:
                    sucesso = False
                    break
            if sucesso and arquivo_pdf.is_file():
                return arquivo_pdf.read_bytes()
            erros_compilacao.append(
                f"--- {nome} ---\n" + "\n".join(log_final.splitlines()[-28:])
            )
        raise ErroGeracaoRelatorioEstacaPrancha(
            "A compilação do relatório falhou nos motores LaTeX disponíveis. "
            "A fonte .tex continua disponível para compilação manual.\n"
            + "\n".join(erros_compilacao)
        )
