"""
Motor de cálculo para Zapata Excéntrica (Eccentric Footing).

Modelo: zapata rectangular B×L bajo carga axial + momento biaxial.
  - Distribución lineal de presiones (Navier)
  - Contacto parcial cuando ex > L/6 (Meyerhof, solo caso uniaxial Mx)
  - Diseño de armadura en dirección L (principal) y dirección B (secundaria)
"""
from dataclasses import dataclass, field
import math
import numpy as np
from core.normas.base import NormaBase
from core.zapata_aislada import MaterialHormigon, MaterialAcero


_VARILLAS = [
    ("Ø8mm",  0.503), ("Ø10mm", 0.785), ("Ø12mm", 1.131),
    ("Ø16mm", 2.011), ("Ø20mm", 3.142), ("Ø25mm", 4.909), ("Ø32mm", 8.042),
]


def _seleccionar_varilla(As_cm2_por_m: float, varilla_forzada: str = "") -> tuple:
    if varilla_forzada:
        for nombre, area in _VARILLAS:
            if varilla_forzada in nombre:
                sep = area / As_cm2_por_m if As_cm2_por_m > 0 else 0.20
                sep = max(0.07, min(0.50, sep))
                return nombre, np.floor(sep * 100) / 100
    mejor = None
    for nombre, area in _VARILLAS:
        sep = area / As_cm2_por_m if As_cm2_por_m > 0 else 0.30
        if 0.10 <= sep <= 0.35:
            mejor = (nombre, sep)
            break
    if mejor is None:
        area = 4.909
        sep = min(max(area / As_cm2_por_m, 0.10), 0.35) if As_cm2_por_m > 0 else 0.25
        mejor = ("Ø25mm", sep)
    return mejor[0], np.floor(mejor[1] * 100) / 100


# ─── Estructuras de entrada ───────────────────────────────────────────────────

@dataclass
class CargaExcentrica:
    """Carga axial + momentos biaxiales."""
    Pd:  float = 200.0   # Carga muerta [kN]
    Pl:  float = 100.0   # Carga viva [kN]
    Mdx: float = 40.0   # Momento muerto en dirección L [kN·m]
    Mlx: float = 20.0   # Momento vivo  en dirección L [kN·m]
    Mdy: float = 0.0    # Momento muerto en dirección B [kN·m]
    Mly: float = 0.0    # Momento vivo  en dirección B [kN·m]

    @property
    def Pser(self) -> float:  return self.Pd + self.Pl

    @property
    def Mser_x(self) -> float: return self.Mdx + self.Mlx

    @property
    def Mser_y(self) -> float: return self.Mdy + self.Mly

    @property
    def Pu(self) -> float:  return 1.2 * self.Pd + 1.6 * self.Pl

    @property
    def Mux(self) -> float: return 1.2 * self.Mdx + 1.6 * self.Mlx

    @property
    def Muy(self) -> float: return 1.2 * self.Mdy + 1.6 * self.Mly

    @property
    def ex(self) -> float:
        """Excentricidad de servicio en dirección L [m]."""
        return self.Mser_x / self.Pser if self.Pser > 0 else 0.0

    @property
    def ey(self) -> float:
        """Excentricidad de servicio en dirección B [m]."""
        return self.Mser_y / self.Pser if self.Pser > 0 else 0.0


@dataclass
class ColumnaExcentrica:
    """Dimensiones de la columna."""
    cx: float = 0.35   # Dimensión en dirección L [m]
    cy: float = 0.35   # Dimensión en dirección B [m]


@dataclass
class SueloExcentrica:
    """Parámetros del suelo de fundación."""
    qa: float = 120.0          # Presión admisible [kN/m²]
    Df: float = 1.20           # Profundidad de empotramiento [m]
    gamma_suelo: float = 18.0  # Peso específico [kN/m³]


@dataclass
class GeometriaExcentrica:
    """Dimensiones de la zapata."""
    B_fijo: float = 0.0        # Ancho fijo (0 = auto) [m]
    L_fijo: float = 0.0        # Largo fijo (0 = auto) [m]
    h: float = 0.50            # Peralte total [m]
    recubrimiento: float = 0.075

    @property
    def d(self) -> float:
        return self.h - self.recubrimiento - 0.010  # ~Ø20 mm


# ─── Resultado ────────────────────────────────────────────────────────────────

@dataclass
class ResultadosZapataExcentrica:
    B: float = 0.0
    L: float = 0.0
    h: float = 0.0
    d: float = 0.0
    A: float = 0.0

    # Excentricidades de servicio y última
    ex: float = 0.0
    ey: float = 0.0
    ex_u: float = 0.0
    ey_u: float = 0.0

    # Contacto
    tipo_contacto: str = "total"
    en_nucleo: bool = True
    L_ef: float = 0.0    # longitud efectiva de contacto para contacto parcial [m]

    # Presiones de servicio — 4 esquinas (eje: +L/2 = lado del momento positivo)
    q_neto: float = 0.0
    q1: float = 0.0   # (+L/2, +B/2) — máxima
    q2: float = 0.0   # (+L/2, -B/2)
    q3: float = 0.0   # (-L/2, +B/2)
    q4: float = 0.0   # (-L/2, -B/2) — mínima
    q_max: float = 0.0
    q_min: float = 0.0
    ok_presion: bool = False
    ok_tension: bool = True

    # Presiones últimas (diseño)
    q1u: float = 0.0
    q2u: float = 0.0
    q3u: float = 0.0
    q4u: float = 0.0
    q_max_u: float = 0.0
    q_min_u: float = 0.0

    # Punzonado
    bo: float = 0.0
    Vpu: float = 0.0
    phi_Vpn: float = 0.0
    ok_punzonado: bool = False
    rel_punzonado: float = 0.0

    # Cortante unidireccional
    Vu_L: float = 0.0
    Vu_B: float = 0.0
    phi_Vn: float = 0.0
    ok_cortante_L: bool = False
    ok_cortante_B: bool = False

    # Flexión — dirección L (barras paralelas a L, resistiendo Mu_L)
    Mu_L: float = 0.0
    As_req_L: float = 0.0
    As_min_L: float = 0.0
    As_dis_L: float = 0.0
    varilla_L: str = ""
    sep_L: float = 0.0
    n_barras_L: int = 0

    # Flexión — dirección B (barras paralelas a B, resistiendo Mu_B)
    Mu_B: float = 0.0
    As_req_B: float = 0.0
    As_min_B: float = 0.0
    As_dis_B: float = 0.0
    varilla_B: str = ""
    sep_B: float = 0.0
    n_barras_B: int = 0

    mensajes: list = field(default_factory=list)

    def agregar_mensaje(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"tipo": tipo, "texto": texto})


# ─── Motor principal ──────────────────────────────────────────────────────────

class ZapataExcentricaRectangular:
    """
    Diseña una zapata rectangular bajo carga axial + momento biaxial.

    Convención de ejes:
      L  — dimensión en el plano del momento principal (Mx)
      B  — dimensión transversal (Mx⊥)
      ex = Mser_x / Pser  (excentricidad en L)
      ey = Mser_y / Pser  (excentricidad en B)

    Distribución de presiones (Navier):
      q(x,y) = P/(BL) + 12·Mx·x/(BL³) + 12·My·y/(LB³)
    """

    def __init__(
        self,
        carga: CargaExcentrica,
        columna: ColumnaExcentrica,
        suelo: SueloExcentrica,
        hormigon: MaterialHormigon,
        acero: MaterialAcero,
        norma: NormaBase,
        geo: GeometriaExcentrica,
        varilla_pref: str = "",
    ):
        self.carga    = carga
        self.columna  = columna
        self.suelo    = suelo
        self.hormigon = hormigon
        self.acero    = acero
        self.norma    = norma
        self.geo      = geo
        self.res      = ResultadosZapataExcentrica()
        self.varilla_pref = varilla_pref

    # ── Método principal ─────────────────────────────────────────────────────

    def calcular(self) -> ResultadosZapataExcentrica:
        self._dimensionar()
        if self.res.B == 0:
            return self.res

        for i in range(8):
            self._presiones()
            self._verificar_punzonado()
            self._verificar_cortante()
            if self.res.ok_punzonado and self.res.ok_cortante_L and self.res.ok_cortante_B:
                break
            self.geo.h += 0.05
            self.res.agregar_mensaje(
                f"↑ Iteración {i+1}: aumentando h a {self.geo.h:.2f} m", "info")

        self.geo.h = math.ceil(self.geo.h / 0.05) * 0.05
        self._presiones()
        self._verificar_punzonado()
        self._verificar_cortante()
        self._armadura()
        return self.res

    # ── 1. Dimensionamiento ──────────────────────────────────────────────────

    def _dimensionar(self):
        res     = self.res
        carga   = self.carga
        suelo   = self.suelo
        col     = self.columna
        geo     = self.geo

        q_neto = suelo.qa - suelo.Df * suelo.gamma_suelo
        res.q_neto = q_neto

        if q_neto <= 0:
            res.agregar_mensaje("ERROR: presión neta ≤ 0. Revisar Df y γ del suelo.", "error")
            return

        res.ex   = carga.ex
        res.ey   = carga.ey
        res.ex_u = carga.Mux / carga.Pu if carga.Pu > 0 else 0.0
        res.ey_u = carga.Muy / carga.Pu if carga.Pu > 0 else 0.0

        if geo.B_fijo > 0 and geo.L_fijo > 0:
            B = geo.B_fijo
            L = geo.L_fijo
        else:
            # Área inicial
            Pp_est = 0.10 * carga.Pser
            A0     = (carga.Pser + Pp_est) / q_neto

            # Mínimos (apoyo + vuelo de 15 cm + margen de núcleo)
            L_min = max(col.cx + 2 * 0.15, abs(carga.ex) * 6 * 1.20, 0.60)
            B_min = max(col.cy + 2 * 0.15, abs(carga.ey) * 6 * 1.20, 0.60)

            L0 = max(math.sqrt(A0), L_min)
            B0 = max(A0 / L0, B_min)
            L  = math.ceil(L0 / 0.05) * 0.05
            B  = math.ceil(B0 / 0.05) * 0.05

            # Iterar hasta satisfacer q_max ≤ qa
            for _ in range(40):
                q_test = (carga.Pser / (B * L)) * (
                    1 + 6 * abs(carga.ex) / L + 6 * abs(carga.ey) / B)
                if q_test <= suelo.qa:
                    break
                # Aumentar la dimensión que más reduce q_max
                if abs(carga.ex) / L >= abs(carga.ey) / B:
                    L += 0.05
                else:
                    B += 0.05

        res.B = B
        res.L = L
        res.h = geo.h
        res.d = geo.d
        res.A = B * L
        res.agregar_mensaje(
            f"ℹ Dimensiones: B={B:.2f} m × L={L:.2f} m  "
            f"(ex={carga.ex:.3f} m, ey={carga.ey:.3f} m)", "info")

    # ── 2. Presiones ─────────────────────────────────────────────────────────

    def _presiones(self):
        res   = self.res
        B, L  = res.B, res.L
        carga = self.carga
        suelo = self.suelo
        geo   = self.geo
        col   = self.columna

        res.h = geo.h
        res.d = geo.d

        # Presiones de servicio (incluye peso propio + relleno)
        Pp = B * L * geo.h * 24.0
        Ps = B * L * max(suelo.Df - geo.h, 0.0) * suelo.gamma_suelo
        P_total = carga.Pser + Pp + Ps

        # Variaciones en los bordes
        dqL = 6.0 * carga.Mser_x / (B * L**2)   # incremento en x=+L/2
        dqB = 6.0 * carga.Mser_y / (L * B**2)   # incremento en y=+B/2
        qm  = P_total / (B * L)

        res.q1 = qm + dqL + dqB   # (+L/2, +B/2)
        res.q2 = qm + dqL - dqB   # (+L/2, -B/2)
        res.q3 = qm - dqL + dqB   # (-L/2, +B/2)
        res.q4 = qm - dqL - dqB   # (-L/2, -B/2)

        res.q_max = max(res.q1, res.q2, res.q3, res.q4)
        res.q_min = min(res.q1, res.q2, res.q3, res.q4)

        # Verificación del núcleo central
        ex_abs = abs(carga.ex)
        ey_abs = abs(carga.ey)
        res.en_nucleo = (6 * ex_abs / L + 6 * ey_abs / B) <= 1.0

        # Contacto parcial (Meyerhof — solo uniaxial en L)
        if res.q_min < 0 and ey_abs < 1e-6:
            a = L / 2.0 - ex_abs
            if a > col.cx / 2:
                L_ef        = 3.0 * a
                q_parc      = 2.0 * P_total / (3.0 * B * a)
                res.tipo_contacto = "parcial"
                res.L_ef    = L_ef
                res.q_max   = q_parc
                res.q_min   = 0.0
                res.q1 = res.q2 = q_parc
                res.q3 = res.q4 = 0.0
                res.ok_tension = False
                res.agregar_mensaje(
                    f"⚠ Contacto parcial: ex={ex_abs:.3f} m > L/6={L/6:.3f} m. "
                    f"L_ef={L_ef:.2f} m, q_max={q_parc:.1f} kN/m²", "warn")
            else:
                res.tipo_contacto = "fuera de zapata"
                res.ok_tension = False
                res.agregar_mensaje(
                    "✘ Excentricidad excesiva: el resultante sale de la zapata.", "error")
                return
        elif res.q_min < 0:
            res.tipo_contacto = "parcial (biaxial)"
            res.ok_tension = False
            res.agregar_mensaje(
                f"⚠ Presión mínima negativa ({res.q_min:.1f} kN/m²): contacto parcial "
                f"biaxial. Amplíe zapata o reduzca momentos.", "warn")
        else:
            res.tipo_contacto = "total"
            res.ok_tension = True

        res.ok_presion = res.q_max <= suelo.qa
        if res.ok_presion:
            res.agregar_mensaje(
                f"✔ Presión máx {res.q_max:.1f} kN/m² ≤ qa={suelo.qa:.1f} kN/m² "
                f"(ratio={res.q_max/suelo.qa*100:.0f}%)", "ok")
        else:
            res.agregar_mensaje(
                f"✘ Presión máx {res.q_max:.1f} kN/m² > qa={suelo.qa:.1f} kN/m² — ampliar zapata", "error")

        # Presiones últimas (sin peso propio — solo carga de diseño)
        qm_u  = carga.Pu / (B * L)
        dqL_u = 6.0 * carga.Mux / (B * L**2)
        dqB_u = 6.0 * carga.Muy / (L * B**2)

        res.q1u = qm_u + dqL_u + dqB_u
        res.q2u = qm_u + dqL_u - dqB_u
        res.q3u = qm_u - dqL_u + dqB_u
        res.q4u = qm_u - dqL_u - dqB_u
        res.q_max_u = max(res.q1u, res.q2u, res.q3u, res.q4u)
        res.q_min_u = min(res.q1u, res.q2u, res.q3u, res.q4u)

        # Pendiente real de la distribución: slope = dq/dx = 12·M/(B·L³)
        slope_L = 12.0 * carga.Mux / (B * L**3)   # [kN/m²/m]
        slope_B = 12.0 * carga.Muy / (L * B**3)   # [kN/m²/m]

        d  = geo.d
        cx = col.cx
        cy = col.cy

        # Cortante y momento en dirección L (integración analítica)
        aL = L / 2.0 - cx / 2.0
        if aL > 0:
            # Presión en la cara alta del pilar (x = +cx/2)
            q_cf_L  = qm_u + slope_L * cx / 2.0
            # Momento último en cara de pilar — lado de mayor presión
            res.Mu_L = max(0.0, q_cf_L * aL**2 / 2.0 + slope_L * aL**3 / 3.0)
            # Cortante a distancia d de la cara
            if aL > d:
                xd      = cx / 2.0 + d
                res.Vu_L = max(0.0,
                    qm_u * (L / 2.0 - xd) +
                    slope_L * ((L / 2.0)**2 - xd**2) / 2.0)
            else:
                res.Vu_L = 0.0
        else:
            res.Mu_L = 0.0
            res.Vu_L = 0.0

        # Cortante y momento en dirección B
        aB = B / 2.0 - cy / 2.0
        if aB > 0:
            q_cf_B  = qm_u + slope_B * cy / 2.0
            res.Mu_B = max(0.0, q_cf_B * aB**2 / 2.0 + slope_B * aB**3 / 3.0)
            if aB > d:
                yd      = cy / 2.0 + d
                res.Vu_B = max(0.0,
                    qm_u * (B / 2.0 - yd) +
                    slope_B * ((B / 2.0)**2 - yd**2) / 2.0)
            else:
                res.Vu_B = 0.0
        else:
            res.Mu_B = 0.0
            res.Vu_B = 0.0

    # ── 3. Punzonado ─────────────────────────────────────────────────────────

    def _verificar_punzonado(self):
        res = self.res
        col = self.columna
        d   = self.geo.d
        B, L = res.B, res.L

        bo        = 2.0 * (col.cx + d) + 2.0 * (col.cy + d)
        res.bo    = bo
        q_avg_u   = self.carga.Pu / (B * L)
        area_int  = (col.cx + d) * (col.cy + d)
        Vpu       = q_avg_u * (B * L - area_int)
        res.Vpu   = Vpu

        phi_Vpn     = self.norma.resistencia_punzonado(
            fck=self.hormigon.fck, b0=bo, d=d,
            c1=col.cx, c2=col.cy)
        res.phi_Vpn     = phi_Vpn
        res.ok_punzonado  = Vpu <= phi_Vpn
        res.rel_punzonado = Vpu / phi_Vpn if phi_Vpn > 0 else 0.0

        if res.ok_punzonado:
            res.agregar_mensaje(
                f"✔ Punzonado: Vu={Vpu:.1f} kN ≤ φVn={phi_Vpn:.1f} kN "
                f"(ratio={res.rel_punzonado*100:.0f}%)", "ok")
        else:
            res.agregar_mensaje(
                f"✘ Punzonado: Vu={Vpu:.1f} kN > φVn={phi_Vpn:.1f} kN — aumentar h", "error")

    # ── 4. Cortante unidireccional ────────────────────────────────────────────

    def _verificar_cortante(self):
        res     = self.res
        d       = self.geo.d

        phi_Vn      = self.norma.resistencia_cortante_unidireccional(
            fck=self.hormigon.fck, bw=1.0, d=d)
        res.phi_Vn      = phi_Vn
        res.ok_cortante_L = res.Vu_L <= phi_Vn
        res.ok_cortante_B = res.Vu_B <= phi_Vn

        for lbl, Vu, ok in [("L", res.Vu_L, res.ok_cortante_L),
                              ("B", res.Vu_B, res.ok_cortante_B)]:
            if ok:
                res.agregar_mensaje(
                    f"✔ Cortante dir.{lbl}: Vu={Vu:.1f} kN/m ≤ φVn={phi_Vn:.1f} kN/m "
                    f"(ratio={Vu/phi_Vn*100:.0f}%)", "ok")
            else:
                res.agregar_mensaje(
                    f"✘ Cortante dir.{lbl}: Vu={Vu:.1f} kN/m > φVn={phi_Vn:.1f} kN/m — aumentar h", "error")

    # ── 5. Armadura ──────────────────────────────────────────────────────────

    def _armadura(self):
        res  = self.res
        fck  = self.hormigon.fck
        fy   = self.acero.fy
        d    = self.geo.d
        B, L = res.B, res.L

        # Dirección L (barras paralelas a L — n_barras_L barras a lo largo de B)
        As_req_L = self.norma.area_acero_flexion(Mu=res.Mu_L, d=d, fck=fck, fy=fy)
        As_min_L = self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d)
        As_dis_L = max(As_req_L, As_min_L)
        res.As_req_L = As_req_L
        res.As_min_L = As_min_L
        res.As_dis_L = As_dis_L
        varilla_L, sep_L = _seleccionar_varilla(As_dis_L, self.varilla_pref)
        res.varilla_L    = varilla_L
        res.sep_L        = sep_L
        res.n_barras_L   = round(B / sep_L) if sep_L > 0 else 0
        res.agregar_mensaje(
            f"✔ Arm. dir.L: {varilla_L} @ {sep_L*100:.0f} cm  "
            f"(As={As_dis_L:.2f} cm²/m) — {res.n_barras_L} barras en B={B:.2f} m", "ok")

        # Dirección B (barras paralelas a B — n_barras_B barras a lo largo de L)
        As_req_B = self.norma.area_acero_flexion(Mu=res.Mu_B, d=d, fck=fck, fy=fy)
        As_min_B = self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d)
        As_dis_B = max(As_req_B, As_min_B)
        res.As_req_B = As_req_B
        res.As_min_B = As_min_B
        res.As_dis_B = As_dis_B
        varilla_B, sep_B = _seleccionar_varilla(As_dis_B, self.varilla_pref)
        res.varilla_B    = varilla_B
        res.sep_B        = sep_B
        res.n_barras_B   = round(L / sep_B) if sep_B > 0 else 0
        res.agregar_mensaje(
            f"✔ Arm. dir.B: {varilla_B} @ {sep_B*100:.0f} cm  "
            f"(As={As_dis_B:.2f} cm²/m) — {res.n_barras_B} barras en L={L:.2f} m", "ok")
