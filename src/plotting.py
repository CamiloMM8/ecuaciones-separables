"""Generación de gráficas de la solución particular."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
from sympy.core.expr import Expr

from .parser import X


def plot_solution(
    F_text: str,
    solution: Expr,
    x0: float,
    y0: float,
    plot_interval: tuple[float, float],
    output_dir: Path,
    case_label: str = "caso",
) -> tuple[Path | None, str | None]:
    """
    Genera gráfica de la solución particular en el intervalo válido.
    Retorna (ruta_png, mensaje_error).
    """
    a, b = plot_interval
    if a >= b:
        return None, "Intervalo de gráfica inválido."

    x_vals = np.linspace(a, b, 500)
    try:
        f = sp.lambdify(X, solution, modules=["numpy"])
        y_vals = f(x_vals)
    except (TypeError, ValueError) as exc:
        return None, f"No se pudo evaluar la solución numéricamente: {exc}"

    y_vals = np.asarray(y_vals, dtype=float)
    mask = np.isfinite(y_vals)
    if not np.any(mask):
        return None, "La solución no tiene valores finitos en el intervalo."

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x_vals[mask], y_vals[mask], "b-", linewidth=2, label="Solución particular")
    ax.plot(x0, y0, "ro", markersize=10, label=f"Punto inicial ({x0}, {y0})")

    ax.set_xlabel("x", fontsize=12)
    ax.set_ylabel("y", fontsize=12)
    ax.set_title(f"dy/dx = {F_text}\nIntervalo: [{a:.3f}, {b:.3f}]", fontsize=11)
    ax.grid(True, alpha=0.4)
    ax.legend(loc="best")
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.axvline(0, color="gray", linewidth=0.5)

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in case_label)
    filepath = output_dir / f"grafica_{safe_label}.png"
    fig.tight_layout()
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return filepath, None
