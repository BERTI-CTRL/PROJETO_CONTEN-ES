"""Botão de exportação dos cortes nas páginas de contenções."""

from collections.abc import Callable

from streamlit.delta_generator import DeltaGenerator


def mostrar_download_corte(
    painel: DeltaGenerator, nome: str, gerar_dxf: Callable[[], bytes] | None = None
) -> None:
    painel.download_button(
        "Baixar corte em DXF",
        data=gerar_dxf if gerar_dxf is not None else b"",
        file_name=f"{nome}.dxf",
        mime="application/dxf",
        key=f"dxf_{nome}",
        type="primary",
        on_click="ignore",
        disabled=gerar_dxf is None,
    )
    if gerar_dxf is None:
        painel.caption("Corrija os dados indicados abaixo para liberar o download.")
