"""Interfaz Streamlit para ecuaciones diferenciales separables."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.casos_prueba import CASOS_PRUEBA
from src.steps import NON_SEPARABLE_MSG, run_analysis

OUTPUT_DIR = Path(__file__).parent / "output"

st.set_page_config(
    page_title="Ecuaciones Separables",
    page_icon="📐",
    layout="wide",
)

st.title("Análisis de ecuaciones diferenciales separables")
st.markdown(
    "Ingrese una ecuación de primer orden en la forma "
    r"$\dfrac{dy}{dx} = F(x, y)$ con condición inicial $y(x_0) = y_0$."
)

# Sidebar
with st.sidebar:
    st.header("Entrada de datos")

    case_options = {c.name: c for c in CASOS_PRUEBA}
    selected_case_name = st.selectbox(
        "Casos de prueba",
        options=["Personalizado"] + list(case_options.keys()),
    )

    if selected_case_name != "Personalizado":
        case = case_options[selected_case_name]
        default_F = case.F
        default_x0 = case.x0
        default_y0 = case.y0
        default_a = case.a
        default_b = case.b
        st.info(case.description)
    else:
        default_F = "y/(1+x)"
        default_x0 = 0.0
        default_y0 = 2.0
        default_a = -0.5
        default_b = 3.0

    F_text = st.text_input(
        "F(x, y)",
        value=default_F,
        help="Ejemplos: y/(1+x), (x+1)**2, x*y + x",
    )
    col1, col2 = st.columns(2)
    with col1:
        x0 = st.number_input("x₀", value=float(default_x0), format="%.4f")
    with col2:
        y0 = st.number_input("y₀", value=float(default_y0), format="%.4f")

    col3, col4 = st.columns(2)
    with col3:
        a = st.number_input("a (inicio intervalo)", value=float(default_a), format="%.4f")
    with col4:
        b = st.number_input("b (fin intervalo)", value=float(default_b), format="%.4f")

    analyze = st.button("Analizar ecuación", type="primary", use_container_width=True)

st.markdown("---")

if analyze:
    case_label = (
        case_options[selected_case_name].id
        if selected_case_name != "Personalizado"
        else "custom"
    )

    with st.spinner("Analizando ecuación..."):
        result = run_analysis(F_text, x0, y0, a, b, OUTPUT_DIR, case_label)

    if not result.validation.valid:
        st.error(result.validation.message)
    elif result.stopped_reason == NON_SEPARABLE_MSG:
        st.warning(result.stopped_reason)
        for title, lines in result.sections.items():
            with st.expander(title, expanded=(title == "Clasificación")):
                for line in lines:
                    st.markdown(line)
    elif result.stopped_reason:
        st.error(result.stopped_reason)
        for title, lines in result.sections.items():
            with st.expander(title, expanded=True):
                for line in lines:
                    st.markdown(line)
    else:
        st.success("Análisis completado correctamente.")

        for title, lines in result.sections.items():
            with st.expander(title, expanded=(title in ("Clasificación", "Verificación", "Gráfica"))):
                for line in lines:
                    st.markdown(line)

        if result.plot_path and result.plot_path.exists():
            st.subheader("Gráfica de la solución particular")
            st.image(str(result.plot_path), use_container_width=True)
            with open(result.plot_path, "rb") as f:
                st.download_button(
                    "Descargar gráfica (PNG)",
                    data=f.read(),
                    file_name=result.plot_path.name,
                    mime="image/png",
                )
        elif result.plot_error:
            st.warning(result.plot_error)

else:
    st.info(
        "Seleccione un caso de prueba o ingrese sus datos en el panel lateral "
        "y pulse **Analizar ecuación**."
    )

    with st.bottom:
        st.caption("Aplicación académica desarrollada para el curso de Ecuaciones diferenciales de la Universidad del Tolima")
