"""
ESCALC Wind — ASCE 7-22 Tables & Analytical Equations
Official values from ASCE/SEI 7-22 and Commentary (Tables C30.3-x).
"""
import math

# Table 26.11-1 — Terrain Exposure Constants (ASCE 7-22)
# NOTE: zg for Exposure C = 2,460 ft (not 900 ft from older editions)
EXPOSURE_CONSTANTS = {
    'B': {'alpha': 7.5,  'zg': 3280, 'c': 0.30, 'l': 320,  'epsilon': 0.3333, 'Zmin': 30, 'b': 0.84},
    'C': {'alpha': 9.8,  'zg': 2460, 'c': 0.20, 'l': 500,  'epsilon': 0.2000, 'Zmin': 15, 'b': 1.00},
    'D': {'alpha': 11.5, 'zg': 1935, 'c': 0.15, 'l': 650,  'epsilon': 0.1250, 'Zmin': 7,  'b': 1.09},
}

# Table 26.13-1 — Internal Pressure Coefficient GCpi
GCpi_TABLE = {
    'Enclosed':       0.18,
    'Partially Open': 0.55,
    'Open':           0.00,
}


# ── Analytical GCp Equations (ASCE 7-22 Commentary Tables C30.3-x) ──────────

def GCp_wall(area_ft2: float, zone: int) -> tuple:
    """
    Table C30.3-1 — Walls h ≤ 60 ft (Figure 30.3-1).
    Returns (GCpd, GCpu). Zone 4 = interior, Zone 5 = corner.
    """
    A = max(10.0, area_ft2)
    # Positive (same for zones 4 and 5)
    if A <= 10:        GCpd = 1.0
    elif A <= 500:     GCpd = 1.1766 - 0.1766 * math.log10(A)
    else:              GCpd = 0.7

    if zone == 4:
        if A <= 10:    GCpu = -1.1
        elif A <= 500: GCpu = -1.2766 + 0.1766 * math.log10(A)
        else:          GCpu = -0.8
    else:  # zone 5
        if A <= 10:    GCpu = -1.4
        elif A <= 500: GCpu = -1.5766 + 0.1766 * math.log10(A)
        else:          GCpu = -1.0

    return GCpd, GCpu


def GCp_hip_roof_7_20(area_ft2: float, zone: int) -> tuple:
    """
    Table C30.3-6 — Hip Roofs 7° < θ ≤ 20° (Figure 30.3-2E).
    Applies to the Florida reference project (θ = 10.78°).
    Verification: area=182.68 ft², zone=1 → GCpd=0.30, GCpu=-0.83 ✓
    """
    A = area_ft2
    if A <= 10:        GCpd = 0.7
    elif A <= 100:     GCpd = 1.100 - 0.400 * math.log10(A)
    else:              GCpd = 0.3

    if zone == 1:
        if A <= 10:    GCpu = -1.8
        elif A <= 200: GCpu = -2.5686 + 0.7686 * math.log10(A)
        else:          GCpu = -0.8
    elif zone == 2:
        if A <= 10:    GCpu = -2.4
        elif A <= 200: GCpu = -3.2455 + 0.8455 * math.log10(A)
        else:          GCpu = -1.3
    else:  # zone 3
        if A <= 10:    GCpu = -2.6
        elif A <= 200: GCpu = -3.5224 + 0.9223 * math.log10(A)
        else:          GCpu = -1.4

    return GCpd, GCpu


def GCp_gable_roof_7_20(area_ft2: float, zone: int) -> tuple:
    """
    Table C30.3-3 — Gable Roofs 7° < θ ≤ 20° (Figure 30.3-2B).
    Also used for Shed roofs (conservative).
    """
    A = area_ft2
    if A <= 10:        GCpd = 0.6
    elif A <= 200:     GCpd = 0.8306 - 0.2306 * math.log10(A)
    else:              GCpd = 0.3

    if zone == 1:
        if A <= 10:    GCpu = -2.0
        elif A <= 300: GCpu = -3.0155 + 1.0155 * math.log10(A)
        else:          GCpu = -0.5
    elif zone == 2:
        if A <= 10:    GCpu = -2.7
        elif A <= 200: GCpu = -4.0067 + 1.3066 * math.log10(A)
        else:          GCpu = -1.0
    else:  # zone 3
        if A <= 10:    GCpu = -3.6
        elif A <= 100: GCpu = -5.400 + 1.800 * math.log10(A)
        else:          GCpu = -1.8

    return GCpd, GCpu


def GCp_flat_low_roof(area_ft2: float, zone: int) -> tuple:
    """
    Table C30.3-2 — Flat Roofs / θ ≤ 7° (Figure 30.3-2A).
    """
    A = area_ft2
    GCpd = 0.3
    if zone == 1:
        if A <= 10:    GCpu = -1.0
        elif A <= 500: GCpu = -1.0 - 0.7 * (math.log10(A) / math.log10(500))
        else:          GCpu = -1.0
    elif zone == 2:
        if A <= 10:    GCpu = -2.3
        elif A <= 500: GCpu = -3.0063 + 0.7063 * math.log10(A)
        else:          GCpu = -1.1
    else:  # zone 3
        if A <= 10:    GCpu = -3.2
        elif A <= 500: GCpu = -4.4360 + 1.2360 * math.log10(A)
        else:          GCpu = -1.1

    return GCpd, GCpu


def get_GCp_roof(area_ft2: float, zone: int, theta_deg: float,
                 roof_type: str = 'Hipped') -> tuple:
    """
    Selects the correct ASCE 7-22 GCp roof equation based on type and slope.
    """
    if roof_type == 'Flat' or theta_deg <= 7.0:
        return GCp_flat_low_roof(area_ft2, zone)
    elif roof_type == 'Hipped':
        return GCp_hip_roof_7_20(area_ft2, zone)
    else:  # Gable, Shed
        return GCp_gable_roof_7_20(area_ft2, zone)
