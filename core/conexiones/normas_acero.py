"""
ESCALC — Motor de Normas para Conexiones en Acero.

Factores de resistencia (φ) y parámetros normativos por país.
Referencia principal: AISC 360-22 Capítulo J.
"""
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class NormaAcero:
    """Factores de diseño para conexiones en acero según norma."""
    codigo:     str
    nombre:     str
    pais:       str
    sistema:    str   # "LRFD" | "ASD"

    # Factores φ (LRFD) — o equivalentes 1/Ω para ASD
    phi_flexion:      float = 0.90
    phi_cortante:     float = 0.75
    phi_fluencia:     float = 0.90
    phi_traccion:     float = 0.75
    phi_compresion:   float = 0.90
    phi_aplastamiento: float = 0.75
    phi_soldadura:    float = 0.75

    # Espaciado mínimo entre pernos [múltiplo de db]
    espaciado_min_factor: float = 2.67   # AISC: 2.67db | CIRSOC/EC3: 3.0db

    # Referencia normativa
    referencia: str = ""


# ── Instancias de normas disponibles ─────────────────────────────────────────

NORMAS_ACERO: dict[str, NormaAcero] = {

    "AISC360": NormaAcero(
        codigo="AISC360",
        nombre="AISC 360-22",
        pais="USA / Internacional",
        sistema="LRFD",
        phi_flexion=0.90,
        phi_cortante=0.75,
        phi_fluencia=0.90,
        phi_traccion=0.75,
        phi_compresion=0.90,
        phi_aplastamiento=0.75,
        phi_soldadura=0.75,
        espaciado_min_factor=2.67,
        referencia="AISC 360-22 Cap. J",
    ),

    "CIRSOC301": NormaAcero(
        codigo="CIRSOC301",
        nombre="CIRSOC 301-2005",
        pais="Argentina",
        sistema="LRFD",
        phi_flexion=0.90,
        phi_cortante=0.75,
        phi_fluencia=0.90,
        phi_traccion=0.75,
        phi_compresion=0.90,
        phi_aplastamiento=0.75,
        phi_soldadura=0.75,
        espaciado_min_factor=3.0,   # CIRSOC: 3db
        referencia="CIRSOC 301-2005 Cap. 9",
    ),

    "EC3": NormaAcero(
        codigo="EC3",
        nombre="Eurocódigo 3 — EN 1993-1-8",
        pais="España / Europa",
        sistema="LRFD",
        phi_flexion=1.0 / 1.00,    # γM0=1.00
        phi_cortante=1.0 / 1.25,   # γM2=1.25 → φ=0.80
        phi_fluencia=1.0 / 1.00,
        phi_traccion=1.0 / 1.25,
        phi_compresion=1.0 / 1.00,
        phi_aplastamiento=1.0 / 1.25,
        phi_soldadura=1.0 / 1.25,
        espaciado_min_factor=3.0,
        referencia="EN 1993-1-8:2005 §3 y §4",
    ),

    "NSR10": NormaAcero(
        codigo="NSR10",
        nombre="NSR-10 Título F",
        pais="Colombia",
        sistema="LRFD",
        phi_flexion=0.90,
        phi_cortante=0.75,
        phi_fluencia=0.90,
        phi_traccion=0.75,
        phi_compresion=0.90,
        phi_aplastamiento=0.75,
        phi_soldadura=0.75,
        espaciado_min_factor=2.67,
        referencia="NSR-10 F.4",
    ),

    "NCH427": NormaAcero(
        codigo="NCH427",
        nombre="NCh 427 Of.2000",
        pais="Chile",
        sistema="LRFD",
        phi_flexion=0.90,
        phi_cortante=0.75,
        phi_fluencia=0.90,
        phi_traccion=0.75,
        phi_compresion=0.90,
        phi_aplastamiento=0.75,
        phi_soldadura=0.75,
        espaciado_min_factor=3.0,
        referencia="NCh 427 Of.2000 + NCh 2369",
    ),
}


def get_norma(codigo: str) -> NormaAcero:
    """Retorna la norma por código, AISC360 como default."""
    return NORMAS_ACERO.get(codigo, NORMAS_ACERO["AISC360"])


# ── Coeficiente βw para soldaduras EC3 ───────────────────────────────────────

BETA_W_EC3 = {
    "S235": 0.80,
    "S275": 0.85,
    "S355": 0.90,
    "S420": 1.00,
    "S460": 1.00,
}


def beta_w_ec3(acero: str) -> float:
    return BETA_W_EC3.get(acero, 1.00)
