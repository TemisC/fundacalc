"""
ESCALC — Base de datos de materiales para conexiones en acero.
Aceros estructurales, pernos y electrodos.
Fuente: AISC 360-22, CIRSOC 301-2005, EC3, NSR-10, NCh 427.
"""
import math
from dataclasses import dataclass
from typing import Optional


# ── Aceros estructurales ──────────────────────────────────────────────────────

@dataclass
class AceroEstructural:
    codigo:  str
    nombre:  str
    Fy:      float   # Tensión de fluencia [MPa]
    Fu:      float   # Tensión de rotura [MPa]
    E:       float   # Módulo de elasticidad [MPa]
    norma:   str     # Norma de referencia


ACEROS: dict[str, AceroEstructural] = {
    # ASTM (USA / Latinoamérica)
    "A36":      AceroEstructural("A36",      "ASTM A36",              Fy=250, Fu=400, E=200000, norma="ASTM"),
    "A572-50":  AceroEstructural("A572-50",  "ASTM A572 Gr.50",       Fy=345, Fu=450, E=200000, norma="ASTM"),
    "A572-60":  AceroEstructural("A572-60",  "ASTM A572 Gr.60",       Fy=415, Fu=520, E=200000, norma="ASTM"),
    "A992":     AceroEstructural("A992",     "ASTM A992 (perfiles W)", Fy=345, Fu=450, E=200000, norma="ASTM"),
    "A500-B":   AceroEstructural("A500-B",   "ASTM A500 Gr.B (HSS)",   Fy=317, Fu=400, E=200000, norma="ASTM"),
    "A500-C":   AceroEstructural("A500-C",   "ASTM A500 Gr.C (HSS)",   Fy=345, Fu=427, E=200000, norma="ASTM"),
    # Eurocódigo 3
    "S235":     AceroEstructural("S235",     "EN S235 (EC3)",          Fy=235, Fu=360, E=210000, norma="EC3"),
    "S275":     AceroEstructural("S275",     "EN S275 (EC3)",          Fy=275, Fu=430, E=210000, norma="EC3"),
    "S355":     AceroEstructural("S355",     "EN S355 (EC3)",          Fy=355, Fu=510, E=210000, norma="EC3"),
    # CIRSOC / Argentina
    "F-24":     AceroEstructural("F-24",     "IRAM F-24 (CIRSOC)",     Fy=235, Fu=370, E=200000, norma="CIRSOC"),
    "F-36":     AceroEstructural("F-36",     "IRAM F-36 (CIRSOC)",     Fy=355, Fu=510, E=200000, norma="CIRSOC"),
    # Chile
    "A37-24ES": AceroEstructural("A37-24ES", "A37-24ES (NCh)",         Fy=235, Fu=370, E=200000, norma="NCh"),
    "A52-36ES": AceroEstructural("A52-36ES", "A52-36ES (NCh)",         Fy=355, Fu=510, E=200000, norma="NCh"),
}


# ── Pernos estructurales ──────────────────────────────────────────────────────

@dataclass
class TipoPerno:
    codigo:         str
    nombre:         str
    Fnt:            float   # Resistencia a tracción nominal [MPa]
    Fnv_X:          float   # Resistencia a corte sin hilos en plano [MPa]
    Fnv_N:          float   # Resistencia a corte con hilos en plano [MPa]
    Futa:           float   # Resistencia última para anclaje [MPa]
    pretensado:     bool    # ¿requiere pretensado?
    norma:          str


PERNOS: dict[str, TipoPerno] = {
    "A307":     TipoPerno("A307",    "ASTM A307 (perno ordinario)",              Fnt=310, Fnv_X=165, Fnv_N=165, Futa=414,  pretensado=False, norma="ASTM"),
    "A325-X":   TipoPerno("A325-X",  "A325 / F3125-A325 (sin hilos en plano)",   Fnt=620, Fnv_X=372, Fnv_N=310, Futa=724,  pretensado=True,  norma="ASTM"),
    "A325-N":   TipoPerno("A325-N",  "A325 / F3125-A325 (con hilos en plano)",   Fnt=620, Fnv_X=372, Fnv_N=310, Futa=724,  pretensado=True,  norma="ASTM"),
    "A490-X":   TipoPerno("A490-X",  "A490 / F3125-A490 (sin hilos en plano)",   Fnt=780, Fnv_X=457, Fnv_N=372, Futa=1000, pretensado=True,  norma="ASTM"),
    "A490-N":   TipoPerno("A490-N",  "A490 / F3125-A490 (con hilos en plano)",   Fnt=780, Fnv_X=457, Fnv_N=372, Futa=1000, pretensado=True,  norma="ASTM"),
    "ISO-4.6":  TipoPerno("ISO-4.6", "ISO 898-1 Clase 4.6",                      Fnt=240, Fnv_X=144, Fnv_N=144, Futa=400,  pretensado=False, norma="ISO"),
    "ISO-8.8":  TipoPerno("ISO-8.8", "ISO 898-1 Clase 8.8 (equiv. A325)",        Fnt=560, Fnv_X=336, Fnv_N=280, Futa=800,  pretensado=True,  norma="ISO"),
    "ISO-10.9": TipoPerno("ISO-10.9","ISO 898-1 Clase 10.9 (equiv. A490)",       Fnt=700, Fnv_X=420, Fnv_N=350, Futa=1000, pretensado=True,  norma="ISO"),
}

# Pretensado mínimo [kN] — AISC Tabla J3.1
PRETENSADO_MIN: dict[str, dict[int, float]] = {
    "A325": {16: 71, 19: 91, 22: 110, 24: 125, 27: 146, 30: 176},
    "A490": {16: 89, 19: 114, 22: 138, 24: 157, 27: 184, 30: 220},
}

# Diámetros comerciales [mm]
DIAMETROS_PERNOS = [12, 14, 16, 19, 20, 22, 24, 27, 30, 33, 36]


def area_perno_nominal(db_mm: float) -> float:
    """Área nominal del perno [mm²]."""
    return math.pi * (db_mm / 2) ** 2


def area_raiz_rosca(db_mm: float) -> float:
    """Área de la raíz de la rosca ≈ 0.75×Ab [mm²]."""
    return 0.75 * area_perno_nominal(db_mm)


def diametro_agujero_estandar(db_mm: float) -> float:
    """Diámetro de agujero estándar = db + 1.6mm (AISC J3.3)."""
    return db_mm + 1.6


def Fnv_perno(tipo: str, hilos_en_plano: bool = False) -> float:
    """Resistencia nominal a corte del perno [MPa]."""
    p = PERNOS[tipo]
    return p.Fnv_N if hilos_en_plano else p.Fnv_X


# ── Electrodos de soldadura ───────────────────────────────────────────────────

@dataclass
class Electrodo:
    codigo:  str
    nombre:  str
    FEXX:    float   # Resistencia nominal del electrodo [MPa]
    proceso: str


ELECTRODOS: dict[str, Electrodo] = {
    "E60":   Electrodo("E60",   "E6010 / E6013 (SMAW)",           FEXX=414, proceso="SMAW"),
    "E70":   Electrodo("E70",   "E7018 / E71T-1 — más común",     FEXX=482, proceso="SMAW/FCAW"),
    "E80":   Electrodo("E80",   "E80XX (alta resistencia)",        FEXX=552, proceso="SMAW"),
    "ER70S": Electrodo("ER70S", "ER70S-X (GMAW/GTAW)",            FEXX=482, proceso="GMAW"),
}
