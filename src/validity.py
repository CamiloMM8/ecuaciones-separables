"""Análisis del intervalo de validez de la solución."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import sympy as sp
from sympy.core.expr import Expr

from .latex_fmt import inline, labeled
from .parser import X, Y


@dataclass
class ValidityResult:
    """Intervalo de validez y restricciones detectadas."""

    interval: tuple[float, float]
    plot_interval: tuple[float, float]
    restrictions: list[str]
    singularities: list[float]
    message: str


def _collect_denominator_singularities(expr: Expr) -> list[Expr]:
    """Encuentra denominadores simbólicos en la expresión."""
    denoms: set[Expr] = set()

    def walk(e: Expr) -> None:
        if e.is_Atom:
            return
        if isinstance(e, sp.Pow) and e.exp.is_negative:
            denoms.add(e.base)
        if e.is_Mul or e.is_Add:
            num, den = sp.fraction(sp.together(e))
            if den != 1:
                denoms.add(den)
        for arg in e.args:
            walk(arg)

    walk(sp.together(expr))
    return list(denoms)


def _numeric_singularities(expr: Expr, x0: float, search_range: tuple[float, float]) -> list[float]:
    """Busca ceros de denominadores en un rango alrededor de x0."""
    singularities: list[float] = []
    a, b = search_range
    x_vals = np.linspace(a, b, 5000)

    for denom in _collect_denominator_singularities(expr):
        d_expr = denom
        if Y in d_expr.free_symbols:
            continue
        try:
            f = sp.lambdify(X, d_expr, modules=["numpy"])
            vals = f(x_vals)
            for i in range(len(x_vals) - 1):
                if np.isfinite(vals[i]) and np.isfinite(vals[i + 1]):
                    if vals[i] * vals[i + 1] <= 0:
                        # Refinar con bisección simple
                        lo, hi = x_vals[i], x_vals[i + 1]
                        for _ in range(40):
                            mid = (lo + hi) / 2
                            if f(lo) * f(mid) <= 0:
                                hi = mid
                            else:
                                lo = mid
                        singularities.append((lo + hi) / 2)
        except (TypeError, ValueError, ZeroDivisionError):
            continue

    return sorted(set(round(s, 6) for s in singularities))


def _max_interval_containing(
    x0: float,
    singularities: list[float],
    a: float,
    b: float,
) -> tuple[float, float]:
    """Mayor intervalo dentro de (a,b) que contiene x0 sin singularidades."""
    left_bounds = [a] + [s for s in singularities if s < x0]
    right_bounds = [s for s in singularities if s > x0] + [b]

    left = max(left_bounds) if left_bounds else a
    right = min(right_bounds) if right_bounds else b

    # Pequeño margen interior para evitar evaluar en singularidades
    eps = 1e-4 * max(abs(b - a), 1.0)
    left_open = left + eps if left < x0 else left
    right_open = right - eps if right > x0 else right

    if left_open >= right_open:
        return (x0 - eps, x0 + eps)

    return (left_open, right_open)


def analyze_validity(
    F: Expr,
    solution: Expr,
    x0: float,
    y0: float,
    a: float,
    b: float,
) -> ValidityResult:
    """Determina intervalo de validez intersectado con [a, b]."""
    restrictions: list[str] = []

    for denom in _collect_denominator_singularities(F):
        restrictions.append(
            labeled("F(x,y): denominador ≠ 0 →", sp.latex(denom) + r" \neq 0")
        )

    for denom in _collect_denominator_singularities(solution):
        if X in denom.free_symbols or not denom.free_symbols:
            restrictions.append(
                labeled("Solución: denominador ≠ 0 →", sp.latex(denom) + r" \neq 0")
            )

    for expr in sp.preorder_traversal(solution):
        if isinstance(expr, sp.log):
            restrictions.append(
                labeled("log requiere argumento > 0:", sp.latex(expr.args[0]) + r" > 0")
            )
        if expr.is_Pow and expr.exp == sp.S.Half:
            restrictions.append(
                labeled("√ requiere argumento ≥ 0:", sp.latex(expr.base) + r" \geq 0")
            )

    search = (min(a, x0) - abs(b - a), max(b, x0) + abs(b - a))
    singularities = _numeric_singularities(F, x0, search)
    singularities += _numeric_singularities(solution, x0, search)
    singularities = sorted(set(singularities))

    interval = _max_interval_containing(x0, singularities, a - 10, b + 10)
    plot_left = max(interval[0], a)
    plot_right = min(interval[1], b)
    if plot_left >= plot_right:
        plot_left, plot_right = a, b

    msg_parts = [
        f"Intervalo de validez (contiene x0 = {x0}): ({interval[0]:.4f}, {interval[1]:.4f})",
        f"Intervalo representado en la gráfica: [{plot_left:.4f}, {plot_right:.4f}]",
    ]
    if singularities:
        msg_parts.append(
            "Singularidades detectadas: "
            + ", ".join(f"x = {s:.4f}" for s in singularities)
        )

    return ValidityResult(
        interval=interval,
        plot_interval=(plot_left, plot_right),
        restrictions=restrictions,
        singularities=singularities,
        message=" | ".join(msg_parts),
    )
