"""Exportação dos quatro cortes da página Escoradas em DXF."""

from contencoes.cad.corte_dxf import CorteDXF, parametros

GAMA = ("γ", "peso_especifico_solo_kN_m3", " kN/m³")
GAMA_AGUA = ("γw", "peso_especifico_agua_kN_m3", " kN/m³")
ATRITO = ("φ", "angulo_atrito_solo_graus", "°")
CU = ("cu", "coesao_nao_drenada_kPa", " kPa")
FS = ("FS mínimo", "fator_seguranca_minimo", "")
H = ("H", "altura_escavacao_m", " m")


def _vala(cad, h, largura, margem, *, agua=None):
    fundo = -h
    base = -h * 1.3
    for x1, x2 in ((-margem, 0), (largura, largura + margem)):
        cad.linha((x1, 0), (x2, 0), "TERRENO")
        if agua is None:
            cad.solo(x1, x2, 0, base)
        else:
            cad.solo(x1, x2, 0, max(base, agua))
            cad.solo(x1, x2, agua, base, submerso=True)
            cad.linha((x1, agua), (x2, agua), "AGUA")
    cad.solo(0, largura, fundo, base)
    cad.linha((0, fundo), (largura, fundo), "TERRENO")
    for x in (0, largura):
        cad.linha((x, 0), (x, fundo), "CONTENCAO")
    cad.vertical(0, 0, fundo, -margem - cad.t * 3, "H")


def gerar_dxf_pressao_aparente(dados):
    h = dados["altura_escavacao_m"]
    na = dados["profundidade_nivel_agua_m"]
    n = int(dados["quantidade_niveis_escora"])
    e = dados["espacamento_longitudinal_escoras_m"]
    cad = CorteDXF(h)
    largura, margem = h, h * 0.6
    _vala(cad, h, largura, margem, agua=-na)
    cad.texto("N.A.", largura + cad.t * 2, -na + cad.t, "AGUA")
    cad.vertical(largura + margem, 0, -na, cad.t * 2, "z N.A.")
    cad.sobrecarga(-margem, 0, dados["sobrecarga_superficie_kPa"])
    cad.sobrecarga(largura, largura + margem, dados["sobrecarga_superficie_kPa"])

    # Mantém o arquivo limitado em entradas muito grandes e registra o total.
    representadas = min(n, 100)
    for indice in range(1, representadas + 1):
        profundidade = h * indice / (representadas + 1)
        cad.linha((0, -profundidade), (largura, -profundidade), "APOIOS")
    y = -max(h * 1.3, na) - cad.t * 8
    cad.texto("Vista longitudinal · dois eixos de escoras", 0, y + cad.t * 4)
    cad.linha((0, y), (e, y), "REFERENCIAS")
    for x in (0, e):
        cad.linha((x, y - cad.t), (x, y + cad.t), "APOIOS")
    cad.cota((0, y), (e, y), (0, y - cad.t * 3), "e", vertical=False)

    cad.painel("Pressões e escoras", largura + margem + cad.t * 8, [
        dados["tipo_solo"],
        f"Níveis de escoras: {n}",
        *parametros(dados, (
            H, ("q", "sobrecarga_superficie_kPa", " kPa"), GAMA, ATRITO, CU,
            ("m", "coeficiente_empirico_argila", ""),
            ("e longitudinal", "espacamento_longitudinal_escoras_m", " m"),
            ("z N.A.", "profundidade_nivel_agua_m", " m"), GAMA_AGUA,
        )),
        "Vão transversal e posições das escoras esquemáticos",
        *([f"Exibidos {representadas} níveis de {n}"] if representadas < n else []),
    ])
    return cad.bytes()


def gerar_dxf_ruptura_fundo(dados):
    h, b = dados["altura_escavacao_m"], dados["largura_escavacao_m"]
    cad = CorteDXF(max(h, b))
    margem = max(h * 0.6, cad.t * 3)
    _vala(cad, h, b, margem)
    cad.cota((0, -h), (b, -h), (0, -h - cad.t * 3), "B", vertical=False)
    cad.painel("Ruptura de fundo · Terzaghi", b + margem + cad.t * 4, parametros(dados, (
        H, ("B", "largura_escavacao_m", " m"), GAMA, CU, FS,
    )))
    return cad.bytes()


def gerar_dxf_graux(dados):
    h = dados["altura_escavacao_m"]
    d = dados["ficha_abaixo_fundo_m"]
    z = dados["diferenca_carga_agua_m"]
    fundo, ponta, agua = -h, -h - d, z - h
    cad = CorteDXF(max(h + d, z))
    largura = (h + d) * 0.7
    cad.solo(-largura, 0, 0, min(0, agua))
    cad.solo(-largura, 0, min(0, agua), ponta, submerso=True)
    cad.solo(0, largura, fundo, ponta, submerso=True)
    cad.linha((-largura, 0), (0, 0), "TERRENO")
    cad.linha((0, fundo), (largura, fundo), "TERRENO")
    cad.linha((0, 0), (0, ponta), "CONTENCAO")
    cad.linha((-largura, agua), (0, agua), "AGUA")
    cad.texto("Carga externa", -largura, agua + cad.t, "AGUA")
    cad.linha((0, fundo), (largura, fundo), "AGUA")
    cad.texto("Referência interna", cad.t, fundo + cad.t, "AGUA")
    cad.vertical(0, 0, fundo, -largura - cad.t * 3, "H")
    cad.vertical(0, fundo, ponta, -largura - cad.t * 3, "D")
    cad.vertical(0, agua, fundo, -largura - cad.t * 8, "Z")
    cad.painel("Estabilidade hidráulica · Graux", largura + cad.t * 4, [
        *parametros(dados, (
            H, ("D", "ficha_abaixo_fundo_m", " m"), ("Z", "diferenca_carga_agua_m", " m"),
            ("γn", "peso_especifico_natural_kN_m3", " kN/m³"),
            ("γsub", "peso_especifico_submerso_kN_m3", " kN/m³"), ATRITO, GAMA_AGUA, FS,
        )),
        "Extensões horizontais esquemáticas",
    ])
    return cad.bytes()


def gerar_dxf_froehlich(dados, resultado):
    h = dados["altura_escavacao_m"]
    hcr = resultado["altura_critica_m"]
    alcance = max(h, hcr, 1)
    cad = CorteDXF(alcance)
    largura, base = alcance * 0.72, -alcance * 1.18
    cad.solo(0, largura, 0, base)
    cad.solo(-largura, 0, -h, base)
    for p1, p2 in (((-largura, -h), (0, -h)), ((0, -h), (0, 0)), ((0, 0), (largura, 0))):
        cad.linha(p1, p2, "TERRENO")
    cad.linha((0, -hcr), (largura, -hcr), "REFERENCIAS")
    cad.texto("Profundidade crítica teórica", cad.t, -hcr - cad.t * 2, "REFERENCIAS")
    cad.vertical(0, 0, -h, -largura - cad.t * 3, "H")
    cad.vertical(largura, 0, -hcr, cad.t * 3, "Hcr")
    cad.painel("Corte vertical · Fröhlich", largura + cad.t * 8, [
        *parametros(dados, (H, GAMA, ("c", "coesao_solo_kPa", " kPa"), ATRITO)),
        f"Hcr = {hcr:.3f} m",
        "Extensões horizontais esquemáticas",
    ])
    return cad.bytes()
