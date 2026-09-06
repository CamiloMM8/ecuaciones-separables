"""Verificación de la solución particular."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp
from sympy.core.expr import Expr

from .parser import X, Y


@dataclass
class VerificationResult:
    """Resultado de verificar la solución."""

    ode_satisfied: bool
    ic_satisfied: bool
    derivative_check: Expr
    ic_check: Expr
    derivative_latex: str
    ic_latex: str
    message: str


def verify_solution(
    F: Expr,
    particular: Expr,
    x0: float,
    y0: float,
) -> VerificationResult:
    """Deriva la solución y comprueba la ecuación y la condición inicial."""
    dydx = sp.diff(particular, X)
    ode_residual = sp.simplify(dydx - F.subs(Y, particular))
    ic_residual = sp.simplify(particular.subs(X, x0) - y0)

    ode_ok = ode_residual == 0
    try:
        ode_num = float(sp.N(ode_residual.subs(X, x0)))
        ode_ok = ode_ok or abs(ode_num) < 1e-6
    except (TypeError, ValueError):
        pass

    ic_ok = ic_residual == 0
    try:
        ic_num = float(sp.N(ic_residual))
        ic_ok = ic_ok or abs(ic_num) < 1e-6
    except (TypeError, ValueError):
        pass

    parts = []
    if ode_ok:
        parts.append("✓ La derivada de la solución satisface dy/dx = F(x, y).")
    else:
        parts.append("✗ La derivada no coincide con F(x, y) en forma simbólica.")

    if ic_ok:
        parts.append(f"✓ y({x0}) = {y0} se cumple.")
    else:
        parts.append(f"✗ La condición inicial y({x0}) = {y0} no se cumple.")

    return VerificationResult(
        ode_satisfied=ode_ok,
        ic_satisfied=ic_ok,
        derivative_check=ode_residual,
        ic_check=ic_residual,
        derivative_latex=sp.latex(ode_residual),
        ic_latex=sp.latex(ic_residual),
        message=" ".join(parts),
    )
