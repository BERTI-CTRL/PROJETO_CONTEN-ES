from io import StringIO
import unittest

import ezdxf

from contencoes.calculos_muro_de_arrimo import calcular_muro, carregar_exemplo_muro
from contencoes.exportar_muro_arrimo_dxf import gerar_desenho_muro_dxf


class ExportacaoMuroDXFTest(unittest.TestCase):
    def test_exporta_muro_cotado_pressao_e_resumo_de_calculo(self) -> None:
        entradas_muro, camadas_solo = carregar_exemplo_muro()
        resultado_muro = calcular_muro(entradas_muro, camadas_solo)

        arquivo_dxf = gerar_desenho_muro_dxf(
            entradas_muro, camadas_solo, resultado_muro
        )
        documento = ezdxf.read(StringIO(arquivo_dxf.decode("utf-8")))
        espaco_modelo = documento.modelspace()

        self.assertEqual(documento.header["$INSUNITS"], 6)
        self.assertEqual(len(espaco_modelo.query('LWPOLYLINE[layer=="MURO"]')), 1)
        self.assertEqual(len(espaco_modelo.query('LWPOLYLINE[layer=="PRESSAO_TOTAL"]')), 1)
        self.assertGreaterEqual(len(espaco_modelo.query("DIMENSION")), 3)
        hachuras_solo = [
            hachura
            for hachura in espaco_modelo.query("HATCH")
            if hachura.dxf.layer.startswith("SOLO_CAMADA_")
        ]
        self.assertEqual(len(hachuras_solo), 3)
        self.assertTrue(all(hachura.dxf.color == 256 for hachura in hachuras_solo))

        largura_base_m = float(entradas_muro["largura_base_m"])
        for hachura in hachuras_solo:
            vertices_hachura = [
                vertice
                for caminho in hachura.paths.paths
                for vertice in caminho.vertices
            ]
            self.assertTrue(vertices_hachura)
            self.assertGreaterEqual(
                min(vertice[0] for vertice in vertices_hachura), largura_base_m
            )

        linha_aterro = next(iter(espaco_modelo.query('LINE[layer=="ATERRO"]')))
        self.assertGreater(linha_aterro.dxf.start.x, largura_base_m)
        self.assertAlmostEqual(linha_aterro.dxf.end.x, largura_base_m)

        resumo = "\n".join(texto.dxf.text for texto in espaco_modelo.query("TEXT"))
        resumo += "\n" + "\n".join(texto.text for texto in espaco_modelo.query("MTEXT"))
        self.assertIn("RESUMO DO MURO", resumo)
        self.assertIn("FS contra tombamento", resumo)
        self.assertIn("Pressao maxima na base", resumo)

    def test_exporta_perfil_seco_com_uma_hachura_por_camada(self) -> None:
        entradas_muro, camadas_solo = carregar_exemplo_muro()
        entradas_muro["profundidade_nivel_agua_m"] = None
        resultado_muro = calcular_muro(entradas_muro, camadas_solo)

        arquivo_dxf = gerar_desenho_muro_dxf(
            entradas_muro, camadas_solo, resultado_muro
        )
        documento = ezdxf.read(StringIO(arquivo_dxf.decode("utf-8")))
        hachuras_solo = [
            hachura
            for hachura in documento.modelspace().query("HATCH")
            if hachura.dxf.layer.startswith("SOLO_CAMADA_")
        ]

        self.assertEqual(len(hachuras_solo), 2)
        self.assertTrue(
            all(hachura.dxf.layer.endswith("_NATURAL") for hachura in hachuras_solo)
        )


if __name__ == "__main__":
    unittest.main()
