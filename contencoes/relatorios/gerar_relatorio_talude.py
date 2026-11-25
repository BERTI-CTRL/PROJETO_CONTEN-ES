"""Monta um memorial didático LaTeX/PDF para estabilidade de taludes.

Os valores apresentados vêm das entradas e dos resultados já calculados pela
página. O módulo só organiza, explica e desenha esses dados; não recalcula FS.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


DIRETORIO_TEMPLATES = Path(__file__).parent / "templates"
NOME_TEMPLATE = "talude.tex.j2"


class ErroGeracaoRelatorioTalude(RuntimeError):
    """Erro legível quando não há compilador ou a compilação LaTeX falha."""


def _formatar_numero(valor: float | int | None, casas: int = 2) -> str:
    """Formata números em português, sem tentar recalcular os resultados."""
    if valor is None:
        return "--"
    texto = f"{float(valor):,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _formatar_numero_tex(valor: float | int | None, casas: int = 2) -> str:
    """Usa vírgula decimal dentro de expressões LaTeX."""
    if valor is None:
        return r"\text{--}"
    return f"{float(valor):.{casas}f}".replace(".", r"{,}")


def _decimal_tikz(valor: float) -> str:
    """TikZ usa ponto decimal nas coordenadas, independente do idioma do PDF."""
    return f"{float(valor):.5f}"


def _escapar_tex(texto: Any) -> str:
    """Escapa texto de interface para que não seja interpretado como comando LaTeX."""
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
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }
    return "".join(substituicoes.get(caractere, caractere) for caractere in str(texto))


def _estado_curto(estado: Any) -> str:
    """Encurta o diagnóstico para caber nas tabelas comparativas."""
    texto = str(estado)
    if texto == "VÁLIDO":
        return "Válido"
    if "N′ < 0" in texto:
        return "Normal efetiva negativa"
    if texto == "FORA DO MACIÇO":
        return "Fora do maciço"
    if "Fmob" in texto:
        return "Força mobilizada não positiva"
    return texto


def _estado_legivel(estado: Any) -> str:
    """Troca símbolos Unicode de diagnóstico por texto que compila em pdfLaTeX."""
    texto = str(estado)
    return texto.replace("N′ < 0", "normal efetiva negativa").replace(
        "Fmob ≤ 0", "força mobilizada não positiva"
    )


def _pontos_cota_terreno(
    entradas: dict[str, Any], x_inicial: float, x_final: float, quantidade: int = 30
) -> list[tuple[float, float]]:
    """Amostra o perfil por trechos: terreno plano, face e terreno a montante."""
    altura = float(entradas["altura_talude_m"])
    relacao_face = float(entradas["relacao_horizontal_vertical_face"])
    fim_face = altura * relacao_face
    inclinacao = float(entradas["inclinacao_terreno_montante_graus"])
    pontos_x = {
        x_inicial,
        x_final,
        0.0,
        fim_face,
        fim_face + float(entradas["distancia_crista_entrada_m"]),
    }
    pontos_x.update(
        x_inicial + (x_final - x_inicial) * indice / quantidade
        for indice in range(quantidade + 1)
    )
    pontos_ordenados = sorted(x for x in pontos_x if x_inicial <= x <= x_final)
    pontos: list[tuple[float, float]] = []
    for x in pontos_ordenados:
        if x <= 0:
            y = 0.0
        elif x <= fim_face:
            y = x / relacao_face
        else:
            y = altura + (x - fim_face) * math.tan(math.radians(inclinacao))
        pontos.append((x, y))
    return pontos


def _gerar_croqui_tikz(
    entradas: dict[str, Any], resultado: dict[str, Any], circulo: dict[str, Any] | None
) -> str:
    """Desenha a seção cotada com camadas, água, círculo e fatias selecionadas."""
    altura = float(entradas["altura_talude_m"])
    geometria = resultado["geometria"]
    fim_face = float(geometria["comprimento_horizontal_face_m"])
    x_entrada = float(geometria["coordenada_x_entrada_m"])
    x_saida = -float(entradas["distancia_pe_saida_m"])
    tem_centro_circular = bool(
        circulo
        and circulo.get("centro_x_m") is not None
        and circulo.get("centro_y_m") is not None
    )
    centro_x = float(circulo["centro_x_m"]) if tem_centro_circular else 0.0
    centro_y = float(circulo["centro_y_m"]) if tem_centro_circular else 0.0
    raio = float(circulo["raio_m"]) if tem_centro_circular else 0.0

    x_minimo = min(x_saida, -0.3 * altura, centro_x - raio if tem_centro_circular else 0.0) - 0.6
    x_maximo = max(x_entrada + 0.5 * altura, centro_x + raio if tem_centro_circular else 0.0) + 0.6
    if tem_centro_circular:
        x_minimo = min(x_minimo, float(circulo["x_saida_m"]) - 0.6)
        x_maximo = max(x_maximo, float(circulo["x_entrada_m"]) + 0.6)
    y_minimo = -0.5 * altura
    if tem_centro_circular:
        y_minimo = min(y_minimo, centro_y - raio - 0.7)
    y_maximo = max(altura, float(geometria["cota_entrada_m"])) + 0.9
    escala = min(0.72, 13.2 / max(x_maximo - x_minimo, 1.0), 8.3 / max(y_maximo - y_minimo, 1.0))

    linhas = [
        rf"\begin{{tikzpicture}}[x={_decimal_tikz(escala)}cm,y={_decimal_tikz(escala)}cm,>=Stealth, every node/.style={{font=\scriptsize}}]",
        rf"\path[use as bounding box] ({_decimal_tikz(x_minimo)},{_decimal_tikz(y_minimo)}) rectangle ({_decimal_tikz(x_maximo)},{_decimal_tikz(y_maximo)});",
    ]

    # Preenchimento em partes evita a necessidade de adivinhar uma seção retangular.
    pontos_face = _pontos_cota_terreno(entradas, x_minimo, x_maximo)
    base = y_minimo
    solo_poligono = " -- ".join(
        f"({_decimal_tikz(x)},{_decimal_tikz(y)})" for x, y in pontos_face
    )
    linhas.append(
        rf"\fill[areia] ({_decimal_tikz(x_minimo)},{_decimal_tikz(base)}) -- {solo_poligono} -- ({_decimal_tikz(x_maximo)},{_decimal_tikz(base)}) -- cycle;"
    )

    # Destaca a massa deslizante e a superfície circular usada nas fatias.
    if tem_centro_circular and circulo.get("fatias"):
        x_arco_inicio = float(circulo["x_saida_m"])
        x_arco_fim = float(circulo["x_entrada_m"])
        topo_massa = _pontos_cota_terreno(entradas, x_arco_inicio, x_arco_fim, 38)
        pontos_arco = []
        for indice in range(41, -1, -1):
            x = x_arco_inicio + (x_arco_fim - x_arco_inicio) * indice / 41
            y = centro_y - math.sqrt(max(0.0, raio**2 - (x - centro_x) ** 2))
            pontos_arco.append((x, y))
        massa = " -- ".join(
            f"({_decimal_tikz(x)},{_decimal_tikz(y)})" for x, y in topo_massa + pontos_arco
        )
        linhas.append(rf"\fill[laranja,opacity=.24] {massa} -- cycle;")

    # Interface entre solos e linha do nível d'água são cotadas no mesmo perfil.
    cota_interface = float(geometria["cota_interface_camadas_m"])
    linhas.extend([
        rf"\draw[densely dashed,corinterface] ({_decimal_tikz(x_minimo)},{_decimal_tikz(cota_interface)}) -- ({_decimal_tikz(x_maximo)},{_decimal_tikz(cota_interface)}) node[pos=.82,above,fill=white,inner sep=1pt] {{Interface das camadas}};",
    ])
    cota_agua = geometria["cota_nivel_agua_m"]
    if cota_agua is not None:
        linhas.append(
            rf"\draw[dash dot,azulagua,thick] ({_decimal_tikz(x_minimo)},{_decimal_tikz(float(cota_agua))}) -- ({_decimal_tikz(x_maximo)},{_decimal_tikz(float(cota_agua))}) node[pos=.18,above,fill=white,inner sep=1pt] {{$N.A.={_formatar_numero_tex(float(cota_agua))}\,\mathrm{{m}}$}};"
        )

    linhas.extend([
        rf"\draw[very thick,verde] ({_decimal_tikz(x_minimo)},0) -- (0,0) -- ({_decimal_tikz(fim_face)},{_decimal_tikz(altura)}) -- ({_decimal_tikz(x_maximo)},{_decimal_tikz(float(geometria['cota_entrada_m']) + (x_maximo - x_entrada) * math.tan(math.radians(float(entradas['inclinacao_terreno_montante_graus']))) if x_maximo > x_entrada else float(geometria['cota_entrada_m']))});",
        rf"\draw[<->,thick] (-.38,0) -- (-.38,{_decimal_tikz(altura)}) node[midway,left,fill=white,inner sep=1pt] {{$H={_formatar_numero_tex(altura)}\,\mathrm{{m}}$}};",
        rf"\draw[<->,thick] (0,-.22) -- ({_decimal_tikz(fim_face)},-.22) node[midway,below,fill=white,inner sep=1pt] {{$H:V={_formatar_numero_tex(float(entradas['relacao_horizontal_vertical_face']))}:1$}};",
        rf"\fill[verde] (0,0) circle (1.2pt) node[below left] {{Pé}};",
        rf"\fill[verde] ({_decimal_tikz(fim_face)},{_decimal_tikz(altura)}) circle (1.2pt) node[above left] {{Crista}};",
        rf"\fill[azul] ({_decimal_tikz(x_entrada)},{_decimal_tikz(float(geometria['cota_entrada_m']))}) circle (1.2pt) node[above right,fill=white,inner sep=1pt] {{$E=({_formatar_numero_tex(x_entrada)}; {_formatar_numero_tex(float(geometria['cota_entrada_m']))})$}};",
    ])

    sobrecarga = float(entradas["sobrecarga_crista_kPa"])
    if sobrecarga > 0 and x_entrada > fim_face:
        for indice in range(5):
            x = fim_face + (x_entrada - fim_face) * (indice + 0.5) / 5
            y = float(geometria["cota_entrada_m"]) + (x - x_entrada) * math.tan(
                math.radians(float(entradas["inclinacao_terreno_montante_graus"]))
            )
            linhas.append(
                rf"\draw[->,orange!85!black,thick] ({_decimal_tikz(x)},{_decimal_tikz(y + .6)}) -- ({_decimal_tikz(x)},{_decimal_tikz(y + .08)});"
            )
        linhas.append(
            rf"\node[above,orange!80!black] at ({_decimal_tikz((fim_face + x_entrada) / 2)},{_decimal_tikz(float(geometria['cota_entrada_m']) + .62)}) {{$q={_formatar_numero_tex(sobrecarga)}\,\mathrm{{kPa}}$}};"
        )

    if tem_centro_circular:
        x_inicio = float(circulo["x_saida_m"])
        x_fim = float(circulo["x_entrada_m"])
        pontos_arco = []
        for indice in range(61):
            x = x_inicio + (x_fim - x_inicio) * indice / 60
            y = centro_y - math.sqrt(max(0.0, raio**2 - (x - centro_x) ** 2))
            pontos_arco.append((x, y))
        caminho_arco = " -- ".join(
            f"({_decimal_tikz(x)},{_decimal_tikz(y)})" for x, y in pontos_arco
        )
        linhas.extend([
            rf"\draw[red!75!black,very thick] {caminho_arco};",
            rf"\fill[red!75!black] ({_decimal_tikz(centro_x)},{_decimal_tikz(centro_y)}) circle (1.5pt) node[above right,fill=white,inner sep=1pt] {{$C=({_formatar_numero_tex(centro_x)}; {_formatar_numero_tex(centro_y)})$}};",
            rf"\draw[<->,red!75!black] ({_decimal_tikz(centro_x)},{_decimal_tikz(centro_y)}) -- ({_decimal_tikz(x_inicio)},{_decimal_tikz(centro_y - math.sqrt(max(0.0, raio**2 - (x_inicio - centro_x) ** 2)))}) node[midway,above,fill=white,inner sep=1pt] {{$R={_formatar_numero_tex(raio)}\,\mathrm{{m}}$}};",
        ])
        for fatia in circulo.get("fatias", []):
            x1 = float(fatia["x_inicial_m"])
            x2 = float(fatia["x_final_m"])
            if fatia.get("cota_base_inicial_m") is not None:
                linhas.append(
                    rf"\draw[gray!65] ({_decimal_tikz(x1)},{_decimal_tikz(float(fatia['cota_topo_inicial_m']))}) -- ({_decimal_tikz(x1)},{_decimal_tikz(float(fatia['cota_base_inicial_m']))});"
                )
            if fatia.get("cota_base_final_m") is not None:
                linhas.append(
                    rf"\draw[gray!65] ({_decimal_tikz(x2)},{_decimal_tikz(float(fatia['cota_topo_final_m']))}) -- ({_decimal_tikz(x2)},{_decimal_tikz(float(fatia['cota_base_final_m']))});"
                )
        linhas.extend([
            rf"\draw[<->,blue!75!black] ({_decimal_tikz(x_saida)},-.62) -- ({_decimal_tikz(x_entrada)},-.62) node[midway,below,fill=white,inner sep=1pt] {{$d={_formatar_numero_tex(float(geometria['distancia_entre_entrada_e_saida_m']))}\,\mathrm{{m}}$}};",
            rf"\node[below left,red!75!black,fill=white,inner sep=1pt] at ({_decimal_tikz(x_inicio)},{_decimal_tikz(float(circulo['fatias'][0]['cota_base_inicial_m']) if circulo.get('fatias') and circulo['fatias'][0].get('cota_base_inicial_m') is not None else 0.0)}) {{$S$}};",
        ])
    linhas.append(r"\end{tikzpicture}")
    return "\n".join(linhas)


def _gerar_grafico_fs_tikz(circulos: list[dict[str, Any]]) -> str:
    """Compara os dois métodos sem uma dependência gráfica adicional no PDF."""
    valores = [
        float(valor)
        for circulo in circulos
        for valor in (circulo.get("fator_seguranca"), circulo.get("bishop", {}).get("fator_seguranca"))
        if valor is not None
    ]
    limite = max(valores, default=1.0) * 1.12
    largura = 9.0
    escala = largura / limite
    linhas = [
        r"\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth,every node/.style={font=\scriptsize}]",
        rf"\draw[->] (0,0) -- ({_decimal_tikz(largura + 2.0)},0) node[right] {{$FS$}};",
    ]
    for indice in range(1, 6):
        valor = limite * indice / 5
        x = valor * escala
        linhas.extend([
            rf"\draw[gray!25] ({_decimal_tikz(x)},.12) -- ({_decimal_tikz(x)},{_decimal_tikz(len(circulos) * .53 + .35)});",
            rf"\node[below] at ({_decimal_tikz(x)},0) {{{_formatar_numero_tex(valor, 1)}}};",
        ])
    for indice, circulo in enumerate(circulos):
        y = (len(circulos) - indice - 1) * .53 + .16
        identificacao = _escapar_tex(circulo["identificacao"])
        linhas.append(rf"\node[anchor=east] at (-.12,{_decimal_tikz(y + .12)}) {{{identificacao}}};")
        for deslocamento, chave, cor, sigla in (
            (0.04, "fator_seguranca", "verde", "Fellenius"),
            (0.22, None, "azul", "Bishop"),
        ):
            valor = (
                circulo.get(chave)
                if chave
                else circulo.get("bishop", {}).get("fator_seguranca")
            )
            y_barra = y + deslocamento
            if valor is None:
                linhas.append(rf"\node[anchor=west,text=gray] at (.08,{_decimal_tikz(y_barra + .05)}) {{-- {sigla}}};")
                continue
            x_fim = float(valor) * escala
            linhas.extend([
                rf"\fill[{cor},opacity=.82] (0,{_decimal_tikz(y_barra)}) rectangle ({_decimal_tikz(x_fim)},{_decimal_tikz(y_barra + .12)});",
                rf"\node[anchor=west] at ({_decimal_tikz(x_fim + .08)},{_decimal_tikz(y_barra + .06)}) {{{_formatar_numero_tex(float(valor), 3)}}};",
            ])
    linhas.extend([
        r"\fill[verde] (0,-.82) rectangle (.24,-.68);",
        r"\node[anchor=west] at (.32,-.75) {Fellenius};",
        r"\fill[azul] (2.1,-.82) rectangle (2.34,-.68);",
        r"\node[anchor=west] at (2.42,-.75) {Bishop Simplificado};",
    ])
    linhas.append(r"\end{tikzpicture}")
    return "\n".join(linhas)


def _montar_tabelas_fatias(fatias: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    """Divide o quadro extenso em geometria/pesos e equilíbrio por fatia."""
    tabelas = {"geometria": [], "equilibrio": []}
    for fatia in fatias:
        numero = fatia["numero_fatia"]
        tabelas["geometria"].append({
            "numero": str(numero),
            "x_inicial": _formatar_numero(fatia.get("x_inicial_m")),
            "x_final": _formatar_numero(fatia.get("x_final_m")),
            "base_m": _formatar_numero(fatia.get("cota_base_m")),
            "alpha": _formatar_numero(fatia.get("angulo_base_medio_graus")),
            "arco": _formatar_numero(fatia.get("comprimento_arco_m")),
            "area_sup": _formatar_numero(
                sum(float(fatia.get(chave, 0.0) or 0.0) for chave in (
                    "area_camada_superior_nao_saturada_m2",
                    "area_camada_superior_saturada_m2",
                )),
                3,
            ),
            "area_inf": _formatar_numero(
                sum(float(fatia.get(chave, 0.0) or 0.0) for chave in (
                    "area_camada_inferior_nao_saturada_m2",
                    "area_camada_inferior_saturada_m2",
                )),
                3,
            ),
            "peso": _formatar_numero(fatia.get("peso_fatia_kN_m")),
            "sobrecarga": _formatar_numero(fatia.get("sobrecarga_fatia_kN_m")),
        })
        tabelas["equilibrio"].append({
            "numero": str(numero),
            "normal": _formatar_numero(fatia.get("forca_normal_total_kN_m")),
            "agua": _formatar_numero(fatia.get("resultante_pressao_neutra_kN_m")),
            "normal_efetiva": _formatar_numero(fatia.get("forca_normal_efetiva_kN_m")),
            "coesao": _formatar_numero(fatia.get("forca_resistente_coesao_kN_m")),
            "atrito": _formatar_numero(fatia.get("forca_resistente_atrito_kN_m")),
            "resistencia": _formatar_numero(fatia.get("forca_resistente_kN_m")),
            "mobilizada": _formatar_numero(fatia.get("forca_mobilizada_kN_m")),
            "situacao": _escapar_tex(fatia.get("situacao", "--")),
        })
    return tabelas


def montar_relatorio_talude_tex(
    entradas_talude: dict[str, Any],
    resultado_talude: dict[str, Any],
    circulo_selecionado: dict[str, Any] | None,
    nome_projeto: str = "Estudo de estabilidade de talude",
) -> str:
    """Renderiza o fonte TeX autocontido a partir dos valores já calculados."""
    geometria = resultado_talude["geometria"]
    circulos_contexto = []
    for circulo in resultado_talude["circulos"]:
        circulos_contexto.append({
            "identificacao": _escapar_tex(circulo["identificacao"]),
            "raio": _formatar_numero(circulo.get("raio_m")),
            "centro_x": _formatar_numero(circulo.get("centro_x_m")),
            "centro_y": _formatar_numero(circulo.get("centro_y_m")),
            "fs_fellenius": _formatar_numero(circulo.get("fator_seguranca"), 3),
            "fs_bishop": _formatar_numero(circulo.get("bishop", {}).get("fator_seguranca"), 3),
            "situacao_fellenius": _escapar_tex(_estado_curto(circulo.get("situacao", "-"))),
            "situacao_bishop": _escapar_tex(_estado_curto(circulo.get("bishop", {}).get("situacao", "-"))),
        })

    critico_fellenius = resultado_talude.get("circulo_critico")
    critico_bishop = resultado_talude.get("circulo_critico_bishop")
    busca_centros = resultado_talude.get("busca_centros") or {}
    critico_malha = busca_centros.get("circulo_critico")
    selecionado = circulo_selecionado
    bishop = selecionado.get("bishop", {}) if selecionado else {}
    fatias = selecionado.get("fatias", []) if selecionado else []
    soma_resistente = selecionado.get("resistencia_total_kN_m") if selecionado else None
    soma_mobilizada = selecionado.get("forca_mobilizada_total_kN_m") if selecionado else None
    tabelas_fatias = _montar_tabelas_fatias(fatias)

    contexto = {
        "circulo_selecionado": selecionado is not None,
        "nome_projeto": _escapar_tex(nome_projeto),
        "data_relatorio": r"\today",
        "entradas": {
            "altura": _formatar_numero(entradas_talude["altura_talude_m"]),
            "relacao_face": _formatar_numero(entradas_talude["relacao_horizontal_vertical_face"]),
            "beta": _formatar_numero(entradas_talude["inclinacao_terreno_montante_graus"]),
            "distancia_entrada": _formatar_numero(entradas_talude["distancia_crista_entrada_m"]),
            "espessura_superior": _formatar_numero(entradas_talude["espessura_camada_superior_m"]),
            "z_na": _formatar_numero(entradas_talude.get("profundidade_nivel_agua_abaixo_crista_m")),
            "gamma_agua": _formatar_numero(entradas_talude["peso_especifico_agua_kN_m3"]),
            "sobrecarga": _formatar_numero(entradas_talude["sobrecarga_crista_kPa"]),
            "fatias": int(entradas_talude["quantidade_fatias"]),
            "distancia_saida": _formatar_numero(entradas_talude["distancia_pe_saida_m"]),
        },
        "camadas": [
            {
                "numero": indice,
                "gamma_nat": _formatar_numero(entradas_talude[f"peso_especifico_natural_camada_{nome}_kN_m3"]),
                "gamma_sat": _formatar_numero(entradas_talude[f"peso_especifico_saturado_camada_{nome}_kN_m3"]),
                "coesao": _formatar_numero(entradas_talude[f"coesao_efetiva_camada_{nome}_kPa"]),
                "phi": _formatar_numero(entradas_talude[f"angulo_atrito_efetivo_camada_{nome}_graus"]),
            }
            for indice, nome in ((1, "superior"), (2, "inferior"))
        ],
        "geometria": {
            "cota_interface": _formatar_numero(geometria["cota_interface_camadas_m"]),
            "x_entrada": _formatar_numero(geometria["coordenada_x_entrada_m"]),
            "y_entrada": _formatar_numero(geometria["cota_entrada_m"]),
            "distancia": _formatar_numero(geometria["distancia_entre_entrada_e_saida_m"]),
            "inclinacao_face": _formatar_numero(geometria["inclinacao_face_graus"]),
            "cota_agua": _formatar_numero(geometria["cota_nivel_agua_m"]),
        },
        "circulos": circulos_contexto,
        "critico_fellenius": critico_fellenius,
        "critico_bishop": critico_bishop,
        "critico_malha": critico_malha,
        "pontos_malha": busca_centros.get("quantidade_pontos_por_eixo"),
        "selecionado": {
            "identificacao": _escapar_tex(selecionado["identificacao"]) if selecionado else "Nenhum círculo selecionado",
            "situacao": _escapar_tex(_estado_legivel(selecionado["situacao"])) if selecionado else "Não há candidato selecionado",
            "raio": _formatar_numero(selecionado.get("raio_m")) if selecionado else "--",
            "centro_x": _formatar_numero(selecionado.get("centro_x_m")) if selecionado else "--",
            "centro_y": _formatar_numero(selecionado.get("centro_y_m")) if selecionado else "--",
            "fs": _formatar_numero(selecionado.get("fator_seguranca"), 3) if selecionado else "--",
            "resistencia": _formatar_numero(soma_resistente),
            "mobilizada": _formatar_numero(soma_mobilizada),
            "bishop_fs": _formatar_numero(bishop.get("fator_seguranca"), 3),
            "bishop_estado": _escapar_tex(bishop.get("situacao", "Não calculado")),
        },
        "bishop_historico": [
            {
                "iteracao": linha["iteracao"],
                "fs": _formatar_numero(linha["fs"], 5),
                "residuo": _formatar_numero(linha["residuo"], 6),
            }
            for linha in bishop.get("historico", [])
        ],
        "tabelas_fatias": tabelas_fatias,
        "numero_fatias": len(fatias),
        "croqui_tikz": _gerar_croqui_tikz(entradas_talude, resultado_talude, selecionado),
        "grafico_fs_tikz": _gerar_grafico_fs_tikz(resultado_talude["circulos"]),
    }
    ambiente = Environment(
        loader=FileSystemLoader(DIRETORIO_TEMPLATES),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return ambiente.get_template(NOME_TEMPLATE).render(**contexto)


def compilar_relatorio_talude_pdf(codigo_tex: str, timeout_s: int = 90) -> bytes:
    """Compila o relatório sem shell escape, em diretório temporário isolado."""
    compiladores = [
        (nome, shutil.which(nome))
        for nome in ("pdflatex", "lualatex", "tectonic")
    ]
    compiladores = [(nome, caminho) for nome, caminho in compiladores if caminho]
    if not compiladores:
        raise ErroGeracaoRelatorioTalude(
            "Nenhum compilador LaTeX (pdflatex, lualatex ou Tectonic) está instalado. "
            "A fonte .tex pode ser baixada e compilada no MiKTeX ou TeX Live."
        )

    with tempfile.TemporaryDirectory(prefix="relatorio-talude-") as diretorio_temp:
        pasta_temp = Path(diretorio_temp)
        arquivo_tex = pasta_temp / "relatorio_talude.tex"
        arquivo_pdf = pasta_temp / "relatorio_talude.pdf"
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
        raise ErroGeracaoRelatorioTalude(
            "A compilação do PDF falhou nos motores LaTeX disponíveis. "
            "A fonte .tex continua disponível para compilação manual.\n"
            + "\n".join(erros_compilacao)
        )

