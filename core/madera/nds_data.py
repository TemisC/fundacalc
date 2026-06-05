# core/madera/nds_data.py
# Tablas NDS 2024 — Supplement Table 4A (Visually Graded Dimension Lumber)
# Propiedades de referencia en psi
# Engineering Software CALC — ESCALC Wood v1.0

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
    "dead":         0.9,
    "occupancy":    1.0,
    "snow":         1.15,
    "construction": 1.25,
    "wind_seismic": 1.6,
    "impact":       2.0,
}

# Factor de contenido de humedad CM (NDS Tabla 4.3.3 — dimension lumber)
MOISTURE_FACTORS = {
    "dry": {"Fb": 1.0, "Fv": 1.0, "E": 1.0},
    "wet": {"Fb": 0.85, "Fv": 0.97, "E": 0.9},
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
