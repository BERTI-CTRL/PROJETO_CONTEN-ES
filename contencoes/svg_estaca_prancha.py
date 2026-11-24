"""Interface de importação dos croquis de estaca-prancha."""

from contencoes.svg_cortes_estaca_prancha import (
    gerar_svg_cortina_ancorada,
    gerar_svg_cortina_em_balanco,
)

__all__ = ["gerar_svg_cortina_ancorada", "gerar_svg_cortina_em_balanco"]
