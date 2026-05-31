"""
Módulo 9.2 — Muro de Gravedad (hormigón ciclópeo / mampostería).

Verificaciones de estabilidad (por metro lineal de muro):
  · Vuelco          FS_v ≥ 2.0
  · Deslizamiento   FS_d ≥ 1.5
  · Presión base    q_max ≤ qa
  · Excentricidad   |e| ≤ B/6  (sin tracción — sección maciza sin acero)

Geometría: sección trapezoidal con frente vertical y trasdós inclinado.
  Frente: x = 0 (vertical, cara expuesta)
  Trasdós: desde x = b_base (base) hasta x = b_corona (corona)
"""
import math
from dataclasses import dataclass, field
from typing import List


@dataclass
class ResultadoEstabilidadGravedad:
    Ka: float
    Ea_gamma: float   # empuje triangular [kN/m]
    Ea_q:     float   # empuje por sobrecarga [kN/m]
    Ea:       float   # empuje total [kN/m]
    Mo:       float   # momento volcador sobre toe [kN.m/m]

    W_muro:  float    # peso del muro [kN/m]
    x_CG:    float    # brazo CG desde el toe [m]
    Mr:      float    # momento resistente [kN.m/m]

    x_R:    float     # posición resultante desde toe [m]
    e:      float     # excentricidad [m]
    b_base: float     # ancho de la base (para referencia en checks) [m]

    q_max: float      # presión máx en toe [kPa]
    q_min: float      # presión mín en heel [kPa]

    Ep:        float  # empuje pasivo en toe [kN/m]
    FS_vuelco: float
    FS_desliz: float

    ok_vuelco:        bool
    ok_desliz:        bool
    ok_presion:       bool
    ok_excentricidad: bool
    ok_global:        bool


@dataclass
class ResultadosMuroGravedad:
    H:          float
    b_base:     float
    b_corona:   float
    A_seccion:  float   # área sección transversal [m²]
    Ka:         float

    estabilidad: ResultadoEstabilidadGravedad
    mensajes: List[dict] = field(default_factory=list)


class MuroGravedad:

    def calcular(
        self,
        # Geometría
        H:          float,   # altura total del muro [m]
        b_base:     float,   # ancho en la base [m]
        b_corona:   float,   # ancho en la corona [m]
        h_emb:      float,   # enterramiento del pie — empuje pasivo [m]
        # Material del muro
        gamma_muro: float,   # peso unitario del material [kN/m³]
        # Suelo retenido
        gamma_r:    float,   # peso unitario suelo retenido [kN/m³]
        phi_r:      float,   # fricción suelo retenido [°]
        c_r:        float,   # cohesión suelo retenido [kPa]
        q_s:        float,   # sobrecarga en superficie [kPa]
        # Suelo de fundación
        gamma_f:      float,   # peso unitario suelo fundación [kN/m³]
        phi_f:        float,   # fricción suelo fundación [°]
        c_f:          float,   # cohesión suelo fundación [kPa]
        qa:           float,   # presión admisible [kPa]
        # Interfaz base
        delta_factor: float = 0.667,   # δ = δ_factor × φ_f
    ) -> "MuroGravedad":

        mensajes: List[dict] = []

        if H <= 0 or b_base <= 0 or b_corona <= 0:
            raise ValueError("H, b_base y b_corona deben ser positivos")
        if b_corona > b_base:
            raise ValueError("b_corona no puede ser mayor que b_base")

        # ── Empuje activo Rankine ────────────────────────────────────────
        Ka       = math.tan(math.radians(45 - phi_r / 2)) ** 2
        Ea_gamma = 0.5 * Ka * gamma_r * H ** 2
        Ea_q     = Ka * q_s * H
        Ea       = Ea_gamma + Ea_q
        Mo       = Ea_gamma * (H / 3) + Ea_q * (H / 2)

        # ── Peso del muro y centroide horizontal ─────────────────────────
        # Sección trapezoidal: frente vertical, trasdós inclinado.
        # Centroide desde el frente (toe):
        #   x_CG = (b_base·b_corona + (b_base−b_corona)²/3) / (b_base + b_corona)
        A_sec  = (b_base + b_corona) / 2.0 * H
        W_muro = gamma_muro * A_sec
        x_CG   = (b_base * b_corona + (b_base - b_corona) ** 2 / 3.0) / (b_base + b_corona)
        Mr     = W_muro * x_CG

        # ── FS vuelco (respecto al toe) ───────────────────────────────────
        FS_v = Mr / Mo if Mo > 1e-9 else 999.0

        # ── FS deslizamiento ─────────────────────────────────────────────
        phi_f_rad = math.radians(phi_f)
        Kp    = math.tan(math.radians(45 + phi_f / 2)) ** 2
        Ep    = 0.5 * Kp * gamma_f * h_emb ** 2
        delta = delta_factor * phi_f_rad
        F_resist = W_muro * math.tan(delta) + c_f * b_base + Ep
        FS_d = F_resist / Ea if Ea > 1e-9 else 999.0

        # ── Presiones en la base ─────────────────────────────────────────
        x_R = (Mr - Mo) / W_muro if W_muro > 1e-9 else b_base / 2
        e   = b_base / 2 - x_R

        if abs(e) <= b_base / 6:
            q_max = (W_muro / b_base) * (1 + 6 * e / b_base)
            q_min = (W_muro / b_base) * (1 - 6 * e / b_base)
        else:
            q_max = 2 * W_muro / (3 * max(x_R, 1e-6))
            q_min = 0.0

        ok_v = FS_v >= 2.0
        ok_d = FS_d >= 1.5
        ok_p = q_max <= qa
        ok_e = abs(e) <= b_base / 6
        ok_g = ok_v and ok_d and ok_p and ok_e

        estab = ResultadoEstabilidadGravedad(
            Ka=Ka, Ea_gamma=Ea_gamma, Ea_q=Ea_q, Ea=Ea, Mo=Mo,
            W_muro=W_muro, x_CG=x_CG, Mr=Mr,
            x_R=x_R, e=e, b_base=b_base,
            q_max=q_max, q_min=q_min, Ep=Ep,
            FS_vuelco=FS_v, FS_desliz=FS_d,
            ok_vuelco=ok_v, ok_desliz=ok_d,
            ok_presion=ok_p, ok_excentricidad=ok_e,
            ok_global=ok_g,
        )

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
                             "texto": f"|e| = {abs(e):.3f} m > B/6 = {b_base/6:.3f} m — resultante fuera del tercio medio"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Excentricidad: |e| = {abs(e):.3f} m ≤ B/6 = {b_base/6:.3f} m ✓"})

        if c_r > 0:
            mensajes.append({"tipo": "advertencia",
                             "texto": "Cohesión activa (c > 0): se usa Rankine sin reducción por tracción"})

        self.res = ResultadosMuroGravedad(
            H=H, b_base=b_base, b_corona=b_corona,
            A_seccion=A_sec, Ka=Ka,
            estabilidad=estab,
            mensajes=mensajes,
        )
        self._inp = dict(
            H=H, b_base=b_base, b_corona=b_corona, h_emb=h_emb,
            gamma_muro=gamma_muro,
            gamma_r=gamma_r, phi_r=phi_r, c_r=c_r, q_s=q_s,
            gamma_f=gamma_f, phi_f=phi_f, c_f=c_f, qa=qa,
            delta_factor=delta_factor,
        )
        return self
