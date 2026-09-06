"""Parseo y validación de la ecuación diferencial y condiciones iniciales."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import sympy as sp
from sympy.core.expr import Expr

X, Y = sp.symbols("x y")
ALLOWED_SYMBOLS = {X, Y}


@dataclass
class ParsedInput:
    """Entrada validada del usuario."""

    F: Expr
    F_text: str
    x0: float
    y0: float
    a: float
    b: float


@dataclass
class ValidationResult:
    """Resultado de la validación."""

    valid: bool
    message: str
    parsed: Optional[ParsedInput] = None


def parse_expression(expr_text: str) -> tuple[Optional[Expr], Optional[str]]:
    """Convierte texto a expresión SymPy con variables x e y."""
    text = expr_text.strip()
    if not text:
        return None, "La expresión F(x, y) no puede estar vacía."

    local_dict = {"x": X, "y": Y}
    try:
        from sympy.parsing.sympy_parser import (
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )

        transformations = standard_transformations + (
            implicit_multiplication_application,
        )
        expr = parse_expr(text, local_dict=local_dict, transformations=transformations)
    except (sp.SympifyError, TypeError, SyntaxError, ValueError) as exc:
        return None, f"Sintaxis inválida en F(x, y): {exc}"

    if not isinstance(expr, Expr):
        return None, "F(x, y) debe ser una expresión matemática válida."

    free = expr.free_symbols
    disallowed = free - ALLOWED_SYMBOLS
    if disallowed:
        names = ", ".join(sorted(str(s) for s in disallowed))
        return None, f"Variables no permitidas: {names}. Solo se admiten x e y."

    return expr, None


def _is_finite_at(expr: Expr, x_val: float, y_val: float) -> tuple[bool, Optional[str]]:
    """Comprueba que la expresión esté definida en (x0, y0)."""
    try:
        value = complex(sp.N(expr.subs({X: x_val, Y: y_val})))
    except (TypeError, ValueError, ZeroDivisionError, sp.SympifyError) as exc:
        return False, f"F(x, y) no está definida en ({x_val}, {y_val}): {exc}"

    if value.real != value.real or value.imag != value.imag:  # NaN check
        return False, f"F(x, y) no está definida en ({x_val}, {y_val})."

    if abs(value.imag) > 1e-9:
        return False, (
            f"F({x_val}, {y_val}) = {value} no es un valor real. "
            "Revise el dominio de la ecuación."
        )

    return True, None


def validate_input(
    F_text: str,
    x0: float,
    y0: float,
    a: float,
    b: float,
) -> ValidationResult:
    """Valida sintaxis, variables, intervalo y dominio en el punto inicial."""
    expr, err = parse_expression(F_text)
    if err:
        return ValidationResult(valid=False, message=err)

    if a >= b:
        return ValidationResult(
            valid=False,
            message=f"El intervalo gráfico requiere a < b. Recibido: [{a}, {b}].",
        )

    if not (a <= x0 <= b):
        return ValidationResult(
            valid=False,
            message=(
                f"La condición inicial exige x0 ∈ [a, b]. "
                f"Recibido: x0 = {x0}, intervalo [{a}, {b}]."
            ),
        )

    ok, domain_err = _is_finite_at(expr, x0, y0)
    if not ok:
        return ValidationResult(valid=False, message=domain_err or "Dominio inválido.")

    return ValidationResult(
        valid=True,
        message="Entrada válida: sintaxis correcta, variables permitidas, "
        f"x0 = {x0} ∈ [{a}, {b}] y F({x0}, {y0}) está definida.",
        parsed=ParsedInput(F=expr, F_text=F_text.strip(), x0=x0, y0=y0, a=a, b=b),
    )
