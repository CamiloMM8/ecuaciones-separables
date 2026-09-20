"""Resolución por separación de variables (sin usar dsolve)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import sympy as sp
from sympy.core.expr import Expr

from .explicit_derivation import build_explicit_and_ic_steps
from .latex_fmt import bold_labeled, inline, labeled
from .parser import X, Y


C = sp.Symbol("C")


@dataclass
class ConstantSolution:
    """Solución constante y = c verificada."""

    value: Expr
    verified: bool
    check_message: str


@dataclass
class SolverResult:
    """Resultado completo del procedimiento de separación."""

    constant_solutions: list[ConstantSolution] = field(default_factory=list)
    separation_lhs: Optional[Expr] = None
    separation_rhs: Optional[Expr] = None
    integral_lhs: Optional[Expr] = None
    integral_rhs: Optional[Expr] = None
    implicit_general: Optional[Expr] = None
    explicit_general_branches: list[Expr] = field(default_factory=list)
    particular_solution: Optional[Expr] = None
    particular_branch_index: Optional[int] = None
    constant_value: Optional[Expr] = None
    steps: list[str] = field(default_factory=list)
    error: Optional[str] = None


def _find_constant_solutions(F: Expr, h: Expr) -> list[ConstantSolution]:
    """Resuelve h(y)=0 y verifica soluciones constantes en la ecuación original."""
    results: list[ConstantSolution] = []
    candidates = sp.solve(sp.Eq(h, 0), Y)

    for cand in candidates:
        if cand.has(X):
            continue
        lhs = sp.Integer(0)
        rhs = sp.simplify(F.subs(Y, cand))
        verified = sp.simplify(lhs - rhs) == 0
        if verified:
            msg = (
                f"{labeled('y =', sp.latex(cand))} satisface "
                f"{inline('dy/dx = 0 = F(x, ' + sp.latex(cand) + ')')}."
            )
        else:
            msg = (
                f"{labeled('y =', sp.latex(cand))} proviene de h(y)=0, pero no satisface "
                f"la ecuación original "
                f"{inline('0 \\neq F(x, ' + sp.latex(cand) + ')')}."
            )
        results.append(ConstantSolution(value=cand, verified=verified, check_message=msg))

    return results


def _integrate_side(expr: Expr, variable: sp.Symbol) -> Expr:
    return sp.integrate(expr, variable)


def _apply_initial_condition(
    branches: list[Expr],
    x0: float,
    y0: float,
) -> tuple[Optional[Expr], Optional[int], Optional[Expr]]:
    """Selecciona la rama que satisface y(x0) = y0 y calcula C."""
    C_sym = C

    for idx, branch in enumerate(branches):
        branch_at_x0 = sp.simplify(branch.subs(X, x0))

        if C_sym in branch_at_x0.free_symbols:
            c_solutions = sp.solve(sp.Eq(branch_at_x0, y0), C_sym)
            if not c_solutions:
                continue
            c_val = c_solutions[0]
            particular = sp.simplify(branch.subs(C_sym, c_val))
            return particular, idx, c_val

        try:
            val = float(sp.N(branch_at_x0))
            if abs(val - y0) < 1e-6:
                return branch_at_x0, idx, None
        except (TypeError, ValueError):
            if sp.simplify(branch_at_x0 - y0) == 0:
                return branch_at_x0, idx, None

    return None, None, None


def solve_separable(
    F: Expr,
    g: Expr,
    h: Expr,
    x0: float,
    y0: float,
) -> SolverResult:
    """Ejecuta separación de variables, integración y condición inicial."""
    result = SolverResult()
    steps: list[str] = []

    # Soluciones constantes
    result.constant_solutions = _find_constant_solutions(F, h)
    if result.constant_solutions:
        steps.append("**Soluciones constantes** (de h(y) = 0):")
        for cs in result.constant_solutions:
            status = "válida" if cs.verified else "descartada"
            steps.append(
                f"- {labeled('y =', sp.latex(cs.value))} ({status}): {cs.check_message}"
            )

    # Separación
    inv_h = sp.simplify(1 / h)
    result.separation_lhs = inv_h
    result.separation_rhs = g
    steps.append(
        "**Separación de variables:** "
        + inline(r"\frac{1}{h(y)}\,dy = g(x)\,dx")
        + " "
        + inline(
            rf"\Rightarrow \frac{{1}}{{{sp.latex(h)}}}\,dy = {sp.latex(g)}\,dx"
        )
    )

    # Integrales
    int_lhs = _integrate_side(inv_h, Y)
    int_rhs = _integrate_side(g, X)
    result.integral_lhs = int_lhs
    result.integral_rhs = int_rhs
    steps.append(
        "**Integración:** "
        + inline(r"\int \frac{1}{h(y)}\,dy = \int g(x)\,dx + C")
    )
    steps.append(
        inline(
            rf"\int {sp.latex(inv_h)}\,dy = \int {sp.latex(g)}\,dx + C "
            rf"\Rightarrow {sp.latex(int_lhs)} = {sp.latex(int_rhs)} + C"
        )
    )

    implicit = sp.Eq(int_lhs, int_rhs + C)
    result.implicit_general = implicit
    steps.append(
        bold_labeled("Solución general (implícita):", sp.latex(implicit))
    )

    # Forma explícita
    try:
        explicit_branches = sp.solve(implicit, Y)
    except (NotImplementedError, ValueError):
        explicit_branches = []

    if not explicit_branches:
        try:
            explicit_branches = sp.solve(sp.expand(int_lhs - int_rhs), Y)
        except (NotImplementedError, ValueError):
            explicit_branches = []

    result.explicit_general_branches = explicit_branches

    # Solución particular
    branches = explicit_branches if explicit_branches else []
    if not branches:
        # Intentar despejar numéricamente vía solve respecto a C y sustituir
        c_from_ic = sp.solve(sp.Eq(int_lhs.subs({Y: y0, X: x0}), int_rhs.subs(X, x0) + C), C)
        if c_from_ic:
            implicit_part = sp.Eq(int_lhs, int_rhs + c_from_ic[0])
            try:
                branches = sp.solve(implicit_part, Y)
            except (NotImplementedError, ValueError):
                branches = []

    particular, branch_idx, c_val = _apply_initial_condition(branches, x0, y0)

    if particular is None and branches:
        result.error = (
            f"Ninguna rama de la solución general satisface y({x0}) = {y0}."
        )
    elif particular is None:
        # Verificar si solución constante verificada coincide
        for cs in result.constant_solutions:
            if cs.verified and abs(float(sp.N(cs.value.subs(Y, y0) if cs.value.has(Y) else cs.value)) - y0) < 1e-6:
                particular = sp.Integer(cs.value) if cs.value.is_number else cs.value
                branch_idx = -1
                break

    result.particular_solution = particular
    result.particular_branch_index = branch_idx
    result.constant_value = c_val
    result.steps = steps

    if particular is not None and explicit_branches and branch_idx is not None:
        detailed = build_explicit_and_ic_steps(
            implicit, explicit_branches, branch_idx, x0, y0
        )
        steps.extend(detailed)
    elif particular is not None:
        steps.append(
            bold_labeled(
                "Solución particular:",
                f"y = {sp.latex(sp.simplify(particular))}",
            )
        )

    return result
