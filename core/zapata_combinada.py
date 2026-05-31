"""
Motor de cálculo para Zapata Combinada Rectangular.

Soporta dos columnas con cargas axiales.
Proceso de diseño:
  1. Dimensionamiento en planta — intenta centrar la resultante; si la geometría
     lo impide, calcula la distribución real de presiones (trapezoidal / triangular
     con posible despegue).
  2. Presiones de servicio reales (no asume uniformidad).
  3. Viga invertida — diagramas de cortante V(x) y momento M(x) longitudinal
     con la carga distribuida real (variable en x).
  4. Verificación de punzonado en cada columna usando qu local.
  5. Verificación de cortante unidireccional usando qu real.
  6. Diseño de armadura longitudinal (superior e inferior).
  7. Diseño de armadura transversal (franjas bajo cada columna) usando qu local.
"""

from dataclasses import dataclass, field
import numpy as np
from core.normas.base import NormaBase
from core.zapata_aislada import MaterialHormigon, MaterialAcero


# ─── Estructuras de entrada ─────────────────────────────────────────────────

@dataclass
class ColCombinada:
    """Carga y geometría de una columna de la zapata combinada."""
    Pd: float = 0.0       # Carga muerta [kN]
    Pl: float = 0.0       # Carga viva  [kN]
    ancho: float = 0.35   # bx [m]
    largo: float = 0.35   # by [m]

    @property
    def Pser(self): return self.Pd + self.Pl

    @property
    def Pu(self): return 1.2 * self.Pd + 1.6 * self.Pl


@dataclass
class SueloCombinada:
    qa: float = 150.0
    Df: float = 1.20
    gamma_suelo: float = 18.0


@dataclass
class GeometriaCombi:
    L_entre: float = 4.0        # Distancia entre ejes de columnas [m]
    B_fijo: float = 0.0         # Ancho fijo (0 = auto) [m]
    h: float = 0.60             # Altura de la zapata [m]
    recubrimiento: float = 0.075
    col1_en_borde: bool = True  # Columna 1 en borde de propiedad

    @property
    def d(self): return self.h - self.recubrimiento - 0.008


# ─── Resultado ──────────────────────────────────────────────────────────────

@dataclass
class ResultadosZapataCombi:
    # Geometría calculada
    B: float = 0.0
    L: float = 0.0
    h: float = 0.0
    d1: float = 0.0    # borde izq → eje col1 [m]
    d2: float = 0.0    # borde izq → eje col2 [m]
    area: float = 0.0

    # Presiones de servicio
    q_neto: float = 0.0
    q_max: float = 0.0     # presión máxima real [kN/m²]
    q_min: float = 0.0     # presión mínima real (≥0) [kN/m²]
    a_efectiva: float = 0.0  # longitud de la zona en contacto [m] (≤ L)
    presion_uniforme: bool = True
    q_ultima: float = 0.0   # presión factorizada promedio (referencia)
    ok_presion: bool = False

    # Diagramas (listas para graficar)
    x_diag: list = field(default_factory=list)
    V_diag: list = field(default_factory=list)
    M_diag: list = field(default_factory=list)

    # Momentos críticos longitudinales
    Mu_neg1: float = 0.0    # Momento en cara col1 [kN·m]
    Mu_neg2: float = 0.0    # Momento en cara col2 [kN·m]
    Mu_pos: float = 0.0     # Momento positivo máximo [kN·m]
    x_Mu_pos: float = 0.0

    # Punzonado col1
    ok_punz1: bool = False
    rel_punz1: float = 0.0
    Vu_punz1: float = 0.0
    phi_Vn_punz1: float = 0.0

    # Punzonado col2
    ok_punz2: bool = False
    rel_punz2: float = 0.0
    Vu_punz2: float = 0.0
    phi_Vn_punz2: float = 0.0

    # Cortante unidireccional
    ok_cortante: bool = False
    rel_cortante: float = 0.0
    Vu_cort: float = 0.0
    phi_Vn_cort: float = 0.0

    # Armadura longitudinal
    Mu_long_top: float = 0.0
    Mu_long_bot: float = 0.0
    As_long_top_pm: float = 0.0   # cm²/m
    As_long_bot_pm: float = 0.0   # cm²/m
    varilla_long_top: str = ""
    sep_long_top: float = 0.0
    n_long_top: int = 0
    varilla_long_bot: str = ""
    sep_long_bot: float = 0.0
    n_long_bot: int = 0

    # Armadura transversal
    vol_trans1: float = 0.0
    vol_trans2: float = 0.0
    Mu_trans1: float = 0.0
    Mu_trans2: float = 0.0
    As_trans1: float = 0.0   # cm²/m
    As_trans2: float = 0.0   # cm²/m
    varilla_trans1: str = ""
    sep_trans1: float = 0.0
    varilla_trans2: str = ""
    sep_trans2: float = 0.0

    mensajes: list = field(default_factory=list)

    def agregar_mensaje(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"tipo": tipo, "texto": texto})


# ─── Motor principal ─────────────────────────────────────────────────────────

class ZapataCombinadaRectangular:
    """
    Diseña una zapata combinada rectangular bajo dos columnas.

    Calcula la distribución real de presiones (uniforme, trapezoidal o
    triangular con despegue) y usa esa distribución para todos los
    cálculos de V, M, punzonado, cortante y armadura.
    """

    def __init__(
        self,
        col1: ColCombinada,
        col2: ColCombinada,
        suelo: SueloCombinada,
        hormigon: MaterialHormigon,
        acero: MaterialAcero,
        norma: NormaBase,
        geo: GeometriaCombi,
        varilla_pref: str = "",
    ):
        self.col1 = col1
        self.col2 = col2
        self.suelo = suelo
        self.hormigon = hormigon
        self.acero = acero
        self.norma = norma
        self.geo = geo
        self.res = ResultadosZapataCombi()
        self.varilla_pref = varilla_pref

        # Factored pressure distribution parameters (set in _presiones)
        self._qu_left = 0.0   # factored pressure at x=0  [kN/m²]
        self._qu_right = 0.0  # factored pressure at x=L  [kN/m²]
        self._a_u = 0.0       # effective contact length for factored [m]
        self._e_u = 0.0       # eccentricity of factored resultant [m] (+ → left of center)

    # ── Método principal ────────────────────────────────────────────────────

    def calcular(self) -> ResultadosZapataCombi:
        self._dimensionar()
        if self.res.B == 0 or self.res.L == 0:
            return self.res
        self._presiones()

        for i in range(7):
            self._diagramas()
            self._punzonado()
            self._cortante()
            if self.res.ok_punz1 and self.res.ok_punz2 and self.res.ok_cortante:
                break
            self.geo.h += 0.05
            self.res.agregar_mensaje(
                f"↑ Iteración {i+1}: aumentando h a {self.geo.h:.2f} m", "info")
            self._presiones()  # recalcular distribución con nuevo h

        self.geo.h = np.ceil(self.geo.h / 0.05) * 0.05
        self.res.h = self.geo.h
        self._armadura_longitudinal()
        self._armadura_transversal()
        return self.res

    # ── 1. Dimensionamiento ─────────────────────────────────────────────────

    def _dimensionar(self):
        res = self.res
        col1, col2 = self.col1, self.col2
        geo = self.geo
        suelo = self.suelo

        d1 = col1.ancho / 2 if geo.col1_en_borde else 0.20
        d2 = d1 + geo.L_entre

        P1, P2 = col1.Pser, col2.Pser
        x_R = (P1 * d1 + P2 * d2) / (P1 + P2)

        # Longitud ideal (resultante centrada) y longitud mínima (contener col2)
        L_ideal = 2 * x_R
        L_min   = d2 + col2.ancho / 2
        L = np.ceil(max(L_ideal, L_min) / 0.05) * 0.05

        if L > L_ideal + 0.001:
            res.agregar_mensaje(
                f"⚠ La geometría impide centrar la resultante "
                f"(L_ideal={L_ideal:.2f} m < L_min={L_min:.2f} m). "
                f"Presión NO uniforme — se calcula distribución real.", "advertencia")

        q_neta = suelo.qa - suelo.Df * suelo.gamma_suelo
        res.q_neto = q_neta

        if q_neta <= 0:
            res.agregar_mensaje("ERROR: presión neta ≤ 0. Revisar Df y γ del suelo.", "error")
            return

        Pp = 0.10 * (P1 + P2)
        area_req = (P1 + P2 + Pp) / q_neta

        if geo.B_fijo > 0:
            B = geo.B_fijo
        else:
            B = area_req / L
            B_min = max(col1.largo, col2.largo) + 2 * 0.10
            B = max(B, B_min)
            B = np.ceil(B / 0.05) * 0.05

        res.B  = B
        res.L  = L
        res.h  = geo.h
        res.d1 = d1
        res.d2 = d2
        res.area = B * L

        res.agregar_mensaje(
            f"ℹ Zapata: {B:.2f} m × {L:.2f} m  (A={B*L:.2f} m²) | "
            f"Col1 en x={d1:.2f} m, Col2 en x={d2:.2f} m", "info")

    # ── 2. Presiones ─────────────────────────────────────────────────────────

    def _presiones(self):
        res = self.res
        col1, col2 = self.col1, self.col2
        suelo = self.suelo
        B, L = res.B, res.L
        d1, d2 = res.d1, res.d2

        gamma_h = 24.0
        Pp = B * L * self.geo.h * gamma_h
        Ps = suelo.Df * suelo.gamma_suelo * B * L - Pp

        # ── Servicio ───────────────────────────────────────────────────────
        P_ser = col1.Pser + col2.Pser + Pp + Ps
        # Pp y Ps son uniformes → actúan en L/2, no generan excentricidad adicional
        # La excentricidad viene de las cargas de columna
        P_col  = col1.Pser + col2.Pser
        x_R_col = (col1.Pser * d1 + col2.Pser * d2) / P_col if P_col > 0 else L/2
        # Con cargas uniformes incluidas:
        x_R_ser = (col1.Pser * d1 + col2.Pser * d2 + (Pp + Ps) * L/2) / P_ser
        e_ser = L/2 - x_R_ser  # + → resultante a la izquierda del centroide

        q_max_s, q_min_s, a_s = _distribucion_presion(P_ser, B, L, x_R_ser)
        res.q_max = q_max_s
        res.q_min = q_min_s
        res.a_efectiva = a_s
        res.presion_uniforme = (a_s >= L - 0.01) and (abs(q_max_s - q_min_s) / max(q_max_s, 1) < 0.05)

        if a_s < L - 0.01:
            res.agregar_mensaje(
                f"⚠ Presión triangular con despegue: zona activa = {a_s:.2f} m de {L:.2f} m. "
                f"Revisar diseño (ampliar L o usar zapata trapezoidal).", "advertencia")

        res.ok_presion = q_max_s <= suelo.qa
        if res.ok_presion:
            res.agregar_mensaje(
                f"✔ Presión máx {q_max_s:.1f} kN/m² ≤ qa={suelo.qa:.1f} kN/m² "
                f"(ratio={q_max_s/suelo.qa*100:.0f}%)", "ok")
        else:
            res.agregar_mensaje(
                f"✘ Presión {q_max_s:.1f} kN/m² > qa={suelo.qa:.1f} kN/m² — ampliar zapata", "error")

        # ── Factorizada (ACI: solo cargas de columna factorizadas) ─────────
        P_u = col1.Pu + col2.Pu
        x_R_u = (col1.Pu * d1 + col2.Pu * d2) / P_u if P_u > 0 else L/2
        e_u = L/2 - x_R_u

        qu_max, qu_min, a_u = _distribucion_presion(P_u, B, L, x_R_u)

        # Guardar para uso en _diagramas, _punzonado, _cortante, _armadura_transversal
        if e_u >= 0:  # alta presión a la izquierda (x=0)
            self._qu_left  = qu_max
            self._qu_right = qu_min
        else:         # alta presión a la derecha (x=L)
            self._qu_left  = qu_min
            self._qu_right = qu_max
        self._a_u = a_u
        self._e_u = e_u
        res.q_ultima = P_u / (B * L)  # promedio de referencia

    # ── Presión factorizada en posición x ──────────────────────────────────

    def _qu_at(self, x: float) -> float:
        """Presión factorizada del suelo en posición x [kN/m²]."""
        L = self.res.L
        a_u = self._a_u
        if a_u >= L - 0.001:
            # Trapezoidal (contacto completo)
            q = self._qu_left + (self._qu_right - self._qu_left) * x / L
            return max(q, 0.0)
        elif self._e_u >= 0:
            # Triangular, alta presión a la izquierda (x=0)
            if x <= a_u:
                return self._qu_left * (1.0 - x / a_u)
            return 0.0
        else:
            # Triangular, alta presión a la derecha (x=L)
            x_from_right = L - x
            if x_from_right <= a_u:
                return self._qu_right * (1.0 - x_from_right / a_u)
            return 0.0

    def _int_wu(self, x: float) -> float:
        """∫₀ˣ qu(t)·B dt — fuerza ascendente acumulada desde 0 hasta x [kN]."""
        B, L = self.res.B, self.res.L
        a_u = self._a_u

        if a_u >= L - 0.001:
            # Trapezoidal
            q0, qL = self._qu_left, self._qu_right
            return B * (q0 * x + (qL - q0) * x**2 / (2 * L))
        elif self._e_u >= 0:
            # Triangular, alta en izquierda
            xp = min(x, a_u)
            return B * self._qu_left * (xp - xp**2 / (2 * a_u))
        else:
            # Triangular, alta en derecha
            x0 = L - a_u  # inicio de zona de presión desde izquierda
            if x <= x0:
                return 0.0
            xp = min(x - x0, a_u)
            return B * self._qu_right * (xp - xp**2 / (2 * a_u))

    def _int2_wu(self, x: float) -> float:
        """∫₀ˣ [∫₀ˢ qu(t)·B dt] ds — para cálculo analítico de M(x) [kN·m]."""
        B, L = self.res.B, self.res.L
        a_u = self._a_u

        if a_u >= L - 0.001:
            q0, qL = self._qu_left, self._qu_right
            return B * (q0 * x**2 / 2 + (qL - q0) * x**3 / (6 * L))
        elif self._e_u >= 0:
            qm = self._qu_left
            if x <= a_u:
                return B * qm * (x**2 / 2 - x**3 / (6 * a_u))
            else:
                II_a = B * qm * a_u**2 / 3
                I_a  = B * qm * a_u / 2
                return II_a + I_a * (x - a_u)
        else:
            x0 = L - a_u
            if x <= x0:
                return 0.0
            qm = self._qu_right
            xp = min(x - x0, a_u)
            II_local = B * qm * (xp**2 / 2 - xp**3 / (6 * a_u))
            I_local  = B * qm * (xp - xp**2 / (2 * a_u))
            if x > x0 + a_u:
                # Past end of pressure zone
                II_a = B * qm * a_u**2 / 3
                I_a  = B * qm * a_u / 2
                return II_a + I_a * (x - (x0 + a_u))
            return II_local

    # ── 3. Diagramas V y M ────────────────────────────────────────────────────

    def _diagramas(self):
        res = self.res
        col1, col2 = self.col1, self.col2
        B, L, d1, d2 = res.B, res.L, res.d1, res.d2
        R1, R2 = col1.Pu, col2.Pu

        def V(x):
            v = self._int_wu(x)
            if x > d1: v -= R1
            if x > d2: v -= R2
            return v

        def M(x):
            m = self._int2_wu(x)
            if x > d1: m -= R1 * (x - d1)
            if x > d2: m -= R2 * (x - d2)
            return m

        xs = np.linspace(0, L, 400)
        Vs = np.vectorize(V)(xs)
        Ms = np.vectorize(M)(xs)

        res.x_diag = xs.tolist()
        res.V_diag = Vs.tolist()
        res.M_diag = Ms.tolist()

        # Momentos en caras de columnas
        x_f1l = max(d1 - col1.ancho / 2, 0.001)
        x_f1r = d1 + col1.ancho / 2
        x_f2l = d2 - col2.ancho / 2
        x_f2r = min(d2 + col2.ancho / 2, L - 0.001)

        res.Mu_neg1 = max(-M(x_f1l), 0.0)   # cara izquierda col1 (voladizo)
        res.Mu_neg2 = max(-M(x_f2r), 0.0)   # cara derecha col2 (voladizo)

        # Momento positivo máximo entre columnas: buscar V=0 en [x_f1r, x_f2l]
        # Intentar bisección numérica
        x_V0 = _bisection_V0(V, x_f1r + 0.001, x_f2l - 0.001)
        if x_V0 is not None:
            Mu_mid = M(x_V0)
            res.Mu_pos   = max(Mu_mid, 0.0)
            res.x_Mu_pos = x_V0
        else:
            xs_mid = xs[(xs > x_f1r) & (xs < x_f2l)]
            if len(xs_mid):
                Ms_mid = np.vectorize(M)(xs_mid)
                idx = int(np.argmax(Ms_mid))
                res.Mu_pos   = max(float(Ms_mid[idx]), 0.0)
                res.x_Mu_pos = float(xs_mid[idx])
            else:
                res.Mu_pos   = 0.0
                res.x_Mu_pos = (d1 + d2) / 2

    # ── 4. Punzonado ─────────────────────────────────────────────────────────

    def _chk_punzonado(self, col: ColCombinada, xc: float, label: str):
        d = self.geo.d
        B, L = self.res.B, self.res.L
        c1, c2 = col.ancho, col.largo

        # qu local en la posición de la columna
        qu_local = self._qu_at(xc)
        A_crit   = (c1 + d) * (c2 + d)
        Vu       = col.Pu - qu_local * A_crit

        b0     = 2 * ((c1 + d) + (c2 + d))
        phi_Vn = self.norma.resistencia_punzonado(
            fck=self.hormigon.fck, b0=b0, d=d, c1=c1, c2=c2)
        ok  = Vu <= phi_Vn
        rel = Vu / phi_Vn if phi_Vn > 0 else 0

        if ok:
            self.res.agregar_mensaje(
                f"✔ Punzonado {label}: Vu={Vu:.1f} kN ≤ φVn={phi_Vn:.1f} kN "
                f"(qu_local={qu_local:.0f} kN/m², ratio={rel:.2f})", "ok")
        else:
            self.res.agregar_mensaje(
                f"✘ Punzonado {label} FALLA: Vu={Vu:.1f} > φVn={phi_Vn:.1f} kN "
                f"(qu_local={qu_local:.0f} kN/m²)", "error")
        return Vu, phi_Vn, ok, rel

    def _punzonado(self):
        res = self.res
        res.Vu_punz1, res.phi_Vn_punz1, res.ok_punz1, res.rel_punz1 = \
            self._chk_punzonado(self.col1, res.d1, "Col1")
        res.Vu_punz2, res.phi_Vn_punz2, res.ok_punz2, res.rel_punz2 = \
            self._chk_punzonado(self.col2, res.d2, "Col2")

    # ── 5. Cortante unidireccional ────────────────────────────────────────────

    def _cortante(self):
        res = self.res
        d = self.geo.d
        B, L, d1, d2 = res.B, res.L, res.d1, res.d2
        col1, col2 = self.col1, self.col2
        R1, R2 = col1.Pu, col2.Pu

        def V(x):
            v = self._int_wu(x)
            if x > d1: v -= R1
            if x > d2: v -= R2
            return v

        candidates = []
        for xc in [
            d1 + col1.ancho / 2 + d,
            d2 - col2.ancho / 2 - d,
            d2 + col2.ancho / 2 + d,
            d1 - col1.ancho / 2 - d,
        ]:
            if 0 < xc < L:
                candidates.append(abs(V(xc)))

        Vu     = max(candidates) if candidates else 0.0
        phi_Vn = self.norma.resistencia_cortante_unidireccional(
            fck=self.hormigon.fck, bw=B, d=d)

        res.Vu_cort    = Vu
        res.phi_Vn_cort = phi_Vn
        res.rel_cortante = Vu / phi_Vn if phi_Vn > 0 else 0
        res.ok_cortante  = Vu <= phi_Vn

        if res.ok_cortante:
            res.agregar_mensaje(
                f"✔ Cortante: Vu={Vu:.1f} kN ≤ φVn={phi_Vn:.1f} kN "
                f"(ratio={res.rel_cortante:.2f})", "ok")
        else:
            res.agregar_mensaje(
                f"✘ Cortante FALLA: Vu={Vu:.1f} > φVn={phi_Vn:.1f} kN", "error")

    # ── 6. Armadura longitudinal ─────────────────────────────────────────────

    def _armadura_longitudinal(self):
        res = self.res
        d = self.geo.d
        B = res.B
        fck, fy = self.hormigon.fck, self.acero.fy

        Mu_top = max(res.Mu_neg1, res.Mu_neg2)
        res.Mu_long_top = Mu_top
        As_top = self.norma.area_acero_flexion(Mu=Mu_top, d=d, fck=fck, fy=fy) if Mu_top > 0 else 0
        As_top = max(As_top, self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d))
        res.As_long_top_pm = As_top
        res.varilla_long_top, res.sep_long_top = _seleccionar_varilla(As_top, self.varilla_pref)
        res.n_long_top = max(int(np.ceil(B / res.sep_long_top)) + 1, 3) if res.sep_long_top > 0 else 3

        Mu_bot = max(res.Mu_pos, 0)
        res.Mu_long_bot = Mu_bot
        As_bot = self.norma.area_acero_flexion(Mu=Mu_bot, d=d, fck=fck, fy=fy) if Mu_bot > 0 else 0
        As_bot = max(As_bot, self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d))
        res.As_long_bot_pm = As_bot
        res.varilla_long_bot, res.sep_long_bot = _seleccionar_varilla(As_bot, self.varilla_pref)
        res.n_long_bot = max(int(np.ceil(B / res.sep_long_bot)) + 1, 3) if res.sep_long_bot > 0 else 3

        res.agregar_mensaje(
            f"✔ Armadura long. superior: {res.varilla_long_top} @ {res.sep_long_top*100:.0f} cm "
            f"(As={As_top:.2f} cm²/m)", "ok")
        res.agregar_mensaje(
            f"✔ Armadura long. inferior: {res.varilla_long_bot} @ {res.sep_long_bot*100:.0f} cm "
            f"(As={As_bot:.2f} cm²/m)", "ok")

    # ── 7. Armadura transversal ─────────────────────────────────────────────

    def _armadura_transversal(self):
        res = self.res
        d = self.geo.d
        fck, fy = self.hormigon.fck, self.acero.fy
        B = res.B

        for col, xc, attr_vol, attr_Mu, attr_As, attr_v, attr_s, label in [
            (self.col1, res.d1, "vol_trans1", "Mu_trans1", "As_trans1",
             "varilla_trans1", "sep_trans1", "Col1"),
            (self.col2, res.d2, "vol_trans2", "Mu_trans2", "As_trans2",
             "varilla_trans2", "sep_trans2", "Col2"),
        ]:
            vol_t = (B - col.largo) / 2
            # qu local en la posición de la columna
            qu_local = self._qu_at(xc)
            Mu_t = qu_local * vol_t**2 / 2   # kN·m/m

            As_pm = self.norma.area_acero_flexion(Mu=Mu_t, d=d, fck=fck, fy=fy) if Mu_t > 0 else 0
            As_pm = max(As_pm, self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d))
            varilla, sep = _seleccionar_varilla(As_pm, self.varilla_pref)

            setattr(res, attr_vol, vol_t)
            setattr(res, attr_Mu, Mu_t)
            setattr(res, attr_As, As_pm)
            setattr(res, attr_v, varilla)
            setattr(res, attr_s, sep)

            res.agregar_mensaje(
                f"✔ Trans. {label}: {varilla} @ {sep*100:.0f} cm "
                f"(As={As_pm:.2f} cm²/m, voladizo={vol_t:.2f} m, "
                f"qu_local={qu_local:.0f} kN/m²)", "ok")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _distribucion_presion(P_total: float, B: float, L: float, x_R: float):
    """
    Calcula q_max, q_min y longitud efectiva de contacto a partir del punto
    de aplicación de la resultante x_R (medido desde el borde izquierdo).

    Retorna (q_max, q_min, a_efectiva):
      - Uniforme:    q_max ≈ q_min, a = L
      - Trapezoidal: q_max > q_min ≥ 0, a = L
      - Triangular:  q_min = 0, a < L (despegue parcial)
    """
    q_avg = P_total / (B * L)
    e = L / 2 - x_R   # excentricidad (+: resultante a la izq del centroide)

    ratio = abs(6 * e / L)

    if ratio < 0.01:
        return q_avg, q_avg, L

    if ratio <= 1.0:
        q_max = q_avg * (1 + 6 * e / L)
        q_min = q_avg * (1 - 6 * e / L)
        return max(q_max, 0.0), max(q_min, 0.0), L

    # Triangular con despegue
    if e > 0:
        # Alta presión a la izquierda; zona activa desde x=0 hasta x=a
        a = min(3 * x_R, L)
    else:
        # Alta presión a la derecha; zona activa desde x=L-a hasta x=L
        a = min(3 * (L - x_R), L)

    a = max(a, 0.001)
    q_max = 2 * P_total / (B * a)
    return q_max, 0.0, a


def _bisection_V0(V_func, xa: float, xb: float, tol: float = 1e-4):
    """Busca el cero de V en [xa, xb] por bisección. Retorna None si no hay cruce."""
    fa, fb = V_func(xa), V_func(xb)
    if fa * fb > 0:
        return None
    for _ in range(50):
        xm = (xa + xb) / 2
        fm = V_func(xm)
        if abs(fm) < tol or (xb - xa) / 2 < tol:
            return xm
        if fa * fm < 0:
            xb, fb = xm, fm
        else:
            xa, fa = xm, fm
    return (xa + xb) / 2


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
