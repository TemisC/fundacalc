"""
Módulo 9.3 — Muro de Gaviones (escalonado).

Verificaciones globales (por metro lineal):
  · Vuelco          FS_v ≥ 2.0
  · Deslizamiento   FS_d ≥ 1.5
  · Presión base    q_max ≤ qa
  · Excentricidad   |e| ≤ B/6

Verificación interna entre capas:
  · FS deslizamiento ≥ 1.3 en cada junta horizontal

Geometría: N cursos de altura uniforme h_capa, frente vertical, trasdós escalonado.
  El ancho disminuye uniformemente desde b_base (curso 1, inferior) hasta b_corona (curso N, superior).
  Paso por curso: Δb = (b_base − b_corona) / (N − 1)
"""
import math
from dataclasses import dataclass, field
from typing import List


@dataclass
class VerificacionInterna:
    junta:     int    # número de junta (1 = entre curso 1 y 2)
    H_sobre:   float  # altura del muro sobre esta junta [m]
    W_sobre:   float  # peso de gaviones sobre esta junta [kN/m]
    Ea_sobre:  float  # empuje activo sobre esta junta [kN/m]
    FS_desliz: float
    ok_desliz: bool


@dataclass
class ResultadoEstabilidadGavion:
    Ka: float
    Ea_gamma: float   # empuje triangular [kN/m]
    Ea_q:     float   # empuje por sobrecarga [kN/m]
    Ea:       float   # empuje total [kN/m]
    Mo:       float   # momento volcador sobre toe [kN.m/m]

    W_total:  float   # peso total del muro [kN/m]
    x_CG:     float   # brazo CG desde el toe [m]
    Mr:       float   # momento resistente [kN.m/m]

    x_R:    float
    e:      float
    b_base: float

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
class ResultadosMuroGaviones:
    H:          float
    N:          int
    h_capa:     float
    b_base:     float
    b_corona:   float
    anchos:     List[float]   # ancho de cada curso [m], índice 0 = base
    Ka:         float
    A_seccion:  float         # área total [m²]

    estabilidad:  ResultadoEstabilidadGavion
    internas:     List[VerificacionInterna]   # N-1 verificaciones
    ok_interna:   bool                         # todas las juntas OK

    mensajes: List[dict] = field(default_factory=list)


class MuroGaviones:

    def calcular(
        self,
        N:            int,     # número de cursos (capas)
        h_capa:       float,   # altura de cada curso [m]
        b_base:       float,   # ancho del curso inferior [m]
        b_corona:     float,   # ancho del curso superior [m]
        h_emb:        float,   # enterramiento del pie [m]
        gamma_g:      float,   # peso unitario del gavión [kN/m³]
        phi_r:        float,   # fricción suelo retenido [°]
        c_r:          float,   # cohesión suelo retenido [kPa]
        gamma_r:      float,   # peso unitario suelo retenido [kN/m³]
        q_s:          float,   # sobrecarga superficial [kPa]
        phi_f:        float,   # fricción suelo fundación [°]
        c_f:          float,   # cohesión suelo fundación [kPa]
        gamma_f:      float,   # peso unitario suelo fundación [kN/m³]
        qa:           float,   # presión admisible [kPa]
        phi_gavion:   float = 35.0,   # fricción interna entre cursos [°]
        delta_factor: float = 0.667,
    ) -> "MuroGaviones":

        if N < 2:
            raise ValueError("Se requieren al menos 2 cursos")
        if b_corona > b_base:
            raise ValueError("b_corona no puede ser mayor que b_base")
        if h_capa <= 0 or b_base <= 0 or b_corona <= 0:
            raise ValueError("h_capa, b_base y b_corona deben ser positivos")

        mensajes: List[dict] = []
        H = N * h_capa
        delta_b = (b_base - b_corona) / (N - 1) if N > 1 else 0.0

        # ── Anchos de cada curso (0 = base) ─────────────────────────────
        anchos = [b_base - i * delta_b for i in range(N)]

        # ── Peso y centroide global ───────────────────────────────────────
        # Frente vertical: CG del curso i está a b_i/2 del frente
        sum_b    = sum(anchos)
        sum_b2   = sum(b * b for b in anchos)
        W_total  = gamma_g * h_capa * sum_b
        x_CG     = sum_b2 / (2 * sum_b) if sum_b > 1e-9 else b_base / 2
        A_sec    = h_capa * sum_b
        Mr       = W_total * x_CG

        # ── Empuje activo (Rankine, plano vertical en el talón de la base) ──
        Ka       = math.tan(math.radians(45 - phi_r / 2)) ** 2
        Ea_gamma = 0.5 * Ka * gamma_r * H ** 2
        Ea_q     = Ka * q_s * H
        Ea       = Ea_gamma + Ea_q
        Mo       = Ea_gamma * (H / 3) + Ea_q * (H / 2)

        # ── FS vuelco ─────────────────────────────────────────────────────
        FS_v = Mr / Mo if Mo > 1e-9 else 999.0

        # ── FS deslizamiento global ───────────────────────────────────────
        phi_f_rad = math.radians(phi_f)
        Kp    = math.tan(math.radians(45 + phi_f / 2)) ** 2
        Ep    = 0.5 * Kp * gamma_f * h_emb ** 2
        delta = delta_factor * phi_f_rad
        F_resist = W_total * math.tan(delta) + c_f * b_base + Ep
        FS_d = F_resist / Ea if Ea > 1e-9 else 999.0

        # ── Presiones en la base ──────────────────────────────────────────
        x_R = (Mr - Mo) / W_total if W_total > 1e-9 else b_base / 2
        e   = b_base / 2 - x_R

        if abs(e) <= b_base / 6:
            q_max = (W_total / b_base) * (1 + 6 * e / b_base)
            q_min = (W_total / b_base) * (1 - 6 * e / b_base)
        else:
            q_max = 2 * W_total / (3 * max(x_R, 1e-6))
            q_min = 0.0

        ok_v = FS_v >= 2.0
        ok_d = FS_d >= 1.5
        ok_p = q_max <= qa
        ok_e = abs(e) <= b_base / 6
        ok_g = ok_v and ok_d and ok_p and ok_e

        estab = ResultadoEstabilidadGavion(
            Ka=Ka, Ea_gamma=Ea_gamma, Ea_q=Ea_q, Ea=Ea, Mo=Mo,
            W_total=W_total, x_CG=x_CG, Mr=Mr,
            x_R=x_R, e=e, b_base=b_base,
            q_max=q_max, q_min=q_min, Ep=Ep,
            FS_vuelco=FS_v, FS_desliz=FS_d,
            ok_vuelco=ok_v, ok_desliz=ok_d,
            ok_presion=ok_p, ok_excentricidad=ok_e,
            ok_global=ok_g,
        )

        # ── Verificaciones internas (junta j: entre curso j y j+1) ──────
        # j=1 es la junta entre el curso base (1) y el segundo curso (2)
        tan_phi_g = math.tan(math.radians(phi_gavion))
        internas: List[VerificacionInterna] = []

        for j in range(1, N):   # j = 1 .. N-1
            # Cursos sobre la junta j: índices j..N-1 en la lista (0-based)
            W_sobre  = gamma_g * h_capa * sum(anchos[j:])
            H_sobre  = (N - j) * h_capa
            Ea_sobre = 0.5 * Ka * gamma_r * H_sobre ** 2 + Ka * q_s * H_sobre
            FS_int   = W_sobre * tan_phi_g / Ea_sobre if Ea_sobre > 1e-9 else 999.0
            ok_int   = FS_int >= 1.3
            internas.append(VerificacionInterna(
                junta=j, H_sobre=H_sobre, W_sobre=W_sobre,
                Ea_sobre=Ea_sobre, FS_desliz=FS_int, ok_desliz=ok_int,
            ))

        ok_interna = all(vi.ok_desliz for vi in internas)

        # ── Mensajes globales ─────────────────────────────────────────────
        if not ok_v:
            mensajes.append({"tipo": "error",
                             "texto": f"Vuelco insuficiente: FS = {FS_v:.2f} < 2.0"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Vuelco: FS = {FS_v:.2f} ≥ 2.0 ✓"})

        if not ok_d:
            mensajes.append({"tipo": "error",
                             "texto": f"Deslizamiento global insuficiente: FS = {FS_d:.2f} < 1.5"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Deslizamiento global: FS = {FS_d:.2f} ≥ 1.5 ✓"})

        if not ok_p:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"q_max = {q_max:.1f} kPa supera qa = {qa:.1f} kPa"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Presión base: q_max = {q_max:.1f} kPa ≤ qa = {qa:.1f} kPa ✓"})

        if not ok_e:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"|e| = {abs(e):.3f} m > B/6 = {b_base/6:.3f} m — resultante fuera del tercio medio"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Excentricidad: |e| = {abs(e):.3f} m ≤ B/6 = {b_base/6:.3f} m ✓"})

        fallas_int = [vi for vi in internas if not vi.ok_desliz]
        if fallas_int:
            for vi in fallas_int:
                mensajes.append({"tipo": "error",
                                 "texto": f"Junta {vi.junta}: FS_desliz = {vi.FS_desliz:.2f} < 1.3"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Juntas internas: todas FS ≥ 1.3 ✓"})

        if c_r > 0:
            mensajes.append({"tipo": "advertencia",
                             "texto": "Cohesión activa (c > 0): se usa Rankine sin reducción por tracción"})

        self.res = ResultadosMuroGaviones(
            H=H, N=N, h_capa=h_capa,
            b_base=b_base, b_corona=b_corona, anchos=anchos,
            Ka=Ka, A_seccion=A_sec,
            estabilidad=estab, internas=internas,
            ok_interna=ok_interna,
            mensajes=mensajes,
        )
        self._inp = dict(
            N=N, h_capa=h_capa, b_base=b_base, b_corona=b_corona,
            h_emb=h_emb, gamma_g=gamma_g,
            phi_r=phi_r, c_r=c_r, gamma_r=gamma_r, q_s=q_s,
            phi_f=phi_f, c_f=c_f, gamma_f=gamma_f, qa=qa,
            phi_gavion=phi_gavion, delta_factor=delta_factor,
        )
        return self
