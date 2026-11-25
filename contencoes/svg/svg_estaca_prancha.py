"""Croquis vetoriais gerados a partir das entradas e dos resultados."""

from __future__ import annotations

from typing import Any

from contencoes.svg.svg_perfil_estaca import Perfil, cota, linha, numero, painel, retangulo, texto


def gerar_svg_cortina_em_balanco(
    entradas: dict[str, Any], resultado: dict[str, Any]
) -> str:
    h = entradas["altura_livre_escavacao_m"]
    teorica = resultado["ficha_teorica_m"]
    preliminar = resultado["ficha_preliminar_m"]
    perfil = Perfil("balanco", h + preliminar)
    topo, fundo, ponta = perfil.superficie, perfil.y(h), perfil.ponta
    x = perfil.parede
    ponta_teorica = perfil.y(h + teorica)
    return "".join((
        perfil.abertura("Cortina em balanço", "Corte com escavação, solo retido e fichas cotadas."),
        perfil.camada(x, perfil.direita, topo, ponta),
        perfil.camada(perfil.esquerda, x, fundo, ponta),
        perfil.regua(),
        linha(x, topo, perfil.direita, topo, cor="#8e6328", largura=3),
        linha(perfil.esquerda, fundo, x, fundo, cor="#8e6328", largura=2),
        linha(x, ponta_teorica, perfil.direita, ponta_teorica,
              cor="#1e658d", largura=2, tracejado="6 4"),
        perfil.estaca(),
        texto(477, topo + 24, "Solo retido", peso=700, halo=True),
        texto(88, fundo - 10, "Escavação", peso=700, halo=True),
        cota(239, topo, fundo, f"h = {numero(h)} m"),
        cota(293, fundo, ponta_teorica, "f teórica", deslocamento=-9),
        cota(434, fundo, ponta, "f preliminar", deslocamento=12),
        painel("Solo e ficha", [
            f"γ = {numero(entradas['peso_especifico_solo_kN_m3'])} kN/m³",
            f"φ = {numero(entradas['angulo_atrito_solo_graus'], 1)}°",
            f"Passivo mobilizado = {numero(entradas['percentual_passivo_mobilizado'], 1)}% de Kₚ",
            f"Acréscimo prático da ficha = +{numero(entradas['percentual_acrescimo_ficha'], 1)}%",
            f"f teórica = {numero(teorica)} m",
            f"f preliminar = {numero(preliminar)} m",
        ]),
        perfil.rodape(),
        "</svg>",
    ))


def gerar_svg_cortina_ancorada(
    entradas: dict[str, Any], resultado: dict[str, Any]
) -> str:
    h1 = entradas["espessura_camada_superior_ate_na_m"]
    d = entradas["profundidade_na_ate_escavacao_m"]
    ficha = entradas["ficha_abaixo_escavacao_m"]
    ha = entradas["altura_ancoragem_acima_na_m"]
    q = entradas["sobrecarga_superficie_kPa"]
    perfil = Perfil("ancorada", resultado["profundidade_ponta_abaixo_superficie_m"])
    topo, agua, ponta = perfil.superficie, perfil.y(h1), perfil.ponta
    fundo = perfil.y(resultado["profundidade_escavacao_abaixo_superficie_m"])
    tirante = perfil.y(h1 - ha)
    x = perfil.parede
    setas = []
    if q > 0:
        for posicao in range(484, 688, 31):
            setas.extend((
                linha(posicao, topo - 22, posicao, topo - 4, cor="#305a74", largura=1.6),
                f'<path d="M{posicao - 4} {topo - 9}l4 5 4 -5" '
                'fill="none" stroke="#305a74" stroke-width="1.6"/>',
            ))
    return "".join((
        perfil.abertura("Cortina ancorada", "Corte com sobrecarga, nível d’água, tirante e camadas de solo."),
        perfil.camada(x, perfil.direita, topo, agua),
        perfil.camada(x, perfil.direita, agua, ponta, "submerso"),
        perfil.camada(perfil.esquerda, x, fundo, ponta, "submerso"),
        perfil.regua(),
        linha(x, topo, perfil.direita, topo, cor="#8e6328", largura=3),
        linha(perfil.esquerda, fundo, x, fundo, cor="#476d82", largura=2),
        linha(x, agua, perfil.direita, agua, cor="#147b9d", largura=2, tracejado="8 4"),
        perfil.estaca(),
        *setas,
        texto(574, topo - 29, f"q = {numero(q)} kPa", ancora="middle", peso=700),
        linha(x + 8, tirante, 600, tirante, cor="#99551b", largura=4),
        retangulo(597, tirante - 8, 7, 16, "#99551b", raio=2),
        texto(610, tirante - 8, "Tirante", cor="#7e4519", peso=700, halo=True),
        texto(683, agua + 18, "N.A.", cor="#0b6383", ancora="end", peso=700, halo=True),
        texto(88, fundo - 10, "Escavação", peso=700, halo=True),
        cota(195, topo, agua, f"H₁ = {numero(h1)} m"),
        cota(285, agua, fundo, f"D = {numero(d)} m"),
        cota(375, fundo, ponta, f"f = {numero(ficha)} m"),
        cota(435, tirante, agua, f"hₐ = {numero(ha)} m"),
        painel("Solo e verificação", [
            f"γ₁ = {numero(entradas['peso_especifico_solo_superior_kN_m3'])} · "
            f"γ₂ = {numero(entradas['peso_especifico_solo_submerso_kN_m3'])} kN/m³",
            f"φ = {numero(entradas['angulo_atrito_solo_graus'], 1)}° · "
            f"Kₚ mobilizado = {numero(entradas['percentual_passivo_mobilizado'], 1)}%",
            f"γw = {numero(entradas.get('peso_especifico_agua_kN_m3', 9.81))} kN/m³",
            f"FS mínimo ao tombamento = {numero(entradas['fator_seguranca_minimo_tombamento'])}",
        ]),
        perfil.camada(726, 749, 291, 307),
        texto(759, 304, "Solo acima do N.A.", tamanho=15),
        perfil.camada(726, 749, 320, 336, "submerso"),
        texto(759, 333, "Solo submerso", tamanho=15),
        perfil.rodape(),
        "</svg>",
    ))
