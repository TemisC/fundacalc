"""
Módulo 9.4 — Muro con Contrafuertes (H > 6 m).

Verificaciones globales (por metro lineal de muro):
  · Vuelco          FS_v ≥ 2.0
  · Deslizamiento   FS_d ≥ 1.5
  · Presión base    q_max ≤ qa
  · Excentricidad   |e| ≤ B/6

Diseño RC (ACI 318-19):
  · Pantalla   — losa continua entre contrafuertes; Mu_neg (sobre apoyo) y Mu_pos (vano)
  · Punta      — voladizo horizontal, presión neta hacia arriba
  · Talón      — voladizo horizontal, carga neta hacia abajo
  · Contrafuerte — viga ménsula vertical; Mu y As en la base (por contrafuerte)

Geometría (frente vertical, trasdós escalonado por la presencia de contrafuertes):
  B_total = B_punta + e_pantalla + B_talon
  Contrafuertes: triángulos de e_cont × h_fuste × B_talon / 2
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple

# ── Tabla de barras métricas ─────────────────────────────────────────────────
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
    """Retorna (etiqueta, As_dis [cm²/m])."""
    As_req = max(As_req_cm2_m, 0.01) * 100
    for nombre, db, Ab in _BARRAS:
        for sep in _SEPARACIONES:
            As_dis = Ab / sep * 1000
            if As_dis >= As_req and sep >= 100:
                return f"{nombre} c/{sep//10}cm", As_dis / 100
    return "∅32 c/10cm", 804.2 / 100 * 1000 / 100


def _seleccionar_barra_total(As_req_cm2: float) -> Tuple[str, float]:
    """Para el contrafuerte: dado As total [cm²], retorna (etiqueta de barras, As_dis [cm²])."""
    As_req_mm2 = max(As_req_cm2, 0.01) * 100
    for nombre, db, Ab in _BARRAS:
        for n in range(2, 30):
            As_total = n * Ab
            if As_total >= As_req_mm2:
                return f"{n} barras {nombre}", As_total / 100
    return "Ver dimensionamiento", As_req_cm2


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class ResultadoEstabilidadCF:
    Ka: float
    Ea_gamma: float
    Ea_q:     float
    Ea:       float
    Mo:       float

    W_pantalla:    float
    W_zapata:      float
    W_talon_soil:  float
    W_q_talon:     float
    W_cont_m:      float   # peso contrafuertes por metro de muro [kN/m]
    W_total:       float
    Mr:            float

    x_R:      float
    e:        float
    B_total:  float

    q_max: float
    q_min: float

    Ep:        float
    FS_vuelco: float
    FS_desliz: float

    ok_vuelco:        bool
    ok_desliz:        bool
    ok_presion:       bool
    ok_excentricidad: bool
    ok_global:        bool


@dataclass
class ElementoRC:
    nombre:  str
    Mu:      float   # [kN·m/m] para pantalla/punta/talón; [kN·m] para contrafuerte
    d:       float   # [m]
    As_req:  float   # [cm²/m] o [cm²/contrafuerte]
    As_min:  float
    As_dis:  float
    barra:   str
    nota:    str = ""


@dataclass
class ResultadosMuroContrafuertes:
    H:              float
    h_fuste:        float
    B_total:        float
    Ka:             float
    s:              float   # espaciado entre contrafuertes [m]
    L_libre:        float   # luz libre de la pantalla [m]

    estabilidad:    ResultadoEstabilidadCF
    pantalla_neg:   ElementoRC
    pantalla_pos:   ElementoRC
    punta:          ElementoRC
    talon:          ElementoRC
    contrafuerte:   ElementoRC   # por contrafuerte (no por metro)

    mensajes: List[dict] = field(default_factory=list)


# ── Motor ─────────────────────────────────────────────────────────────────────

class MuroContrafuertes:

    def calcular(
        self,
        # Geometría
        H:              float,   # altura total [m]
        h_zapata:       float,   # espesor de zapata [m]
        e_pantalla:     float,   # espesor de la pantalla [m]
        e_contrafuerte: float,   # espesor del contrafuerte [m]
        B_punta:        float,   # proyección de punta [m]
        B_talon:        float,   # proyección de talón [m]
        s:              float,   # espaciado entre contrafuertes [m]
        # Suelo retenido
        gamma_r: float,
        phi_r:   float,
        c_r:     float,
        q_s:     float,
        # Suelo de fundación
        gamma_f:      float,
        phi_f:        float,
        c_f:          float,
        qa:           float,
        # Materiales
        gamma_c:      float = 24.0,
        fc:           float = 25.0,
        fy:           float = 420.0,
        recub:        float = 0.07,
        delta_factor: float = 0.667,
    ) -> "MuroContrafuertes":

        mensajes: List[dict] = []

        h_fuste = H - h_zapata
        B_total = B_punta + e_pantalla + B_talon
        L_libre = s - e_contrafuerte   # luz libre de la pantalla

        if h_fuste <= 0:
            raise ValueError("h_zapata debe ser menor que H")
        if L_libre <= 0:
            raise ValueError("El espaciado s debe ser mayor que e_contrafuerte")

        # ── Empuje activo Rankine ────────────────────────────────────────
        Ka       = math.tan(math.radians(45 - phi_r / 2)) ** 2
        Ea_gamma = 0.5 * Ka * gamma_r * H ** 2
        Ea_q     = Ka * q_s * H
        Ea       = Ea_gamma + Ea_q
        Mo       = Ea_gamma * (H / 3) + Ea_q * (H / 2)

        # ── Pesos y brazos desde la punta (toe) ──────────────────────────
        W_pantalla   = gamma_c * e_pantalla * h_fuste
        x_pantalla   = B_punta + e_pantalla / 2

        W_zapata     = gamma_c * B_total * h_zapata
        x_zapata     = B_total / 2

        W_talon_soil = gamma_r * B_talon * h_fuste
        x_talon      = B_punta + e_pantalla + B_talon / 2

        W_q_talon    = q_s * B_talon
        x_q          = x_talon

        # Contrafuertes (triángulo: base B_talon, altura h_fuste) por metro de muro
        W_cont_m     = gamma_c * e_contrafuerte * h_fuste * B_talon / 2.0 / s
        x_cont       = B_punta + e_pantalla + B_talon / 3.0   # CG del triángulo

        W_total = W_pantalla + W_zapata + W_talon_soil + W_q_talon + W_cont_m

        Mr = (W_pantalla   * x_pantalla
              + W_zapata     * x_zapata
              + W_talon_soil * x_talon
              + W_q_talon    * x_q
              + W_cont_m     * x_cont)

        # ── FS vuelco ────────────────────────────────────────────────────
        FS_v = Mr / Mo if Mo > 1e-9 else 999.0

        # ── FS deslizamiento ─────────────────────────────────────────────
        phi_f_rad = math.radians(phi_f)
        Kp    = math.tan(math.radians(45 + phi_f / 2)) ** 2
        Ep    = 0.5 * Kp * gamma_f * h_zapata ** 2
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

        estab = ResultadoEstabilidadCF(
            Ka=Ka, Ea_gamma=Ea_gamma, Ea_q=Ea_q, Ea=Ea, Mo=Mo,
            W_pantalla=W_pantalla, W_zapata=W_zapata,
            W_talon_soil=W_talon_soil, W_q_talon=W_q_talon,
            W_cont_m=W_cont_m, W_total=W_total, Mr=Mr,
            x_R=x_R, e=e, B_total=B_total,
            q_max=q_max, q_min=q_min, Ep=Ep,
            FS_vuelco=FS_v, FS_desliz=FS_d,
            ok_vuelco=ok_v, ok_desliz=ok_d,
            ok_presion=ok_p, ok_excentricidad=ok_e,
            ok_global=ok_g,
        )

        # ── Diseño RC ────────────────────────────────────────────────────
        phi_bend = 0.90
        db_asumida = 0.016  # ∅16 para peralte inicial

        def _as_req(Mu_kNm: float, d_m: float, b_mm: float = 1000) -> float:
            if Mu_kNm <= 0 or d_m <= 0:
                return 0.0
            d_mm = d_m * 1000
            Rn   = Mu_kNm * 1e6 / (phi_bend * b_mm * d_mm ** 2)
            disc = max(1 - 2 * Rn / (0.85 * fc), 1e-9)
            rho  = 0.85 * fc / fy * (1 - math.sqrt(disc))
            return rho * b_mm * d_mm / 100  # cm²/m

        def _as_min(d_m: float, b_mm: float = 1000) -> float:
            rho_min = max(0.25 * math.sqrt(fc) / fy, 1.4 / fy)
            return rho_min * b_mm * (d_m * 1000) / 100

        # ── Pantalla (losa continua horizontal) ──────────────────────────
        # Presión en la base de la pantalla (mayor valor → diseño conservador)
        p_base  = Ka * (gamma_r * h_fuste + q_s)   # [kPa]
        d_pant  = max(e_pantalla - recub - db_asumida / 2, 0.05)

        # ACI 8.3.3: Mu_neg ≈ wu×L²/10, Mu_pos ≈ wu×L²/16  (losa continua)
        wu_pant   = 1.6 * p_base   # [kN/m² × 1m altura = kN/m por metro de altura]
        Mu_pant_n = wu_pant * L_libre ** 2 / 10.0
        Mu_pant_p = wu_pant * L_libre ** 2 / 14.0   # vano interior

        As_req_pn = _as_req(Mu_pant_n, d_pant)
        As_req_pp = _as_req(Mu_pant_p, d_pant)
        As_min_pant = max(_as_min(d_pant),
                          0.0020 * 1000 * (e_pantalla * 1000) / 100)  # mín ACI 7.6.1 para losas
        As_n = max(As_req_pn, As_min_pant)
        As_p = max(As_req_pp, As_min_pant)
        bar_pn, As_dis_pn = _seleccionar_barra(As_n)
        bar_pp, As_dis_pp = _seleccionar_barra(As_p)

        pantalla_neg = ElementoRC(
            "Pantalla (apoyo, neg.)", Mu_pant_n, d_pant,
            As_req_pn, As_min_pant, As_dis_pn, bar_pn,
            nota="Barras horiz. cara trasdós, en apoyo sobre contrafuerte"
        )
        pantalla_pos = ElementoRC(
            "Pantalla (vano, pos.)", Mu_pant_p, d_pant,
            As_req_pp, As_min_pant, As_dis_pp, bar_pp,
            nota="Barras horiz. cara intradós, en vano libre"
        )

        # ── Punta ────────────────────────────────────────────────────────
        q_at_stem  = q_max - (q_max - q_min) * B_punta / B_total
        q_punta_av = (q_max + q_at_stem) / 2
        w_losa_toe = gamma_c * h_zapata
        q_net_pt   = max(q_punta_av - w_losa_toe, 0.0)
        Mu_punta   = 1.6 * q_net_pt * B_punta ** 2 / 2
        d_zap      = max(h_zapata - recub - db_asumida / 2, 0.05)
        As_req_pt  = _as_req(Mu_punta, d_zap)
        As_min_zap = max(_as_min(d_zap),
                         0.0018 * 1000 * (h_zapata * 1000) / 100)
        As_pt = max(As_req_pt, As_min_zap)
        bar_pt, As_dis_pt = _seleccionar_barra(As_pt)
        punta_rc = ElementoRC("Punta", Mu_punta, d_zap,
                               As_req_pt, As_min_zap, As_dis_pt, bar_pt)

        # ── Talón ────────────────────────────────────────────────────────
        q_at_heel  = q_min
        q_at_stem2 = q_min + (q_max - q_min) * (B_total - B_talon) / B_total
        q_talon_av = (q_at_heel + q_at_stem2) / 2
        w_down_talon = gamma_r * h_fuste + q_s + gamma_c * h_zapata
        q_net_tal    = max(w_down_talon - q_talon_av, 0.0)
        Mu_talon     = 1.6 * q_net_tal * B_talon ** 2 / 2
        As_req_tl    = _as_req(Mu_talon, d_zap)
        As_tl        = max(As_req_tl, As_min_zap)
        bar_tl, As_dis_tl = _seleccionar_barra(As_tl)
        talon_rc = ElementoRC("Talón", Mu_talon, d_zap,
                               As_req_tl, As_min_zap, As_dis_tl, bar_tl)

        # ── Contrafuerte (viga ménsula vertical) ─────────────────────────
        # Fuerza horizontal por contrafuerte (para la altura h_fuste)
        Ea_g_cont = 0.5 * Ka * gamma_r * h_fuste ** 2 * s   # [kN]
        Ea_q_cont = Ka * q_s * h_fuste * s                   # [kN]
        Mo_cont   = Ea_g_cont * h_fuste / 3 + Ea_q_cont * h_fuste / 2   # [kN·m]
        Mu_cont   = 1.6 * Mo_cont

        # Sección del contrafuerte en la base: b = e_cont, d = B_talon − recub
        b_cont   = e_contrafuerte   # [m]
        d_cont   = max(B_talon - recub - db_asumida / 2, 0.10)   # [m]
        # As requerida para un bloque de dimensiones b_cont × d_cont
        As_req_cont = _as_req(Mu_cont, d_cont, b_mm=b_cont * 1000)
        As_min_cont = max(_as_min(d_cont, b_mm=b_cont * 1000),
                          0.0025 * (b_cont * 1000) * (d_cont * 1000) / 100)
        As_cont_total = max(As_req_cont, As_min_cont)   # [cm²/contrafuerte]
        bar_cont, As_dis_cont = _seleccionar_barra_total(As_cont_total)

        contrafuerte_rc = ElementoRC(
            "Contrafuerte (base)", Mu_cont, d_cont,
            As_req_cont, As_min_cont, As_dis_cont, bar_cont,
            nota=f"Valores por contrafuerte (s={s:.2f}m); barras en cara de tracción (talón)"
        )

        # ── Mensajes ─────────────────────────────────────────────────────
        chks = [
            (ok_v, f"Vuelco: FS = {FS_v:.2f}", "≥ 2.0"),
            (ok_d, f"Deslizamiento: FS = {FS_d:.2f}", "≥ 1.5"),
            (ok_p, f"Presión base: q_max = {q_max:.1f} kPa", f"≤ qa = {qa:.1f} kPa"),
            (ok_e, f"Excentricidad: |e| = {abs(e):.3f} m", f"≤ B/6 = {B_total/6:.3f} m"),
        ]
        for ok, val, lim in chks:
            tipo = "ok" if ok else "error"
            txt  = f"{val} {'✓' if ok else '✗'} (req. {lim})"
            mensajes.append({"tipo": tipo, "texto": txt})

        if s > 5.0:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"Espaciado s = {s:.2f} m > 5.0 m — revisar diseño de pantalla"})
        if e_pantalla < H / 20:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"e_pantalla = {e_pantalla:.2f} m < H/20 = {H/20:.2f} m — considerar aumentar espesor"})
        if c_r > 0:
            mensajes.append({"tipo": "advertencia",
                             "texto": "Cohesión activa (c > 0): se usa Rankine sin reducción por tracción"})

        self.res = ResultadosMuroContrafuertes(
            H=H, h_fuste=h_fuste, B_total=B_total, Ka=Ka, s=s,
            L_libre=L_libre,
            estabilidad=estab,
            pantalla_neg=pantalla_neg, pantalla_pos=pantalla_pos,
            punta=punta_rc, talon=talon_rc,
            contrafuerte=contrafuerte_rc,
            mensajes=mensajes,
        )
        self._inp = dict(
            H=H, h_zapata=h_zapata, e_pantalla=e_pantalla,
            e_contrafuerte=e_contrafuerte, B_punta=B_punta,
            B_talon=B_talon, s=s,
            gamma_r=gamma_r, phi_r=phi_r, c_r=c_r, q_s=q_s,
            gamma_f=gamma_f, phi_f=phi_f, c_f=c_f, qa=qa,
            gamma_c=gamma_c, fc=fc, fy=fy, recub=recub,
            delta_factor=delta_factor,
        )
        return self
