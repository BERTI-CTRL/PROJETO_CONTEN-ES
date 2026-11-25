"""Exportação dos dois cortes de estaca-prancha em DXF."""

from contencoes.cad.corte_dxf import CorteDXF, parametros


def _perfil(cad, largura, fundo, ponta):
    cad.linha((-largura, fundo), (0, fundo), "TERRENO")
    cad.linha((0, 0), (largura, 0), "TERRENO")
    cad.linha((0, 0), (0, ponta), "CONTENCAO")
    cad.solo(-largura, 0, fundo, ponta)
    cad.texto("Escavação", -largura, fundo + cad.t)
    cad.texto("Solo retido", largura / 2, cad.t)
    cad.texto("Extensões horizontais esquemáticas", -largura, cad.t * 2)


def gerar_dxf_cortina_em_balanco(dados, resultado):
    h = dados["altura_livre_escavacao_m"]
    teorica = resultado["ficha_teorica_m"]
    preliminar = resultado["ficha_preliminar_m"]
    altura = h + preliminar
    cad = CorteDXF(altura)
    largura = altura * 0.72
    _perfil(cad, largura, -h, -altura)
    cad.solo(0, largura, 0, -altura)
    cad.linha((0, -h - teorica), (largura, -h - teorica), "REFERENCIAS")
    cad.texto("Ponta teórica", largura / 2, -h - teorica + cad.t, "REFERENCIAS")
    cad.vertical(0, 0, -h, -largura - 3 * cad.t, "h")
    cad.vertical(0, -h, -h - teorica, -largura - 3 * cad.t, "f teórica")
    cad.vertical(0, -h, -altura, -largura - 8 * cad.t, "f preliminar")
    cad.painel("Cortina em balanço", largura + 4 * cad.t, [
        f"h = {h:g} m",
        *parametros(dados, (
            ("γ", "peso_especifico_solo_kN_m3", " kN/m³"),
            ("φ", "angulo_atrito_solo_graus", "°"),
            ("Passivo mobilizado", "percentual_passivo_mobilizado", "%"),
            ("Acréscimo prático da ficha", "percentual_acrescimo_ficha", "%"),
        )),
        f"f teórica = {teorica:.3f} m",
        f"f preliminar = {preliminar:.3f} m",
    ])
    return cad.bytes()


def gerar_dxf_cortina_ancorada(dados, resultado):
    h1 = dados["espessura_camada_superior_ate_na_m"]
    ha = dados["altura_ancoragem_acima_na_m"]
    fundo = -resultado["profundidade_escavacao_abaixo_superficie_m"]
    ponta = -resultado["profundidade_ponta_abaixo_superficie_m"]
    agua = -h1
    tirante = agua + ha
    cad = CorteDXF(-ponta)
    largura = -ponta * 0.72
    _perfil(cad, largura, fundo, ponta)
    cad.solo(0, largura, 0, agua)
    cad.solo(0, largura, agua, ponta, submerso=True)
    cad.linha((0, agua), (largura, agua), "AGUA")
    cad.texto("N.A.", largura * 0.8, agua + cad.t, "AGUA")
    extremidade = largura * 0.63
    cad.linha((0, tirante), (extremidade, tirante), "APOIOS")
    cad.linha((extremidade, tirante - cad.t), (extremidade, tirante + cad.t), "APOIOS")
    cad.texto("Tirante esquemático", cad.t, tirante + cad.t, "APOIOS")
    cad.sobrecarga(0, largura, dados["sobrecarga_superficie_kPa"])
    for topo, base, simbolo in ((0, agua, "H1"), (agua, fundo, "D"), (fundo, ponta, "f")):
        cad.vertical(0, topo, base, -largura - 3 * cad.t, simbolo)
    cad.vertical(0, tirante, agua, -largura - 8 * cad.t, "ha")
    cad.painel("Cortina ancorada", largura + 4 * cad.t, parametros(dados, (
        ("q", "sobrecarga_superficie_kPa", " kPa"),
        ("H1", "espessura_camada_superior_ate_na_m", " m"),
        ("D", "profundidade_na_ate_escavacao_m", " m"),
        ("f", "ficha_abaixo_escavacao_m", " m"),
        ("ha", "altura_ancoragem_acima_na_m", " m"),
        ("γ1", "peso_especifico_solo_superior_kN_m3", " kN/m³"),
        ("γ2", "peso_especifico_solo_submerso_kN_m3", " kN/m³"),
        ("φ", "angulo_atrito_solo_graus", "°"),
        ("Passivo mobilizado", "percentual_passivo_mobilizado", "%"),
        ("FS mínimo", "fator_seguranca_minimo_tombamento", ""),
    )))
    return cad.bytes()
