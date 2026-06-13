# ESCALC — Engineering Software CALC

Suite de cálculo estructural en Python + Flask.  
Cada módulo es independiente. Todos comparten el servidor Flask principal.

---

## Arranque rápido

```bash
# 1. Clonar / abrir en VS Code
# 2. Crear entorno virtual
python -m venv venv

# 3. Activar
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Levantar servidor
python app.py
# → http://localhost:5050
```

O presionar **F5** en VS Code (usa `.vscode/launch.json` preconfigurado).

---

## Estructura del proyecto

```
ESCALC/
│
├── app.py                      ← Servidor Flask principal
├── requirements.txt            ← Todas las dependencias
├── README.md                   ← Este archivo
│
├── .vscode/
│   ├── launch.json             ← F5 → Flask debug
│   └── settings.json           ← Intérprete, Jinja2, formateo
│
├── templates/
│   ├── home.html               ← Portal principal (lista de módulos)
│   └── base.html               ← Layout compartido (header, nav, footer)
│
├── static/
│   └── css/
│       └── escalc.css          ← Estilos globales dark theme
│
│── wood/                       ← Módulo Wood — Cálculo NDS 2024
│   ├── ESCALC_Wood_Maestro.md  ← Documento maestro del módulo
│   ├── rafter_engine.py        ← Motor de cálculo de rafters
│   ├── nds_data.py             ← Tablas NDS: especies, grados, secciones
│   ├── routes/
│   │   └── wood.py             ← Blueprint Flask /wood
│   ├── utils/
│   │   ├── svg_rafter.py       ← Diagrama SVG del rafter
│   │   └── pdf_report.py       ← Memoria de cálculo PDF (ReportLab)
│   └── templates/
│       ├── wood_home.html
│       └── rafter.html
│
├── draw/                       ← Módulo Draw — Visualizador SVG
│   ├── ESCALC_Draw_Maestro.md  ← Documento maestro del módulo
│   ├── element_viewer.py       ← Orquestador: genera los 4 paneles
│   ├── geometry.py             ← Proyección isométrica 30°
│   ├── primitives.py           ← dim(), hatch(), apoyos, nodos
│   ├── section_props.py        ← A, Ix, Iy, Sx, Sy por perfil
│   ├── elements/
│   │   ├── column.py           ← Columna: elevación + ISO
│   │   ├── beam.py             ← Viga: elevación + ISO
│   │   ├── truss.py            ← Cercha: 2D + ISO (4 tipos)
│   │   └── section.py         ← Sección transversal
│   ├── routes/
│   │   └── draw.py             ← Blueprint Flask /draw
│   └── templates/
│       └── element_viewer.html ← Visor 4 paneles
│
├── foundation/                 ← [EN DESARROLLO]
├── steel/                      ← [EN DESARROLLO]
└── elements/                   ← [EN DESARROLLO]
```

---

## Módulos

| Módulo | Ruta | Estado | Documento maestro |
|---|---|---|---|
| **Wood** | `/wood/rafter` | ✅ Activo | `wood/ESCALC_Wood_Maestro.md` |
| **Draw** | `/draw/` | ✅ Activo | `draw/ESCALC_Draw_Maestro.md` |
| Foundation | `/foundation` | 🔧 En desarrollo | — |
| Steel | `/steel` | 🔧 En desarrollo | — |
| Elements | `/elements` | 🔧 En desarrollo | — |

---

## Cómo usar los documentos maestros

Cada módulo tiene su propio `.md` que contiene **todo el código Python** listo
para copiar y pegar en VS Code. El flujo de trabajo es:

1. Abrir el `.md` del módulo en VS Code (panel lateral)
2. Crear los archivos `.py` en la carpeta correspondiente
3. Copiar cada bloque de código del `.md` al archivo `.py`
4. Correr `python app.py` y verificar en el browser

No hace falta escribir código desde cero — los `.md` son los blueprints completos.

---

## Integración entre módulos

Wood → Draw: cuando el módulo Wood termina un cálculo, llama
automáticamente al visor Draw para generar las vistas del perfil:

```python
# En wood/routes/wood.py
from draw.element_viewer import from_calculation

result = calc.calculate()
views  = from_calculation(result)   # genera los 4 SVG automáticamente
```

---

## Stack técnico

| Componente | Tecnología | Por qué |
|---|---|---|
| Servidor | Flask 3.0 | Mínimo boilerplate, blueprints por módulo |
| Templates | Jinja2 | Incluido en Flask, ideal para SVG dinámico |
| Cálculo | Python + NumPy | Motor NDS directo, sin dependencias externas |
| Dibujo SVG | Python puro (`math`) | Sin librerías de dibujo, SVG como string |
| PDF | ReportLab | Memorias de cálculo profesionales |
| Frontend | HTML + CSS + JS mínimo | Sin frameworks, sin npm |

---

## Convenciones del proyecto

- Todos los módulos devuelven **strings SVG** — nunca archivos, nunca objetos complejos
- Las rutas Flask son siempre **stateless** — reciben form data, retornan HTML
- Los motores de cálculo (`*_engine.py`) son **independientes de Flask** — se pueden importar y testear sin levantar el servidor
- El CSS usa variables CSS para dark/light mode — nunca colores hardcodeados fuera de `draw/geometry.py`
- Las dimensiones de perfiles siempre en **mm** internamente — la conversión a otras unidades es responsabilidad de la UI

---

## Tests rápidos

```bash
# Testear motor de cálculo Wood (sin Flask)
python wood/test_rafter.py

# Testear motor de dibujo Draw (sin Flask)
python draw/test_draw.py

# Levantar todo
python app.py
```

---

*ESCALC · Engineering Software CALC*  
*Python 3.11 · Flask 3.0 · NDS 2024 · AISC 360*
