"""
ESCALC — Módulo C1: Unión Apernada a Corte (Shear Tab / Plancha de Alma).

Conexión simple: plancha rectangular soldada a columna, apernada al alma de la viga.
Transmite solo cortante (conexión articulada).

Referencia: AISC 360-22 Capítulo J + AISC Manual Parte 10.
"""
import math
from dataclasses import dataclass, field
from typing import List

from .normas_acero import NormaAcero, get_norma
from .materiales_acero import (
    AceroEstructural, TipoPerno, Electrodo,
    area_perno_nominal, diametro_agujero_estandar, Fnv_perno,
    ACEROS, PERNOS, ELECTRODOS,
)


# ── Datos de entrada ──────────────────────────────────────────────────────────

@dataclass
class DatosPernos:
    n:          int     # Número de pernos (columna vertical)
    db:         float   # Diámetro del perno [mm]
    tipo:       str     # Código en PERNOS (ej. "A325-X")
    n_corte:    int     # Planos de corte (1 o 2)
    e1:         float   # Distancia borde superior al 1er perno [mm]
    e2:         float   # Distancia borde lateral al eje de pernos [mm]
    p:          float   # Separación entre pernos [mm]
    hilos_en_plano: bool = False  # ¿Hilos en el plano de corte?


@dataclass
class DatosPlancha:
    tp:     float   # Espesor [mm]
    bp:     float   # Ancho [mm]
    acero:  str     # Código en ACEROS (ej. "A36")


@dataclass
class DatosViга:
    tw:     float   # Espesor del alma [mm]
    acero:  str     # Código en ACEROS


@dataclass
class DatosSoldadura:
    w:      float   # Tamaño del filete [mm]
    electrodo: str  # Código en ELECTRODOS (ej. "E70")
    lados:  int = 2 # Lados de soldadura (1 o 2)


@dataclass
class EntradaShearTab:
    Vu:         float          # Cortante último [kN] (LRFD)
    pernos:     DatosPernos
    plancha:    DatosPlancha
    viga:       DatosViга
    soldadura:  DatosSoldadura
    norma:      str = "AISC360"


# ── Resultados ────────────────────────────────────────────────────────────────

@dataclass
class Verificacion:
    nombre:      str
    referencia:  str
    demanda:     float    # [kN]
    capacidad:   float    # [kN]
    relacion:    float    # D/C
    formula:     str
    ok:          bool
    nota:        str = ""

    @classmethod
    def crear(cls, nombre, ref, demanda_N, capacidad_N, formula, nota=""):
        dem  = demanda_N / 1000
        cap  = capacidad_N / 1000
        rel  = dem / cap if cap > 0 else 999.0
        return cls(
            nombre=nombre, referencia=ref,
            demanda=round(dem, 2), capacidad=round(cap, 2),
            relacion=round(rel, 4), formula=formula,
            ok=(rel <= 1.0), nota=nota,
        )


@dataclass
class ResultadoShearTab:
    ok:                  bool
    relacion_max:        float
    verificacion_critica: str
    verificaciones:      List[Verificacion]
    mensajes:            List[dict] = field(default_factory=list)
    # Datos calculados internos (para PDF/DXF)
    Lp:                  float = 0.0   # Longitud de plancha [mm]
    Ab:                  float = 0.0   # Área nominal perno [mm²]
    d_agujero:           float = 0.0   # Diámetro agujero [mm]
    Fnv:                 float = 0.0   # Resistencia corte perno [MPa]


# ── Motor de cálculo ──────────────────────────────────────────────────────────

class ShearTab:
    """Motor de cálculo para unión apernada a corte (Shear Tab)."""

    def calcular(self, datos: EntradaShearTab) -> ResultadoShearTab:
        norma   = get_norma(datos.norma)
        pernos  = datos.pernos
        plancha = datos.plancha
        viga    = datos.viga
        sold    = datos.soldadura

        acero_p = ACEROS[plancha.acero]
        acero_v = ACEROS[viga.acero]
        electrodo = ELECTRODOS[sold.electrodo]
        tipo_p  = PERNOS[pernos.tipo]

        Vu_N    = datos.Vu * 1000          # kN → N
        phi_v   = norma.phi_aplastamiento  # 0.75
        phi_s   = norma.phi_soldadura      # 0.75

        verificaciones: List[Verificacion] = []

        # Geometría auxiliar
        Lp       = (pernos.n - 1) * pernos.p + 2 * pernos.e1
        Ab       = area_perno_nominal(pernos.db)
        d_ag     = diametro_agujero_estandar(pernos.db)
        Fnv      = Fnv_perno(pernos.tipo, pernos.hilos_en_plano)

        # ── 1. Corte en pernos (AISC J3.6) ───────────────────────────────────
        phi_Rn_pernos = phi_v * Fnv * Ab * pernos.n_corte * pernos.n
        verificaciones.append(Verificacion.crear(
            "Corte en pernos", "AISC 360-22 J3.6",
            Vu_N, phi_Rn_pernos,
            f"φRn = φ·Fnv·Ab·n_corte·n = 0.75 × {Fnv:.0f} × {Ab:.0f} × {pernos.n_corte} × {pernos.n}",
        ))

        # ── 2. Aplastamiento en plancha (AISC J3.10) ─────────────────────────
        Lc_borde_p = pernos.e2 - d_ag / 2
        Lc_inter_p = pernos.p  - d_ag
        Rn_b_p = min(1.2 * Lc_borde_p * plancha.tp * acero_p.Fu,
                     2.4 * pernos.db  * plancha.tp * acero_p.Fu)
        Rn_i_p = min(1.2 * Lc_inter_p * plancha.tp * acero_p.Fu,
                     2.4 * pernos.db  * plancha.tp * acero_p.Fu)
        phi_Rn_aplast_p = phi_v * (Rn_b_p + max(pernos.n - 1, 0) * Rn_i_p)
        verificaciones.append(Verificacion.crear(
            "Aplastamiento en plancha", "AISC 360-22 J3.10",
            Vu_N, phi_Rn_aplast_p,
            "φRn = φ·[1.2·Lc·t·Fu ≤ 2.4·db·t·Fu] por perno",
        ))

        # ── 3. Aplastamiento en alma de viga (AISC J3.10) ────────────────────
        Lc_borde_v = pernos.e2 - d_ag / 2
        Rn_b_v = min(1.2 * Lc_borde_v * viga.tw * acero_v.Fu,
                     2.4 * pernos.db  * viga.tw * acero_v.Fu)
        Rn_i_v = min(1.2 * Lc_inter_p * viga.tw * acero_v.Fu,
                     2.4 * pernos.db  * viga.tw * acero_v.Fu)
        phi_Rn_aplast_v = phi_v * (Rn_b_v + max(pernos.n - 1, 0) * Rn_i_v)
        verificaciones.append(Verificacion.crear(
            "Aplastamiento en alma de viga", "AISC 360-22 J3.10",
            Vu_N, phi_Rn_aplast_v,
            f"Igual plancha pero tw={viga.tw}mm, Fu={acero_v.Fu}MPa",
        ))

        # ── 4. Desgarro en bloque — plancha (AISC J4.3) ──────────────────────
        Anv_p = plancha.tp * (Lp - pernos.n * d_ag)
        Ant_p = plancha.tp * (pernos.e2 - d_ag / 2)
        Agv_p = plancha.tp * Lp
        Ubs   = 1.0  # tracción uniforme
        phi_Rn_bs_p = phi_v * min(
            0.60 * acero_p.Fu * Anv_p + Ubs * acero_p.Fu * Ant_p,
            0.60 * acero_p.Fy * Agv_p + Ubs * acero_p.Fu * Ant_p,
        )
        verificaciones.append(Verificacion.crear(
            "Desgarro en bloque — plancha", "AISC 360-22 J4.3",
            Vu_N, phi_Rn_bs_p,
            "φRn = φ·[0.60·Fu·Anv + Ubs·Fu·Ant] ≤ φ·[0.60·Fy·Agv + Ubs·Fu·Ant]",
        ))

        # ── 5. Corte en plancha — bruta y neta (AISC J4.4) ───────────────────
        Anv_plan = plancha.tp * (Lp - pernos.n * d_ag)
        phi_Vn_bruta = 1.00 * 0.60 * acero_p.Fy * plancha.tp * Lp
        phi_Vn_neta  = phi_v * 0.60 * acero_p.Fu * Anv_plan
        phi_Vn_plan  = min(phi_Vn_bruta, phi_Vn_neta)
        verificaciones.append(Verificacion.crear(
            "Corte en plancha", "AISC 360-22 J4.4",
            Vu_N, phi_Vn_plan,
            f"min(φ·0.60·Fy·Agv; φ·0.60·Fu·Anv) = min({phi_Vn_bruta/1000:.1f}; {phi_Vn_neta/1000:.1f}) kN",
        ))

        # ── 6. Soldadura plancha-columna (AISC J2.4) ─────────────────────────
        # Carga excéntrica → ángulo resultante ≈ vertical
        a_sold   = 0.707 * sold.w          # garganta efectiva [mm]
        L_sold   = sold.lados * Lp          # longitud total soldadura
        theta    = 90.0                     # carga perp. al eje de sold.
        f_dir    = 1.0 + 0.50 * math.sin(math.radians(theta)) ** 1.5  # = 1.50
        Fw       = 0.60 * electrodo.FEXX * f_dir
        phi_Rn_sold = phi_s * Fw * a_sold * L_sold
        verificaciones.append(Verificacion.crear(
            "Soldadura plancha-columna", "AISC 360-22 J2.4",
            Vu_N, phi_Rn_sold,
            f"φRn = φ·0.60·FEXX·(1+0.5·sin¹·⁵θ)·a·L = 0.75×0.60×{electrodo.FEXX}×1.50×{a_sold:.2f}×{L_sold:.0f}",
        ))

        # ── Verificaciones geométricas mínimas (no dimensionales) ─────────────
        s_min = norma.espaciado_min_factor * pernos.db
        mensajes = []
        if pernos.p < s_min:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"Separación entre pernos p={pernos.p}mm < mínimo {s_min:.0f}mm ({norma.nombre})"})
        if pernos.e1 < 1.5 * pernos.db:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"Distancia al borde e1={pernos.e1}mm < 1.5·db={1.5*pernos.db:.0f}mm (AISC Tabla J3.4)"})
        if pernos.e2 < 1.5 * pernos.db:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"Distancia al borde e2={pernos.e2}mm < 1.5·db={1.5*pernos.db:.0f}mm (AISC Tabla J3.4)"})

        # Tamaño mínimo de soldadura (AISC Tabla J2.4)
        w_min = _w_min_filete(max(plancha.tp, viga.tw))
        if sold.w < w_min:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"Filete w={sold.w}mm < mínimo {w_min}mm para t={max(plancha.tp,viga.tw):.0f}mm (AISC Tabla J2.4)"})

        # ── Resumen ───────────────────────────────────────────────────────────
        ok      = all(v.ok for v in verificaciones)
        rel_max = max(v.relacion for v in verificaciones)
        critica = next(v.nombre for v in verificaciones if v.relacion == rel_max)

        if ok:
            mensajes.append({"tipo": "ok",
                             "texto": f"Conexión CONFORME — ratio máximo {rel_max:.3f} ✓"})
        else:
            mensajes.append({"tipo": "error",
                             "texto": f"Conexión NO CONFORME — ratio máximo {rel_max:.3f} en: {critica}"})

        return ResultadoShearTab(
            ok=ok,
            relacion_max=round(rel_max, 4),
            verificacion_critica=critica,
            verificaciones=verificaciones,
            mensajes=mensajes,
            Lp=Lp, Ab=round(Ab, 2),
            d_agujero=round(d_ag, 1),
            Fnv=Fnv,
        )


def _w_min_filete(t_max_mm: float) -> float:
    """Tamaño mínimo de filete según AISC Tabla J2.4."""
    if t_max_mm <= 6:  return 3.0
    if t_max_mm <= 13: return 5.0
    if t_max_mm <= 19: return 6.0
    return 8.0
