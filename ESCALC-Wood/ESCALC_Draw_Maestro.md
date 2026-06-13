# ESCALC Draw — Documento Maestro de Desarrollo
> Módulo: **Visualizador de Elementos Estructurales**  
> Suite: **ESCALC** (Engineering Software CALC)  
> Stack: **Python 3.11+ · Flask · SVG puro (sin librerías de dibujo externas)**  
> IDE: Visual Studio Code  
> Elementos: Columna · Viga · Cercha (Pratt, Howe, Warren, Fink)  
> Perfiles: W/IPE · C/UPN · L Angular · HSS Rect · HSS Circ · Sección maciza  
> Vistas: Elevación 2D · Sección transversal · Isométrica axonométrica · Propiedades  
> Versión del documento: 1.0

---

## Índice

1. [Visión y alcance del módulo](#1-visión-y-alcance)
2. [Arquitectura del módulo](#2-arquitectura-del-módulo)
3. [Estructura de carpetas](#3-estructura-de-carpetas)
4. [Setup en VS Code](#4-setup-en-vs-code)
5. [Motor de geometría — `draw/geometry.py`](#5-motor-de-geometría--drawgeometrypy)
6. [Primitivas SVG — `draw/primitives.py`](#6-primitivas-svg--drawprimitivespyy)
7. [Propiedades de sección — `draw/section_props.py`](#7-propiedades-de-sección--drawsection_propspy)
8. [Elemento: Columna — `draw/column.py`](#8-elemento-columna--drawcolumnpy)
9. [Elemento: Viga — `draw/beam.py`](#9-elemento-viga--drawbeampy)
10. [Elemento: Cercha — `draw/truss.py`](#10-elemento-cercha--drawtrusspy)
11. [Orquestador — `draw/element_viewer.py`](#11-orquestador--drawelement_viewerpy)
12. [Rutas Flask — `routes/draw.py`](#12-rutas-flask--routesdrawpy)
13. [Template HTML — `templates/element_viewer.html`](#13-template-html--templateselement_viewerhtml)
14. [CSS del visor — `static/css/viewer.css`](#14-css-del-visor--staticcssviewercss)
15. [Integración con módulos de cálculo](#15-integración-con-módulos-de-cálculo)
16. [Convenciones de dibujo técnico](#16-convenciones-de-dibujo-técnico)
17. [Valores de prueba](#17-valores-de-prueba)
18. [Roadmap — extensiones futuras](#18-roadmap--extensiones-futuras)

---

## 1. Visión y alcance

ESCALC Draw es el **módulo de visualización paramétrica** de la suite ESCALC.
Genera diagramas técnicos de elementos estructurales en SVG puro — sin canvas,
sin librerías de dibujo, sin JavaScript de cálculo. Todo el SVG se construye
en Python y se inyecta en el template Jinja2.

### Dos modos de uso

| Modo | Descripción | Cómo se activa |
|---|---|---|
| **Visor libre** | El usuario elige elemento, perfil y dimensiones manualmente | Ruta `/draw` |
| **Auto desde cálculo** | Al terminar un cálculo (rafter, viga, columna), el SVG se genera automáticamente | El motor de cálculo llama a `element_viewer.py` |

### Qué genera cada vista

| Vista | Contenido |
|---|---|
| **Elevación 2D** | Perfil lateral con apoyos, longitud y cotas |
| **Sección transversal** | Corte perpendicular al eje con hatching de 45° |
| **Isométrica** | Proyección axonométrica 30° — da sensación de volumen y espesor |
| **Propiedades** | Sección con A, Ix, Iy, Sx, Sy calculados en Python |

### Perfiles soportados

| Código | Nombre | Dimensiones requeridas |
|---|---|---|
| `W` | W / IPE — doble T | d, bf, tf, tw |
| `C` | C / UPN — canal | d, bf, tf, tw |
| `L` | L — angular | leg_a, leg_b, t |
| `HSS-R` | HSS rectangular (tubo rect.) | D, B, t |
| `HSS-C` | HSS circular (tubo circ.) | od, t |
| `SOLID` | Sección maciza rectangular | b, h |

---

## 2. Arquitectura del módulo

```
Request del browser
    │
    │  GET /draw?elem=column&profile=W&d=300&bf=150...
    ▼
routes/draw.py  (Flask Blueprint)
    │
    ├── Parsea y valida parámetros
    │
    ├── draw/element_viewer.py  ← Orquestador principal
    │       │
    │       ├── draw/column.py      ← SVG de columna (elevación + ISO)
    │       ├── draw/beam.py        ← SVG de viga (elevación + ISO)
    │       ├── draw/truss.py       ← SVG de cercha (2D + ISO)
    │       ├── draw/section.py     ← SVG de sección transversal
    │       ├── draw/primitives.py  ← Funciones base: dim(), hatch(), iso_point()
    │       ├── draw/geometry.py    ← Proyección isométrica, coordenadas
    │       └── draw/section_props.py  ← A, Ix, Iy, Sx, Sy
    │
    └── Devuelve dict con 4 strings SVG
            │
            ▼
    templates/element_viewer.html  (Jinja2)
            │
            ▼
    Browser renderiza los 4 paneles SVG
```

### Principio de diseño clave

Cada función de dibujo retorna un **string SVG puro** — no un objeto, no un
archivo. El orquestador los concatena y los pasa al template. Esto hace que
el sistema sea completamente stateless y fácil de integrar con cualquier módulo
de cálculo.

---

## 3. Estructura de carpetas

```
ESCALC/
│
├── draw/                          ← Módulo Draw (este documento)
│   │
│   ├── __init__.py
│   ├── element_viewer.py          ← Orquestador: genera los 4 paneles
│   ├── geometry.py                ← Proyección isométrica y geometría
│   ├── primitives.py              ← dim(), hatch(), iso_face(), label()
│   ├── section_props.py           ← Cálculo A, Ix, Iy, Sx, Sy
│   │
│   ├── elements/
│   │   ├── __init__.py
│   │   ├── column.py              ← Elevación e ISO de columna
│   │   ├── beam.py                ← Elevación e ISO de viga
│   │   ├── truss.py               ← 2D e ISO de cercha
│   │   └── section.py             ← Sección transversal (todas las formas)
│   │
│   └── profiles/
│       ├── __init__.py
│       └── profile_data.py        ← Dimensiones reales AISC/CIRSOC
│
├── routes/
│   ├── __init__.py
│   └── draw.py                    ← Blueprint Flask /draw
│
├── templates/
│   ├── base.html
│   └── element_viewer.html        ← 4 paneles SVG + controles
│
├── static/
│   └── css/
│       └── viewer.css             ← Estilos del visor
│
├── app.py
└── requirements.txt
```

---

## 4. Setup en VS Code

### 4.1 Instalación

```bash
cd ESCALC/draw

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
python app.py
# → http://localhost:5050/draw
```

### 4.2 `requirements.txt`

```
flask==3.0.3
jinja2==3.1.4
werkzeug==3.0.3
```

> ESCALC Draw no requiere NumPy ni matplotlib — todo el SVG
> se genera con matemática pura Python (math, dataclasses).

### 4.3 `.vscode/launch.json`

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "ESCALC Draw — Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "app.py",
        "FLASK_ENV": "development",
        "FLASK_DEBUG": "1"
      },
      "args": ["run", "--port=5050"],
      "jinja": true
    }
  ]
}
```

---

## 5. Motor de geometría — `draw/geometry.py`

Todas las funciones de coordenadas viven aquí. El resto del código las importa.

```python
# draw/geometry.py
# ESCALC Draw — Motor de geometría y proyección isométrica
# Proyección axonométrica estándar 30° (ángulo de isométrica técnica)

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Point2D:
    x: float
    y: float

    def __add__(self, other):
        return Point2D(self.x + other.x, self.y + other.y)

    def fmt(self) -> str:
        return f"{self.x:.2f},{self.y:.2f}"


def iso_point(wx: float, wy: float, wz: float,
              origin_x: float, origin_y: float,
              scale: float = 0.5) -> Point2D:
    """
    Proyección isométrica axonométrica 30°.

    Sistema de coordenadas del mundo:
        wx = eje X  → derecha
        wy = eje Y  → arriba (altura del elemento)
        wz = eje Z  → profundidad

    Fórmulas estándar de proyección isométrica:
        screen_x = (wx - wz) * cos(30°) * scale
        screen_y = (wx + wz) * sin(30°) * scale - wy * scale

    Args:
        wx, wy, wz: coordenadas en el espacio 3D (mm o m, consistente)
        origin_x, origin_y: punto de origen en el canvas SVG (px)
        scale: factor de escala px/unidad

    Returns:
        Point2D con coordenadas SVG (x hacia derecha, y hacia abajo)
    """
    COS30 = math.cos(math.pi / 6)  # ≈ 0.866
    SIN30 = math.sin(math.pi / 6)  # = 0.5

    screen_x = (wx - wz) * COS30 * scale
    screen_y = (wx + wz) * SIN30 * scale - wy * scale

    return Point2D(origin_x + screen_x, origin_y - screen_y)


def iso_face(points_3d: list, origin_x: float, origin_y: float,
             scale: float) -> list:
    """
    Proyecta una lista de puntos 3D (wx, wy, wz) a puntos 2D SVG.

    Args:
        points_3d: lista de tuplas (wx, wy, wz)
        origin_x, origin_y: origen SVG
        scale: factor escala

    Returns:
        Lista de Point2D proyectados
    """
    return [iso_point(wx, wy, wz, origin_x, origin_y, scale)
            for wx, wy, wz in points_3d]


def svg_polygon(points: list, fill: str, stroke: str = "#c8d8e8",
                stroke_width: float = 0.8, opacity: float = 1.0) -> str:
    """Genera un <polygon> SVG desde lista de Point2D."""
    pts_str = " ".join(p.fmt() for p in points)
    op = f' opacity="{opacity}"' if opacity < 1 else ""
    return (f'<polygon points="{pts_str}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}"{op}/>')


def svg_path_face(points: list, fill: str, stroke: str = "#c8d8e8",
                  stroke_width: float = 0.8) -> str:
    """Genera un <path> cerrado SVG desde lista de Point2D."""
    if not points:
        return ""
    d = f"M{points[0].fmt()} " + " ".join(f"L{p.fmt()}" for p in points[1:]) + " Z"
    return (f'<path d="{d}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}"/>')


# ── Paleta de colores ESCALC Draw ──────────────────────────────────────────
COLORS = {
    # Acero — superficies
    "flange":       "#b8c8d8",   # ala (flange) — cara principal
    "flange_side":  "#8a9aaa",   # ala — cara lateral (más oscura en ISO)
    "web":          "#98aabb",   # alma (web)
    "web_side":     "#78889a",   # alma — cara lateral
    "steel_light":  "#d8e8f4",   # superficie en luz (ISO)
    "steel_dark":   "#6a7a8a",   # superficie en sombra (ISO)
    "outline":      "#d0e0f0",   # contorno principal

    # Hatching de sección
    "hatch_stroke": "#5a6a7a",

    # Dimensiones y cotas
    "dim_text":     "#5a7aaa",
    "dim_line":     "#3a4a6a",
    "dim_dot":      "#4a6a9a",

    # Nodos de cercha
    "node_fill":    "#c8d8ec",
    "node_stroke":  "#8899bb",

    # Apoyo
    "support":      "#7a8a9a",

    # Fondo de panel
    "panel_bg":     "#181c25",

    # Texto de etiquetas
    "label":        "#5a7aaa",
}
```

---

## 6. Primitivas SVG — `draw/primitives.py`

```python
# draw/primitives.py
# ESCALC Draw — Funciones primitivas de dibujo SVG
# Todas retornan strings SVG listos para concatenar

import math
from draw.geometry import Point2D, COLORS


# ── Constantes de estilo ───────────────────────────────────────────────────

FONT = "font-family=\"Segoe UI,system-ui,sans-serif\""
STROKE_VISIBLE   = 1.5   # contorno principal de elemento
STROKE_HIDDEN    = 0.6   # línea oculta (dasharray)
STROKE_DIM       = 0.8   # líneas de cota
STROKE_CENTER    = 0.5   # eje de simetría
STROKE_HATCH     = 0.7   # líneas de hatching


def dim_line(x1: float, y1: float, x2: float, y2: float,
             label: str, offset: float = 20, side: int = 1) -> str:
    """
    Dibuja una cota lineal entre dos puntos.

    La cota se desplaza perpendicularmente a la línea en la dirección `side`
    (+1 = izquierda/arriba, -1 = derecha/abajo).

    Args:
        x1, y1, x2, y2: extremos de la dimensión a cotar
        label: texto de la cota (ej: "300 mm")
        offset: distancia de la cota al elemento (px)
        side: dirección del desplazamiento (+1 / -1)

    Returns:
        String SVG con la cota completa (líneas + puntos + texto)
    """
    dx, dy = x2 - x1, y2 - y1
    length = math.sqrt(dx**2 + dy**2)
    if length < 1:
        return ""

    # Vector normal unitario (perpendicular a la cota)
    nx = -dy / length * side
    ny =  dx / length * side

    ox, oy = nx * offset, ny * offset

    # Puntos de la línea de cota (desplazada)
    ax1, ay1 = x1 + ox, y1 + oy
    ax2, ay2 = x2 + ox, y2 + oy

    # Centro de la etiqueta
    mx = (ax1 + ax2) / 2
    my = (ay1 + ay2) / 2

    c = COLORS
    svg = (
        # Línea de cota
        f'<line x1="{ax1:.1f}" y1="{ay1:.1f}" x2="{ax2:.1f}" y2="{ay2:.1f}" '
        f'stroke="{c["dim_line"]}" stroke-width="{STROKE_DIM}"/>'

        # Líneas de referencia (desde el elemento hasta la cota)
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{ax1:.1f}" y2="{ay1:.1f}" '
        f'stroke="{c["dim_line"]}" stroke-width="0.5" stroke-dasharray="2 2"/>'
        f'<line x1="{x2:.1f}" y1="{y2:.1f}" x2="{ax2:.1f}" y2="{ay2:.1f}" '
        f'stroke="{c["dim_line"]}" stroke-width="0.5" stroke-dasharray="2 2"/>'

        # Puntos terminales
        f'<circle cx="{ax1:.1f}" cy="{ay1:.1f}" r="1.8" fill="{c["dim_dot"]}"/>'
        f'<circle cx="{ax2:.1f}" cy="{ay2:.1f}" r="1.8" fill="{c["dim_dot"]}"/>'

        # Texto
        f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" '
        f'dominant-baseline="central" fill="{c["dim_text"]}" '
        f'font-size="9" {FONT} opacity="0.9">{label}</text>'
    )
    return f'<g opacity="0.8">{svg}</g>'


def center_line(x1: float, y1: float, x2: float, y2: float) -> str:
    """Línea de eje de simetría (dash-dot)."""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{COLORS["dim_line"]}" stroke-width="{STROKE_CENTER}" '
        f'stroke-dasharray="8 3 2 3" opacity="0.5"/>'
    )


def hatch_rect(x: float, y: float, w: float, h: float,
               angle_deg: float = 45, spacing: float = 4.0) -> str:
    """
    Genera líneas de hatching dentro de un rectángulo.
    Usado en secciones transversales para indicar material cortado.

    Args:
        x, y: esquina superior izquierda del rectángulo
        w, h: ancho y alto
        angle_deg: ángulo de las líneas (45° estándar ISO)
        spacing: separación entre líneas (px)

    Returns:
        String SVG con todas las líneas de hatching clippeadas al rect
    """
    clip_id = f"hclip_{int(x)}_{int(y)}_{int(w)}_{int(h)}"
    lines = []

    # Rango de barrido para cubrir el rect rotado
    total = w + h
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    offset = -total
    while offset <= total * 2:
        # Línea a lo largo de todo el rectángulo
        lx1 = x + offset * cos_a
        ly1 = y + offset * sin_a
        lx2 = lx1 + total * (-sin_a)
        ly2 = ly1 + total * cos_a
        lines.append(
            f'<line x1="{lx1:.1f}" y1="{ly1:.1f}" '
            f'x2="{lx2:.1f}" y2="{ly2:.1f}" '
            f'stroke="{COLORS["hatch_stroke"]}" stroke-width="{STROKE_HATCH}"/>'
        )
        offset += spacing

    lines_svg = "\n".join(lines)

    return (
        f'<defs>'
        f'<clipPath id="{clip_id}">'
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"/>'
        f'</clipPath>'
        f'</defs>'
        f'<g clip-path="url(#{clip_id})" opacity="0.35">'
        f'{lines_svg}'
        f'</g>'
    )


def hatch_polygon(points: list, clip_id: str,
                  angle_deg: float = 45, spacing: float = 4.0) -> str:
    """
    Hatching clippeado a un polígono arbitrario.

    Args:
        points: lista de tuplas (x, y) del polígono
        clip_id: ID único para el clipPath
        angle_deg: ángulo del hatching
        spacing: separación entre líneas

    Returns:
        String SVG con hatching del polígono
    """
    if not points:
        return ""

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    pts_str = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
    clip_svg = (
        f'<defs><clipPath id="{clip_id}">'
        f'<polygon points="{pts_str}"/>'
        f'</clipPath></defs>'
    )

    lines = []
    total = (x_max - x_min) + (y_max - y_min)
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    offset = -total
    while offset <= total * 2:
        lx1 = x_min + offset * cos_a
        ly1 = y_min + offset * sin_a
        lx2 = lx1 + total * (-sin_a)
        ly2 = ly1 + total * cos_a
        lines.append(
            f'<line x1="{lx1:.1f}" y1="{ly1:.1f}" '
            f'x2="{lx2:.1f}" y2="{ly2:.1f}" '
            f'stroke="{COLORS["hatch_stroke"]}" stroke-width="{STROKE_HATCH}"/>'
        )
        offset += spacing

    return (
        clip_svg +
        f'<g clip-path="url(#{clip_id})" opacity="0.35">'
        + "\n".join(lines) +
        f'</g>'
    )


def support_pin(cx: float, cy: float, size: float = 12) -> str:
    """Dibuja soporte de rótula (triángulo + línea base)."""
    c = COLORS["support"]
    return (
        f'<polygon points="{cx},{cy} {cx-size},{cy+size*1.5} {cx+size},{cy+size*1.5}" '
        f'fill="none" stroke="{c}" stroke-width="1.2"/>'
        f'<line x1="{cx-size-4}" y1="{cy+size*1.5+2}" '
        f'x2="{cx+size+4}" y2="{cy+size*1.5+2}" '
        f'stroke="{c}" stroke-width="1.2"/>'
    )


def support_roller(cx: float, cy: float, size: float = 10) -> str:
    """Dibuja soporte de rodillo (rectángulo + línea base)."""
    c = COLORS["support"]
    return (
        f'<rect x="{cx-size}" y="{cy}" width="{size*2}" height="{size}" '
        f'rx="2" fill="none" stroke="{c}" stroke-width="1.2"/>'
        f'<line x1="{cx-size-4}" y1="{cy+size+2}" '
        f'x2="{cx+size+4}" y2="{cy+size+2}" '
        f'stroke="{c}" stroke-width="1.2"/>'
    )


def truss_node(cx: float, cy: float, r: float = 3.5) -> str:
    """Nodo de cercha (círculo relleno)."""
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" '
        f'fill="{COLORS["node_fill"]}" stroke="{COLORS["node_stroke"]}" '
        f'stroke-width="0.8"/>'
    )


def panel_label(cx: float, cy: float, text: str) -> str:
    """Etiqueta inferior de panel de vista."""
    return (
        f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" '
        f'fill="{COLORS["label"]}" font-size="9" {FONT} opacity="0.8">'
        f'{text}</text>'
    )


def svg_wrap(content: str, vw: int = 400, vh: int = 300,
             bg: str = "#181c25") -> str:
    """
    Envuelve contenido en un elemento <svg> completo.

    Args:
        content: string SVG interior
        vw, vh: dimensiones del viewBox
        bg: color de fondo

    Returns:
        String SVG completo listo para inyectar en HTML
    """
    return (
        f'<svg viewBox="0 0 {vw} {vh}" xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="100%" style="display:block;background:{bg}">'
        f'{content}'
        f'</svg>'
    )
```

---

## 7. Propiedades de sección — `draw/section_props.py`

```python
# draw/section_props.py
# ESCALC Draw — Cálculo de propiedades geométricas de sección
# Todas las fórmulas en mm y mm^n

import math
from dataclasses import dataclass


@dataclass
class SectionProperties:
    """Propiedades geométricas de la sección transversal."""
    A_mm2:  float    # Área (mm²)
    Ix_mm4: float    # Inercia respecto eje X (mm⁴)
    Iy_mm4: float    # Inercia respecto eje Y (mm⁴)
    Sx_mm3: float    # Módulo resistente eje X (mm³)
    Sy_mm3: float    # Módulo resistente eje Y (mm³)
    rx_mm:  float    # Radio de giro eje X (mm)
    ry_mm:  float    # Radio de giro eje Y (mm)

    @property
    def A_cm2(self) -> float:  return self.A_mm2  / 100
    @property
    def Ix_cm4(self) -> float: return self.Ix_mm4 / 10_000
    @property
    def Iy_cm4(self) -> float: return self.Iy_mm4 / 10_000
    @property
    def Sx_cm3(self) -> float: return self.Sx_mm3 / 1_000
    @property
    def Sy_cm3(self) -> float: return self.Sy_mm3 / 1_000


def calc_W_section(d: float, bf: float, tf: float, tw: float) -> SectionProperties:
    """
    Perfil W / IPE — doble T laminado.
    Fórmula: área total = 2 alas + alma
    Inercia Ix = Inercia total - hueco interior
    """
    hw = d - 2 * tf   # altura del alma

    A  = 2 * bf * tf + hw * tw
    Ix = (bf * d**3 / 12) - ((bf - tw) * hw**3 / 12)
    Iy = (2 * tf * bf**3 / 12) + (hw * tw**3 / 12)
    Sx = Ix / (d / 2)
    Sy = Iy / (bf / 2)
    rx = math.sqrt(Ix / A)
    ry = math.sqrt(Iy / A)

    return SectionProperties(A, Ix, Iy, Sx, Sy, rx, ry)


def calc_C_section(d: float, bf: float, tf: float, tw: float) -> SectionProperties:
    """
    Perfil C / UPN — canal laminado.
    Centroide en X desplazado del alma, pero para propiedades estándar
    se toma el eje de centroide de la sección.
    """
    hw = d - 2 * tf

    A  = 2 * bf * tf + hw * tw
    Ix = (bf * d**3 / 12) - ((bf - tw) * hw**3 / 12)
    Iy = (2 * (bf**3 * tf / 3)) + (hw * tw**3 / 12)
    Sx = Ix / (d / 2)
    Sy = Iy / bf
    rx = math.sqrt(Ix / A)
    ry = math.sqrt(Iy / A)

    return SectionProperties(A, Ix, Iy, Sx, Sy, rx, ry)


def calc_L_section(leg_a: float, leg_b: float, t: float) -> SectionProperties:
    """
    Perfil L — angular.
    Eje de referencia en el vértice exterior.
    """
    A  = (leg_a + leg_b - t) * t
    # Inercia respecto al vértice, luego se desplaza al centroide
    Ix_v = (t * leg_a**3 / 3) + ((leg_b - t) * t**3 / 3)
    Iy_v = (leg_a * t**3 / 3) + (t * (leg_b - t)**3 / 3)

    y_c = (leg_a**2 * t / 2 + (leg_b - t) * t**2 / 2) / A
    x_c = (t**2 * leg_a / 2 + (leg_b - t)**2 * t / 2) / A

    Ix = Ix_v - A * y_c**2
    Iy = Iy_v - A * x_c**2
    Sx = Ix / max(leg_a - y_c, y_c)
    Sy = Iy / max(leg_b - x_c, x_c)
    rx = math.sqrt(Ix / A)
    ry = math.sqrt(Iy / A)

    return SectionProperties(A, Ix, Iy, Sx, Sy, rx, ry)


def calc_HSS_rect(D: float, B: float, t: float) -> SectionProperties:
    """HSS rectangular (tubo de sección rectangular)."""
    Di, Bi = D - 2*t, B - 2*t

    A  = D*B - Di*Bi
    Ix = (B * D**3 / 12) - (Bi * Di**3 / 12)
    Iy = (D * B**3 / 12) - (Di * Bi**3 / 12)
    Sx = Ix / (D / 2)
    Sy = Iy / (B / 2)
    rx = math.sqrt(Ix / A)
    ry = math.sqrt(Iy / A)

    return SectionProperties(A, Ix, Iy, Sx, Sy, rx, ry)


def calc_HSS_circ(od: float, t: float) -> SectionProperties:
    """HSS circular (tubo de sección circular / CHS)."""
    id_ = od - 2*t

    A  = math.pi / 4 * (od**2 - id_**2)
    Ix = math.pi / 64 * (od**4 - id_**4)
    Iy = Ix
    Sx = Ix / (od / 2)
    Sy = Sx
    rx = math.sqrt(Ix / A)
    ry = rx

    return SectionProperties(A, Ix, Iy, Sx, Sy, rx, ry)


def calc_solid_rect(b: float, h: float) -> SectionProperties:
    """Sección maciza rectangular."""
    A  = b * h
    Ix = b * h**3 / 12
    Iy = h * b**3 / 12
    Sx = Ix / (h / 2)
    Sy = Iy / (b / 2)
    rx = math.sqrt(Ix / A)
    ry = math.sqrt(Iy / A)

    return SectionProperties(A, Ix, Iy, Sx, Sy, rx, ry)


def get_section_props(profile_type: str, **dims) -> SectionProperties:
    """
    Dispatcher — llama al calculador correcto según el tipo de perfil.

    Uso:
        props = get_section_props('W', d=300, bf=150, tf=12, tw=8)
        props = get_section_props('HSS-C', od=168, t=8)
    """
    dispatch = {
        'W':      lambda: calc_W_section(dims['d'], dims['bf'], dims['tf'], dims['tw']),
        'C':      lambda: calc_C_section(dims['d'], dims['bf'], dims['tf'], dims['tw']),
        'L':      lambda: calc_L_section(dims['leg_a'], dims['leg_b'], dims['t']),
        'HSS-R':  lambda: calc_HSS_rect(dims['D'], dims['B'], dims['t']),
        'HSS-C':  lambda: calc_HSS_circ(dims['od'], dims['t']),
        'SOLID':  lambda: calc_solid_rect(dims['b'], dims['h']),
    }
    if profile_type not in dispatch:
        raise ValueError(f"Tipo de perfil desconocido: '{profile_type}'")
    return dispatch[profile_type]()
```

---

## 8. Elemento: Columna — `draw/elements/column.py`

```python
# draw/elements/column.py
# ESCALC Draw — Dibujo de columna en elevación e isométrica

from draw.geometry import iso_point, svg_path_face, COLORS
from draw.primitives import (
    dim_line, center_line, hatch_rect, support_pin, support_roller,
    panel_label, svg_wrap
)


VW, VH = 380, 320   # dimensiones del viewport de cada panel


def _profile_dims(profile_type: str, dims: dict) -> dict:
    """Extrae dimensiones relevantes según tipo de perfil."""
    t = profile_type
    d = dims
    if t in ('W', 'C'):
        return {'d': d.get('d',300), 'bf': d.get('bf',150),
                'tf': d.get('tf',12), 'tw': d.get('tw',8)}
    elif t == 'L':
        return {'leg': d.get('leg_a', 100), 't': d.get('t', 10)}
    elif t == 'HSS-R':
        return {'D': d.get('D',150), 'B': d.get('B',100), 't': d.get('t',8)}
    elif t == 'HSS-C':
        return {'od': d.get('od',168), 't': d.get('t',8)}
    else:  # SOLID
        return {'b': d.get('b',150), 'h': d.get('h',200)}


def draw_column_elevation(profile_type: str, dims: dict,
                           height_m: float, show_dims: bool = True) -> str:
    """
    Genera SVG de elevación 2D de columna.

    La columna se dibuja verticalmente centrada en el viewport.
    Las cotas se muestran a la derecha (offset +20px).

    Returns:
        String SVG completo del panel de elevación
    """
    pd = _profile_dims(profile_type, dims)
    cx, cy = VW / 2, VH / 2
    t = profile_type

    # Escala de altura: la columna ocupa 65% del viewport vertical
    col_px_h = VH * 0.65
    h_mm = height_m * 1000

    # Ancho de representación en pantalla (no a escala real, sino proporcional)
    if t in ('W', 'C'):
        col_w = max(20, min(pd['bf'] * 0.09, 70))
        flange_t = max(3, pd['tf'] * 0.09)
        web_t    = max(2, pd['tw'] * 0.09)
    elif t == 'HSS-R':
        col_w = max(18, min(pd['B'] * 0.09, 60))
        wall_t = max(2, pd['t'] * 0.09)
    elif t == 'HSS-C':
        col_w = max(18, min(pd['od'] * 0.09, 60))
        wall_t = max(2, pd['t'] * 0.09)
    elif t == 'L':
        col_w = max(16, min(pd['leg'] * 0.09, 55))
        wall_t = max(2, pd['t'] * 0.09)
    else:  # SOLID
        col_w = max(18, min(pd['b'] * 0.09, 65))

    x0 = cx - col_w / 2
    y_top = cy - col_px_h / 2
    y_bot = cy + col_px_h / 2
    c = COLORS

    parts = []

    # Eje de simetría vertical
    parts.append(center_line(cx, y_top - 15, cx, y_bot + 15))

    if t in ('W', 'C'):
        # Ala superior
        parts.append(
            f'<rect x="{cx-col_w/2}" y="{y_top}" width="{col_w}" height="{flange_t}" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
        )
        # Alma
        parts.append(
            f'<rect x="{cx-web_t/2}" y="{y_top+flange_t}" width="{web_t}" '
            f'height="{col_px_h-2*flange_t}" '
            f'fill="{c["web"]}" stroke="{c["outline"]}" stroke-width=".5"/>'
        )
        # Ala inferior
        parts.append(
            f'<rect x="{cx-col_w/2}" y="{y_bot-flange_t}" width="{col_w}" '
            f'height="{flange_t}" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
        )

    elif t == 'HSS-R':
        parts.append(
            f'<rect x="{cx-col_w/2}" y="{y_top}" width="{col_w}" '
            f'height="{col_px_h}" rx="2" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
        )
        # Líneas interiores (pared interior visible)
        parts.append(
            f'<rect x="{cx-col_w/2+wall_t}" y="{y_top+wall_t}" '
            f'width="{col_w-2*wall_t}" height="{col_px_h-2*wall_t}" rx="1" '
            f'fill="none" stroke="{c["dim_line"]}" stroke-width=".5" '
            f'stroke-dasharray="3 2"/>'
        )

    elif t == 'HSS-C':
        parts.append(
            f'<rect x="{cx-col_w/2}" y="{y_top}" width="{col_w}" '
            f'height="{col_px_h}" rx="{col_w/2}" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
        )

    elif t == 'L':
        leg_px = col_w
        t_px = max(2, pd['t'] * 0.09)
        pts = (f"{cx},{y_top} {cx+leg_px},{y_top} {cx+leg_px},{y_top+t_px} "
               f"{cx+t_px},{y_top+t_px} {cx+t_px},{y_bot} {cx},{y_bot}")
        parts.append(
            f'<polygon points="{pts}" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
        )

    else:  # SOLID
        parts.append(
            f'<rect x="{cx-col_w/2}" y="{y_top}" width="{col_w}" '
            f'height="{col_px_h}" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
        )

    # Placas de base y tope
    plate_w = col_w + 10
    parts.append(
        f'<rect x="{cx-plate_w/2}" y="{y_bot}" width="{plate_w}" height="6" '
        f'rx="1" fill="{c["flange_side"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
    )
    parts.append(
        f'<rect x="{cx-plate_w/2}" y="{y_top-6}" width="{plate_w}" height="6" '
        f'rx="1" fill="{c["flange_side"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
    )

    # Apoyo empotrado (base)
    parts.append(support_pin(cx, y_bot + 6))

    # Cotas
    if show_dims:
        # Cota de altura (derecha)
        parts.append(dim_line(
            cx + col_w/2, y_top, cx + col_w/2, y_bot,
            f"{height_m} m", offset=28, side=1
        ))
        # Cota de ancho (arriba)
        parts.append(dim_line(
            cx - col_w/2, y_top - 8, cx + col_w/2, y_top - 8,
            f"{pd.get('bf', pd.get('od', pd.get('b', pd.get('leg', '?'))))} mm",
            offset=-18, side=1
        ))

    parts.append(panel_label(cx, VH - 12, "Elevación 2D"))

    return svg_wrap("\n".join(parts), VW, VH)


def draw_column_isometric(profile_type: str, dims: dict,
                           height_m: float) -> str:
    """
    Genera SVG de vista isométrica de columna.

    La proyección axonométrica 30° muestra las tres caras visibles
    del perfil con diferente luminosidad (claro / medio / oscuro).

    Returns:
        String SVG completo del panel isométrico
    """
    pd = _profile_dims(profile_type, dims)
    t = profile_type
    h_mm = height_m * 1000

    # Escala: la columna entra en el viewport con margen
    sc = min(VH * 0.55 / h_mm, VW * 0.25 / max(
        pd.get('bf', pd.get('B', pd.get('od', pd.get('b', 200)))), 50
    ))

    ox, oy = VW * 0.42, VH * 0.82

    def iP(wx, wy, wz):
        return iso_point(wx, wy, wz, ox, oy, sc)

    c = COLORS
    parts = []

    if t in ('W', 'C'):
        d = pd['d']; bf = pd['bf']; tf = pd['tf']; tw = pd['tw']
        depth = bf * 0.3   # profundidad isométrica visible

        # ── Cara frontal: ala superior, alma, ala inferior ──
        def face_rect(pts_3d, fill, stroke='#b0c0d0', sw=0.8):
            pts2d = [iP(*p) for p in pts_3d]
            return svg_path_face(pts2d, fill, stroke, sw)

        # Ala superior — cara frontal
        parts.append(face_rect([
            (-bf/2, h_mm, 0), (bf/2, h_mm, 0),
            (bf/2, h_mm-tf, 0), (-bf/2, h_mm-tf, 0)
        ], c['flange']))
        # Ala inferior — cara frontal
        parts.append(face_rect([
            (-bf/2, tf, 0), (bf/2, tf, 0),
            (bf/2, 0, 0), (-bf/2, 0, 0)
        ], c['flange']))
        # Alma — cara frontal
        parts.append(face_rect([
            (-tw/2, h_mm-tf, 0), (tw/2, h_mm-tf, 0),
            (tw/2, tf, 0), (-tw/2, tf, 0)
        ], c['web']))

        # ── Cara lateral derecha (profundidad) ──
        parts.append(face_rect([
            (bf/2, h_mm, 0), (bf/2, h_mm, depth),
            (bf/2, h_mm-tf, depth), (bf/2, h_mm-tf, 0)
        ], c['flange_side'], '#a0b0c0'))
        parts.append(face_rect([
            (bf/2, tf, 0), (bf/2, tf, depth),
            (bf/2, 0, depth), (bf/2, 0, 0)
        ], c['flange_side'], '#a0b0c0'))
        parts.append(face_rect([
            (tw/2, h_mm-tf, 0), (tw/2, h_mm-tf, depth),
            (tw/2, tf, depth), (tw/2, tf, 0)
        ], c['web_side'], '#a0b0c0'))

    elif t == 'HSS-R':
        D = pd['D']; B = pd['B']; thick = pd['t']
        depth = B * 0.3

        def face_rect(pts_3d, fill, stroke='#b0c0d0', sw=0.8):
            pts2d = [iP(*p) for p in pts_3d]
            return svg_path_face(pts2d, fill, stroke, sw)

        # Cara frontal
        parts.append(face_rect([
            (-B/2, h_mm, 0), (B/2, h_mm, 0),
            (B/2, 0, 0), (-B/2, 0, 0)
        ], c['flange']))
        # Cara lateral
        parts.append(face_rect([
            (B/2, h_mm, 0), (B/2, h_mm, depth),
            (B/2, 0, depth), (B/2, 0, 0)
        ], c['flange_side'], '#a0b0c0'))

    elif t == 'HSS-C':
        od = pd['od']
        r  = od / 2
        depth = od * 0.25

        def face_rect(pts_3d, fill, stroke='#b0c0d0', sw=0.8):
            pts2d = [iP(*p) for p in pts_3d]
            return svg_path_face(pts2d, fill, stroke, sw)

        parts.append(face_rect([
            (-r, h_mm, 0), (r, h_mm, 0),
            (r, 0, 0), (-r, 0, 0)
        ], c['flange']))
        parts.append(face_rect([
            (r, h_mm, 0), (r, h_mm, depth),
            (r, 0, depth), (r, 0, 0)
        ], c['flange_side'], '#a0b0c0'))

    else:  # L y SOLID
        w = pd.get('b', pd.get('leg', 100))
        depth = w * 0.3

        def face_rect(pts_3d, fill, stroke='#b0c0d0', sw=0.8):
            pts2d = [iP(*p) for p in pts_3d]
            return svg_path_face(pts2d, fill, stroke, sw)

        parts.append(face_rect([
            (0, h_mm, 0), (w, h_mm, 0),
            (w, 0, 0), (0, 0, 0)
        ], c['flange']))
        parts.append(face_rect([
            (w, h_mm, 0), (w, h_mm, depth),
            (w, 0, depth), (w, 0, 0)
        ], c['flange_side'], '#a0b0c0'))

    parts.append(panel_label(VW / 2, VH - 12, "Vista isométrica"))
    return svg_wrap("\n".join(parts), VW, VH)
```

---

## 9. Elemento: Viga — `draw/elements/beam.py`

```python
# draw/elements/beam.py
# ESCALC Draw — Dibujo de viga en elevación e isométrica

from draw.geometry import iso_point, svg_path_face, COLORS
from draw.primitives import (
    dim_line, center_line, hatch_rect, support_pin, support_roller,
    panel_label, svg_wrap
)

VW, VH = 380, 320


def draw_beam_elevation(profile_type: str, dims: dict,
                         length_m: float, show_dims: bool = True) -> str:
    """
    Genera SVG de elevación 2D de viga (vista lateral).

    La viga se dibuja horizontalmente centrada.
    Los apoyos (rótula + rodillo) se colocan en los extremos.
    """
    cx, cy = VW / 2, VH / 2
    beam_l = VW * 0.80
    t = profile_type
    c = COLORS

    # Altura del perfil en pantalla
    if t in ('W', 'C'):
        beam_h = max(16, min(dims.get('d', 300) * 0.11, VH * 0.35))
        tf_px  = max(3, dims.get('tf', 12) * 0.11)
        tw_px  = max(2, dims.get('tw', 8) * 0.11)
    elif t == 'HSS-R':
        beam_h = max(14, min(dims.get('D', 150) * 0.11, VH * 0.30))
        t_px   = max(2, dims.get('t', 8) * 0.11)
    elif t == 'HSS-C':
        beam_h = max(14, min(dims.get('od', 150) * 0.11, VH * 0.30))
    else:
        beam_h = max(14, min(dims.get('h', 200) * 0.11, VH * 0.30))

    x0 = cx - beam_l / 2
    x1 = cx + beam_l / 2
    y0 = cy - beam_h / 2

    parts = []

    # Eje de simetría horizontal
    parts.append(center_line(x0 - 10, cy, x1 + 10, cy))

    if t in ('W', 'C'):
        # Ala superior
        parts.append(
            f'<rect x="{x0}" y="{y0}" width="{beam_l}" height="{tf_px}" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".7"/>'
        )
        # Alma
        parts.append(
            f'<rect x="{x0}" y="{y0+tf_px}" width="{beam_l}" '
            f'height="{beam_h-2*tf_px}" '
            f'fill="{c["web"]}" stroke="{c["outline"]}" stroke-width=".5"/>'
        )
        # Ala inferior
        parts.append(
            f'<rect x="{x0}" y="{y0+beam_h-tf_px}" width="{beam_l}" '
            f'height="{tf_px}" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".7"/>'
        )
    elif t == 'HSS-R':
        parts.append(
            f'<rect x="{x0}" y="{y0}" width="{beam_l}" height="{beam_h}" '
            f'rx="2" fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
        )
        parts.append(
            f'<rect x="{x0+t_px}" y="{y0+t_px}" '
            f'width="{beam_l-2*t_px}" height="{beam_h-2*t_px}" rx="1" '
            f'fill="none" stroke="{c["dim_line"]}" stroke-width=".5" '
            f'stroke-dasharray="3 2"/>'
        )
    elif t == 'HSS-C':
        parts.append(
            f'<rect x="{x0}" y="{y0}" width="{beam_l}" height="{beam_h}" '
            f'rx="{beam_h/2}" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
        )
    else:
        parts.append(
            f'<rect x="{x0}" y="{y0}" width="{beam_l}" height="{beam_h}" '
            f'fill="{c["flange"]}" stroke="{c["outline"]}" stroke-width=".8"/>'
        )

    # Apoyos
    parts.append(support_pin(x0, cy + beam_h / 2))
    parts.append(support_roller(x1, cy + beam_h / 2))

    # Cotas
    if show_dims:
        parts.append(dim_line(
            x0, y0 - 6, x1, y0 - 6,
            f"L = {length_m} m", offset=-18, side=1
        ))
        d_val = dims.get('d', dims.get('D', dims.get('od', dims.get('h', '?'))))
        parts.append(dim_line(
            x1 + 8, y0, x1 + 8, y0 + beam_h,
            f"{d_val} mm", offset=20, side=1
        ))

    parts.append(panel_label(cx, VH - 12, "Elevación lateral"))
    return svg_wrap("\n".join(parts), VW, VH)


def draw_beam_isometric(profile_type: str, dims: dict,
                          length_m: float) -> str:
    """
    Genera SVG de vista isométrica de viga.

    La viga se muestra con sus tres caras visibles:
    cara frontal (frente del perfil), cara superior (ala superior)
    y cara lateral derecha (sección del extremo).
    """
    t = profile_type
    L = length_m * 1000   # mm

    # Escala para que la viga quepa horizontalmente
    sc = min(VW * 0.55 / L, VH * 0.30 / dims.get('d', 300))
    sc = max(sc, 0.025)

    ox, oy = VW * 0.12, VH * 0.62

    def iP(wx, wy, wz):
        return iso_point(wx, wy, wz, ox, oy, sc)

    c = COLORS
    parts = []

    def face(pts_3d, fill, stroke='#b0c0d0', sw=0.8):
        pts2d = [iP(*p) for p in pts_3d]
        return svg_path_face(pts2d, fill, stroke, sw)

    if t in ('W', 'C'):
        d  = dims.get('d', 300)
        bf = dims.get('bf', 150)
        tf = dims.get('tf', 12)
        tw = dims.get('tw', 8)
        depth = bf * 0.3   # "espesor" lateral visible en ISO

        # Cara inferior del ala inferior (cara que mira hacia abajo)
        parts.append(face([
            (0, 0, 0), (L, 0, 0), (L, 0, bf), (0, 0, bf)
        ], c['flange_side'], '#a0b0c0'))

        # Cara frontal: ala sup, alma, ala inf
        parts.append(face([
            (0, d-tf, 0), (L, d-tf, 0), (L, d, 0), (0, d, 0)
        ], c['flange']))
        parts.append(face([
            (0, tf, 0), (L, tf, 0), (L, d-tf, 0), (0, d-tf, 0)
        ], c['web']))
        parts.append(face([
            (0, 0, 0), (L, 0, 0), (L, tf, 0), (0, tf, 0)
        ], c['flange']))

        # Cara superior del ala superior
        parts.append(face([
            (0, d, 0), (L, d, 0), (L, d, bf), (0, d, bf)
        ], c['steel_light'], '#c0d0e0'))

        # Sección extremo derecho (cara lateral)
        parts.append(face([
            (L, d, 0), (L, d, bf), (L, d-tf, bf), (L, d-tf, 0)
        ], c['flange'], '#a8b8c8'))
        parts.append(face([
            (L, d-tf, 0), (L, d-tf, tw), (L, tf, tw), (L, tf, 0)
        ], c['web'], '#a8b8c8'))
        parts.append(face([
            (L, tf, 0), (L, tf, bf), (L, 0, bf), (L, 0, 0)
        ], c['flange'], '#a8b8c8'))

    else:
        # Para otros perfiles: representación simplificada
        d = dims.get('d', dims.get('D', dims.get('od', dims.get('h', 200))))
        b = dims.get('bf', dims.get('B', dims.get('od', dims.get('b', 100))))

        parts.append(face([
            (0, 0, 0), (L, 0, 0), (L, d, 0), (0, d, 0)
        ], c['flange']))
        parts.append(face([
            (0, d, 0), (L, d, 0), (L, d, b*0.3), (0, d, b*0.3)
        ], c['steel_light'], '#c0d0e0'))
        parts.append(face([
            (L, d, 0), (L, d, b*0.3), (L, 0, b*0.3), (L, 0, 0)
        ], c['flange_side'], '#a8b8c8'))

    parts.append(panel_label(VW / 2, VH - 12, "Vista isométrica"))
    return svg_wrap("\n".join(parts), VW, VH)
```

---

## 10. Elemento: Cercha — `draw/elements/truss.py`

```python
# draw/elements/truss.py
# ESCALC Draw — Dibujo de cercha (Pratt, Howe, Warren, Fink)

import math
from draw.geometry import iso_point, COLORS
from draw.primitives import (
    dim_line, support_pin, support_roller, truss_node, panel_label, svg_wrap
)

VW, VH = 380, 320


def _truss_nodes(truss_type: str, panels: int,
                  length_m: float, height_m: float,
                  margin: float, pw: float, bY: float, tY: float):
    """
    Calcula los nodos superiores e inferiores de la cercha
    según su tipo (paralela o triangulada tipo Fink).

    Returns:
        Lista de dicts {'xb', 'xt', 'yb', 'yt'} por panel node
    """
    nodes = []
    for i in range(panels + 1):
        xb = margin + i * pw
        if truss_type == 'fink':
            # Cercha de techo — perfil triangular simétrico
            mid = panels / 2
            frac = i / mid if i <= mid else (panels - i) / mid
            yt = bY - frac * (bY - tY)
        else:
            # Cercha paralela — cordón superior recto
            yt = tY
        nodes.append({'x': xb, 'yb': bY, 'yt': yt})
    return nodes


def _diagonals(truss_type: str, panels: int, nodes: list) -> list:
    """
    Retorna lista de segmentos diagonales como tuplas
    (node_i, node_j) donde i, j son índices en la lista de nodos.
    """
    segs = []
    mid = panels // 2

    for i in range(panels):
        if truss_type == 'pratt':
            # Diagonales en compresión hacia el centro
            if i < mid:
                segs.append(('top', i, 'bot', i + 1))
            else:
                segs.append(('bot', i, 'top', i + 1))
        elif truss_type == 'howe':
            # Diagonales en tensión hacia el centro
            if i < mid:
                segs.append(('bot', i, 'top', i + 1))
            else:
                segs.append(('top', i, 'bot', i + 1))
        elif truss_type == 'warren':
            # Diagonales alternadas sin montantes
            if i % 2 == 0:
                segs.append(('top', i, 'bot', i + 1))
            else:
                segs.append(('bot', i, 'top', i + 1))
        elif truss_type == 'fink':
            # Fink: dos mitades simétricas con diagonales hacia el centro
            if i < mid:
                segs.append(('bot', i, 'top', i + 1))
            else:
                segs.append(('top', i, 'bot', i + 1))
    return segs


def draw_truss_2d(truss_type: str, panels: int, length_m: float,
                   height_m: float, show_dims: bool = True) -> str:
    """
    Genera SVG de vista frontal de cercha.

    Args:
        truss_type: 'pratt' | 'howe' | 'warren' | 'fink'
        panels: número de vanos (2–12)
        length_m: luz total en metros
        height_m: altura de la cercha en metros
        show_dims: mostrar cotas

    Returns:
        String SVG del panel 2D
    """
    margin = 35.0
    pw = (VW - 2 * margin) / panels
    bY = VH - 58.0   # Y del cordón inferior
    tY = bY - height_m * (VH - 90) / max(height_m * 1.2, 4)  # Y cordón superior
    tY = max(tY, 30.0)

    c = COLORS
    nodes = _truss_nodes(truss_type, panels, length_m, height_m,
                          margin, pw, bY, tY)
    parts = []

    def seg(x1, y1, x2, y2, stroke, sw):
        return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" '
                f'x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>')

    # Cordones
    for i in range(panels):
        # Inferior
        parts.append(seg(nodes[i]['x'], nodes[i]['yb'],
                          nodes[i+1]['x'], nodes[i+1]['yb'],
                          c['flange'], 2.5))
        # Superior
        parts.append(seg(nodes[i]['x'], nodes[i]['yt'],
                          nodes[i+1]['x'], nodes[i+1]['yt'],
                          c['flange'], 2.5))

    # Montantes verticales
    for i in range(panels + 1):
        if truss_type != 'warren':  # Warren no tiene montantes
            parts.append(seg(nodes[i]['x'], nodes[i]['yb'],
                              nodes[i]['x'], nodes[i]['yt'],
                              c['web'], 1.5))

    # Diagonales
    diags = _diagonals(truss_type, panels, nodes)
    for (face_a, ia, face_b, ib) in diags:
        x1 = nodes[ia]['x']
        y1 = nodes[ia]['yb'] if face_a == 'bot' else nodes[ia]['yt']
        x2 = nodes[ib]['x']
        y2 = nodes[ib]['yb'] if face_b == 'bot' else nodes[ib]['yt']
        parts.append(seg(x1, y1, x2, y2, c['web'], 1.2))

    # Nodos (círculos)
    for n in nodes:
        parts.append(truss_node(n['x'], n['yb']))
        parts.append(truss_node(n['x'], n['yt']))

    # Apoyos
    parts.append(support_pin(nodes[0]['x'], nodes[0]['yb']))
    parts.append(support_roller(nodes[-1]['x'], nodes[-1]['yb']))

    # Cotas
    if show_dims:
        parts.append(dim_line(
            margin, bY + 10, VW - margin, bY + 10,
            f"L = {length_m} m", offset=20
        ))
        if truss_type != 'fink':
            parts.append(dim_line(
                margin - 10, tY, margin - 10, bY,
                f"h = {height_m} m", offset=-20, side=-1
            ))

    type_labels = {
        'pratt': 'Pratt', 'howe': 'Howe',
        'warren': 'Warren', 'fink': 'Fink (techo)'
    }
    parts.append(panel_label(
        VW / 2, VH - 12,
        f"Cercha {type_labels.get(truss_type, truss_type)} — {panels} vanos"
    ))
    return svg_wrap("\n".join(parts), VW, VH)


def draw_truss_isometric(truss_type: str, panels: int,
                           length_m: float, height_m: float) -> str:
    """
    Genera SVG de vista isométrica de cercha.
    La cercha se muestra con profundidad (ancho del perfil de los cordones).
    """
    L_mm = length_m * 1000
    H_mm = height_m * 1000
    sc = min(VW * 0.60 / L_mm, VH * 0.50 / H_mm)
    sc = max(sc, 0.008)

    ox, oy = VW * 0.15, VH * 0.75

    def iP(wx, wy, wz):
        return iso_point(wx, wy, wz, ox, oy, sc)

    c = COLORS
    pw = L_mm / panels
    parts = []

    def seg_3d(x1, y1, z1, x2, y2, z2, stroke, sw):
        p1 = iP(x1, y1, z1)
        p2 = iP(x2, y2, z2)
        return (f'<line x1="{p1.x:.1f}" y1="{p1.y:.1f}" '
                f'x2="{p2.x:.1f}" y2="{p2.y:.1f}" '
                f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>')

    def node_3d(wx, wy, wz, r=3.5):
        p = iP(wx, wy, wz)
        return (f'<circle cx="{p.x:.1f}" cy="{p.y:.1f}" r="{r}" '
                f'fill="{c["node_fill"]}" stroke="{c["node_stroke"]}" '
                f'stroke-width=".8"/>')

    # Nodos y coordenadas
    def get_y(i):
        if truss_type == 'fink':
            mid = panels / 2
            frac = i / mid if i <= mid else (panels - i) / mid
            return frac * H_mm
        return H_mm

    # Dos planos de la cercha (z=0 y z=400mm)
    depth = 400
    for z in [0, depth]:
        for i in range(panels):
            xi, xi1 = i * pw, (i + 1) * pw
            yi, yi1 = get_y(i), get_y(i + 1)

            parts.append(seg_3d(xi, 0, z, xi1, 0, z, c['flange'], 2.5))
            parts.append(seg_3d(xi, yi, z, xi1, yi1, z, c['flange'], 2.5))

            if truss_type != 'warren':
                parts.append(seg_3d(xi, 0, z, xi, yi, z, c['web'], 1.5))

            diags = _diagonals(truss_type, panels,
                                [{'x': j * pw, 'yb': 0, 'yt': get_y(j)}
                                 for j in range(panels + 1)])
            for (fa, ia, fb, ib) in diags:
                x1 = ia * pw; y1 = 0 if fa == 'bot' else get_y(ia)
                x2 = ib * pw; y2 = 0 if fb == 'bot' else get_y(ib)
                parts.append(seg_3d(x1, y1, z, x2, y2, z, c['web'], 1.2))

    # Travesaños (conectan los dos planos)
    for i in range(panels + 1):
        xi = i * pw; yi = get_y(i)
        parts.append(seg_3d(xi, 0, 0, xi, 0, depth, c['web'], 1.0))
        parts.append(seg_3d(xi, yi, 0, xi, yi, depth, c['web'], 1.0))

    # Nodos en ambos planos
    for z in [0, depth]:
        for i in range(panels + 1):
            xi = i * pw; yi = get_y(i)
            parts.append(node_3d(xi, 0, z))
            parts.append(node_3d(xi, yi, z))

    parts.append(panel_label(VW / 2, VH - 12, "Vista isométrica"))
    return svg_wrap("\n".join(parts), VW, VH)
```

---

## 11. Orquestador — `draw/element_viewer.py`

```python
# draw/element_viewer.py
# ESCALC Draw — Orquestador principal
# Recibe los parámetros, llama a cada módulo de dibujo
# y retorna un dict con los 4 strings SVG

from draw.elements.column  import draw_column_elevation, draw_column_isometric
from draw.elements.beam    import draw_beam_elevation,   draw_beam_isometric
from draw.elements.truss   import draw_truss_2d,         draw_truss_isometric
from draw.elements.section import draw_section_2d,       draw_section_props
from draw.section_props    import get_section_props


def generate_views(element_type: str, profile_type: str,
                   dims: dict, length_m: float,
                   truss_type: str = 'pratt', truss_panels: int = 6,
                   truss_height_m: float = 2.0,
                   show_dims: bool = True) -> dict:
    """
    Genera los 4 paneles SVG del visor de elementos.

    Args:
        element_type:   'column' | 'beam' | 'truss'
        profile_type:   'W' | 'C' | 'L' | 'HSS-R' | 'HSS-C' | 'SOLID'
        dims:           dict con dimensiones del perfil (mm)
        length_m:       longitud/altura del elemento (m)
        truss_type:     tipo de cercha (solo si element_type='truss')
        truss_panels:   número de vanos de la cercha
        truss_height_m: altura de la cercha (m)
        show_dims:      mostrar cotas en las vistas 2D

    Returns:
        dict con claves:
            'svg_elevation'  → panel de elevación 2D
            'svg_section'    → panel de sección transversal
            'svg_isometric'  → panel de vista isométrica
            'svg_props'      → panel de propiedades geométricas
            'props'          → objeto SectionProperties (para uso en cálculo)
    """
    result = {}

    if element_type == 'column':
        result['svg_elevation'] = draw_column_elevation(
            profile_type, dims, length_m, show_dims)
        result['svg_isometric'] = draw_column_isometric(
            profile_type, dims, length_m)

    elif element_type == 'beam':
        result['svg_elevation'] = draw_beam_elevation(
            profile_type, dims, length_m, show_dims)
        result['svg_isometric'] = draw_beam_isometric(
            profile_type, dims, length_m)

    elif element_type == 'truss':
        result['svg_elevation'] = draw_truss_2d(
            truss_type, truss_panels, length_m, truss_height_m, show_dims)
        result['svg_isometric'] = draw_truss_isometric(
            truss_type, truss_panels, length_m, truss_height_m)

    # Sección y propiedades (solo para columna y viga)
    if element_type != 'truss':
        result['svg_section'] = draw_section_2d(profile_type, dims)
        try:
            props = get_section_props(profile_type, **dims)
            result['svg_props'] = draw_section_props(profile_type, dims, props)
            result['props'] = props
        except Exception as e:
            result['svg_props'] = f'<p style="color:#e05252">Error: {e}</p>'
            result['props'] = None
    else:
        result['svg_section'] = draw_truss_2d(
            truss_type, truss_panels, length_m, truss_height_m, False)
        result['svg_props'] = '<svg viewBox="0 0 380 320"></svg>'
        result['props'] = None

    return result


def from_calculation(calc_result) -> dict:
    """
    Genera vistas a partir del resultado de un cálculo ESCALC.
    Recibe el objeto RafterResults (u otro) y extrae los parámetros.

    Uso desde el módulo Wood:
        from draw.element_viewer import from_calculation
        views = from_calculation(rafter_result)

    Returns:
        dict con los 4 SVG (igual que generate_views)
    """
    # Detectar tipo de objeto por atributos
    if hasattr(calc_result, 'b_in'):
        # Es un RafterResults (viga de madera)
        # Convertir pulgadas a mm
        dims = {
            'b':  calc_result.b_in * 25.4,
            'h':  calc_result.d_in * 25.4,
        }
        length_m = getattr(calc_result, 'rafter_length_ft', 12) * 0.3048
        return generate_views('beam', 'SOLID', dims, length_m)

    elif hasattr(calc_result, 'column_section'):
        # Es un resultado de columna de acero (módulo Elements futuro)
        s = calc_result.column_section
        return generate_views('column', s.profile_type, s.dims, s.height_m)

    else:
        raise ValueError("Tipo de resultado de cálculo no reconocido")
```

---

## 12. Rutas Flask — `routes/draw.py`

```python
# routes/draw.py
# ESCALC Draw — Blueprint Flask

from flask import Blueprint, render_template, request
from draw.element_viewer import generate_views

draw_bp = Blueprint('draw', __name__, template_folder='../templates')


def _parse_dims(form) -> dict:
    """Extrae y convierte dimensiones del formulario."""
    def f(key, default=0.0):
        try: return float(form.get(key, default))
        except: return default
    def i(key, default=0):
        try: return int(form.get(key, default))
        except: return default

    return {
        'd':     f('d', 300),    'bf':  f('bf', 150),
        'tf':    f('tf', 12),    'tw':  f('tw', 8),
        'leg_a': f('leg_a', 100),'leg_b': f('leg_b', 100),
        't':     f('t', 8),
        'D':     f('D', 150),    'B':   f('B', 100),
        'od':    f('od', 168),
        'b':     f('b', 150),    'h':   f('h', 200),
    }


@draw_bp.route('/', methods=['GET', 'POST'])
def viewer():
    """Visor libre de elementos — GET muestra formulario, POST procesa."""

    defaults = {
        'element_type':    'column',
        'profile_type':    'W',
        'length_m':        3.5,
        'truss_type':      'pratt',
        'truss_panels':    6,
        'truss_height_m':  2.0,
        'show_dims':       True,
        'd': 300, 'bf': 150, 'tf': 12, 'tw': 8,
        'leg_a': 100, 'leg_b': 100, 't': 8,
        'D': 150, 'B': 100, 'od': 168,
        'b': 150, 'h': 200,
    }

    if request.method == 'POST':
        form = request.form
        element_type = form.get('element_type', 'column')
        profile_type = form.get('profile_type', 'W')
        length_m     = float(form.get('length_m', 3.5))
        truss_type   = form.get('truss_type', 'pratt')
        truss_panels = int(form.get('truss_panels', 6))
        truss_h      = float(form.get('truss_height_m', 2.0))
        show_dims    = form.get('show_dims', 'true') == 'true'
        dims         = _parse_dims(form)

        views = generate_views(
            element_type, profile_type, dims, length_m,
            truss_type, truss_panels, truss_h, show_dims
        )

        return render_template('element_viewer.html',
            views=views, inputs=form, **defaults)

    # GET — vista inicial con valores por defecto
    views = generate_views('column', 'W',
        {'d': 300, 'bf': 150, 'tf': 12, 'tw': 8},
        length_m=3.5)

    return render_template('element_viewer.html',
        views=views, inputs=defaults, **defaults)
```

---

## 13. Template HTML — `templates/element_viewer.html`

```html
{% extends "base.html" %}
{% block title %}Element Viewer{% endblock %}

{% block content %}
<div class="viewer-layout">

  <!-- SIDEBAR ────────────────────────────────────── -->
  <aside class="viewer-sidebar">
    <form method="POST" action="/draw/" id="viewer-form">

      <div class="s-group">
        <div class="s-title">Elemento</div>
        <div class="btn-group-3">
          {% for val, label in [('column','Columna'),('beam','Viga'),('truss','Cercha')] %}
          <label class="radio-btn {{ 'active' if inputs.get('element_type','column')==val else '' }}">
            <input type="radio" name="element_type" value="{{ val }}"
              {{ 'checked' if inputs.get('element_type','column')==val else '' }}
              onchange="togglePanels(this.value)"> {{ label }}
          </label>
          {% endfor %}
        </div>
      </div>

      <!-- Panel perfil (columna/viga) -->
      <div class="s-group" id="panel-profile">
        <div class="s-title">Perfil</div>
        <div class="field">
          <label>Tipo</label>
          <select name="profile_type" onchange="toggleDimFields(this.value)">
            {% for val, label in [('W','W / IPE — doble T'),('C','C / UPN — canal'),
                                   ('L','L — angular'),('HSS-R','HSS rectangular'),
                                   ('HSS-C','HSS circular'),('SOLID','Sección maciza')] %}
            <option value="{{ val }}" {{ 'selected' if inputs.get('profile_type','W')==val else '' }}>
              {{ label }}
            </option>
            {% endfor %}
          </select>
        </div>

        <!-- Campos W/C -->
        <div id="dims-W" class="dim-set">
          <div class="field-row">
            <div class="field"><label>d <span class="u">mm</span></label>
              <input type="number" name="d" value="{{ inputs.get('d',300) }}" step="10" min="100" max="900" oninput="submitForm()"></div>
            <div class="field"><label>bf <span class="u">mm</span></label>
              <input type="number" name="bf" value="{{ inputs.get('bf',150) }}" step="5" min="50" max="400" oninput="submitForm()"></div>
          </div>
          <div class="field-row">
            <div class="field"><label>tf <span class="u">mm</span></label>
              <input type="number" name="tf" value="{{ inputs.get('tf',12) }}" step="1" min="5" max="40" oninput="submitForm()"></div>
            <div class="field"><label>tw <span class="u">mm</span></label>
              <input type="number" name="tw" value="{{ inputs.get('tw',8) }}" step="1" min="3" max="30" oninput="submitForm()"></div>
          </div>
        </div>

        <!-- Campos HSS-R -->
        <div id="dims-HSS-R" class="dim-set" style="display:none">
          <div class="field-row">
            <div class="field"><label>D <span class="u">mm</span></label>
              <input type="number" name="D" value="{{ inputs.get('D',150) }}" step="10" min="50" max="500" oninput="submitForm()"></div>
            <div class="field"><label>B <span class="u">mm</span></label>
              <input type="number" name="B" value="{{ inputs.get('B',100) }}" step="10" min="50" max="400" oninput="submitForm()"></div>
          </div>
          <div class="field"><label>t <span class="u">mm</span></label>
            <input type="number" name="t" value="{{ inputs.get('t',8) }}" step="1" min="3" max="25" oninput="submitForm()"></div>
        </div>

        <!-- Campos HSS-C -->
        <div id="dims-HSS-C" class="dim-set" style="display:none">
          <div class="field-row">
            <div class="field"><label>OD <span class="u">mm</span></label>
              <input type="number" name="od" value="{{ inputs.get('od',168) }}" step="10" min="50" max="600" oninput="submitForm()"></div>
            <div class="field"><label>t <span class="u">mm</span></label>
              <input type="number" name="t" value="{{ inputs.get('t',8) }}" step="1" min="3" max="25" oninput="submitForm()"></div>
          </div>
        </div>

        <!-- Campos L -->
        <div id="dims-L" class="dim-set" style="display:none">
          <div class="field-row">
            <div class="field"><label>Lado a <span class="u">mm</span></label>
              <input type="number" name="leg_a" value="{{ inputs.get('leg_a',100) }}" step="5" min="30" max="250" oninput="submitForm()"></div>
            <div class="field"><label>Lado b <span class="u">mm</span></label>
              <input type="number" name="leg_b" value="{{ inputs.get('leg_b',100) }}" step="5" min="30" max="250" oninput="submitForm()"></div>
          </div>
          <div class="field"><label>t <span class="u">mm</span></label>
            <input type="number" name="t" value="{{ inputs.get('t',8) }}" step="1" min="3" max="20" oninput="submitForm()"></div>
        </div>

        <!-- Campos SOLID -->
        <div id="dims-SOLID" class="dim-set" style="display:none">
          <div class="field-row">
            <div class="field"><label>b <span class="u">mm</span></label>
              <input type="number" name="b" value="{{ inputs.get('b',150) }}" step="10" min="50" max="600" oninput="submitForm()"></div>
            <div class="field"><label>h <span class="u">mm</span></label>
              <input type="number" name="h" value="{{ inputs.get('h',200) }}" step="10" min="50" max="800" oninput="submitForm()"></div>
          </div>
        </div>
      </div>

      <!-- Panel cercha -->
      <div class="s-group" id="panel-truss" style="display:none">
        <div class="s-title">Geometría cercha</div>
        <div class="field">
          <label>Tipo</label>
          <select name="truss_type" oninput="submitForm()">
            {% for val, label in [('pratt','Pratt'),('howe','Howe'),('warren','Warren'),('fink','Fink — techo')] %}
            <option value="{{ val }}" {{ 'selected' if inputs.get('truss_type','pratt')==val else '' }}>{{ label }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field-row">
          <div class="field"><label>Vanos</label>
            <input type="number" name="truss_panels" value="{{ inputs.get('truss_panels',6) }}" step="1" min="2" max="12" oninput="submitForm()"></div>
          <div class="field"><label>Altura <span class="u">m</span></label>
            <input type="number" name="truss_height_m" value="{{ inputs.get('truss_height_m',2.0) }}" step="0.5" min="0.5" max="8" oninput="submitForm()"></div>
        </div>
      </div>

      <!-- Longitud -->
      <div class="s-group">
        <div class="s-title" id="len-title">Altura columna</div>
        <div class="field">
          <label id="len-label">metros</label>
          <input type="number" name="length_m" value="{{ inputs.get('length_m',3.5) }}"
            step="0.5" min="0.5" max="30" oninput="submitForm()">
        </div>
      </div>

      <!-- Cotas -->
      <div class="s-group">
        <div class="s-title">Opciones</div>
        <label class="toggle-label">
          <input type="checkbox" name="show_dims" value="true"
            {{ 'checked' if inputs.get('show_dims',True) else '' }}
            onchange="submitForm()">
          Mostrar cotas
        </label>
      </div>

      <button type="submit" class="btn-primary">Actualizar</button>
    </form>
  </aside>

  <!-- CANVAS ─────────────────────────────────────── -->
  <main class="viewer-canvas">
    <div class="view-grid">
      <div class="view-pane">
        <div class="view-label">Elevación 2D</div>
        {{ views.svg_elevation | safe }}
      </div>
      <div class="view-pane">
        <div class="view-label">Sección transversal</div>
        {{ views.svg_section | safe }}
      </div>
      <div class="view-pane">
        <div class="view-label">Vista isométrica</div>
        {{ views.svg_isometric | safe }}
      </div>
      <div class="view-pane">
        <div class="view-label">Propiedades geométricas</div>
        {{ views.svg_props | safe }}
      </div>
    </div>
  </main>
</div>

<script>
let debounce;
function submitForm(){
  clearTimeout(debounce);
  debounce = setTimeout(()=>document.getElementById('viewer-form').submit(), 400);
}

function togglePanels(val){
  document.getElementById('panel-profile').style.display = val==='truss'?'none':'block';
  document.getElementById('panel-truss').style.display   = val==='truss'?'block':'none';
  const lenTitles = {column:'Altura columna', beam:'Longitud viga', truss:'Luz total'};
  document.getElementById('len-title').textContent = lenTitles[val] || 'Longitud';
  submitForm();
}

function toggleDimFields(type){
  document.querySelectorAll('.dim-set').forEach(el=>el.style.display='none');
  const map = {'W':'dims-W','C':'dims-W','L':'dims-L',
               'HSS-R':'dims-HSS-R','HSS-C':'dims-HSS-C','SOLID':'dims-SOLID'};
  const el = document.getElementById(map[type]);
  if(el) el.style.display = 'block';
  submitForm();
}

toggleDimFields('{{ inputs.get("profile_type","W") }}');
</script>
{% endblock %}
```

---

## 14. CSS del visor — `static/css/viewer.css`

```css
/* viewer.css — ESCALC Draw — Visor de elementos estructurales */

.viewer-layout {
  display: grid;
  grid-template-columns: 230px 1fr;
  gap: 0;
  height: calc(100vh - 52px);
}

.viewer-sidebar {
  background: var(--surf);
  border-right: 1px solid var(--brd);
  padding: 14px 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.s-group {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--brd);
}
.s-group:last-child { border-bottom: none; }

.s-title {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .07em;
  color: var(--txt3);
  margin-bottom: 6px;
}

.btn-group-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
}

.radio-btn {
  display: block;
  background: var(--surf2);
  border: 1px solid var(--brd);
  border-radius: 5px;
  padding: 6px 4px;
  text-align: center;
  cursor: pointer;
  font-size: 11px;
  color: var(--txt2);
  transition: all .15s;
  user-select: none;
}
.radio-btn input { display: none; }
.radio-btn.active,
.radio-btn:has(input:checked) {
  background: var(--acc2);
  border-color: var(--acc);
  color: #fff;
}

.viewer-canvas {
  background: var(--bg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.view-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 1px;
  background: var(--brd);
  flex: 1;
}

.view-pane {
  background: var(--surf);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.view-label {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: .07em;
  color: var(--txt3);
  padding: 6px 10px 2px;
  flex-shrink: 0;
}

.view-pane svg {
  flex: 1;
  display: block;
  width: 100%;
  height: 100%;
}

.u {
  font-size: 9px;
  color: var(--txt3);
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--txt2);
  cursor: pointer;
}

.btn-primary {
  width: 100%;
  background: var(--acc);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 9px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
}
.btn-primary:hover { opacity: .85; }
```

---

## 15. Integración con módulos de cálculo

### Llamada desde ESCALC Wood (rafter)

```python
# En routes/wood.py — después del cálculo
from draw.element_viewer import from_calculation

@wood_bp.route("/rafter/calcular", methods=["POST"])
def rafter_calcular():
    # ... cálculo existente ...
    result = calc.calculate()

    # Generar vistas automáticamente desde el resultado
    views = from_calculation(result)

    return render_template("rafter.html",
        result=result,
        views=views,        # ← las 4 vistas SVG
        svg=svg_content,
        inputs=form,
        ...
    )
```

En el template `rafter.html` se agrega la sección de vistas:

```html
{% if views %}
<div class="check-panel" style="margin-top:1rem">
  <div class="check-panel-title">Visualización del perfil</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">
    <div>{{ views.svg_elevation | safe }}</div>
    <div>{{ views.svg_section  | safe }}</div>
  </div>
</div>
{% endif %}
```

### Registro del Blueprint en `app.py`

```python
from routes.draw import draw_bp
app.register_blueprint(draw_bp, url_prefix="/draw")

# Rutas disponibles:
# GET  /draw/           → visor libre
# POST /draw/           → actualiza vistas con nuevos parámetros
```

---

## 16. Convenciones de dibujo técnico

Estas reglas rigen todo el módulo. Si generás código nuevo, respetarlas siempre:

| Convención | Regla ESCALC Draw |
|---|---|
| Línea visible | stroke-width = 1.5, color `#d0e0f0` |
| Línea oculta | stroke-width = 0.6, `stroke-dasharray="5 3"` |
| Eje de simetría | stroke-width = 0.5, `stroke-dasharray="8 3 2 3"` |
| Hatching sección | ángulo 45°, spacing 4px, opacity 0.35 |
| Cotas | font-size 9px, color `#5a7aaa`, puntos terminales r=1.8 |
| Isométrica | proyección axonométrica 30° estándar |
| Cara en luz | `#d8e8f4` (flange claro) |
| Cara en sombra | `#6a7a8a` (oscuro) |
| Cara lateral media | `#8a9aaa` |
| Nodos de cercha | círculo r=3.5, fill `#c8d8ec` |
| Rótula | triángulo 12px con línea base |
| Rodillo | rectángulo 10px con línea base |

---

## 17. Valores de prueba

Ejecutar `python test_draw.py` en la carpeta `draw/`:

```python
# test_draw.py
from draw.element_viewer import generate_views
from draw.section_props  import get_section_props

def test_columna_W():
    dims = {'d':300,'bf':150,'tf':12,'tw':8}
    views = generate_views('column','W', dims, length_m=4.0)
    assert views['svg_elevation'].startswith('<svg')
    assert views['svg_isometric'].startswith('<svg')
    props = get_section_props('W', **dims)
    assert abs(props.A_cm2 - 58.8) < 5, f"Área W300×150 ≈ 58.8 cm², got {props.A_cm2:.1f}"
    print(f"✓ Columna W300×150 | A={props.A_cm2:.1f}cm² Ix={props.Ix_cm4:.0f}cm⁴")

def test_viga_HSS_R():
    dims = {'D':200,'B':100,'t':8}
    views = generate_views('beam','HSS-R', dims, length_m=6.0)
    assert views['svg_elevation'].startswith('<svg')
    props = get_section_props('HSS-R', **dims)
    print(f"✓ Viga HSS 200×100×8 | A={props.A_cm2:.1f}cm² Ix={props.Ix_cm4:.0f}cm⁴")

def test_cercha_pratt():
    views = generate_views('truss','W',{}, length_m=12.0,
                            truss_type='pratt', truss_panels=6, truss_height_m=2.0)
    assert views['svg_elevation'].startswith('<svg')
    assert views['svg_isometric'].startswith('<svg')
    print("✓ Cercha Pratt 12m 6 vanos")

def test_circ_HSS():
    dims = {'od':168,'t':8}
    props = get_section_props('HSS-C', **dims)
    # A teórico = π/4*(168²-152²) ≈ 40.5 cm²
    assert abs(props.A_cm2 - 40.5) < 3, f"HSS-C OD168 t8 ≈ 40.5 cm², got {props.A_cm2:.1f}"
    print(f"✓ HSS circular OD168×8 | A={props.A_cm2:.1f}cm²")

if __name__ == '__main__':
    print("=== ESCALC Draw — Tests ===")
    test_columna_W()
    test_viga_HSS_R()
    test_cercha_pratt()
    test_circ_HSS()
    print("=== Todos OK ===")
```

---

## 18. Roadmap — extensiones futuras

| Feature | Descripción | Prioridad |
|---|---|---|
| **Exportar SVG** | Botón "Descargar SVG" del panel activo | Alta |
| **Exportar DXF** | Generar archivo DXF con `ezdxf` para importar en AutoCAD | Alta |
| **Perfil madera** | Sección rectangular de madera con veta (para ESCALC Wood) | Alta |
| **Perfil compuesto** | Doble T compuesto (ala de acero + alma de concreto) | Media |
| **Tabla AISC** | Selector de perfil por nombre ("W12×26", "HSS6×4×3/8") | Media |
| **Tabla CIRSOC** | Perfiles laminados argentinos (IPN, IPE, HEB, HEA) | Media |
| **Zoom y pan SVG** | Interacción mouse en el viewport (sin JS externo) | Media |
| **Detalle de soldadura** | Vista de extremo de viga con planchas y pernos | Baja |
| **Múltiples elementos** | Vista de pórtico: columna + viga ensambladas | Baja |

---

*ESCALC Draw — Documento Maestro v1.0*  
*Engineering Software CALC — Módulo: Visualizador de Elementos Estructurales*  
*Stack: Python 3.11 · Flask · SVG puro (sin dependencias de dibujo externas)*  
*Elementos: Columna · Viga · Cercha (Pratt / Howe / Warren / Fink)*  
*Perfiles: W · C · L · HSS-R · HSS-C · Sección maciza*  
*IDE: Visual Studio Code — python app.py → http://localhost:5050/draw*
