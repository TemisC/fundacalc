"""
Módulo 9.5 — Muro de Sótano.

El muro es una losa vertical apoyada en la losa de techo (corona) y en la losa de piso (base).
No se verifican estabilidad global ni cimentación — las reacciones las absorben las losas.

Cargas:
  · Empuje activo Rankine (triangular + sobrecarga uniforme)
  · Presión hidrostática (si el NF está por encima de la base)

Condiciones de apoyo:
  'biapoyado'      — articulado en corona y en base
  'empotrado_base' — empotrado en la losa de piso, articulado en la losa de techo

Diseño RC (ACI 318-19):
  · Barras verticales (cara suelo)   — para M_max positivo (vano)
  · Barras verticales (cara interior) — para |M_base| negativo (empotramiento)
  · Barras horizontales               — acero de temperatura/contracción (ACI 11.6.1)
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple

_BARRAS: List[Tuple[str, float, float]] = [
    ("∅8",   8.0,   50.3),
    ("∅10", 10.0,   78.5),
    ("∅12", 12.0,  113.1),
    ("∅16", 16.0,  201.1),
    ("∅20", 20.0,  314.2),
    ("∅25", 25.0,  490.9),
    ("∅32", 32.0,  804.2),
]
_SEPARACIONES = [100, 125, 150, 175, 200, 225, 250, 300]


def _seleccionar_barra(As_req_cm2_m: float) -> Tuple[str, float]:
    As_req = max(As_req_cm2_m, 0.01) * 100
    for nombre, db, Ab in _BARRAS:
        for sep in _SEPARACIONES:
            As_dis = Ab / sep * 1000
            if As_dis >= As_req and sep >= 100:
                return f"{nombre} c/{sep//10}cm", As_dis / 100
    return "∅32 c/10cm", 804.2 / 100 * 1000 / 100


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class ResultadoCargas:
    Ka:             float
    pa_corona:      float   # presión activa en la corona [kPa]
    pa_base:        float   # presión activa en la base [kPa]
    pw_base:        float   # presión hidrostática en la base [kPa]
    p_total_base:   float   # presión total en la base [kPa]
    Ea:             float   # empuje activo total [kN/m]
    Ew:             float   # empuje hidrostático total [kN/m]
    E_total:        float   # fuerza horizontal total [kN/m]
    tiene_nf:       bool


@dataclass
class ResultadoMomentos:
    condicion:  str
    R_top:      float   # reacción en el apoyo superior [kN/m]
    R_bot:      float   # reacción en el apoyo inferior [kN/m]
    M_base:     float   # momento en la base [kN·m/m]  (neg = hogging para empotrado)
    M_max:      float   # momento máximo positivo en el vano [kN·m/m]
    z_max:      float   # profundidad donde ocurre M_max [m]
    M_corona:   float   # momento en la corona [kN·m/m] (0 si articulado)


@dataclass
class ElementoRC:
    nombre:  str
    Mu:      float   # [kN·m/m]
    d:       float   # peralte efectivo [m]
    As_req:  float   # [cm²/m]
    As_min:  float
    As_dis:  float
    barra:   str
    nota:    str = ""


@dataclass
class ResultadosMuroSotano:
    H:          float
    e_muro:     float
    h_NF:       float
    condicion:  str
    Ka:         float

    cargas:             ResultadoCargas
    momentos:           ResultadoMomentos
    vert_cara_suelo:    ElementoRC
    vert_cara_int:      ElementoRC
    horiz_temp:         ElementoRC

    mensajes: List[dict] = field(default_factory=list)


# ── Motor ─────────────────────────────────────────────────────────────────────

class MuroSotano:

    def calcular(
        self,
        H:          float,   # altura libre entre apoyos [m]
        e_muro:     float,   # espesor del muro [m]
        h_NF:       float,   # prof. del nivel freático desde la superficie [m]
        condicion:  str,     # 'biapoyado' | 'empotrado_base'
        # Suelo retenido
        phi_r:      float,
        c_r:        float,
        gamma_r:    float,
        q_s:        float,
        # Agua
        gamma_w:    float,
        # Materiales
        fc:         float,
        fy:         float,
        recub:      float,
        gamma_c:    float = 24.0,
    ) -> "MuroSotano":

        mensajes: List[dict] = []

        if H <= 0 or e_muro <= 0:
            raise ValueError("H y e_muro deben ser positivos")
        if condicion not in ('biapoyado', 'empotrado_base'):
            raise ValueError("condicion debe ser 'biapoyado' o 'empotrado_base'")

        # ── Presiones ────────────────────────────────────────────────────
        Ka       = math.tan(math.radians(45 - phi_r / 2)) ** 2
        pa_top   = Ka * q_s
        pa_bot   = Ka * (gamma_r * H + q_s)
        tiene_nf = h_NF < H
        h_w      = max(H - h_NF, 0.0)
        pw_bot   = gamma_w * h_w

        Ea = 0.5 * Ka * gamma_r * H ** 2 + Ka * q_s * H
        Ew = 0.5 * gamma_w * h_w ** 2

        cargas = ResultadoCargas(
            Ka=Ka, pa_corona=pa_top, pa_base=pa_bot,
            pw_base=pw_bot, p_total_base=pa_bot + pw_bot,
            Ea=Ea, Ew=Ew, E_total=Ea + Ew,
            tiene_nf=tiene_nf,
        )

        # ── Diagrama de momentos — integración numérica O(N) ─────────────
        # Coordenada z: 0 en la corona (techo), H en la base (piso).
        N   = 400
        dz  = H / N
        z_mid   = [(i + 0.5) * dz for i in range(N)]
        z_nodes = [i * dz for i in range(N + 1)]

        def p_z(z):
            return Ka * (gamma_r * z + q_s) + gamma_w * max(z - h_NF, 0.0)

        p_mid = [p_z(zi) for zi in z_mid]

        if condicion == 'biapoyado':
            # Reacciones: equilibrio estático
            R_top = sum(p_mid[i] * (H - z_mid[i]) * dz for i in range(N)) / H
            R_bot = sum(p_mid[i] * z_mid[i]          * dz for i in range(N)) / H

            # Momento en cada nodo con sumas acumuladas — O(N)
            M_nodes = [0.0] * (N + 1)
            cum_p = cum_pz = 0.0
            for j in range(N + 1):
                zj = z_nodes[j]
                M_nodes[j] = R_top * zj - zj * cum_p + cum_pz
                if j < N:
                    cum_p  += p_mid[j] * dz
                    cum_pz += p_mid[j] * z_mid[j] * dz

            M_base   = M_nodes[N]   # ≈ 0 (articulado en base)
            M_corona = 0.0

        else:  # empotrado_base
            # Método de la fuerza: estructura primaria = ménsula fija en z=H
            # M0(z) = −z·Σp·dz + Σp·z_mid·dz (momento en la ménsula sin prop)
            # R_top = −(3/H³)·∫M0(z)·z dz  (compatibilidad: δ_techo = 0)
            M0      = [0.0] * (N + 1)
            cum_p   = cum_pz = num = 0.0
            for j in range(N + 1):
                zj    = z_nodes[j]
                m0    = -zj * cum_p + cum_pz
                M0[j] = m0
                num  += m0 * zj * dz
                if j < N:
                    cum_p  += p_mid[j] * dz
                    cum_pz += p_mid[j] * z_mid[j] * dz

            R_top    = -(3.0 / H ** 3) * num
            R_bot    = sum(p_mid[i] * dz for i in range(N)) - R_top
            M_nodes  = [M0[j] + R_top * z_nodes[j] for j in range(N + 1)]
            M_base   = M_nodes[N]    # negativo = hogging en el empotramiento
            M_corona = 0.0

        M_max    = max(M_nodes)
        idx_max  = M_nodes.index(M_max)
        z_at_max = z_nodes[idx_max]

        momentos = ResultadoMomentos(
            condicion=condicion,
            R_top=R_top, R_bot=R_bot,
            M_base=M_base, M_max=M_max,
            z_max=z_at_max, M_corona=M_corona,
        )

        # ── Diseño RC ────────────────────────────────────────────────────
        db_as   = 0.016  # ∅16 para estimación del peralte efectivo
        d_muro  = max(e_muro - recub - db_as / 2, 0.05)
        phi_b   = 0.90
        b_mm    = 1000.0
        d_mm    = d_muro * 1000

        def _as_req(Mu_kNm: float) -> float:
            if Mu_kNm <= 0 or d_muro <= 0:
                return 0.0
            Rn   = Mu_kNm * 1e6 / (phi_b * b_mm * d_mm ** 2)
            disc = max(1 - 2 * Rn / (0.85 * fc), 1e-9)
            rho  = 0.85 * fc / fy * (1 - math.sqrt(disc))
            return rho * b_mm * d_mm / 100

        # ACI 11.6.1 — acero mínimo vertical en muros
        rho_l_min    = 0.0012 if db_as >= 0.016 else 0.0015
        As_min_vert  = rho_l_min * 1000 * (e_muro * 1000) / 100

        # Cara expuesta al suelo — M_max positivo (vano)
        Mu_pos       = 1.6 * M_max
        As_req_pos   = _as_req(Mu_pos)
        As_pos       = max(As_req_pos, As_min_vert)
        bar_pos, As_dis_pos = _seleccionar_barra(As_pos)
        vert_suelo = ElementoRC(
            "Vertical (cara suelo)", Mu_pos, d_muro,
            As_req_pos, As_min_vert, As_dis_pos, bar_pos,
            nota="Barras verticales, cara expuesta al suelo (M+ de vano)"
        )

        # Cara interior — |M_base| negativo (empotramiento)
        Mu_neg       = 1.6 * abs(M_base)
        As_req_neg   = _as_req(Mu_neg)
        As_neg       = max(As_req_neg, As_min_vert)
        bar_neg, As_dis_neg = _seleccionar_barra(As_neg)
        nota_neg     = ("Barras verticales, cara interior (M− en empotramiento)"
                        if condicion == 'empotrado_base' else
                        "Cara interior — sin momento significativo (apoyo articulado)")
        vert_int = ElementoRC(
            "Vertical (cara interior)", Mu_neg, d_muro,
            As_req_neg, As_min_vert, As_dis_neg, bar_neg, nota=nota_neg
        )

        # Barras horizontales — temperatura/contracción por cara
        rho_t_min   = 0.0020 if db_as >= 0.016 else 0.0025
        As_min_horiz = rho_t_min * 1000 * (e_muro * 1000) / 100 / 2  # por cara
        bar_h, As_dis_h = _seleccionar_barra(As_min_horiz)
        horiz_temp = ElementoRC(
            "Horizontal (temp./retracción)", 0.0, e_muro,
            0.0, As_min_horiz, As_dis_h, bar_h,
            nota=f"Por cada cara del muro — ρ_t = {rho_t_min:.4f} (ACI 11.6.1)"
        )

        # ── Mensajes ─────────────────────────────────────────────────────
        mensajes.append({"tipo": "ok",
                         "texto": f"R_top (corona) = {R_top:.2f} kN/m"})
        mensajes.append({"tipo": "ok",
                         "texto": f"R_bot (base)   = {R_bot:.2f} kN/m"})
        mensajes.append({"tipo": "ok",
                         "texto": f"M_max positivo = {M_max:.2f} kN·m/m a z = {z_at_max:.2f} m"})
        if condicion == 'empotrado_base':
            mensajes.append({"tipo": "ok",
                             "texto": f"M_base (empotr.) = {M_base:.2f} kN·m/m"})
        if tiene_nf:
            mensajes.append({"tipo": "advertencia",
                             "texto": (f"Nivel freático a h_NF = {h_NF:.2f} m — "
                                       f"verificar drenaje y subpresión en losa de piso")})
        if H > 5.0:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"H = {H:.2f} m > 5 m — considerar losa intermedia como apoyo adicional"})
        if e_muro < H / 15:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"e_muro = {e_muro:.2f} m < H/15 = {H/15:.2f} m — revisar rigidez"})
        if c_r > 0:
            mensajes.append({"tipo": "advertencia",
                             "texto": "Cohesión activa (c > 0): se usa Rankine sin reducción por tracción"})

        self.res = ResultadosMuroSotano(
            H=H, e_muro=e_muro, h_NF=h_NF,
            condicion=condicion, Ka=Ka,
            cargas=cargas, momentos=momentos,
            vert_cara_suelo=vert_suelo,
            vert_cara_int=vert_int,
            horiz_temp=horiz_temp,
            mensajes=mensajes,
        )
        self._inp = dict(
            H=H, e_muro=e_muro, h_NF=h_NF, condicion=condicion,
            phi_r=phi_r, c_r=c_r, gamma_r=gamma_r, q_s=q_s,
            gamma_w=gamma_w, fc=fc, fy=fy, recub=recub, gamma_c=gamma_c,
        )
        return self
