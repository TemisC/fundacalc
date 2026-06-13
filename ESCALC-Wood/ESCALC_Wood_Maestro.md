# ESCALC Wood — Documento Maestro de Desarrollo
> Módulo: **Cálculo Estructural de Techos en Madera — Roof Rafters**  
> Suite: **ESCALC** (Engineering Software CALC)  
> Stack: **Python 3.11+ · Flask · NumPy · Matplotlib · ReportLab · Jinja2**  
> IDE: Visual Studio Code  
> Norma: NDS 2024 (National Design Specification for Wood Construction — AWC/ANSI)  
> Versión del documento: 1.0

---

## Índice

1. [Visión y alcance del módulo](#1-visión-y-alcance-del-módulo)
2. [Decisión de stack — Por qué Python + Flask](#2-decisión-de-stack--por-qué-python--flask)
3. [Estructura de carpetas](#3-estructura-de-carpetas)
4. [Setup del entorno en VS Code](#4-setup-del-entorno-en-vs-code)
5. [Motor de cálculo NDS — `rafter_engine.py`](#5-motor-de-cálculo-nds--rafter_enginepy)
6. [Tablas de materiales NDS — `nds_data.py`](#6-tablas-de-materiales-nds--nds_datapy)
7. [Backend Flask — `app.py`](#7-backend-flask--apppy)
8. [Rutas API — `routes/wood.py`](#8-rutas-api--routeswoodpy)
9. [Templates HTML — `templates/`](#9-templates-html--templates)
10. [Estilos CSS — `static/css/escalc.css`](#10-estilos-css--staticcssescalccss)
11. [Gráfico SVG del rafter — `utils/svg_rafter.py`](#11-gráfico-svg-del-rafter--utilssvg_rafterpy)
12. [Exportación PDF — `utils/pdf_report.py`](#12-exportación-pdf--utilspdf_reportpy)
13. [Integración con ESCALC principal](#13-integración-con-escalc-principal)
14. [Valores de prueba y validación](#14-valores-de-prueba-y-validación)
15. [Roadmap — módulos futuros de Wood](#15-roadmap--módulos-futuros-de-wood)

---

## 1. Visión y alcance del módulo

ESCALC Wood es el **módulo de madera estructural** de la suite ESCALC. Esta primera entrega cubre el diseño de **rafters de techo** (vigas de cubierta inclinadas) bajo la norma NDS 2024.

### Qué calcula

- Determinación de cargas (DL, LL, SL, WL) y combinaciones de diseño
- Cálculo de momentos y cortantes máximos (viga simplemente apoyada con voladizo opcional)
- Verificación de **flexión** (fb ≤ F'b) según NDS Ch. 3
- Verificación de **corte horizontal** (fv ≤ F'v) según NDS 3.4
- Verificación de **deflexión** (Δ_LL ≤ L/360) según NDS App. F
- Aplicación de todos los **factores de ajuste NDS**: CD, CM, Ct, CF, CL, Cr, Ci
- Generación de **diagrama SVG** del rafter con cargas y cotas
- Exportación de **memoria de cálculo en PDF**

### Qué NO cubre (versiones futuras)

- Vigas de caballete (ridge beam)
- Uniones y conectores metálicos (ESCALC Steel)
- Diseño de correas (purlins)
- Análisis sísmico de la cubierta

---

## 2. Decisión de stack — Por qué Python + Flask

| Criterio | Flask (Python) | Django | FastAPI |
|---|---|---|---|
| Curva de aprendizaje | Baja — mínimo boilerplate | Alta — mucho config inicial | Media |
| Adecuado para app de cálculo | Sí — rutas simples, sin ORM complejo | Excesivo para este uso | Bueno, pero async innecesario |
| Integración con NumPy/SciPy | Nativa Python | Nativa Python | Nativa Python |
| Templates HTML | Jinja2 incluido | Incluido | Requiere extra |
| Generación PDF | ReportLab directo | ReportLab directo | ReportLab directo |
| Modo de ejecución en VS Code | `python app.py` | `python manage.py runserver` | `uvicorn main:app` |

**Conclusión**: Flask es la opción más directa para una app de cálculo con interfaz web. Se levanta con un solo comando, no requiere configuración de base de datos, y el cálculo Python queda centralizado en el backend.

### Flujo de datos

```
Usuario (browser)
    │
    │  POST /calcular  { inputs JSON }
    ▼
Flask app.py
    │
    ├── rafter_engine.py   ← Todo el cálculo NDS (Python puro + NumPy)
    │       │
    │       └── nds_data.py  ← Tablas de especies, grados, dimensiones
    │
    ├── utils/svg_rafter.py  ← Genera diagrama SVG como string
    │
    ├── utils/pdf_report.py  ← Genera PDF con ReportLab
    │
    └── Jinja2 template      ← Renderiza resultado al browser
```

---

## 3. Estructura de carpetas

Crear esta estructura exacta en VS Code:

```
ESCALC/
│
├── wood/                          ← Módulo Wood (este documento)
│   ├── app.py                     ← Servidor Flask principal
│   ├── rafter_engine.py           ← Motor de cálculo NDS
│   ├── nds_data.py                ← Tablas NDS: especies, grados, secciones
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── wood.py                ← Endpoints /calcular, /pdf, /svg
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── svg_rafter.py          ← Generador de diagrama SVG
│   │   └── pdf_report.py          ← Generador de memoria PDF
│   │
│   ├── templates/
│   │   ├── base.html              ← Layout ESCALC (header, nav, footer)
│   │   ├── wood_home.html         ← Pantalla inicio módulo Wood
│   │   └── rafter.html            ← Formulario + resultados rafter
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── escalc.css         ← Estilos ESCALC (dark/light)
│   │   └── img/
│   │       └── escalc_logo.svg
│   │
│   ├── requirements.txt
│   └── .vscode/
│       ├── settings.json
│       └── launch.json            ← Run & Debug config para Flask
│
├── foundation/                    ← Módulo Foundation (existente)
├── steel/                         ← Módulo Steel Connections (existente)
└── elements/                      ← Módulo Elements (existente)
```

---

## 4. Setup del entorno en VS Code

### 4.1 Extensiones requeridas

Instalar en VS Code (Ctrl+Shift+X):

| Extensión | ID | Para qué |
|---|---|---|
| Python | `ms-python.python` | Soporte Python principal |
| Pylance | `ms-python.vscode-pylance` | Intellisense y type checking |
| Flask Snippets | `cstrap.flask-snippets` | Snippets de rutas y templates |
| Jinja | `wholroyd.jinja` | Syntax highlighting en .html con Jinja2 |
| Better Comments | `aaron-bond.better-comments` | Comentarios de cálculo coloreados |
| GitLens | `eamodio.gitlens` | Control de versiones |

### 4.2 Archivo `.vscode/settings.json`

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python",
  "python.terminal.activateEnvironment": true,
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "files.associations": {
    "*.html": "jinja-html"
  },
  "emmet.includeLanguages": {
    "jinja-html": "html"
  },
  "[python]": {
    "editor.tabSize": 4,
    "editor.rulers": [88]
  }
}
```

### 4.3 Archivo `.vscode/launch.json`

Permite hacer F5 en VS Code para levantar Flask en modo debug:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "ESCALC Wood — Flask Debug",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "app.py",
        "FLASK_ENV": "development",
        "FLASK_DEBUG": "1"
      },
      "args": ["run", "--host=0.0.0.0", "--port=5050"],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

### 4.4 Instalación paso a paso

```bash
# 1. Abrir terminal en VS Code (Ctrl + `)
# 2. Posicionarse en la carpeta del módulo
cd ESCALC/wood

# 3. Crear entorno virtual
python -m venv venv

# 4. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Levantar la app (o usar F5 con launch.json)
python app.py
```

La app queda disponible en: `http://localhost:5050`

### 4.5 `requirements.txt`

```
flask==3.0.3
numpy==1.26.4
matplotlib==3.8.4
reportlab==4.2.2
jinja2==3.1.4
Werkzeug==3.0.3
```

---

## 5. Motor de cálculo NDS — `rafter_engine.py`

Este es el corazón del módulo. Contiene toda la lógica estructural NDS, independiente de Flask. Se puede importar y testear en cualquier script Python.

```python
# rafter_engine.py
# ESCALC Wood — Motor de Cálculo NDS 2024
# Módulo: Roof Rafter Design
# Norma: NDS 2024 (AWC/ANSI) + ASCE 7-22 (combinaciones de carga)
# Engineering Software CALC — v1.0

import math
from dataclasses import dataclass, field
from typing import Optional
from nds_data import NDS_SPECIES, ACTUAL_SIZES, DURATION_FACTORS


@dataclass
class RafterInputs:
    """Parámetros de entrada para el diseño del rafter."""
    # Geometría
    span_ft: float          # Luz horizontal (ft) — de apoyo a apoyo
    slope_in_ft: float      # Pendiente (in/ft) — ej: 6 = 6:12
    spacing_in: float       # Separación entre rafters (in)
    cantilever_ft: float    # Voladizo (ft), 0 si no hay

    # Sección de madera (nominal)
    species: str            # Clave de especie, ej: "spruce-pine-fir"
    grade: str              # Grado visual: "no2", "no1", "select"
    width_nom: int          # Ancho nominal (in): 2, 3, 4
    depth_nom: int          # Peralte nominal (in): 6, 8, 10, 12

    # Cargas (psf sobre plano horizontal)
    dl_roofing: float       # Carga muerta cubierta (teja, OSB, etc.)
    dl_self: float          # Peso propio del rafter estimado
    ll: float               # Sobrecarga de uso / mantenimiento
    wl: float               # Carga de viento (psf)
    sl: float               # Carga de nieve (psf), 0 si no aplica

    # Factores de ajuste NDS
    cm: float = 1.0         # Factor de contenido de humedad (seco=1.0, húmedo=0.85)
    ct: float = 1.0         # Factor de temperatura (≤100°F=1.0)

    # Límite de deflexión
    deflection_limit: int = 360   # L/360 por defecto


@dataclass
class AdjustmentFactors:
    """Factores de ajuste NDS aplicados al cálculo."""
    CD: float   # Duración de carga (NDS 2.3.2)
    CM: float   # Contenido de humedad (NDS 4.3.3)
    Ct: float   # Temperatura (NDS 2.3.3)
    CF_b: float # Factor de forma para flexión (NDS Supp. 4A)
    CL: float   # Estabilidad lateral (NDS 3.3.3) — simplificado = 1.0 para rafters con forro
    Cr: float   # Factor de miembro repetitivo (NDS 4.3.9)
    Ci: float   # Factor de incisión (NDS 4.3.8) — 1.0 para madera no incisa


@dataclass
class RafterResults:
    """Resultados completos del cálculo NDS."""
    # Geometría calculada
    slope_angle_deg: float
    slope_factor: float         # sech(θ) = longitud inclinada / luz horizontal
    rafter_length_ft: float     # Longitud real del rafter (inclinada)
    tributary_width_ft: float   # Ancho tributario

    # Sección real (inches)
    b_in: float                 # Ancho real
    d_in: float                 # Peralte real
    area_in2: float
    S_in3: float                # Módulo de sección
    I_in4: float                # Momento de inercia

    # Cargas de diseño (lb/ft sobre longitud horizontal)
    w_DL: float                 # Carga muerta por unidad de longitud
    w_LL: float
    w_WL: float
    w_SL: float
    w_total: float              # Carga de diseño total (combinación gobernante)
    load_combo_governing: str   # Combinación que governa

    # Solicitaciones
    M_max_ftlb: float           # Momento máximo (ft·lb)
    V_max_lb: float             # Cortante máximo (lb)

    # Propiedades de referencia NDS (psi)
    Fb_ref: float               # Resistencia de flexión de referencia
    Fv_ref: float               # Resistencia de corte de referencia
    E_ref: float                # Módulo de elasticidad de referencia

    # Factores de ajuste
    factors: AdjustmentFactors

    # Resistencias ajustadas (psi)
    Fb_prime: float             # F'b = Fb × CD × CM × Ct × CF × CL × Cr
    Fv_prime: float             # F'v = Fv × CD × CM × Ct
    E_prime: float              # E'  = E  × CM × Ct

    # Tensiones actuantes (psi)
    fb_actual: float            # Tensión de flexión actuante
    fv_actual: float            # Tensión de corte actuante

    # Deflexión (in)
    delta_LL_in: float          # Deflexión por carga viva (in)
    delta_limit_in: float       # Límite L/360 (in)
    delta_ratio: float          # Relación Δ_actual / Δ_límite

    # Relaciones de demanda/capacidad
    ratio_bending: float        # fb / F'b
    ratio_shear: float          # fv / F'v
    ratio_deflection: float     # Δ / Δ_limit

    # Verificación global
    bending_ok: bool
    shear_ok: bool
    deflection_ok: bool
    all_ok: bool

    # Mensajes
    governing_check: str        # Qué verificación es la más crítica
    warnings: list = field(default_factory=list)


class RafterCalculator:
    """
    Motor de cálculo de rafters según NDS 2024.
    
    Uso:
        calc = RafterCalculator(inputs)
        results = calc.calculate()
    """

    def __init__(self, inputs: RafterInputs):
        self.inp = inputs
        self._validate_inputs()

    def _validate_inputs(self):
        """Validaciones básicas de entrada."""
        i = self.inp
        assert 4 <= i.span_ft <= 40, "Luz debe estar entre 4 y 40 ft"
        assert 1 <= i.slope_in_ft <= 24, "Pendiente entre 1:12 y 24:12"
        assert i.spacing_in in [12, 16, 19.2, 24], "Separación típica: 12, 16, 19.2 ó 24 in"
        assert i.species in NDS_SPECIES, f"Especie '{i.species}' no encontrada en tablas NDS"
        assert i.grade in NDS_SPECIES[i.species], f"Grado '{i.grade}' no disponible"
        assert i.width_nom in [2, 3, 4], "Ancho nominal: 2, 3 ó 4 in"
        assert i.depth_nom in [6, 8, 10, 12], "Peralte nominal: 6, 8, 10 ó 12 in"
        assert 0 <= i.cantilever_ft <= 4, "Voladizo máximo 4 ft"
        assert i.dl_roofing >= 0 and i.ll >= 0

    def _geometry(self):
        """Calcula parámetros geométricos del rafter."""
        i = self.inp
        slope_ratio = i.slope_in_ft / 12.0
        angle_rad = math.atan(slope_ratio)
        slope_factor = math.sqrt(1 + slope_ratio**2)   # longitud inclinada / luz horiz.
        rafter_length = i.span_ft * slope_factor + i.cantilever_ft * slope_factor
        tributary_width = i.spacing_in / 12.0
        return angle_rad, slope_factor, rafter_length, tributary_width

    def _section_properties(self):
        """Dimensiones reales y propiedades de sección."""
        i = self.inp
        key = str(i.width_nom)
        b, d = ACTUAL_SIZES[key][str(i.depth_nom)]
        area = b * d
        S = (b * d**2) / 6.0
        I = (b * d**3) / 12.0
        return b, d, area, S, I

    def _load_combinations(self, tributary_ft):
        """
        Combinaciones de carga ASCE 7-22 / NDS.
        Todas las cargas en lb/ft sobre longitud horizontal.
        Retorna (w_total, combo_name).
        """
        i = self.inp
        w_DL = (i.dl_roofing + i.dl_self) * tributary_ft
        w_LL = i.ll * tributary_ft
        w_WL = i.wl * tributary_ft
        w_SL = i.sl * tributary_ft

        # Combinaciones básicas (ASD)
        combos = {
            "D + L":                   w_DL + w_LL,
            "D + S":                   w_DL + w_SL,
            "D + W":                   w_DL + w_WL,
            "D + 0.75W + 0.75L + 0.75S": w_DL + 0.75*w_WL + 0.75*w_LL + 0.75*w_SL,
        }
        governing_combo = max(combos, key=combos.get)
        w_total = combos[governing_combo]
        return w_DL, w_LL, w_WL, w_SL, w_total, governing_combo

    def _duration_factor(self) -> tuple[float, str]:
        """
        Factor de duración de carga CD (NDS Tabla 2.3.2).
        Governa la carga de menor duración que controla el diseño.
        """
        i = self.inp
        # Jerarquía de CD (mayor CD = menos conservador)
        if i.wl > 0 and i.wl >= i.ll and i.wl >= i.sl:
            return 1.6, "Viento (CD = 1.6)"
        elif i.sl > 0 and i.sl >= i.ll:
            return 1.15, "Nieve (CD = 1.15)"
        elif i.ll > 0:
            return 1.0, "Ocupación/Uso (CD = 1.0)"
        else:
            return 0.9, "Solo carga muerta (CD = 0.9)"

    def _form_factor_bending(self, d_in: float) -> float:
        """
        Factor de forma CF para flexión (NDS Sup. Table 4A).
        Aplica a sección rectangular de madera aserrada, ancho ≤ 4 in.
        """
        if d_in <= 8:
            return 1.2
        elif d_in <= 10:
            return 1.1
        elif d_in <= 12:
            return 1.0
        else:
            return 1.0  # NDS Tabla 4A footnote

    def _repetitive_factor(self) -> float:
        """
        Factor miembro repetitivo Cr (NDS 4.3.9).
        Aplica si: 3+ miembros paralelos, espaciados ≤24in, con piso/forro compartido.
        """
        if self.inp.spacing_in <= 24:
            return 1.15   # Rafters típicos con clavado de OSB o forro
        return 1.0

    def calculate(self) -> RafterResults:
        """Ejecuta el cálculo completo NDS y retorna RafterResults."""
        i = self.inp

        # 1. Geometría
        angle_rad, slope_factor, rafter_length, tributary_ft = self._geometry()

        # 2. Propiedades de sección
        b, d, area, S, I = self._section_properties()

        # 3. Propiedades de referencia NDS (psi)
        nds = NDS_SPECIES[i.species][i.grade]
        Fb_ref = nds["Fb"]
        Fv_ref = nds["Fv"]
        E_ref  = nds["E"]

        # 4. Cargas y combinaciones
        w_DL, w_LL, w_WL, w_SL, w_total, combo_name = self._load_combinations(tributary_ft)

        # 5. Factores de ajuste
        CD, cd_reason = self._duration_factor()
        CF_b = self._form_factor_bending(d)
        Cr   = self._repetitive_factor()
        CM   = i.cm
        Ct   = i.ct
        CL   = 1.0   # Simplificado: rafter con forro OSB provee soporte lateral continuo
        Ci   = 1.0   # Madera no incisa

        factors = AdjustmentFactors(
            CD=CD, CM=CM, Ct=Ct, CF_b=CF_b, CL=CL, Cr=Cr, Ci=Ci
        )

        # 6. Resistencias ajustadas
        Fb_prime = Fb_ref * CD * CM * Ct * CF_b * CL * Cr * Ci
        Fv_prime = Fv_ref * CD * CM * Ct
        E_prime  = E_ref  * CM * Ct

        # 7. Solicitaciones (viga simplemente apoyada con voladizo opcional)
        L = i.span_ft  # luz horizontal en ft
        # Momento máximo en vano: w*L²/8
        M_max_ftlb = (w_total * L**2) / 8.0
        # Cortante máximo en apoyo: w*L/2
        V_max_lb   = (w_total * L) / 2.0

        # 8. Tensiones actuantes (psi)
        fb_actual = (M_max_ftlb * 12.0) / S          # convertir ft·lb → in·lb
        fv_actual = (1.5 * V_max_lb) / (b * d)       # NDS 3.4.2 parabólica

        # 9. Deflexión por carga viva (in) — viga simplemente apoyada
        w_LL_inlb = (i.ll * tributary_ft) / 12.0     # lb/in
        L_in = L * 12.0                               # ft → in
        delta_LL = (5 * w_LL_inlb * L_in**4) / (384 * E_prime * I)
        delta_limit = L_in / i.deflection_limit

        # 10. Relaciones de demanda/capacidad
        ratio_b = fb_actual / Fb_prime
        ratio_v = fv_actual / Fv_prime
        ratio_d = delta_LL / delta_limit if delta_limit > 0 else 999

        bending_ok    = ratio_b <= 1.0
        shear_ok      = ratio_v <= 1.0
        deflection_ok = ratio_d <= 1.0
        all_ok = bending_ok and shear_ok and deflection_ok

        # 11. Verificación gobernante
        ratios = {"Flexión": ratio_b, "Corte": ratio_v, "Deflexión": ratio_d}
        governing_check = max(ratios, key=ratios.get)

        # 12. Advertencias
        warnings = []
        if i.slope_in_ft < 3:
            warnings.append("Pendiente < 3:12 — verificar capacidad de drenaje y estanqueidad.")
        if ratio_b > 0.9:
            warnings.append(f"Flexión al {ratio_b*100:.0f}% de capacidad — considerar aumentar peralte.")
        if ratio_d > 0.9:
            warnings.append("Deflexión próxima al límite — considerar criterio L/240 para cargas totales.")
        if i.cantilever_ft > 0:
            warnings.append("Con voladizo: verificar momento negativo y apoyo en extremo libre.")

        return RafterResults(
            slope_angle_deg   = math.degrees(angle_rad),
            slope_factor      = slope_factor,
            rafter_length_ft  = rafter_length,
            tributary_width_ft= tributary_ft,
            b_in=b, d_in=d, area_in2=area, S_in3=S, I_in4=I,
            w_DL=w_DL, w_LL=w_LL, w_WL=w_WL, w_SL=w_SL,
            w_total=w_total,
            load_combo_governing=combo_name,
            M_max_ftlb=M_max_ftlb,
            V_max_lb=V_max_lb,
            Fb_ref=Fb_ref, Fv_ref=Fv_ref, E_ref=E_ref,
            factors=factors,
            Fb_prime=Fb_prime, Fv_prime=Fv_prime, E_prime=E_prime,
            fb_actual=fb_actual, fv_actual=fv_actual,
            delta_LL_in=delta_LL,
            delta_limit_in=delta_limit,
            delta_ratio=ratio_d,
            ratio_bending=ratio_b,
            ratio_shear=ratio_v,
            ratio_deflection=ratio_d,
            bending_ok=bending_ok,
            shear_ok=shear_ok,
            deflection_ok=deflection_ok,
            all_ok=all_ok,
            governing_check=governing_check,
            warnings=warnings,
        )
```

---

## 6. Tablas de materiales NDS — `nds_data.py`

```python
# nds_data.py
# Tablas NDS 2024 — Supplement Table 4A (Visually Graded Dimension Lumber)
# Propiedades de referencia en psi

NDS_SPECIES = {
    "spruce-pine-fir": {
        "no2":    {"Fb": 875,  "Fv": 135, "E": 1_400_000, "Emin": 510_000},
        "no1":    {"Fb": 1050, "Fv": 135, "E": 1_500_000, "Emin": 550_000},
        "select": {"Fb": 1250, "Fv": 135, "E": 1_500_000, "Emin": 550_000},
    },
    "douglas-fir-larch": {
        "no2":    {"Fb": 900,  "Fv": 180, "E": 1_600_000, "Emin": 580_000},
        "no1":    {"Fb": 1100, "Fv": 180, "E": 1_700_000, "Emin": 620_000},
        "select": {"Fb": 1500, "Fv": 180, "E": 1_900_000, "Emin": 690_000},
    },
    "hem-fir": {
        "no2":    {"Fb": 850,  "Fv": 150, "E": 1_300_000, "Emin": 470_000},
        "no1":    {"Fb": 975,  "Fv": 150, "E": 1_400_000, "Emin": 510_000},
        "select": {"Fb": 1400, "Fv": 150, "E": 1_600_000, "Emin": 580_000},
    },
    "southern-pine": {
        "no2":    {"Fb": 1100, "Fv": 175, "E": 1_600_000, "Emin": 580_000},
        "no1":    {"Fb": 1350, "Fv": 175, "E": 1_700_000, "Emin": 620_000},
        "select": {"Fb": 1750, "Fv": 175, "E": 1_800_000, "Emin": 660_000},
    },
}

# Dimensiones reales (in) según tabla WWPA/SPIB
# Clave: {ancho_nominal: {peralte_nominal: [b_real, d_real]}}
ACTUAL_SIZES = {
    "2": {
        "6":  [1.5,  5.5],
        "8":  [1.5,  7.25],
        "10": [1.5,  9.25],
        "12": [1.5,  11.25],
    },
    "3": {
        "6":  [2.5,  5.5],
        "8":  [2.5,  7.25],
        "10": [2.5,  9.25],
        "12": [2.5,  11.25],
    },
    "4": {
        "6":  [3.5,  5.5],
        "8":  [3.5,  7.25],
        "10": [3.5,  9.25],
        "12": [3.5,  11.25],
    },
}

# Factores de duración de carga CD (NDS Tabla 2.3.2)
DURATION_FACTORS = {
    "dead":        0.9,
    "occupancy":   1.0,
    "snow":        1.15,
    "construction":1.25,
    "wind_seismic":1.6,
    "impact":      2.0,
}

# Factor de contenido de humedad CM (NDS Tabla 4.3.3 — dimensión lumber)
MOISTURE_FACTORS = {
    "dry":   {"Fb": 1.0, "Fv": 1.0, "E": 1.0},
    "wet":   {"Fb": 0.85, "Fv": 0.97, "E": 0.9},
}

# Etiquetas legibles para la UI
SPECIES_LABELS = {
    "spruce-pine-fir":   "Spruce-Pine-Fir (SPF)",
    "douglas-fir-larch": "Douglas Fir-Larch (DF-L)",
    "hem-fir":           "Hem-Fir",
    "southern-pine":     "Southern Pine (SP)",
}

GRADE_LABELS = {
    "no2":    "No. 2",
    "no1":    "No. 1",
    "select": "Select Structural",
}
```

---

## 7. Backend Flask — `app.py`

```python
# app.py
# ESCALC Wood — Servidor Flask
# Levantar con: python app.py  (o F5 con launch.json)

from flask import Flask
from routes.wood import wood_bp

app = Flask(__name__)
app.secret_key = "escalc-wood-dev-key"

# Registrar blueprint del módulo Wood
app.register_blueprint(wood_bp, url_prefix="/wood")

# Redirigir raíz a módulo Wood
@app.route("/")
def index():
    from flask import redirect
    return redirect("/wood")

if __name__ == "__main__":
    app.run(debug=True, port=5050, host="0.0.0.0")
```

---

## 8. Rutas API — `routes/wood.py`

```python
# routes/wood.py
# Blueprint Flask para el módulo Wood

from flask import Blueprint, render_template, request, jsonify, send_file
from rafter_engine import RafterCalculator, RafterInputs
from nds_data import NDS_SPECIES, SPECIES_LABELS, GRADE_LABELS, ACTUAL_SIZES
from utils.svg_rafter import build_rafter_svg
from utils.pdf_report import generate_rafter_pdf
import io

wood_bp = Blueprint("wood", __name__, template_folder="../templates")


@wood_bp.route("/")
def wood_home():
    """Pantalla de inicio del módulo Wood."""
    return render_template("wood_home.html")


@wood_bp.route("/rafter")
def rafter_form():
    """Formulario en blanco para diseño de rafter."""
    context = {
        "species_options": SPECIES_LABELS,
        "grade_options": GRADE_LABELS,
        "result": None,
        "svg": None,
        "inputs": {},
    }
    return render_template("rafter.html", **context)


@wood_bp.route("/rafter/calcular", methods=["POST"])
def rafter_calcular():
    """
    Recibe el formulario, ejecuta el cálculo NDS y devuelve
    la misma página con los resultados.
    """
    form = request.form

    try:
        inputs = RafterInputs(
            span_ft        = float(form["span_ft"]),
            slope_in_ft    = float(form["slope_in_ft"]),
            spacing_in     = float(form["spacing_in"]),
            cantilever_ft  = float(form.get("cantilever_ft", 0)),
            species        = form["species"],
            grade          = form["grade"],
            width_nom      = int(form["width_nom"]),
            depth_nom      = int(form["depth_nom"]),
            dl_roofing     = float(form["dl_roofing"]),
            dl_self        = float(form.get("dl_self", 3)),
            ll             = float(form["ll"]),
            wl             = float(form.get("wl", 0)),
            sl             = float(form.get("sl", 0)),
            cm             = float(form.get("cm", 1.0)),
            ct             = float(form.get("ct", 1.0)),
            deflection_limit = int(form.get("deflection_limit", 360)),
        )

        calc = RafterCalculator(inputs)
        result = calc.calculate()
        svg_content = build_rafter_svg(inputs, result)

        context = {
            "species_options": SPECIES_LABELS,
            "grade_options": GRADE_LABELS,
            "result": result,
            "svg": svg_content,
            "inputs": form,
        }
        return render_template("rafter.html", **context)

    except (ValueError, AssertionError) as e:
        context = {
            "species_options": SPECIES_LABELS,
            "grade_options": GRADE_LABELS,
            "result": None,
            "svg": None,
            "inputs": form,
            "error": str(e),
        }
        return render_template("rafter.html", **context)


@wood_bp.route("/rafter/pdf", methods=["POST"])
def rafter_pdf():
    """Genera y descarga la memoria de cálculo en PDF."""
    form = request.form
    inputs = RafterInputs(
        span_ft        = float(form["span_ft"]),
        slope_in_ft    = float(form["slope_in_ft"]),
        spacing_in     = float(form["spacing_in"]),
        cantilever_ft  = float(form.get("cantilever_ft", 0)),
        species        = form["species"],
        grade          = form["grade"],
        width_nom      = int(form["width_nom"]),
        depth_nom      = int(form["depth_nom"]),
        dl_roofing     = float(form["dl_roofing"]),
        dl_self        = float(form.get("dl_self", 3)),
        ll             = float(form["ll"]),
        wl             = float(form.get("wl", 0)),
        sl             = float(form.get("sl", 0)),
        cm             = float(form.get("cm", 1.0)),
        ct             = float(form.get("ct", 1.0)),
        deflection_limit = int(form.get("deflection_limit", 360)),
    )
    calc   = RafterCalculator(inputs)
    result = calc.calculate()
    pdf_bytes = generate_rafter_pdf(inputs, result)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="ESCALC_Wood_Rafter.pdf",
    )
```

---

## 9. Templates HTML — `templates/`

### 9.1 `templates/base.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ESCALC Wood — {% block title %}{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/escalc.css">
</head>
<body>

  <header class="escalc-header">
    <div class="header-inner">
      <a href="/" class="brand">
        <span class="brand-e">E</span>SCALC
        <span class="brand-module">Wood</span>
      </a>
      <nav class="header-nav">
        <a href="/wood/rafter" class="nav-link {% if request.path == '/wood/rafter' %}active{% endif %}">
          Roof Rafter
        </a>
        <a href="#" class="nav-link disabled" title="Próximamente">Viga de cubierta</a>
        <a href="#" class="nav-link disabled" title="Próximamente">Correa (purlin)</a>
      </nav>
    </div>
  </header>

  <main class="escalc-main">
    {% block content %}{% endblock %}
  </main>

  <footer class="escalc-footer">
    <span>ESCALC · Engineering Software CALC · v1.0 · NDS 2024</span>
  </footer>

</body>
</html>
```

### 9.2 `templates/rafter.html`

```html
{% extends "base.html" %}
{% block title %}Roof Rafter Design{% endblock %}

{% block content %}
<div class="calc-layout">

  <!-- ═══════════════════════════════════════════
       PANEL IZQUIERDO — FORMULARIO DE INPUTS
  ═══════════════════════════════════════════ -->
  <aside class="panel-inputs">
    <form method="POST" action="/wood/rafter/calcular" id="rafter-form">

      <!-- Geometría -->
      <div class="input-group">
        <div class="input-group-title">Geometría del rafter</div>
        <div class="field-row">
          <div class="field">
            <label>Luz horizontal <span class="unit">ft</span></label>
            <input type="number" name="span_ft" value="{{ inputs.get('span_ft', 12) }}"
                   step="0.5" min="4" max="40" required>
          </div>
          <div class="field">
            <label>Pendiente <span class="unit">in/ft</span></label>
            <input type="number" name="slope_in_ft" value="{{ inputs.get('slope_in_ft', 6) }}"
                   step="1" min="1" max="24" required>
          </div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Separación <span class="unit">in</span></label>
            <select name="spacing_in">
              {% for val in [12, 16, 19.2, 24] %}
              <option value="{{ val }}" {% if inputs.get('spacing_in', '16') == val|string %}selected{% endif %}>
                {{ val }}"
              </option>
              {% endfor %}
            </select>
          </div>
          <div class="field">
            <label>Voladizo <span class="unit">ft</span></label>
            <input type="number" name="cantilever_ft" value="{{ inputs.get('cantilever_ft', 0) }}"
                   step="0.5" min="0" max="4">
          </div>
        </div>
      </div>

      <!-- Sección de madera -->
      <div class="input-group">
        <div class="input-group-title">Sección (NDS)</div>
        <div class="field">
          <label>Especie</label>
          <select name="species">
            {% for key, label in species_options.items() %}
            <option value="{{ key }}" {% if inputs.get('species', 'spruce-pine-fir') == key %}selected{% endif %}>
              {{ label }}
            </option>
            {% endfor %}
          </select>
        </div>
        <div class="field">
          <label>Grado visual</label>
          <select name="grade">
            {% for key, label in grade_options.items() %}
            <option value="{{ key }}" {% if inputs.get('grade', 'no2') == key %}selected{% endif %}>
              {{ label }}
            </option>
            {% endfor %}
          </select>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Ancho nominal <span class="unit">in</span></label>
            <select name="width_nom">
              {% for val in [2, 3, 4] %}
              <option value="{{ val }}" {% if inputs.get('width_nom', '2') == val|string %}selected{% endif %}>
                {{ val }}"
              </option>
              {% endfor %}
            </select>
          </div>
          <div class="field">
            <label>Peralte nominal <span class="unit">in</span></label>
            <select name="depth_nom">
              {% for val in [6, 8, 10, 12] %}
              <option value="{{ val }}" {% if inputs.get('depth_nom', '8') == val|string %}selected{% endif %}>
                {{ val }}"
              </option>
              {% endfor %}
            </select>
          </div>
        </div>
      </div>

      <!-- Cargas -->
      <div class="input-group">
        <div class="input-group-title">Cargas <span class="unit">(psf — plano horiz.)</span></div>
        <div class="field-row">
          <div class="field">
            <label>Cubierta DL</label>
            <input type="number" name="dl_roofing" value="{{ inputs.get('dl_roofing', 10) }}" step="1" min="0">
          </div>
          <div class="field">
            <label>Peso propio</label>
            <input type="number" name="dl_self" value="{{ inputs.get('dl_self', 3) }}" step="0.5" min="0">
          </div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Uso LL</label>
            <input type="number" name="ll" value="{{ inputs.get('ll', 20) }}" step="1" min="0">
          </div>
          <div class="field">
            <label>Viento WL</label>
            <input type="number" name="wl" value="{{ inputs.get('wl', 0) }}" step="1" min="0">
          </div>
        </div>
        <div class="field">
          <label>Nieve SL <span class="unit">psf</span></label>
          <input type="number" name="sl" value="{{ inputs.get('sl', 0) }}" step="1" min="0">
        </div>
      </div>

      <!-- Condiciones de servicio -->
      <div class="input-group">
        <div class="input-group-title">Condiciones de servicio</div>
        <div class="field">
          <label>Factor humedad CM</label>
          <select name="cm">
            <option value="1.0" {% if inputs.get('cm', '1.0') == '1.0' %}selected{% endif %}>Seco — CM = 1.0</option>
            <option value="0.85" {% if inputs.get('cm') == '0.85' %}selected{% endif %}>Húmedo — CM = 0.85</option>
          </select>
        </div>
        <div class="field">
          <label>Factor temperatura Ct</label>
          <select name="ct">
            <option value="1.0" {% if inputs.get('ct', '1.0') == '1.0' %}selected{% endif %}>≤ 100°F — Ct = 1.0</option>
            <option value="0.9" {% if inputs.get('ct') == '0.9' %}selected{% endif %}>100–150°F — Ct = 0.9</option>
          </select>
        </div>
        <div class="field">
          <label>Límite deflexión</label>
          <select name="deflection_limit">
            <option value="360" {% if inputs.get('deflection_limit', '360') == '360' %}selected{% endif %}>L / 360 (estándar)</option>
            <option value="240" {% if inputs.get('deflection_limit') == '240' %}selected{% endif %}>L / 240 (cargas totales)</option>
            <option value="180" {% if inputs.get('deflection_limit') == '180' %}selected{% endif %}>L / 180</option>
          </select>
        </div>
      </div>

      <button type="submit" class="btn-calc">Calcular</button>

    </form>
  </aside>

  <!-- ═══════════════════════════════════════════
       PANEL DERECHO — RESULTADOS
  ═══════════════════════════════════════════ -->
  <section class="panel-results">

    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    {% endif %}

    {% if result %}

    <!-- Estado global -->
    <div class="status-card {{ 'ok' if result.all_ok else 'fail' }}">
      <span class="status-dot"></span>
      <span class="status-text">
        {% if result.all_ok %}
          Sección OK — Todas las verificaciones aprobadas
        {% else %}
          Sección insuficiente — Revisar tamaño o vano
        {% endif %}
      </span>
    </div>

    <!-- Métricas clave -->
    <div class="metrics-grid">
      <div class="metric">
        <div class="metric-label">M máx.</div>
        <div class="metric-value">{{ "%.0f"|format(result.M_max_ftlb) }}</div>
        <div class="metric-unit">ft·lb</div>
      </div>
      <div class="metric">
        <div class="metric-label">V máx.</div>
        <div class="metric-value">{{ "%.0f"|format(result.V_max_lb) }}</div>
        <div class="metric-unit">lb</div>
      </div>
      <div class="metric">
        <div class="metric-label">Δ carga viva</div>
        <div class="metric-value">{{ "%.3f"|format(result.delta_LL_in) }}</div>
        <div class="metric-unit">in</div>
      </div>
      <div class="metric">
        <div class="metric-label">Límite L/{{ inputs.get('deflection_limit', 360) }}</div>
        <div class="metric-value">{{ "%.3f"|format(result.delta_limit_in) }}</div>
        <div class="metric-unit">in</div>
      </div>
    </div>

    <!-- Diagrama SVG -->
    <div class="svg-container">
      {{ svg | safe }}
    </div>

    <!-- Tabla de verificaciones -->
    <div class="check-panel">
      <div class="check-panel-title">Verificaciones NDS 2024</div>
      <table class="check-table">
        <thead>
          <tr>
            <th>Verificación</th>
            <th>Actuante</th>
            <th>Admisible</th>
            <th>Relación</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Flexión — f<sub>b</sub> ≤ F'<sub>b</sub></td>
            <td>{{ "%.0f"|format(result.fb_actual) }} psi</td>
            <td>{{ "%.0f"|format(result.Fb_prime) }} psi</td>
            <td>{{ "%.2f"|format(result.ratio_bending) }}</td>
            <td>
              <span class="pill {{ 'ok' if result.bending_ok else 'fail' }}">
                {{ "✓ OK" if result.bending_ok else "✗ Falla" }}
              </span>
            </td>
          </tr>
          <tr>
            <td>Corte — f<sub>v</sub> ≤ F'<sub>v</sub></td>
            <td>{{ "%.0f"|format(result.fv_actual) }} psi</td>
            <td>{{ "%.0f"|format(result.Fv_prime) }} psi</td>
            <td>{{ "%.2f"|format(result.ratio_shear) }}</td>
            <td>
              <span class="pill {{ 'ok' if result.shear_ok else 'fail' }}">
                {{ "✓ OK" if result.shear_ok else "✗ Falla" }}
              </span>
            </td>
          </tr>
          <tr>
            <td>Deflexión — Δ ≤ L/{{ inputs.get('deflection_limit', 360) }}</td>
            <td>{{ "%.3f"|format(result.delta_LL_in) }} in</td>
            <td>{{ "%.3f"|format(result.delta_limit_in) }} in</td>
            <td>{{ "%.2f"|format(result.ratio_deflection) }}</td>
            <td>
              <span class="pill {{ 'ok' if result.deflection_ok else 'fail' }}">
                {{ "✓ OK" if result.deflection_ok else "✗ Falla" }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Factores de ajuste -->
    <div class="check-panel">
      <div class="check-panel-title">Factores de ajuste aplicados (NDS 2024)</div>
      <table class="check-table">
        <thead><tr><th>Factor</th><th>Símbolo</th><th>Valor</th><th>Referencia NDS</th></tr></thead>
        <tbody>
          <tr><td>Duración de carga</td><td>C<sub>D</sub></td><td>{{ result.factors.CD }}</td><td>NDS 2.3.2</td></tr>
          <tr><td>Contenido de humedad</td><td>C<sub>M</sub></td><td>{{ result.factors.CM }}</td><td>NDS 4.3.3</td></tr>
          <tr><td>Temperatura</td><td>C<sub>t</sub></td><td>{{ result.factors.Ct }}</td><td>NDS 2.3.3</td></tr>
          <tr><td>Factor de forma (flexión)</td><td>C<sub>F</sub></td><td>{{ result.factors.CF_b }}</td><td>NDS Sup. 4A</td></tr>
          <tr><td>Estabilidad lateral</td><td>C<sub>L</sub></td><td>{{ result.factors.CL }}</td><td>NDS 3.3.3</td></tr>
          <tr><td>Miembro repetitivo</td><td>C<sub>r</sub></td><td>{{ result.factors.Cr }}</td><td>NDS 4.3.9</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Advertencias -->
    {% if result.warnings %}
    <div class="warnings-panel">
      <div class="check-panel-title">Advertencias</div>
      {% for w in result.warnings %}
      <div class="warning-item">⚠ {{ w }}</div>
      {% endfor %}
    </div>
    {% endif %}

    <!-- Botón PDF -->
    <form method="POST" action="/wood/rafter/pdf">
      {% for key, val in inputs.items() %}
      <input type="hidden" name="{{ key }}" value="{{ val }}">
      {% endfor %}
      <button type="submit" class="btn-pdf">Descargar memoria de cálculo PDF</button>
    </form>

    {% else %}
    <div class="empty-state">
      <p>Complete los datos y presione <strong>Calcular</strong></p>
    </div>
    {% endif %}

  </section>
</div>
{% endblock %}
```

---

## 10. Estilos CSS — `static/css/escalc.css`

```css
/* escalc.css — ESCALC Wood UI
   Paleta: fondo neutro oscuro, acentos en verde (madera)
   Compatible con todos los módulos ESCALC */

:root {
  --bg:           #0f1117;
  --surface:      #181c25;
  --surface2:     #1e2330;
  --border:       #2a2f3e;
  --border2:      #3a4055;
  --text:         #e8eaf0;
  --text2:        #9da5b8;
  --text3:        #606880;
  --accent:       #4caf7d;        /* verde madera */
  --accent-dim:   #2d6b4a;
  --danger:       #e05252;
  --danger-dim:   #4a1f1f;
  --warning:      #e0a020;
  --warning-dim:  #3d2c08;
  --font:         'Segoe UI', system-ui, sans-serif;
  --mono:         'Cascadia Code', 'Fira Code', monospace;
  --radius:       8px;
  --radius-lg:    12px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 14px;
  line-height: 1.6;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── Header ───────────────────────────── */
.escalc-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 1.5rem;
  height: 52px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.header-inner {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  text-decoration: none;
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.5px;
}
.brand-e { color: var(--accent); }
.brand-module {
  font-size: 12px;
  font-weight: 400;
  color: var(--text2);
  margin-left: 8px;
  border-left: 1px solid var(--border2);
  padding-left: 8px;
}
.header-nav { display: flex; gap: 4px; }
.nav-link {
  padding: 6px 12px;
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--text2);
  font-size: 13px;
  transition: background .15s, color .15s;
}
.nav-link:hover, .nav-link.active {
  background: var(--surface2);
  color: var(--text);
}
.nav-link.disabled { opacity: 0.4; pointer-events: none; }

/* ── Layout principal ─────────────────── */
.escalc-main {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem;
}
.calc-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 1.5rem;
  align-items: start;
}
@media (max-width: 900px) {
  .calc-layout { grid-template-columns: 1fr; }
}

/* ── Panel inputs ─────────────────────── */
.panel-inputs {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  position: sticky;
  top: 1rem;
}
.input-group {
  margin-bottom: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border);
}
.input-group:last-of-type { border-bottom: none; }
.input-group-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--text3);
  margin-bottom: 0.75rem;
}
.field { margin-bottom: 0.6rem; }
.field label {
  display: block;
  font-size: 12px;
  color: var(--text2);
  margin-bottom: 3px;
}
.unit {
  font-size: 10px;
  color: var(--text3);
  font-weight: 400;
}
.field input, .field select {
  width: 100%;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  padding: 6px 10px;
  font-size: 13px;
  outline: none;
  transition: border-color .15s;
  font-family: var(--font);
}
.field input:focus, .field select:focus {
  border-color: var(--accent);
}
.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.btn-calc {
  width: 100%;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  padding: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: opacity .15s;
}
.btn-calc:hover { opacity: 0.85; }

/* ── Panel resultados ─────────────────── */
.panel-results { display: flex; flex-direction: column; gap: 1rem; }

.status-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius);
  border: 1px solid;
}
.status-card.ok  { background: rgba(76,175,125,.12); border-color: var(--accent-dim); }
.status-card.fail{ background: var(--danger-dim);   border-color: var(--danger); }
.status-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.status-card.ok  .status-dot  { background: var(--accent); }
.status-card.fail .status-dot { background: var(--danger); }
.status-text { font-size: 13px; font-weight: 500; }
.status-card.ok  .status-text { color: var(--accent); }
.status-card.fail .status-text{ color: var(--danger); }

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 8px;
}
.metric {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 14px;
}
.metric-label { font-size: 11px; color: var(--text2); margin-bottom: 4px; }
.metric-value { font-size: 22px; font-weight: 600; color: var(--text); }
.metric-unit  { font-size: 11px; color: var(--text3); }

.svg-container {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1rem;
  overflow: hidden;
}
.svg-container svg { width: 100%; height: auto; }

.check-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
}
.check-panel-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--text3);
  margin-bottom: 0.75rem;
}
.check-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.check-table th {
  text-align: left;
  color: var(--text2);
  font-weight: 500;
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
}
.check-table td {
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
}
.check-table tr:last-child td { border-bottom: none; }

.pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.pill.ok   { background: rgba(76,175,125,.18); color: var(--accent); }
.pill.fail { background: var(--danger-dim);    color: var(--danger); }

.warnings-panel { padding: 0.75rem 1rem; border-radius: var(--radius); background: var(--warning-dim); border: 1px solid var(--warning); }
.warning-item { font-size: 12px; color: var(--warning); padding: 3px 0; }

.btn-pdf {
  width: 100%;
  background: var(--surface2);
  border: 1px solid var(--border2);
  color: var(--text);
  border-radius: var(--radius);
  padding: 9px;
  font-size: 13px;
  cursor: pointer;
  transition: background .15s;
}
.btn-pdf:hover { background: var(--border); }

.empty-state {
  background: var(--surface);
  border: 1px dashed var(--border2);
  border-radius: var(--radius-lg);
  padding: 3rem;
  text-align: center;
  color: var(--text3);
}
.alert-error {
  padding: 10px 14px;
  background: var(--danger-dim);
  border: 1px solid var(--danger);
  border-radius: var(--radius);
  color: var(--danger);
  font-size: 13px;
}

/* ── Footer ───────────────────────────── */
.escalc-footer {
  border-top: 1px solid var(--border);
  padding: 0.75rem 1.5rem;
  text-align: center;
  font-size: 11px;
  color: var(--text3);
}
```

---

## 11. Gráfico SVG del rafter — `utils/svg_rafter.py`

```python
# utils/svg_rafter.py
# Genera el diagrama SVG del rafter como string HTML-embebible
# Sin dependencias externas — SVG puro Python

import math


def build_rafter_svg(inputs, result) -> str:
    """
    Genera el diagrama SVG del rafter con:
    - Elemento inclinado según pendiente
    - Cargas distribuidas perpendiculares
    - Apoyos (rótula y rodillo)
    - Cotas de luz y voladizo
    - Color verde si OK, rojo si falla
    """
    W, H = 560, 300
    sx, ex = 50, 510   # extremos del span en x
    pw = ex - sx

    L = inputs.span_ft
    cant = inputs.cantilever_ft
    total_L = L + cant
    px_per_ft = pw / total_L

    base_y = 210
    slope_r = inputs.slope_in_ft / 12.0
    span_px = L * px_per_ft
    cant_px = cant * px_per_ft
    ridge_y = base_y - span_px * slope_r

    color = "#4caf7d" if result.all_ok else "#e05252"
    member_thk = max(4, min(12, result.d_in * 1.2))

    # Coordenadas
    x0, y0 = sx, base_y
    x1, y1 = sx + span_px, ridge_y
    x2, y2 = sx + span_px + cant_px, ridge_y - cant_px * slope_r

    # Vector normal al rafter (perpendicular, apuntando hacia arriba-izq)
    dx, dy = x1 - x0, y1 - y0
    length = math.sqrt(dx**2 + dy**2)
    nx, ny = -dy / length, dx / length   # normal unitaria

    arrow_len = 22

    def support_pin(cx, cy):
        """Dibuja soporte de rótula."""
        return (
            f'<polygon points="{cx-10},{cy+18} {cx+10},{cy+18} {cx},{cy}" '
            f'fill="none" stroke="#9da5b8" stroke-width="1.2"/>'
            f'<line x1="{cx-13}" y1="{cy+20}" x2="{cx+13}" y2="{cy+20}" '
            f'stroke="#9da5b8" stroke-width="1.2"/>'
        )

    def support_roller(cx, cy):
        """Dibuja soporte de rodillo."""
        return (
            f'<rect x="{cx-10}" y="{cy}" width="20" height="10" rx="3" '
            f'fill="none" stroke="#9da5b8" stroke-width="1.2"/>'
            f'<line x1="{cx-12}" y1="{cy+12}" x2="{cx+12}" y2="{cy+12}" '
            f'stroke="#9da5b8" stroke-width="1.2"/>'
        )

    lines = []

    # Grid line
    lines.append(
        f'<line x1="30" y1="{base_y+2}" x2="540" y2="{base_y+2}" '
        f'stroke="#2a2f3e" stroke-width="0.5" stroke-dasharray="4 4"/>'
    )

    # Rafter — vano principal
    lines.append(
        f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
        f'stroke="{color}" stroke-width="{member_thk:.1f}" stroke-linecap="round"/>'
    )

    # Rafter — voladizo (si existe)
    if cant > 0:
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{member_thk:.1f}" '
            f'stroke-linecap="round" stroke-dasharray="7 4"/>'
        )

    # Cargas distribuidas (7 flechas perpendiculares al rafter)
    n_arrows = 7
    for i in range(n_arrows + 1):
        t = i / n_arrows
        ax = x0 + t * (x1 - x0)
        ay = y0 + t * (y1 - y0)
        tip_x = ax + nx * 3
        tip_y = ay + ny * 3
        start_x = ax + nx * arrow_len
        start_y = ay + ny * arrow_len
        lines.append(
            f'<line x1="{start_x:.1f}" y1="{start_y:.1f}" '
            f'x2="{tip_x:.1f}" y2="{tip_y:.1f}" '
            f'stroke="#606880" stroke-width="0.9" '
            f'marker-end="url(#arr-load)"/>'
        )

    # Línea de carga distribuida (sobre las flechas)
    lx0 = x0 + nx * arrow_len
    ly0 = y0 + ny * arrow_len
    lx1 = x1 + nx * arrow_len
    ly1 = y1 + ny * arrow_len
    lines.append(
        f'<line x1="{lx0:.1f}" y1="{ly0:.1f}" x2="{lx1:.1f}" y2="{ly1:.1f}" '
        f'stroke="#606880" stroke-width="1"/>'
    )

    # Apoyos
    lines.append(support_pin(x0, y0))
    lines.append(support_roller(x1, y1))

    # Cota: luz horizontal
    dim_y = base_y + 42
    lines.append(
        f'<line x1="{sx}" y1="{base_y}" x2="{sx}" y2="{dim_y+4}" '
        f'stroke="#3a4055" stroke-width="0.5"/>'
    )
    lines.append(
        f'<line x1="{sx+span_px:.1f}" y1="{y1:.1f}" '
        f'x2="{sx+span_px:.1f}" y2="{dim_y+4}" '
        f'stroke="#3a4055" stroke-width="0.5"/>'
    )
    lines.append(
        f'<line x1="{sx}" y1="{dim_y}" x2="{sx+span_px:.1f}" y2="{dim_y}" '
        f'stroke="#9da5b8" stroke-width="0.8" '
        f'marker-start="url(#arr-dim)" marker-end="url(#arr-dim)"/>'
    )
    mid_x = sx + span_px / 2
    lines.append(
        f'<text x="{mid_x:.1f}" y="{dim_y-5}" text-anchor="middle" '
        f'fill="#9da5b8" font-size="11" font-family="Segoe UI,system-ui,sans-serif">'
        f'{L} ft</text>'
    )

    # Cota: voladizo
    if cant > 0:
        lines.append(
            f'<line x1="{sx+span_px:.1f}" y1="{dim_y}" '
            f'x2="{sx+span_px+cant_px:.1f}" y2="{dim_y}" '
            f'stroke="#9da5b8" stroke-width="0.8" stroke-dasharray="3 2" '
            f'marker-end="url(#arr-dim)"/>'
        )
        mid_c = sx + span_px + cant_px / 2
        lines.append(
            f'<text x="{mid_c:.1f}" y="{dim_y-5}" text-anchor="middle" '
            f'fill="#9da5b8" font-size="11" font-family="Segoe UI,system-ui,sans-serif">'
            f'{cant} ft</text>'
        )

    # Etiqueta pendiente
    mid_rx = (x0 + x1) / 2 + 10
    mid_ry = (y0 + y1) / 2 - 14
    lines.append(
        f'<text x="{mid_rx:.1f}" y="{mid_ry:.1f}" text-anchor="middle" '
        f'fill="#606880" font-size="10" font-family="Segoe UI,system-ui,sans-serif">'
        f'{inputs.slope_in_ft:.0f}:12</text>'
    )

    # Info superior
    species_label = inputs.species.replace("-", " ").title()
    lines.append(
        f'<text x="35" y="22" fill="#e8eaf0" font-size="11" font-weight="600" '
        f'font-family="Segoe UI,system-ui,sans-serif">'
        f'{species_label} — {inputs.width_nom}"×{inputs.depth_nom}" — '
        f'w = {result.w_total:.1f} lb/ft</text>'
    )
    lines.append(
        f'<text x="35" y="36" fill="#606880" font-size="10" '
        f'font-family="Segoe UI,system-ui,sans-serif">'
        f'M = {result.M_max_ftlb:.0f} ft·lb  |  '
        f'Δ = {result.delta_LL_in:.3f} in  |  '
        f'Combo: {result.load_combo_governing}</text>'
    )

    # SVG final
    svg = f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"
     role="img" aria-label="Diagrama estructural del rafter">
  <title>Rafter {inputs.span_ft}ft — {inputs.slope_in_ft}:12</title>
  <defs>
    <marker id="arr-load" viewBox="0 0 10 10" refX="8" refY="5"
            markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="#606880"
            stroke-width="1.5" stroke-linecap="round"/>
    </marker>
    <marker id="arr-dim" viewBox="0 0 10 10" refX="8" refY="5"
            markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="#9da5b8"
            stroke-width="1.5" stroke-linecap="round"/>
    </marker>
  </defs>
  {''.join(lines)}
</svg>'''

    return svg
```

---

## 12. Exportación PDF — `utils/pdf_report.py`

```python
# utils/pdf_report.py
# Genera memoria de cálculo en PDF con ReportLab
# ESCALC Wood — Roof Rafter

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import io
from datetime import date


# Paleta ESCALC
C_DARK    = colors.HexColor("#0f1117")
C_SURFACE = colors.HexColor("#181c25")
C_ACCENT  = colors.HexColor("#4caf7d")
C_DANGER  = colors.HexColor("#e05252")
C_TEXT    = colors.HexColor("#e8eaf0")
C_TEXT2   = colors.HexColor("#9da5b8")
C_BORDER  = colors.HexColor("#2a2f3e")
C_WHITE   = colors.white


def generate_rafter_pdf(inputs, result) -> bytes:
    """
    Genera la memoria de cálculo completa en PDF.
    Retorna los bytes del PDF para enviar como respuesta Flask.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle("title",
        fontSize=18, textColor=C_ACCENT, fontName="Helvetica-Bold",
        spaceAfter=4)
    style_sub = ParagraphStyle("sub",
        fontSize=10, textColor=C_TEXT2, fontName="Helvetica",
        spaceAfter=12)
    style_h2 = ParagraphStyle("h2",
        fontSize=12, textColor=C_TEXT, fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=6)
    style_body = ParagraphStyle("body",
        fontSize=9, textColor=C_TEXT, fontName="Helvetica",
        spaceAfter=4, leading=14)
    style_note = ParagraphStyle("note",
        fontSize=8, textColor=C_TEXT2, fontName="Helvetica-Oblique",
        spaceAfter=4)

    def h_line():
        return HRFlowable(width="100%", thickness=0.5,
                          color=C_BORDER, spaceAfter=8, spaceBefore=4)

    def table_style_base():
        return TableStyle([
            ("BACKGROUND",  (0,0), (-1,0),   C_SURFACE),
            ("TEXTCOLOR",   (0,0), (-1,0),   C_TEXT2),
            ("FONTNAME",    (0,0), (-1,0),   "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1),  8),
            ("TEXTCOLOR",   (0,1), (-1,-1),  C_TEXT),
            ("FONTNAME",    (0,1), (-1,-1),  "Helvetica"),
            ("GRID",        (0,0), (-1,-1),  0.3, C_BORDER),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_SURFACE, C_DARK]),
            ("LEFTPADDING",  (0,0), (-1,-1),  6),
            ("RIGHTPADDING", (0,0), (-1,-1),  6),
            ("TOPPADDING",   (0,0), (-1,-1),  4),
            ("BOTTOMPADDING",(0,0), (-1,-1),  4),
        ])

    story = []

    # ── Encabezado ──────────────────────────────────────
    story.append(Paragraph("ESCALC Wood — Roof Rafter", style_title))
    story.append(Paragraph(
        f"Memoria de cálculo · NDS 2024 · {date.today().strftime('%d/%m/%Y')}",
        style_sub))
    story.append(h_line())

    # ── Datos de entrada ─────────────────────────────────
    story.append(Paragraph("1. Datos de entrada", style_h2))
    data_in = [
        ["Parámetro", "Valor", "Unidad"],
        ["Luz horizontal",       f"{inputs.span_ft}",         "ft"],
        ["Pendiente",            f"{inputs.slope_in_ft}:12",  "—"],
        ["Separación rafters",   f"{inputs.spacing_in}",      "in"],
        ["Voladizo",             f"{inputs.cantilever_ft}",   "ft"],
        ["Especie",              inputs.species.replace("-"," ").title(), "—"],
        ["Grado visual",         inputs.grade.upper(),        "—"],
        ["Sección nominal",      f'{inputs.width_nom}"×{inputs.depth_nom}"', "—"],
        ["Sección real (b×d)",   f"{result.b_in}\"×{result.d_in}\"", "in"],
        ["Carga cubierta DL",    f"{inputs.dl_roofing}",      "psf"],
        ["Peso propio rafter",   f"{inputs.dl_self}",         "psf"],
        ["Sobrecarga LL",        f"{inputs.ll}",              "psf"],
        ["Carga viento WL",      f"{inputs.wl}",              "psf"],
        ["Carga nieve SL",       f"{inputs.sl}",              "psf"],
        ["Factor humedad CM",    f"{inputs.cm}",              "—"],
        ["Factor temperatura Ct",f"{inputs.ct}",              "—"],
    ]
    t = Table(data_in, colWidths=[7*cm, 5*cm, 3*cm])
    t.setStyle(table_style_base())
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # ── Propiedades de sección ───────────────────────────
    story.append(Paragraph("2. Propiedades de la sección", style_h2))
    data_sec = [
        ["Propiedad", "Valor", "Unidad"],
        ["Ancho real b",         f"{result.b_in}",               "in"],
        ["Peralte real d",       f"{result.d_in}",               "in"],
        ["Área",                 f"{result.area_in2:.3f}",        "in²"],
        ["Módulo resistente S",  f"{result.S_in3:.3f}",           "in³"],
        ["Inercia I",            f"{result.I_in4:.3f}",           "in⁴"],
    ]
    t2 = Table(data_sec, colWidths=[7*cm, 5*cm, 3*cm])
    t2.setStyle(table_style_base())
    story.append(t2)
    story.append(Spacer(1, 0.4*cm))

    # ── Cargas y combinaciones ────────────────────────────
    story.append(Paragraph("3. Cargas de diseño", style_h2))
    data_load = [
        ["Carga", "Valor", "Unidad"],
        ["Carga muerta total w_DL", f"{result.w_DL:.2f}", "lb/ft"],
        ["Carga viva w_LL",         f"{result.w_LL:.2f}", "lb/ft"],
        ["Carga viento w_WL",       f"{result.w_WL:.2f}", "lb/ft"],
        ["Carga nieve w_SL",        f"{result.w_SL:.2f}", "lb/ft"],
        ["CARGA TOTAL DISEÑO w",    f"{result.w_total:.2f}", "lb/ft"],
        ["Combinación gobernante",  result.load_combo_governing, "—"],
    ]
    t3 = Table(data_load, colWidths=[7*cm, 5*cm, 3*cm])
    ts3 = table_style_base()
    ts3.add("FONTNAME", (0, 6), (-1, 6), "Helvetica-Bold")
    ts3.add("TEXTCOLOR", (0, 6), (-1, 6), C_ACCENT)
    t3.setStyle(ts3)
    story.append(t3)
    story.append(Spacer(1, 0.4*cm))

    # ── Factores de ajuste ────────────────────────────────
    story.append(Paragraph("4. Factores de ajuste NDS 2024", style_h2))
    f = result.factors
    data_fac = [
        ["Factor", "Símbolo", "Valor", "Referencia NDS"],
        ["Duración de carga",   "CD",  f"{f.CD}",    "NDS 2.3.2"],
        ["Contenido humedad",   "CM",  f"{f.CM}",    "NDS 4.3.3"],
        ["Temperatura",         "Ct",  f"{f.Ct}",    "NDS 2.3.3"],
        ["Factor de forma",     "CF",  f"{f.CF_b}",  "NDS Sup. 4A"],
        ["Estabilidad lateral", "CL",  f"{f.CL}",    "NDS 3.3.3"],
        ["Miembro repetitivo",  "Cr",  f"{f.Cr}",    "NDS 4.3.9"],
    ]
    t4 = Table(data_fac, colWidths=[5.5*cm, 2.5*cm, 2.5*cm, 4.5*cm])
    t4.setStyle(table_style_base())
    story.append(t4)
    story.append(Spacer(1, 0.4*cm))

    # ── Resistencias ajustadas ────────────────────────────
    story.append(Paragraph("5. Resistencias ajustadas", style_h2))
    data_res = [
        ["Resistencia", "Referencia (psi)", "Ajustada F' (psi)", "Fórmula"],
        ["Flexión F'b",  f"{result.Fb_ref:.0f}", f"{result.Fb_prime:.0f}",
         "Fb·CD·CM·Ct·CF·CL·Cr"],
        ["Corte F'v",    f"{result.Fv_ref:.0f}", f"{result.Fv_prime:.0f}",
         "Fv·CD·CM·Ct"],
        ["Elastic. E'",  f"{result.E_ref:,}",    f"{result.E_prime:,.0f}",
         "E·CM·Ct"],
    ]
    t5 = Table(data_res, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 4.5*cm])
    t5.setStyle(table_style_base())
    story.append(t5)
    story.append(Spacer(1, 0.4*cm))

    # ── Verificaciones ────────────────────────────────────
    story.append(Paragraph("6. Verificaciones NDS", style_h2))

    def ratio_color(r):
        return C_ACCENT if r <= 1.0 else C_DANGER

    data_chk = [
        ["Verificación", "Actuante", "Admisible", "Relación", "Estado"],
        [
            "Flexión fb ≤ F'b",
            f"{result.fb_actual:.0f} psi",
            f"{result.Fb_prime:.0f} psi",
            f"{result.ratio_bending:.3f}",
            "✓ OK" if result.bending_ok else "✗ FALLA",
        ],
        [
            "Corte fv ≤ F'v",
            f"{result.fv_actual:.0f} psi",
            f"{result.Fv_prime:.0f} psi",
            f"{result.ratio_shear:.3f}",
            "✓ OK" if result.shear_ok else "✗ FALLA",
        ],
        [
            f"Deflexión Δ ≤ L/{inputs.deflection_limit}",
            f"{result.delta_LL_in:.4f} in",
            f"{result.delta_limit_in:.4f} in",
            f"{result.ratio_deflection:.3f}",
            "✓ OK" if result.deflection_ok else "✗ FALLA",
        ],
    ]
    t6 = Table(data_chk, colWidths=[4.5*cm, 2.5*cm, 2.5*cm, 2*cm, 2*cm])
    ts6 = table_style_base()
    for row_idx, ok in enumerate([result.bending_ok, result.shear_ok, result.deflection_ok], start=1):
        c = C_ACCENT if ok else C_DANGER
        ts6.add("TEXTCOLOR", (4, row_idx), (4, row_idx), c)
        ts6.add("FONTNAME",  (4, row_idx), (4, row_idx), "Helvetica-Bold")
    t6.setStyle(ts6)
    story.append(t6)

    # ── Conclusión ────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(h_line())
    conclusion = (
        f"<b>CONCLUSIÓN:</b> La sección {inputs.width_nom}\"×{inputs.depth_nom}\" de "
        f"{inputs.species.replace('-',' ').title()} grado {inputs.grade.upper()}, "
        f"con un vano de {inputs.span_ft} ft y pendiente {inputs.slope_in_ft}:12, "
        + ("<font color='#4caf7d'><b>CUMPLE</b></font> todas las verificaciones NDS 2024."
           if result.all_ok else
           "<font color='#e05252'><b>NO CUMPLE</b></font> alguna verificación NDS 2024. "
           f"Se recomienda aumentar la sección o reducir el vano.")
    )
    story.append(Paragraph(conclusion, style_body))

    # Advertencias
    if result.warnings:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Advertencias:", style_h2))
        for w in result.warnings:
            story.append(Paragraph(f"• {w}", style_note))

    # Pie de página
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "ESCALC · Engineering Software CALC · Módulo Wood · NDS 2024 — "
        "Este documento es una memoria de cálculo preliminar. "
        "Debe ser revisado por un ingeniero estructural habilitado.",
        style_note
    ))

    doc.build(story)
    return buffer.getvalue()
```

---

## 13. Integración con ESCALC principal

Este módulo se integra al portal ESCALC como un Blueprint de Flask independiente. Cuando el proyecto tenga el `app.py` principal de ESCALC, se registra así:

```python
# ESCALC/app.py (portal principal)
from flask import Flask
from foundation.routes import foundation_bp
from steel.routes import steel_bp
from wood.routes.wood import wood_bp           # ← este módulo

app = Flask(__name__)

app.register_blueprint(foundation_bp, url_prefix="/foundation")
app.register_blueprint(steel_bp,      url_prefix="/steel")
app.register_blueprint(wood_bp,       url_prefix="/wood")   # ← registrar aquí

@app.route("/")
def home():
    return render_template("home.html")   # portal principal con todos los módulos
```

La estructura de rutas queda:

```
http://localhost:5000/            ← Portal ESCALC (home con los 4 módulos)
http://localhost:5000/foundation  ← ESCALC Foundation
http://localhost:5000/steel       ← ESCALC Steel Connections
http://localhost:5000/wood        ← ESCALC Wood (este módulo)
http://localhost:5000/wood/rafter ← Rafter calculator
```

---

## 14. Valores de prueba y validación

Usar estos valores para verificar que el cálculo esté correcto contra tablas NDS:

### Caso 1 — Resultado esperado: APRUEBA

| Parámetro | Valor |
|---|---|
| Especie | Spruce-Pine-Fir |
| Grado | No. 2 |
| Sección | 2"×10" |
| Luz | 14 ft |
| Pendiente | 6:12 |
| Separación | 16 in |
| DL cubierta | 10 psf |
| Peso propio | 3 psf |
| LL | 20 psf |
| WL, SL | 0 psf |
| CM, Ct | 1.0 |

**Resultados esperados aproximados:**

- w_DL = 13 × (16/12) = 17.3 lb/ft
- w_LL = 20 × (16/12) = 26.7 lb/ft
- w_total ≈ 44 lb/ft (combo D+L)
- M_max = 44 × 14² / 8 ≈ **1,078 ft·lb**
- V_max = 44 × 14 / 2 ≈ **308 lb**
- F'b = 875 × 1.0 × 1.0 × 1.0 × 1.1 × 1.0 × 1.15 ≈ **1,107 psi**
- fb = (1078 × 12) / 21.4 ≈ **605 psi** → ratio ≈ 0.55 ✓
- Deflexión L/360 = (14×12)/360 = **0.467 in**
- Verificación: APRUEBA ✓

### Caso 2 — Resultado esperado: FALLA POR DEFLEXIÓN

| Parámetro | Valor |
|---|---|
| Especie | Hem-Fir |
| Grado | No. 2 |
| Sección | 2"×6" |
| Luz | 16 ft |
| Pendiente | 4:12 |
| Separación | 24 in |
| LL | 30 psf |

**Resultado esperado:** La deflexión superará L/360 con esta sección pequeña en vano grande.

### Script de test rápido en Python

Guardar como `test_rafter.py` y correr con `python test_rafter.py`:

```python
# test_rafter.py — Test unitario del motor de cálculo
from rafter_engine import RafterInputs, RafterCalculator

def test_caso1():
    inp = RafterInputs(
        span_ft=14, slope_in_ft=6, spacing_in=16, cantilever_ft=0,
        species="spruce-pine-fir", grade="no2",
        width_nom=2, depth_nom=10,
        dl_roofing=10, dl_self=3, ll=20, wl=0, sl=0,
        cm=1.0, ct=1.0,
    )
    r = RafterCalculator(inp).calculate()
    assert r.all_ok, f"Caso 1 debería aprobar. Ratios: b={r.ratio_bending:.2f} v={r.ratio_shear:.2f} d={r.ratio_deflection:.2f}"
    print(f"✓ Caso 1 — APRUEBA | M={r.M_max_ftlb:.0f} ft·lb | fb={r.fb_actual:.0f}/{r.Fb_prime:.0f} psi | Δ={r.delta_LL_in:.3f}/{r.delta_limit_in:.3f} in")

def test_caso2():
    inp = RafterInputs(
        span_ft=16, slope_in_ft=4, spacing_in=24, cantilever_ft=0,
        species="hem-fir", grade="no2",
        width_nom=2, depth_nom=6,
        dl_roofing=10, dl_self=3, ll=30, wl=0, sl=0,
        cm=1.0, ct=1.0,
    )
    r = RafterCalculator(inp).calculate()
    print(f"{'✓' if not r.all_ok else '!'} Caso 2 — {'FALLA (esperado)' if not r.all_ok else 'Aprobó (revisar)'}")
    print(f"  Ratios: flexión={r.ratio_bending:.2f} | corte={r.ratio_shear:.2f} | deflexión={r.ratio_deflection:.2f}")

if __name__ == "__main__":
    print("=== Test ESCALC Wood — Rafter Engine ===")
    test_caso1()
    test_caso2()
    print("=== Tests completados ===")
```

---

## 15. Roadmap — módulos futuros de Wood

| Módulo | Descripción | Prioridad |
|---|---|---|
| **Ridge beam** | Viga de caballete (carga puntual de rafters) | Alta |
| **Purlin / Correa** | Correa de techo entre cabios | Alta |
| **Header** | Dintel sobre vanos | Media |
| **Floor joist** | Viga de entrepiso (NDS) | Media |
| **Column** | Columna de madera (NDS Ch. 3.7) | Media |
| **LVL / Engineered wood** | Vigas laminadas, LVL, PSL | Baja |
| **Conexiones madera-acero** | Integración con ESCALC Steel | Baja |

---

*ESCALC Wood — Documento Maestro v1.0*  
*Engineering Software CALC — Módulo: Roof Rafter NDS 2024*  
*Stack: Python 3.11 · Flask 3.0 · NumPy · ReportLab · Jinja2*  
*IDE: Visual Studio Code — F5 para debug, python app.py para producción local*
