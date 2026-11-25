"""Primitivas para cortes geotécnicos em metros no model space."""

from io import StringIO

import ezdxf
from ezdxf import zoom


class CorteDXF:
    def __init__(self, extensao: float):
        self.doc = ezdxf.new("R2010", setup=True, units=6)
        self.modelo = self.doc.modelspace()
        self.t = max(0.025, extensao * 0.023)
        for nome, cor, tipo in (
            ("TERRENO", 30, "CONTINUOUS"),
            ("SOLO", 32, "CONTINUOUS"),
            ("AGUA", 5, "DASHED"),
            ("CONTENCAO", 7, "CONTINUOUS"),
            ("APOIOS", 4, "CONTINUOUS"),
            ("REFERENCIAS", 8, "DASHED"),
            ("SOBRECARGA", 1, "CONTINUOUS"),
            ("COTAS", 2, "CONTINUOUS"),
            ("PARAMETROS", 7, "CONTINUOUS"),
        ):
            self.doc.layers.new(nome, dxfattribs={"color": cor, "linetype": tipo})

    def linha(self, inicio, fim, camada):
        if inicio != fim:
            self.modelo.add_line(inicio, fim, dxfattribs={"layer": camada})

    def texto(self, texto, x, y, camada="PARAMETROS", *, tamanho=1):
        self.modelo.add_text(
            texto, dxfattribs={"insert": (x, y), "height": self.t * tamanho, "layer": camada}
        )

    def solo(self, x1, x2, topo, base, *, submerso=False):
        if topo <= base:
            return
        camada = "AGUA" if submerso else "SOLO"
        hachura = self.modelo.add_hatch(dxfattribs={"layer": camada})
        hachura.set_pattern_fill("ANSI31" if submerso else "ANSI37", scale=self.t * 2)
        hachura.dxf.color = 256
        hachura.paths.add_polyline_path(
            [(x1, topo), (x2, topo), (x2, base), (x1, base)], is_closed=True
        )

    def cota(self, p1, p2, base, simbolo, *, vertical=True):
        eixo = 1 if vertical else 0
        if p1[eixo] == p2[eixo]:
            return
        cota = self.modelo.add_linear_dim(
            base, p1, p2, angle=90 if vertical else 0, text=f"{simbolo} = <> m",
            dxfattribs={"layer": "COTAS"},
            override={
                "dimtxt": self.t, "dimasz": self.t * 0.65, "dimgap": self.t * 0.3,
                "dimexo": self.t * 0.25, "dimexe": self.t * 0.5, "dimdec": 3,
                "dimlfac": 1, "dimdsep": ord(","), "dimtad": 1,
            },
        )
        cota.render()

    def vertical(self, x, topo, base, deslocamento, simbolo):
        self.cota((x, topo), (x, base), (x + deslocamento, topo), simbolo)

    def sobrecarga(self, inicio, fim, q):
        if q <= 0:
            return
        for indice in range(1, 5):
            x = inicio + (fim - inicio) * indice / 5
            self.linha((x, self.t * 3), (x, 0), "SOBRECARGA")
            for sinal in (-1, 1):
                self.linha((x + sinal * self.t * 0.4, self.t), (x, 0), "SOBRECARGA")
        self.texto(f"q = {q:g} kPa", inicio, self.t * 3.7, "SOBRECARGA")

    def painel(self, titulo, x, linhas):
        self.texto(titulo, x, self.t * 4, tamanho=1.45)
        for indice, texto in enumerate(linhas):
            self.texto(texto, x, self.t * (1.8 - 1.8 * indice))

    def bytes(self) -> bytes:
        zoom.extents(self.modelo, factor=1.15)
        arquivo = StringIO()
        self.doc.write(arquivo)
        return self.doc.encode(arquivo.getvalue())


def parametros(dados, campos):
    return [
        f"{nome} = {dados[chave]:g}{unidade}"
        for nome, chave, unidade in campos
    ]
