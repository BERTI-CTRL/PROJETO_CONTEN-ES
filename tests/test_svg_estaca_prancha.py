import unittest

from contencoes.calculos_estaca_prancha import (
    calcular_cortina_ancorada,
    calcular_cortina_em_balanco,
    carregar_exemplos_estaca_prancha,
)
from contencoes.svg_estaca_prancha import (
    gerar_svg_cortina_ancorada,
    gerar_svg_cortina_em_balanco,
)


class GeracaoSVGEstacaPranchaTest(unittest.TestCase):
    def test_svg_em_balanco_mostra_cotas_e_todos_os_parametros_informados(self) -> None:
        entradas = carregar_exemplos_estaca_prancha()["cortina_em_balanco"]
        entradas.update(
            {
                "altura_livre_escavacao_m": 4.3,
                "peso_especifico_solo_kN_m3": 19.5,
                "angulo_atrito_solo_graus": 32.0,
                "percentual_passivo_mobilizado": 80.0,
                "percentual_acrescimo_ficha": 15.0,
            }
        )

        svg = gerar_svg_cortina_em_balanco(
            entradas, calcular_cortina_em_balanco(entradas)
        )

        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("h = 4,30 m", svg)
        self.assertIn("γ = 19,50 kN/m³", svg)
        self.assertIn("φ = 32,0°", svg)
        self.assertIn("Passivo mobilizado = 80,0% de Kₚ", svg)
        self.assertIn("Acréscimo prático da ficha = +15,0%", svg)
        self.assertIn("f teórica = ", svg)
        self.assertIn("f preliminar = ", svg)

    def test_svg_ancorado_mostra_geometria_solo_e_verificacao_informados(self) -> None:
        entradas = carregar_exemplos_estaca_prancha()["cortina_ancorada"]
        entradas.update(
            {
                "sobrecarga_superficie_kPa": 7.5,
                "espessura_camada_superior_ate_na_m": 2.4,
                "peso_especifico_solo_superior_kN_m3": 18.5,
                "peso_especifico_solo_submerso_kN_m3": 11.5,
                "profundidade_na_ate_escavacao_m": 3.2,
                "ficha_abaixo_escavacao_m": 2.7,
                "angulo_atrito_solo_graus": 28.0,
                "altura_ancoragem_acima_na_m": 0.6,
                "percentual_passivo_mobilizado": 75.0,
                "fator_seguranca_minimo_tombamento": 1.65,
            }
        )

        svg = gerar_svg_cortina_ancorada(
            entradas, calcular_cortina_ancorada(entradas)
        )

        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("q = 7,50 kPa", svg)
        self.assertIn("H₁ = 2,40 m", svg)
        self.assertIn("D = 3,20 m", svg)
        self.assertIn("f = 2,70 m", svg)
        self.assertIn("hₐ = 0,60 m", svg)
        self.assertIn("γ₁ = 18,50 · γ₂ = 11,50 kN/m³", svg)
        self.assertIn("φ = 28,0° · Kₚ mobilizado = 75,0%", svg)
        self.assertIn("FS mínimo ao tombamento = 1,65", svg)


if __name__ == "__main__":
    unittest.main()
