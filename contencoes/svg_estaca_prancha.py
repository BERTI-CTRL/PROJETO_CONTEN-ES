from __future__ import annotations

from html import escape
from math import ceil
from typing import Any


def _formatar_numero(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _svg_texto(
    x: float,
    y: float,
    texto: str,
    *,
    tamanho: int = 16,
    peso: int = 400,
    ancora: str = "start",
    cor: str = "#26383f",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{ancora}" '
        f'font-family="sans-serif" font-size="{tamanho}" font-weight="{peso}" '
        f'fill="{cor}">{escape(texto)}</text>'
    )


def _svg_linha(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    cor: str = "#46565d",
    largura: float = 2,
    tracejado: str | None = None,
) -> str:
    tracejado_svg = f' stroke-dasharray="{tracejado}"' if tracejado else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{cor}" stroke-width="{largura:.1f}"{tracejado_svg} />'
    )


def _svg_cota_vertical(x: float, y1: float, y2: float, texto: str) -> str:
    topo, base = sorted((y1, y2))
    meio = (topo + base) / 2
    if base - topo < 18:
        return (
            _svg_linha(x, topo, x, base, cor="#34566a", largura=1.5)
            + _svg_texto(x - 10, meio - 5, texto, tamanho=14, ancora="end", cor="#244c62")
        )
    return "".join(
        (
            _svg_linha(x, topo + 7, x, base - 7, cor="#34566a", largura=1.5),
            f'<path d="M {x - 5:.1f} {topo + 8:.1f} L {x:.1f} {topo:.1f} '
            f'L {x + 5:.1f} {topo + 8:.1f} M {x - 5:.1f} {base - 8:.1f} '
            f'L {x:.1f} {base:.1f} L {x + 5:.1f} {base - 8:.1f}" '
            'fill="none" stroke="#34566a" stroke-width="1.5" />',
            _svg_texto(x - 10, meio + 5, texto, tamanho=14, ancora="end", cor="#244c62"),
        )
    )


def _svg_painel(x: float, y: float, linhas: list[str], *, largura: float = 265) -> str:
    altura = 24 + 23 * len(linhas)
    partes = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{largura:.1f}" height="{altura:.1f}" '
        'rx="8" fill="#fffdf8" stroke="#cbbfa8" stroke-width="1" />'
    ]
    for indice, texto in enumerate(linhas):
        partes.append(
            _svg_texto(
                x + 12,
                y + 22 + 23 * indice,
                texto,
                tamanho=14 if indice else 15,
                peso=500 if indice == 0 else 400,
            )
        )
    return "".join(partes)


def gerar_svg_cortina_em_balanco(
    entradas: dict[str, Any], resultado: dict[str, Any]
) -> str:
    altura_m = float(entradas["altura_livre_escavacao_m"])
    ficha_teorica_m = float(resultado["ficha_teorica_m"])
    ficha_preliminar_m = float(resultado["ficha_preliminar_m"])
    profundidade_ponta_m = altura_m + ficha_preliminar_m
    escala = min(34.0, 350.0 / max(profundidade_ponta_m, 0.1))
    x_parede = 430.0
    y_superficie = 68.0
    y_escavacao = y_superficie + altura_m * escala
    y_ponta_teorica = y_escavacao + ficha_teorica_m * escala
    y_ponta_preliminar = y_escavacao + ficha_preliminar_m * escala
    altura_svg = max(450, ceil(y_ponta_preliminar + 120))
    percentual_passivo = float(entradas["percentual_passivo_mobilizado"])
    percentual_acrescimo = float(entradas["percentual_acrescimo_ficha"])
    partes = [
        f'<svg role="img" aria-label="Croqui dinâmico da cortina em balanço" '
        f'viewBox="0 0 1000 {altura_svg}" style="display:block;width:100%;height:auto">',
        "<title>Cortina em balanço com valores informados</title>",
        "<desc>Geometria da escavação e da estaca-prancha, com ficha teórica, ficha preliminar e parâmetros do solo.</desc>",
        f'<rect x="{x_parede + 10:.1f}" y="{y_superficie:.1f}" width="500" '
        f'height="{y_ponta_preliminar - y_superficie:.1f}" fill="#f1e2c4" />',
        f'<rect x="55" y="{y_escavacao:.1f}" width="{x_parede - 65:.1f}" '
        f'height="{y_ponta_preliminar - y_escavacao:.1f}" fill="#dceaf0" />',
        _svg_linha(x_parede, y_superficie, 940, y_superficie, cor="#176452", largura=3),
        _svg_linha(60, y_escavacao, x_parede - 10, y_escavacao, cor="#687a80", largura=2.5, tracejado="8 5"),
        f'<rect x="{x_parede - 9:.1f}" y="{y_superficie:.1f}" width="18" '
        f'height="{y_ponta_preliminar - y_superficie:.1f}" rx="2" fill="#87949a" stroke="#34434a" stroke-width="2" />',
        _svg_texto(82, y_escavacao - 12, "Escavação", tamanho=15, peso=500),
        _svg_texto(500, y_superficie + 28, "Solo retido · camada homogênea", tamanho=16, peso=500),
        _svg_cota_vertical(165, y_superficie, y_escavacao, f"h = {_formatar_numero(altura_m)} m"),
        _svg_cota_vertical(255, y_escavacao, y_ponta_teorica, f"f teórica = {_formatar_numero(ficha_teorica_m)} m"),
        _svg_cota_vertical(350, y_escavacao, y_ponta_preliminar, f"f preliminar = {_formatar_numero(ficha_preliminar_m)} m"),
    ]
    if y_ponta_preliminar - y_ponta_teorica > 5:
        partes.extend(
            (
                _svg_linha(390, y_ponta_teorica, x_parede - 11, y_ponta_teorica, cor="#34566a", largura=1.5, tracejado="5 4"),
                _svg_texto(x_parede + 22, y_ponta_teorica + 5, "Ponta teórica", tamanho=13, cor="#244c62"),
            )
        )
    partes.extend(
        (
            f'<circle cx="{x_parede:.1f}" cy="{y_ponta_preliminar:.1f}" r="5" fill="#34434a" />',
            _svg_painel(
                650,
                y_superficie + 52,
                [
                    "Parâmetros do solo",
                    f"γ = {_formatar_numero(float(entradas['peso_especifico_solo_kN_m3']))} kN/m³",
                    f"φ = {_formatar_numero(float(entradas['angulo_atrito_solo_graus']), 1)}°",
                ],
                largura=270,
            ),
            _svg_painel(
                650,
                y_superficie + 145,
                [
                    "Parâmetros de cálculo",
                    f"Passivo mobilizado = {_formatar_numero(percentual_passivo, 1)}% de Kₚ",
                    f"Acréscimo prático da ficha = +{_formatar_numero(percentual_acrescimo, 1)}%",
                ],
                largura=270,
            ),
            f'<text x="55" y="{y_ponta_preliminar + 48:.1f}" font-family="sans-serif" font-size="13" fill="#52646b">Vista esquemática · dimensões verticais cotadas</text>',
            "</svg>",
        )
    )
    return "".join(partes)


def gerar_svg_cortina_ancorada(
    entradas: dict[str, Any], resultado: dict[str, Any]
) -> str:
    profundidade_na_m = float(entradas["espessura_camada_superior_ate_na_m"])
    profundidade_escavacao_m = float(resultado["profundidade_escavacao_abaixo_superficie_m"])
    profundidade_ponta_m = float(resultado["profundidade_ponta_abaixo_superficie_m"])
    profundidade_ancoragem_m = profundidade_na_m - float(entradas["altura_ancoragem_acima_na_m"])
    profundidade_d_m = float(entradas["profundidade_na_ate_escavacao_m"])
    ficha_m = float(entradas["ficha_abaixo_escavacao_m"])
    profundidade_total_m = profundidade_na_m + profundidade_d_m + ficha_m
    escala = min(34.0, 370.0 / max(profundidade_total_m, 0.1))
    x_parede = 430.0
    y_superficie = 68.0
    y_na = y_superficie + profundidade_na_m * escala
    y_escavacao = y_superficie + profundidade_escavacao_m * escala
    y_ponta = y_superficie + profundidade_ponta_m * escala
    y_ancoragem = y_superficie + profundidade_ancoragem_m * escala
    altura_svg = max(470, ceil(y_ponta + 190))
    sobrecarga = float(entradas["sobrecarga_superficie_kPa"])
    partes = [
        f'<svg role="img" aria-label="Croqui dinâmico da cortina ancorada" '
        f'viewBox="0 0 1000 {altura_svg}" style="display:block;width:100%;height:auto">',
        "<title>Cortina ancorada com valores informados</title>",
        "<desc>Perfil com sobrecarga, nível d’água, escavação, tirante, camadas do solo e cotas inseridas.</desc>",
        f'<rect x="{x_parede + 10:.1f}" y="{y_superficie:.1f}" width="500" '
        f'height="{y_na - y_superficie:.1f}" fill="#f1e2c4" />',
        f'<rect x="{x_parede + 10:.1f}" y="{y_na:.1f}" width="500" '
        f'height="{y_ponta - y_na:.1f}" fill="#dceaf0" />',
        f'<rect x="55" y="{y_escavacao:.1f}" width="{x_parede - 65:.1f}" '
        f'height="{y_ponta - y_escavacao:.1f}" fill="#dceaf0" />',
        _svg_linha(x_parede, y_superficie, 940, y_superficie, cor="#176452", largura=3),
        _svg_linha(x_parede, y_na, 940, y_na, cor="#287b9c", largura=2, tracejado="8 5"),
        _svg_linha(60, y_escavacao, x_parede - 10, y_escavacao, cor="#687a80", largura=2.5, tracejado="8 5"),
        f'<rect x="{x_parede - 9:.1f}" y="{y_superficie:.1f}" width="18" '
        f'height="{y_ponta - y_superficie:.1f}" rx="2" fill="#87949a" stroke="#34434a" stroke-width="2" />',
        _svg_linha(x_parede + 10, y_ancoragem, 655, y_ancoragem, cor="#d99028", largura=4),
        f'<rect x="649" y="{y_ancoragem - 8:.1f}" width="8" height="16" fill="#d99028" />',
        _svg_texto(674, y_ancoragem - 12, "Tirante", tamanho=15, peso=500),
        _svg_texto(795, y_na + 5, "N.A.", tamanho=14, peso=500, cor="#176b88"),
        _svg_texto(70, y_escavacao - 12, "Fundo da escavação", tamanho=14, peso=500),
        _svg_texto(520, y_superficie + 43, "Solo natural", tamanho=15, peso=500),
        _svg_texto(520, y_na + 35, "Solo submerso", tamanho=15, peso=500),
        _svg_cota_vertical(140, y_superficie, y_na, f"H₁ = {_formatar_numero(profundidade_na_m)} m"),
        _svg_cota_vertical(220, y_na, y_escavacao, f"D = {_formatar_numero(profundidade_d_m)} m"),
        _svg_cota_vertical(300, y_escavacao, y_ponta, f"f = {_formatar_numero(ficha_m)} m"),
        _svg_cota_vertical(380, y_ancoragem, y_na, f"hₐ = {_formatar_numero(float(entradas['altura_ancoragem_acima_na_m']))} m"),
    ]
    if sobrecarga > 0:
        for x_seta in (520, 585, 650, 715, 780, 845):
            partes.extend(
                (
                    _svg_linha(x_seta, y_superficie - 26, x_seta, y_superficie - 5, cor="#287b9c", largura=1.8),
                    f'<path d="M {x_seta - 5} {y_superficie - 11} L {x_seta} {y_superficie - 4} '
                    f'L {x_seta + 5} {y_superficie - 11}" fill="none" stroke="#287b9c" stroke-width="1.8" />',
                )
            )
    partes.extend(
        (
            _svg_texto(680, y_superficie - 34, f"q = {_formatar_numero(sobrecarga)} kPa", tamanho=15, peso=500, ancora="middle", cor="#176b88"),
            _svg_painel(
                650,
                y_ponta + 35,
                [
                    "Parâmetros do solo e verificação",
                    f"γ₁ = {_formatar_numero(float(entradas['peso_especifico_solo_superior_kN_m3']))} · γ₂ = {_formatar_numero(float(entradas['peso_especifico_solo_submerso_kN_m3']))} kN/m³",
                    f"φ = {_formatar_numero(float(entradas['angulo_atrito_solo_graus']), 1)}° · Kₚ mobilizado = {_formatar_numero(float(entradas['percentual_passivo_mobilizado']), 1)}%",
                    f"FS mínimo ao tombamento = {_formatar_numero(float(entradas['fator_seguranca_minimo_tombamento']), 2)}",
                ],
                largura=300,
            ),
            "</svg>",
        )
    )
    return "".join(partes)
