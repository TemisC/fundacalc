"""
Módulo 8 — Capacidad Portante del suelo.
Métodos: Terzaghi (1943), Meyerhof (1963), Hansen (1970).
"""
import math
from dataclasses import dataclass, field
from typing import List, Optional


# ── Factores portantes comunes (Reissner / Prandtl) ──────────────────────────

def _Nq(phi_r: float) -> float:
    return math.exp(math.pi * math.tan(phi_r)) * math.tan(math.pi / 4 + phi_r / 2) ** 2


def _Nc(phi_r: float, Nq: float) -> float:
    return (Nq - 1) / math.tan(phi_r) if phi_r > 1e-9 else 5.14


def _Ng_meyerhof(phi_r: float, Nq: float) -> float:
    return (Nq - 1) * math.tan(1.4 * phi_r)


def _Ng_hansen(phi_r: float, Nq: float) -> float:
    return 1.5 * (Nq - 1) * math.tan(phi_r)


def phi_desde_spt(N60: float, sigma_v_kPa: float = 100.0) -> float:
    """Correlación SPT → φ (Schmertmann 1975, corrección Liao & Whitman 1986)."""
    Cn = min(2.0, math.sqrt(100.0 / max(sigma_v_kPa, 10.0)))
    N1_60 = min(N60 * Cn, 100.0)
    phi = 27.1 + 0.3 * N1_60 - 0.00054 * N1_60 ** 2
    return round(max(20.0, min(45.0, phi)), 1)


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class ResultadoMetodo:
    nombre: str
    Nc: float
    Nq: float
    Ngamma: float
    sc: float
    sq: float
    sgamma: float
    dc: float
    dq: float
    dgamma: float
    q_ult: float    # [kPa]
    q_adm: float    # [kPa]


@dataclass
class ResultadosCP:
    metodos: List[ResultadoMetodo]
    phi: float          # [°]
    c: float            # [kPa]
    gamma_ef: float     # peso unitario efectivo en la base [kN/m³]
    q: float            # presión de sobrecarga = γ·Df [kPa]
    FS: float
    qa_conserv: float   # qa más conservador (mínimo entre métodos)
    qa_medio: float     # promedio
    ok: bool
    mensajes: List[dict] = field(default_factory=list)


# ── Motor principal ───────────────────────────────────────────────────────────

class CapacidadPortante:

    def calcular(
        self,
        phi_deg: float,
        c: float,
        gamma: float,
        Df: float,
        B: float,
        L: float = 0.0,
        forma: str = "rectangular",
        FS: float = 3.0,
        nf_prof: Optional[float] = None,
        gamma_sub: Optional[float] = None,
    ) -> "CapacidadPortante":
        """
        phi_deg  : ángulo de fricción interna [°]
        c        : cohesión [kPa]
        gamma    : peso unitario natural del suelo [kN/m³]
        Df       : profundidad de desplante [m]
        B        : ancho de la fundación [m]
        L        : largo [m] (0 = corrida, igual a B = cuadrada)
        forma    : "corrida" | "cuadrada" | "rectangular" | "circular"
        FS       : factor de seguridad global
        nf_prof  : profundidad del nivel freático desde la superficie [m]
        gamma_sub: peso unitario sumergido [kN/m³] (default γ − 9.81)
        """
        GW = 9.81
        if gamma_sub is None:
            gamma_sub = max(gamma - GW, 8.0)

        # ── Presión de sobrecarga y γ efectivo en la base ─────────────────
        if nf_prof is None:
            q_sobr = gamma * Df
            gamma_ef = gamma
        else:
            nf_prof = max(0.0, nf_prof)
            if nf_prof <= Df:
                q_sobr = gamma * nf_prof + gamma_sub * (Df - nf_prof)
                gamma_ef = gamma_sub
            elif nf_prof < Df + B:
                q_sobr = gamma * Df
                frac = (nf_prof - Df) / B
                gamma_ef = gamma_sub + frac * (gamma - gamma_sub)
            else:
                q_sobr = gamma * Df
                gamma_ef = gamma

        phi_r = math.radians(phi_deg)
        mensajes: List[dict] = []

        # ── Factores de capacidad portante ────────────────────────────────
        Nq   = _Nq(phi_r)
        Nc   = _Nc(phi_r, Nq)
        Ng_m = _Ng_meyerhof(phi_r, Nq)
        Ng_h = _Ng_hansen(phi_r, Nq)

        # Relación B/L (usado en factores de forma)
        if forma in ("corrida",) or L <= 0:
            BL = 0.0
        elif forma == "circular":
            BL = 1.0
        elif forma == "cuadrada" or abs(B - L) < 1e-6:
            BL = 1.0
        else:
            BL = B / max(L, B)   # B ≤ L siempre

        # ── TERZAGHI (1943) ───────────────────────────────────────────────
        Nc_t = 5.7 if phi_deg < 1e-6 else Nc
        Ng_t = Ng_m  # aproximación estándar

        if forma == "corrida" or L <= 0:
            sc_t, sg_t = 1.0, 1.0
        elif forma in ("cuadrada",) or abs(BL - 1.0) < 1e-6:
            sc_t, sg_t = 1.3, 0.8
        elif forma == "circular":
            sc_t, sg_t = 1.3, 0.6
        else:
            sc_t = 1.0 + 0.3 * BL
            sg_t = 1.0 - 0.2 * BL

        q_ult_t = c * Nc_t * sc_t + q_sobr * Nq + 0.5 * gamma_ef * B * Ng_t * sg_t
        q_ult_t = max(0.0, q_ult_t)

        terzaghi = ResultadoMetodo(
            nombre="Terzaghi (1943)",
            Nc=Nc_t, Nq=Nq, Ngamma=Ng_t,
            sc=sc_t, sq=1.0, sgamma=sg_t,
            dc=1.0, dq=1.0, dgamma=1.0,
            q_ult=q_ult_t, q_adm=q_ult_t / FS,
        )

        # ── MEYERHOF (1963) ───────────────────────────────────────────────
        Kp   = math.tan(math.pi / 4 + phi_r / 2) ** 2
        sqKp = math.sqrt(Kp)

        sc_m = 1.0 + 0.2 * BL * Kp
        sq_m = (1.0 + 0.1 * BL * Kp) if phi_deg >= 10 else 1.0
        sg_m = (1.0 + 0.1 * BL * Kp) if phi_deg >= 10 else 1.0

        Df_B = Df / B
        dc_m = 1.0 + 0.2 * Df_B * sqKp
        dq_m = (1.0 + 0.1 * Df_B * sqKp) if phi_deg >= 10 else 1.0
        dg_m = dq_m

        q_ult_m = (c * Nc * sc_m * dc_m
                   + q_sobr * Nq * sq_m * dq_m
                   + 0.5 * gamma_ef * B * Ng_m * sg_m * dg_m)
        q_ult_m = max(0.0, q_ult_m)

        meyerhof = ResultadoMetodo(
            nombre="Meyerhof (1963)",
            Nc=Nc, Nq=Nq, Ngamma=Ng_m,
            sc=sc_m, sq=sq_m, sgamma=sg_m,
            dc=dc_m, dq=dq_m, dgamma=dg_m,
            q_ult=q_ult_m, q_adm=q_ult_m / FS,
        )

        # ── HANSEN (1970) ─────────────────────────────────────────────────
        if phi_deg > 1e-6:
            sc_h = 1.0 + BL * (Nq / Nc)
        else:
            sc_h = 1.0 + 0.2 * BL
        sq_h = 1.0 + BL * math.tan(phi_r)
        sg_h = max(0.0, 1.0 - 0.4 * BL)

        if Df_B <= 1:
            dc_h = 1.0 + 0.4 * Df_B
            dq_h = 1.0 + 2 * math.tan(phi_r) * (1 - math.sin(phi_r)) ** 2 * Df_B
        else:
            atan_db = math.atan(Df_B)
            dc_h = 1.0 + 0.4 * atan_db
            dq_h = 1.0 + 2 * math.tan(phi_r) * (1 - math.sin(phi_r)) ** 2 * atan_db
        dg_h = 1.0

        q_ult_h = (c * Nc * sc_h * dc_h
                   + q_sobr * Nq * sq_h * dq_h
                   + 0.5 * gamma_ef * B * Ng_h * sg_h * dg_h)
        q_ult_h = max(0.0, q_ult_h)

        hansen = ResultadoMetodo(
            nombre="Hansen (1970)",
            Nc=Nc, Nq=Nq, Ngamma=Ng_h,
            sc=sc_h, sq=sq_h, sgamma=sg_h,
            dc=dc_h, dq=dq_h, dgamma=dg_h,
            q_ult=q_ult_h, q_adm=q_ult_h / FS,
        )

        metodos = [terzaghi, meyerhof, hansen]
        qa_vals = [m.q_adm for m in metodos]
        qa_conserv = min(qa_vals)
        qa_medio   = sum(qa_vals) / len(qa_vals)

        # ── Mensajes ─────────────────────────────────────────────────────
        if phi_deg < 10 and c < 1:
            mensajes.append({"tipo": "error",
                             "texto": "φ < 10° y c ≈ 0: suelo sin resistencia significativa, revisar parámetros"})
        if FS < 2.5:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"FS = {FS:.1f} es bajo para fundaciones superficiales (mínimo recomendado: 2.5 – 3.0)"})
        if nf_prof is not None and nf_prof <= Df:
            mensajes.append({"tipo": "advertencia",
                             "texto": "Nivel freático en o por encima de la fundación: se aplicó γ' en la base"})
        for m in metodos:
            mensajes.append({"tipo": "ok",
                             "texto": f"{m.nombre}: qu = {m.q_ult:.1f} kPa  →  qa = {m.q_adm:.1f} kPa"})

        self.res = ResultadosCP(
            metodos=metodos,
            phi=phi_deg, c=c,
            gamma_ef=gamma_ef, q=q_sobr, FS=FS,
            qa_conserv=qa_conserv,
            qa_medio=qa_medio,
            ok=qa_conserv > 0,
            mensajes=mensajes,
        )
        return self
