"""Clasificación de ecuaciones separables: F(x,y) = g(x)*h(y)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import sympy as sp
from sympy.core.expr import Expr

from .latex_fmt import inline
from .parser import X, Y


@dataclass
class SeparableResult:
    """Resultado de la clasificación separable."""

    is_separable: bool
    F_original: Expr
    F_simplified: Expr
    F_factored: Expr
    g: Optional[Expr] = None
    h: Optional[Expr] = None
    message: str = ""
    verification: Optional[Expr] = None


def _depends_only_on(expr: Expr, var: sp.Symbol) -> bool:
    syms = expr.free_symbols
    return syms <= {var}


def _split_factors(expr: Expr) -> tuple[Optional[Expr], Optional[Expr], list[Expr]]:
    """
    Intenta escribir expr como producto de factor solo-x y factor solo-y.
    Retorna (g_part, h_part, mixed_factors).
    """
    factored = sp.factor(sp.together(expr))
    if factored == 0:
        return sp.Integer(0), sp.Integer(1), []

    factors = sp.Mul.make_args(factored)
    g_factors: list[Expr] = []
    h_factors: list[Expr] = []
    mixed: list[Expr] = []

    for factor in factors:
        syms = factor.free_symbols
        if not syms:
            g_factors.append(factor)
        elif syms <= {X}:
            g_factors.append(factor)
        elif syms <= {Y}:
            h_factors.append(factor)
        else:
            mixed.append(factor)

    if mixed:
        return None, None, mixed

    g_part = sp.Mul(*g_factors) if g_factors else sp.Integer(1)
    h_part = sp.Mul(*h_factors) if h_factors else sp.Integer(1)
    return g_part, h_part, []


def _try_separable_decomposition(expr: Expr) -> tuple[Optional[Expr], Optional[Expr]]:
    """Busca g(x) y h(y) tales que expr = g(x)*h(y)."""
    expr = sp.simplify(expr)

    if not expr.has(Y):
        return expr, sp.Integer(1)
    if not expr.has(X):
        return sp.Integer(1), expr

    num, den = sp.fraction(sp.together(expr))
    g_num, h_num, mixed_num = _split_factors(num)
    g_den, h_den, mixed_den = _split_factors(den)

    if mixed_num or mixed_den:
        refactored = sp.factor(expr)
        if refactored != expr:
            return _try_separable_decomposition(refactored)
        return None, None

    g = sp.simplify(g_num / g_den)
    h = sp.simplify(h_num / h_den)
    return g, h


def classify_separable(F: Expr) -> SeparableResult:
    """Simplifica, factoriza y determina si F(x,y) = g(x)*h(y)."""
    F_original = F
    F_simplified = sp.simplify(F)
    F_factored = sp.factor(F_simplified)

    g, h = _try_separable_decomposition(F_factored)

    if g is None or h is None:
        return SeparableResult(
            is_separable=False,
            F_original=F_original,
            F_simplified=F_simplified,
            F_factored=F_factored,
            message=(
                "No se encontró una descomposición F(x, y) = g(x)·h(y) "
                "con g dependiendo solo de x y h solo de y."
            ),
        )

    product = sp.simplify(g * h)
    verification = sp.simplify(product - F_simplified)

    if verification != 0:
        return SeparableResult(
            is_separable=False,
            F_original=F_original,
            F_simplified=F_simplified,
            F_factored=F_factored,
            message="La descomposición candidata no es equivalente a F(x, y).",
        )

    return SeparableResult(
        is_separable=True,
        F_original=F_original,
        F_simplified=F_simplified,
        F_factored=F_factored,
        g=g,
        h=h,
        verification=verification,
        message=(
            "La ecuación es separable: "
            f"{inline('F(x, y) = g(x) \\cdot h(y)')} con "
            f"{inline('g(x) = ' + sp.latex(g))} e "
            f"{inline('h(y) = ' + sp.latex(h))}."
        ),
    )
