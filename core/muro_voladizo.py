"""
Módulo 9.1 — Muro en Voladizo (L invertida).

Verificaciones de estabilidad (por metro lineal de muro):
  · Vuelco          FS_v ≥ 2.0
  · Deslizamiento   FS_d ≥ 1.5
  · Presión base    q_max ≤ qa
  · Excentricidad   |e| ≤ B/6

Diseño RC (ACI 318-19):
  · Fuste  — voladizo vertical cargado por empuje activo
  · Punta  — voladizo horizontal, presión neta hacia arriba
  · Talón  — voladizo horizontal, carga neta hacia abajo
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple

# ── Tabla de barras métricas ─────────────────────────────────────────────────
_BARRAS: List[Tuple[str, float, float]] = [
    # (nombre, db [mm], Ab [mm²])
    ("∅8",   8.0,   50.3),
    ("∅10", 10.0,   78.5),
    ("∅12", 12.0,  113.1),
    ("∅16", 16.0,  201.1),
    ("∅20", 20.0,  314.2),
    ("∅25", 25.0,  490.9),
    ("∅32", 32.0,  804.2),
]
_SEPARACIONES = [100, 125, 150, 175, 200, 225, 250, 300]  # [mm]


def _seleccionar_barra(As_req_cm2_m: float) -> Tuple[str, float]:
    """Dado As requerido [cm²/m], devuelve (etiqueta, As_dis [cm²/m])."""
    As_req = max(As_req_cm2_m, 0.01) * 100  # → mm²/m
    for nombre, db, Ab in _BARRAS:
        for s in _SEPARACIONES:
            As_dis = Ab / s * 1000  # mm²/m
            if As_dis >= As_req and s >= 100:
                label = f"{nombre} c/{s//10}cm"
                return label, As_dis / 100
    # fallback ∅32@100
    return "∅32 c/10cm", 804.2 / 100 * 1000 / 100


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class ResultadoEstabilidad:
    Ka: float
    Ea_gamma: float   # empuje triangular    [kN/m]
    Ea_q:     float   # empuje por sobrecarga [kN/m]
    Ea:       float   # empuje total          [kN/m]
    Mo:       float   # momento volcador sobre punta [kN.m/m]

    W_fuste:       float  # peso fuste            [kN/m]
    W_zapata:      float  # peso zapata            [kN/m]
    W_talon_soil:  float  # peso suelo sobre talón [kN/m]
    W_q_talon:     float  # peso sobrecarga talón  [kN/m]
    W_total:       float  # ΣW                     [kN/m]
    Mr:            float  # momento resistente sobre punta [kN.m/m]

    x_R:   float  # posición resultante desde punta [m]
    e:     float  # excentricidad                   [m]
    B_total: float

    q_max: float   # presión máx en punta [kPa]
    q_min: float   # presión mín en talón [kPa]

    Ep:        float  # empuje pasivo en punta [kN/m]
    FS_vuelco: float
    FS_desliz: float

    ok_vuelco:       bool
    ok_desliz:       bool
    ok_presion:      bool
    ok_excentricidad: bool
    ok_global:       bool


@dataclass
class ElementoRC:
    nombre: str
    Mu:     float   # momento último [kN.m/m]
    d:      float   # peralte efectivo [m]
    As_req: float   # área requerida [cm²/m]
    As_min: float   # área mínima ACI [cm²/m]
    As_dis: float   # área diseñada [cm²/m]
    barra:  str     # etiqueta barra + separación


@dataclass
class ResultadosMuro:
    # Entrada derivada
    H:       float   # altura total retenida [m]
    h_fuste: float   # altura fuste [m]
    B_total: float   # ancho total zapata [m]
    Ka:      float

    estabilidad: ResultadoEstabilidad
    fuste:       ElementoRC
    punta:       ElementoRC
    talon:       ElementoRC
    As_temp:     float   # acero temperatura fuste [cm²/m de altura, por cara]
    barra_temp:  str

    mensajes: List[dict] = field(default_factory=list)


# ── Motor ─────────────────────────────────────────────────────────────────────

class MuroVoladizo:

    def calcular(
        self,
        # Geometría
        H:        float,   # Altura total retenida: base de zapata → corona [m]
        h_zapata: float,   # Espesor de la zapata [m]
        b_base:   float,   # Ancho del fuste en la base [m]
        b_corona: float,   # Ancho del fuste en la corona [m]
        B_punta:  float,   # Proyección de la punta (toe) [m]
        B_talon:  float,   # Proyección del talón (heel) [m]
        # Suelo retenido
        gamma_r: float,    # Peso unitario suelo retenido [kN/m³]
        phi_r:   float,    # Fricción suelo retenido [°]
        c_r:     float,    # Cohesión suelo retenido [kPa]
        q_s:     float,    # Sobrecarga en superficie [kPa]
        # Suelo de fundación
        gamma_f: float,    # Peso unitario suelo fundación [kN/m³]
        phi_f:   float,    # Fricción suelo fundación [°]
        c_f:     float,    # Cohesión suelo fundación [kPa]
        qa:      float,    # Presión admisible [kPa]
        # Hormigón y acero
        gamma_c: float = 24.0,
        fc:      float = 25.0,   # [MPa]
        fy:      float = 420.0,  # [MPa]
        recub:   float = 0.07,   # [m]
        # Interfaz base
        delta_factor: float = 0.667,  # δ = δ_factor × φ_f
    ) -> "MuroVoladizo":

        mensajes: List[dict] = []

        # ── Geometría derivada ────────────────────────────────────────────
        h_fuste = H - h_zapata
        b_avg   = (b_base + b_corona) / 2
        B_total = B_punta + b_base + B_talon

        if h_fuste <= 0:
            raise ValueError("h_zapata debe ser menor que H")
        if B_total <= 0:
            raise ValueError("Ancho total de zapata inválido")

        # ── Presión activa de Rankine ─────────────────────────────────────
        phi_r_rad = math.radians(phi_r)
        Ka = math.tan(math.radians(45 - phi_r / 2)) ** 2
        Ea_gamma = 0.5 * Ka * gamma_r * H ** 2
        Ea_q     = Ka * q_s * H
        Ea       = Ea_gamma + Ea_q

        Mo = Ea_gamma * (H / 3) + Ea_q * (H / 2)

        # ── Pesos y brazos desde la punta (toe) ──────────────────────────
        W_fuste      = gamma_c * b_avg * h_fuste
        x_fuste      = B_punta + b_avg / 2

        W_zapata     = gamma_c * B_total * h_zapata
        x_zapata     = B_total / 2

        W_talon_soil = gamma_r * B_talon * h_fuste
        x_talon      = B_punta + b_base + B_talon / 2

        W_q_talon    = q_s * B_talon
        # arm igual al suelo del talón

        W_total = W_fuste + W_zapata + W_talon_soil + W_q_talon

        Mr = (W_fuste * x_fuste
              + W_zapata * x_zapata
              + W_talon_soil * x_talon
              + W_q_talon * x_talon)

        # ── FS vuelco ────────────────────────────────────────────────────
        FS_v = Mr / Mo if Mo > 1e-9 else 999.0

        # ── FS deslizamiento ─────────────────────────────────────────────
        phi_f_rad = math.radians(phi_f)
        Kp = math.tan(math.radians(45 + phi_f / 2)) ** 2
        Ep = 0.5 * Kp * gamma_f * h_zapata ** 2
        delta = delta_factor * phi_f_rad
        F_resist = W_total * math.tan(delta) + c_f * B_total + Ep
        FS_d = F_resist / Ea if Ea > 1e-9 else 999.0

        # ── Presión en la base ───────────────────────────────────────────
        x_R = (Mr - Mo) / W_total if W_total > 1e-9 else B_total / 2
        e   = B_total / 2 - x_R

        if abs(e) <= B_total / 6:
            q_max = (W_total / B_total) * (1 + 6 * e / B_total)
            q_min = (W_total / B_total) * (1 - 6 * e / B_total)
        else:
            q_max = 2 * W_total / (3 * max(x_R, 1e-6))
            q_min = 0.0

        ok_v = FS_v >= 2.0
        ok_d = FS_d >= 1.5
        ok_p = q_max <= qa
        ok_e = abs(e) <= B_total / 6
        ok_g = ok_v and ok_d and ok_p and ok_e

        estab = ResultadoEstabilidad(
            Ka=Ka, Ea_gamma=Ea_gamma, Ea_q=Ea_q, Ea=Ea, Mo=Mo,
            W_fuste=W_fuste, W_zapata=W_zapata,
            W_talon_soil=W_talon_soil, W_q_talon=W_q_talon,
            W_total=W_total, Mr=Mr,
            x_R=x_R, e=e, B_total=B_total,
            q_max=q_max, q_min=q_min, Ep=Ep,
            FS_vuelco=FS_v, FS_desliz=FS_d,
            ok_vuelco=ok_v, ok_desliz=ok_d,
            ok_presion=ok_p, ok_excentricidad=ok_e,
            ok_global=ok_g,
        )

        # ── Diseño RC ────────────────────────────────────────────────────
        phi_bend = 0.90

        def _as_req(Mu_kNm: float, d_m: float, b_mm: float = 1000) -> float:
            """Retorna As requerido [cm²/m]."""
            if Mu_kNm <= 0 or d_m <= 0:
                return 0.0
            d_mm = d_m * 1000
            Rn   = Mu_kNm * 1e6 / (phi_bend * b_mm * d_mm ** 2)
            disc = 1 - 2 * Rn / (0.85 * fc)
            if disc <= 0:
                disc = 1e-9
            rho  = 0.85 * fc / fy * (1 - math.sqrt(disc))
            return rho * b_mm * d_mm / 100  # cm²/m

        def _as_min_flex(d_m: float, b_mm: float = 1000) -> float:
            """As mín ACI 318 (flexión) [cm²/m]."""
            rho_min = max(0.25 * math.sqrt(fc) / fy, 1.4 / fy)
            return rho_min * b_mm * (d_m * 1000) / 100

        # Fuste — voladizo vertical, Mu en base del fuste
        Mu_fuste = 1.6 * (Ka * gamma_r * h_fuste**3 / 6
                          + Ka * q_s * h_fuste**2 / 2)
        db_asumida = 0.016  # ∅16 para estimación inicial de d
        d_fuste = max(b_base - recub - db_asumida / 2, 0.05)
        As_req_f = _as_req(Mu_fuste, d_fuste)
        As_min_f = max(_as_min_flex(d_fuste),
                       0.0018 * 1000 * (b_base * 1000) / 100)  # temp/shrinkage min
        As_f     = max(As_req_f, As_min_f)
        bar_f, As_dis_f = _seleccionar_barra(As_f)

        fuste_rc = ElementoRC("Fuste", Mu_fuste, d_fuste,
                               As_req_f, As_min_f, As_dis_f, bar_f)

        # Punta — voladizo horizontal, presión neta hacia arriba
        # Presión en punta: q_max (toe)
        # Presión en cara de fuste (x = B_punta desde toe):
        q_at_B_punta = q_max - (q_max - q_min) * B_punta / B_total
        q_punta_avg  = (q_max + q_at_B_punta) / 2
        w_slab_toe   = gamma_c * h_zapata
        q_net_punta  = max(q_punta_avg - w_slab_toe, 0.0)
        Mu_punta     = 1.6 * q_net_punta * B_punta**2 / 2
        d_punta      = max(h_zapata - recub - db_asumida / 2, 0.05)
        As_req_p     = _as_req(Mu_punta, d_punta)
        As_min_p     = max(_as_min_flex(d_punta),
                            0.0018 * 1000 * (h_zapata * 1000) / 100)
        As_p         = max(As_req_p, As_min_p)
        bar_p, As_dis_p = _seleccionar_barra(As_p)

        punta_rc = ElementoRC("Punta", Mu_punta, d_punta,
                               As_req_p, As_min_p, As_dis_p, bar_p)

        # Talón — voladizo horizontal, carga neta hacia abajo
        q_at_heel    = q_min  # presión bajo talón
        q_at_B_talon = q_min + (q_max - q_min) * (B_total - B_talon) / B_total
        q_talon_avg  = (q_at_heel + q_at_B_talon) / 2
        w_down_talon = (gamma_r * h_fuste + q_s + gamma_c * h_zapata)
        q_net_talon  = max(w_down_talon - q_talon_avg, 0.0)
        Mu_talon     = 1.6 * q_net_talon * B_talon**2 / 2
        d_talon      = d_punta  # mismo canto de zapata
        As_req_t     = _as_req(Mu_talon, d_talon)
        As_min_t     = As_min_p
        As_t         = max(As_req_t, As_min_t)
        bar_t, As_dis_t = _seleccionar_barra(As_t)

        talon_rc = ElementoRC("Talón", Mu_talon, d_talon,
                               As_req_t, As_min_t, As_dis_t, bar_t)

        # Acero temperatura / contracción en fuste (barras horizontales, por cara)
        As_temp_face = 0.0009 * (b_base * 1000) * 1000 / 100  # cm²/m de altura
        As_temp_face = max(As_temp_face, 2.0)  # mínimo práctico 2 cm²/m
        bar_temp, As_dis_temp = _seleccionar_barra(As_temp_face)

        # ── Mensajes ─────────────────────────────────────────────────────
        if not ok_v:
            mensajes.append({"tipo": "error",
                             "texto": f"Vuelco insuficiente: FS = {FS_v:.2f} < 2.0"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Vuelco: FS = {FS_v:.2f} ≥ 2.0 ✓"})

        if not ok_d:
            mensajes.append({"tipo": "error",
                             "texto": f"Deslizamiento insuficiente: FS = {FS_d:.2f} < 1.5"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Deslizamiento: FS = {FS_d:.2f} ≥ 1.5 ✓"})

        if not ok_p:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"q_max = {q_max:.1f} kPa supera qa = {qa:.1f} kPa"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Presión base: q_max = {q_max:.1f} kPa ≤ qa = {qa:.1f} kPa ✓"})

        if not ok_e:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"|e| = {abs(e):.3f} m > B/6 = {B_total/6:.3f} m — resultante fuera del tercio medio"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Excentricidad: |e| = {abs(e):.3f} m ≤ B/6 = {B_total/6:.3f} m ✓"})

        if c_r > 0:
            mensajes.append({"tipo": "advertencia",
                             "texto": "Cohesión activa (c > 0): se usa Rankine sin reducción por tracción"})

        self.res = ResultadosMuro(
            H=H, h_fuste=h_fuste, B_total=B_total, Ka=Ka,
            estabilidad=estab,
            fuste=fuste_rc, punta=punta_rc, talon=talon_rc,
            As_temp=As_temp_face, barra_temp=bar_temp,
            mensajes=mensajes,
        )
        # Guardar inputs para el reporte
        self._inp = dict(
            H=H, h_zapata=h_zapata, b_base=b_base, b_corona=b_corona,
            B_punta=B_punta, B_talon=B_talon,
            gamma_r=gamma_r, phi_r=phi_r, c_r=c_r, q_s=q_s,
            gamma_f=gamma_f, phi_f=phi_f, c_f=c_f, qa=qa,
            gamma_c=gamma_c, fc=fc, fy=fy, recub=recub,
            delta_factor=delta_factor,
        )
        return self
