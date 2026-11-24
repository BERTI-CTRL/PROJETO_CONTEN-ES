"""Primitivas para os croquis de estaca-prancha."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from math import floor, log10


def numero(valor: float, casas: int = 2) -> str:
    return f"{valor:,.{casas}f}".translate(str.maketrans(",.", ".,"))


def texto(x, y, valor, *, tamanho=16, peso=500, cor="#17364b", ancora="start", halo=False):
    contorno = ' stroke="#f5f9fc" stroke-width="5" paint-order="stroke"' if halo else ""
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" font-size="{tamanho}" font-weight="{peso}" '
        f'fill="{cor}" text-anchor="{ancora}"{contorno}>{escape(valor)}</text>'
    )


def linha(x1, y1, x2, y2, *, cor="#8199ab", largura=1, tracejado=""):
    traco = f' stroke-dasharray="{tracejado}"' if tracejado else ""
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{cor}" stroke-width="{largura}"{traco}/>'
    )


def retangulo(x, y, largura, altura, cor, *, raio=0, borda="none"):
    return (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{largura:.2f}" height="{altura:.2f}" '
        f'rx="{raio}" fill="{cor}" stroke="{borda}"/>'
    )


@dataclass(frozen=True)
class Perfil:
    caso: str
    profundidade: float

    superficie = 128
    parede = 460
    esquerda = 84
    direita = 688
    largura = 1024

    @property
    def escala(self) -> float:
        if self.profundidade <= 14:
            return 24
        # A seção continua crescendo, com redução gradual da escala.
        return 24 * (20 - 84 / self.profundidade) / self.profundidade

    def y(self, profundidade: float) -> float:
        return self.superficie + profundidade * self.escala

    @property
    def ponta(self) -> float:
        return self.y(self.profundidade)

    def abertura(self, titulo: str, descricao: str) -> str:
        altura = max(420, self.ponta + 62)
        return "".join((
            f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="Croqui dinâmico da {escape(titulo.lower())}" '
            f'viewBox="0 0 {self.largura} {altura:.2f}" '
            'style="display:block;width:100%;height:auto;font-family:system-ui,sans-serif">',
            f'<title>{escape(titulo)}</title><desc>{escape(descricao)}</desc>',
            '<defs>',
            f'<pattern id="{self.caso}-solo" width="12" height="12" patternUnits="userSpaceOnUse">'
            '<rect width="12" height="12" fill="#f5e3bf"/>'
            '<path d="M2 9l3 -3m3 -3l1 -1" stroke="#b08a4c" opacity=".40"/></pattern>',
            f'<pattern id="{self.caso}-submerso" width="12" height="12" patternUnits="userSpaceOnUse">'
            '<rect width="12" height="12" fill="#cfe8ef"/>'
            '<path d="M0 10l10 -10m2 10l-2 2" stroke="#458ca5" opacity=".32"/></pattern>',
            '</defs>',
            retangulo(1, 1, self.largura - 2, altura - 2, "#f5f9fc", raio=18, borda="#c9d9e5"),
            retangulo(20, 18, 984, 54, "#122f46", raio=12),
            texto(40, 52, titulo, tamanho=23, peso=700, cor="#ffffff"),
            texto(983, 51, "CORTE ESQUEMÁTICO", tamanho=13, peso=700,
                  cor="#b7deef", ancora="end"),
        ))

    def regua(self) -> str:
        # Passos de 1, 2 ou 5 vezes uma potência de dez.
        alvo = max(self.profundidade / 5, 0.01)
        ordem = 10 ** floor(log10(alvo))
        passo = next(ordem * fator for fator in (1, 2, 5, 10) if ordem * fator >= alvo)
        casas = max(0, -floor(log10(passo)))
        partes = [texto(52, self.superficie - 17, "z (m)", tamanho=14, ancora="end")]
        for indice in range(floor(self.profundidade / passo) + 1):
            z = indice * passo
            y = self.y(z)
            partes.extend((
                linha(60, y, self.direita, y, cor="#7593a7", tracejado="3 5"),
                linha(52, y, 60, y, cor="#42647a"),
                texto(46, y + 5, numero(z, casas), tamanho=13, ancora="end"),
            ))
        return "".join(partes)

    def camada(self, x1, x2, topo, base, tipo="solo") -> str:
        return retangulo(x1, topo, x2 - x1, base - topo, f"url(#{self.caso}-{tipo})")

    def estaca(self) -> str:
        altura = self.ponta - self.superficie
        return "".join((
            retangulo(self.parede - 8, self.superficie, 16, altura, "#1c3e58", raio=2),
            retangulo(self.parede - 4, self.superficie, 4, altura, "#79a9c9"),
            linha(self.parede - 12, self.ponta, self.parede + 12, self.ponta,
                  cor="#1c3e58", largura=2),
        ))

    def rodape(self) -> str:
        return texto(32, max(392, self.ponta + 39),
                     "Profundidade a partir da superfície · sem escala horizontal",
                     tamanho=14, cor="#49687d")


def cota(x, topo, base, valor, *, deslocamento=0):
    y = (topo + base) / 2 + deslocamento
    return "".join((
        linha(x, topo, x, base, cor="#355f79", largura=1.5),
        linha(x - 5, topo, x + 5, topo, cor="#355f79", largura=1.5),
        linha(x - 5, base, x + 5, base, cor="#355f79", largura=1.5),
        texto(x - 8, y + 5, valor, tamanho=15, peso=650, ancora="end", halo=True),
    ))


def painel(titulo, linhas):
    x, y = 710, 93
    partes = [
        retangulo(x, y, 294, 46 + len(linhas) * 32, "#ffffff", raio=12, borda="#c9d9e5"),
        texto(x + 16, y + 28, titulo, tamanho=18, peso=700),
    ]
    for i, valor in enumerate(linhas):
        altura = y + 46 + i * 32
        partes.extend((
            linha(x + 16, altura - 5, x + 278, altura - 5, cor="#e2ecf3"),
            texto(x + 16, altura + 15, valor, tamanho=15),
        ))
    return "".join(partes)
