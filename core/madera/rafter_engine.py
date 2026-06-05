# core/madera/rafter_engine.py
# ESCALC Wood — Motor de Cálculo NDS 2024
# Módulo: Roof Rafter Design (vigas de cubierta inclinadas)
# Norma: NDS 2024 (AWC/ANSI) + ASCE 7-22 (combinaciones de carga ASD)
# Engineering Software CALC — v1.0

import math
from dataclasses import dataclass, field
from typing import Optional
from core.madera.nds_data import NDS_SPECIES, ACTUAL_SIZES, DURATION_FACTORS


@dataclass
class RafterInputs:
    """Parámetros de entrada para el diseño del rafter."""
    # Geometría
    span_ft:       float   # Luz horizontal (ft) — de apoyo a apoyo
    slope_in_ft:   float   # Pendiente (in/ft) — ej: 6 = 6:12
    spacing_in:    float   # Separación entre rafters (in)
    cantilever_ft: float   # Voladizo (ft), 0 si no hay

    # Sección de madera (nominal)
    species:    str   # Clave de especie, ej: "spruce-pine-fir"
    grade:      str   # Grado visual: "no2", "no1", "select"
    width_nom:  int   # Ancho nominal (in): 2, 3, 4
    depth_nom:  int   # Peralte nominal (in): 6, 8, 10, 12

    # Cargas (psf sobre plano horizontal)
    dl_roofing: float   # Carga muerta cubierta (teja, OSB, etc.)
    dl_self:    float   # Peso propio del rafter estimado
    ll:         float   # Sobrecarga de uso / mantenimiento
    wl:         float   # Carga de viento (psf)
    sl:         float   # Carga de nieve (psf), 0 si no aplica

    # Factores de ajuste NDS
    cm: float = 1.0   # Factor de contenido de humedad (seco=1.0, húmedo=0.85)
    ct: float = 1.0   # Factor de temperatura (≤100°F=1.0)

    # Límite de deflexión
    deflection_limit: int = 360   # L/360 por defecto


@dataclass
class AdjustmentFactors:
    """Factores de ajuste NDS aplicados al cálculo."""
    CD:   float   # Duración de carga (NDS 2.3.2)
    CM:   float   # Contenido de humedad (NDS 4.3.3)
    Ct:   float   # Temperatura (NDS 2.3.3)
    CF_b: float   # Factor de forma para flexión (NDS Supp. 4A)
    CL:   float   # Estabilidad lateral (NDS 3.3.3) — 1.0 para rafters con forro
    Cr:   float   # Factor de miembro repetitivo (NDS 4.3.9)
    Ci:   float   # Factor de incisión (NDS 4.3.8) — 1.0 para madera no incisa
    CD_reason: str = ""   # Descripción de la carga gobernante


@dataclass
class RafterResults:
    """Resultados completos del cálculo NDS."""
    # Geometría calculada
    slope_angle_deg:   float
    slope_factor:      float   # longitud inclinada / luz horizontal
    rafter_length_ft:  float   # Longitud real del rafter (inclinada)
    tributary_width_ft: float  # Ancho tributario

    # Sección real (inches)
    b_in:     float   # Ancho real
    d_in:     float   # Peralte real
    area_in2: float
    S_in3:    float   # Módulo de sección
    I_in4:    float   # Momento de inercia

    # Cargas de diseño (lb/ft sobre longitud horizontal)
    w_DL:   float
    w_LL:   float
    w_WL:   float
    w_SL:   float
    w_total: float
    load_combo_governing: str

    # Solicitaciones
    M_max_ftlb: float   # Momento máximo (ft·lb)
    V_max_lb:   float   # Cortante máximo (lb)

    # Propiedades de referencia NDS (psi)
    Fb_ref: float
    Fv_ref: float
    E_ref:  float

    # Factores de ajuste
    factors: AdjustmentFactors

    # Resistencias ajustadas (psi)
    Fb_prime: float   # F'b = Fb × CD × CM × Ct × CF × CL × Cr
    Fv_prime: float   # F'v = Fv × CD × CM × Ct
    E_prime:  float   # E'  = E  × CM × Ct

    # Tensiones actuantes (psi)
    fb_actual: float
    fv_actual: float

    # Deflexión (in)
    delta_LL_in:    float
    delta_limit_in: float
    delta_ratio:    float

    # Relaciones de demanda/capacidad
    ratio_bending:    float
    ratio_shear:      float
    ratio_deflection: float

    # Verificación global
    bending_ok:    bool
    shear_ok:      bool
    deflection_ok: bool
    all_ok:        bool

    # Mensajes
    governing_check: str
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
        i = self.inp
        if not (4 <= i.span_ft <= 40):
            raise ValueError("Luz debe estar entre 4 y 40 ft")
        if not (1 <= i.slope_in_ft <= 24):
            raise ValueError("Pendiente entre 1:12 y 24:12")
        if i.spacing_in not in [12, 16, 19.2, 24]:
            raise ValueError("Separación típica: 12, 16, 19.2 ó 24 in")
        if i.species not in NDS_SPECIES:
            raise ValueError(f"Especie '{i.species}' no encontrada en tablas NDS")
        if i.grade not in NDS_SPECIES[i.species]:
            raise ValueError(f"Grado '{i.grade}' no disponible")
        if i.width_nom not in [2, 3, 4]:
            raise ValueError("Ancho nominal: 2, 3 ó 4 in")
        if i.depth_nom not in [6, 8, 10, 12]:
            raise ValueError("Peralte nominal: 6, 8, 10 ó 12 in")
        if not (0 <= i.cantilever_ft <= 4):
            raise ValueError("Voladizo máximo 4 ft")

    def _geometry(self):
        i = self.inp
        slope_ratio = i.slope_in_ft / 12.0
        angle_rad = math.atan(slope_ratio)
        slope_factor = math.sqrt(1 + slope_ratio**2)
        rafter_length = (i.span_ft + i.cantilever_ft) * slope_factor
        tributary_width = i.spacing_in / 12.0
        return angle_rad, slope_factor, rafter_length, tributary_width

    def _section_properties(self):
        i = self.inp
        b, d = ACTUAL_SIZES[str(i.width_nom)][str(i.depth_nom)]
        area = b * d
        S = (b * d**2) / 6.0
        I = (b * d**3) / 12.0
        return b, d, area, S, I

    def _load_combinations(self, tributary_ft: float):
        i = self.inp
        w_DL = (i.dl_roofing + i.dl_self) * tributary_ft
        w_LL = i.ll  * tributary_ft
        w_WL = i.wl  * tributary_ft
        w_SL = i.sl  * tributary_ft

        combos = {
            "D + L":                      w_DL + w_LL,
            "D + S":                      w_DL + w_SL,
            "D + W":                      w_DL + w_WL,
            "D + 0.75W + 0.75L + 0.75S":  w_DL + 0.75*w_WL + 0.75*w_LL + 0.75*w_SL,
        }
        governing = max(combos, key=combos.get)
        return w_DL, w_LL, w_WL, w_SL, combos[governing], governing

    def _duration_factor(self):
        i = self.inp
        if i.wl > 0 and i.wl >= i.ll and i.wl >= i.sl:
            return 1.6, "Viento (CD = 1.6)"
        elif i.sl > 0 and i.sl >= i.ll:
            return 1.15, "Nieve (CD = 1.15)"
        elif i.ll > 0:
            return 1.0, "Ocupación/Uso (CD = 1.0)"
        else:
            return 0.9, "Solo carga muerta (CD = 0.9)"

    def _form_factor_bending(self, d_in: float) -> float:
        """CF para flexión (NDS Sup. Table 4A)."""
        if d_in <= 8.0:
            return 1.2
        elif d_in <= 10.0:
            return 1.1
        else:
            return 1.0

    def _repetitive_factor(self) -> float:
        """Cr (NDS 4.3.9) — 1.15 para rafters con forro compartido."""
        return 1.15 if self.inp.spacing_in <= 24 else 1.0

    def calculate(self) -> RafterResults:
        i = self.inp

        # 1. Geometría
        angle_rad, slope_factor, rafter_length, tributary_ft = self._geometry()

        # 2. Sección
        b, d, area, S, I = self._section_properties()

        # 3. Propiedades NDS de referencia (psi)
        nds   = NDS_SPECIES[i.species][i.grade]
        Fb_ref = nds["Fb"]
        Fv_ref = nds["Fv"]
        E_ref  = nds["E"]

        # 4. Cargas y combinaciones
        w_DL, w_LL, w_WL, w_SL, w_total, combo_name = self._load_combinations(tributary_ft)

        # 5. Factores de ajuste
        CD, cd_reason = self._duration_factor()
        CF_b = self._form_factor_bending(d)
        Cr   = self._repetitive_factor()
        CM, Ct, CL, Ci = i.cm, i.ct, 1.0, 1.0

        factors = AdjustmentFactors(
            CD=CD, CM=CM, Ct=Ct, CF_b=CF_b, CL=CL, Cr=Cr, Ci=Ci,
            CD_reason=cd_reason,
        )

        # 6. Resistencias ajustadas
        Fb_prime = Fb_ref * CD * CM * Ct * CF_b * CL * Cr * Ci
        Fv_prime = Fv_ref * CD * CM * Ct
        E_prime  = E_ref  * CM * Ct

        # 7. Solicitaciones (viga simplemente apoyada)
        L = i.span_ft
        M_max_ftlb = (w_total * L**2) / 8.0
        V_max_lb   = (w_total * L) / 2.0

        # 8. Tensiones actuantes (psi)
        fb_actual = (M_max_ftlb * 12.0) / S        # ft·lb → in·lb
        fv_actual = (1.5 * V_max_lb) / (b * d)     # NDS 3.4.2 parabólica

        # 9. Deflexión por carga viva
        w_LL_inlb  = (i.ll * tributary_ft) / 12.0  # lb/in
        L_in       = L * 12.0                        # ft → in
        delta_LL   = (5 * w_LL_inlb * L_in**4) / (384 * E_prime * I)
        delta_limit = L_in / i.deflection_limit

        # 10. Relaciones D/C
        ratio_b = fb_actual / Fb_prime
        ratio_v = fv_actual / Fv_prime
        ratio_d = delta_LL / delta_limit if delta_limit > 0 else 999.0

        bending_ok    = ratio_b <= 1.0
        shear_ok      = ratio_v <= 1.0
        deflection_ok = ratio_d <= 1.0
        all_ok = bending_ok and shear_ok and deflection_ok

        # 11. Verificación gobernante
        governing_check = max(
            {"Flexión": ratio_b, "Corte": ratio_v, "Deflexión": ratio_d},
            key=lambda k: {"Flexión": ratio_b, "Corte": ratio_v, "Deflexión": ratio_d}[k]
        )

        # 12. Advertencias
        warnings = []
        if i.slope_in_ft < 3:
            warnings.append("Pendiente < 3:12 — verificar capacidad de drenaje.")
        if ratio_b > 0.9:
            warnings.append(f"Flexión al {ratio_b*100:.0f}% de capacidad — considerar aumentar peralte.")
        if ratio_d > 0.9:
            warnings.append("Deflexión próxima al límite — considerar L/240 para cargas totales.")
        if i.cantilever_ft > 0:
            warnings.append("Con voladizo: verificar momento negativo y detalle del apoyo.")

        return RafterResults(
            slope_angle_deg=math.degrees(angle_rad),
            slope_factor=slope_factor,
            rafter_length_ft=rafter_length,
            tributary_width_ft=tributary_ft,
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
