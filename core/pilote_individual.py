"""
Módulo 6B — Pilote Individual.

Capacidad Axial (análisis por capas):
  · Arcilla (undrained): método α  →  fs = α(cu) · cu · π·D · Δz
  · Arena/grava:         método β  →  fs = β · σ'v · π·D · Δz   (β = K·tan δ)
  · Punta: Qp = Nc·cu·Ap (arcilla) | Nq·σ'v·Ap (arena, limitado)
  · FS global = Qu / Qa ≥ 2.5

Capacidad Lateral (Broms, 1964 — cabeza libre):
  · Suelo cohesivo  : Hu de ecuación cuadrática (pilote largo) o fórmula directa (corto)
  · Suelo granular  : bisección numérica sobre My = f(Hu)

Diseño RC (ACI 318-19 — sección circular):
  · Barras longitudinales: ρ ∈ [0.8%, 4.0%]
  · Espiral mínima: ρs ≥ 0.45·(Ag/Ach−1)·f'c/fy
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple

# ── Barras métricas ───────────────────────────────────────────────────────────
_BARRAS: List[Tuple[str, float, float]] = [
    ("∅12", 12.0,  113.1),
    ("∅16", 16.0,  201.1),
    ("∅20", 20.0,  314.2),
    ("∅25", 25.0,  490.9),
    ("∅32", 32.0,  804.2),
]

def _seleccionar_n_barras(As_req_cm2: float, db_mm: float = 20.0) -> Tuple[str, int, float]:
    """Retorna (descripción, n_barras, As_total_cm²) para la barra elegida."""
    for nombre, db, Ab_mm2 in _BARRAS:
        if db < db_mm * 0.9:
            continue
        for n in range(4, 32, 2):
            if n * Ab_mm2 / 100 >= As_req_cm2:
                return f"{n} barras {nombre}", n, n * Ab_mm2 / 100
    n = math.ceil(As_req_cm2 / (_BARRAS[-1][2] / 100))
    n = max(n, 4)
    return f"{n} barras ∅32", n, n * _BARRAS[-1][2] / 100


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class CapaSuelo:
    numero:    int
    tipo:      str    # 'arcilla' | 'arena'
    espesor:   float  # [m]
    gamma:     float  # [kN/m³]
    cu:        float  # [kPa]  (arcilla)
    phi:       float  # [°]    (arena)
    N60:       float  # SPT    (arena)
    # calculados
    z_top:     float  # profundidad al tope [m]
    z_mid:     float  # profundidad al centroide [m]
    sigma_v:   float  # tensión efectiva en centroide [kPa]
    alpha:     float  # factor α (arcilla)
    beta:      float  # factor β (arena)
    fs:        float  # fricción unitaria [kPa]
    Qs:        float  # fricción total de la capa [kN]


@dataclass
class ResultadoAxial:
    Ag:          float   # área bruta sección [m²]
    perimetro:   float   # π·D [m]
    capas:       List[CapaSuelo]
    Qs_total:    float   # fricción lateral total [kN]
    Qp:          float   # capacidad en punta [kN]
    Qu:          float   # capacidad última [kN]
    Qa:          float   # capacidad admisible [kN]
    FS_axial:    float
    tipo_punta:  str     # 'arcilla' | 'arena'
    Nq_o_Nc:    float   # factor de punta usado


@dataclass
class ResultadoLateral:
    metodo:      str     # 'cohesivo' | 'granular'
    condicion:   str     # 'libre'
    tipo_pilote: str     # 'corto' | 'largo'
    My:          float   # momento de fluencia [kN·m]
    Hu:          float   # capacidad última lateral [kN]
    FS_lateral:  float
    H_dis:       float   # carga lateral de diseño [kN]
    ok_lateral:  bool
    z_max:       float   # profundidad del momento máximo [m]


@dataclass
class ResultadoRC:
    D:          float   # diámetro [m]
    Ag:         float   # área bruta [m²]
    Ast_req:    float   # área requerida [cm²]
    Ast_min:    float   # área mínima ACI [cm²]
    Ast_max:    float   # área máxima ACI [cm²]
    Ast_dis:    float   # área diseñada [cm²]
    rho_l:      float   # cuantía longitudinal [-]
    desc_long:  str     # descripción barras
    # Espiral
    rho_s_min:  float   # cuantía mínima espiral [-]
    db_esp:     float   # diámetro barra espiral [mm]
    paso_esp:   float   # paso del espiral [mm]


@dataclass
class ResultadosPilote:
    D:      float
    L:      float
    tipo:   str   # 'vaciado_in_situ' | 'hincado'

    axial:    ResultadoAxial
    lateral:  ResultadoLateral
    rc:       ResultadoRC

    mensajes: List[dict] = field(default_factory=list)


# ── Motor ─────────────────────────────────────────────────────────────────────

class PiloteIndividual:

    def calcular(
        self,
        # Geometría del pilote
        D:         float,    # diámetro [m]
        L:         float,    # longitud [m]
        tipo:      str,      # 'vaciado_in_situ' | 'hincado'
        # Perfil de suelo (lista de dicts)
        capas_inp: List[dict],
        # Carga axial de diseño
        Qa_dis:    float,    # [kN]
        FS_min:    float = 2.5,
        # Carga lateral
        H_lat:     float = 0.0,   # [kN]
        e_lat:     float = 0.0,   # excentricidad sobre el terreno [m]
        tipo_lat:  str = 'granular',  # 'cohesivo' | 'granular'
        cu_lat:    float = 50.0,  # cu promedio para Broms cohesivo [kPa]
        phi_lat:   float = 30.0,  # φ para Broms granular [°]
        gamma_lat: float = 18.0,  # γ para Broms granular [kN/m³]
        # Materiales
        fc:        float = 25.0,
        fy:        float = 420.0,
        recub:     float = 0.075,
        gamma_c:   float = 24.0,
    ) -> "PiloteIndividual":

        mensajes: List[dict] = []
        Ag = math.pi * D ** 2 / 4
        perim = math.pi * D

        # ── Factor de reducción por tipo de pilote ────────────────────────
        # Vaciado in situ: menor fricción (K más bajo → β menor)
        beta_factor = 1.0 if tipo == 'hincado' else 0.65

        # ── Capacidad axial por capas ─────────────────────────────────────
        capas_out: List[CapaSuelo] = []
        z_acum = 0.0
        sigma_v_acum = 0.0
        Qs_total = 0.0

        for i, c in enumerate(capas_inp, 1):
            h   = float(c.get('espesor', 1.0))
            tip = str(c.get('tipo', 'arcilla'))
            gam = float(c.get('gamma', 18.0))
            cu  = float(c.get('cu', 50.0))
            phi = float(c.get('phi', 30.0))
            N60 = float(c.get('N60', 20.0))

            z_top = z_acum
            z_mid = z_acum + h / 2
            z_bot = z_acum + h
            sigma_v = sigma_v_acum + gam * h / 2  # tensión efectiva en centroide

            if tip == 'arcilla':
                # α de Terzaghi/API (1984)
                if cu <= 25:
                    alpha = 1.0
                elif cu >= 70:
                    alpha = 0.5
                else:
                    alpha = 1.0 - 0.5 * (cu - 25) / (70 - 25)
                beta = 0.0
                fs = alpha * cu
            else:  # arena / grava
                # β method: K·tan(δ), δ = 0.75·φ (bored) o φ (driven)
                delta = 0.75 * phi if tipo == 'vaciado_in_situ' else phi
                K = 0.7 if tipo == 'vaciado_in_situ' else 1.0
                beta = K * math.tan(math.radians(delta)) * beta_factor
                beta = min(beta, 0.5)  # cap conservador
                alpha = 0.0
                fs = beta * max(sigma_v, 5.0)  # evitar división por cero

            Qs_i = fs * perim * h
            capas_out.append(CapaSuelo(
                numero=i, tipo=tip, espesor=h, gamma=gam,
                cu=cu, phi=phi, N60=N60,
                z_top=z_top, z_mid=z_mid,
                sigma_v=sigma_v, alpha=alpha, beta=beta,
                fs=fs, Qs=Qs_i,
            ))
            Qs_total  += Qs_i
            z_acum    += h
            sigma_v_acum += gam * h

        # ── Capacidad en punta ────────────────────────────────────────────
        capa_base = capas_out[-1]
        sigma_v_base = sigma_v_acum

        if capa_base.tipo == 'arcilla':
            Nc_o_Nq = 9.0
            Qp = Nc_o_Nq * capa_base.cu * Ag
            tipo_punta = 'arcilla'
        else:
            phi_b = capa_base.phi
            Nq = math.exp(math.pi * math.tan(math.radians(phi_b))) * \
                 math.tan(math.radians(45 + phi_b / 2)) ** 2
            qp = Nq * min(sigma_v_base, 200.0)  # limitado 200 kPa (bored)
            Qp = qp * Ag
            Nc_o_Nq = Nq
            tipo_punta = 'arena'

        Qu = Qs_total + Qp
        Qa = Qu / FS_min
        FS_axial = Qu / max(Qa_dis, 1e-3)

        axial = ResultadoAxial(
            Ag=Ag, perimetro=perim, capas=capas_out,
            Qs_total=Qs_total, Qp=Qp, Qu=Qu,
            Qa=Qa, FS_axial=FS_axial,
            tipo_punta=tipo_punta, Nq_o_Nc=Nc_o_Nq,
        )

        # ── Capacidad lateral — Broms (1964), cabeza libre ────────────────
        # Momento de fluencia de la sección RC (estimación inicial con ρ = 2%)
        rho_est = 0.02
        Ast_est  = rho_est * Ag
        d_est    = D - 2 * recub - 0.020 / 2
        # fy [MPa] → [kN/m²] = fy × 1000 ; Ast [m²] ; d [m] → My [kN·m]
        My       = 0.9 * Ast_est * (fy * 1000) * d_est
        My       = max(My, 10.0)   # mínimo razonable

        tipo_pilote_lat = 'corto'
        z_max_broms     = 0.0

        if tipo_lat == 'cohesivo':
            # Pilote corto, cabeza libre
            L_eff = L - 1.5 * D
            if L_eff <= 0:
                Hu = 0.1
            else:
                denom = 2 * e_lat + L + 1.5 * D
                Hu_short = 9 * cu_lat * D * L_eff ** 2 / denom if denom > 0 else 0.0

                # Pilote largo: Hu² + 9cuD(e+1.5D)·Hu - 9cuD·My = 0
                a_coef = 9 * cu_lat * D
                b_coef = a_coef * (e_lat + 1.5 * D)
                disc   = b_coef ** 2 + 4 * a_coef * My
                Hu_long = (-b_coef + math.sqrt(max(disc, 0))) / 2

                if Hu_long < Hu_short:
                    tipo_pilote_lat = 'largo'
                    Hu = Hu_long
                    x0 = Hu / (9 * cu_lat * D) if cu_lat > 0 else 0
                    z_max_broms = 1.5 * D + x0
                else:
                    Hu = Hu_short

        else:  # granular
            Kp_lat = math.tan(math.radians(45 + phi_lat / 2)) ** 2
            k_lat  = 1.5 * Kp_lat * gamma_lat * D   # [kN/m³·D → kN/m²/m]

            # Pilote corto
            denom = 2 * (e_lat + L) if (e_lat + L) > 0 else 1
            Hu_short = Kp_lat * gamma_lat * D * L ** 3 / denom

            # Pilote largo: My = Hu·(e+z*) - KpγD·z*³/2,  z* = √(Hu/k_lat)
            def f_broms(Hu_try):
                if Hu_try <= 0:
                    return -My
                z_star = math.sqrt(Hu_try / k_lat)
                M_calc = Hu_try * (e_lat + z_star) - Kp_lat * gamma_lat * D * z_star ** 3 / 2
                return M_calc - My

            Hu_lo, Hu_hi = 1.0, max(Hu_short * 5, 500)
            for _ in range(60):
                Hu_mid = (Hu_lo + Hu_hi) / 2
                if f_broms(Hu_mid) < 0:
                    Hu_lo = Hu_mid
                else:
                    Hu_hi = Hu_mid
            Hu_long = Hu_mid

            if Hu_long < Hu_short:
                tipo_pilote_lat = 'largo'
                Hu = Hu_long
                z_max_broms = math.sqrt(Hu_long / k_lat) if k_lat > 0 else 0
            else:
                Hu = Hu_short

        Hu = max(Hu, 0.0)
        FS_lat = Hu / max(H_lat, 0.1) if H_lat > 0 else 999.0
        ok_lat = FS_lat >= 1.5

        lateral = ResultadoLateral(
            metodo=tipo_lat, condicion='libre',
            tipo_pilote=tipo_pilote_lat,
            My=My, Hu=Hu, FS_lateral=FS_lat,
            H_dis=H_lat, ok_lateral=ok_lat,
            z_max=z_max_broms,
        )

        # ── Diseño RC ────────────────────────────────────────────────────
        phi_c  = 0.75   # ACI para columnas/pilotes
        fc_kPa = fc * 1000  # MPa → kPa... no, mantener en MPa

        # Área de acero para carga axial (sin momento por simplificación)
        # φPn = φ × 0.85 × [0.85×fc×(Ag-Ast) + fy×Ast] ≥ Qa_dis
        # Qa_dis en kN, fc en MPa, Ag en m², Ast en m²
        Ag_mm2 = Ag * 1e6
        Qa_kN  = Qa_dis

        # Despejar Ast: φ×0.85×(0.85fc(Ag-Ast)×1e-3 + fy×Ast×1e-3) = Qa_kN
        # → Ast = (Qa_kN/φ/0.85 - 0.85fc×Ag×1e-3) / (fy - 0.85fc) × 1e3/1e-3
        num_kN = Qa_kN / (phi_c * 0.85)
        Ast_mm2 = (num_kN - 0.85 * fc * Ag_mm2 * 1e-3) / (fy - 0.85 * fc) * 1e3
        Ast_mm2 = max(Ast_mm2, 0.0)

        As_min_mm2 = 0.008 * Ag_mm2   # ACI 10.9.1 para pilotes: 0.8%
        As_max_mm2 = 0.040 * Ag_mm2   # 4%

        Ast_req = max(Ast_mm2, As_min_mm2)
        Ast_dis_mm2 = min(Ast_req, As_max_mm2)
        rho_l = Ast_dis_mm2 / Ag_mm2

        # Seleccionar barras longitudinales (db ≥ 16 mm para pilotes)
        desc_long, n_long, Ast_dis_cm2 = _seleccionar_n_barras(Ast_dis_mm2 / 100, db_mm=16.0)

        # Espiral — ACI 10.9.3
        D_core = D - 2 * recub       # diámetro del núcleo [m]
        Ach_mm2 = math.pi * (D_core * 1000) ** 2 / 4
        rho_s_min = 0.45 * (Ag_mm2 / Ach_mm2 - 1) * fc / fy
        rho_s_min = max(rho_s_min, 0.012)  # mínimo práctico

        # Diámetro de la barra espiral (∅10 o ∅12 típico)
        db_esp = 10.0   # [mm]
        Ab_esp = math.pi * db_esp ** 2 / 4  # [mm²]
        # ρs = 4×Ab_esp / (D_core_mm × paso)
        D_core_mm = D_core * 1000
        paso = 4 * Ab_esp / (rho_s_min * D_core_mm)
        paso = min(max(paso, 40), 80)  # límites prácticos [mm]

        rc = ResultadoRC(
            D=D, Ag=Ag,
            Ast_req=Ast_req / 100,
            Ast_min=As_min_mm2 / 100,
            Ast_max=As_max_mm2 / 100,
            Ast_dis=Ast_dis_cm2,
            rho_l=rho_l,
            desc_long=desc_long,
            rho_s_min=rho_s_min,
            db_esp=db_esp,
            paso_esp=paso,
        )

        # ── Mensajes ─────────────────────────────────────────────────────
        rige_long = ("rige flexión/carga axial" if Ast_mm2 >= As_min_mm2 - 1e-6
                     else "rige As_mín (ACI 318-19 §10.6.1.1 — 0.8% para pilotes)")
        mensajes.append({"tipo": "ok", "texto":
            f"Armadura long.: {desc_long}  (As={Ast_dis_cm2:.2f} cm²) — {rige_long}"})

        if FS_axial >= FS_min:
            mensajes.append({"tipo": "ok",
                             "texto": f"Capacidad axial: Qu = {Qu:.1f} kN, FS = {FS_axial:.2f} ≥ {FS_min:.1f} ✓"})
        else:
            mensajes.append({"tipo": "error",
                             "texto": f"Capacidad axial insuficiente: FS = {FS_axial:.2f} < {FS_min:.1f}"})

        if H_lat > 0:
            if ok_lat:
                mensajes.append({"tipo": "ok",
                                 "texto": f"Capacidad lateral: Hu = {Hu:.1f} kN, FS = {FS_lat:.2f} ≥ 1.5 ✓"})
            else:
                mensajes.append({"tipo": "error",
                                 "texto": f"Capacidad lateral insuficiente: FS = {FS_lat:.2f} < 1.5"})

        if rho_l < 0.008:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"ρ_l = {rho_l*100:.2f}% < 0.8% — se usa mínimo ACI para pilotes"})
        elif rho_l > 0.04:
            mensajes.append({"tipo": "advertencia",
                             "texto": f"ρ_l = {rho_l*100:.2f}% > 4% — revisar sección del pilote"})
        else:
            mensajes.append({"tipo": "ok",
                             "texto": f"Cuantía longitudinal ρ = {rho_l*100:.2f}% dentro del rango ACI (0.8–4%) ✓"})

        if tipo_pilote_lat == 'largo':
            mensajes.append({"tipo": "advertencia",
                             "texto": "Pilote largo (flexible): la resistencia lateral la controla My. Aumentar D o As mejora Hu."})

        self.res = ResultadosPilote(
            D=D, L=L, tipo=tipo,
            axial=axial, lateral=lateral, rc=rc,
            mensajes=mensajes,
        )
        self._inp = dict(
            D=D, L=L, tipo=tipo, capas=capas_inp,
            Qa_dis=Qa_dis, FS_min=FS_min,
            H_lat=H_lat, e_lat=e_lat,
            tipo_lat=tipo_lat, cu_lat=cu_lat,
            phi_lat=phi_lat, gamma_lat=gamma_lat,
            fc=fc, fy=fy, recub=recub,
        )
        return self
