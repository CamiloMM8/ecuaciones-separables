"""Casos de prueba obligatorios y caso propuesto del grupo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TestCase:
    id: str
    name: str
    F: str
    x0: float
    y0: float
    a: float
    b: float
    description: str = ""


CASOS_PRUEBA: list[TestCase] = [
    TestCase(
        id="1",
        name="Caso 1 — Separación básica",
        F="y/(1+x)",
        x0=0.0,
        y0=2.0,
        a=-0.9,
        b=3.0,
        description="dy/dx = y/(1+x), y(0) = 2",
    ),
    TestCase(
        id="2",
        name="Caso 2 — Función exclusiva de x",
        F="(x+1)**2",
        x0=0.0,
        y0=1.0,
        a=-1.0,
        b=2.0,
        description="dy/dx = (x+1)², y(0) = 1",
    ),
    TestCase(
        id="3",
        name="Caso 3 — Selección de una expresión",
        F="-x/y",
        x0=4.0,
        y0=-3.0,
        a=1.0,
        b=6.0,
        description="dy/dx = -x/y, y(4) = -3",
    ),
    TestCase(
        id="4",
        name="Caso 4 — Soluciones constantes",
        F="(y**2-1)/(x**2-1)",
        x0=2.0,
        y0=2.0,
        a=1.5,
        b=4.0,
        description="dy/dx = (y²-1)/(x²-1), y(2) = 2",
    ),
    TestCase(
        id="5",
        name="Caso 5 — Expresión factorizable",
        F="x*y + x",
        x0=0.0,
        y0=0.0,
        a=-1.0,
        b=2.0,
        description="dy/dx = xy + x, y(0) = 0",
    ),
    TestCase(
        id="6",
        name="Caso 6 — Ecuación no separable",
        F="y + sin(x)",
        x0=0.0,
        y0=1.0,
        a=-1.0,
        b=3.0,
        description="dy/dx = y + sin(x), y(0) = 1",
    ),
    TestCase(
        id="7",
        name="Caso 7 — Caso propuesto del grupo",
        F="2*x*y",
        x0=0.0,
        y0=3.0,
        a=-1.0,
        b=2.0,
        description="dy/dx = 2xy, y(0) = 3",
    ),
]


def get_case_by_id(case_id: str) -> TestCase | None:
    for case in CASOS_PRUEBA:
        if case.id == case_id:
            return case
    return None
