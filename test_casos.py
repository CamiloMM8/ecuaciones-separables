"""Script de prueba para los casos obligatorios."""

from pathlib import Path

from src.casos_prueba import CASOS_PRUEBA
from src.steps import NON_SEPARABLE_MSG, run_analysis

OUTPUT = Path(__file__).parent / "output"


def main() -> None:
    print("=" * 60)
    for case in CASOS_PRUEBA:
        print(f"\n{case.name}")
        print("-" * 40)
        result = run_analysis(
            case.F, case.x0, case.y0, case.a, case.b, OUTPUT, f"caso{case.id}"
        )

        if not result.validation.valid:
            print(f"  VALIDACIÓN FALLIDA: {result.validation.message}")
            continue

        if result.stopped_reason == NON_SEPARABLE_MSG:
            print(f"  OK (no separable): {result.stopped_reason}")
            continue

        if result.stopped_reason:
            print(f"  ERROR: {result.stopped_reason}")
            continue

        assert result.solver and result.solver.particular_solution is not None
        assert result.verification is not None
        print(f"  Separable: g={result.separable.g}, h={result.separable.h}")
        print(f"  Particular: {result.solver.particular_solution}")
        print(f"  Verificación EDO: {result.verification.ode_satisfied}")
        print(f"  Verificación CI: {result.verification.ic_satisfied}")
        print(f"  Intervalo: {result.validity.plot_interval if result.validity else 'N/A'}")
        print(f"  Gráfica: {result.plot_path}")

        if not result.verification.ode_satisfied or not result.verification.ic_satisfied:
            print("  *** FALLO EN VERIFICACIÓN ***")

    print("\n" + "=" * 60)
    print("Prueba de validación inválida (a >= b):")
    r = run_analysis("y", 0, 1, 2, 1, OUTPUT, "invalid")
    print(f"  {r.validation.message}")


if __name__ == "__main__":
    main()
