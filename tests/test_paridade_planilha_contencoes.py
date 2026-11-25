"""Casos de conferência das abas Estaca-prancha e Talude da planilha atual."""

import unittest

from contencoes.calculos.calculos_estabilidade_taludes import (
    calcular_estabilidade_talude,
    carregar_exemplo_talude,
)
from contencoes.calculos.calculos_estaca_prancha import (
    calcular_cortina_ancorada,
    carregar_exemplos_estaca_prancha,
)


class ParidadePlanilhaTest(unittest.TestCase):
    def test_cortina_ancorada_inclui_resultante_e_momento_da_agua(self):
        entradas = carregar_exemplos_estaca_prancha()["cortina_ancorada"]
        entradas.update(
            sobrecarga_superficie_kPa=8.0,
            espessura_camada_superior_ate_na_m=2.5,
            peso_especifico_solo_superior_kN_m3=18.0,
            peso_especifico_solo_submerso_kN_m3=10.0,
            profundidade_na_ate_escavacao_m=3.0,
            ficha_abaixo_escavacao_m=2.5,
            angulo_atrito_solo_graus=32.0,
            altura_ancoragem_acima_na_m=0.7,
            percentual_passivo_mobilizado=80.0,
            fator_seguranca_minimo_tombamento=1.3,
            peso_especifico_agua_kN_m3=9.81,
        )
        resultado = calcular_cortina_ancorada(entradas)
        self.assertAlmostEqual(resultado["empuxo_hidrostatico_kN_m"], 148.37625)
        self.assertAlmostEqual(resultado["momento_hidrostatico_kNm_m"], 647.909625)
        self.assertAlmostEqual(resultado["forca_tirante_kN_m"], 226.47871664466453)
        self.assertAlmostEqual(resultado["fator_seguranca_tombamento"], 0.37833371268902294)
        self.assertEqual(resultado["status_tombamento"], "REVER")

        entradas["peso_especifico_agua_kN_m3"] = 0
        sem_diferencial = calcular_cortina_ancorada(entradas)
        self.assertEqual(sem_diferencial["empuxo_hidrostatico_kN_m"], 0)
        self.assertAlmostEqual(sem_diferencial["forca_tirante_kN_m"], 78.10246664466456)
        self.assertAlmostEqual(sem_diferencial["fator_seguranca_tombamento"], 0.8625339117017244)

    def test_bishop_seleciona_seu_proprio_critico(self):
        entradas = carregar_exemplo_talude()
        entradas.update(
            altura_talude_m=7.0,
            relacao_horizontal_vertical_face=1.0,
            distancia_crista_entrada_m=4.0,
            espessura_camada_superior_m=4.0,
            profundidade_nivel_agua_abaixo_crista_m=5.8,
            sobrecarga_crista_kPa=12.0,
            quantidade_fatias=16,
            coesao_efetiva_camada_superior_kPa=8.0,
            angulo_atrito_efetivo_camada_superior_graus=32.0,
            coesao_efetiva_camada_inferior_kPa=3.0,
            angulo_atrito_efetivo_camada_inferior_graus=28.0,
            raios_candidatos_m=[6.73145600891813 + i for i in range(10)],
        )
        resultado = calcular_estabilidade_talude(entradas)
        self.assertIsNone(resultado["circulo_critico"])

        critico = resultado["circulo_critico_bishop"]
        self.assertEqual(critico["identificacao"], "R06")
        self.assertEqual(critico["bishop"]["iteracoes"], 7)
        self.assertAlmostEqual(critico["bishop"]["fator_seguranca"], 1.0931450820728623)
        for invalido in resultado["circulos"][6:]:
            self.assertIsNone(invalido["bishop"]["fator_seguranca"])
            self.assertEqual(invalido["bishop"]["situacao"], "GEOMETRIA INVÁLIDA")
