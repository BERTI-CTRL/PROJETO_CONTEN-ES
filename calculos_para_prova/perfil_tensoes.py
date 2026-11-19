"""Tensoes verticais totais, neutras e efetivas em camadas horizontais."""


def calcular_tensoes_na_profundidade(profundidade, camadas, nivel_agua, gamma_agua=9.81):
    """Integra os pesos das camadas ate z e calcula u e sigma'v.

    Cada camada e uma tupla: (espessura_m, gamma_natural, gamma_saturado).
    γ vem em kN/m³, profundidade em m e as tensoes resultam em kPa.
    """
    sigma_v = 0.0
    topo = 0.0

    for espessura, gamma_natural, gamma_saturado in camadas:
        base = topo + espessura
        trecho = max(0.0, min(profundidade, base) - topo)
        altura_natural = max(0.0, min(trecho, nivel_agua - topo))
        altura_saturada = trecho - altura_natural
        sigma_v += gamma_natural * altura_natural + gamma_saturado * altura_saturada
        topo = base

    u = gamma_agua * max(0.0, profundidade - nivel_agua)
    return {"sigma_v": sigma_v, "u": u, "sigma_efetiva": sigma_v - u}


def calcular_perfil(camadas, nivel_agua, gamma_agua=9.81):
    """Retorna resultados na superficie, nas interfaces e no nivel d'agua."""
    profundidades = [0.0]
    profundidade = 0.0
    for espessura, _, _ in camadas:
        profundidade += espessura
        profundidades.append(profundidade)
    if 0.0 < nivel_agua < profundidade:
        profundidades.append(nivel_agua)

    resultados = []
    for z in sorted(set(profundidades)):
        tensoes = calcular_tensoes_na_profundidade(z, camadas, nivel_agua, gamma_agua)
        if z == 0:
            ponto = "Superficie"
        elif z == nivel_agua:
            ponto = "Nivel d'agua"
        else:
            ponto = f"Interface/base em z={z:g} m"
        resultados.append({"Ponto": ponto, "z (m)": z, **tensoes})
    return resultados
