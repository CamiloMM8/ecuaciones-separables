"""Pasos detallados: solución general explícita y condición inicial."""

from __future__ import annotations

from typing import Optional

import sympy as sp
from sympy.core.expr import Expr

from .latex_fmt import bold_labeled, inline, labeled
from .parser import X, Y

C = sp.Symbol("C")
K = sp.Symbol("K")


def _tex(expr: Expr | sp.Eq) -> str:
    if isinstance(expr, sp.Eq):
        return sp.latex(expr)
    return sp.latex(sp.simplify(expr))


def _split_add_with_c(expr: Expr) -> tuple[Expr, Expr]:
    if not expr.is_Add:
        if expr.has(C):
            return sp.Integer(0), expr
        return expr, sp.Integer(0)

    x_part = sp.Integer(0)
    c_part = sp.Integer(0)
    for term in expr.args:
        if term.has(C):
            c_part += term
        else:
            x_part += term
    return sp.simplify(x_part), sp.simplify(c_part)


def _unwrap_log(expr: Expr) -> tuple[bool, Expr]:
    if isinstance(expr, sp.log):
        return True, sp.simplify(expr.args[0])
    return False, expr


def _extract_k_multiplier_form(branch: Expr) -> tuple[Optional[Expr], Expr]:
    """
    Detecta y = K·g(x) + offset.
    Retorna (g(x), offset). offset=0 en el caso multiplicativo puro.
    """
    if not branch.has(C):
        return None, sp.Integer(0)

    # y = exp(C + expr) - p
    if branch.is_Add:
        terms = list(branch.args)
        exp_term = next((t for t in terms if isinstance(t, sp.exp)), None)
        if exp_term is not None:
            arg = exp_term.args[0]
            x_part, c_part = _split_add_with_c(arg)
            if c_part == C:
                offset = sp.simplify(sum(t for t in terms if t is not exp_term))
                return sp.exp(x_part), offset

    # y = (x+1)*exp(C)
    if branch.is_Mul:
        g = sp.Integer(1)
        for factor in sp.Mul.make_args(branch):
            if isinstance(factor, sp.exp):
                arg = factor.args[0]
                x_part, c_part = _split_add_with_c(arg)
                if c_part == C:
                    continue
            elif factor.has(C):
                return None, sp.Integer(0)
            else:
                g *= factor
        return sp.simplify(g), sp.Integer(0)

    # y = exp(C + expr)
    if isinstance(branch, sp.exp):
        arg = branch.args[0]
        x_part, c_part = _split_add_with_c(arg)
        if c_part == C:
            return sp.exp(x_part), sp.Integer(0)

    return None, sp.Integer(0)


def _derive_initial_condition_k_form(
    g_x: Expr,
    offset: Expr,
    x0: float,
    y0: float,
    branch: Expr,
    start_at: int = 7,
) -> list[str]:
    """Condición inicial para y = K·g(x) + offset (offset suele ser 0 o -p)."""
    steps: list[str] = []
    n = start_at
    at_x0 = sp.simplify(g_x.subs(X, x0))

    if offset == 0:
        general_tex = _tex(K * g_x)
    else:
        general_tex = _tex(K * g_x + offset)

    steps.append("**Aplicando la condición inicial:**")
    steps.append(
        f"{n}. Sustituimos {inline(f'y({x0}) = {y0}')} en "
        + labeled("y =", general_tex)
        + ":"
    )
    n += 1

    g_at_x0_tex = _tex(g_x.subs(X, x0))
    if offset == 0:
        steps.append(
            inline(f"{y0} = K \\cdot \\left({g_at_x0_tex}\\right)")
        )
        eq_at_x0 = sp.Eq(y0, K * at_x0)
    else:
        offset_at_x0 = sp.simplify(offset)
        steps.append(
            inline(
                f"{y0} = K \\cdot \\left({g_at_x0_tex}\\right) "
                f"+ \\left({ _tex(offset_at_x0) }\\right)"
            )
        )
        eq_at_x0 = sp.Eq(y0, K * at_x0 + offset)

    steps.append("   Simplificando: " + labeled("", _tex(eq_at_x0)))
    n += 1

    k_solutions = sp.solve(eq_at_x0, K)
    if not k_solutions:
        return steps

    k_val = sp.simplify(k_solutions[0])
    steps.append(f"{n}. Despejamos {inline('K')}: {labeled('K =', _tex(k_val))}")
    n += 1

    particular = sp.simplify(K * g_x + offset).subs(K, k_val)
    steps.append(
        f"{n}. Sustituimos "
        + inline(f"K = {_tex(k_val)}")
        + " en la solución general: "
        + labeled("y =", _tex(particular))
    )
    n += 1

    c_solutions = sp.solve(sp.Eq(sp.exp(C), k_val), C)
    if c_solutions:
        final = sp.simplify(branch.subs(C, c_solutions[0]))
    else:
        final = sp.simplify(particular)

    if sp.simplify(final - particular) != 0:
        steps.append(f"{n}. Simplificando: " + labeled("y =", _tex(final)))
    elif sp.expand(final) != final:
        steps.append(f"{n}. Simplificando: " + labeled("y =", _tex(sp.expand(final))))
        final = sp.expand(final)

    steps.append(bold_labeled("Solución particular:", f"y = {_tex(final)}"))
    return steps


def _derive_initial_condition_c_form(
    branch: Expr,
    x0: float,
    y0: float,
) -> list[str]:
    steps: list[str] = []
    steps.append("**Aplicando la condición inicial:**")

    if C not in branch.free_symbols:
        steps.append(
            f"La expresión seleccionada no depende de "
            + inline("C")
            + f". Se verifica {inline(f'y({x0})={y0}')} por sustitución directa."
        )
        return steps

    at_x0 = sp.simplify(branch.subs(X, x0))
    steps.append(
        f"1. Sustituimos {inline(f'y({x0}) = {y0}')} en "
        + labeled("y =", _tex(branch))
        + ":"
    )
    steps.append(labeled("", _tex(sp.Eq(y0, at_x0))))

    c_solutions = sp.solve(sp.Eq(at_x0, y0), C)
    if not c_solutions:
        return steps

    c_val = sp.simplify(c_solutions[0])
    steps.append(
        "2. Despejamos la constante de integración: "
        + labeled("C =", _tex(c_val))
    )
    steps.append(
        "   Esta "
        + inline("C")
        + " proviene directamente de la condición inicial "
        + "(no es un cambio "
        + inline("K = e^{C}")
        + " porque "
        + inline("y")
        + " ya estaba despejada linealmente)."
    )

    particular = sp.simplify(branch.subs(C, c_val))
    steps.append(
        "3. Sustituimos "
        + inline(f"C = {_tex(c_val)}")
        + ": "
        + labeled("y =", _tex(particular))
    )

    expanded = sp.expand(particular)
    if sp.simplify(expanded - particular) == 0 and expanded != particular:
        steps.append("4. Simplificando: " + labeled("y =", _tex(expanded)))
        particular = expanded

    steps.append(bold_labeled("Solución particular:", f"y = {_tex(particular)}"))
    return steps


def _derive_from_log_y(
    implicit: sp.Eq,
    branch: Expr,
    x0: float,
    y0: float,
) -> list[str]:
    lhs, rhs = implicit.lhs, implicit.rhs
    _, y_inner = _unwrap_log(lhs)
    x_part, _ = _split_add_with_c(rhs)
    g_x, offset = _extract_k_multiplier_form(branch)
    if g_x is None:
        g_x = _extract_k_multiplier_form(branch)[0] or sp.simplify(branch.subs(C, 0))

    steps: list[str] = []
    steps.append("**Solución general (explícita):**")
    steps.append(f"1. Partimos de la solución implícita: {inline(_tex(implicit))}")

    rhs_tex = _tex(x_part) + r" + C" if x_part != 0 else "C"
    steps.append(
        "2. Aplicamos la función exponencial en ambos lados: "
        + inline(rf"e^{{\ln({ _tex(y_inner) })}} = e^{{{rhs_tex}}}")
    )

    if x_part != 0:
        steps.append(
            "3. Usamos la propiedad "
            + inline(r"e^{a+b} = e^{a}\cdot e^{b}")
            + " en el lado derecho: "
            + inline(
                rf"e^{{\ln({ _tex(y_inner) })}} = e^{{{ _tex(x_part) }}}\cdot e^{{C}}"
            )
        )
        is_log_x, x_inner = _unwrap_log(x_part)
        if is_log_x:
            rhs_after = x_inner * sp.exp(C)
            steps.append(
                "4. Como "
                + inline(rf"e^{{\ln({ _tex(y_inner) })}} = {_tex(y_inner)}")
                + " y "
                + inline(rf"e^{{{ _tex(x_part) }}} = {_tex(x_inner)}")
                + ", obtenemos: "
                + inline(_tex(sp.Eq(y_inner, rhs_after)))
            )
        else:
            steps.append(
                "4. Como "
                + inline(rf"e^{{\ln({ _tex(y_inner) })}} = {_tex(y_inner)}")
                + ", obtenemos: "
                + inline(_tex(sp.Eq(y_inner, x_part * sp.exp(C))))
            )
    else:
        steps.append(
            "3. Como "
            + inline(rf"e^{{\ln({ _tex(y_inner) })}} = {_tex(y_inner)}")
            + ", queda: "
            + inline(_tex(sp.Eq(y_inner, sp.exp(C))))
        )

    steps.append(
        "5. Como "
        + inline("e^{C}")
        + " es una constante arbitraria, definimos "
        + inline("K = e^{C}")
        + ". Entonces: "
        + labeled("y =", _tex(K * g_x))
    )
    steps.append(
        "6. **Solución general explícita**: "
        + labeled("y =", _tex(K * g_x))
        + ". "
        + inline("K")
        + " es la nueva constante que reemplaza a "
        + inline("e^{C}")
        + "."
    )

    steps.extend(_derive_initial_condition_k_form(g_x, offset, x0, y0, branch, start_at=7))
    return steps


def _derive_from_log_shifted(
    implicit: sp.Eq,
    branch: Expr,
    x0: float,
    y0: float,
) -> list[str]:
    lhs, rhs = implicit.lhs, implicit.rhs
    _, log_arg = _unwrap_log(lhs)
    shift = sp.simplify(log_arg - Y)
    x_part, _ = _split_add_with_c(rhs)
    g_x, offset = _extract_k_multiplier_form(branch)
    if g_x is None:
        g_x = sp.exp(x_part)
        offset = sp.simplify(branch - sp.exp(C + x_part))

    steps: list[str] = []
    steps.append("**Solución general (explícita):**")
    steps.append(f"1. Partimos de: {inline(_tex(implicit))}")

    rhs_tex = _tex(x_part) + r" + C" if x_part != 0 else "C"
    steps.append(
        "2. Aplicamos exponencial en ambos lados: "
        + inline(rf"e^{{\ln({ _tex(log_arg) })}} = e^{{{rhs_tex}}}")
    )
    steps.append(
        "3. Usamos "
        + inline(r"e^{a+b}=e^{a}\cdot e^{b}")
        + ": "
        + inline(rf"{_tex(log_arg)} = e^{{{ _tex(x_part) }}}\cdot e^{{C}}")
    )
    steps.append(
        "4. Definimos "
        + inline("K = e^{C}")
        + " y despejamos "
        + inline("y")
        + ": "
        + labeled("y =", _tex(K * g_x + offset))
    )
    steps.append(
        "5. **Solución general explícita**: "
        + labeled("y =", _tex(K * g_x + offset))
    )

    steps.extend(_derive_initial_condition_k_form(g_x, offset, x0, y0, branch, start_at=6))
    return steps


def _derive_from_isolated_y(
    implicit: sp.Eq,
    branch: Expr,
    x0: float,
    y0: float,
) -> list[str]:
    steps: list[str] = []
    steps.append("**Solución general (explícita):**")
    steps.append(
        f"1. De {inline(_tex(implicit))}, la variable "
        + inline("y")
        + " ya está despejada."
    )
    steps.append(
        "2. **Solución general explícita**: "
        + labeled("y =", _tex(branch))
        + ", donde "
        + inline("C")
        + " es la constante de integración."
    )
    steps.extend(_derive_initial_condition_c_form(branch, x0, y0))
    return steps


def _derive_from_quadratic_y(
    implicit: sp.Eq,
    branches: list[Expr],
    branch_idx: int,
    x0: float,
    y0: float,
) -> list[str]:
    steps: list[str] = []
    lhs, rhs = implicit.lhs, implicit.rhs
    branch = sp.simplify(branches[branch_idx])

    steps.append("**Solución general (explícita):**")
    steps.append(f"1. Partimos de: {inline(_tex(implicit))}")

    if lhs == Y**2 / 2:
        ysqr = sp.simplify(2 * rhs)
        steps.append(
            "2. Multiplicamos ambos lados por 2: "
            + labeled("y^{2} =", _tex(ysqr))
        )

    steps.append(
        "3. Extraemos raíz cuadrada: "
        + inline(r"y = \pm \sqrt{\text{expresión en }x\text{ y }C}")
    )
    for i, br in enumerate(branches, 1):
        steps.append(f"   - Rama {i}: {labeled('y =', _tex(sp.simplify(br)))}")

    steps.append(
        f"4. Se trabajará con la **rama {branch_idx + 1}** al aplicar la condición inicial."
    )
    steps.extend(_derive_initial_condition_c_form(branch, x0, y0))
    return steps


def _classify_implicit(implicit: sp.Eq) -> str:
    lhs = implicit.lhs
    if lhs == Y:
        return "isolated_y"
    is_log, log_arg = _unwrap_log(lhs)
    if is_log:
        if sp.simplify(log_arg - Y) == 0:
            return "log_y"
        return "log_shifted"
    if lhs == Y**2 / 2 or lhs.has(Y**2):
        return "quadratic"
    return "generic"


def build_explicit_and_ic_steps(
    implicit: sp.Eq,
    branches: list[Expr],
    branch_idx: Optional[int],
    x0: float,
    y0: float,
) -> list[str]:
    if not branches or branch_idx is None or branch_idx < 0:
        return []

    branch = sp.simplify(branches[branch_idx])
    pattern = _classify_implicit(implicit)

    if pattern == "log_y":
        return _derive_from_log_y(implicit, branch, x0, y0)
    if pattern == "log_shifted":
        return _derive_from_log_shifted(implicit, branch, x0, y0)
    if pattern == "isolated_y":
        return _derive_from_isolated_y(implicit, branch, x0, y0)
    if pattern == "quadratic" and len(branches) > 1:
        return _derive_from_quadratic_y(implicit, branches, branch_idx, x0, y0)

    g_x, offset = _extract_k_multiplier_form(branch)
    steps = [
        "**Solución general (explícita):**",
        "Despejando "
        + inline("y")
        + " a partir de la solución implícita: "
        + labeled("y =", _tex(branch)),
    ]
    if g_x is not None:
        steps.extend(_derive_initial_condition_k_form(g_x, offset, x0, y0, branch))
    else:
        steps.extend(_derive_initial_condition_c_form(branch, x0, y0))
    return steps
