"""Exporta perfil, fatias e memória de cálculo do talude para DXF."""

from __future__ import annotations

import math
from io import StringIO
from typing import Any

import ezdxf


CHAVES_AREAS_FATIA = (
    "area_camada_superior_nao_saturada_m2",
    "area_camada_superior_saturada_m2",
    "area_camada_inferior_nao_saturada_m2",
    "area_camada_inferior_saturada_m2",
)


def gerar_desenho_talude_dxf(
    entradas_talude: dict[str, Any], resultado_talude: dict[str, Any], circulo: dict[str, Any]
) -> bytes:
    """Gera um DXF em metros com geometria real e polígonos para conferência de área."""
    documento = ezdxf.new("R2010", setup=True, units=6)
    espaco_modelo = documento.modelspace()
    _criar_camadas(documento)

    _desenhar_perfil(espaco_modelo, entradas_talude, resultado_talude)
    _desenhar_circulo_critico(espaco_modelo, circulo)

    fatias = circulo["fatias"]
    deslocamento_area_m = _desenhar_fatias(
        espaco_modelo, resultado_talude, fatias, circulo
    )
    _desenhar_cotas(espaco_modelo, entradas_talude, resultado_talude)
    _adicionar_memoria_completa(
        espaco_modelo,
        entradas_talude,
        resultado_talude,
        circulo,
        deslocamento_area_m,
    )

    arquivo_texto = StringIO()
    documento.write(arquivo_texto)
    return documento.encode(arquivo_texto.getvalue())


def _criar_camadas(documento: ezdxf.document.Drawing) -> None:
    camadas_desenho = {
        "TERRENO": (3, "CONTINUOUS"),
        "CAMADAS": (30, "DASHED"),
        "NIVEL_AGUA": (5, "DASHDOT"),
        "CIRCULO_CRITICO": (1, "CONTINUOUS"),
        "CENTRO_CIRCULO": (7, "CONTINUOUS"),
        "FATIAS_GEOMETRIA": (8, "CONTINUOUS"),
        "AREA_CONFERENCIA": (2, "CONTINUOUS"),
        "COTAS": (2, "CONTINUOUS"),
        "MEMORIAL": (7, "CONTINUOUS"),
    }
    for nome_camada, (cor, tipo_linha) in camadas_desenho.items():
        documento.layers.new(nome_camada, dxfattribs={"color": cor, "linetype": tipo_linha})


def _desenhar_perfil(
    espaco_modelo: Any, entradas_talude: dict[str, Any], resultado_talude: dict[str, Any]
) -> None:
    pontos_perfil = resultado_talude["perfil_terreno"]
    espaco_modelo.add_lwpolyline(
        [(ponto["x_m"], ponto["cota_y_m"]) for ponto in pontos_perfil],
        dxfattribs={"layer": "TERRENO"},
    )

    x_minimo_m = float(entradas_talude["limite_x_grafico_minimo_m"])
    x_maximo_m = float(entradas_talude["limite_x_grafico_maximo_m"])
    cota_interface_m = float(resultado_talude["geometria"]["cota_interface_camadas_m"])
    espaco_modelo.add_line(
        (x_minimo_m, cota_interface_m),
        (x_maximo_m, cota_interface_m),
        dxfattribs={"layer": "CAMADAS"},
    )
    _adicionar_texto(
        espaco_modelo,
        "Interface das camadas",
        (x_minimo_m + 0.25, cota_interface_m + 0.12),
        max(0.18, float(entradas_talude["altura_talude_m"]) * 0.025),
        "CAMADAS",
    )

    cota_nivel_agua_m = resultado_talude["geometria"]["cota_nivel_agua_m"]
    if cota_nivel_agua_m is not None:
        espaco_modelo.add_line(
            (x_minimo_m, cota_nivel_agua_m),
            (x_maximo_m, cota_nivel_agua_m),
            dxfattribs={"layer": "NIVEL_AGUA"},
        )
        _adicionar_texto(
            espaco_modelo,
            "Nivel d'agua",
            (x_minimo_m + 0.25, cota_nivel_agua_m + 0.12),
            max(0.18, float(entradas_talude["altura_talude_m"]) * 0.025),
            "NIVEL_AGUA",
        )


def _desenhar_circulo_critico(espaco_modelo: Any, circulo: dict[str, Any]) -> None:
    x_saida_m = float(circulo["x_saida_m"])
    x_entrada_m = float(circulo["x_entrada_m"])
    centro_x_m = float(circulo["centro_x_m"])
    centro_y_m = float(circulo["centro_y_m"])
    raio_m = float(circulo["raio_m"])

    quantidade_pontos_arco = 121
    pontos_arco = []
    for indice_ponto in range(quantidade_pontos_arco):
        coordenada_x_m = x_saida_m + indice_ponto * (x_entrada_m - x_saida_m) / (
            quantidade_pontos_arco - 1
        )
        radicando_arco = max(0.0, raio_m**2 - (coordenada_x_m - centro_x_m) ** 2)
        coordenada_y_m = centro_y_m - radicando_arco**0.5
        pontos_arco.append((coordenada_x_m, coordenada_y_m))
    espaco_modelo.add_lwpolyline(
        pontos_arco, dxfattribs={"layer": "CIRCULO_CRITICO"}
    )
    espaco_modelo.add_circle(
        (centro_x_m, centro_y_m),
        max(0.025, raio_m * 0.008),
        dxfattribs={"layer": "CENTRO_CIRCULO"},
    )
    espaco_modelo.add_line(
        (centro_x_m - raio_m * 0.015, centro_y_m),
        (centro_x_m + raio_m * 0.015, centro_y_m),
        dxfattribs={"layer": "CENTRO_CIRCULO"},
    )
    espaco_modelo.add_line(
        (centro_x_m, centro_y_m - raio_m * 0.015),
        (centro_x_m, centro_y_m + raio_m * 0.015),
        dxfattribs={"layer": "CENTRO_CIRCULO"},
    )


def _desenhar_fatias(
    espaco_modelo: Any,
    resultado_talude: dict[str, Any],
    fatias: list[dict[str, Any]],
    circulo: dict[str, Any],
) -> float:
    """Desenha a geometria real e, abaixo, os trapézios usados no cálculo das áreas."""
    pontos_perfil = resultado_talude["perfil_terreno"]
    menor_cota_desenho_m = min(ponto["cota_y_m"] for ponto in pontos_perfil)
    menor_cota_desenho_m = min(
        menor_cota_desenho_m,
        *(fatia["cota_base_m"] for fatia in fatias if fatia["cota_base_m"] is not None),
    )
    centro_x_m = float(circulo["centro_x_m"])
    centro_y_m = float(circulo["centro_y_m"])
    raio_m = float(circulo["raio_m"])
    menor_cota_desenho_m = min(menor_cota_desenho_m, centro_y_m - raio_m)
    maior_cota_desenho_m = max(
        centro_y_m, *(ponto["cota_y_m"] for ponto in pontos_perfil)
    )
    deslocamento_area_m = maior_cota_desenho_m - menor_cota_desenho_m + max(
        2.0, (maior_cota_desenho_m - menor_cota_desenho_m) * 0.2
    )

    _adicionar_texto(
        espaco_modelo,
        "FATIAS GEOMETRICAS - SUPERFICIE CIRCULAR E PERFIL DO TERRENO",
        (pontos_perfil[0]["x_m"], maior_cota_desenho_m + 0.7),
        0.28,
        "FATIAS_GEOMETRIA",
    )
    for fatia in fatias:
        if fatia["cota_base_inicial_m"] is None or fatia["cota_base_final_m"] is None:
            continue
        pontos_superficie = [
            ponto
            for ponto in pontos_perfil
            if fatia["x_inicial_m"] < ponto["x_m"] < fatia["x_final_m"]
        ]
        pontos_superficie = [
            (fatia["x_inicial_m"], fatia["cota_topo_inicial_m"]),
            *[(ponto["x_m"], ponto["cota_y_m"]) for ponto in pontos_superficie],
            (fatia["x_final_m"], fatia["cota_topo_final_m"]),
        ]
        pontos_base = []
        quantidade_pontos_base = 21
        for indice_ponto in range(quantidade_pontos_base):
            x_m = fatia["x_final_m"] - indice_ponto * (
                fatia["x_final_m"] - fatia["x_inicial_m"]
            ) / (quantidade_pontos_base - 1)
            cota_base_m = centro_y_m - max(
                0.0, raio_m**2 - (x_m - centro_x_m) ** 2
            ) ** 0.5
            pontos_base.append((x_m, cota_base_m))
        espaco_modelo.add_lwpolyline(
            [*pontos_superficie, *pontos_base],
            close=True,
            dxfattribs={"layer": "FATIAS_GEOMETRIA"},
        )

    _adicionar_texto(
        espaco_modelo,
        "POLIGONOS FECHADOS PARA AREA - cordas usadas pela regra trapezoidal do calculo.",
        (pontos_perfil[0]["x_m"], menor_cota_desenho_m - deslocamento_area_m - 0.6),
        0.24,
        "AREA_CONFERENCIA",
    )
    for fatia in fatias:
        if fatia["situacao"] != "OK":
            continue
        vertices_area = [
            (fatia["x_inicial_m"], fatia["cota_topo_inicial_m"] - deslocamento_area_m),
            (fatia["x_final_m"], fatia["cota_topo_final_m"] - deslocamento_area_m),
            (fatia["x_final_m"], fatia["cota_base_final_m"] - deslocamento_area_m),
            (fatia["x_inicial_m"], fatia["cota_base_inicial_m"] - deslocamento_area_m),
        ]
        espaco_modelo.add_lwpolyline(
            vertices_area,
            close=True,
            dxfattribs={"layer": "AREA_CONFERENCIA"},
        )
        _adicionar_texto(
            espaco_modelo,
            f"{int(fatia['numero_fatia']):02d}",
            (fatia["x_medio_m"] - 0.08, menor_cota_desenho_m - deslocamento_area_m - 0.35),
            0.16,
            "AREA_CONFERENCIA",
        )
    return deslocamento_area_m


def _desenhar_cotas(
    espaco_modelo: Any, entradas_talude: dict[str, Any], resultado_talude: dict[str, Any]
) -> None:
    altura_talude_m = float(entradas_talude["altura_talude_m"])
    comprimento_horizontal_face_m = float(
        resultado_talude["geometria"]["comprimento_horizontal_face_m"]
    )
    coordenada_x_entrada_m = float(resultado_talude["geometria"]["coordenada_x_entrada_m"])
    cota_entrada_m = float(resultado_talude["geometria"]["cota_entrada_m"])
    escala_cota_m = max(0.18, altura_talude_m * 0.035)
    estilo_cota = {
        "dimtxt": escala_cota_m,
        "dimasz": escala_cota_m * 0.8,
        "dimexo": escala_cota_m * 0.25,
        "dimexe": escala_cota_m * 0.5,
        "dimgap": escala_cota_m * 0.3,
        "dimdec": 2,
        "dimlfac": 1,
        "dimtad": 1,
    }
    espaco_modelo.add_linear_dim(
        base=(0.0, -escala_cota_m * 2.5),
        p1=(0.0, 0.0),
        p2=(comprimento_horizontal_face_m, altura_talude_m),
        angle=0,
        override=estilo_cota,
        dxfattribs={"layer": "COTAS"},
    ).render()
    espaco_modelo.add_linear_dim(
        base=(-escala_cota_m * 2.5, 0.0),
        p1=(0.0, 0.0),
        p2=(0.0, altura_talude_m),
        angle=90,
        override=estilo_cota,
        dxfattribs={"layer": "COTAS"},
    ).render()
    espaco_modelo.add_linear_dim(
        base=(0.0, altura_talude_m + escala_cota_m * 2.5),
        p1=(comprimento_horizontal_face_m, altura_talude_m),
        p2=(coordenada_x_entrada_m, cota_entrada_m),
        angle=0,
        override=estilo_cota,
        dxfattribs={"layer": "COTAS"},
    ).render()


def _adicionar_memoria_completa(
    espaco_modelo: Any,
    entradas_talude: dict[str, Any],
    resultado_talude: dict[str, Any],
    circulo: dict[str, Any],
    deslocamento_area_m: float,
) -> None:
    geometria = resultado_talude["geometria"]
    altura_talude_m = float(entradas_talude["altura_talude_m"])
    x_memorial_m = float(entradas_talude["limite_x_grafico_maximo_m"]) + max(
        3.0, altura_talude_m * 0.6
    )
    y_memorial_m = altura_talude_m + max(2.0, altura_talude_m * 0.35)
    altura_texto_m = max(0.12, altura_talude_m * 0.018)
    linhas_memoria = _criar_linhas_memoria(
        entradas_talude, resultado_talude, circulo, deslocamento_area_m
    )
    conteudo_memoria = "\\P".join(linhas_memoria)
    espaco_modelo.add_mtext(
        conteudo_memoria,
        dxfattribs={
            "insert": (x_memorial_m, y_memorial_m),
            "char_height": altura_texto_m,
            "width": max(34.0, altura_talude_m * 5.0),
            "layer": "MEMORIAL",
        },
    )


def _criar_linhas_memoria(
    entradas_talude: dict[str, Any],
    resultado_talude: dict[str, Any],
    circulo: dict[str, Any],
    deslocamento_area_m: float,
) -> list[str]:
    geometria = resultado_talude["geometria"]
    altura_talude_m = float(entradas_talude["altura_talude_m"])
    relacao_horizontal_vertical = float(entradas_talude["relacao_horizontal_vertical_face"])
    comprimento_face_m = float(geometria["comprimento_horizontal_face_m"])
    distancia_entrada_m = float(entradas_talude["distancia_crista_entrada_m"])
    x_entrada_m = float(geometria["coordenada_x_entrada_m"])
    y_entrada_m = float(geometria["cota_entrada_m"])
    distancia_saida_m = float(entradas_talude["distancia_pe_saida_m"])
    distancia_entrada_saida_m = float(geometria["distancia_entre_entrada_e_saida_m"])
    raio_m = float(circulo["raio_m"])
    centro_x_m = float(circulo["centro_x_m"])
    centro_y_m = float(circulo["centro_y_m"])
    altura_centro_m = math.sqrt(raio_m**2 - (distancia_entrada_saida_m / 2) ** 2)
    fator_seguranca = float(circulo["fator_seguranca"])
    quantidade_fatias = int(entradas_talude["quantidade_fatias"])
    largura_fatia_m = distancia_entrada_saida_m / quantidade_fatias
    cota_nivel_agua_m = geometria["cota_nivel_agua_m"]
    if cota_nivel_agua_m is None:
        texto_nivel_agua = "sem nivel d'agua (u=0)"
        cota_nivel_agua_texto = "nao informado"
    else:
        texto_nivel_agua = f"yNA={float(cota_nivel_agua_m):.3f} m"
        cota_nivel_agua_texto = (
            f"zNA={float(entradas_talude['profundidade_nivel_agua_abaixo_crista_m']):.3f} m abaixo da crista"
        )

    linhas = [
        "MEMORIA COMPLETA - TALUDE | FELLENIUS (FATIAS ORDINARIAS)",
        "Unidades: m, m2, kN/m, kPa e graus; largura analisada por metro perpendicular ao corte.",
        f"GEOMETRIA: x_crista=H*m; x_entrada=x_crista+a; y_entrada=H+(x_entrada-x_crista)*tan(beta); beta={float(entradas_talude['inclinacao_terreno_montante_graus']):.3f} graus.",
        f"Substituicao: x_crista={altura_talude_m:.3f}*{relacao_horizontal_vertical:.3f}={comprimento_face_m:.3f} m; x_entrada={comprimento_face_m:.3f}+{distancia_entrada_m:.3f}={x_entrada_m:.3f} m; y_entrada={y_entrada_m:.3f} m.",
        f"d=sqrt((x_entrada+Lb)^2+y_entrada^2)=sqrt(({x_entrada_m:.3f}+{distancia_saida_m:.3f})^2+{y_entrada_m:.3f}^2)={distancia_entrada_saida_m:.3f} m.",
        "CIRCULO: h0=sqrt(R^2-(d/2)^2); xC=(xE-Lb)/2-(yE/d)*h0; yC=yE/2+((xE+Lb)/d)*h0.",
        f"Substituicao: h0=sqrt({raio_m:.3f}^2-({distancia_entrada_saida_m:.3f}/2)^2)={altura_centro_m:.3f} m; xC=({x_entrada_m:.3f}-{distancia_saida_m:.3f})/2-({y_entrada_m:.3f}/{distancia_entrada_saida_m:.3f})*{altura_centro_m:.3f}={centro_x_m:.3f} m; yC={y_entrada_m:.3f}/2+(({x_entrada_m:.3f}+{distancia_saida_m:.3f})/{distancia_entrada_saida_m:.3f})*{altura_centro_m:.3f}={centro_y_m:.3f} m.",
        f"FATIAS: b=d/n={distancia_entrada_saida_m:.3f}/{quantidade_fatias}={largura_fatia_m:.4f} m. As cotas y do painel AREA foram deslocadas {deslocamento_area_m:.3f} m apenas para separar o desenho.",
        "AREA CAD: cada polilinha fechada em AREA_CONFERENCIA e um trapezio com cordas entre as cotas de borda; AREA > Objeto deve retornar a soma das quatro areas do calculo.",
        "Area por fatia A=(b/2)*(h_esquerda+h_direita); as quatro parcelas sao camada 1 nao saturada/saturada e camada 2 nao saturada/saturada.",
        "PESO: W=A1n*gamma1n+A1s*gamma1sat+A2n*gamma2n+A2s*gamma2sat+q*b_crista.",
        f"PARAMETROS: camada 1 gamma={float(entradas_talude['peso_especifico_natural_camada_superior_kN_m3']):.3f}/{float(entradas_talude['peso_especifico_saturado_camada_superior_kN_m3']):.3f} kN/m3; c'={float(entradas_talude['coesao_efetiva_camada_superior_kPa']):.3f} kPa; phi'={float(entradas_talude['angulo_atrito_efetivo_camada_superior_graus']):.3f} graus.",
        f"PARAMETROS: camada 2 gamma={float(entradas_talude['peso_especifico_natural_camada_inferior_kN_m3']):.3f}/{float(entradas_talude['peso_especifico_saturado_camada_inferior_kN_m3']):.3f} kN/m3; c'={float(entradas_talude['coesao_efetiva_camada_inferior_kPa']):.3f} kPa; phi'={float(entradas_talude['angulo_atrito_efetivo_camada_inferior_graus']):.3f} graus.",
        f"CAMADAS: h1={float(entradas_talude['espessura_camada_superior_m']):.3f} m; interface y=H-h1={altura_talude_m:.3f}-{float(entradas_talude['espessura_camada_superior_m']):.3f}={float(geometria['cota_interface_camadas_m']):.3f} m.",
        "BASE: alpha_i=asin((x_i-xC)/R); alpha_m=(alpha_i+alpha_f)/2; L_arco=R*abs(alpha_f-alpha_i), angulos convertidos para radianos nas funcoes trigonometricas.",
        f"NIVEL D'AGUA: {cota_nivel_agua_texto}; u=gamma_w*max(0,yNA-y_base,medio); U=u*L_arco. {texto_nivel_agua}.",
        "FORCAS: N=W*cos(alpha_m); N'=N-U; FRc=c1'*L1+c2'*L2; FRphi=N'[(L1/L)*tan(phi1')+(L2/L)*tan(phi2')]. L1 e L2 sao os comprimentos do arco em cada camada.",
        "FR=FRc+FRphi; Fmob=W*sin(alpha_m); FS=sum(FR)/sum(Fmob). Forcas resistentes so somadas quando N' >= 0.",
        f"RESULTADO CRITICO {circulo['identificacao']}: R={raio_m:.4f} m; C=({centro_x_m:.4f}; {centro_y_m:.4f}) m; sum(FR)={float(circulo['resistencia_total_kN_m']):.4f} kN/m; sum(Fmob)={float(circulo['forca_mobilizada_total_kN_m']):.4f} kN/m; FS={float(circulo['resistencia_total_kN_m']):.4f}/{float(circulo['forca_mobilizada_total_kN_m']):.4f}={fator_seguranca:.5f}.",
        "MEMORIA POR FATIA (os valores intermediarios mantem as unidades indicadas acima):",
    ]
    for fatia in circulo["fatias"]:
        linhas.extend(_linhas_calculo_fatia(entradas_talude, fatia))
    linhas.append(
        "Observacao: desenho e memorial didaticos para conferencia; confirmar criterios, unidades e convencoes adotados no projeto."
    )
    return linhas


def _linhas_calculo_fatia(entradas_talude: dict[str, Any], fatia: dict[str, Any]) -> list[str]:
    numero_fatia = int(fatia["numero_fatia"])
    area_camada_superior_nao_saturada_m2 = float(fatia[CHAVES_AREAS_FATIA[0]])
    area_camada_superior_saturada_m2 = float(fatia[CHAVES_AREAS_FATIA[1]])
    area_camada_inferior_nao_saturada_m2 = float(fatia[CHAVES_AREAS_FATIA[2]])
    area_camada_inferior_saturada_m2 = float(fatia[CHAVES_AREAS_FATIA[3]])
    area_total_m2 = sum(float(fatia[chave]) for chave in CHAVES_AREAS_FATIA)
    peso_fatia_kN_m = float(fatia["peso_fatia_kN_m"])
    largura_crista_m = float(fatia["x_final_m"] - fatia["x_inicial_m"])
    sobrecarga_fatia_kN_m = float(fatia["sobrecarga_fatia_kN_m"])
    angulo_medio_graus = float(fatia["angulo_base_medio_graus"])
    comprimento_arco_m = float(fatia["comprimento_arco_m"])
    pressao_neutra_kPa = float(fatia["pressao_neutra_kPa"])
    resultante_pressao_neutra_kN_m = float(fatia["resultante_pressao_neutra_kN_m"])
    forca_normal_total_kN_m = float(fatia["forca_normal_total_kN_m"])
    forca_normal_efetiva_kN_m = float(fatia["forca_normal_efetiva_kN_m"])
    forca_resistente_coesao_kN_m = float(fatia["forca_resistente_coesao_kN_m"])
    forca_resistente_atrito_kN_m = float(fatia["forca_resistente_atrito_kN_m"])
    forca_resistente_kN_m = float(fatia["forca_resistente_kN_m"])
    forca_mobilizada_kN_m = float(fatia["forca_mobilizada_kN_m"])
    comprimento_camada_superior_m = float(fatia["comprimento_camada_superior_m"])
    comprimento_camada_inferior_m = float(fatia["comprimento_camada_inferior_m"])
    largura_arco_m = comprimento_camada_superior_m + comprimento_camada_inferior_m
    espessuras_iniciais_m = fatia["espessuras_componentes_inicial_m"]
    espessuras_finais_m = fatia["espessuras_componentes_final_m"]
    largura_fatia_m = float(fatia["x_final_m"] - fatia["x_inicial_m"])
    unidade_peso_agua_kN_m3 = float(entradas_talude["peso_especifico_agua_kN_m3"])
    sobrecarga_kPa = float(entradas_talude["sobrecarga_crista_kPa"])
    largura_sobrecarga_m = (
        sobrecarga_fatia_kN_m / sobrecarga_kPa if sobrecarga_kPa > 0 else 0.0
    )
    coesao_superior_kPa = float(entradas_talude["coesao_efetiva_camada_superior_kPa"])
    coesao_inferior_kPa = float(entradas_talude["coesao_efetiva_camada_inferior_kPa"])
    atrito_superior_graus = float(
        entradas_talude["angulo_atrito_efetivo_camada_superior_graus"]
    )
    atrito_inferior_graus = float(
        entradas_talude["angulo_atrito_efetivo_camada_inferior_graus"]
    )
    area_por_camadas = []
    nomes_areas = ("A1n", "A1s", "A2n", "A2s")
    for indice_area, nome_area in enumerate(nomes_areas):
        altura_esquerda_m = float(espessuras_iniciais_m[indice_area])
        altura_direita_m = float(espessuras_finais_m[indice_area])
        area_calculada_m2 = float(fatia[CHAVES_AREAS_FATIA[indice_area]])
        area_por_camadas.append(
            f"{nome_area}=(b/2)*(hE+hD)=({largura_fatia_m:.4f}/2)*({altura_esquerda_m:.4f}+{altura_direita_m:.4f})={area_calculada_m2:.4f} m2"
        )
    y_base_medio = float(fatia["cota_base_m"])
    if entradas_talude.get("profundidade_nivel_agua_abaixo_crista_m") is None:
        formula_pressao_neutra = "u=0 (sem nivel d'agua)"
    else:
        cota_nivel_agua_m = float(
            entradas_talude["altura_talude_m"]
            - float(entradas_talude["profundidade_nivel_agua_abaixo_crista_m"])
        )
        formula_pressao_neutra = (
            f"u={unidade_peso_agua_kN_m3:.3f}*max(0, {cota_nivel_agua_m:.3f}-{y_base_medio:.3f})"
            f"={pressao_neutra_kPa:.3f} kPa"
        )
    delta_angulo_rad = float(fatia["variacao_angular_rad"])
    raio_m = comprimento_arco_m / delta_angulo_rad if delta_angulo_rad else 0.0
    alfa_medio_rad = math.radians(angulo_medio_graus)

    return [
        f"F{numero_fatia:02d} | x=[{float(fatia['x_inicial_m']):.3f}; {float(fatia['x_final_m']):.3f}] m; topo=[{float(fatia['cota_topo_inicial_m']):.3f}; {float(fatia['cota_topo_final_m']):.3f}] m; base=[{float(fatia['cota_base_inicial_m']):.3f}; {float(fatia['cota_base_final_m']):.3f}] m; b={largura_crista_m:.4f} m.",
        f"AREAS: {'; '.join(area_por_camadas)}; Atotal={area_total_m2:.4f} m2.",
        f"W=({area_camada_superior_nao_saturada_m2:.4f}*{float(entradas_talude['peso_especifico_natural_camada_superior_kN_m3']):.3f}+{area_camada_superior_saturada_m2:.4f}*{float(entradas_talude['peso_especifico_saturado_camada_superior_kN_m3']):.3f}+{area_camada_inferior_nao_saturada_m2:.4f}*{float(entradas_talude['peso_especifico_natural_camada_inferior_kN_m3']):.3f}+{area_camada_inferior_saturada_m2:.4f}*{float(entradas_talude['peso_especifico_saturado_camada_inferior_kN_m3']):.3f}+Q)={peso_fatia_kN_m:.3f} kN/m; Q=q*Bcrista={sobrecarga_kPa:.3f}*{largura_sobrecarga_m:.3f}={sobrecarga_fatia_kN_m:.3f} kN/m.",
        f"alpha_i={float(fatia['angulo_base_inicial_graus']):.3f}; alpha_f={float(fatia['angulo_base_final_graus']):.3f}; alpha_m={angulo_medio_graus:.3f} graus; L=R*DeltaAlpha={raio_m:.4f}*{delta_angulo_rad:.5f}={comprimento_arco_m:.4f} m; L1={comprimento_camada_superior_m:.4f}; L2={comprimento_camada_inferior_m:.4f} m.",
        f"{formula_pressao_neutra}; U=u*L={pressao_neutra_kPa:.3f}*{comprimento_arco_m:.4f}={resultante_pressao_neutra_kN_m:.3f} kN/m; N=W*cos({angulo_medio_graus:.3f})={peso_fatia_kN_m:.3f}*{math.cos(alfa_medio_rad):.5f}={forca_normal_total_kN_m:.3f}; N'=N-U={forca_normal_total_kN_m:.3f}-{resultante_pressao_neutra_kN_m:.3f}={forca_normal_efetiva_kN_m:.3f} kN/m.",
        f"FRc={coesao_superior_kPa:.3f}*{comprimento_camada_superior_m:.4f}+{coesao_inferior_kPa:.3f}*{comprimento_camada_inferior_m:.4f}={forca_resistente_coesao_kN_m:.3f}; FRphi={forca_normal_efetiva_kN_m:.3f}*[{comprimento_camada_superior_m:.4f}/{largura_arco_m:.4f}*tan({atrito_superior_graus:.2f})+{comprimento_camada_inferior_m:.4f}/{largura_arco_m:.4f}*tan({atrito_inferior_graus:.2f})]={forca_resistente_atrito_kN_m:.3f}; FR={forca_resistente_coesao_kN_m:.3f}+{forca_resistente_atrito_kN_m:.3f}={forca_resistente_kN_m:.3f}; Fmob={peso_fatia_kN_m:.3f}*sin({angulo_medio_graus:.3f})={peso_fatia_kN_m:.3f}*{math.sin(alfa_medio_rad):.5f}={forca_mobilizada_kN_m:.3f} kN/m; situacao={fatia['situacao']}.",
    ]


def _adicionar_texto(
    espaco_modelo: Any,
    texto: str,
    ponto_insercao: tuple[float, float],
    altura_texto_m: float,
    nome_camada: str,
) -> None:
    espaco_modelo.add_text(
        texto,
        dxfattribs={
            "insert": ponto_insercao,
            "height": altura_texto_m,
            "layer": nome_camada,
        },
    )
