# FundaCalc — Documento Maestro de Desarrollo
> App de Cálculo Estructural de Fundaciones y Zapatas  
> Stack: Python 3.11+ · FastAPI · NumPy · Matplotlib · ReportLab · ezdxf  
> IDE: Visual Studio Code  
> Última actualización: Módulo 3 — Zapata Corrida implementado

---

## Índice

1. [Visión y Alcance](#1-visión-y-alcance)
2. [Estructura de Carpetas](#2-estructura-de-carpetas)
3. [Instalación del Entorno](#3-instalación-del-entorno)
4. [Configuración de VS Code](#4-configuración-de-vs-code)
5. [Módulo Core — Motor de Cálculo](#5-módulo-core--motor-de-cálculo)
   - 5.1 [Normas soportadas](#51-normas-soportadas)
   - 5.2 [zapata_aislada.py — Motor principal](#52-zapata_aisladapy--motor-principal)
   - 5.3 [normas/base.py — Clase abstracta](#53-normasbasepy--clase-abstracta)
   - 5.4 [normas/aci318.py](#54-normasaci318py)
   - 5.5 [normas/cirsoc201.py](#55-normascirsoc201py)
   - 5.6 [normas/nch170.py](#56-normasnch170py)
   - 5.7 [normas/nsr10.py](#57-normasnsr10py)
   - 5.8 [normas/nte_e060.py](#58-normasnte_e060py)
   - 5.9 [normas/ntc_cdmx.py](#59-normasntc_cdmxpy)
   - 5.10 [normas/ehe08.py](#510-normasehe08py)
6. [Módulo UI — Interfaz Gráfica](#6-módulo-ui--interfaz-gráfica)
   - 6.1 [main.py — Punto de entrada](#61-mainpy--punto-de-entrada)
   - 6.2 [ui/ventana_principal.py](#62-uiventana_principalpy)
   - 6.3 [ui/panel_zapata_aislada.py](#63-uipanel_zapata_aisladapy)
   - 6.4 [ui/panel_resultados.py](#64-uipanel_resultadospy)
   - 6.5 [ui/panel_grafico.py](#65-uipanel_graficopy)
7. [Módulo Reportes — PDF](#7-módulo-reportes--pdf)
   - 7.1 [reportes/generador_pdf.py](#71-reportesgenerador_pdfpy)
8. [Módulo Datos — Proyectos](#8-módulo-datos--proyectos)
   - 8.1 [datos/gestor_proyectos.py](#81-datosgestor_proyectospy)
9. [Lógica Estructural Detallada](#9-lógica-estructural-detallada)
10. [Roadmap — Módulos Futuros](#10-roadmap--módulos-futuros)
11. [Pruebas y Validación](#11-pruebas-y-validación)
12. [Módulo Detallado de Acero](#12-módulo-detallado-de-acero)
    - 12.1 [core/detallado_acero.py — Motor de detallado](#121-coredetallado_aceropymotor-de-detallado)
    - 12.2 [ui/panel_detallado.py — Selector interactivo de varilla](#122-uipanel_detalladopy--selector-interactivo-de-varilla)
    - 12.3 [ui/panel_grafico.py — Actualización con armado real](#123-uipanel_graficopy--actualización-con-armado-real)
13. [Exportación CAD — Formato DXF](#13-exportación-cad--formato-dxf)
    - 13.1 [reportes/exportador_dxf.py](#131-reportesexportador_dxfpy)
    - 13.2 [Instalación de ezdxf](#132-instalación-de-ezdxf)
14. [PDF Actualizado con Detallado Completo](#14-pdf-actualizado-con-detallado-completo)
    - 14.1 [reportes/generador_pdf_detallado.py](#141-reportesgenerador_pdf_detalladopy)

---

## 1. Visión y Alcance

### Objetivo
Aplicación de escritorio para el diseño y verificación estructural de fundaciones superficiales, siguiendo normas de países hispanohablantes, con salida de memoria de cálculo en PDF.

### Módulos planificados
| Módulo | Estado | Descripción |
|---|---|---|
| Zapata Aislada    | ✅ Módulo 1 — activo | Zapata cuadrada/rectangular bajo columna individual |
| Zapata Combinada  | ✅ Módulo 2 — activo | Dos columnas sobre una zapata rectangular |
| Zapata Corrida    | ✅ Módulo 3 — activo | Bajo muro portante, carga lineal [kN/m] |
| Losa de Fundación | 🔲 Módulo 4 — futuro | Mat foundation / losa flotante |
| Zapata Excéntrica | 🔲 Módulo 5 — futuro | Con momento, presión trapezoidal |
| Pilotes y encepados | 🔲 Módulo 6 — pro | Grupo de pilotes, encepado |

### Normas soportadas
| País | Norma | Código interno |
|---|---|---|
| Argentina | CIRSOC 201-2005 | `CIRSOC201` |
| Chile | NCh 170 Of. 2016 (con ACI) | `NCH170` |
| Colombia | NSR-10 Título C | `NSR10` |
| México | NTC-CDMX 2017 | `NTC_CDMX` |
| Perú | NTE E.060-2009 | `NTE_E060` |
| España | EHE-08 | `EHE08` |
| Uruguay | UNIT / ACI adoptado | `UNIT_ACI` |

---

## 2. Estructura de Carpetas

Crear esta estructura exacta en VS Code antes de escribir código:

```
FundaCalc/
│
├── main.py                        # Punto de entrada de la aplicación
├── requirements.txt               # Dependencias Python
├── config.json                    # Configuración global (norma por defecto, idioma, etc.)
│
├── core/                          # Motor de cálculo — independiente de la UI
│   ├── __init__.py
│   ├── zapata_aislada.py          # ← MÓDULO 1 (completo en este documento)
│   ├── zapata_combinada.py        # Estructura base (futuro)
│   ├── zapata_corrida.py          # Estructura base (futuro)
│   ├── losa_fundacion.py          # Estructura base (futuro)
│   ├── materiales.py              # Hormigón, acero — propiedades
│   ├── suelos.py                  # Capacidad portante, Terzaghi, Meyerhof
│   └── normas/
│       ├── __init__.py
│       ├── base.py                # Clase abstracta NormaBase
│       ├── aci318.py              # ACI 318-19 (base para varios países)
│       ├── cirsoc201.py           # Argentina
│       ├── nch170.py              # Chile
│       ├── nsr10.py               # Colombia
│       ├── nte_e060.py            # Perú
│       ├── ntc_cdmx.py            # México
│       ├── ehe08.py               # España
│       └── unit_aci.py            # Uruguay
│
├── ui/                            # Interfaz gráfica PyQt6
│   ├── __init__.py
│   ├── ventana_principal.py       # MainWindow, menú, tabs
│   ├── panel_zapata_aislada.py    # Formulario de ingreso datos
│   ├── panel_resultados.py        # Tabla y resumen de resultados
│   ├── panel_grafico.py           # Render de la zapata con matplotlib
│   └── estilos.py                 # Hoja de estilos QSS global
│
├── reportes/
│   ├── __init__.py
│   └── generador_pdf.py           # Memoria de cálculo PDF con ReportLab
│
├── datos/
│   ├── __init__.py
│   ├── gestor_proyectos.py        # Guardar/cargar proyectos JSON
│   └── proyectos/                 # Carpeta de proyectos guardados
│
├── assets/
│   ├── logo.png
│   ├── icono_zapata.svg
│   └── imagenes/                  # Diagramas de referencia
│
└── tests/
    ├── test_zapata_aislada.py
    └── test_normas.py
```

---

## 3. Instalación del Entorno

### 3.1 Requisitos previos
- Python 3.11 o superior → https://www.python.org/downloads/
- Visual Studio Code → https://code.visualstudio.com/
- Git (opcional pero recomendado)

### 3.2 Crear entorno virtual (ejecutar en terminal de VS Code)

```bash
# Desde la carpeta raíz FundaCalc/
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en macOS/Linux
source venv/bin/activate
```

### 3.3 requirements.txt

Crear el archivo `requirements.txt` con este contenido exacto:

```
PyQt6==6.7.0
numpy==1.26.4
scipy==1.13.0
matplotlib==3.9.0
reportlab==4.2.0
Pillow==10.3.0
```

Instalar con:

```bash
pip install -r requirements.txt
```

### 3.4 Verificar instalación

```bash
python -c "import PyQt6, numpy, matplotlib, reportlab; print('Todo OK')"
```

---

## 4. Configuración de VS Code

### 4.1 Extensiones recomendadas

Instalar desde el panel de extensiones (Ctrl+Shift+X):

```
ms-python.python
ms-python.pylance
ms-python.black-formatter
njqdev.vscode-python-typehint
```

### 4.2 settings.json del workspace

Crear `.vscode/settings.json` en la raíz del proyecto:

```json
{
  "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### 4.3 launch.json — Configuración de depuración

Crear `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Ejecutar FundaCalc",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

---

## 5. Módulo Core — Motor de Cálculo

---

### 5.1 Normas soportadas

El diseño clave: **todas las normas comparten la misma interfaz** (`NormaBase`).  
El motor de cálculo llama siempre a los mismos métodos. Cambiar la norma = cambiar el objeto. Nada más.

---

### 5.2 `zapata_aislada.py` — Motor principal

**Ruta:** `core/zapata_aislada.py`

```python
"""
Motor de cálculo para Zapata Aislada.
Compatible con cualquier norma que implemente NormaBase.

Proceso de diseño:
  1. Dimensionamiento en planta (presión admisible del suelo)
  2. Verificación por punzonado (cortante bidireccional)
  3. Verificación por cortante unidireccional (viga ancha)
  4. Diseño a flexión y cálculo de armadura
  5. Verificación de longitud de desarrollo
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from core.normas.base import NormaBase


# ---------------------------------------------------------------------------
# Estructuras de datos de entrada
# ---------------------------------------------------------------------------

@dataclass
class CargasColumna:
    """Cargas aplicadas en la base de la columna (nivel de terreno)."""
    Pd: float = 0.0    # Carga muerta axial [kN]
    Pl: float = 0.0    # Carga viva axial [kN]
    Mxd: float = 0.0   # Momento muerto eje X [kN·m]
    Mxl: float = 0.0   # Momento vivo eje X [kN·m]
    Myd: float = 0.0   # Momento muerto eje Y [kN·m]
    Myl: float = 0.0   # Momento vivo eje Y [kN·m]
    Vxd: float = 0.0   # Cortante muerto eje X [kN]
    Vxl: float = 0.0   # Cortante vivo eje X [kN]

    @property
    def Pu(self) -> float:
        """Carga axial última (combinación 1.2D + 1.6L)."""
        return 1.2 * self.Pd + 1.6 * self.Pl

    @property
    def Pser(self) -> float:
        """Carga de servicio (D + L)."""
        return self.Pd + self.Pl

    @property
    def Mxu(self) -> float:
        return 1.2 * self.Mxd + 1.6 * self.Mxl

    @property
    def Myu(self) -> float:
        return 1.2 * self.Myd + 1.6 * self.Myl


@dataclass
class Columna:
    """Geometría de la columna."""
    ancho: float = 0.30   # Dimensión en X [m]
    largo: float = 0.30   # Dimensión en Y [m]
    Es_circular: bool = False
    diametro: float = 0.30  # Solo si Es_circular


@dataclass
class Suelo:
    """Parámetros geotécnicos del suelo de fundación."""
    qa: float = 150.0      # Capacidad portante admisible [kN/m²]
    Df: float = 1.20       # Profundidad de desplante [m]
    gamma_suelo: float = 18.0  # Peso unitario del suelo [kN/m³]
    gamma_relleno: float = 18.0


@dataclass
class MaterialHormigon:
    """Propiedades del hormigón."""
    fck: float = 25.0   # Resistencia característica [MPa]
    nombre: str = "H-25"

    @property
    def fcd(self) -> float:
        """Resistencia de diseño (con φ=0.65 ACI o según norma)."""
        return 0.85 * self.fck  # fc' en terminología ACI


@dataclass
class MaterialAcero:
    """Propiedades del acero de refuerzo."""
    fy: float = 420.0   # Límite de fluencia [MPa]
    nombre: str = "ADN420"


@dataclass
class GeometriaZapata:
    """
    Dimensiones de la zapata.
    Si se fija 'cuadrada=True' solo se usa 'B' para ambas dimensiones.
    """
    B: float = 0.0        # Dimensión en X [m] (calculada o ingresada)
    L: float = 0.0        # Dimensión en Y [m]
    h: float = 0.50       # Altura total de la zapata [m]
    recubrimiento: float = 0.075  # Recubrimiento libre [m]
    cuadrada: bool = True

    @property
    def d(self) -> float:
        """Peralte efectivo estimado (asumiendo Ø16mm)."""
        return self.h - self.recubrimiento - 0.008  # 8mm = Ø/2 asumido

    @property
    def Area(self) -> float:
        return self.B * self.L


# ---------------------------------------------------------------------------
# Estructura de resultados
# ---------------------------------------------------------------------------

@dataclass
class ResultadosZapata:
    """Contiene todos los resultados del cálculo."""
    # Dimensionamiento
    B_requerido: float = 0.0
    L_requerido: float = 0.0
    h_requerido: float = 0.0
    area_requerida: float = 0.0

    # Presiones
    q_neto: float = 0.0         # Presión neta de diseño [kN/m²]
    q_max: float = 0.0          # Presión máxima bajo la zapata [kN/m²]
    q_min: float = 0.0          # Presión mínima [kN/m²]
    q_ultima: float = 0.0       # Presión última factorizada [kN/m²]

    # Verificaciones
    ok_presion: bool = False
    ok_punzonado: bool = False
    ok_cortante: bool = False

    # Punzonado
    Vu_punz: float = 0.0        # Cortante último por punzonado [kN]
    phi_Vn_punz: float = 0.0    # Resistencia nominal [kN]
    relacion_punzonado: float = 0.0  # Vu / φVn

    # Cortante unidireccional
    Vu_cort: float = 0.0
    phi_Vn_cort: float = 0.0
    relacion_cortante: float = 0.0

    # Armadura — Dirección X
    Mu_x: float = 0.0
    As_x_requerido: float = 0.0  # [cm²/m]
    As_x_minimo: float = 0.0
    As_x_diseno: float = 0.0
    varilla_x: str = ""
    separacion_x: float = 0.0   # [m]

    # Armadura — Dirección Y
    Mu_y: float = 0.0
    As_y_requerido: float = 0.0
    As_y_minimo: float = 0.0
    As_y_diseno: float = 0.0
    varilla_y: str = ""
    separacion_y: float = 0.0

    # Desarrollo
    ld_requerido: float = 0.0
    ld_disponible: float = 0.0
    ok_desarrollo: bool = False

    # Mensajes de verificación
    mensajes: list = field(default_factory=list)

    def agregar_mensaje(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"tipo": tipo, "texto": texto})


# ---------------------------------------------------------------------------
# Motor principal de cálculo
# ---------------------------------------------------------------------------

class ZapataAislada:
    """
    Calcula y diseña una zapata aislada cuadrada o rectangular.
    
    Uso:
        norma = ACI318()
        zapata = ZapataAislada(cargas, columna, suelo, hormigon, acero, norma)
        resultados = zapata.calcular()
    """

    def __init__(
        self,
        cargas: CargasColumna,
        columna: Columna,
        suelo: Suelo,
        hormigon: MaterialHormigon,
        acero: MaterialAcero,
        norma: NormaBase,
        geometria: Optional[GeometriaZapata] = None,
    ):
        self.cargas = cargas
        self.columna = columna
        self.suelo = suelo
        self.hormigon = hormigon
        self.acero = acero
        self.norma = norma
        self.geo = geometria or GeometriaZapata()
        self.resultados = ResultadosZapata()

    # ------------------------------------------------------------------
    # Paso 1: Dimensionamiento en planta
    # ------------------------------------------------------------------
    def dimensionar_planta(self) -> None:
        """Calcula B y L para no superar la capacidad admisible del suelo."""
        res = self.resultados

        # Peso propio estimado de la zapata (10% de la carga de servicio)
        Pp_zapata = 0.10 * self.cargas.Pser
        P_total = self.cargas.Pser + Pp_zapata

        # Presión neta disponible
        q_neta = self.suelo.qa - (self.suelo.Df * self.suelo.gamma_suelo)
        res.q_neto = q_neta

        if q_neta <= 0:
            res.agregar_mensaje(
                "ERROR: La presión neta es ≤ 0. Revisar Df y γ del suelo.", "error"
            )
            return

        # Área requerida
        area_req = P_total / q_neta
        res.area_requerida = area_req

        if self.geo.cuadrada:
            lado = np.sqrt(area_req)
            # Redondear al múltiplo de 0.05 m superior
            lado_redond = np.ceil(lado / 0.05) * 0.05
            self.geo.B = lado_redond
            self.geo.L = lado_redond
        else:
            # Mantener relación B/L si ya fue ingresada
            if self.geo.B > 0 and self.geo.L > 0:
                ratio = self.geo.L / self.geo.B
                self.geo.B = np.ceil(np.sqrt(area_req / ratio) / 0.05) * 0.05
                self.geo.L = np.ceil(self.geo.B * ratio / 0.05) * 0.05
            else:
                lado = np.ceil(np.sqrt(area_req) / 0.05) * 0.05
                self.geo.B = lado
                self.geo.L = lado

        res.B_requerido = self.geo.B
        res.L_requerido = self.geo.L

    # ------------------------------------------------------------------
    # Paso 2: Presiones bajo la zapata
    # ------------------------------------------------------------------
    def calcular_presiones(self) -> None:
        """Calcula presiones de servicio y última bajo la zapata."""
        res = self.resultados
        B, L = self.geo.B, self.geo.L
        d = self.geo.d

        # Peso propio real de la zapata
        gamma_horm = 24.0  # kN/m³
        Pp = B * L * self.geo.h * gamma_horm
        Ps = self.suelo.Df * self.suelo.gamma_suelo * B * L - Pp

        # Presión de servicio
        P_total = self.cargas.Pser + Pp + Ps
        Mx_total = self.cargas.Mxd + self.cargas.Mxl
        My_total = self.cargas.Myd + self.cargas.Myl

        q_med = P_total / (B * L)
        q_ex = abs(Mx_total) / (B * L**2 / 6)
        q_ey = abs(My_total) / (L * B**2 / 6)

        res.q_max = q_med + q_ex + q_ey
        res.q_min = q_med - q_ex - q_ey

        if res.q_max <= self.suelo.qa:
            res.ok_presion = True
            res.agregar_mensaje(
                f"✔ Presión máxima {res.q_max:.1f} kN/m² ≤ qa={self.suelo.qa:.1f} kN/m²", "ok"
            )
        else:
            res.ok_presion = False
            res.agregar_mensaje(
                f"✘ Presión máxima {res.q_max:.1f} kN/m² > qa={self.suelo.qa:.1f} kN/m² — Ampliar zapata", "error"
            )

        # Presión última neta (para diseño de armadura y cortante)
        Pu = self.cargas.Pu
        res.q_ultima = Pu / (B * L)

    # ------------------------------------------------------------------
    # Paso 3: Verificación por punzonado
    # ------------------------------------------------------------------
    def verificar_punzonado(self) -> None:
        """
        Verifica cortante por punzonado (bidireccional) según la norma.
        Perímetro crítico a d/2 de la cara de la columna.
        """
        res = self.resultados
        d = self.geo.d
        c1 = self.columna.ancho
        c2 = self.columna.largo
        B, L = self.geo.B, self.geo.L

        # Perímetro crítico
        b0 = 2 * ((c1 + d) + (c2 + d))

        # Área dentro del perímetro crítico
        A_critica = (c1 + d) * (c2 + d)

        # Fuerza cortante última de punzonado
        Vu_punz = res.q_ultima * (B * L - A_critica)
        res.Vu_punz = Vu_punz

        # Resistencia según norma
        phi_Vn = self.norma.resistencia_punzonado(
            fck=self.hormigon.fck,
            b0=b0,
            d=d,
            c1=c1,
            c2=c2,
        )
        res.phi_Vn_punz = phi_Vn
        res.relacion_punzonado = Vu_punz / phi_Vn

        if Vu_punz <= phi_Vn:
            res.ok_punzonado = True
            res.agregar_mensaje(
                f"✔ Punzonado: Vu={Vu_punz:.1f} kN ≤ φVn={phi_Vn:.1f} kN "
                f"(ratio={res.relacion_punzonado:.2f})", "ok"
            )
        else:
            res.ok_punzonado = False
            res.agregar_mensaje(
                f"✘ Punzonado FALLA: Vu={Vu_punz:.1f} kN > φVn={phi_Vn:.1f} kN. "
                f"Aumentar h o usar hormigón de mayor resistencia.", "error"
            )

    # ------------------------------------------------------------------
    # Paso 4: Verificación por cortante unidireccional (viga ancha)
    # ------------------------------------------------------------------
    def verificar_cortante_unidireccional(self) -> None:
        """
        Cortante unidireccional en la sección crítica a 'd' de la cara de la columna.
        Se verifica en ambas direcciones y se toma el crítico.
        """
        res = self.resultados
        d = self.geo.d
        B, L = self.geo.B, self.geo.L
        c1, c2 = self.columna.ancho, self.columna.largo

        # Longitud del voladizo en cada dirección
        av_x = (L / 2) - (c2 / 2) - d  # voladizo en Y (sección en dirección X)
        av_y = (B / 2) - (c1 / 2) - d

        Vu_x = res.q_ultima * B * av_x  # [kN]
        Vu_y = res.q_ultima * L * av_y

        Vu_crit = max(Vu_x, Vu_y)
        bw_crit = B if Vu_x >= Vu_y else L  # ancho de sección crítica
        res.Vu_cort = Vu_crit

        # Resistencia según norma
        phi_Vn = self.norma.resistencia_cortante_unidireccional(
            fck=self.hormigon.fck,
            bw=bw_crit,
            d=d,
        )
        res.phi_Vn_cort = phi_Vn
        res.relacion_cortante = Vu_crit / phi_Vn

        if Vu_crit <= phi_Vn:
            res.ok_cortante = True
            res.agregar_mensaje(
                f"✔ Cortante: Vu={Vu_crit:.1f} kN ≤ φVn={phi_Vn:.1f} kN "
                f"(ratio={res.relacion_cortante:.2f})", "ok"
            )
        else:
            res.ok_cortante = False
            res.agregar_mensaje(
                f"✘ Cortante FALLA: Aumentar d (altura de la zapata).", "error"
            )

    # ------------------------------------------------------------------
    # Paso 5: Diseño a flexión y armadura
    # ------------------------------------------------------------------
    def diseno_flexion(self) -> None:
        """
        Momento último en la cara de la columna en cada dirección.
        Calcula el área de acero requerida.
        """
        res = self.resultados
        d = self.geo.d
        B, L = self.geo.B, self.geo.L
        c1, c2 = self.columna.ancho, self.columna.largo
        qu = res.q_ultima
        fck = self.hormigon.fck
        fy = self.acero.fy

        # Voladizos para momento
        vol_x = (B / 2) - (c1 / 2)  # dirección X
        vol_y = (L / 2) - (c2 / 2)  # dirección Y

        # Momento último por metro ancho (kN·m/m)
        Mu_x = qu * vol_x**2 / 2
        Mu_y = qu * vol_y**2 / 2

        res.Mu_x = Mu_x
        res.Mu_y = Mu_y

        # Área de acero requerida en cada dirección
        res.As_x_requerido = self.norma.area_acero_flexion(Mu=Mu_x, d=d, fck=fck, fy=fy)
        res.As_y_requerido = self.norma.area_acero_flexion(Mu=Mu_y, d=d, fck=fck, fy=fy)

        # Área mínima según norma
        res.As_x_minimo = self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d)
        res.As_y_minimo = self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d)

        # Área de diseño = max(requerido, mínimo)
        res.As_x_diseno = max(res.As_x_requerido, res.As_x_minimo)
        res.As_y_diseno = max(res.As_y_requerido, res.As_y_minimo)

        # Selección de varilla y separación
        res.varilla_x, res.separacion_x = self._seleccionar_varilla(res.As_x_diseno)
        res.varilla_y, res.separacion_y = self._seleccionar_varilla(res.As_y_diseno)

        res.agregar_mensaje(
            f"✔ Armadura X: {res.varilla_x} @ {res.separacion_x*100:.0f} cm "
            f"(As={res.As_x_diseno:.2f} cm²/m)", "ok"
        )
        res.agregar_mensaje(
            f"✔ Armadura Y: {res.varilla_y} @ {res.separacion_y*100:.0f} cm "
            f"(As={res.As_y_diseno:.2f} cm²/m)", "ok"
        )

    def _seleccionar_varilla(self, As_cm2_por_m: float) -> tuple[str, float]:
        """
        Selecciona la varilla comercial más conveniente y calcula la separación.
        Returns: (nombre_varilla, separacion_en_metros)
        
        Tabla de varillas métricas comunes (diámetro, área en cm²):
        """
        varillas = [
            ("Ø8mm",  0.503),
            ("Ø10mm", 0.785),
            ("Ø12mm", 1.131),
            ("Ø16mm", 2.011),
            ("Ø20mm", 3.142),
            ("Ø25mm", 4.909),
            ("Ø32mm", 8.042),
        ]

        mejor = None
        for nombre, area_barra in varillas:
            sep = area_barra / As_cm2_por_m  # metros
            if 0.10 <= sep <= 0.35:  # separación razonable: 10 a 35 cm
                mejor = (nombre, sep)
                break

        if mejor is None:
            # Usar Ø25 con separación forzada
            area_barra = 4.909
            sep = min(max(area_barra / As_cm2_por_m, 0.10), 0.35)
            mejor = ("Ø25mm", sep)

        # Redondear separación al cm inferior
        sep_redond = np.floor(mejor[1] * 100) / 100
        return mejor[0], sep_redond

    # ------------------------------------------------------------------
    # Paso 6: Longitud de desarrollo
    # ------------------------------------------------------------------
    def verificar_longitud_desarrollo(self) -> None:
        """Verifica que haya espacio suficiente para el desarrollo del refuerzo."""
        res = self.resultados
        B = self.geo.B
        c1 = self.columna.ancho
        recub = self.geo.recubrimiento

        # Longitud disponible desde cara de columna hasta borde de zapata
        ld_disponible = (B / 2) - (c1 / 2) - recub
        res.ld_disponible = ld_disponible

        # Longitud requerida según norma
        db = 0.016  # Asumiendo Ø16mm de la varilla
        ld_req = self.norma.longitud_desarrollo(
            db=db, fck=self.hormigon.fck, fy=self.acero.fy
        )
        res.ld_requerido = ld_req

        if ld_disponible >= ld_req:
            res.ok_desarrollo = True
            res.agregar_mensaje(
                f"✔ Desarrollo: ld_disp={ld_disponible*100:.0f} cm ≥ ld_req={ld_req*100:.0f} cm", "ok"
            )
        else:
            res.ok_desarrollo = False
            res.agregar_mensaje(
                f"✘ Desarrollo insuficiente: Aumentar B o usar ganchos estándar.", "advertencia"
            )

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------
    def calcular(self) -> ResultadosZapata:
        """
        Ejecuta el proceso completo de diseño en orden.
        Retorna el objeto ResultadosZapata con todos los resultados.
        """
        self.dimensionar_planta()
        self.calcular_presiones()

        # Iterar altura si falla punzonado o cortante
        max_iter = 5
        for i in range(max_iter):
            self.verificar_punzonado()
            self.verificar_cortante_unidireccional()

            if self.resultados.ok_punzonado and self.resultados.ok_cortante:
                break
            else:
                self.geo.h += 0.05  # Incrementar 5 cm y reintentar
                self.resultados.agregar_mensaje(
                    f"ℹ Iteración {i+1}: Aumentando h a {self.geo.h:.2f} m", "info"
                )

        self.geo.h = np.ceil(self.geo.h / 0.05) * 0.05  # Normalizar
        self.resultados.h_requerido = self.geo.h

        self.diseno_flexion()
        self.verificar_longitud_desarrollo()

        return self.resultados
```

---

### 5.3 `normas/base.py` — Clase abstracta

**Ruta:** `core/normas/base.py`

```python
"""
Clase base abstracta para todas las normas de diseño.
Cada norma debe implementar estos métodos.
"""

from abc import ABC, abstractmethod


class NormaBase(ABC):
    """Interfaz común para todas las normas de diseño de hormigón."""

    nombre: str = "Base"
    pais: str = "N/A"
    year: int = 0
    phi_flexion: float = 0.90
    phi_cortante: float = 0.75

    @abstractmethod
    def resistencia_punzonado(
        self, fck: float, b0: float, d: float, c1: float, c2: float
    ) -> float:
        """
        Resistencia de diseño por punzonado (cortante bidireccional).

        Args:
            fck: Resistencia característica del hormigón [MPa]
            b0:  Perímetro crítico [m]
            d:   Peralte efectivo [m]
            c1:  Dimensión columna en dirección 1 [m]
            c2:  Dimensión columna en dirección 2 [m]

        Returns:
            φ·Vn [kN]
        """
        ...

    @abstractmethod
    def resistencia_cortante_unidireccional(
        self, fck: float, bw: float, d: float
    ) -> float:
        """
        Resistencia de diseño por cortante unidireccional.

        Args:
            fck: Resistencia característica [MPa]
            bw:  Ancho de la sección [m]
            d:   Peralte efectivo [m]

        Returns:
            φ·Vn [kN]
        """
        ...

    @abstractmethod
    def area_acero_flexion(
        self, Mu: float, d: float, fck: float, fy: float
    ) -> float:
        """
        Área de acero requerida por flexión.

        Args:
            Mu:  Momento último [kN·m/m]
            d:   Peralte efectivo [m]
            fck: Resistencia hormigón [MPa]
            fy:  Límite de fluencia del acero [MPa]

        Returns:
            As [cm²/m]
        """
        ...

    @abstractmethod
    def area_acero_minimo(
        self, fck: float, fy: float, bw: float, d: float
    ) -> float:
        """
        Área mínima de acero según la norma.

        Returns:
            As_min [cm²/m]
        """
        ...

    @abstractmethod
    def longitud_desarrollo(
        self, db: float, fck: float, fy: float
    ) -> float:
        """
        Longitud de desarrollo de barras en tracción.

        Args:
            db:  Diámetro nominal de la barra [m]
            fck: Resistencia del hormigón [MPa]
            fy:  Fluencia del acero [MPa]

        Returns:
            ld [m]
        """
        ...

    def combinaciones_carga(self) -> dict:
        """
        Factores de combinación de carga.
        Puede sobreescribirse si la norma difiere de ACI.
        """
        return {
            "principal": {"D": 1.2, "L": 1.6},
            "con_viento": {"D": 1.2, "L": 1.0, "W": 1.6},
            "con_sismo": {"D": 1.2, "L": 1.0, "E": 1.0},
        }

    def __str__(self):
        return f"{self.nombre} ({self.pais}, {self.year})"
```

---

### 5.4 `normas/aci318.py`

**Ruta:** `core/normas/aci318.py`

```python
"""
ACI 318-19 — American Concrete Institute
Base para Chile (NCh), Uruguay (UNIT) y Perú (NTE E.060 usa ACI como referencia).
"""

import numpy as np
from core.normas.base import NormaBase


class ACI318(NormaBase):

    nombre = "ACI 318-19"
    pais = "USA / Internacional"
    year = 2019
    phi_flexion = 0.90
    phi_cortante = 0.75

    def resistencia_punzonado(self, fck, b0, d, c1, c2) -> float:
        """
        ACI 318-19 §22.6.5.2
        Vc = mínimo de tres expresiones.
        Unidades: fck en MPa, b0 y d en m → resultado en kN
        """
        # Relación de aspecto de la columna
        beta = max(c1, c2) / min(c1, c2) if min(c1, c2) > 0 else 1.0
        # αs: 40 para columna interior, 30 borde, 20 esquina
        alpha_s = 40.0

        # Conversión a mm para fórmulas ACI (trabajan en mm y MPa → N)
        b0_mm = b0 * 1000
        d_mm = d * 1000

        Vc1 = (0.33 * np.sqrt(fck)) * b0_mm * d_mm
        Vc2 = (0.17 * (1 + 2 / beta) * np.sqrt(fck)) * b0_mm * d_mm
        Vc3 = (0.083 * (2 + alpha_s * d_mm / b0_mm) * np.sqrt(fck)) * b0_mm * d_mm

        Vc = min(Vc1, Vc2, Vc3)  # en Newtons
        return self.phi_cortante * Vc / 1000  # kN

    def resistencia_cortante_unidireccional(self, fck, bw, d) -> float:
        """
        ACI 318-19 §22.5.5.1 (tabla simplificada)
        Vc = 0.17 · √fck · bw · d  (sin refuerzo de cortante)
        """
        bw_mm = bw * 1000
        d_mm = d * 1000
        Vc = 0.17 * np.sqrt(fck) * bw_mm * d_mm  # Newtons
        return self.phi_cortante * Vc / 1000  # kN

    def area_acero_flexion(self, Mu, d, fck, fy) -> float:
        """
        Diseño por flexión — método simplificado ACI.
        Mu en kN·m/m, d en m → As en cm²/m
        """
        phi = self.phi_flexion
        # Convertir a N·mm/mm
        Mu_Nmm = Mu * 1e6
        d_mm = d * 1000

        # Cuantía de refuerzo requerida (aproximación iterativa)
        # Rn = Mu / (φ · bw · d²)  con bw = 1000mm
        Rn = Mu_Nmm / (phi * 1000 * d_mm**2)

        # ρ = (0.85·fck/fy) · [1 - √(1 - 2Rn/(0.85·fck))]
        m = fy / (0.85 * fck)
        discriminante = 1 - 2 * Rn / (0.85 * fck)
        if discriminante < 0:
            discriminante = 0  # sección insuficiente, se debe aumentar d

        rho = (1 / m) * (1 - np.sqrt(discriminante))
        As_mm2 = rho * 1000 * d_mm  # mm²/m
        return As_mm2 / 100  # cm²/m

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """
        ACI 318-19 §9.6.1.2
        As_min = max(0.25√fck/fy, 1.4/fy) · bw · d
        """
        bw_mm = bw * 1000
        d_mm = d * 1000
        rho_min = max(0.25 * np.sqrt(fck) / fy, 1.4 / fy)
        As_min = rho_min * bw_mm * d_mm  # mm²/m
        return As_min / 100  # cm²/m

    def longitud_desarrollo(self, db, fck, fy) -> float:
        """
        ACI 318-19 §25.5.2 — Longitud de desarrollo simplificada.
        db en m → ld en m
        """
        db_mm = db * 1000
        # Para barra recta en tracción, condiciones normales
        ld_mm = (fy / (1.1 * np.sqrt(fck))) * db_mm
        ld_mm = max(ld_mm, 300)  # mínimo 300 mm
        return ld_mm / 1000  # m
```

---

### 5.5 `normas/cirsoc201.py`

**Ruta:** `core/normas/cirsoc201.py`

```python
"""
CIRSOC 201-2005 — Argentina
Basado en ACI 318-99 con adaptaciones locales.
Resistencias características usan fck (equivalente a f'c).
"""

import numpy as np
from core.normas.aci318 import ACI318


class CIRSOC201(ACI318):
    """
    CIRSOC 201-2005 Argentina.
    Hereda de ACI318 con modificaciones según CIRSOC.
    """

    nombre = "CIRSOC 201-2005"
    pais = "Argentina"
    year = 2005
    # CIRSOC usa los mismos factores φ que ACI 318-99
    phi_flexion = 0.90
    phi_cortante = 0.75

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """
        CIRSOC 201 Art. 10.5 — mismo criterio que ACI.
        Cuantía mínima: ρ_min = 0.0020 para As de temperatura y retracción.
        Para flexión: igual que ACI.
        """
        return super().area_acero_minimo(fck, fy, bw, d)

    def combinaciones_carga(self) -> dict:
        """CIRSOC 103 combinaciones de carga."""
        return {
            "principal": {"D": 1.4, "L": 1.7},  # CIRSOC usa 1.4D + 1.7L
            "con_viento": {"D": 1.05, "L": 1.275, "W": 1.275},
            "con_sismo": {"D": 1.05, "L": 1.275, "E": 1.4},
        }
```

---

### 5.6 `normas/nch170.py`

**Ruta:** `core/normas/nch170.py`

```python
"""
NCh 170 Of. 2016 — Chile
Chile adopta ACI 318 con modificaciones menores.
Usa la misma metodología pero con nomenclatura local:
  - fck = resistencia característica (equivalente a f'c)
  - fy  = tensión de fluencia del acero
"""

from core.normas.aci318 import ACI318


class NCh170(ACI318):

    nombre = "NCh 170 Of.2016"
    pais = "Chile"
    year = 2016

    # Chile adopta íntegramente los factores φ de ACI 318-14
    phi_flexion = 0.90
    phi_cortante = 0.75
```

---

### 5.7 `normas/nsr10.py`

**Ruta:** `core/normas/nsr10.py`

```python
"""
NSR-10 Título C — Colombia
Norma Colombiana de Construcción Sismo-Resistente.
Título C basado en ACI 318-05 con adaptaciones.
"""

import numpy as np
from core.normas.aci318 import ACI318


class NSR10(ACI318):

    nombre = "NSR-10 Título C"
    pais = "Colombia"
    year = 2010
    phi_flexion = 0.90
    phi_cortante = 0.75

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """
        NSR-10 C.10.5 — igual que ACI 318 con cuantía mínima.
        """
        return super().area_acero_minimo(fck, fy, bw, d)
```

---

### 5.8 `normas/nte_e060.py`

**Ruta:** `core/normas/nte_e060.py`

```python
"""
NTE E.060-2009 — Perú
Norma Técnica de Edificación — Concreto Armado.
Basada en ACI 318-99.
"""

from core.normas.aci318 import ACI318


class NTE_E060(ACI318):

    nombre = "NTE E.060-2009"
    pais = "Perú"
    year = 2009
    phi_flexion = 0.90
    phi_cortante = 0.85  # Perú usa φ=0.85 para cortante (diferencia clave)
```

---

### 5.9 `normas/ntc_cdmx.py`

**Ruta:** `core/normas/ntc_cdmx.py`

```python
"""
NTC-CDMX 2017 — México (Ciudad de México)
Normas Técnicas Complementarias para Diseño y Construcción de Estructuras de Concreto.
México tiene un sistema distinto: usa f'c en kg/cm² y fy en kg/cm².
Esta implementación convierte internamente a MPa para mantener la interfaz unificada.
"""

import numpy as np
from core.normas.base import NormaBase


class NTC_CDMX(NormaBase):

    nombre = "NTC-CDMX 2017"
    pais = "México"
    year = 2017
    phi_flexion = 0.90   # FR para flexión
    phi_cortante = 0.80  # FR para cortante en México

    def resistencia_punzonado(self, fck, b0, d, c1, c2) -> float:
        """
        NTC-CDMX §6.5 — Resistencia al punzonamiento.
        vcu = 0.5 · (fck)^0.5  [MPa]  → mismo orden que ACI
        """
        b0_mm = b0 * 1000
        d_mm = d * 1000
        vcu = 0.5 * np.sqrt(fck)  # MPa
        Vcu = vcu * b0_mm * d_mm  # N
        return self.phi_cortante * Vcu / 1000  # kN

    def resistencia_cortante_unidireccional(self, fck, bw, d) -> float:
        """
        NTC-CDMX §6.4 — Cortante en vigas y losas.
        """
        bw_mm = bw * 1000
        d_mm = d * 1000
        Vcu = 0.5 * np.sqrt(fck) * bw_mm * d_mm  # N
        return self.phi_cortante * Vcu / 1000  # kN

    def area_acero_flexion(self, Mu, d, fck, fy) -> float:
        """
        NTC-CDMX §7.2 — Diseño por flexión.
        Mismo procedimiento que ACI con factores locales.
        """
        phi = self.phi_flexion
        Mu_Nmm = Mu * 1e6
        d_mm = d * 1000
        Rn = Mu_Nmm / (phi * 1000 * d_mm**2)
        m = fy / (0.85 * fck)
        disc = max(1 - 2 * Rn / (0.85 * fck), 0)
        rho = (1 / m) * (1 - np.sqrt(disc))
        return rho * 1000 * d_mm / 100  # cm²/m

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """NTC-CDMX: ρ_min = 0.001 para losas y zapatas."""
        bw_mm = bw * 1000
        d_mm = d * 1000
        rho_min = max(0.25 * np.sqrt(fck) / fy, 0.001)
        return rho_min * bw_mm * d_mm / 100  # cm²/m

    def longitud_desarrollo(self, db, fck, fy) -> float:
        """NTC-CDMX §8.4 — Desarrollo de refuerzo."""
        db_mm = db * 1000
        ld_mm = (fy / (1.1 * np.sqrt(fck))) * db_mm
        return max(ld_mm, 300) / 1000  # m
```

---

### 5.10 `normas/ehe08.py`

**Ruta:** `core/normas/ehe08.py`

```python
"""
EHE-08 — España
Instrucción de Hormigón Estructural.
Usa el sistema europeo (Eurocódigo base):
  - fck en MPa
  - γc = 1.5 (hormigón), γs = 1.15 (acero)
  - fcd = fck / γc,  fyd = fyk / γs
"""

import numpy as np
from core.normas.base import NormaBase


class EHE08(NormaBase):

    nombre = "EHE-08"
    pais = "España"
    year = 2008
    gamma_c = 1.5    # Coeficiente parcial del hormigón
    gamma_s = 1.15   # Coeficiente parcial del acero
    phi_flexion = 1.0 / 1.15   # ≈ 0.87 (inverso del γs)
    phi_cortante = 1.0 / 1.5   # ≈ 0.67 (inverso del γc)

    @property
    def alpha_cc(self):
        """Coeficiente de fatiga del hormigón."""
        return 0.85

    def fcd(self, fck):
        return self.alpha_cc * fck / self.gamma_c

    def fyd(self, fyk):
        return min(fyk / self.gamma_s, 400.0)  # MPa

    def resistencia_punzonado(self, fck, b0, d, c1, c2) -> float:
        """
        EHE-08 Art. 46 — Punzonamiento.
        τRd = 0.18/γc · ξ · (100·ρl·fck)^(1/3)  [MPa]
        """
        b0_mm = b0 * 1000
        d_mm = d * 1000
        xi = min(1 + np.sqrt(200 / d_mm), 2.0)  # factor de tamaño
        rho_l = 0.005  # cuantía estimada (se puede iterar)

        tau_Rd = (0.18 / self.gamma_c) * xi * (100 * rho_l * fck) ** (1/3)
        Vrd = tau_Rd * b0_mm * d_mm  # N
        return Vrd / 1000  # kN (sin factor φ, ya incluido en τRd)

    def resistencia_cortante_unidireccional(self, fck, bw, d) -> float:
        """
        EHE-08 Art. 44 — Cortante sin armadura específica.
        Vcu = [0.18/γc · ξ · (100·ρl·fck)^(1/3)] · bw · d
        """
        bw_mm = bw * 1000
        d_mm = d * 1000
        xi = min(1 + np.sqrt(200 / d_mm), 2.0)
        rho_l = 0.005

        tau_cu = (0.18 / self.gamma_c) * xi * (100 * rho_l * fck) ** (1/3)
        Vcu = tau_cu * bw_mm * d_mm  # N
        return Vcu / 1000  # kN

    def area_acero_flexion(self, Mu, d, fck, fy) -> float:
        """
        EHE-08 Art. 42 — Diseño a flexión simple.
        μ = Md / (b·d²·fcd)  →  ω → As = ω·b·d·fcd/fyd
        """
        fcd_val = self.fcd(fck)
        fyd_val = self.fyd(fy)
        d_m = d
        b = 1.0  # 1 metro de ancho

        mu = Mu / (b * d_m**2 * fcd_val * 1000)  # adimensional
        mu = min(mu, 0.30)  # límite de dominio

        # ω = 1 - √(1 - 2μ)
        omega = 1 - np.sqrt(max(1 - 2 * mu, 0))
        As_m2 = omega * b * d_m * fcd_val * 1000 / fyd_val  # m²/m
        return As_m2 * 10000  # cm²/m

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """EHE-08 Art. 42.3.5 — Cuantía mínima."""
        fyd_val = self.fyd(fy)
        rho_min = max(0.0028, 0.0028 * (30 / fck) if fck < 30 else 0.0028)
        bw_mm = bw * 1000
        d_mm = d * 1000
        return rho_min * bw_mm * d_mm / 100  # cm²/m

    def longitud_desarrollo(self, db, fck, fy) -> float:
        """
        EHE-08 Art. 69.5.1 — Longitud básica de anclaje.
        lb = (fy / (4·fbd)) · db
        fbd = 2.25 · η1 · η2 · fctd
        """
        fctd = 0.21 * fck**(2/3) / self.gamma_c
        fbd = 2.25 * fctd
        db_mm = db * 1000
        fyd_val = self.fyd(fy)
        lb_mm = (fyd_val / (4 * fbd)) * db_mm
        return max(lb_mm, 300) / 1000  # m

    def combinaciones_carga(self) -> dict:
        """EHE-08 / Eurocódigo combinaciones."""
        return {
            "fundamental": {"G": 1.35, "Q": 1.5},
            "accidental": {"G": 1.0, "Q": 1.0, "A": 1.0},
        }
```

---

## 6. Módulo UI — Interfaz Gráfica

---

### 6.1 `main.py` — Punto de entrada

**Ruta:** `main.py` (raíz del proyecto)

```python
"""
FundaCalc — Punto de entrada principal.
Inicializa la aplicación PyQt6.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.ventana_principal import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FundaCalc")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FundaCalc Dev")

    # Cargar hoja de estilos global
    try:
        with open("ui/estilos.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass  # Continúa sin estilos personalizados

    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

---

### 6.2 `ui/ventana_principal.py`

**Ruta:** `ui/ventana_principal.py`

```python
"""
Ventana principal de FundaCalc.
Contiene: barra de menú, barra de herramientas, pestañas de módulos.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QMenuBar, QMenu, QStatusBar, QLabel, QComboBox,
    QHBoxLayout, QToolBar, QPushButton, QFileDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from ui.panel_zapata_aislada import PanelZapataAislada
from datos.gestor_proyectos import GestorProyectos


# Mapa de normas disponibles
NORMAS_DISPONIBLES = {
    "ACI 318-19 (Internacional)": "ACI318",
    "CIRSOC 201-2005 (Argentina)": "CIRSOC201",
    "NCh 170 Of.2016 (Chile)": "NCH170",
    "NSR-10 (Colombia)": "NSR10",
    "NTE E.060-2009 (Perú)": "NTE_E060",
    "NTC-CDMX 2017 (México)": "NTC_CDMX",
    "EHE-08 (España)": "EHE08",
}


class VentanaPrincipal(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FundaCalc v1.0 — Diseño de Fundaciones")
        self.setMinimumSize(1100, 750)
        self.gestor = GestorProyectos()
        self._norma_actual = "ACI318"

        self._crear_menu()
        self._crear_toolbar()
        self._crear_central()
        self._crear_statusbar()

    # ------------------------------------------------------------------
    def _crear_menu(self):
        menubar = self.menuBar()

        # Archivo
        m_archivo = menubar.addMenu("&Archivo")
        a_nuevo = QAction("&Nuevo proyecto", self)
        a_nuevo.setShortcut("Ctrl+N")
        a_nuevo.triggered.connect(self._nuevo_proyecto)

        a_abrir = QAction("&Abrir proyecto...", self)
        a_abrir.setShortcut("Ctrl+O")
        a_abrir.triggered.connect(self._abrir_proyecto)

        a_guardar = QAction("&Guardar proyecto", self)
        a_guardar.setShortcut("Ctrl+S")
        a_guardar.triggered.connect(self._guardar_proyecto)

        a_salir = QAction("&Salir", self)
        a_salir.setShortcut("Ctrl+Q")
        a_salir.triggered.connect(self.close)

        m_archivo.addAction(a_nuevo)
        m_archivo.addAction(a_abrir)
        m_archivo.addAction(a_guardar)
        m_archivo.addSeparator()
        m_archivo.addAction(a_salir)

        # Reportes
        m_reportes = menubar.addMenu("&Reportes")
        a_pdf = QAction("Exportar PDF...", self)
        a_pdf.setShortcut("Ctrl+P")
        a_pdf.triggered.connect(self._exportar_pdf)
        m_reportes.addAction(a_pdf)

        # Ayuda
        m_ayuda = menubar.addMenu("&Ayuda")
        a_acerca = QAction("Acerca de FundaCalc", self)
        a_acerca.triggered.connect(self._acerca_de)
        m_ayuda.addAction(a_acerca)

    # ------------------------------------------------------------------
    def _crear_toolbar(self):
        toolbar = QToolBar("Herramientas principales")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Selector de norma
        lbl_norma = QLabel("  Norma de diseño:  ")
        self.combo_norma = QComboBox()
        self.combo_norma.addItems(list(NORMAS_DISPONIBLES.keys()))
        self.combo_norma.setMinimumWidth(250)
        self.combo_norma.currentIndexChanged.connect(self._cambiar_norma)

        btn_calcular = QPushButton("▶  Calcular")
        btn_calcular.setObjectName("btn_calcular_primary")
        btn_calcular.clicked.connect(self._ejecutar_calculo)

        btn_pdf = QPushButton("📄  Exportar PDF")
        btn_pdf.clicked.connect(self._exportar_pdf)

        toolbar.addWidget(lbl_norma)
        toolbar.addWidget(self.combo_norma)
        toolbar.addSeparator()
        toolbar.addWidget(btn_calcular)
        toolbar.addWidget(btn_pdf)

    # ------------------------------------------------------------------
    def _crear_central(self):
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1: Zapata Aislada
        self.panel_zapata_aislada = PanelZapataAislada(norma_codigo=self._norma_actual)
        self.tabs.addTab(self.panel_zapata_aislada, "🏗  Zapata Aislada")

        # Tabs futuros (deshabilitados)
        tab_combinada = QWidget()
        self.tabs.addTab(tab_combinada, "Zapata Combinada")
        self.tabs.setTabEnabled(1, False)

        tab_corrida = QWidget()
        self.tabs.addTab(tab_corrida, "Zapata Corrida")
        self.tabs.setTabEnabled(2, False)

        tab_losa = QWidget()
        self.tabs.addTab(tab_losa, "Losa de Fundación")
        self.tabs.setTabEnabled(3, False)

        self.setCentralWidget(self.tabs)

    # ------------------------------------------------------------------
    def _crear_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.lbl_status = QLabel("Listo")
        self.statusbar.addWidget(self.lbl_status)

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def _cambiar_norma(self, index):
        texto = self.combo_norma.currentText()
        self._norma_actual = NORMAS_DISPONIBLES[texto]
        self.panel_zapata_aislada.set_norma(self._norma_actual)
        self.lbl_status.setText(f"Norma: {texto}")

    def _ejecutar_calculo(self):
        tab_actual = self.tabs.currentIndex()
        if tab_actual == 0:
            self.panel_zapata_aislada.calcular()
            self.lbl_status.setText("Cálculo completado ✔")

    def _exportar_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar reporte PDF", "", "PDF (*.pdf)"
        )
        if path:
            tab_actual = self.tabs.currentIndex()
            if tab_actual == 0:
                self.panel_zapata_aislada.exportar_pdf(path)
                self.lbl_status.setText(f"PDF exportado: {path}")

    def _nuevo_proyecto(self):
        self.panel_zapata_aislada.limpiar()
        self.lbl_status.setText("Nuevo proyecto")

    def _abrir_proyecto(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir proyecto", "datos/proyectos/", "JSON (*.json)"
        )
        if path:
            datos = self.gestor.cargar(path)
            if datos:
                self.panel_zapata_aislada.cargar_datos(datos)
                self.lbl_status.setText(f"Proyecto cargado: {path}")

    def _guardar_proyecto(self):
        datos = self.panel_zapata_aislada.obtener_datos()
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar proyecto", "datos/proyectos/", "JSON (*.json)"
        )
        if path:
            self.gestor.guardar(datos, path)
            self.lbl_status.setText(f"Guardado: {path}")

    def _acerca_de(self):
        QMessageBox.about(
            self, "Acerca de FundaCalc",
            "<h3>FundaCalc v1.0</h3>"
            "<p>Aplicación para el diseño estructural de fundaciones.</p>"
            "<p>Módulo 1: Zapata Aislada</p>"
            "<p>Normas: ACI 318, CIRSOC 201, NCh 170, NSR-10, NTE E.060, NTC-CDMX, EHE-08</p>"
        )
```

---

### 6.3 `ui/panel_zapata_aislada.py`

**Ruta:** `ui/panel_zapata_aislada.py`

```python
"""
Panel de ingreso de datos y visualización de resultados para Zapata Aislada.
Layout: Izquierda = formulario de entrada | Derecha = resultados + gráfico.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox,
    QFormLayout, QLabel, QLineEdit, QDoubleSpinBox,
    QCheckBox, QSplitter, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt

from core.zapata_aislada import (
    ZapataAislada, CargasColumna, Columna, Suelo,
    MaterialHormigon, MaterialAcero, GeometriaZapata
)
from core.normas.aci318 import ACI318
from core.normas.cirsoc201 import CIRSOC201
from core.normas.nch170 import NCh170
from core.normas.nsr10 import NSR10
from core.normas.nte_e060 import NTE_E060
from core.normas.ntc_cdmx import NTC_CDMX
from core.normas.ehe08 import EHE08

from ui.panel_resultados import PanelResultados
from ui.panel_grafico import PanelGrafico
from reportes.generador_pdf import GeneradorPDF


NORMAS_MAP = {
    "ACI318": ACI318,
    "CIRSOC201": CIRSOC201,
    "NCH170": NCh170,
    "NSR10": NSR10,
    "NTE_E060": NTE_E060,
    "NTC_CDMX": NTC_CDMX,
    "EHE08": EHE08,
}


def _spinbox(min_val=0.0, max_val=9999.0, decimals=2, valor=0.0, sufijo=""):
    """Helper para crear QDoubleSpinBox con configuración estándar."""
    sb = QDoubleSpinBox()
    sb.setRange(min_val, max_val)
    sb.setDecimals(decimals)
    sb.setValue(valor)
    if sufijo:
        sb.setSuffix(f"  {sufijo}")
    return sb


class PanelZapataAislada(QWidget):

    def __init__(self, norma_codigo="ACI318"):
        super().__init__()
        self._norma_codigo = norma_codigo
        self._ultimo_resultado = None
        self._ultimo_calculo = None
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo: formulario
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(10)

        form_layout.addWidget(self._grupo_cargas())
        form_layout.addWidget(self._grupo_columna())
        form_layout.addWidget(self._grupo_suelo())
        form_layout.addWidget(self._grupo_materiales())
        form_layout.addWidget(self._grupo_geometria())
        form_layout.addStretch()

        scroll.setWidget(form_widget)
        splitter.addWidget(scroll)

        # Panel derecho: resultados + gráfico
        panel_derecho = QWidget()
        layout_der = QVBoxLayout(panel_derecho)
        self.panel_resultados = PanelResultados()
        self.panel_grafico = PanelGrafico()
        layout_der.addWidget(self.panel_grafico, stretch=2)
        layout_der.addWidget(self.panel_resultados, stretch=3)
        splitter.addWidget(panel_derecho)

        splitter.setSizes([400, 700])
        layout.addWidget(splitter)

    # ------------------------------------------------------------------
    # Grupos de formulario
    # ------------------------------------------------------------------
    def _grupo_cargas(self) -> QGroupBox:
        grp = QGroupBox("Cargas en la columna")
        form = QFormLayout(grp)

        self.sb_Pd = _spinbox(0, 50000, 1, 500.0, "kN")
        self.sb_Pl = _spinbox(0, 50000, 1, 300.0, "kN")
        self.sb_Mxd = _spinbox(0, 5000, 2, 0.0, "kN·m")
        self.sb_Mxl = _spinbox(0, 5000, 2, 0.0, "kN·m")
        self.sb_Myd = _spinbox(0, 5000, 2, 0.0, "kN·m")
        self.sb_Myl = _spinbox(0, 5000, 2, 0.0, "kN·m")

        form.addRow("Carga muerta Pd:", self.sb_Pd)
        form.addRow("Carga viva Pl:", self.sb_Pl)
        form.addRow("Momento muerto Mxd:", self.sb_Mxd)
        form.addRow("Momento vivo Mxl:", self.sb_Mxl)
        form.addRow("Momento muerto Myd:", self.sb_Myd)
        form.addRow("Momento vivo Myl:", self.sb_Myl)
        return grp

    def _grupo_columna(self) -> QGroupBox:
        grp = QGroupBox("Geometría de la columna")
        form = QFormLayout(grp)
        self.sb_col_ancho = _spinbox(0.10, 5.0, 2, 0.30, "m")
        self.sb_col_largo = _spinbox(0.10, 5.0, 2, 0.30, "m")
        form.addRow("Ancho (bx):", self.sb_col_ancho)
        form.addRow("Largo (by):", self.sb_col_largo)
        return grp

    def _grupo_suelo(self) -> QGroupBox:
        grp = QGroupBox("Parámetros del suelo")
        form = QFormLayout(grp)
        self.sb_qa = _spinbox(10, 5000, 1, 150.0, "kN/m²")
        self.sb_Df = _spinbox(0.30, 10.0, 2, 1.20, "m")
        self.sb_gamma_s = _spinbox(10, 30, 1, 18.0, "kN/m³")
        form.addRow("Capacidad admisible qa:", self.sb_qa)
        form.addRow("Profundidad de desplante Df:", self.sb_Df)
        form.addRow("Peso unitario del suelo γ:", self.sb_gamma_s)
        return grp

    def _grupo_materiales(self) -> QGroupBox:
        grp = QGroupBox("Materiales")
        form = QFormLayout(grp)
        self.sb_fck = _spinbox(15, 80, 1, 25.0, "MPa")
        self.sb_fy = _spinbox(200, 600, 1, 420.0, "MPa")
        self.sb_recub = _spinbox(0.03, 0.15, 3, 0.075, "m")
        form.addRow("Resistencia hormigón fck:", self.sb_fck)
        form.addRow("Fluencia acero fy:", self.sb_fy)
        form.addRow("Recubrimiento libre:", self.sb_recub)
        return grp

    def _grupo_geometria(self) -> QGroupBox:
        grp = QGroupBox("Geometría de la zapata (opcional)")
        form = QFormLayout(grp)
        self.cb_cuadrada = QCheckBox("Forzar zapata cuadrada")
        self.cb_cuadrada.setChecked(True)
        self.sb_h = _spinbox(0.20, 3.0, 2, 0.50, "m")
        form.addRow("", self.cb_cuadrada)
        form.addRow("Altura inicial h:", self.sb_h)
        return grp

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------
    def set_norma(self, codigo: str):
        self._norma_codigo = codigo

    def calcular(self):
        """Recopila datos del formulario, ejecuta el motor y muestra resultados."""
        cargas = CargasColumna(
            Pd=self.sb_Pd.value(),
            Pl=self.sb_Pl.value(),
            Mxd=self.sb_Mxd.value(),
            Mxl=self.sb_Mxl.value(),
            Myd=self.sb_Myd.value(),
            Myl=self.sb_Myl.value(),
        )
        columna = Columna(
            ancho=self.sb_col_ancho.value(),
            largo=self.sb_col_largo.value(),
        )
        suelo = Suelo(
            qa=self.sb_qa.value(),
            Df=self.sb_Df.value(),
            gamma_suelo=self.sb_gamma_s.value(),
        )
        hormigon = MaterialHormigon(fck=self.sb_fck.value())
        acero = MaterialAcero(fy=self.sb_fy.value())
        geometria = GeometriaZapata(
            h=self.sb_h.value(),
            recubrimiento=self.sb_recub.value(),
            cuadrada=self.cb_cuadrada.isChecked(),
        )

        norma_cls = NORMAS_MAP.get(self._norma_codigo, ACI318)
        norma = norma_cls()

        motor = ZapataAislada(cargas, columna, suelo, hormigon, acero, norma, geometria)
        resultado = motor.calcular()

        self._ultimo_resultado = resultado
        self._ultimo_calculo = {
            "cargas": cargas,
            "columna": columna,
            "suelo": suelo,
            "hormigon": hormigon,
            "acero": acero,
            "geometria": motor.geo,
            "norma": norma,
        }

        self.panel_resultados.mostrar(resultado)
        self.panel_grafico.dibujar(motor.geo, columna, resultado)

    def exportar_pdf(self, ruta: str):
        if self._ultimo_resultado and self._ultimo_calculo:
            gen = GeneradorPDF()
            gen.generar(
                ruta=ruta,
                resultado=self._ultimo_resultado,
                datos=self._ultimo_calculo,
            )

    def limpiar(self):
        """Resetea el formulario a valores por defecto."""
        self.sb_Pd.setValue(500.0)
        self.sb_Pl.setValue(300.0)
        self.panel_resultados.limpiar()

    def obtener_datos(self) -> dict:
        """Retorna dict con todos los datos del formulario para guardar en JSON."""
        return {
            "Pd": self.sb_Pd.value(),
            "Pl": self.sb_Pl.value(),
            "Mxd": self.sb_Mxd.value(),
            "Mxl": self.sb_Mxl.value(),
            "col_ancho": self.sb_col_ancho.value(),
            "col_largo": self.sb_col_largo.value(),
            "qa": self.sb_qa.value(),
            "Df": self.sb_Df.value(),
            "gamma_s": self.sb_gamma_s.value(),
            "fck": self.sb_fck.value(),
            "fy": self.sb_fy.value(),
            "recubrimiento": self.sb_recub.value(),
            "h": self.sb_h.value(),
            "cuadrada": self.cb_cuadrada.isChecked(),
            "norma": self._norma_codigo,
        }

    def cargar_datos(self, datos: dict):
        """Carga datos desde un dict (proyecto guardado)."""
        self.sb_Pd.setValue(datos.get("Pd", 500))
        self.sb_Pl.setValue(datos.get("Pl", 300))
        self.sb_Mxd.setValue(datos.get("Mxd", 0))
        self.sb_Mxl.setValue(datos.get("Mxl", 0))
        self.sb_col_ancho.setValue(datos.get("col_ancho", 0.30))
        self.sb_col_largo.setValue(datos.get("col_largo", 0.30))
        self.sb_qa.setValue(datos.get("qa", 150))
        self.sb_Df.setValue(datos.get("Df", 1.20))
        self.sb_gamma_s.setValue(datos.get("gamma_s", 18))
        self.sb_fck.setValue(datos.get("fck", 25))
        self.sb_fy.setValue(datos.get("fy", 420))
        self.sb_recub.setValue(datos.get("recubrimiento", 0.075))
        self.sb_h.setValue(datos.get("h", 0.50))
        self.cb_cuadrada.setChecked(datos.get("cuadrada", True))
```

---

### 6.4 `ui/panel_resultados.py`

**Ruta:** `ui/panel_resultados.py`

```python
"""
Panel de resultados — muestra tabla de verificaciones y armadura.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QGroupBox, QLabel, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from core.zapata_aislada import ResultadosZapata


class PanelResultados(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Resumen rápido (semáforo)
        self.grp_semaforo = QGroupBox("Estado del diseño")
        self.layout_semaforo = QHBoxLayout(self.grp_semaforo)
        self.lbl_presion = self._crear_indicador("Presión")
        self.lbl_punzonado = self._crear_indicador("Punzonado")
        self.lbl_cortante = self._crear_indicador("Cortante")
        self.lbl_desarrollo = self._crear_indicador("Desarrollo")
        for lbl in [self.lbl_presion, self.lbl_punzonado, self.lbl_cortante, self.lbl_desarrollo]:
            self.layout_semaforo.addWidget(lbl)

        # Tabla de resultados
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Parámetro", "Valor", "Unidad"])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)

        # Mensajes
        self.grp_mensajes = QGroupBox("Verificaciones")
        self.layout_msg = QVBoxLayout(self.grp_mensajes)

        layout.addWidget(self.grp_semaforo)
        layout.addWidget(self.tabla)
        layout.addWidget(self.grp_mensajes)

    def _crear_indicador(self, texto: str) -> QLabel:
        lbl = QLabel(f"⬤  {texto}\n—")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            "background: #e0e0e0; border-radius: 8px; padding: 8px; font-size: 11px;"
        )
        return lbl

    def _set_indicador(self, lbl: QLabel, texto: str, ok: bool):
        color = "#2e7d32" if ok else "#c62828"
        icono = "✔" if ok else "✘"
        lbl.setText(f"{icono}  {texto}")
        lbl.setStyleSheet(
            f"background: {color}; color: white; border-radius: 8px; "
            f"padding: 8px; font-size: 11px; font-weight: bold;"
        )

    def mostrar(self, res: ResultadosZapata):
        """Pobla la tabla con los resultados del cálculo."""
        self._set_indicador(self.lbl_presion, "Presión", res.ok_presion)
        self._set_indicador(self.lbl_punzonado, "Punzonado", res.ok_punzonado)
        self._set_indicador(self.lbl_cortante, "Cortante", res.ok_cortante)
        self._set_indicador(self.lbl_desarrollo, "Desarrollo", res.ok_desarrollo)

        filas = [
            ("DIMENSIONES", "", ""),
            ("Largo B", f"{res.B_requerido:.2f}", "m"),
            ("Ancho L", f"{res.L_requerido:.2f}", "m"),
            ("Altura h", f"{res.h_requerido:.2f}", "m"),
            ("Área", f"{res.B_requerido * res.L_requerido:.2f}", "m²"),
            ("PRESIONES", "", ""),
            ("Presión máxima", f"{res.q_max:.1f}", "kN/m²"),
            ("Presión mínima", f"{res.q_min:.1f}", "kN/m²"),
            ("Presión última", f"{res.q_ultima:.1f}", "kN/m²"),
            ("PUNZONADO", "", ""),
            ("Vu punzonado", f"{res.Vu_punz:.1f}", "kN"),
            ("φVn punzonado", f"{res.phi_Vn_punz:.1f}", "kN"),
            ("Relación Vu/φVn", f"{res.relacion_punzonado:.3f}", ""),
            ("CORTANTE", "", ""),
            ("Vu cortante", f"{res.Vu_cort:.1f}", "kN"),
            ("φVn cortante", f"{res.phi_Vn_cort:.1f}", "kN"),
            ("FLEXIÓN — EJE X", "", ""),
            ("Momento último Mu_x", f"{res.Mu_x:.2f}", "kN·m/m"),
            ("As requerido", f"{res.As_x_requerido:.2f}", "cm²/m"),
            ("As diseño", f"{res.As_x_diseno:.2f}", "cm²/m"),
            ("Varilla", res.varilla_x, ""),
            ("Separación", f"{res.separacion_x * 100:.0f}", "cm"),
            ("FLEXIÓN — EJE Y", "", ""),
            ("Momento último Mu_y", f"{res.Mu_y:.2f}", "kN·m/m"),
            ("As requerido", f"{res.As_y_requerido:.2f}", "cm²/m"),
            ("As diseño", f"{res.As_y_diseno:.2f}", "cm²/m"),
            ("Varilla", res.varilla_y, ""),
            ("Separación", f"{res.separacion_y * 100:.0f}", "cm"),
        ]

        self.tabla.setRowCount(len(filas))
        for i, (param, valor, unidad) in enumerate(filas):
            if valor == "" and unidad == "":
                # Fila de encabezado de sección
                item = QTableWidgetItem(param)
                item.setBackground(QColor("#1565C0"))
                item.setForeground(QColor("white"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                self.tabla.setItem(i, 0, item)
                self.tabla.setSpan(i, 0, 1, 3)
            else:
                self.tabla.setItem(i, 0, QTableWidgetItem(param))
                self.tabla.setItem(i, 1, QTableWidgetItem(valor))
                self.tabla.setItem(i, 2, QTableWidgetItem(unidad))

        self.tabla.resizeColumnsToContents()

        # Mensajes
        for i in reversed(range(self.layout_msg.count())):
            self.layout_msg.itemAt(i).widget().deleteLater()

        for msg in res.mensajes:
            lbl = QLabel(msg["texto"])
            color = {"ok": "#2e7d32", "error": "#c62828",
                     "advertencia": "#e65100", "info": "#1565c0"}.get(msg["tipo"], "#000")
            lbl.setStyleSheet(f"color: {color}; padding: 2px 4px;")
            self.layout_msg.addWidget(lbl)

    def limpiar(self):
        self.tabla.setRowCount(0)
        for lbl in [self.lbl_presion, self.lbl_punzonado, self.lbl_cortante, self.lbl_desarrollo]:
            lbl.setText("⬤  —\n—")
            lbl.setStyleSheet(
                "background: #e0e0e0; border-radius: 8px; padding: 8px; font-size: 11px;"
            )
```

---

### 6.5 `ui/panel_grafico.py`

**Ruta:** `ui/panel_grafico.py`

```python
"""
Visualización gráfica de la zapata usando Matplotlib embebido en PyQt6.
Muestra: planta de la zapata, columna centrada, cotas, perímetro de punzonado.
"""

import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from core.zapata_aislada import GeometriaZapata, Columna, ResultadosZapata


class PanelGrafico(QWidget):

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(280)
        self.figura = Figure(figsize=(8, 3.5), dpi=90)
        self.canvas = FigureCanvas(self.figura)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def dibujar(self, geo: GeometriaZapata, col: Columna, res: ResultadosZapata):
        """Dibuja planta y sección transversal de la zapata."""
        self.figura.clear()

        ax1 = self.figura.add_subplot(1, 2, 1)
        ax2 = self.figura.add_subplot(1, 2, 2)

        self._dibujar_planta(ax1, geo, col, res)
        self._dibujar_seccion(ax2, geo, col, res)

        self.figura.tight_layout(pad=1.5)
        self.canvas.draw()

    def _dibujar_planta(self, ax, geo, col, res):
        """Vista en planta con columna, perímetro de punzonado y armadura."""
        B, L = geo.B, geo.L
        c1, c2 = col.ancho, col.largo
        d = geo.d

        # Zapata (exterior)
        zapata = mpatches.Rectangle(
            (-B/2, -L/2), B, L,
            linewidth=2, edgecolor='#1565C0', facecolor='#BBDEFB', alpha=0.5
        )
        ax.add_patch(zapata)

        # Columna
        columna = mpatches.Rectangle(
            (-c1/2, -c2/2), c1, c2,
            linewidth=2, edgecolor='#37474F', facecolor='#90A4AE'
        )
        ax.add_patch(columna)

        # Perímetro crítico de punzonado (a d/2 de la cara)
        B_punz = c1 + d
        L_punz = c2 + d
        punzonado = mpatches.Rectangle(
            (-B_punz/2, -L_punz/2), B_punz, L_punz,
            linewidth=1.5, edgecolor='#C62828', facecolor='none',
            linestyle='--', label=f"Perímetro punzonado\n(a d/2={d*100:.0f}cm)"
        )
        ax.add_patch(punzonado)

        # Cotas
        ax.annotate('', xy=(B/2, -L/2 - 0.15), xytext=(-B/2, -L/2 - 0.15),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.5))
        ax.text(0, -L/2 - 0.25, f"B = {B:.2f} m", ha='center', fontsize=8, color='#1565C0')

        ax.annotate('', xy=(B/2 + 0.15, L/2), xytext=(B/2 + 0.15, -L/2),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.5))
        ax.text(B/2 + 0.30, 0, f"L = {L:.2f} m", ha='center', fontsize=8,
                color='#1565C0', rotation=90, va='center')

        ax.set_xlim(-B/2 - 0.5, B/2 + 0.6)
        ax.set_ylim(-L/2 - 0.45, L/2 + 0.3)
        ax.set_aspect('equal')
        ax.set_title("Vista en Planta", fontweight='bold', fontsize=10)
        ax.legend(loc='upper left', fontsize=7)
        ax.axis('off')

    def _dibujar_seccion(self, ax, geo, col, res):
        """Sección transversal mostrando altura, recubrimiento y armadura."""
        B, h = geo.B, geo.h
        recub = geo.recubrimiento
        d = geo.d
        c1 = col.ancho

        # Contorno zapata
        zapata = mpatches.Rectangle(
            (-B/2, 0), B, h,
            linewidth=2, edgecolor='#1565C0', facecolor='#BBDEFB', alpha=0.5
        )
        ax.add_patch(zapata)

        # Columna sobre zapata
        col_rect = mpatches.Rectangle(
            (-c1/2, h), c1, 0.40,
            linewidth=2, edgecolor='#37474F', facecolor='#90A4AE'
        )
        ax.add_patch(col_rect)

        # Línea de armadura inferior
        y_arm = recub + 0.008
        ax.axhline(y=y_arm, xmin=0.05, xmax=0.95, color='#C62828', linewidth=2,
                   label=f"Armadura ({res.varilla_x} @ {res.separacion_x*100:.0f}cm)")

        # Cotas de altura
        ax.annotate('', xy=(B/2 + 0.10, h), xytext=(B/2 + 0.10, 0),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.5))
        ax.text(B/2 + 0.25, h/2, f"h = {h:.2f} m", ha='left', fontsize=8,
                color='#1565C0', va='center')

        ax.annotate('', xy=(-B/2 - 0.10, y_arm), xytext=(-B/2 - 0.10, 0),
                    arrowprops=dict(arrowstyle='<->', color='#C62828', lw=1.0))
        ax.text(-B/2 - 0.35, y_arm/2, f"r={recub*100:.0f}cm", ha='center',
                fontsize=7, color='#C62828', va='center')

        ax.set_xlim(-B/2 - 0.5, B/2 + 0.5)
        ax.set_ylim(-0.2, h + 0.7)
        ax.set_aspect('equal')
        ax.set_title("Sección Transversal", fontweight='bold', fontsize=10)
        ax.legend(loc='upper right', fontsize=7)
        ax.axis('off')
```

---

## 7. Módulo Reportes — PDF

### 7.1 `reportes/generador_pdf.py`

**Ruta:** `reportes/generador_pdf.py`

```python
"""
Generador de memoria de cálculo en PDF usando ReportLab.
Produce un informe profesional con:
  - Portada con datos del proyecto
  - Resumen ejecutivo (semáforo de verificaciones)
  - Tablas de resultados
  - Esquemas de la zapata
"""

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from core.zapata_aislada import ResultadosZapata


AZUL = colors.HexColor("#1565C0")
VERDE = colors.HexColor("#2e7d32")
ROJO = colors.HexColor("#c62828")
GRIS_CLARO = colors.HexColor("#ECEFF1")


class GeneradorPDF:

    def generar(self, ruta: str, resultado: ResultadosZapata, datos: dict):
        doc = SimpleDocTemplate(
            ruta,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        estilos = getSampleStyleSheet()
        historia = []

        # ---- Portada ----
        historia += self._portada(estilos, datos)
        historia.append(PageBreak())

        # ---- Datos de entrada ----
        historia += self._datos_entrada(estilos, datos)
        historia.append(Spacer(1, 0.5*cm))

        # ---- Resultados ----
        historia += self._tabla_resultados(estilos, resultado)
        historia.append(Spacer(1, 0.5*cm))

        # ---- Verificaciones ----
        historia += self._verificaciones(estilos, resultado)

        doc.build(historia)

    # ------------------------------------------------------------------
    def _estilo_titulo(self, estilos):
        return ParagraphStyle(
            'Titulo', parent=estilos['Title'],
            fontSize=18, textColor=AZUL, spaceAfter=6,
        )

    def _portada(self, estilos, datos):
        norma = datos.get("norma")
        elementos = [
            Spacer(1, 2*cm),
            Paragraph("FundaCalc", ParagraphStyle(
                'Logo', fontSize=32, textColor=AZUL, alignment=TA_CENTER, spaceAfter=4
            )),
            Paragraph("Memoria de Cálculo — Zapata Aislada", ParagraphStyle(
                'Sub', fontSize=14, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=20
            )),
            HRFlowable(width="100%", thickness=2, color=AZUL),
            Spacer(1, 1*cm),
            Paragraph(f"Norma de diseño: <b>{norma}</b>", estilos['Normal']),
            Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilos['Normal']),
        ]
        return elementos

    def _datos_entrada(self, estilos, datos):
        cargas = datos["cargas"]
        col = datos["columna"]
        suelo = datos["suelo"]
        horm = datos["hormigon"]
        acero = datos["acero"]
        geo = datos["geometria"]
        norma = datos["norma"]

        titulo = Paragraph("1. Datos de Entrada", self._estilo_titulo(estilos))

        tabla_data = [
            ["CARGAS", "", "SUELO", ""],
            ["Pd (muerta)", f"{cargas.Pd:.1f} kN", "qa", f"{suelo.qa:.1f} kN/m²"],
            ["Pl (viva)", f"{cargas.Pl:.1f} kN", "Df", f"{suelo.Df:.2f} m"],
            ["Pu (última)", f"{cargas.Pu:.1f} kN", "γ suelo", f"{suelo.gamma_suelo:.1f} kN/m³"],
            ["COLUMNA", "", "MATERIALES", ""],
            ["Ancho (bx)", f"{col.ancho:.2f} m", "fck", f"{horm.fck:.1f} MPa"],
            ["Largo (by)", f"{col.largo:.2f} m", "fy", f"{acero.fy:.1f} MPa"],
            ["Norma", str(norma), "Recubrimiento", f"{geo.recubrimiento*100:.1f} cm"],
        ]

        tabla = Table(tabla_data, colWidths=[4*cm, 3.5*cm, 4*cm, 3.5*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 4), (-1, 4), AZUL),
            ('TEXTCOLOR', (0, 4), (-1, 4), colors.white),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, 3), GRIS_CLARO),
            ('BACKGROUND', (0, 5), (-1, -1), GRIS_CLARO),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))

        return [titulo, Spacer(1, 0.3*cm), tabla]

    def _tabla_resultados(self, estilos, res: ResultadosZapata):
        titulo = Paragraph("2. Resultados del Diseño", self._estilo_titulo(estilos))

        data = [
            ["Parámetro", "Valor", "Unidad", "Estado"],
            ["Dimensiones", "", "", ""],
            ["B (largo)", f"{res.B_requerido:.2f}", "m", ""],
            ["L (ancho)", f"{res.L_requerido:.2f}", "m", ""],
            ["h (altura)", f"{res.h_requerido:.2f}", "m", ""],
            ["Verificaciones", "", "", ""],
            ["Presión máx.", f"{res.q_max:.1f}", "kN/m²", "✔ OK" if res.ok_presion else "✘ FALLA"],
            ["Punzonado Vu/φVn", f"{res.relacion_punzonado:.3f}", "—", "✔ OK" if res.ok_punzonado else "✘ FALLA"],
            ["Cortante Vu/φVn", f"{res.relacion_cortante:.3f}", "—", "✔ OK" if res.ok_cortante else "✘ FALLA"],
            ["Armadura", "", "", ""],
            ["As diseño eje X", f"{res.As_x_diseno:.2f}", "cm²/m", f"{res.varilla_x} @ {res.separacion_x*100:.0f}cm"],
            ["As diseño eje Y", f"{res.As_y_diseno:.2f}", "cm²/m", f"{res.varilla_y} @ {res.separacion_y*100:.0f}cm"],
        ]

        tabla = Table(data, colWidths=[5*cm, 3.5*cm, 3*cm, 4*cm])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ])
        # Colorear fila de estado
        for i, fila in enumerate(data):
            if "FALLA" in str(fila[-1]):
                style.add('TEXTCOLOR', (3, i), (3, i), ROJO)
                style.add('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')
            elif "OK" in str(fila[-1]):
                style.add('TEXTCOLOR', (3, i), (3, i), VERDE)
        tabla.setStyle(style)

        return [titulo, Spacer(1, 0.3*cm), tabla]

    def _verificaciones(self, estilos, res: ResultadosZapata):
        titulo = Paragraph("3. Mensajes de Verificación", self._estilo_titulo(estilos))
        elementos = [titulo, Spacer(1, 0.2*cm)]

        for msg in res.mensajes:
            color = {
                "ok": "#2e7d32", "error": "#c62828",
                "advertencia": "#e65100", "info": "#1565c0"
            }.get(msg["tipo"], "#000000")
            p = Paragraph(
                f'<font color="{color}">{msg["texto"]}</font>',
                estilos['Normal']
            )
            elementos.append(p)
            elementos.append(Spacer(1, 0.1*cm))

        return elementos
```

---

## 8. Módulo Datos — Proyectos

### 8.1 `datos/gestor_proyectos.py`

**Ruta:** `datos/gestor_proyectos.py`

```python
"""
Guardar y cargar proyectos en formato JSON.
"""

import json
import os
from datetime import datetime


class GestorProyectos:

    def guardar(self, datos: dict, ruta: str) -> bool:
        datos["_meta"] = {
            "version": "1.0",
            "fecha": datetime.now().isoformat(),
            "app": "FundaCalc",
        }
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return True

    def cargar(self, ruta: str) -> dict | None:
        if not os.path.exists(ruta):
            return None
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
```

---

## 9. Lógica Estructural Detallada

### Proceso de diseño — Zapata Aislada (resumen)

```
┌──────────────────────────────────────────────────────────────────┐
│  ENTRADA: Pd, Pl, Mx, My, columna, suelo, materiales, norma     │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ PASO 1 — Dimensionamiento en planta                              │
│  • P_total = Pser + Pp_zapata (estimado 10%)                    │
│  • q_neta  = qa - γs·Df                                         │
│  • A_req   = P_total / q_neta                                   │
│  • B = L   = √A_req  (redondeado a 5cm superior)                │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ PASO 2 — Verificación de presiones de servicio                   │
│  • q_med = P_total / A                                           │
│  • q_max = q_med + Mx/(B·L²/6) + My/(L·B²/6)                  │
│  • Verificar: q_max ≤ qa                                         │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ PASO 3 — Verificación por punzonado (cortante bidireccional)     │
│  • d = h - recub - Ø/2                                          │
│  • b₀ = 2·(c1+d) + 2·(c2+d)                                    │
│  • A_crit = (c1+d)·(c2+d)                                       │
│  • Vu = qu·(B·L - A_crit)                                       │
│  • φVn según norma (ACI §22.6, EHE Art.46, etc.)               │
│  • Si Vu > φVn → aumentar h y repetir                           │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ PASO 4 — Verificación por cortante unidireccional                │
│  • Sección crítica a 'd' de la cara de la columna               │
│  • Vu = qu · B · (L/2 - c2/2 - d)                              │
│  • φVn según norma                                               │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ PASO 5 — Diseño a flexión                                        │
│  • Sección crítica: cara de la columna                           │
│  • Mu = qu · vol² / 2   (por metro ancho)                        │
│  • As = f(Mu, d, fck, fy)  según norma                          │
│  • As_diseno = max(As_req, As_min)                               │
│  • Selección de varilla y separación comercial                   │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ PASO 6 — Verificación de longitud de desarrollo                  │
│  • ld_disponible = B/2 - c1/2 - recub                          │
│  • ld_requerido según norma (función de db, fck, fy)            │
│  • Si ld_disp < ld_req → usar ganchos estándar                  │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  SALIDA: ResultadosZapata + Gráfico + Memoria PDF                │
└──────────────────────────────────────────────────────────────────┘
```

### Tabla de varillas comerciales métricas

| Designación | Ø nominal (mm) | Área (cm²) | Peso (kg/m) |
|---|---|---|---|
| Ø8  | 8  | 0.503 | 0.395 |
| Ø10 | 10 | 0.785 | 0.617 |
| Ø12 | 12 | 1.131 | 0.888 |
| Ø16 | 16 | 2.011 | 1.578 |
| Ø20 | 20 | 3.142 | 2.466 |
| Ø25 | 25 | 4.909 | 3.853 |
| Ø32 | 32 | 8.042 | 6.313 |

---

## 10. Roadmap — Módulos Futuros

### Módulo 2: Zapata Combinada
- Dos columnas con cargas distintas
- Dimensionamiento para resultante centrada
- Distribución trapezoidal de presiones
- Verificación de viga longitudinal

### Módulo 3: Zapata Corrida
- Bajo muros portantes
- Carga lineal [kN/m]
- Verificación por metro lineal

### Módulo 4: Losa de Fundación
- Método de coeficientes ACI
- Análisis elástico simplificado (módulo de balasto)
- Armado en dos capas ortogonales

### Funcionalidades transversales pendientes
- [ ] Verificación sísmica (ampliación de zapata)
- [ ] Exportación a DXF (AutoCAD)
- [ ] Visualización 3D con PyVista
- [ ] Base de datos de suelos (Terzaghi, Meyerhof)
- [ ] Múltiples combinaciones de carga simultáneas
- [ ] Informe comparativo entre normas

---

## 11. Pruebas y Validación

### `tests/test_zapata_aislada.py`

```python
"""
Pruebas unitarias del motor de cálculo.
Ejecutar con: python -m pytest tests/ -v
"""

import pytest
from core.zapata_aislada import (
    ZapataAislada, CargasColumna, Columna, Suelo,
    MaterialHormigon, MaterialAcero, GeometriaZapata
)
from core.normas.aci318 import ACI318
from core.normas.cirsoc201 import CIRSOC201
from core.normas.ehe08 import EHE08


@pytest.fixture
def caso_base():
    """Caso de referencia para todos los tests."""
    return {
        "cargas": CargasColumna(Pd=500, Pl=300),
        "columna": Columna(ancho=0.30, largo=0.30),
        "suelo": Suelo(qa=150, Df=1.20, gamma_suelo=18.0),
        "hormigon": MaterialHormigon(fck=25.0),
        "acero": MaterialAcero(fy=420.0),
        "geometria": GeometriaZapata(h=0.50, cuadrada=True),
    }


class TestDimensionamiento:

    def test_area_requerida_positiva(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.area_requerida > 0

    def test_zapata_cuadrada(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert abs(res.B_requerido - res.L_requerido) < 0.01

    def test_presion_no_supera_admisible(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.q_max <= caso_base["suelo"].qa * 1.05  # tolerancia 5%


class TestVerificaciones:

    def test_punzonado_ok(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.ok_punzonado

    def test_cortante_ok(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.ok_cortante


class TestNormas:

    def test_aci_vs_cirsoc_resultados_similares(self, caso_base):
        """CIRSOC tiene factores distintos pero resultados del mismo orden."""
        res_aci = ZapataAislada(**caso_base, norma=ACI318()).calcular()
        res_cirsoc = ZapataAislada(**caso_base, norma=CIRSOC201()).calcular()
        # El área no debe diferir más del 30%
        ratio = res_aci.area_requerida / res_cirsoc.area_requerida
        assert 0.70 <= ratio <= 1.30

    def test_ehe08_calcula_sin_error(self, caso_base):
        """EHE-08 (distinto sistema) no debe generar excepciones."""
        motor = ZapataAislada(**caso_base, norma=EHE08())
        res = motor.calcular()
        assert res.B_requerido > 0


class TestArmadura:

    def test_as_diseno_mayor_que_minimo(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.As_x_diseno >= res.As_x_minimo
        assert res.As_y_diseno >= res.As_y_minimo

    def test_separacion_en_rango(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert 0.10 <= res.separacion_x <= 0.35
        assert 0.10 <= res.separacion_y <= 0.35
```

---

## Instrucciones finales para VS Code

### Orden de creación de archivos

1. Crear estructura de carpetas completa
2. Crear todos los `__init__.py` vacíos
3. Copiar en este orden:
   - `core/normas/base.py`
   - `core/normas/aci318.py`
   - `core/normas/cirsoc201.py` (y el resto de normas)
   - `core/zapata_aislada.py`
   - `datos/gestor_proyectos.py`
   - `ui/panel_resultados.py`
   - `ui/panel_grafico.py`
   - `ui/panel_zapata_aislada.py`
   - `ui/ventana_principal.py`
   - `reportes/generador_pdf.py`
   - `main.py`

### Ejecutar la aplicación

```bash
# Activar entorno virtual
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# Ejecutar
python main.py

# O desde VS Code: F5 (con launch.json configurado)
```

### Ejecutar pruebas

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## 12. Módulo Detallado de Acero

Este módulo permite al usuario:
1. Ver el **área de acero requerida** (ej: 32 cm²)
2. **Seleccionar interactivamente el diámetro de varilla** (Ø8 a Ø32)
3. Obtener automáticamente: cantidad de barras, separación real, longitudes de corte, dowels de columna
4. Ver el **gráfico actualizado** con las barras dibujadas en planta y sección
5. Exportar a **PDF** y **DXF (AutoCAD/LibreCAD)**

---

### 12.1 `core/detallado_acero.py` — Motor de detallado

**Ruta:** `core/detallado_acero.py`

```python
"""
Motor de detallado de acero para zapata aislada.

Dado el área de acero requerida (As en cm²) y la varilla seleccionada,
calcula el detallado completo:
  - Cantidad de barras en cada dirección
  - Separación real entre barras
  - Longitud de cada barra (con gancho si corresponde)
  - Barras de arranque (dowels) columna-zapata
  - Tabla de acero: resumen tipo plano estructural
  - Peso total de acero [kg]
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import math


# ---------------------------------------------------------------------------
# Tabla maestra de varillas comerciales
# ---------------------------------------------------------------------------

VARILLAS = {
    # código: (diámetro_mm, área_cm2, peso_kg_m, nombre_display)
    "Ø8":  (8,   0.503, 0.395, "Ø8mm  (1/4\")"),
    "Ø10": (10,  0.785, 0.617, "Ø10mm (3/8\")"),
    "Ø12": (12,  1.131, 0.888, "Ø12mm (1/2\")"),
    "Ø16": (16,  2.011, 1.578, "Ø16mm (5/8\")"),
    "Ø20": (20,  3.142, 2.466, "Ø20mm (3/4\")"),
    "Ø25": (25,  4.909, 3.853, "Ø25mm (1\")"),
    "Ø32": (32,  8.042, 6.313, "Ø32mm (1-1/4\")"),
}

# Varillas imperiales (pulgadas — para referencia NSR-10, NTE E.060)
VARILLAS_IMPERIAL = {
    "#3":  (9.5,  0.713, 0.560, "#3  (3/8\")"),
    "#4":  (12.7, 1.267, 0.994, "#4  (1/2\")"),
    "#5":  (15.9, 1.979, 1.552, "#5  (5/8\")"),
    "#6":  (19.1, 2.850, 2.235, "#6  (3/4\")"),
    "#7":  (22.2, 3.871, 3.042, "#7  (7/8\")"),
    "#8":  (25.4, 5.067, 3.973, "#8  (1\")"),
    "#9":  (28.7, 6.452, 5.060, "#9  (1-1/8\")"),
    "#10": (32.3, 8.194, 6.404, "#10 (1-1/4\")"),
}


def get_todas_varillas() -> dict:
    """Retorna el catálogo completo métrico + imperial."""
    return {**VARILLAS, **VARILLAS_IMPERIAL}


# ---------------------------------------------------------------------------
# Dataclasses de entrada y salida
# ---------------------------------------------------------------------------

@dataclass
class SolicitudDetallado:
    """
    Datos necesarios para generar el detallado de armadura.
    Proviene de los resultados del motor ZapataAislada.
    """
    # Geometría de la zapata
    B: float              # Dimensión X [m]
    L: float              # Dimensión Y [m]
    h: float              # Altura total [m]
    recubrimiento: float  # Recubrimiento libre [m]

    # Columna
    col_bx: float         # Ancho columna eje X [m]
    col_by: float         # Largo columna eje Y [m]

    # Área de acero requerida (resultado del motor)
    As_x_requerido: float  # [cm²] — total en dirección X (= As_cm2/m × L)
    As_y_requerido: float  # [cm²] — total en dirección Y (= As_cm2/m × B)

    # Varillas seleccionadas por el usuario
    codigo_varilla_x: str = "Ø16"
    codigo_varilla_y: str = "Ø16"
    codigo_varilla_dowel: str = "Ø16"  # barras de arranque columna

    # Norma (afecta ganchos y empalmes)
    norma_codigo: str = "ACI318"

    # Longitud de desarrollo requerida (del motor)
    ld_requerido: float = 0.40  # [m]


@dataclass
class DetalleBarras:
    """Resultado del detallado para una dirección."""
    direccion: str            # "X" o "Y"
    codigo_varilla: str
    diametro_mm: float
    area_barra_cm2: float
    peso_kg_m: float

    cantidad_barras: int = 0
    separacion_real_mm: float = 0.0   # separación real entre ejes [mm]
    longitud_barra_m: float = 0.0     # longitud de corte de cada barra [m]
    longitud_con_gancho_m: float = 0.0
    requiere_gancho: bool = False
    tipo_gancho: str = ""             # "90°" o "180°"
    extension_gancho_mm: float = 0.0

    as_provisto_cm2: float = 0.0      # As total provisto
    peso_total_kg: float = 0.0        # peso del acero en esta dirección
    longitud_total_m: float = 0.0     # metros lineales totales de barra


@dataclass
class DetalleDownels:
    """Barras de arranque (dowels) de la columna a la zapata."""
    codigo_varilla: str
    diametro_mm: float
    area_barra_cm2: float
    peso_kg_m: float

    cantidad: int = 0
    longitud_en_zapata_m: float = 0.0    # ld dentro de la zapata
    longitud_en_columna_m: float = 0.40  # empalme estándar
    longitud_total_barra_m: float = 0.0
    peso_total_kg: float = 0.0
    disposicion: str = ""                # "4 esquinas", "perimetral", etc.


@dataclass
class ResultadoDetallado:
    """Resultado completo del detallado de acero."""
    detalle_x: DetalleBarras = None
    detalle_y: DetalleBarras = None
    dowels: DetalleDownels = None

    # Resumen global
    peso_total_acero_kg: float = 0.0
    volumen_hormigon_m3: float = 0.0
    mensajes: list = field(default_factory=list)

    # Tabla de acero (tipo plano estructural)
    tabla_acero: list = field(default_factory=list)
    # Formato: [{"marca","varilla","cantidad","long_m","long_total_m","peso_kg"}]

    def agregar_mensaje(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"tipo": tipo, "texto": texto})


# ---------------------------------------------------------------------------
# Motor de detallado
# ---------------------------------------------------------------------------

class DetalladoAcero:
    """
    Genera el detallado completo de armadura de la zapata aislada.

    Uso:
        solicitud = SolicitudDetallado(...)
        motor = DetalladoAcero(solicitud)
        resultado = motor.calcular()
    """

    def __init__(self, solicitud: SolicitudDetallado):
        self.s = solicitud
        self.resultado = ResultadoDetallado()
        self._catalogo = get_todas_varillas()

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------
    def calcular(self) -> ResultadoDetallado:
        res = self.resultado
        s = self.s

        res.detalle_x = self._detallar_direccion(
            direccion="X",
            As_total_cm2=s.As_x_requerido,
            longitud_zapata=s.L,       # barras van en dirección Y, cubren L
            ancho_zapata=s.B,          # longitud de cada barra = B
            codigo_varilla=s.codigo_varilla_x,
        )

        res.detalle_y = self._detallar_direccion(
            direccion="Y",
            As_total_cm2=s.As_y_requerido,
            longitud_zapata=s.B,       # barras van en dirección X, cubren B
            ancho_zapata=s.L,          # longitud de cada barra = L
            codigo_varilla=s.codigo_varilla_y,
        )

        res.dowels = self._detallar_dowels()

        # Peso total
        res.peso_total_acero_kg = (
            res.detalle_x.peso_total_kg +
            res.detalle_y.peso_total_kg +
            res.dowels.peso_total_kg
        )

        # Volumen de hormigón
        res.volumen_hormigon_m3 = s.B * s.L * s.h

        # Tabla de acero tipo plano
        res.tabla_acero = self._generar_tabla()

        return res

    # ------------------------------------------------------------------
    # Detallado de una dirección
    # ------------------------------------------------------------------
    def _detallar_direccion(
        self,
        direccion: str,
        As_total_cm2: float,
        longitud_zapata: float,   # dimensión perpendicular a las barras
        ancho_zapata: float,      # longitud de cada barra
        codigo_varilla: str,
    ) -> DetalleBarras:
        """
        Calcula cantidad de barras, separación, longitud y gancho.

        Args:
            As_total_cm2: Área total requerida en cm² (no por metro).
            longitud_zapata: Dimensión en la que se distribuyen las barras [m].
            ancho_zapata: Longitud de cada barra [m].
        """
        s = self.s
        if codigo_varilla not in self._catalogo:
            codigo_varilla = "Ø16"

        db_mm, area_cm2, peso_kg_m, nombre = self._catalogo[codigo_varilla]
        db_m = db_mm / 1000

        # Cantidad de barras necesaria (redondeado arriba)
        n_barras = math.ceil(As_total_cm2 / area_cm2)
        n_barras = max(n_barras, 3)  # mínimo 3 barras por dirección

        # Espacio disponible para distribuir (descontando recubrimiento en extremos)
        espacio = longitud_zapata - 2 * s.recubrimiento
        sep_real_m = espacio / (n_barras - 1) if n_barras > 1 else espacio
        sep_real_mm = sep_real_m * 1000

        # Verificar separación máxima (ACI: 3h o 450mm)
        sep_max_mm = min(3 * s.h * 1000, 450)
        if sep_real_mm > sep_max_mm:
            n_barras = math.ceil(espacio / (sep_max_mm / 1000)) + 1
            sep_real_m = espacio / (n_barras - 1)
            sep_real_mm = sep_real_m * 1000

        # Separación mínima (ACI: max(db, 25mm, 4/3·dg))
        sep_min_mm = max(db_mm, 25.0)
        if sep_real_mm < sep_min_mm:
            self.resultado.agregar_mensaje(
                f"⚠ Dir {direccion}: Separación {sep_real_mm:.0f}mm < mínimo {sep_min_mm:.0f}mm. "
                f"Considerar varilla de menor diámetro.", "advertencia"
            )

        # As provisto
        as_provisto = n_barras * area_cm2
        self.resultado.agregar_mensaje(
            f"✔ Dir {direccion}: {n_barras} barras {codigo_varilla} → "
            f"As={as_provisto:.2f}cm² ≥ As_req={As_total_cm2:.2f}cm²", "ok"
        )

        # Longitud de barra y gancho
        long_recta_m = ancho_zapata - 2 * s.recubrimiento
        requiere_gancho, tipo_gancho, ext_gancho_mm = self._verificar_gancho(
            long_recta_m, db_mm
        )

        if requiere_gancho:
            long_con_gancho = long_recta_m + 2 * (ext_gancho_mm / 1000)
            self.resultado.agregar_mensaje(
                f"ℹ Dir {direccion}: Gancho {tipo_gancho} requerido. "
                f"Extensión: {ext_gancho_mm:.0f}mm c/extremo", "info"
            )
        else:
            long_con_gancho = long_recta_m

        # Longitud total y peso
        long_total_m = n_barras * long_con_gancho
        peso_total_kg = long_total_m * peso_kg_m

        return DetalleBarras(
            direccion=direccion,
            codigo_varilla=codigo_varilla,
            diametro_mm=db_mm,
            area_barra_cm2=area_cm2,
            peso_kg_m=peso_kg_m,
            cantidad_barras=n_barras,
            separacion_real_mm=sep_real_mm,
            longitud_barra_m=round(long_recta_m, 3),
            longitud_con_gancho_m=round(long_con_gancho, 3),
            requiere_gancho=requiere_gancho,
            tipo_gancho=tipo_gancho,
            extension_gancho_mm=ext_gancho_mm,
            as_provisto_cm2=round(as_provisto, 2),
            peso_total_kg=round(peso_total_kg, 2),
            longitud_total_m=round(long_total_m, 2),
        )

    # ------------------------------------------------------------------
    # Dowels (barras de arranque columna → zapata)
    # ------------------------------------------------------------------
    def _detallar_dowels(self) -> DetalleDownels:
        """
        Barras de arranque que conectan la columna con la zapata.
        Mínimo: 4 barras en esquinas. Se recomienda mismo diámetro que
        el refuerzo de la columna.
        """
        s = self.s
        codigo = s.codigo_varilla_dowel
        if codigo not in self._catalogo:
            codigo = "Ø16"

        db_mm, area_cm2, peso_kg_m, nombre = self._catalogo[codigo]

        # Cantidad mínima: 4 barras (una por esquina de la columna)
        # Área mínima dowels = 0.005 × Ag columna (ACI §16.3.4.1)
        Ag_col = s.col_bx * s.col_by * 10000  # cm²
        As_min_dowel = 0.005 * Ag_col
        n_dowels = max(4, math.ceil(As_min_dowel / area_cm2))
        # Redondear a múltiplo de 4 (simetría)
        n_dowels = math.ceil(n_dowels / 4) * 4

        disposicion = f"{n_dowels} barras" + (
            " (4 en esquinas)" if n_dowels == 4 else " (perimetral)"
        )

        # Longitud dentro de la zapata: ld requerido
        ld_zapata = max(s.ld_requerido, 0.30)
        # Verificar que no supere h - recub
        d_util = s.h - s.recubrimiento - db_mm / 1000
        if ld_zapata > d_util:
            ld_zapata = d_util
            self.resultado.agregar_mensaje(
                f"⚠ Dowels: ld reducido a {ld_zapata*100:.0f}cm por altura de zapata. "
                f"Revisar empalme.", "advertencia"
            )

        # Longitud en columna: empalme por traslapo estándar (1.3 ld)
        ld_columna = 1.3 * s.ld_requerido
        long_total_barra = ld_zapata + ld_columna
        long_total_m = n_dowels * long_total_barra
        peso_total_kg = long_total_m * peso_kg_m

        self.resultado.agregar_mensaje(
            f"✔ Dowels: {n_dowels}×{codigo} — ld_zapata={ld_zapata*100:.0f}cm, "
            f"empalme_col={ld_columna*100:.0f}cm", "ok"
        )

        return DetalleDownels(
            codigo_varilla=codigo,
            diametro_mm=db_mm,
            area_barra_cm2=area_cm2,
            peso_kg_m=peso_kg_m,
            cantidad=n_dowels,
            longitud_en_zapata_m=round(ld_zapata, 3),
            longitud_en_columna_m=round(ld_columna, 3),
            longitud_total_barra_m=round(long_total_barra, 3),
            peso_total_kg=round(peso_total_kg, 2),
            disposicion=disposicion,
        )

    # ------------------------------------------------------------------
    # Gancho estándar
    # ------------------------------------------------------------------
    def _verificar_gancho(
        self, ld_disponible: float, db_mm: float
    ) -> tuple[bool, str, float]:
        """
        Determina si se requiere gancho y de qué tipo.

        Returns:
            (requiere_gancho, tipo, extension_mm_por_extremo)
        """
        s = self.s
        # Si hay espacio suficiente → barra recta
        if ld_disponible >= s.ld_requerido:
            return False, "", 0.0

        # Gancho 90°: extensión = 12·db (ACI §25.3.2)
        ext_90 = 12 * db_mm
        # Gancho 180°: extensión = max(4·db, 65mm)
        ext_180 = max(4 * db_mm, 65)

        # Preferir gancho 90° (más fácil de ejecutar)
        return True, "90°", ext_90

    # ------------------------------------------------------------------
    # Tabla de acero tipo plano estructural
    # ------------------------------------------------------------------
    def _generar_tabla(self) -> list:
        """
        Genera lista de items para la tabla de acero.
        Formato compatible con plano estructural y reporte PDF.
        """
        s = self.s
        res = self.resultado
        tabla = []
        marca = 1

        def fila(marca, det, cantidad, long_m, descripcion):
            long_total = round(cantidad * long_m, 2)
            _, _, peso_kg_m, _ = self._catalogo[det.codigo_varilla]
            peso = round(long_total * peso_kg_m, 2)
            return {
                "marca": str(marca),
                "varilla": det.codigo_varilla,
                "descripcion": descripcion,
                "cantidad": cantidad,
                "longitud_m": round(long_m, 3),
                "longitud_total_m": long_total,
                "peso_kg": peso,
            }

        # Armadura inferior dirección X
        dx = res.detalle_x
        desc_x = (
            f"Armadura inf. Dir-X — {dx.cantidad_barras}×{dx.codigo_varilla} "
            f"sep={dx.separacion_real_mm:.0f}mm"
            + (f" + gancho {dx.tipo_gancho}" if dx.requiere_gancho else "")
        )
        tabla.append(fila(marca, dx, dx.cantidad_barras,
                          dx.longitud_con_gancho_m, desc_x))
        marca += 1

        # Armadura inferior dirección Y
        dy = res.detalle_y
        desc_y = (
            f"Armadura inf. Dir-Y — {dy.cantidad_barras}×{dy.codigo_varilla} "
            f"sep={dy.separacion_real_mm:.0f}mm"
            + (f" + gancho {dy.tipo_gancho}" if dy.requiere_gancho else "")
        )
        tabla.append(fila(marca, dy, dy.cantidad_barras,
                          dy.longitud_con_gancho_m, desc_y))
        marca += 1

        # Dowels
        dw = res.dowels
        _, _, peso_dw, _ = self._catalogo[dw.codigo_varilla]
        tabla.append({
            "marca": str(marca),
            "varilla": dw.codigo_varilla,
            "descripcion": f"Dowels columna-zapata — {dw.disposicion}",
            "cantidad": dw.cantidad,
            "longitud_m": dw.longitud_total_barra_m,
            "longitud_total_m": round(dw.cantidad * dw.longitud_total_barra_m, 2),
            "peso_kg": dw.peso_total_kg,
        })

        return tabla
```

---

### 12.2 `ui/panel_detallado.py` — Selector interactivo de varilla

**Ruta:** `ui/panel_detallado.py`

Este panel se agrega como pestaña adicional dentro del `PanelZapataAislada`.  
Permite seleccionar la varilla y ver el detallado en tiempo real.

```python
"""
Panel interactivo de detallado de acero.
El usuario selecciona el diámetro de varilla y ve el detallado actualizado.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFormLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QSplitter,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from core.detallado_acero import (
    DetalladoAcero, SolicitudDetallado, ResultadoDetallado,
    VARILLAS, VARILLAS_IMPERIAL
)
from core.zapata_aislada import ResultadosZapata, GeometriaZapata, Columna
from ui.panel_grafico_armado import PanelGraficoArmado


class PanelDetallado(QWidget):
    """
    Panel que muestra el detallado de acero con selector de varilla.
    Requiere que se haya ejecutado el cálculo previo.
    """

    def __init__(self):
        super().__init__()
        self._resultado_zapata: ResultadosZapata = None
        self._geo: GeometriaZapata = None
        self._col: Columna = None
        self._resultado_detallado: ResultadoDetallado = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Banner informativo
        self.lbl_info = QLabel(
            "⚠ Ejecute primero el cálculo de la zapata para habilitar el detallado."
        )
        self.lbl_info.setStyleSheet(
            "background: #FFF9C4; color: #F57F17; padding: 8px; "
            "border-radius: 4px; font-weight: bold;"
        )
        layout.addWidget(self.lbl_info)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---- Panel izquierdo: selección de varillas ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        left = QWidget()
        left_layout = QVBoxLayout(left)

        left_layout.addWidget(self._grupo_resumen_requerido())
        left_layout.addWidget(self._grupo_seleccion_varillas())
        left_layout.addWidget(self._grupo_tabla_acero())
        left_layout.addWidget(self._grupo_resumen_pesos())
        left_layout.addStretch()

        scroll.setWidget(left)
        splitter.addWidget(scroll)

        # ---- Panel derecho: gráfico con armado ----
        self.grafico_armado = PanelGraficoArmado()
        splitter.addWidget(self.grafico_armado)
        splitter.setSizes([480, 620])

        layout.addWidget(splitter)

    # ------------------------------------------------------------------
    def _grupo_resumen_requerido(self) -> QGroupBox:
        grp = QGroupBox("Área de acero requerida (del cálculo)")
        form = QFormLayout(grp)
        self.lbl_as_x = QLabel("—")
        self.lbl_as_y = QLabel("—")
        self.lbl_dim = QLabel("—")
        form.addRow("As requerido Dir-X:", self.lbl_as_x)
        form.addRow("As requerido Dir-Y:", self.lbl_as_y)
        form.addRow("Dimensiones B × L × h:", self.lbl_dim)
        return grp

    def _grupo_seleccion_varillas(self) -> QGroupBox:
        grp = QGroupBox("Selección de varilla")
        form = QFormLayout(grp)

        # Combinar catálogos métrico e imperial
        opciones_metricas = [f"{k}  —  {v[3]}" for k, v in VARILLAS.items()]
        opciones_imperial = [f"{k}  —  {v[3]}" for k, v in VARILLAS_IMPERIAL.items()]
        todas = opciones_metricas + ["── Imperial ──"] + opciones_imperial

        self.combo_var_x = QComboBox()
        self.combo_var_x.addItems(todas)
        self.combo_var_x.setCurrentIndex(3)  # Ø16 por defecto

        self.combo_var_y = QComboBox()
        self.combo_var_y.addItems(todas)
        self.combo_var_y.setCurrentIndex(3)

        self.combo_dowel = QComboBox()
        self.combo_dowel.addItems(todas)
        self.combo_dowel.setCurrentIndex(3)

        # Labels de feedback inmediato
        self.lbl_calc_x = QLabel("—")
        self.lbl_calc_y = QLabel("—")
        self.lbl_calc_dowel = QLabel("—")

        for lbl in [self.lbl_calc_x, self.lbl_calc_y, self.lbl_calc_dowel]:
            lbl.setStyleSheet("color: #1565C0; font-size: 10px;")

        self.combo_var_x.currentIndexChanged.connect(self._actualizar)
        self.combo_var_y.currentIndexChanged.connect(self._actualizar)
        self.combo_dowel.currentIndexChanged.connect(self._actualizar)

        form.addRow("Varilla Dir-X:", self.combo_var_x)
        form.addRow("", self.lbl_calc_x)
        form.addRow("Varilla Dir-Y:", self.combo_var_y)
        form.addRow("", self.lbl_calc_y)
        form.addRow("Varilla Dowels:", self.combo_dowel)
        form.addRow("", self.lbl_calc_dowel)

        btn = QPushButton("🔄  Actualizar Detallado")
        btn.setObjectName("btn_calcular_primary")
        btn.clicked.connect(self._actualizar)
        form.addRow("", btn)

        return grp

    def _grupo_tabla_acero(self) -> QGroupBox:
        grp = QGroupBox("Tabla de Acero — tipo plano estructural")
        layout = QVBoxLayout(grp)

        self.tabla_acero = QTableWidget()
        self.tabla_acero.setColumnCount(6)
        self.tabla_acero.setHorizontalHeaderLabels([
            "Marca", "Varilla", "Descripción", "Cant.", "Long.(m)", "Peso(kg)"
        ])
        self.tabla_acero.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_acero.setAlternatingRowColors(True)
        self.tabla_acero.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla_acero)
        return grp

    def _grupo_resumen_pesos(self) -> QGroupBox:
        grp = QGroupBox("Resumen de materiales")
        form = QFormLayout(grp)
        self.lbl_peso_acero = QLabel("—")
        self.lbl_vol_horm = QLabel("—")
        self.lbl_peso_acero.setStyleSheet("font-weight: bold; color: #1565C0; font-size: 13px;")
        self.lbl_vol_horm.setStyleSheet("font-weight: bold; color: #2e7d32; font-size: 13px;")
        form.addRow("Peso total acero:", self.lbl_peso_acero)
        form.addRow("Volumen hormigón:", self.lbl_vol_horm)
        return grp

    # ------------------------------------------------------------------
    # Interfaz pública
    # ------------------------------------------------------------------
    def cargar_resultados(
        self,
        resultado: ResultadosZapata,
        geo: GeometriaZapata,
        col: Columna,
    ):
        """Llamado desde PanelZapataAislada tras el cálculo."""
        self._resultado_zapata = resultado
        self._geo = geo
        self._col = col

        self.lbl_info.setText("✔ Seleccione las varillas y presione 'Actualizar Detallado'.")
        self.lbl_info.setStyleSheet(
            "background: #E8F5E9; color: #2e7d32; padding: 8px; "
            "border-radius: 4px; font-weight: bold;"
        )

        self.lbl_as_x.setText(f"{resultado.As_x_diseno * geo.L:.2f} cm²  "
                               f"(= {resultado.As_x_diseno:.2f} cm²/m × {geo.L:.2f}m)")
        self.lbl_as_y.setText(f"{resultado.As_y_diseno * geo.B:.2f} cm²  "
                               f"(= {resultado.As_y_diseno:.2f} cm²/m × {geo.B:.2f}m)")
        self.lbl_dim.setText(f"{geo.B:.2f} × {geo.L:.2f} × {geo.h:.2f} m")

        self._actualizar()

    def _codigo_de_combo(self, combo: QComboBox) -> str:
        """Extrae el código de varilla del texto del combo."""
        texto = combo.currentText().strip()
        if "──" in texto:
            return "Ø16"
        codigo = texto.split(" ")[0]
        return codigo if codigo else "Ø16"

    def _actualizar(self):
        """Recalcula el detallado con la varilla seleccionada."""
        if self._resultado_zapata is None:
            return

        res = self._resultado_zapata
        geo = self._geo
        col = self._col

        # As total (no por metro) = As_cm2/m × dimensión
        As_x_total = res.As_x_diseno * geo.L
        As_y_total = res.As_y_diseno * geo.B

        solicitud = SolicitudDetallado(
            B=geo.B,
            L=geo.L,
            h=geo.h,
            recubrimiento=geo.recubrimiento,
            col_bx=col.ancho,
            col_by=col.largo,
            As_x_requerido=As_x_total,
            As_y_requerido=As_y_total,
            codigo_varilla_x=self._codigo_de_combo(self.combo_var_x),
            codigo_varilla_y=self._codigo_de_combo(self.combo_var_y),
            codigo_varilla_dowel=self._codigo_de_combo(self.combo_dowel),
            ld_requerido=res.ld_requerido,
        )

        motor = DetalladoAcero(solicitud)
        resultado = motor.calcular()
        self._resultado_detallado = resultado

        # Actualizar labels de feedback
        dx = resultado.detalle_x
        dy = resultado.detalle_y
        dw = resultado.dowels

        self.lbl_calc_x.setText(
            f"→ {dx.cantidad_barras} barras × {dx.codigo_varilla}  |  "
            f"sep = {dx.separacion_real_mm:.0f} mm  |  "
            f"long = {dx.longitud_con_gancho_m:.2f} m"
            + (f"  + gancho {dx.tipo_gancho}" if dx.requiere_gancho else "")
        )
        self.lbl_calc_y.setText(
            f"→ {dy.cantidad_barras} barras × {dy.codigo_varilla}  |  "
            f"sep = {dy.separacion_real_mm:.0f} mm  |  "
            f"long = {dy.longitud_con_gancho_m:.2f} m"
            + (f"  + gancho {dy.tipo_gancho}" if dy.requiere_gancho else "")
        )
        self.lbl_calc_dowel.setText(
            f"→ {dw.cantidad} barras × {dw.codigo_varilla}  |  "
            f"ld_zapata = {dw.longitud_en_zapata_m*100:.0f} cm  |  "
            f"empalme = {dw.longitud_en_columna_m*100:.0f} cm"
        )

        # Poblar tabla de acero
        self._poblar_tabla(resultado.tabla_acero)

        # Actualizar resumen
        self.lbl_peso_acero.setText(f"{resultado.peso_total_acero_kg:.1f} kg")
        self.lbl_vol_horm.setText(f"{resultado.volumen_hormigon_m3:.3f} m³")

        # Actualizar gráfico con barras reales
        self.grafico_armado.dibujar_armado(geo, col, resultado)

    def _poblar_tabla(self, tabla: list):
        self.tabla_acero.setRowCount(len(tabla) + 1)  # +1 para totales
        peso_total = 0.0
        long_total_total = 0.0

        for i, item in enumerate(tabla):
            self.tabla_acero.setItem(i, 0, QTableWidgetItem(item["marca"]))
            self.tabla_acero.setItem(i, 1, QTableWidgetItem(item["varilla"]))
            self.tabla_acero.setItem(i, 2, QTableWidgetItem(item["descripcion"]))
            self.tabla_acero.setItem(i, 3, QTableWidgetItem(str(item["cantidad"])))
            self.tabla_acero.setItem(i, 4, QTableWidgetItem(f"{item['longitud_m']:.3f}"))
            self.tabla_acero.setItem(i, 5, QTableWidgetItem(f"{item['peso_kg']:.2f}"))
            peso_total += item["peso_kg"]

        # Fila de total
        fila_total = len(tabla)
        total_item = QTableWidgetItem("TOTAL")
        total_item.setBackground(QColor("#1565C0"))
        total_item.setForeground(QColor("white"))
        font = QFont()
        font.setBold(True)
        total_item.setFont(font)
        self.tabla_acero.setItem(fila_total, 0, total_item)
        self.tabla_acero.setSpan(fila_total, 0, 1, 4)
        peso_item = QTableWidgetItem(f"{peso_total:.2f} kg")
        peso_item.setBackground(QColor("#1565C0"))
        peso_item.setForeground(QColor("white"))
        peso_item.setFont(font)
        self.tabla_acero.setItem(fila_total, 5, peso_item)
        self.tabla_acero.resizeColumnsToContents()

    def obtener_detallado(self) -> ResultadoDetallado:
        return self._resultado_detallado
```

---

### 12.3 `ui/panel_grafico_armado.py` — Gráfico con barras reales

**Ruta:** `ui/panel_grafico_armado.py`

```python
"""
Visualización del armado real de la zapata:
  - Vista en PLANTA: grilla de barras en X e Y, columna, dowels
  - Sección TRANSVERSAL: barras inferiores, recubrimiento, dowels
Escala real proporcional. Todas las barras dibujadas individualmente.
"""

import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from core.detallado_acero import ResultadoDetallado
from core.zapata_aislada import GeometriaZapata, Columna


class PanelGraficoArmado(QWidget):

    def __init__(self):
        super().__init__()
        self.figura = Figure(figsize=(9, 7), dpi=90)
        self.canvas = FigureCanvas(self.figura)

        # Botones de vista
        btn_planta = QPushButton("Vista Planta")
        btn_seccion = QPushButton("Vista Sección")
        btn_ambas = QPushButton("Ambas vistas")
        btn_planta.clicked.connect(lambda: self._set_vista("planta"))
        btn_seccion.clicked.connect(lambda: self._set_vista("seccion"))
        btn_ambas.clicked.connect(lambda: self._set_vista("ambas"))

        bar_layout = QHBoxLayout()
        for btn in [btn_planta, btn_seccion, btn_ambas]:
            btn.setMaximumWidth(130)
            bar_layout.addWidget(btn)
        bar_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(bar_layout)
        layout.addWidget(self.canvas)

        self._vista = "ambas"
        self._ultimo_geo = None
        self._ultimo_col = None
        self._ultimo_res = None

    def _set_vista(self, vista: str):
        self._vista = vista
        if self._ultimo_geo:
            self.dibujar_armado(self._ultimo_geo, self._ultimo_col, self._ultimo_res)

    def dibujar_armado(
        self,
        geo: GeometriaZapata,
        col: Columna,
        res: ResultadoDetallado,
    ):
        self._ultimo_geo = geo
        self._ultimo_col = col
        self._ultimo_res = res
        self.figura.clear()

        if self._vista == "ambas":
            ax_planta = self.figura.add_subplot(1, 2, 1)
            ax_seccion = self.figura.add_subplot(1, 2, 2)
            self._planta(ax_planta, geo, col, res)
            self._seccion(ax_seccion, geo, col, res)
        elif self._vista == "planta":
            ax = self.figura.add_subplot(1, 1, 1)
            self._planta(ax, geo, col, res)
        else:
            ax = self.figura.add_subplot(1, 1, 1)
            self._seccion(ax, geo, col, res)

        self.figura.tight_layout(pad=2.0)
        self.canvas.draw()

    # ------------------------------------------------------------------
    def _planta(self, ax, geo, col, res):
        """
        Vista en planta del armado:
        - Rectángulo exterior de la zapata
        - Grilla de barras en X (líneas horizontales)
        - Grilla de barras en Y (líneas verticales)
        - Columna (rellena gris)
        - Dowels (cruces rojas)
        - Cotas y leyenda
        """
        B, L = geo.B, geo.L
        recub = geo.recubrimiento
        c1, c2 = col.ancho, col.largo
        dx = res.detalle_x
        dy = res.detalle_y
        dw = res.dowels

        # Zapata (contorno)
        rect = mpatches.Rectangle(
            (-B/2, -L/2), B, L,
            linewidth=2, edgecolor='#1565C0', facecolor='#E3F2FD', zorder=1
        )
        ax.add_patch(rect)

        # --- Barras en dirección X (van de -B/2+recub a +B/2-recub, distribuidas en Y) ---
        espacio_y = L - 2 * recub
        if dx.cantidad_barras > 1:
            posiciones_y = np.linspace(-L/2 + recub, L/2 - recub, dx.cantidad_barras)
        else:
            posiciones_y = [0.0]

        x_ini = -B/2 + recub
        x_fin = B/2 - recub

        for y in posiciones_y:
            ax.plot([x_ini, x_fin], [y, y],
                    color='#C62828', linewidth=1.5, zorder=3,
                    solid_capstyle='round')

        # --- Barras en dirección Y (van de -L/2+recub a +L/2-recub, distribuidas en X) ---
        if dy.cantidad_barras > 1:
            posiciones_x = np.linspace(-B/2 + recub, B/2 - recub, dy.cantidad_barras)
        else:
            posiciones_x = [0.0]

        y_ini = -L/2 + recub
        y_fin = L/2 - recub

        # Barras Y van debajo de X (se dibujan primero, líneas un poco más delgadas)
        for x in posiciones_x:
            ax.plot([x, x], [y_ini, y_fin],
                    color='#1565C0', linewidth=1.2, zorder=2,
                    solid_capstyle='round')

        # --- Columna ---
        col_rect = mpatches.Rectangle(
            (-c1/2, -c2/2), c1, c2,
            linewidth=2, edgecolor='#37474F', facecolor='#78909C', zorder=4
        )
        ax.add_patch(col_rect)

        # --- Dowels (esquinas de la columna) ---
        offset = 0.03  # offset desde esquina de columna
        dowel_positions = []
        if dw.cantidad >= 4:
            dowel_positions = [
                (-c1/2 + offset, -c2/2 + offset),
                ( c1/2 - offset, -c2/2 + offset),
                ( c1/2 - offset,  c2/2 - offset),
                (-c1/2 + offset,  c2/2 - offset),
            ]
        # Si hay más de 4 dowels, agregar intermedios
        if dw.cantidad > 4:
            extra = dw.cantidad - 4
            paso_x = c1 / (extra // 2 + 1) if extra >= 2 else c1
            for i in range(1, extra // 2 + 1):
                dowel_positions.append((-c1/2 + i * paso_x, -c2/2 + offset))
                dowel_positions.append((-c1/2 + i * paso_x,  c2/2 - offset))

        for xd, yd in dowel_positions:
            ax.plot(xd, yd, 'r+', markersize=10, markeredgewidth=2, zorder=5)

        # --- Cotas ---
        off = 0.15
        ax.annotate('', xy=(B/2, -L/2 - off), xytext=(-B/2, -L/2 - off),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.5))
        ax.text(0, -L/2 - off - 0.10, f"B = {B:.2f} m", ha='center', fontsize=8,
                color='#1565C0', fontweight='bold')

        ax.annotate('', xy=(B/2 + off, L/2), xytext=(B/2 + off, -L/2),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.5))
        ax.text(B/2 + off + 0.08, 0, f"L = {L:.2f} m",
                ha='left', fontsize=8, color='#1565C0',
                fontweight='bold', rotation=90, va='center')

        # Sep barras X
        if len(posiciones_y) > 1:
            sep = posiciones_y[1] - posiciones_y[0]
            ax.annotate('', xy=(-B/2 - 0.05, posiciones_y[1]),
                        xytext=(-B/2 - 0.05, posiciones_y[0]),
                        arrowprops=dict(arrowstyle='<->', color='#C62828', lw=1.0))
            ax.text(-B/2 - 0.18, (posiciones_y[0] + posiciones_y[1]) / 2,
                    f"{sep*100:.0f}cm", ha='center', fontsize=7, color='#C62828', rotation=90)

        # --- Leyenda ---
        leyenda = [
            mlines.Line2D([], [], color='#C62828', lw=2,
                          label=f"Dir-X: {dx.cantidad_barras}×{dx.codigo_varilla} "
                                f"@ {dx.separacion_real_mm:.0f}mm"),
            mlines.Line2D([], [], color='#1565C0', lw=2,
                          label=f"Dir-Y: {dy.cantidad_barras}×{dy.codigo_varilla} "
                                f"@ {dy.separacion_real_mm:.0f}mm"),
            mlines.Line2D([], [], color='red', marker='+', linestyle='None',
                          markersize=10, label=f"Dowels: {dw.cantidad}×{dw.codigo_varilla}"),
        ]
        ax.legend(handles=leyenda, loc='upper left', fontsize=7, framealpha=0.9)

        ax.set_xlim(-B/2 - 0.40, B/2 + 0.45)
        ax.set_ylim(-L/2 - 0.40, L/2 + 0.30)
        ax.set_aspect('equal')
        ax.set_title("PLANTA — Armadura inferior", fontweight='bold', fontsize=11)
        ax.axis('off')

    # ------------------------------------------------------------------
    def _seccion(self, ax, geo, col, res):
        """
        Sección transversal:
        - Perfil de la zapata (rectángulo)
        - Capa de armadura inferior (círculos de barra a escala)
        - Dowels subiendo hacia la columna
        - Columna sobre la zapata
        - Cotas: h, recubrimiento, d
        """
        B, h = geo.B, geo.h
        recub = geo.recubrimiento
        d = geo.d
        c1 = col.ancho
        dx = res.detalle_x
        dw = res.dowels
        db_m = dx.diametro_mm / 1000

        # Zapata
        zapata = mpatches.Rectangle(
            (-B/2, 0), B, h,
            linewidth=2, edgecolor='#1565C0', facecolor='#E3F2FD', zorder=1
        )
        ax.add_patch(zapata)

        # Columna
        col_rect = mpatches.Rectangle(
            (-c1/2, h), c1, 0.40,
            linewidth=2, edgecolor='#37474F', facecolor='#78909C', zorder=3
        )
        ax.add_patch(col_rect)

        # --- Barras inferiores en sección (círculos proporcionales) ---
        y_barra = recub + db_m / 2  # eje de la barra inferior
        if dx.cantidad_barras > 1:
            xs = np.linspace(-B/2 + recub + db_m/2,
                             B/2 - recub - db_m/2,
                             dx.cantidad_barras)
        else:
            xs = [0.0]

        radio_plot = db_m * 1.5  # escala visual (agrandar un poco)
        for xi in xs:
            circ = plt.Circle((xi, y_barra), radio_plot,
                               color='#C62828', zorder=4)
            ax.add_patch(circ)

        # --- Dowels (líneas verticales desde armadura hasta columna) ---
        offset_c = 0.04
        dowel_xs = [-c1/2 + offset_c, c1/2 - offset_c]  # 2 dowels visibles en sección
        for xd in dowel_xs:
            ax.plot([xd, xd], [y_barra, h + 0.35],
                    color='#E65100', linewidth=2.5, zorder=5,
                    solid_capstyle='round')

        # --- Cotas ---
        off_x = B/2 + 0.12

        # Altura total h
        ax.annotate('', xy=(off_x, h), xytext=(off_x, 0),
                    arrowprops=dict(arrowstyle='<->', color='#1565C0', lw=1.5))
        ax.text(off_x + 0.08, h/2, f"h = {h*100:.0f} cm",
                ha='left', va='center', fontsize=8, color='#1565C0', fontweight='bold')

        # Recubrimiento
        off_x2 = -B/2 - 0.12
        ax.annotate('', xy=(off_x2, y_barra), xytext=(off_x2, 0),
                    arrowprops=dict(arrowstyle='<->', color='#C62828', lw=1.2))
        ax.text(off_x2 - 0.05, y_barra / 2,
                f"r={recub*100:.0f}cm",
                ha='right', va='center', fontsize=7, color='#C62828')

        # Peralte efectivo d
        ax.annotate('', xy=(off_x2, d), xytext=(off_x2, 0),
                    arrowprops=dict(arrowstyle='<->', color='#2e7d32', lw=1.2))
        ax.text(off_x2 - 0.05, d + 0.02,
                f"d={d*100:.1f}cm",
                ha='right', va='bottom', fontsize=7, color='#2e7d32')

        # Ancho B
        ax.annotate('', xy=(B/2, -0.12), xytext=(-B/2, -0.12),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.5))
        ax.text(0, -0.20, f"B = {B:.2f} m",
                ha='center', fontsize=8, color='#1565C0', fontweight='bold')

        # --- Leyenda ---
        leyenda = [
            mpatches.Patch(color='#C62828',
                           label=f"Armadura inf. {dx.cantidad_barras}×{dx.codigo_varilla}"),
            mlines.Line2D([], [], color='#E65100', lw=2.5,
                          label=f"Dowels {dw.cantidad}×{dw.codigo_varilla}"),
        ]
        ax.legend(handles=leyenda, loc='upper right', fontsize=7)

        ax.set_xlim(-B/2 - 0.45, B/2 + 0.40)
        ax.set_ylim(-0.35, h + 0.65)
        ax.set_aspect('equal')
        ax.set_title("SECCIÓN TRANSVERSAL", fontweight='bold', fontsize=11)
        ax.axis('off')
```

---

## 13. Exportación CAD — Formato DXF

### 13.1 `reportes/exportador_dxf.py`

El formato DXF es compatible con **AutoCAD**, **LibreCAD**, **BricsCAD**, **ZWCAD** y cualquier software de ingeniería civil.

**Ruta:** `reportes/exportador_dxf.py`

```python
"""
Exportador DXF de la zapata aislada con detallado de acero.
Genera un archivo .dxf con capas organizadas:

  CAPAS:
  ├── ZAPATA_CONTORNO      — Líneas del contorno de la zapata
  ├── ZAPATA_SECCION       — Sección transversal
  ├── ARMADURA_X           — Barras en dirección X (planta)
  ├── ARMADURA_Y           — Barras en dirección Y (planta)
  ├── ARMADURA_SECCION     — Barras en sección (círculos)
  ├── DOWELS               — Barras de arranque
  ├── COTAS                — Dimensiones y cotas
  ├── TEXTOS               — Rótulos y anotaciones
  └── COLUMNA              — Contorno de la columna

Requiere: pip install ezdxf
"""

import math
import ezdxf
from ezdxf import colors as dxf_colors
from ezdxf.enums import TextEntityAlignment

from core.detallado_acero import ResultadoDetallado
from core.zapata_aislada import GeometriaZapata, Columna


# Colores DXF (índice ACI)
COLOR_ZAPATA    = 5    # Azul
COLOR_ARMADURA_X = 1   # Rojo
COLOR_ARMADURA_Y = 3   # Verde
COLOR_DOWELS    = 30   # Naranja
COLOR_COTAS     = 7    # Blanco/Negro
COLOR_TEXTOS    = 7
COLOR_COLUMNA   = 8    # Gris


class ExportadorDXF:
    """
    Genera un archivo DXF con planta y sección de la zapata armada.

    Uso:
        exp = ExportadorDXF()
        exp.exportar("zapata.dxf", geo, col, resultado_detallado)
    """

    # Escala: todo en METROS en el DXF.
    # El usuario puede escalar al imprimir desde AutoCAD.

    def exportar(
        self,
        ruta: str,
        geo: GeometriaZapata,
        col: Columna,
        res: ResultadoDetallado,
        proyecto: str = "FundaCalc",
    ):
        doc = ezdxf.new(dxfversion="R2010")
        doc.header["$INSUNITS"] = 6  # metros

        msp = doc.modelspace()

        # Crear capas
        self._crear_capas(doc)

        # ---- BLOQUE 1: Vista en Planta (origen en 0,0) ----
        origen_planta = (0, 0)
        self._dibujar_planta(msp, geo, col, res, origen_planta)

        # ---- BLOQUE 2: Sección transversal (a la derecha de la planta) ----
        offset_seccion = geo.B + 1.5  # separación horizontal
        origen_seccion = (offset_seccion, 0)
        self._dibujar_seccion(msp, geo, col, res, origen_seccion)

        # ---- TABLA DE ACERO (texto debajo de los planos) ----
        origen_tabla = (0, -geo.L / 2 - 1.5)
        self._dibujar_tabla_acero(msp, res, origen_tabla)

        # ---- Carátula / Rótulo ----
        self._dibujar_rotulo(msp, geo, col, res, proyecto)

        doc.saveas(ruta)

    # ------------------------------------------------------------------
    def _crear_capas(self, doc):
        capas = [
            ("ZAPATA_CONTORNO",  COLOR_ZAPATA,     "Continuous"),
            ("ZAPATA_SECCION",   COLOR_ZAPATA,     "Continuous"),
            ("ARMADURA_X",       COLOR_ARMADURA_X, "Continuous"),
            ("ARMADURA_Y",       COLOR_ARMADURA_Y, "Continuous"),
            ("ARMADURA_SECCION", COLOR_ARMADURA_X, "Continuous"),
            ("DOWELS",           COLOR_DOWELS,     "Continuous"),
            ("COTAS",            COLOR_COTAS,      "Continuous"),
            ("TEXTOS",           COLOR_TEXTOS,     "Continuous"),
            ("COLUMNA",          COLOR_COLUMNA,    "Continuous"),
        ]
        for nombre, color, tipo_linea in capas:
            capa = doc.layers.new(nombre)
            capa.color = color

    # ------------------------------------------------------------------
    def _dibujar_planta(self, msp, geo, col, res, origen):
        """Dibuja la vista en planta completa."""
        ox, oy = origen
        B, L = geo.B, geo.L
        recub = geo.recubrimiento
        c1, c2 = col.ancho, col.largo
        dx = res.detalle_x
        dy = res.detalle_y
        dw = res.dowels

        cx = ox  # Centro X
        cy = oy  # Centro Y

        # --- Contorno zapata ---
        msp.add_lwpolyline(
            [(cx - B/2, cy - L/2),
             (cx + B/2, cy - L/2),
             (cx + B/2, cy + L/2),
             (cx - B/2, cy + L/2),
             (cx - B/2, cy - L/2)],
            dxfattribs={"layer": "ZAPATA_CONTORNO", "lineweight": 50}
        )

        # --- Barras Dir-X (horizontales en planta) ---
        if dx.cantidad_barras > 1:
            posiciones_y = _linspace(cy - L/2 + recub, cy + L/2 - recub, dx.cantidad_barras)
        else:
            posiciones_y = [cy]

        x_ini = cx - B/2 + recub
        x_fin = cx + B/2 - recub
        for y in posiciones_y:
            msp.add_line(
                (x_ini, y), (x_fin, y),
                dxfattribs={"layer": "ARMADURA_X", "lineweight": 30}
            )

        # --- Barras Dir-Y (verticales en planta) ---
        if dy.cantidad_barras > 1:
            posiciones_x = _linspace(cx - B/2 + recub, cx + B/2 - recub, dy.cantidad_barras)
        else:
            posiciones_x = [cx]

        y_ini = cy - L/2 + recub
        y_fin = cy + L/2 - recub
        for x in posiciones_x:
            msp.add_line(
                (x, y_ini), (x, y_fin),
                dxfattribs={"layer": "ARMADURA_Y", "lineweight": 25}
            )

        # --- Columna ---
        msp.add_lwpolyline(
            [(cx - c1/2, cy - c2/2),
             (cx + c1/2, cy - c2/2),
             (cx + c1/2, cy + c2/2),
             (cx - c1/2, cy + c2/2),
             (cx - c1/2, cy - c2/2)],
            dxfattribs={"layer": "COLUMNA", "lineweight": 60}
        )

        # --- Dowels ---
        offset = 0.04
        dowel_pts = [
            (cx - c1/2 + offset, cy - c2/2 + offset),
            (cx + c1/2 - offset, cy - c2/2 + offset),
            (cx + c1/2 - offset, cy + c2/2 - offset),
            (cx - c1/2 + offset, cy + c2/2 - offset),
        ]
        r_dowel = dw.diametro_mm / 1000 / 2
        for (xd, yd) in dowel_pts:
            msp.add_circle(
                (xd, yd), r_dowel * 3,
                dxfattribs={"layer": "DOWELS", "lineweight": 25}
            )
            # Cruz interior
            msp.add_line((xd - r_dowel*3, yd), (xd + r_dowel*3, yd),
                         dxfattribs={"layer": "DOWELS"})
            msp.add_line((xd, yd - r_dowel*3), (xd, yd + r_dowel*3),
                         dxfattribs={"layer": "DOWELS"})

        # --- Cotas ---
        self._cota_horizontal(msp, cx - B/2, cx + B/2, cy - L/2 - 0.30,
                               f"B = {B:.2f} m")
        self._cota_vertical(msp, cy - L/2, cy + L/2, cx + B/2 + 0.30,
                             f"L = {L:.2f} m")

        # --- Título vista ---
        msp.add_text(
            "VISTA EN PLANTA — ARMADURA INFERIOR",
            dxfattribs={
                "layer": "TEXTOS",
                "height": 0.08,
                "insert": (cx, cy + L/2 + 0.35),
            }
        )

        # --- Separación entre barras (texto sobre primera barra) ---
        if len(posiciones_y) > 1:
            sep_mm = (posiciones_y[1] - posiciones_y[0]) * 1000
            msp.add_text(
                f"sep = {sep_mm:.0f}mm",
                dxfattribs={
                    "layer": "TEXTOS",
                    "height": 0.05,
                    "insert": (cx - B/2 - 0.45,
                                (posiciones_y[0] + posiciones_y[1]) / 2),
                }
            )

    # ------------------------------------------------------------------
    def _dibujar_seccion(self, msp, geo, col, res, origen):
        """Dibuja la sección transversal con barras y dowels."""
        ox, oy = origen
        B, h = geo.B, geo.h
        recub = geo.recubrimiento
        d = geo.d
        c1 = col.ancho
        dx = res.detalle_x
        dw = res.dowels
        db_m = dx.diametro_mm / 1000

        cx, cy = ox, oy  # base inferior centro

        # --- Zapata (sección) ---
        msp.add_lwpolyline(
            [(cx - B/2, cy),
             (cx + B/2, cy),
             (cx + B/2, cy + h),
             (cx - B/2, cy + h),
             (cx - B/2, cy)],
            dxfattribs={"layer": "ZAPATA_SECCION", "lineweight": 50}
        )

        # --- Columna ---
        msp.add_lwpolyline(
            [(cx - c1/2, cy + h),
             (cx + c1/2, cy + h),
             (cx + c1/2, cy + h + 0.50),
             (cx - c1/2, cy + h + 0.50),
             (cx - c1/2, cy + h)],
            dxfattribs={"layer": "COLUMNA", "lineweight": 60}
        )

        # --- Barras inferiores (círculos en sección) ---
        y_barra = cy + recub + db_m / 2
        n = dx.cantidad_barras
        if n > 1:
            xs = _linspace(cx - B/2 + recub + db_m/2,
                           cx + B/2 - recub - db_m/2, n)
        else:
            xs = [cx]

        r_plot = db_m / 2
        for xi in xs:
            # Círculo relleno (hatch) — representación de sección de barra
            msp.add_circle(
                (xi, y_barra), r_plot * 1.5,
                dxfattribs={"layer": "ARMADURA_SECCION", "lineweight": 30}
            )

        # --- Dowels (líneas verticales) ---
        dowel_xs_sec = [cx - c1/2 + 0.04, cx + c1/2 - 0.04]
        for xd in dowel_xs_sec:
            msp.add_line(
                (xd, y_barra),
                (xd, cy + h + 0.45),
                dxfattribs={"layer": "DOWELS", "lineweight": 40}
            )
            # Gancho en la base
            gancho_largo = 12 * dw.diametro_mm / 1000
            sentido = 1 if xd > cx else -1
            msp.add_line(
                (xd, y_barra),
                (xd + sentido * gancho_largo, y_barra),
                dxfattribs={"layer": "DOWELS", "lineweight": 40}
            )

        # --- Línea de recubrimiento ---
        msp.add_line(
            (cx - B/2, cy + recub),
            (cx + B/2, cy + recub),
            dxfattribs={"layer": "COTAS", "lineweight": 13,
                        "linetype": "DASHED"}
        )

        # --- Cotas ---
        self._cota_vertical(msp, cy, cy + h, cx + B/2 + 0.25, f"h={h*100:.0f}cm")
        self._cota_vertical(msp, cy, cy + recub, cx - B/2 - 0.25,
                            f"r={recub*100:.0f}cm")
        self._cota_horizontal(msp, cx - B/2, cx + B/2, cy - 0.25, f"B={B:.2f}m")

        # --- Título ---
        msp.add_text(
            "SECCIÓN TRANSVERSAL",
            dxfattribs={
                "layer": "TEXTOS",
                "height": 0.08,
                "insert": (cx, cy + h + 0.70),
            }
        )

        # --- Anotación armadura ---
        msp.add_text(
            f"{dx.cantidad_barras}Ø{dx.diametro_mm:.0f}mm @ {dx.separacion_real_mm:.0f}mm",
            dxfattribs={
                "layer": "TEXTOS",
                "height": 0.055,
                "insert": (cx - B/2, cy - 0.12),
            }
        )

    # ------------------------------------------------------------------
    def _dibujar_tabla_acero(self, msp, res, origen):
        """Tabla de acero en formato plano estructural."""
        ox, oy = origen
        col_widths = [0.15, 0.20, 1.60, 0.20, 0.30, 0.25]
        headers = ["MCA", "VAR.", "DESCRIPCIÓN", "CANT.", "LONG.(m)", "PESO(kg)"]
        h_text = 0.05
        row_h = 0.12

        # Encabezado
        x = ox
        for i, (header, w) in enumerate(zip(headers, col_widths)):
            msp.add_lwpolyline(
                [(x, oy), (x+w, oy), (x+w, oy+row_h), (x, oy+row_h), (x, oy)],
                dxfattribs={"layer": "TEXTOS"}
            )
            msp.add_text(
                header,
                dxfattribs={"layer": "TEXTOS", "height": h_text,
                            "insert": (x + 0.01, oy + 0.04)}
            )
            x += w

        total_w = sum(col_widths)

        # Filas de datos
        for j, item in enumerate(res.tabla_acero):
            y_fila = oy - (j + 1) * row_h
            valores = [
                item["marca"],
                item["varilla"],
                item["descripcion"][:50],  # truncar si es muy largo
                str(item["cantidad"]),
                f"{item['longitud_m']:.3f}",
                f"{item['peso_kg']:.2f}",
            ]
            x = ox
            for val, w in zip(valores, col_widths):
                msp.add_lwpolyline(
                    [(x, y_fila), (x+w, y_fila),
                     (x+w, y_fila+row_h), (x, y_fila+row_h), (x, y_fila)],
                    dxfattribs={"layer": "TEXTOS"}
                )
                msp.add_text(
                    str(val),
                    dxfattribs={"layer": "TEXTOS", "height": h_text * 0.85,
                                "insert": (x + 0.01, y_fila + 0.03)}
                )
                x += w

        # Fila TOTAL
        y_total = oy - (len(res.tabla_acero) + 1) * row_h
        msp.add_text(
            f"TOTAL ACERO: {res.peso_total_acero_kg:.1f} kg     "
            f"HORMIGÓN: {res.volumen_hormigon_m3:.3f} m³",
            dxfattribs={"layer": "TEXTOS", "height": h_text,
                        "insert": (ox, y_total + 0.03)}
        )

    # ------------------------------------------------------------------
    def _dibujar_rotulo(self, msp, geo, col, res, proyecto):
        """Carátula básica en la esquina inferior derecha."""
        ox = geo.B + 1.5 + geo.B + 1.0
        oy = -geo.L / 2 - 1.5
        msp.add_text(
            f"Proyecto: {proyecto}",
            dxfattribs={"layer": "TEXTOS", "height": 0.10,
                        "insert": (ox, oy + 0.40)}
        )
        msp.add_text(
            f"Zapata: {geo.B:.2f}m × {geo.L:.2f}m × {geo.h:.2f}m",
            dxfattribs={"layer": "TEXTOS", "height": 0.07,
                        "insert": (ox, oy + 0.25)}
        )
        msp.add_text(
            f"Acero total: {res.peso_total_acero_kg:.1f} kg",
            dxfattribs={"layer": "TEXTOS", "height": 0.07,
                        "insert": (ox, oy + 0.12)}
        )
        msp.add_text(
            "FundaCalc v1.0",
            dxfattribs={"layer": "TEXTOS", "height": 0.07,
                        "insert": (ox, oy)}
        )

    # ------------------------------------------------------------------
    # Helpers de cotas
    # ------------------------------------------------------------------
    def _cota_horizontal(self, msp, x1, x2, y, texto):
        off = 0.08
        # Línea de cota
        msp.add_line((x1, y), (x2, y), dxfattribs={"layer": "COTAS"})
        # Testigos
        msp.add_line((x1, y - off), (x1, y + off), dxfattribs={"layer": "COTAS"})
        msp.add_line((x2, y - off), (x2, y + off), dxfattribs={"layer": "COTAS"})
        # Texto
        msp.add_text(
            texto,
            dxfattribs={"layer": "TEXTOS", "height": 0.06,
                        "insert": ((x1 + x2) / 2, y - 0.12)}
        )

    def _cota_vertical(self, msp, y1, y2, x, texto):
        off = 0.08
        msp.add_line((x, y1), (x, y2), dxfattribs={"layer": "COTAS"})
        msp.add_line((x - off, y1), (x + off, y1), dxfattribs={"layer": "COTAS"})
        msp.add_line((x - off, y2), (x + off, y2), dxfattribs={"layer": "COTAS"})
        msp.add_text(
            texto,
            dxfattribs={"layer": "TEXTOS", "height": 0.06,
                        "insert": (x + 0.10, (y1 + y2) / 2),
                        "rotation": 90}
        )


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------
def _linspace(start, stop, n):
    if n == 1:
        return [(start + stop) / 2]
    step = (stop - start) / (n - 1)
    return [start + i * step for i in range(n)]
```

### 13.2 Instalación de ezdxf

Agregar al `requirements.txt`:

```
ezdxf==1.3.4
```

Instalar:

```bash
pip install ezdxf
```

Integrar el botón de exportación DXF en `ui/ventana_principal.py`:

```python
# En _crear_menu(), dentro del menú Reportes:
a_dxf = QAction("Exportar DXF (AutoCAD)...", self)
a_dxf.setShortcut("Ctrl+D")
a_dxf.triggered.connect(self._exportar_dxf)
m_reportes.addAction(a_dxf)

# Método a agregar en VentanaPrincipal:
def _exportar_dxf(self):
    from reportes.exportador_dxf import ExportadorDXF
    path, _ = QFileDialog.getSaveFileName(
        self, "Exportar DXF", "", "AutoCAD DXF (*.dxf)"
    )
    if path:
        detallado = self.panel_zapata_aislada.panel_detallado.obtener_detallado()
        geo = self.panel_zapata_aislada._ultimo_calculo["geometria"]
        col = self.panel_zapata_aislada._ultimo_calculo["columna"]
        if detallado and geo and col:
            exp = ExportadorDXF()
            exp.exportar(path, geo, col, detallado)
            self.lbl_status.setText(f"DXF exportado: {path}")
        else:
            QMessageBox.warning(self, "Aviso",
                "Ejecute el cálculo y el detallado antes de exportar DXF.")
```

---

## 14. PDF Actualizado con Detallado Completo

### 14.1 `reportes/generador_pdf_detallado.py`

**Ruta:** `reportes/generador_pdf_detallado.py`

```python
"""
PDF completo con detallado de acero:
  Página 1 — Portada + datos de entrada
  Página 2 — Resultados del cálculo estructural
  Página 3 — Tabla de acero + resumen de materiales
  Página 4 — Plano esquemático (planta + sección exportados desde matplotlib)
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np

from core.zapata_aislada import ResultadosZapata, GeometriaZapata, Columna
from core.detallado_acero import ResultadoDetallado
from reportes.generador_pdf import GeneradorPDF, AZUL, VERDE, ROJO, GRIS_CLARO


class GeneradorPDFDetallado(GeneradorPDF):
    """
    Extiende GeneradorPDF con las secciones de detallado de acero.
    """

    def generar_completo(
        self,
        ruta: str,
        resultado: ResultadosZapata,
        detallado: ResultadoDetallado,
        datos: dict,
    ):
        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )
        estilos = getSampleStyleSheet()
        historia = []

        # Página 1: portada + datos
        historia += self._portada(estilos, datos)
        historia.append(PageBreak())
        historia += self._datos_entrada(estilos, datos)
        historia.append(PageBreak())

        # Página 2: resultados estructurales
        historia += self._tabla_resultados(estilos, resultado)
        historia.append(Spacer(1, 0.5*cm))
        historia += self._verificaciones(estilos, resultado)
        historia.append(PageBreak())

        # Página 3: tabla de acero
        historia += self._seccion_detallado(estilos, detallado)
        historia.append(PageBreak())

        # Página 4: plano esquemático
        historia += self._plano_esquematico(estilos, datos, detallado)

        doc.build(historia)

    # ------------------------------------------------------------------
    def _seccion_detallado(self, estilos, det: ResultadoDetallado):
        titulo = Paragraph(
            "3. Detallado de Acero de Refuerzo",
            ParagraphStyle('T', parent=estilos['Title'],
                           fontSize=16, textColor=AZUL, spaceAfter=8)
        )
        elementos = [titulo, Spacer(1, 0.3*cm)]

        # Resumen Dir X e Y
        dx = det.detalle_x
        dy = det.detalle_y
        dw = det.dowels

        data_dir = [
            ["", "Dirección X", "Dirección Y", "Dowels Columna"],
            ["Varilla",
             dx.codigo_varilla, dy.codigo_varilla, dw.codigo_varilla],
            ["Diámetro",
             f"{dx.diametro_mm:.0f} mm", f"{dy.diametro_mm:.0f} mm",
             f"{dw.diametro_mm:.0f} mm"],
            ["Área barra",
             f"{dx.area_barra_cm2:.3f} cm²", f"{dy.area_barra_cm2:.3f} cm²",
             f"{dw.area_barra_cm2:.3f} cm²"],
            ["Cantidad",
             str(dx.cantidad_barras), str(dy.cantidad_barras),
             str(dw.cantidad)],
            ["Separación",
             f"{dx.separacion_real_mm:.0f} mm", f"{dy.separacion_real_mm:.0f} mm",
             "—"],
            ["As provisto",
             f"{dx.as_provisto_cm2:.2f} cm²", f"{dy.as_provisto_cm2:.2f} cm²",
             "—"],
            ["Longitud barra",
             f"{dx.longitud_con_gancho_m:.3f} m", f"{dy.longitud_con_gancho_m:.3f} m",
             f"{dw.longitud_total_barra_m:.3f} m"],
            ["Gancho",
             dx.tipo_gancho if dx.requiere_gancho else "No requiere",
             dy.tipo_gancho if dy.requiere_gancho else "No requiere",
             "90°"],
            ["Peso total",
             f"{dx.peso_total_kg:.2f} kg", f"{dy.peso_total_kg:.2f} kg",
             f"{dw.peso_total_kg:.2f} kg"],
        ]

        tbl = Table(data_dir, colWidths=[4*cm, 3.8*cm, 3.8*cm, 3.8*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (0, -1), GRIS_CLARO),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ]))
        elementos.append(tbl)
        elementos.append(Spacer(1, 0.5*cm))

        # Tabla de acero tipo plano
        titulo2 = Paragraph(
            "Tabla de Acero — Lista de Hierros",
            ParagraphStyle('T2', parent=estilos['Heading2'],
                           textColor=AZUL, spaceAfter=6)
        )
        elementos.append(titulo2)

        data_tabla = [["MCA", "VARILLA", "DESCRIPCIÓN", "CANT.", "LONG.(m)", "PESO(kg)"]]
        peso_total = 0.0
        for item in det.tabla_acero:
            data_tabla.append([
                item["marca"],
                item["varilla"],
                item["descripcion"][:45],
                str(item["cantidad"]),
                f"{item['longitud_m']:.3f}",
                f"{item['peso_kg']:.2f}",
            ])
            peso_total += item["peso_kg"]

        data_tabla.append(["", "", "TOTAL", "", "", f"{peso_total:.2f} kg"])

        tbl2 = Table(data_tabla, colWidths=[1.2*cm, 2*cm, 7*cm, 1.5*cm, 2*cm, 2*cm])
        style2 = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), AZUL),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRIS_CLARO]),
        ])
        tbl2.setStyle(style2)
        elementos.append(tbl2)
        elementos.append(Spacer(1, 0.5*cm))

        # Resumen de materiales
        data_mat = [
            ["RESUMEN DE MATERIALES", ""],
            ["Peso total acero", f"{det.peso_total_acero_kg:.1f} kg"],
            ["Volumen hormigón", f"{det.volumen_hormigon_m3:.3f} m³"],
        ]
        tbl_mat = Table(data_mat, colWidths=[8*cm, 4*cm])
        tbl_mat.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), VERDE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (-1, 0)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        elementos.append(tbl_mat)

        return elementos

    # ------------------------------------------------------------------
    def _plano_esquematico(self, estilos, datos, det: ResultadoDetallado):
        """Genera imagen matplotlib y la embebe en el PDF."""
        titulo = Paragraph(
            "4. Plano Esquemático del Armado",
            ParagraphStyle('T', parent=estilos['Title'],
                           fontSize=16, textColor=AZUL, spaceAfter=8)
        )

        geo = datos["geometria"]
        col = datos["columna"]

        # Generar figura con matplotlib en memoria
        fig = self._generar_figura_armado(geo, col, det)

        # Guardar en buffer de bytes
        buf = io.BytesIO()
        fig.savefig(buf, format="PNG", dpi=150, bbox_inches='tight',
                    facecolor='white')
        plt.close(fig)
        buf.seek(0)

        img = RLImage(buf, width=16*cm, height=11*cm)

        nota = Paragraph(
            "<i>Plano esquemático de referencia. Para el plano de taller consultar "
            "el archivo DXF exportado.</i>",
            ParagraphStyle('Nota', parent=estilos['Normal'],
                           fontSize=8, textColor=colors.grey, spaceAfter=4)
        )

        return [titulo, Spacer(1, 0.3*cm), img, Spacer(1, 0.3*cm), nota]

    def _generar_figura_armado(self, geo, col, det) -> plt.Figure:
        """Crea la figura matplotlib para insertar en el PDF."""
        from ui.panel_grafico_armado import PanelGraficoArmado
        # Crear figura directamente sin widget
        fig = plt.Figure(figsize=(14, 6), dpi=120)
        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)

        # Reutilizar las funciones de dibujo
        helper = PanelGraficoArmado.__new__(PanelGraficoArmado)
        helper._planta(ax1, geo, col, det)
        helper._seccion(ax2, geo, col, det)
        fig.tight_layout(pad=2.0)
        return fig
```

---

## Flujo completo de trabajo actualizado

```
Usuario ingresa datos
        ↓
  [Calcular zapata]
  core/zapata_aislada.py
  → ResultadosZapata
        ↓
  Panel muestra: B, L, h, As_req_X, As_req_Y
        ↓
  Usuario selecciona varilla
  (ej: As=32cm² → elige Ø16)
        ↓
  [Actualizar Detallado]
  core/detallado_acero.py
  → ResultadoDetallado
        ↓
  ┌─────────────────────────────────┐
  │ Panel muestra:                  │
  │ • Cant. barras + separación     │
  │ • Longitudes de corte           │
  │ • Ganchos si son necesarios     │
  │ • Dowels columna-zapata         │
  │ • Tabla de acero completa       │
  │ • Peso total kg                 │
  └─────────────────────────────────┘
        ↓
  Gráfico actualizado:
  • Planta: grilla de barras reales
  • Sección: círculos a escala + dowels
        ↓
  ┌──────────┬────────────┐
  │ PDF      │  DXF/CAD  │
  │ 4 páginas│ AutoCAD   │
  │ completo │ LibreCAD  │
  └──────────┴────────────┘
```

---

## Archivos nuevos a agregar a la estructura

```
FundaCalc/
├── core/
│   └── detallado_acero.py         ← NUEVO
├── ui/
│   ├── panel_detallado.py         ← NUEVO
│   └── panel_grafico_armado.py    ← NUEVO
└── reportes/
    ├── exportador_dxf.py          ← NUEVO
    └── generador_pdf_detallado.py ← NUEVO
```

### requirements.txt actualizado

```
PyQt6==6.7.0
numpy==1.26.4
scipy==1.13.0
matplotlib==3.9.0
reportlab==4.2.0
Pillow==10.3.0
ezdxf==1.3.4
```

---

*FundaCalc — Documento Maestro v2.0 | Módulo de Detallado de Acero + Exportación CAD*

---
---

# PARTE II — EVOLUCIÓN A APP WEB (IMPLEMENTACIÓN REAL)

> A partir de esta sección el proyecto migra de app de escritorio (PyQt6)
> a una **aplicación web completa** con backend Python/FastAPI, accesible
> desde cualquier navegador sin instalación de software adicional.

---

## 15. Decisión Arquitectónica — FastAPI Backend + HTML Frontend

### Por qué FastAPI (y no JS puro)

El cálculo estructural requiere NumPy, matplotlib y ReportLab — librerías Python
sin equivalente JS fiel. La decisión fue mantener el motor de cálculo en Python
y exponerlo vía API REST.

| Criterio | JS puro (descartado) | FastAPI + Python (elegido) |
|---|---|---|
| Motor de cálculo | Requiere reescribir en JS | Reutiliza core/ sin cambios |
| Gráficos (planta/sección) | SVG/Canvas manual | Matplotlib Agg → PNG |
| PDF profesional | jsPDF (limitado) | ReportLab (completo) |
| DXF/CAD | Librería JS limitada | ezdxf (total) |
| Normas (7) | Duplicar lógica | core/normas/* sin tocar |
| Despliegue | Static hosting | VPS Ubuntu (Oracle Cloud) |

### Stack final

```
Backend:   FastAPI 0.111 + uvicorn 0.30  →  Python 3.11
Cálculo:   core/zapata_aislada.py + core/normas/*  (sin cambios)
Gráficos:  matplotlib 3.9 backend Agg  →  PNG en memoria (BytesIO)
PDF:       ReportLab 4.2  →  PDF en memoria (BytesIO)
DXF:       ezdxf 1.3      →  archivo .dxf temporal
Frontend:  HTML5 + Bootstrap 5.3 + JS vanilla
```

---

## 16. Arquitectura Real de la App Web

### 16.1 Estructura de carpetas (web)

```
Calculo-Fundaciones/
│
├── web/
│   ├── server.py              ← FastAPI app — punto de entrada web
│   └── static/
│       ├── home.html          ← Landing page (8 módulos, dark theme)
│       └── index.html         ← Calculadora Módulo 1 (Zapata Aislada)
│
├── core/                      ← Motor de cálculo (sin cambios vs desktop)
│   ├── zapata_aislada.py
│   └── normas/
│       ├── aci318.py
│       ├── cirsoc201.py
│       ├── nch170.py
│       ├── nsr10.py
│       ├── nte_e060.py
│       ├── ntc_cdmx.py
│       └── ehe08.py
│
├── reportes/
│   ├── generador_pdf.py       ← PDF completo (portada + sección + armadura)
│   └── generador_dxf.py       ← DXF con capas organizadas
│
└── requirements.txt           ← Dependencias del servidor web
```

### 16.2 Endpoints de la API (web/server.py)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Redirige a `home.html` (landing) |
| `GET` | `/zapata` | Sirve `index.html` (calculadora) |
| `POST` | `/api/calcular` | Ejecuta el motor, devuelve JSON con resultados |
| `GET` | `/api/plot/planta` | PNG de vista en planta (matplotlib) |
| `GET` | `/api/plot/seccion` | PNG de sección transversal (matplotlib) |
| `POST` | `/api/report/pdf` | Genera y descarga PDF (ReportLab) |
| `POST` | `/api/export/dxf` | Genera y descarga DXF (ezdxf) |

### 16.3 Flujo de una petición de cálculo

```
Browser → POST /api/calcular (JSON con datos)
            ↓
          server.py: _build_motor(datos)
            ├── convierte unidades al sistema interno (kN, m)
            ├── instancia norma según datos.norma
            └── crea ZapataAislada(cargas, columna, suelo, ...)
            ↓
          motor.calcular() → ResultadosZapata
            ↓
          motor.calcular_pedestal() → ResultadosPedestal
            ↓
          JSON response: dimensiones, verificaciones, armadura, mensajes
            ↓
Browser ← renderResults(data): actualiza tabla de resultados en el DOM

Browser → GET /api/plot/planta   → PNG planta   (matplotlib, 2 paneles)
Browser → GET /api/plot/seccion  → PNG sección  (matplotlib, drawing only)
```

### 16.4 Sesión de cálculo en el servidor

El servidor es **stateless** — cada petición POST /api/calcular recibe todos los
datos necesarios. Los plots (planta y sección) están en memoria entre llamadas
gracias a variables de módulo (`_ultimo_motor`). Para producción multiusuario
se debería usar Redis o una sesión por request.

### 16.5 requirements.txt (web — limpio para servidor)

```
fastapi==0.111.0
uvicorn==0.30.1
numpy==1.26.4
scipy==1.13.0
matplotlib==3.9.0
reportlab==4.2.0
Pillow==10.3.0
jinja2==3.1.2
ezdxf==1.3.4
python-multipart==0.0.9
```

> **Nota:** `PyQt6` NO va en este requirements — es solo para la versión desktop.
> En el servidor Linux no hay pantalla, PyQt6 fallaría al importar.

---

## 17. Estado Actual de Features — Módulo 1 Web

### 17.1 Funcionalidades implementadas ✅

| Feature | Descripción |
|---|---|
| **7 normas de diseño** | ACI 318-19, CIRSOC 201, NCh 170, NSR-10, NTE E.060, NTC-CDMX, EHE-08 |
| **6 sistemas de unidades** | kN/m², kip/ft², tf/m², psf, ton/m², kg/m² |
| **Dimensionamiento automático** | Calcula B, L, h óptimos |
| **Iteración de altura** | Aumenta h hasta que punzonado y cortante pasen |
| **Diseño pedestal** | Bp, Lp manuales o auto (+10 cm/lado); longitudes de anclaje |
| **Vista en planta** | PNG matplotlib: zapata, columna, perímetro de punzonado, cotas |
| **Sección transversal** | PNG matplotlib: zapata, pedestal, armadura X/Y, dowels, cotas |
| **Memoria PDF** | 4 páginas: portada, datos entrada, sección+armadura, resultados+verificaciones |
| **DXF/CAD** | Exportación con capas: ZAPATA, COLUMNA, ARMADURA_X/Y, COTAS, TEXTOS |
| **Landing page** | home.html: 8 módulos dark-themed, Módulo 1 activo |
| **Loading animation** | Shimmer + spinner mín. 2.5 s al calcular |
| **Placeholder SVGs** | Dibujos genéricos antes del primer cálculo |
| **Info modal Bp×Lp** | Explicación teórica interactiva |
| **Top bar temático** | Misma textura dark/grid que home.html |

### 17.2 Roadmap web — módulos planificados

| Módulo | Estado | Complejidad | Notas |
|---|---|---|---|
| 1 — Zapata Aislada | ✅ Completo | Baja | Activo en producción |
| 2 — Zapata Combinada | 🔲 Próximo | Baja-Media | Viga invertida, distribución trapezoidal |
| 3 — Zapata Corrida | 🔲 Próximo | Baja | Carga lineal kN/m, sección 2D |
| 4 — Losa de Fundación | 🔲 Próximo | Media | Winkler, placas |
| 5 — Zapata Excéntrica | 🔲 Próximo | Baja | Extensión del módulo 1 |
| 6 — Pilotes y Encepados | 🔲 Pro | Media-Alta | Grupo de pilotes, distribución de carga |
| 7 — Muro de Contención | 🔲 Próximo | Media | Rankine/Coulomb, estabilidad |
| 8 — Capacidad Portante | 🔲 Próximo | Baja | Terzaghi, Meyerhof, Hansen |

---

## 18. Despliegue en Servidor Oracle Cloud (Ubuntu)

### 18.1 Requisitos del servidor

- Ubuntu 20.04/22.04 LTS
- Acceso SSH
- IP pública (Oracle Cloud free tier la incluye)
- Python 3.11+

### 18.2 Preparación local (antes de subir)

Verificar que no haya rutas absolutas de Windows hardcodeadas.
`server.py` ya usa `Path(__file__).resolve().parents[1]` — correcto.

Limpiar requirements.txt (sacar PyQt6, agregar python-multipart y ezdxf).

### 18.3 Setup en el servidor

```bash
# 1. Actualizar sistema e instalar dependencias
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx

# 2. Clonar o subir el proyecto
git clone https://github.com/tu-usuario/Calculo-Fundaciones.git
cd Calculo-Fundaciones
# Alternativa: scp -r ruta_local ubuntu@IP_SERVIDOR:~/

# 3. Entorno virtual
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Probar que levanta
uvicorn web.server:app --host 0.0.0.0 --port 8000
```

### 18.4 Servicio systemd (auto-restart)

Crear `/etc/systemd/system/fundacalc.service`:

```ini
[Unit]
Description=FundaCalc FastAPI
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Calculo-Fundaciones
ExecStart=/home/ubuntu/Calculo-Fundaciones/venv/bin/uvicorn web.server:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable fundacalc
sudo systemctl start fundacalc
sudo systemctl status fundacalc
```

### 18.5 Nginx como proxy inverso

Crear `/etc/nginx/sites-available/fundacalc`:

```nginx
server {
    listen 80;
    server_name TU_IP_O_DOMINIO;
    client_max_body_size 10M;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/fundacalc /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

### 18.6 ⚠️ Doble firewall en Oracle Cloud

Oracle Cloud bloquea puertos en dos capas — ambas deben abrirse:

**a) iptables en el VM Ubuntu:**
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

**b) Security List en la consola Oracle Cloud:**
- Networking → Virtual Cloud Networks → tu VCN → Security Lists
- Agregar Ingress Rule: puerto 80 TCP, source `0.0.0.0/0`
- Agregar Ingress Rule: puerto 443 TCP, source `0.0.0.0/0`

### 18.7 HTTPS gratis con Let's Encrypt (opcional)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
# El certificado se renueva automáticamente
```

### 18.8 Actualizaciones del código

```bash
cd /home/ubuntu/Calculo-Fundaciones
git pull origin main
sudo systemctl restart fundacalc
```

---

## 19. Diferencias Desktop vs Web — Mapa de componentes

| Componente | Desktop (PyQt6) | Web (FastAPI) |
|---|---|---|
| UI | `ui/panel_zapata_aislada.py` | `web/static/index.html` + JS |
| Cálculo | `core/zapata_aislada.py` | `core/zapata_aislada.py` (mismo) |
| Gráficos | `ui/panel_grafico.py` (QtAgg) | `web/server.py` funciones `_dibujar_*` (Agg→PNG) |
| PDF | `reportes/generador_pdf.py` | `reportes/generador_pdf.py` (mismo) |
| DXF | `reportes/generador_dxf.py` | `reportes/generador_dxf.py` (mismo) |
| Entrada de datos | QDoubleSpinBox | `<input type="number">` + `buildData()` JS |
| Norma | Combo PyQt6 | `<select>` HTML |
| Unidades | Hardcodeado kN/m | Selector + conversión en server.py |

El motor de cálculo (`core/`) es 100% compartido entre las dos interfaces.
Cualquier mejora al motor beneficia a ambas versiones.

---

*FundaCalc — Documento Maestro v3.0 | Web App (FastAPI) · Módulo 1 Completo · Deploy Oracle Cloud*




---

## 15. Modulo 3 - Zapata Corrida (Strip Footing)

### 15.1 Descripcion

La zapata corrida transmite la carga de un muro portante de forma continua al suelo.
El modelo de calculo es un **voladizo simple** a cada lado del muro, sometido a presion uniforme ascendente.

### 15.2 Parametros de entrada

| Parametro | Simbolo | Unidad | Descripcion |
|---|---|---|---|
| Carga muerta lineal | Pd | kN/m | Carga permanente por metro lineal de muro |
| Carga viva lineal   | Pl | kN/m | Carga variable por metro lineal de muro |
| Espesor del muro    | t  | m    | Grosor del muro portante |
| Presion admisible   | qa | kN/m2 | Capacidad portante del suelo |
| Prof. empotramiento | Df | m | Distancia superficie-base de zapata |
| Peso especifico suelo | gs | kN/m3 | Peso volumetrico del suelo de relleno |
| Resistencia hormigon | fck | MPa | Resistencia a compresion 28 dias |
| Fluencia acero | fy | MPa | Limite elastico del acero de refuerzo |
| Peralte total  | h  | m   | Altura total de la zapata (se itera si el cortante no verifica) |
| Recubrimiento  | r  | m   | Distancia cara inferior-centro de armadura |
| Ancho fijo     | B  | m   | 0 = automatico |

### 15.3 Logica de calculo



### 15.4 Armadura

| Tipo | Direccion | Criterio |
|---|---|---|
| Transversal (principal) | perpendicular al muro | As = max(As_flexion, As_min) segun norma activa |
| Longitudinal (temperatura) | paralela al muro | As_min segun norma activa |

La seleccion de varilla sigue la tabla interna (O8-O32 mm), eligiendo separacion entre 10 y 35 cm.

### 15.5 Archivos

| Archivo | Descripcion |
|---|---|
|  | Motor: CargaMuro, MuroCorrida, SueloCorrida, GeometriaCorrida, ResultadosZapataCorrida, ZapataCorridaRectangular |
|  | Memoria PDF: portada, datos, geometria, seccion, verificaciones, materiales, mensajes |
|  | Plano DXF: planta (franja 1 m), seccion transversal, cuadro de armadura |
|  | Frontend Bootstrap 5.3: formulario, resultados, plot seccion, PDF/DXF, glosario |
|  | Rutas: GET /zapata-corrida, POST /api/corrida/calcular, /api/corrida/plot/seccion, /api/corrida/report/pdf, /api/corrida/report/dxf |

### 15.6 Capas DXF

| Capa | Color | Contenido |
|---|---|---|
| ZAPATA   | 5 azul    | Contorno de la zapata |
| MURO     | 8 gris    | Contorno del muro |
| ACERO_T  | 1 rojo    | Armadura transversal perpendicular muro |
| ACERO_L  | 6 magenta | Armadura longitudinal paralela muro |
| COTAS    | 7 blanco  | Lineas de cota |
| TEXTOS   | 7 blanco  | Textos y leyendas |

### 15.7 Normas soportadas

ACI318, CIRSOC201, NCh170, NSR10, NTE_E060, NTC_CDMX, EHE08, COVENIN1753
