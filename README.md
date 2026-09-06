# Ecuaciones Diferenciales Separables

Programa para el análisis de ecuaciones diferenciales de primer orden separables.
Desarrollado para la asignatura de Ecuaciones Diferenciales — Ingeniería de Sistemas.

## Requisitos

- Python 3.10 o superior
- Dependencias listadas en `requirements.txt`

## Instalación

```powershell
python -m pip install -r requirements.txt
```

## Ejecución

```powershell
streamlit run app.py
```

Se abrirá una interfaz web en el navegador (por defecto `http://localhost:8501`).

## Uso

1. Ingrese la expresión `F(x, y)` de la ecuación `dy/dx = F(x, y)`.
2. Indique la condición inicial `y(x0) = y0` y el intervalo gráfico `[a, b]`.
3. Pulse **Analizar ecuación** o seleccione uno de los casos de prueba precargados.

El programa mostrará paso a paso:

- Validación de la entrada
- Simplificación y factorización de `F(x, y)`
- Clasificación como separable o no separable
- Soluciones constantes (cuando aplique)
- Separación de variables e integrales
- Solución general y particular
- Intervalo de validez
- Verificación de la solución
- Gráfica de la solución particular

Las gráficas se guardan en la carpeta `output/`.

## Casos de prueba obligatorios

| Caso | Ecuación | Condición inicial |
|------|----------|-------------------|
| 1 | `y/(1+x)` | y(0) = 2 |
| 2 | `(x+1)**2` | y(0) = 1 |
| 3 | `-x/y` | y(4) = -3 |
| 4 | `(y**2-1)/(x**2-1)` | y(2) = 2 |
| 5 | `x*y + x` | y(0) = 0 |
| 6 | `y + sin(x)` | y(0) = 1 (no separable) |
| 7 | `2*x*y` | y(0) = 3 (caso del grupo) |

## Estructura del proyecto

```
ecuaciones-separables/
├── app.py              # Interfaz Streamlit
├── requirements.txt
├── README.md
├── src/
│   ├── parser.py       # Entrada y validación
│   ├── separable.py    # Clasificación separable
│   ├── solver.py       # Resolución por separación
│   ├── validity.py     # Intervalo de validez
│   ├── verification.py # Verificación
│   ├── plotting.py     # Gráficas
│   ├── steps.py        # Orquestador del análisis
│   └── casos_prueba.py # Casos precargados
└── output/             # Gráficas exportadas
```
