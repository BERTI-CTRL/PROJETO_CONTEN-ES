"""Circulo de Mohr e construcao pelo polo, com grafico Matplotlib."""

from math import cos, radians, sin, sqrt, tan

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle


def calcular_C(sigma_v, sigma_h):
    return (sigma_v + sigma_h) / 2


def calcular_R(sigma_v, sigma_h, tau_h):
    return sqrt(((sigma_v - sigma_h) / 2) ** 2 + tau_h**2)


def calcular_sigma1(C, R):
    return C + R


def calcular_sigma3(C, R):
    return C - R


def calcular_polo(ponto_face_horizontal, ponto_face_vertical):
    """Cruza a horizontal da face horizontal com a vertical da face vertical."""
    sigma_do_ponto_vertical = ponto_face_vertical[0]
    tau_do_ponto_horizontal = ponto_face_horizontal[1]
    return sigma_do_ponto_vertical, tau_do_ponto_horizontal


def calcular_ponto_pelo_polo(C, polo, angulo):
    """Calcula o outro cruzamento da reta de angulo dado com o circulo."""
    unitario_x = cos(radians(angulo))
    unitario_y = sin(radians(angulo))
    # Q = P + distancia * u; essa distancia leva ao segundo cruzamento.
    distancia = -2 * ((polo[0] - C) * unitario_x + polo[1] * unitario_y)
    return (
        polo[0] + distancia * unitario_x,
        polo[1] + distancia * unitario_y,
    )


def calcular(sigma_v, sigma_h, tau_h, angulo):
    """Junta centro, raio, polo e tensoes no plano escolhido."""
    C = calcular_C(sigma_v, sigma_h)
    R = calcular_R(sigma_v, sigma_h, tau_h)
    ponto_face_horizontal = (sigma_v, tau_h)
    ponto_face_vertical = (sigma_h, -tau_h)
    polo = calcular_polo(ponto_face_horizontal, ponto_face_vertical)
    ponto = calcular_ponto_pelo_polo(C, polo, angulo)

    return {
        "C": C, "R": R,
        "sigma1": calcular_sigma1(C, R),
        "sigma3": calcular_sigma3(C, R),
        "polo": polo,
        "horizontal": ponto_face_horizontal,
        "vertical": ponto_face_vertical,
        "angulo": angulo,
        "ponto": ponto,
    }


def desenhar(resultado):
    """Desenha o circulo, o polo e o ponto encontrado pela reta escolhida."""
    C, R = resultado["C"], resultado["R"]
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.add_patch(Circle((C, 0), R, fill=False, color="#1769aa", linewidth=2,
                        label=f"Círculo: (σ−{C:.2f})²+τ²={R**2:.2f}"))
    ax.axhline(0, color="black", linewidth=0.8)
    ponto_horizontal = resultado["horizontal"]
    ponto_vertical = resultado["vertical"]
    polo = resultado["polo"]
    ponto_alvo = resultado["ponto"]
    if abs(cos(radians(resultado["angulo"]))) < 1e-10:
        equacao_reta = f"Reta pelo polo: σ = {polo[0]:.2f} kPa"
    else:
        inclinacao = tan(radians(resultado["angulo"]))
        intercepto = polo[1] - inclinacao * polo[0]
        equacao_reta = f"Reta: τ = {inclinacao:.3f}σ {intercepto:+.3f}"
    ax.plot(
        [ponto_horizontal[0], polo[0]],
        [ponto_horizontal[1], polo[1]],
        "--", color="gray", label="Horizontal pela face horizontal",
    )
    ax.plot(
        [ponto_vertical[0], polo[0]],
        [ponto_vertical[1], polo[1]],
        ":", color="#555555", label="Vertical pela face vertical",
    )
    ax.plot(
        [polo[0], ponto_alvo[0]],
        [polo[1], ponto_alvo[1]],
        "--", color="#e58b00", label=equacao_reta,
    )
    raio_arco = max(R * 0.18, 5)
    angulo = resultado["angulo"]
    # Uma reta representa a mesma orientação a cada 180 graus; mostra o
    # menor arco assinado entre a horizontal positiva e a reta P-Q.
    angulo_arco = (angulo + 90) % 180 - 90
    theta1, theta2 = (0, angulo_arco) if angulo_arco >= 0 else (angulo_arco, 0)
    ax.add_patch(Arc(polo, 2 * raio_arco, 2 * raio_arco, theta1=theta1,
                     theta2=theta2, color="#16804a", linewidth=2))
    ax.text(0.98, 0.97,
            f"α = {resultado['angulo']:g}°  (arco {angulo_arco:+g}°)",
            transform=ax.transAxes, ha="right", va="top", color="#16804a",
            bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "none"})

    pontos = [
        (f"Mₕ = ({ponto_horizontal[0]:.2f}, {ponto_horizontal[1]:.2f}) kPa", ponto_horizontal, "#16804a"),
        (f"Mᵥ = ({ponto_vertical[0]:.2f}, {ponto_vertical[1]:.2f}) kPa", ponto_vertical, "#bf3333"),
        (f"P = ({polo[0]:.2f}, {polo[1]:.2f}) kPa", polo, "#7541b8"),
        (f"Q = ({ponto_alvo[0]:.2f}, {ponto_alvo[1]:.2f}) kPa", ponto_alvo, "#e58b00"),
        (f"σ₁ = {resultado['sigma1']:.2f} kPa", (resultado["sigma1"], 0), "black"),
        (f"σ₃ = {resultado['sigma3']:.2f} kPa", (resultado["sigma3"], 0), "black"),
    ]
    for nome, (x, y), cor in pontos:
        ax.scatter(x, y, color=cor, zorder=3, label=nome)

    # Reserva espaço para o arco e a anotação de alpha em qualquer quadrante.
    margem = max(R * 0.35, 10)
    ax.set_xlim(C - R - margem, C + R + margem)
    ax.set_ylim(-R - margem, R + margem)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Tensão normal σ (kPa)")
    ax.set_ylabel("Tensão cisalhante τ (kPa)")
    ax.set_title(f"Círculo de Mohr — reta do polo a {resultado['angulo']:g}°")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1.02, 1.0))
    fig.tight_layout(rect=(0, 0, 0.70, 1))
    return fig
