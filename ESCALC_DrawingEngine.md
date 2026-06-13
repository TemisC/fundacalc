# ESCALC — Motor de Dibujo Técnico de Conexiones en Acero
## Contexto para Agente de Desarrollo | Módulo: Conexiones Estructurales
## Versión 1.0 | Engineering Software CALC

---

## PROPÓSITO DE ESTE DOCUMENTO

Este archivo es el **contexto técnico base** que debe pegarse al inicio de cualquier
sesión de desarrollo del motor de dibujo de conexiones de ESCALC.

Contiene:
1. Diccionario geométrico → vocabulario técnico traducido a coordenadas SVG
2. Convenciones de línea → estándar de representación según norma ISO/ANSI
3. Sistema de vistas → las 5 vistas estándar de ESCALC Conexiones
4. Biblioteca de primitivas SVG → funciones listas para usar
5. Reglas de proyección isométrica para acero estructural
6. Ejemplos de referencia SVG correctos
7. Reglas de composición del motor de dibujo

---

## PARTE 1 — DICCIONARIO GEOMÉTRICO

### 1.1 Perfil W (Wide Flange) — Sección transversal

```
Un perfil W en SECCIÓN TRANSVERSAL tiene exactamente esta geometría:

        ←————— bf ——————→
        ┌───────────────┐  ← ala superior (top flange)
        │               │    alto = tf, ancho = bf
        └───┐       ┌───┘
            │       │      ← filetes (arcos de transición)
            │       │
            │       │  ← alma (web)
            │       │    alto ≈ d - 2tf, ancho = tw
            │       │
        ┌───┘       └───┐
        │               │  ← ala inferior (bottom flange)
        └───────────────┘
        ↕ d (altura total)

Variables:
  d  = altura total del perfil [mm]
  bf = ancho del ala [mm]
  tf = espesor del ala [mm]
  tw = espesor del alma [mm]
  k  = distancia borde ala a cara interna del alma (filete incluido)
```

### 1.2 Perfil W — Vista lateral (elevación)

```
Cuando el perfil W se ve DE FRENTE (elevación), aparece como:

  ─────────────────────  ← borde exterior ala superior
  ─  ─  ─  ─  ─  ─  ─   ← cara interior ala superior (línea oculta si hay corte)
           │
           │  ← alma (línea vertical)
           │
  ─  ─  ─  ─  ─  ─  ─   ← cara interior ala inferior
  ─────────────────────  ← borde exterior ala inferior

Cuando el perfil W se ve DE COSTADO, aparece como un rectángulo
con la altura del perfil y un ancho igual a bf.
```

### 1.3 Alma vs Ala — Distinción crítica

```
ALMA (web):
  → Placa VERTICAL y DELGADA en el centro del perfil
  → Resiste el CORTE (fuerza cortante)
  → tw típico: 6-15 mm
  → En sección: rectángulo angosto y alto

ALA (flange):
  → Placa HORIZONTAL y ANCHA en la parte superior e inferior
  → Resiste la FLEXIÓN (momento flector)
  → tf típico: 10-25 mm, bf típico: 150-300 mm
  → En sección: rectángulo ancho y delgado

REGLA VISUAL:
  Si la viga conecta al ALMA de la columna:
  → La columna se ve DE PERFIL (las alas se ven como siluetas laterales)
  → Las alas de la VIGA quedan libres (sin contacto)

  Si la viga conecta al ALA de la columna:
  → La columna se ve DE FRENTE (las alas son lo primero que se ve)
  → La plancha (shear tab) se suelda al ALA, no al alma
```

### 1.4 Perno en sección transversal (corte perpendicular al eje del perno)

```
Representación estándar ANSI/ISO:
  ┌─────────────────────────────┐
  │  Vista en sección:          │
  │                             │
  │    ╔═══╗   ← arandela      │
  │   ╔═════╗  ← cabeza         │
  │   ║  ●  ║  ← cuerpo        │  ● = círculo lleno negro radio r
  │   ╚═════╝  ← tuerca        │    + círculo exterior radio 1.5r
  │    ╚═══╝                   │    + línea de rosca (círculo punteado)
  │                             │
  │  Símbolo SVG correcto:      │
  │  <circle r="r" fill="#222"/>│ cuerpo del perno
  │  <circle r="r*1.4" fill=   │ agujero/arandela
  │    "none" stroke="#222"/>   │
  └─────────────────────────────┘

Representación en vista lateral (perno visto de costado):
  ┌─────────────────────────────┐
  │   ├──────────────────────┤  │ ← longitud del perno
  │   □ ══════════════════ □  │ ← línea con rectángulos en cabeza/tuerca
  └─────────────────────────────┘
```

### 1.5 Soldadura en filete — representación

```
Símbolo en sección:
  La soldadura filete se representa como un triángulo isósceles
  en el vértice donde se unen dos planchas.

  Plancha vertical
  │
  │◣ ← triángulo relleno, cateto = tamaño del filete (w)
  └────────── Plancha horizontal

  En SVG:
  <polygon points="x,y  x,y+w  x+w,y" fill="#EF9F27"/>

Símbolo en elevación (vista lateral de la soldadura):
  Se representa como una línea gruesa continua naranja/amarilla
  a lo largo de la unión.
```

---

## PARTE 2 — CONVENCIONES DE LÍNEA

Estas son las reglas de stroke que el motor de dibujo DEBE respetar:

```javascript
// ESCALC Drawing Engine — Stroke Conventions
const STROKE = {
  // Línea visible principal (contorno de elementos)
  VISIBLE:     { stroke: '#1A1A1A', strokeWidth: 1.5, strokeDasharray: 'none' },

  // Línea oculta (elemento detrás de otro — norma ISO 128)
  HIDDEN:      { stroke: '#444444', strokeWidth: 0.7, strokeDasharray: '5,3' },

  // Eje de simetría / línea de centro
  CENTER:      { stroke: '#888888', strokeWidth: 0.5, strokeDasharray: '8,3,2,3' },

  // Línea de corte (indica dónde se realiza la sección)
  CUTTING:     { stroke: '#1A1A1A', strokeWidth: 2.0, strokeDasharray: 'none' },

  // Línea de cota / dimensión
  DIMENSION:   { stroke: '#555555', strokeWidth: 0.5, strokeDasharray: 'none' },

  // Línea de referencia / leader
  LEADER:      { stroke: '#555555', strokeWidth: 0.6, strokeDasharray: 'none' },

  // Soldadura filete
  WELD_FILLET: { stroke: '#EF9F27', strokeWidth: 3.0, strokeDasharray: 'none' },

  // Soldadura ranura
  WELD_GROOVE: { stroke: '#EF9F27', strokeWidth: 1.5, strokeDasharray: 'none' },

  // Eje del perno
  BOLT_AXIS:   { stroke: '#888888', strokeWidth: 0.4, strokeDasharray: '4,2' },
};

// Paleta de rellenos
const FILL = {
  STEEL_SECTION:  '#D0CEC8',  // sección cortada (hatching o gris sólido)
  STEEL_SURFACE:  '#E8E6E0',  // superficie visible del acero
  STEEL_SHADOW:   '#B0AEA8',  // cara en sombra (isométrica)
  PLATE:          '#85B7EB',  // plancha de conexión (shear tab, end plate)
  BOLT_BODY:      '#222222',  // cuerpo del perno en sección
  BOLT_NUT:       '#444444',  // tuerca
  WELD:           '#EF9F27',  // soldadura
  BACKGROUND:     '#FFFFFF',
  HATCHING:       '#1A1A1A',  // líneas de sección (hatching 45°)
};
```

---

## PARTE 3 — SISTEMA DE VISTAS ESCALC CONEXIONES

El motor de dibujo de ESCALC usa 5 tipos de vista. Cada vista tiene su viewport SVG definido:

```
┌────────────────────────────────────────────────────────────────┐
│  SISTEMA DE VISTAS ESTÁNDAR ESCALC                             │
│                                                                │
│  VISTA_A: Planta          → mirar desde ARRIBA (eje Z→)       │
│  VISTA_B: Elevación       → mirar desde el FRENTE (eje Y→)    │
│  VISTA_C: Lateral         → mirar desde el COSTADO (eje X→)   │
│  VISTA_D: Sección X-X     → corte transversal al eje mayor    │
│  VISTA_E: Isométrica 3D   → proyección isométrica estándar     │
│                                                                │
│  Composición por defecto para conexión simple (shear tab):     │
│                                                                │
│  ┌──────────────┬──────────────────┐                          │
│  │              │                  │                          │
│  │   VISTA_E    │    VISTA_B       │                          │
│  │  Isométrica  │  Elevación front │                          │
│  │     3D       │  (columna frente)│                          │
│  │              │                  │                          │
│  └──────────────┴──────────────────┘                          │
│                                                                │
│  Composición para detalle de pernos:                           │
│  ┌────────┬────────┬────────┐                                  │
│  │VISTA_B │VISTA_C │VISTA_D │                                  │
│  │Elevac. │Lateral │Secc.XX │                                  │
│  └────────┴────────┴────────┘                                  │
└────────────────────────────────────────────────────────────────┘
```

### Proyección isométrica — reglas matemáticas

```javascript
// Transformación de coordenadas 3D → isométrica 2D
// Eje isométrico estándar: 30° con la horizontal

const ISO = {
  // Factor de escala isométrico
  SCALE: 1.0,

  // Vectores unitarios de los 3 ejes en pantalla (coordenadas SVG)
  // Eje X (derecha-frente):  cos(30°) = 0.866, sin(30°) = 0.5
  // Eje Y (izquierda-frente): cos(150°) = -0.866, sin(150°) = -0.5 (en SVG Y invertido)
  // Eje Z (vertical):         x=0, y=-1 (hacia arriba en pantalla)

  xAxis: { dx:  0.866, dy:  0.5  },  // vector X isométrico
  yAxis: { dx: -0.866, dy:  0.5  },  // vector Y isométrico
  zAxis: { dx:  0,     dy: -1.0  },  // vector Z isométrico (vertical)

  // Función de proyección
  project(x3d, y3d, z3d) {
    return {
      x: x3d * this.xAxis.dx + y3d * this.yAxis.dx + z3d * this.zAxis.dx,
      y: x3d * this.xAxis.dy + y3d * this.yAxis.dy + z3d * this.zAxis.dy,
    };
  },
};

// Ejemplo: esquina de una placa en 3D → coordenadas SVG
// Placa en plano XZ (vertical, frente a la columna):
// punto (x=0, y=0, z=100) → ISO.project(0, 0, 100) = { x:0, y:-100 }
// punto (x=50, y=0, z=100) → ISO.project(50, 0, 100) = { x:43.3, y:-75 }
```

---

## PARTE 4 — BIBLIOTECA DE PRIMITIVAS SVG

Estas funciones son el núcleo del motor de dibujo. El agente DEBE usar estas
funciones en lugar de dibujar geometría desde cero.

```javascript
// ═══════════════════════════════════════════════════════════════
// ESCALC Drawing Engine — Primitivas SVG v1.0
// Archivo: js/drawing/primitives.js
// ═══════════════════════════════════════════════════════════════

'use strict';

// ── HELPERS ─────────────────────────────────────────────────────

/** Crea un elemento SVG con atributos */
function svgEl(tag, attrs, parent) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  if (parent) parent.appendChild(el);
  return el;
}

/** Construye un string de puntos para polygon */
function pts(...coords) {
  return coords.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
}

// ── PRIMITIVA 1: PERFIL W EN SECCIÓN TRANSVERSAL ────────────────
/**
 * Dibuja un perfil W en sección transversal (corte)
 * @param {SVGElement} svg   - contenedor SVG
 * @param {number} cx        - centro X
 * @param {number} cy        - centro Y (mitad de altura)
 * @param {Object} p         - propiedades: { d, bf, tf, tw } en mm → escalar con scale
 * @param {number} scale     - mm por pixel
 * @param {string} fill      - color de relleno de la sección
 * @param {boolean} hatching - si true dibuja rayado de sección
 */
function drawPerfilW_Seccion(svg, cx, cy, p, scale = 1, fill = FILL.STEEL_SECTION, hatching = true) {
  const { d, bf, tf, tw } = p;
  const D  = d  * scale;   // altura total en px
  const BF = bf * scale;   // ancho ala en px
  const TF = tf * scale;   // espesor ala en px
  const TW = tw * scale;   // espesor alma en px

  const g = svgEl('g', { class: 'perfil-w-seccion' }, svg);

  // Ala superior
  svgEl('rect', {
    x: cx - BF/2, y: cy - D/2,
    width: BF, height: TF,
    fill, stroke: STROKE.VISIBLE.stroke, 'stroke-width': STROKE.VISIBLE.strokeWidth
  }, g);

  // Alma
  svgEl('rect', {
    x: cx - TW/2, y: cy - D/2 + TF,
    width: TW, height: D - 2*TF,
    fill, stroke: STROKE.VISIBLE.stroke, 'stroke-width': STROKE.VISIBLE.strokeWidth
  }, g);

  // Ala inferior
  svgEl('rect', {
    x: cx - BF/2, y: cy + D/2 - TF,
    width: BF, height: TF,
    fill, stroke: STROKE.VISIBLE.stroke, 'stroke-width': STROKE.VISIBLE.strokeWidth
  }, g);

  // Rayado de sección (hatching 45°)
  if (hatching) drawHatching(svg, cx, cy, BF, D, TW, TF);

  return g;
}

// ── PRIMITIVA 2: PERFIL W EN ELEVACIÓN (vista lateral) ──────────
/**
 * Dibuja un perfil W visto de frente (elevación)
 * Las alas aparecen como líneas horizontales, el alma como rectángulo vertical
 * @param {SVGElement} svg
 * @param {number} x0   - extremo izquierdo
 * @param {number} y0   - tope superior
 * @param {number} L    - longitud visible del perfil
 * @param {Object} p    - propiedades { d, bf, tf, tw }
 * @param {number} scale
 */
function drawPerfilW_Elevacion(svg, x0, y0, L, p, scale = 1) {
  const { d, tf, tw } = p;
  const D  = d  * scale;
  const TF = tf * scale;
  const TW = tw * scale;

  const g = svgEl('g', { class: 'perfil-w-elevacion' }, svg);

  // Borde exterior ala superior
  svgEl('line', { x1: x0, y1: y0, x2: x0 + L, y2: y0,
    stroke: STROKE.VISIBLE.stroke, 'stroke-width': STROKE.VISIBLE.strokeWidth }, g);

  // Cara interior ala superior (línea oculta o visible según corte)
  svgEl('line', { x1: x0, y1: y0 + TF, x2: x0 + L, y2: y0 + TF,
    stroke: STROKE.HIDDEN.stroke, 'stroke-width': STROKE.HIDDEN.strokeWidth,
    'stroke-dasharray': STROKE.HIDDEN.strokeDasharray }, g);

  // Alma (líneas laterales)
  svgEl('line', { x1: x0, y1: y0 + TF, x2: x0, y2: y0 + D - TF,
    stroke: STROKE.VISIBLE.stroke, 'stroke-width': STROKE.VISIBLE.strokeWidth }, g);
  svgEl('line', { x1: x0 + L, y1: y0 + TF, x2: x0 + L, y2: y0 + D - TF,
    stroke: STROKE.VISIBLE.stroke, 'stroke-width': STROKE.VISIBLE.strokeWidth }, g);

  // Cara interior ala inferior
  svgEl('line', { x1: x0, y1: y0 + D - TF, x2: x0 + L, y2: y0 + D - TF,
    stroke: STROKE.HIDDEN.stroke, 'stroke-width': STROKE.HIDDEN.strokeWidth,
    'stroke-dasharray': STROKE.HIDDEN.strokeDasharray }, g);

  // Borde exterior ala inferior
  svgEl('line', { x1: x0, y1: y0 + D, x2: x0 + L, y2: y0 + D,
    stroke: STROKE.VISIBLE.stroke, 'stroke-width': STROKE.VISIBLE.strokeWidth }, g);

  return g;
}

// ── PRIMITIVA 3: PERNO EN SECCIÓN ───────────────────────────────
/**
 * Dibuja un perno visto en sección (círculo + cruz de ejes)
 * @param {SVGElement} svg
 * @param {number} cx, cy  - centro del perno
 * @param {number} db      - diámetro nominal del perno [px]
 * @param {boolean} showAxis - mostrar ejes de centro
 */
function drawPerno_Seccion(svg, cx, cy, db, showAxis = true) {
  const r  = db / 2;
  const g = svgEl('g', { class: 'perno-seccion' }, svg);

  // Agujero (círculo exterior — diámetro del agujero ≈ db + 1.6mm)
  svgEl('circle', { cx, cy, r: r * 1.1,
    fill: FILL.BACKGROUND,
    stroke: STROKE.VISIBLE.stroke, 'stroke-width': STROKE.VISIBLE.strokeWidth }, g);

  // Cuerpo del perno
  svgEl('circle', { cx, cy, r,
    fill: FILL.BOLT_BODY,
    stroke: STROKE.VISIBLE.stroke, 'stroke-width': '0.5' }, g);

  // Rosca (círculo interior punteado)
  svgEl('circle', { cx, cy, r: r * 0.7,
    fill: 'none',
    stroke: '#666', 'stroke-width': '0.4',
    'stroke-dasharray': '3,2' }, g);

  // Ejes de centro (línea de centro cruzada)
  if (showAxis) {
    const ext = r * 1.8;
    // Horizontal
    svgEl('line', { x1: cx - ext, y1: cy, x2: cx + ext, y2: cy,
      stroke: STROKE.CENTER.stroke, 'stroke-width': STROKE.CENTER.strokeWidth,
      'stroke-dasharray': STROKE.CENTER.strokeDasharray }, g);
    // Vertical
    svgEl('line', { x1: cx, y1: cy - ext, x2: cx, y2: cy + ext,
      stroke: STROKE.CENTER.stroke, 'stroke-width': STROKE.CENTER.strokeWidth,
      'stroke-dasharray': STROKE.CENTER.strokeDasharray }, g);
  }

  return g;
}

// ── PRIMITIVA 4: PERNO EN ELEVACIÓN ─────────────────────────────
/**
 * Dibuja un perno visto de costado (vista lateral)
 * @param {SVGElement} svg
 * @param {number} x0   - extremo izquierdo del perno (cabeza)
 * @param {number} cy   - centro vertical
 * @param {number} L    - longitud total [px]
 * @param {number} db   - diámetro [px]
 */
function drawPerno_Elevacion(svg, x0, cy, L, db) {
  const r  = db / 2;
  const hw = r * 1.2;   // semi-ancho de cabeza/tuerca
  const hl = r * 1.4;   // longitud de cabeza/tuerca
  const g = svgEl('g', { class: 'perno-elevacion' }, svg);

  // Cabeza hexagonal (simplificada como rectángulo)
  svgEl('rect', { x: x0, y: cy - hw, width: hl, height: hw * 2,
    fill: FILL.BOLT_NUT, stroke: STROKE.VISIBLE.stroke,
    'stroke-width': STROKE.VISIBLE.strokeWidth }, g);

  // Vástago
  svgEl('rect', { x: x0 + hl, y: cy - r, width: L - 2*hl, height: db,
    fill: FILL.BOLT_BODY, stroke: STROKE.VISIBLE.stroke,
    'stroke-width': '0.5' }, g);

  // Rosca (zona roscada — último 30% del vástago)
  const rz_start = x0 + hl + (L - 2*hl) * 0.7;
  svgEl('line', { x1: rz_start, y1: cy - r, x2: x0 + L - hl, y2: cy - r,
    stroke: '#666', 'stroke-width': '0.5', 'stroke-dasharray': '2,1' }, g);

  // Tuerca
  svgEl('rect', { x: x0 + L - hl, y: cy - hw, width: hl, height: hw * 2,
    fill: FILL.BOLT_NUT, stroke: STROKE.VISIBLE.stroke,
    'stroke-width': STROKE.VISIBLE.strokeWidth }, g);

  // Eje de centro
  svgEl('line', { x1: x0, y1: cy, x2: x0 + L, y2: cy,
    stroke: STROKE.CENTER.stroke, 'stroke-width': STROKE.CENTER.strokeWidth,
    'stroke-dasharray': STROKE.CENTER.strokeDasharray }, g);

  return g;
}

// ── PRIMITIVA 5: PLANCHA RECTANGULAR ────────────────────────────
/**
 * Dibuja una plancha rectangular (shear tab, end plate, etc.)
 * @param {SVGElement} svg
 * @param {number} x, y      - esquina superior izquierda
 * @param {number} w, h      - ancho y alto
 * @param {string} tipo      - 'shear_tab' | 'end_plate' | 'base_plate' | 'stiffener'
 */
function drawPlancha(svg, x, y, w, h, tipo = 'shear_tab') {
  const colores = {
    shear_tab:  { fill: FILL.PLATE,         stroke: '#185FA5' },
    end_plate:  { fill: '#A8D4F5',           stroke: '#0D4A8A' },
    base_plate: { fill: '#C8D8E8',           stroke: '#2A5580' },
    stiffener:  { fill: FILL.STEEL_SECTION,  stroke: '#333' },
  };
  const c = colores[tipo] || colores.shear_tab;
  const g = svgEl('g', { class: `plancha-${tipo}` }, svg);

  svgEl('rect', { x, y, width: w, height: h,
    fill: c.fill, stroke: c.stroke, 'stroke-width': '1.2' }, g);

  return g;
}

// ── PRIMITIVA 6: SOLDADURA FILETE ───────────────────────────────
/**
 * Dibuja símbolo de soldadura en filete (triángulo en vértice)
 * @param {SVGElement} svg
 * @param {number} vx, vy  - vértice (punto de unión de las dos planchas)
 * @param {number} w       - tamaño del filete [px]
 * @param {'TL'|'TR'|'BL'|'BR'} corner - orientación del triángulo
 */
function drawSoldaduraFilete(svg, vx, vy, w, corner = 'TR') {
  const offsets = {
    TR: [[0, 0], [0, -w], [w, 0]],   // vértice arriba-derecha
    TL: [[0, 0], [0, -w], [-w, 0]],  // vértice arriba-izquierda
    BR: [[0, 0], [0,  w], [w, 0]],   // vértice abajo-derecha
    BL: [[0, 0], [0,  w], [-w, 0]],  // vértice abajo-izquierda
  };
  const off = offsets[corner];
  const points = off.map(([dx, dy]) => [vx + dx, vy + dy]);

  svgEl('polygon', {
    points: pts(...points),
    fill: FILL.WELD,
    stroke: '#BA7517', 'stroke-width': '0.5'
  }, svg);
}

// ── PRIMITIVA 7: LÍNEA DE CORTE (sección X-X) ───────────────────
/**
 * Dibuja la línea de corte con flechas estándar
 * @param {SVGElement} svg
 * @param {number} x1,y1  - inicio
 * @param {number} x2,y2  - fin
 * @param {string} label  - etiqueta (ej: 'A', 'B', '1')
 */
function drawLineaCorte(svg, x1, y1, x2, y2, label = 'A') {
  const g = svgEl('g', { class: 'linea-corte' }, svg);

  svgEl('line', { x1, y1, x2, y2,
    stroke: STROKE.CUTTING.stroke, 'stroke-width': STROKE.CUTTING.strokeWidth,
    'stroke-dasharray': '12,4,2,4' }, g);

  // Flecha inicio
  svgEl('text', { x: x1 - 14, y: y1 + 4,
    'font-family': 'monospace', 'font-size': '11', 'font-weight': 'bold',
    fill: '#1A1A1A', 'text-anchor': 'middle' }, g).textContent = label;

  // Flecha fin
  svgEl('text', { x: x2 + 14, y: y2 + 4,
    'font-family': 'monospace', 'font-size': '11', 'font-weight': 'bold',
    fill: '#1A1A1A', 'text-anchor': 'middle' }, g).textContent = label;

  return g;
}

// ── PRIMITIVA 8: COTA (dimensión) ───────────────────────────────
/**
 * Dibuja una cota horizontal o vertical con flechas y valor
 * @param {SVGElement} svg
 * @param {number} x1,y1  - punto 1
 * @param {number} x2,y2  - punto 2
 * @param {string} text   - texto de la cota (ej: '150 mm')
 * @param {number} offset - distancia de la cota al elemento [px]
 * @param {'h'|'v'} dir   - horizontal o vertical
 */
function drawCota(svg, x1, y1, x2, y2, text, offset = 20, dir = 'h') {
  const g = svgEl('g', { class: 'cota' }, svg);
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;

  if (dir === 'h') {
    const ly = Math.min(y1, y2) - offset;
    // Línea de cota
    svgEl('line', { x1, y1: ly, x2, y2: ly,
      stroke: STROKE.DIMENSION.stroke, 'stroke-width': STROKE.DIMENSION.strokeWidth,
      'marker-start': 'url(#arrow-dim)', 'marker-end': 'url(#arrow-dim)' }, g);
    // Líneas de extensión
    svgEl('line', { x1, y1, x2: x1, y2: ly + 3,
      stroke: STROKE.DIMENSION.stroke, 'stroke-width': '0.4' }, g);
    svgEl('line', { x1: x2, y1: y2, x2, y2: ly + 3,
      stroke: STROKE.DIMENSION.stroke, 'stroke-width': '0.4' }, g);
    // Texto
    svgEl('text', { x: mx, y: ly - 4,
      'font-family': 'monospace', 'font-size': '10', fill: '#333',
      'text-anchor': 'middle' }, g).textContent = text;
  } else {
    const lx = Math.min(x1, x2) - offset;
    svgEl('line', { x1: lx, y1, x2: lx, y2,
      stroke: STROKE.DIMENSION.stroke, 'stroke-width': STROKE.DIMENSION.strokeWidth,
      'marker-start': 'url(#arrow-dim)', 'marker-end': 'url(#arrow-dim)' }, g);
    svgEl('line', { x1, y1, x2: lx + 3, y2: y1,
      stroke: STROKE.DIMENSION.stroke, 'stroke-width': '0.4' }, g);
    svgEl('line', { x1: x2, y1: y2, x2: lx + 3, y2,
      stroke: STROKE.DIMENSION.stroke, 'stroke-width': '0.4' }, g);
    svgEl('text', {
      x: lx - 5, y: my,
      'font-family': 'monospace', 'font-size': '10', fill: '#333',
      'text-anchor': 'middle', transform: `rotate(-90, ${lx - 5}, ${my})`
    }, g).textContent = text;
  }

  return g;
}

// ── PRIMITIVA 9: HATCHING (rayado de sección) ────────────────────
/**
 * Aplica rayado estándar de sección (líneas a 45°) dentro de un rectángulo
 * Solo sobre el área del perfil (alas + alma), no sobre el vacío interior
 */
function drawHatching(svg, cx, cy, bf, d, tw, tf, spacing = 4) {
  // Clonar-path del perfil como clip
  const clipId = `clip-hatch-${Date.now()}`;
  const defs = svg.querySelector('defs') || svgEl('defs', {}, svg);

  const clip = svgEl('clipPath', { id: clipId }, defs);
  // Ala superior
  svgEl('rect', { x: cx - bf/2, y: cy - d/2, width: bf, height: tf }, clip);
  // Alma
  svgEl('rect', { x: cx - tw/2, y: cy - d/2 + tf, width: tw, height: d - 2*tf }, clip);
  // Ala inferior
  svgEl('rect', { x: cx - bf/2, y: cy + d/2 - tf, width: bf, height: tf }, clip);

  const g = svgEl('g', { 'clip-path': `url(#${clipId})`, opacity: '0.3' }, svg);

  // Líneas diagonales a 45°
  const size = Math.max(bf, d) * 2;
  for (let i = -size; i < size; i += spacing) {
    svgEl('line', {
      x1: cx + i,     y1: cy - d,
      x2: cx + i + d, y2: cy + d,
      stroke: FILL.HATCHING, 'stroke-width': '0.5'
    }, g);
  }
}

// ── PRIMITIVA 10: PERFIL W ISOMÉTRICO ───────────────────────────
/**
 * Dibuja un perfil W en proyección isométrica (3D simplificado)
 * @param {SVGElement} svg
 * @param {number} ox, oy  - origen (punto inferior-frontal del perfil)
 * @param {Object} p       - { d, bf, tf, tw } en px ya escalados
 * @param {number} L       - longitud visible del perfil [px]
 * @param {'x'|'y'|'z'} axis - eje a lo largo del cual se extiende el perfil
 */
function drawPerfilW_Iso(svg, ox, oy, p, L, axis = 'x') {
  const { d, bf, tf, tw } = p;
  const iso = ISO;
  const g = svgEl('g', { class: 'perfil-w-iso' }, svg);

  // Helper: proyectar punto 3D + offset de origen
  const P = (x, y, z) => {
    const p2 = iso.project(x, y, z);
    return [ox + p2.x, oy + p2.y];
  };

  if (axis === 'y') {
    // Perfil se extiende en dirección Y (viga horizontal hacia el fondo)
    // Cara frontal (alma visible)
    const almaFront = [
      P(tw/2,  0,  0),
      P(tw/2,  0,  d),
      P(tw/2,  L,  d),
      P(tw/2,  L,  0),
    ];
    svgEl('polygon', { points: pts(...almaFront),
      fill: FILL.STEEL_SURFACE, stroke: STROKE.VISIBLE.stroke,
      'stroke-width': STROKE.VISIBLE.strokeWidth }, g);

    // Ala superior (cara vista desde arriba)
    const alaSupTop = [
      P(-bf/2, 0, d),
      P( bf/2, 0, d),
      P( bf/2, L, d),
      P(-bf/2, L, d),
    ];
    svgEl('polygon', { points: pts(...alaSupTop),
      fill: FILL.STEEL_SHADOW, stroke: STROKE.VISIBLE.stroke,
      'stroke-width': STROKE.VISIBLE.strokeWidth }, g);

    // Ala superior cara frontal
    const alaSupFront = [
      P(-bf/2, 0, d - tf),
      P( bf/2, 0, d - tf),
      P( bf/2, 0, d),
      P(-bf/2, 0, d),
    ];
    svgEl('polygon', { points: pts(...alaSupFront),
      fill: FILL.STEEL_SURFACE, stroke: STROKE.VISIBLE.stroke,
      'stroke-width': STROKE.VISIBLE.strokeWidth }, g);

    // Ala inferior cara frontal
    const alaInfFront = [
      P(-bf/2, 0, 0),
      P( bf/2, 0, 0),
      P( bf/2, 0, tf),
      P(-bf/2, 0, tf),
    ];
    svgEl('polygon', { points: pts(...alaInfFront),
      fill: FILL.STEEL_SURFACE, stroke: STROKE.VISIBLE.stroke,
      'stroke-width': STROKE.VISIBLE.strokeWidth }, g);
  }

  return g;
}
```

---

## PARTE 5 — REGLAS DE REPRESENTACIÓN POR TIPO DE CONEXIÓN

### 5.1 Shear Tab — Viga al ALA de columna

```
VISTA ELEVACIÓN FRONTAL (columna de frente):
  - Columna aparece como H completa: ala-izq | alma | ala-der
  - Plancha soldada al ALMA (cara vertical central)
  - 3 pernos en sección (círculos) alineados verticalmente
  - Viga llega de costado: alma visible, alas como rectángulos
  - Alas de la viga: LÍNEA OCULTA (dasharray) si están detrás

VISTA ISOMÉTRICA:
  - Columna de frente, alas visibles a ambos lados
  - Plancha proyecta hacia la viga en dirección Y
  - Viga llega perpendicular al alma de la columna
  - Gap visible entre alas de viga y columna
```

### 5.2 Shear Tab — Viga al ALMA de columna

```
VISTA ELEVACIÓN FRONTAL (columna de perfil):
  - Columna aparece como rectángulo vertical (solo el alma visible)
  - A los lados del alma: dos rectángulos horizontales (alas, vistas de canto)
  - Plancha soldada a la cara del alma
  - 3 pernos en sección
  - Viga llega de frente al alma

VISTA ISOMÉTRICA:
  - Columna de perfil, alma hacia la viga
  - Las dos alas de la columna son las "aletas" laterales
  - Gap visible entre alas de viga y alma de columna
```

### 5.3 Pernos — Grupos y espaciado

```javascript
// Función para dibujar un grupo de N pernos en una línea vertical
function drawGrupoPernos(svg, x, y_top, n, p_spacing, db) {
  for (let i = 0; i < n; i++) {
    drawPerno_Seccion(svg, x, y_top + i * p_spacing, db);
  }
}

// Distancias mínimas (AISC J3.4):
// e1 = distancia borde superior → primer perno ≥ 1.5 db (recomendado 2 db)
// p  = separación centro a centro ≥ 2.67 db (recomendado 3 db)
// e2 = distancia borde lateral ≥ 1.5 db
```

---

## PARTE 6 — EJEMPLOS DE REFERENCIA SVG COMPLETOS

### Ejemplo A — Shear Tab vista elevación (inline SVG)

```html
<!-- ESCALC Conexiones — Shear Tab Elevación Frontal (columna de frente) -->
<!-- Columna W250x89: d=260mm, bf=256mm, tf=17.3mm, tw=10.7mm -->
<!-- Escala: 1mm = 0.8px -->
<svg viewBox="0 0 400 500" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5"
      markerWidth="4" markerHeight="4" orient="auto">
      <path d="M1 1L9 5L1 9" fill="none" stroke="#555" stroke-width="1.5"/>
    </marker>
  </defs>

  <!-- Fondo -->
  <rect width="400" height="500" fill="#FAFAF8"/>

  <!-- COLUMNA W250x89 (escala 0.8) -->
  <!-- bf=256 → 204.8px; d=260 → 208px; tf=17.3 → 13.8px; tw=10.7 → 8.6px -->
  <!-- Centrada en x=200, y=250 -->

  <!-- Ala izquierda -->
  <rect x="98" y="146" width="13.8" height="208"
    fill="#D0CEC8" stroke="#1A1A1A" stroke-width="1.5"/>
  <!-- Alma -->
  <rect x="111.8" y="146" width="204.8" height="208"
    fill="#E8E6E0" stroke="#1A1A1A" stroke-width="1.5"/>
  <!-- Ala derecha -->
  <rect x="316.8" y="146" width="13.8" height="208"
    fill="#D0CEC8" stroke="#1A1A1A" stroke-width="1.5"/>

  <!-- PLANCHA SHEAR TAB (soldada al alma, centro de la columna) -->
  <!-- 150mm alto x 8mm ancho → 120px x 6.4px, centrada verticalmente -->
  <!-- Posición: pegada al alma derecha (x=316.8) -->
  <rect x="316.8" y="200" width="30" height="100"
    fill="#85B7EB" stroke="#185FA5" stroke-width="1.2"/>

  <!-- Soldadura filete (triángulo en vértice plancha-alma) -->
  <polygon points="316.8,200 316.8,210 326.8,200" fill="#EF9F27"/>
  <polygon points="316.8,300 316.8,290 326.8,300" fill="#EF9F27"/>

  <!-- PERNOS EN SECCIÓN (3 pernos, db=22mm → 17.6px) -->
  <!-- Separación p=76mm → 60.8px; e1=38mm → 30.4px desde borde plancha -->
  <circle cx="331.8" cy="230.4" r="8.8" fill="#222" stroke="#1A1A1A" stroke-width="0.8"/>
  <circle cx="331.8" cy="230.4" r="12"  fill="none" stroke="#555" stroke-width="0.5" stroke-dasharray="3,2"/>
  <circle cx="331.8" cy="291.2" r="8.8" fill="#222" stroke="#1A1A1A" stroke-width="0.8"/>
  <circle cx="331.8" cy="291.2" r="12"  fill="none" stroke="#555" stroke-width="0.5" stroke-dasharray="3,2"/>
  <circle cx="331.8" cy="352.0" r="8.8" fill="#222" stroke="#1A1A1A" stroke-width="0.8"/>
  <circle cx="331.8" cy="352.0" r="12"  fill="none" stroke="#555" stroke-width="0.5" stroke-dasharray="3,2"/>

  <!-- Ejes de pernos (líneas de centro) -->
  <line x1="315" y1="230.4" x2="360" y2="230.4" stroke="#888" stroke-width="0.4" stroke-dasharray="5,2,1,2"/>
  <line x1="315" y1="291.2" x2="360" y2="291.2" stroke="#888" stroke-width="0.4" stroke-dasharray="5,2,1,2"/>
  <line x1="315" y1="352.0" x2="360" y2="352.0" stroke="#888" stroke-width="0.4" stroke-dasharray="5,2,1,2"/>

  <!-- Labels -->
  <text x="200" y="90" text-anchor="middle" font-family="monospace"
    font-size="11" fill="#333">W250x89 — Vista elevación (columna de frente)</text>
  <text x="358" y="260" font-family="monospace" font-size="9" fill="#185FA5">Shear tab</text>
  <text x="358" y="295" font-family="monospace" font-size="9" fill="#222">⌀ perno</text>

  <!-- Cota bf -->
  <line x1="98" y1="125" x2="330.6" y2="125" stroke="#555" stroke-width="0.5"
    marker-start="url(#arr)" marker-end="url(#arr)"/>
  <text x="214" y="120" text-anchor="middle" font-family="monospace" font-size="9" fill="#555">bf = 256 mm</text>

  <!-- Cota d -->
  <line x1="76" y1="146" x2="76" y2="354" stroke="#555" stroke-width="0.5"
    marker-start="url(#arr)" marker-end="url(#arr)"/>
  <text x="70" y="255" text-anchor="middle" font-family="monospace" font-size="9"
    fill="#555" transform="rotate(-90,70,255)">d = 260 mm</text>
</svg>
```

---

## PARTE 7 — INSTRUCCIONES PARA EL AGENTE DE DESARROLLO

Cuando el agente de código (Cursor, GitHub Copilot, Claude en VS Code) trabaje
en el motor de dibujo de ESCALC, debe seguir estas reglas:

```
REGLA 1 — NUNCA inventar geometría desde cero
  Siempre usar las primitivas de drawing/primitives.js
  Si una primitiva no existe → pedirla, no improvisar

REGLA 2 — Toda vista de sección lleva hatching
  Cualquier sección transversal de un perfil → drawHatching() obligatorio
  Sin hatching = vista incorrecta según norma

REGLA 3 — Los elementos ocultos van con línea de trazo
  Si un elemento está detrás de otro en esa vista:
  → stroke-dasharray="5,3" stroke-width="0.7"
  Nunca usar línea sólida para un elemento oculto

REGLA 4 — Pernos siempre en grupo
  Nunca dibujar pernos sueltos
  Siempre usar drawGrupoPernos() con los parámetros de distancia AISC

REGLA 5 — La soldadura siempre tiene símbolo visible
  Toda soldadura → drawSoldaduraFilete() o línea gruesa naranja
  Sin símbolo de soldadura = conexión ambigua

REGLA 6 — Las vistas compuestas siguen el sistema de 5 vistas
  Siempre especificar qué vista es cada panel (VISTA_A a VISTA_E)
  Indicar la relación de proyección entre vistas

REGLA 7 — El gap entre alas de viga y columna es obligatorio en shear tab
  En cualquier representación de shear tab:
  Las alas de la viga NO tocan la columna
  El gap mínimo en pantalla = 4px (nunca menos)

REGLA 8 — Escala siempre declarada
  Todo dibujo debe incluir una barra de escala o declarar la escala usada
  Formato: "Escala 1:10" o barra gráfica de 50mm

REGLA 9 — Terminología en el código
  Variables: usar nombres en inglés (standard de la industria)
  Comentarios: en español (contexto ESCALC Latinoamérica)
  Textos visibles en el SVG: en español

REGLA 10 — Nunca mezclar estilos
  Un mismo SVG → una sola paleta (FILL + STROKE definidos arriba)
  No usar colores inline fuera de la paleta definida
```

---

## PARTE 8 — PLANTILLA DE PROMPT PARA PEDIR DIBUJOS AL AGENTE

Cuando quieras pedirle al agente que dibuje una conexión específica, usar esta
plantilla para maximizar la precisión:

```
Usa las primitivas de ESCALC drawing/primitives.js.

Dibuja: [nombre de la conexión]
Vista: [VISTA_A/B/C/D/E]
Perfil columna: [W___x___] → bf=___mm, d=___mm, tf=___mm, tw=___mm
Perfil viga: [W___x___] → bf=___mm, d=___mm, tf=___mm, tw=___mm
Plancha: [alto=___mm, ancho=___mm, espesor=___mm]
Pernos: [n=___, db=___mm, e1=___mm, p=___mm, e2=___mm]
Soldadura: [filete w=___mm, electrodo E___]
Escala: 1:___
Viewport SVG: [___x___px]

Reglas obligatorias:
- Hatching en secciones transversales
- Elementos ocultos con stroke-dasharray="5,3"
- Pernos con drawPerno_Seccion() / drawPerno_Elevacion()
- Gap visible entre alas de viga y columna (mínimo 4px)
- Soldadura con triángulo naranja en el vértice
- Ejes de simetría con stroke-dasharray="8,3,2,3"
```

---

*ESCALC — Engineering Software CALC*
*Módulo: Conexiones Estructurales en Acero*
*Motor de dibujo técnico v1.0*
*Documento de contexto para agente de desarrollo*
