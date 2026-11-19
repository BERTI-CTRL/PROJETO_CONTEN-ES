"""Regressao linear simples para a envoltoria de Mohr-Coulomb."""

from math import atan, degrees, sqrt


def media(valores):
    return sum(valores) / len(valores)


def calcular_SXX(x, xm):
    return sum((xi - xm) ** 2 for xi in x)


def calcular_SXY(x, y, xm, ym):
    return sum((xi - xm) * (yi - ym) for xi, yi in zip(x, y))


def calcular_SYY(y, ym):
    return sum((yi - ym) ** 2 for yi in y)


def calcular_a(SXX, SXY):
    return SXY / SXX


def calcular_b(xm, ym, a):
    return ym - a * xm


def calcular_ajustados(x, a, b):
    return [a * xi + b for xi in x]


def calcular_residuos(y, ajustados):
    return [yi - yhat for yi, yhat in zip(y, ajustados)]


def calcular_SQE(residuos):
    return sum(e**2 for e in residuos)


def calcular_R(SXX, SXY, SYY):
    return SXY / sqrt(SXX * SYY)


def calcular(x, y):
    """Junta o ajuste manual y retorna os termos e valores ajustados."""
    xm, ym = media(x), media(y)
    SXX = calcular_SXX(x, xm)
    SXY = calcular_SXY(x, y, xm, ym)
    SYY = calcular_SYY(y, ym)
    a = calcular_a(SXX, SXY)
    b = calcular_b(xm, ym, a)
    ajustados = calcular_ajustados(x, a, b)
    residuos = calcular_residuos(y, ajustados)
    SQE = calcular_SQE(residuos)
    SQR = SYY - SQE
    R = calcular_R(SXX, SXY, SYY)

    return {
        "a": a, "b": b, "c": b, "phi": degrees(atan(a)),
        "xm": xm, "ym": ym, "SXX": SXX, "SXY": SXY, "SYY": SYY,
        "SQT": SYY, "SQR": SQR, "SQReg": SQR, "SQE": SQE,
        "R": R, "R2": R**2,
        "ajustados": ajustados, "residuos": residuos,
    }
