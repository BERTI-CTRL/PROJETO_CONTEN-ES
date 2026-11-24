"""Cortes SVG da página de escavações escoradas."""

from contencoes.svg.svg_perfil_estaca import Perfil, cota, linha, numero, painel, retangulo, texto

AZUL = "#146e93"
ACO = "#23465f"
SOLO = "#8e6328"


def _corte(perfil, esquerda, direita, fundo, base, *, parede=True):
    topo = perfil.superficie
    partes = [
        perfil.camada(perfil.esquerda, esquerda, topo, fundo),
        perfil.camada(direita, perfil.direita, topo, fundo),
        perfil.camada(perfil.esquerda, perfil.direita, fundo, base),
        perfil.regua(),
        linha(perfil.esquerda, topo, esquerda, topo, cor=SOLO, largura=3),
        linha(direita, topo, perfil.direita, topo, cor=SOLO, largura=3),
        linha(esquerda, fundo, direita, fundo, cor=SOLO, largura=2),
    ]
    if parede:
        partes.extend(
            linha(x, topo, x, fundo, cor=ACO, largura=6)
            for x in (esquerda, direita)
        )
    return "".join(partes)


def _finalizar(perfil, titulo, descricao, desenho, parametros):
    return "".join((
        perfil.abertura(titulo, descricao),
        *desenho,
        painel("Dados do corte", parametros),
        perfil.rodape(),
        "</svg>",
    ))


def gerar_svg_pressao_aparente(dados):
    h = dados["altura_escavacao_m"]
    q = dados["sobrecarga_superficie_kPa"]
    na = dados["profundidade_nivel_agua_m"]
    n = int(dados["quantidade_niveis_escora"])
    perfil = Perfil("escoradas-pressao", 1.3 * h)
    topo, fundo, base = perfil.superficie, perfil.y(h), perfil.ponta
    esquerda, direita = 258, 590
    desenho = [_corte(perfil, esquerda, direita, fundo, base)]
    if na <= perfil.profundidade:
        agua = perfil.y(na)
        desenho.extend((
            linha(perfil.esquerda, agua, esquerda, agua, cor=AZUL, largura=2, tracejado="7 4"),
            linha(direita, agua, perfil.direita, agua, cor=AZUL, largura=2, tracejado="7 4"),
            texto(perfil.direita - 4, agua - 7, "N.A.", cor=AZUL, ancora="end", halo=True),
        ))
    if q > 0:
        for x in (105, 145, 185, 225, 613, 643, 673):
            desenho.append(linha(x, topo - 21, x, topo - 5, cor=ACO, largura=1.5))
            desenho.append(f'<path d="M{x - 4} {topo - 10}l4 5 4 -5" fill="none" stroke="{ACO}"/>')
        desenho.append(texto(166, topo - 28, f"q = {numero(q)} kPa", ancora="middle"))
    niveis_visiveis = min(n, 12)
    altura_escora = min(6, (fundo - topo) / (niveis_visiveis + 1) / 2)
    for indice in range(1, niveis_visiveis + 1):
        y = topo + (fundo - topo) * indice / (niveis_visiveis + 1)
        desenho.extend((
            retangulo(esquerda, y - altura_escora / 2, direita - esquerda, altura_escora, AZUL),
            linha(esquerda + 6, y - 5, esquerda + 6, y + 5, cor=ACO, largura=3),
            linha(direita - 6, y - 5, direita - 6, y + 5, cor=ACO, largura=3),
        ))
    observacao = "Níveis ilustrativos, igualmente espaçados"
    if n > niveis_visiveis:
        observacao = f"Níveis representados: {niveis_visiveis} de {n}"
    desenho.extend((
        cota(236, topo, fundo, f"H = {numero(h)} m"),
        texto(424, fundo + 25, observacao, tamanho=14, ancora="middle", halo=True),
    ))
    return _finalizar(perfil, "Escavação escorada", "Corte com escoras, sobrecarga e nível d’água.", desenho, [
        dados["tipo_solo"].partition(" — ")[0],
        f"H = {numero(h)} m  ·  {n} níveis",
        f"q = {numero(q)} kPa  ·  φ = {numero(dados['angulo_atrito_solo_graus'], 1)}°",
        f"γ = {numero(dados['peso_especifico_solo_kN_m3'])} kN/m³",
        f"cᵤ = {numero(dados['coesao_nao_drenada_kPa'])} kPa  ·  m = {numero(dados['coeficiente_empirico_argila'])}",
        f"z N.A. = {numero(na)} m",
        f"γw = {numero(dados['peso_especifico_agua_kN_m3'])} kN/m³",
        f"e longitudinal = {numero(dados['espacamento_longitudinal_escoras_m'])} m",
    ])


def gerar_svg_ruptura_fundo(dados):
    h, b = dados["altura_escavacao_m"], dados["largura_escavacao_m"]
    perfil = Perfil("escoradas-fundo", 1.35 * h)
    topo, fundo, base = perfil.superficie, perfil.y(h), perfil.ponta
    meia_largura = 36 + 208 * (b / (b + 10))
    esquerda, direita = 424 - meia_largura, 424 + meia_largura
    desenho = [
        _corte(perfil, esquerda, direita, fundo, base),
        cota(165, topo, fundo, f"H = {numero(h)} m"),
        linha(esquerda, fundo + 18, direita, fundo + 18, cor=ACO),
        linha(esquerda, fundo + 13, esquerda, fundo + 23, cor=ACO),
        linha(direita, fundo + 13, direita, fundo + 23, cor=ACO),
        texto(424, fundo + 38, f"B = {numero(b)} m", ancora="middle", halo=True),
    ]
    return _finalizar(perfil, "Ruptura de fundo", "Corte com altura e largura da escavação.", desenho, [
        f"H = {numero(h)} m  ·  B = {numero(b)} m",
        f"γ = {numero(dados['peso_especifico_solo_kN_m3'])} kN/m³",
        f"cᵤ = {numero(dados['coesao_nao_drenada_kPa'])} kPa",
        f"FS mínimo = {numero(dados['fator_seguranca_minimo'])}",
    ])


def gerar_svg_graux(dados):
    h = dados["altura_escavacao_m"]
    z = dados["diferenca_carga_agua_m"]
    d = dados["ficha_abaixo_fundo_m"]
    perfil = Perfil("escoradas-graux", h + d)
    topo, fundo, ponta = perfil.superficie, perfil.y(h), perfil.ponta
    agua = perfil.y(max(0, h - z))
    x = perfil.parede
    desenho = [
        perfil.camada(perfil.esquerda, x, topo, agua),
        perfil.camada(perfil.esquerda, x, agua, ponta, "submerso"),
        perfil.camada(x, perfil.direita, fundo, ponta, "submerso"),
        perfil.regua(),
        perfil.estaca(),
        linha(perfil.esquerda, topo, x, topo, cor=SOLO, largura=2),
        linha(perfil.esquerda, agua, x - 9, agua, cor=AZUL, largura=2, tracejado="7 4"),
        linha(x + 9, fundo, perfil.direita, fundo, cor=AZUL, largura=2),
        texto(416, agua - 8, "N.A. acima do terreno" if z > h else "N.A. externo",
              cor=AZUL, ancora="end", halo=True),
        texto(675, fundo - 8, "Fundo da escavação", ancora="end", halo=True),
        cota(174, topo, fundo, f"H = {numero(h)} m"),
        cota(665, fundo, ponta, f"D = {numero(d)} m"),
    ]
    if 0 < z <= h:
        desenho.append(cota(394, agua, fundo, f"Z = {numero(z)} m"))
    return _finalizar(perfil, "Estabilidade hidráulica · Graux", "Corte com ficha e diferença de carga d’água.", desenho, [
        f"H = {numero(h)} m  ·  D = {numero(d)} m",
        f"Z = {numero(z)} m",
        f"γn = {numero(dados['peso_especifico_natural_kN_m3'])} kN/m³",
        f"γsub = {numero(dados['peso_especifico_submerso_kN_m3'])} kN/m³",
        f"γw = {numero(dados['peso_especifico_agua_kN_m3'])} kN/m³",
        f"φ = {numero(dados['angulo_atrito_solo_graus'], 1)}°",
        f"FS mínimo = {numero(dados['fator_seguranca_minimo'])}",
    ])


def gerar_svg_froehlich(dados, resultado):
    h = dados["altura_escavacao_m"]
    hcr = resultado["altura_critica_m"]
    perfil = Perfil("escoradas-froehlich", max(h, hcr) * 1.12)
    topo, fundo, critico = perfil.superficie, perfil.y(h), perfil.y(hcr)
    x = perfil.parede
    desenho = [
        perfil.camada(perfil.esquerda, x, fundo, perfil.ponta),
        perfil.camada(x, perfil.direita, topo, perfil.ponta),
        perfil.regua(),
        linha(x, topo, perfil.direita, topo, cor=SOLO, largura=3),
        linha(perfil.esquerda, fundo, x, fundo, cor=SOLO, largura=2),
        linha(x, topo, x, fundo, cor=SOLO, largura=3),
        linha(x + 8, critico, perfil.direita, critico, cor=AZUL, largura=2, tracejado="6 4"),
        cota(270, topo, fundo, f"H = {numero(h)} m"),
        texto(675, critico + 19, f"Hcr = {numero(hcr)} m", cor=AZUL, ancora="end", halo=True),
    ]
    return _finalizar(perfil, "Corte vertical · Fröhlich", "Altura avaliada e profundidade crítica teórica.", desenho, [
        f"H avaliada = {numero(h)} m",
        f"Hcr teórica = {numero(hcr)} m",
        f"γ = {numero(dados['peso_especifico_solo_kN_m3'])} kN/m³",
        f"c = {numero(dados['coesao_solo_kPa'])} kPa",
        f"φ = {numero(dados['angulo_atrito_solo_graus'], 1)}°",
    ])
