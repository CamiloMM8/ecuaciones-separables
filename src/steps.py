"""Orquestador del análisis completo de ecuaciones separables."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import sympy as sp

from .parser import ParsedInput, ValidationResult, validate_input
from .plotting import plot_solution
from .separable import SeparableResult, classify_separable
from .solver import SolverResult, solve_separable
from .validity import ValidityResult, analyze_validity
from .verification import VerificationResult, verify_solution

NON_SEPARABLE_MSG = (
    "La ecuación diferencial ingresada no es separable. "
    "El método de separación de variables no puede aplicarse."
)


@dataclass
class AnalysisResult:
    """Resultado completo del análisis."""

    validation: ValidationResult
    separable: Optional[SeparableResult] = None
    solver: Optional[SolverResult] = None
    validity: Optional[ValidityResult] = None
    verification: Optional[VerificationResult] = None
    plot_path: Optional[Path] = None
    plot_error: Optional[str] = None
    stopped_reason: Optional[str] = None
    sections: dict[str, list[str]] = field(default_factory=dict)


def _latex(expr) -> str:
    return sp.latex(expr)


def run_analysis(
    F_text: str,
    x0: float,
    y0: float,
    a: float,
    b: float,
    output_dir: Path,
    case_label: str = "custom",
) -> AnalysisResult:
    """Ejecuta el flujo completo de análisis."""
    result = AnalysisResult(validation=validate_input(F_text, x0, y0, a, b))
    sections: dict[str, list[str]] = {}

    sections["Validación"] = [result.validation.message]
    if not result.validation.valid or result.validation.parsed is None:
        result.sections = sections
        result.stopped_reason = result.validation.message
        return result

    parsed: ParsedInput = result.validation.parsed
    F = parsed.F

    # Clasificación
    sep = classify_separable(F)
    result.separable = sep
    sections["Simplificación y factorización"] = [
        rf"F(x, y) original: \({_latex(F)}\)",
        rf"F simplificada: \({_latex(sep.F_simplified)}\)",
        rf"F factorizada: \({_latex(sep.F_factored)}\)",
    ]

    sections["Clasificación"] = [sep.message]
    if not sep.is_separable:
        sections["Clasificación"].append(f"**{NON_SEPARABLE_MSG}**")
        result.sections = sections
        result.stopped_reason = NON_SEPARABLE_MSG
        return result

    assert sep.g is not None and sep.h is not None
    sections["Clasificación"].extend([
        rf"g(x) = {_latex(sep.g)}",
        rf"h(y) = {_latex(sep.h)}",
        rf"Verificación: g(x)·h(y) - F(x,y) = {_latex(sep.verification)}",
    ])

    # Resolución
    solver = solve_separable(F, sep.g, sep.h, parsed.x0, parsed.y0)
    result.solver = solver

    if solver.constant_solutions:
        cs_lines = []
        for cs in solver.constant_solutions:
            status = "✓" if cs.verified else "✗"
            cs_lines.append(f"{status} y = {_latex(cs.value)}: {cs.check_message}")
        sections["Soluciones constantes"] = cs_lines
    else:
        sections["Soluciones constantes"] = ["h(y) = 0 no produce soluciones constantes adicionales."]

    sections["Separación e integrales"] = list(solver.steps)

    if solver.error:
        sections["Solución particular"] = [f"**Error:** {solver.error}"]
        result.sections = sections
        result.stopped_reason = solver.error
        return result

    if solver.particular_solution is None:
        sections["Solución particular"] = ["No se pudo determinar la solución particular."]
        result.sections = sections
        result.stopped_reason = "No se pudo determinar la solución particular."
        return result

    # Validez
    validity = analyze_validity(
        F, solver.particular_solution, parsed.x0, parsed.y0, parsed.a, parsed.b
    )
    result.validity = validity
    sections["Intervalo de validez"] = [validity.message]
    if validity.restrictions:
        sections["Intervalo de validez"].append("**Restricciones:**")
        sections["Intervalo de validez"].extend(f"- {r}" for r in validity.restrictions[:8])

    # Verificación
    verification = verify_solution(F, solver.particular_solution, parsed.x0, parsed.y0)
    result.verification = verification
    sections["Verificación"] = [
        rf"Comprobación EDO: \(\frac{{dy}}{{dx}} - F(x,y) = {_latex(verification.derivative_check)}\)",
        rf"Comprobación CI: \(y({parsed.x0}) - {parsed.y0} = {_latex(verification.ic_check)}\)",
        verification.message,
    ]

    # Gráfica
    plot_path, plot_err = plot_solution(
        parsed.F_text,
        solver.particular_solution,
        parsed.x0,
        parsed.y0,
        validity.plot_interval,
        output_dir,
        case_label,
    )
    result.plot_path = plot_path
    result.plot_error = plot_err
    if plot_path:
        sections["Gráfica"] = [f"Gráfica guardada en: `{plot_path}`"]
    elif plot_err:
        sections["Gráfica"] = [f"No se pudo generar la gráfica: {plot_err}"]

    result.sections = sections
    return result
