"""Desenha varios circulos de Mohr, a envoltoria e a trajetoria p-q."""

from math import ceil, floor, radians, tan

import matplotlib.pyplot as plt
from matplotlib.patches import Circle


def calcular_ponto_pq(centro, raio):
    """O topo do circulo e (p, q) = (centro, raio)."""
    return centro, raio


def calcular_envoltoria(sigma, coesao, phi_graus):
    """Envoltoria linear de Mohr-Coulomb: tau_f = c + sigma*tan(phi)."""
    return coesao + sigma * tan(radians(phi_graus))


def calcular_tensoes_principais(centro, raio):
    return centro + raio, centro - raio


def desenhar(centros, raios, coesao, phi_graus, mostrar_envoltoria=True, mostrar_pq=True):
    """Retorna uma figura grande para círculos e outra para a trajetória p-q."""
    fig_mohr, ax_mohr = plt.subplots(figsize=(10, 8))
    cores = plt.get_cmap("tab10").colors
    menor_sigma = min(c - r for c, r in zip(centros, raios))
    maior_sigma = max(c + r for c, r in zip(centros, raios))
    margem = max((maior_sigma - menor_sigma) * 0.12, 5)
    sigmas = [menor_sigma - margem + i * (maior_sigma - menor_sigma + 2 * margem) / 100
              for i in range(101)]
    a_envoltoria = tan(radians(phi_graus))
    b_envoltoria = coesao
    taus = [calcular_envoltoria(sigma, coesao, phi_graus) for sigma in sigmas]

    for i, (centro, raio) in enumerate(zip(centros, raios)):
        cor = cores[i % len(cores)]
        ax_mohr.add_patch(Circle((centro, 0), raio, fill=False, color=cor, linewidth=2,
                                 label=f"C{i + 1}: centro={centro:g}, raio={raio:g}"))
        ax_mohr.scatter(centro, raio, color=cor, s=25)
        ax_mohr.scatter(centro, -raio, color=cor, s=25)

    if mostrar_envoltoria:
        ax_mohr.plot(
            sigmas, taus, color="crimson",
            label=f"Envoltória: τ={a_envoltoria:.3f}σ+{b_envoltoria:.3f}",
        )
        ax_mohr.plot(
            sigmas, [-tau for tau in taus], color="crimson", linestyle="--",
            label=f"Inferior: τ={-a_envoltoria:.3f}σ{-b_envoltoria:+.3f}",
        )
    ax_mohr.axhline(0, color="black", linewidth=0.8)
    limite_sigma = ceil((maior_sigma + margem) / 25) * 25
    ax_mohr.set_xlim(0, limite_sigma)
    maior_tau = max(max(raios), max(abs(tau) for tau in taus)) + margem
    limite_tau = ceil(maior_tau / 25) * 25
    ax_mohr.set_ylim(-limite_tau, limite_tau)
    ax_mohr.set_aspect("equal", adjustable="box")
    ax_mohr.set_xlabel(r"Tensao normal $\sigma$ (kPa)")
    ax_mohr.set_ylabel(r"Tensao cisalhante $\tau$ (kPa)")
    ax_mohr.set_title("Circulos e envoltoria")
    ax_mohr.grid(alpha=0.2)
    ax_mohr.set_xticks(range(0, limite_sigma + 1, 25))
    ax_mohr.set_yticks(range(-limite_tau, limite_tau + 1, 25))
    pontos_pq = [calcular_ponto_pq(c, r) for c, r in zip(centros, raios)]
    p = [ponto[0] for ponto in pontos_pq]
    q = [ponto[1] for ponto in pontos_pq]
    if mostrar_pq and len(p) > 1:
        if p[-1] != p[0]:
            a_pq = (q[-1] - q[0]) / (p[-1] - p[0])
            b_pq = q[0] - a_pq * p[0]
            ax_mohr.plot(p, [a_pq * x + b_pq for x in p], "k--", linewidth=2,
                         label=f"P-Q: τ={a_pq:.3f}σ{b_pq:+.3f}")
        else:
            ax_mohr.plot([p[0], p[0]], [min(q), max(q)], "k--", linewidth=2,
                         label=f"P-Q: σ={p[0]:.3f}")
    ax_mohr.legend(fontsize=10)
    fig_pq, ax_pq = plt.subplots(figsize=(10, 7))
    ax_pq.plot(p, q, marker="o", color="#1769aa", label="Trajetoria pelos topos")
    if len(p) > 1:
        if p[-1] != p[0]:
            a_pq = (q[-1] - q[0]) / (p[-1] - p[0])
            b_pq = q[0] - a_pq * p[0]
            legenda_pq = f"P-Q: q={a_pq:.3f}p{b_pq:+.3f}"
        else:
            legenda_pq = f"P-Q: p={p[0]:.3f}"
        ax_pq.plot([p[0], p[-1]], [q[0], q[-1]], linestyle="--", color="crimson",
                   linewidth=2, label=legenda_pq)
    for i, (pi_i, qi_i) in enumerate(pontos_pq):
        nome = "P" if i == 0 else "Q" if i == len(pontos_pq) - 1 else f"{i + 1}"
        ax_pq.annotate(nome, (pi_i, qi_i), xytext=(5, 5), textcoords="offset points")

    ax_pq.set_xlabel(r"$p=(\sigma_1+\sigma_3)/2$ (kPa)")
    ax_pq.set_ylabel(r"$q=(\sigma_1-\sigma_3)/2$ (kPa)")
    ax_pq.set_title("Trajetoria de tensoes p-q")
    ax_pq.grid(alpha=0.2)
    p_min, p_max = floor(min(p) / 25) * 25, ceil(max(p) / 25) * 25
    q_min, q_max = floor(min(q) / 25) * 25, ceil(max(q) / 25) * 25
    ax_pq.set_xticks(range(p_min, p_max + 1, 25))
    ax_pq.set_yticks(range(q_min, q_max + 1, 25))
    ax_pq.legend(fontsize=10)
    fig_mohr.tight_layout()
    fig_pq.tight_layout()
    return fig_mohr, fig_pq
