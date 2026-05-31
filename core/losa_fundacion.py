"""
Motor de cálculo para Losa de Fundación (Mat Foundation).

Modos de entrada:
  'global'   — Carga total del edificio (P + momentos) sobre losa con geometría fija o auto
  'grilla'   — Grilla regular de columnas (nx × ny, separación uniforme)
  'uniforme' — Presión de servicio uniforme descendente (losa flotante / sótano)

Método estructural: ACI 318 — Losa plana invertida (strip method)
  Presión neta ascendente: qu_net = Pu / (B×L)  [kN/m²]
  Momento estático por metro de ancho: M0 = qu_net × l² / 8
  Distribución ACI:  M⁻ = 0.65 · M0 (apoyo → acero superior)
                     M⁺ = 0.35 · M0 (vano  → acero inferior)
  Voladizo de borde: M_cant = qu_net × a² / 2  (→ acero superior)
  4 capas de armadura: sup-X, inf-X, sup-Y, inf-Y
"""
from dataclasses import dataclass, field
import math
from core.normas.base import NormaBase
from core.zapata_aislada import MaterialHormigon, MaterialAcero


# ── Tabla de varillas ─────────────────────────────────────────────────────────

_VARILLAS = [
    ("Ø8mm",  0.503), ("Ø10mm", 0.785), ("Ø12mm", 1.131),
    ("Ø16mm", 2.011), ("Ø20mm", 3.142), ("Ø25mm", 4.909), ("Ø32mm", 8.042),
]


def _varilla(As_cm2: float, pref: str = "") -> tuple:
    if pref:
        for n, a in _VARILLAS:
            if pref in n:
                s = a / As_cm2 if As_cm2 > 0 else 0.20
                return n, max(0.07, min(0.50, math.floor(s * 100) / 100))
    for n, a in _VARILLAS:
        s = a / As_cm2 if As_cm2 > 0 else 0.25
        if 0.10 <= s <= 0.35:
            return n, math.floor(s * 100) / 100
    a = 4.909
    s = min(max(a / As_cm2, 0.10), 0.35) if As_cm2 > 0 else 0.25
    return "Ø25mm", math.floor(s * 100) / 100


def _dis_As(var: str, sep: float) -> float:
    for n, a in _VARILLAS:
        if n == var:
            return round(a / sep, 4) if sep > 0 else 0.0
    return 0.0


# ── Estructuras de entrada ────────────────────────────────────────────────────

@dataclass
class SueloLosa:
    qa:          float = 100.0   # Presión admisible [kN/m²]
    Df:          float = 0.50    # Profundidad de desplante [m]
    gamma_suelo: float = 18.0   # Peso específico del suelo [kN/m³]


@dataclass
class GeometriaLosa:
    L:             float = 0.0    # Largo en X [m]  (0 = auto en modo global)
    B:             float = 0.0    # Ancho en Y [m]
    h:             float = 0.40   # Espesor [m]  (0 = auto)
    recubrimiento: float = 0.075
    cx:            float = 0.35   # Sección columna dir. X [m]
    cy:            float = 0.35   # Sección columna dir. Y [m]
    lx_span:       float = 5.0    # Luz de diseño en X [m]
    ly_span:       float = 5.0    # Luz de diseño en Y [m]
    vuelo_x:       float = 0.50   # Voladizo borde en X [m]
    vuelo_y:       float = 0.50   # Voladizo borde en Y [m]

    @property
    def d(self) -> float:
        return max(self.h - self.recubrimiento - 0.016, 0.05)


@dataclass
class CargaGlobal:
    """Modo A: carga axial total del edificio + momentos resultantes."""
    Pd:    float = 0.0    # Carga muerta total [kN]
    Pl:    float = 0.0    # Carga viva total [kN]
    Mdx:   float = 0.0   # Momento muerto respecto a eje X [kN·m]
    Mlx:   float = 0.0   # Momento vivo  respecto a eje X [kN·m]
    Mdy:   float = 0.0   # Momento muerto respecto a eje Y [kN·m]
    Mly:   float = 0.0   # Momento vivo  respecto a eje Y [kN·m]
    n_col: int   = 4     # Total de columnas (para P_col en punzonado)

    @property
    def Pser(self):   return self.Pd + self.Pl
    @property
    def Pu(self):     return 1.2 * self.Pd + 1.6 * self.Pl
    @property
    def Mser_x(self): return self.Mdx + self.Mlx
    @property
    def Mser_y(self): return self.Mdy + self.Mly
    @property
    def Mux(self):    return 1.2 * self.Mdx + 1.6 * self.Mlx
    @property
    def Muy(self):    return 1.2 * self.Mdy + 1.6 * self.Mly


@dataclass
class CargaGrilla:
    """Modo B: grilla regular nx × ny, carga total del edificio distribuida."""
    Pd_total:  float = 0.0
    Pl_total:  float = 0.0
    nx:        int   = 2      # Columnas en X
    ny:        int   = 2      # Columnas en Y
    spacing_x: float = 5.0   # Separación en X (entre ejes) [m]
    spacing_y: float = 5.0   # Separación en Y [m]
    vuelo_x:   float = 0.50  # Voladizo borde X [m]
    vuelo_y:   float = 0.50  # Voladizo borde Y [m]

    @property
    def n_col(self):  return self.nx * self.ny
    @property
    def L(self):      return (self.nx - 1) * self.spacing_x + 2 * self.vuelo_x
    @property
    def B(self):      return (self.ny - 1) * self.spacing_y + 2 * self.vuelo_y
    @property
    def Pd(self):     return self.Pd_total
    @property
    def Pl(self):     return self.Pl_total
    @property
    def Pser(self):   return self.Pd_total + self.Pl_total
    @property
    def Pu(self):     return 1.2 * self.Pd_total + 1.6 * self.Pl_total
    @property
    def Mser_x(self): return 0.0
    @property
    def Mser_y(self): return 0.0
    @property
    def Mux(self):    return 0.0
    @property
    def Muy(self):    return 0.0


@dataclass
class CargaUniforme:
    """Modo C: presión de servicio uniforme sobre la losa (losa flotante)."""
    q_D:   float = 0.0   # Componente carga muerta [kN/m²]
    q_L:   float = 0.0   # Componente carga viva  [kN/m²]
    n_col: int   = 0     # sin punzonado

    @property
    def q_serv(self):  return self.q_D + self.q_L
    @property
    def qu_net(self):  return 1.2 * self.q_D + 1.6 * self.q_L
    @property
    def Pser(self):    return 0.0
    @property
    def Pu(self):      return 0.0
    @property
    def Mser_x(self):  return 0.0
    @property
    def Mser_y(self):  return 0.0
    @property
    def Mux(self):     return 0.0
    @property
    def Muy(self):     return 0.0


# ── Resultados ────────────────────────────────────────────────────────────────

@dataclass
class ResultadosLosa:
    L: float = 0.0
    B: float = 0.0
    h: float = 0.0
    d: float = 0.0
    A: float = 0.0

    # Presiones de servicio (suelo)
    q_max:     float = 0.0
    q_min:     float = 0.0
    q_prom:    float = 0.0
    ok_presion: bool = False
    en_nucleo:  bool = True

    # Presión neta última para diseño estructural [kN/m²]
    qu_net_avg: float = 0.0
    qu_net_max: float = 0.0

    # Luces de diseño
    lx_diseno: float = 0.0
    ly_diseno: float = 0.0

    # Momentos de diseño [kN·m/m]
    Mu_sup_x:  float = 0.0   # acero superior en X  (máx de M⁻ y M_cant)
    Mu_inf_x:  float = 0.0   # acero inferior en X  (M⁺)
    Mu_sup_y:  float = 0.0   # acero superior en Y
    Mu_inf_y:  float = 0.0   # acero inferior en Y
    Mu_neg_x:  float = 0.0   # M⁻ interior en X (informativo)
    Mu_neg_y:  float = 0.0   # M⁻ interior en Y
    Mu_cant_x: float = 0.0   # M voladizo en X
    Mu_cant_y: float = 0.0   # M voladizo en Y

    # Armadura requerida [cm²/m]
    As_req_sup_x: float = 0.0
    As_req_inf_x: float = 0.0
    As_req_sup_y: float = 0.0
    As_req_inf_y: float = 0.0
    As_min:       float = 0.0

    # Armadura de diseño [cm²/m]
    As_dis_sup_x: float = 0.0
    As_dis_inf_x: float = 0.0
    As_dis_sup_y: float = 0.0
    As_dis_inf_y: float = 0.0

    # Varilla y separación
    var_sup_x: str = "";  sep_sup_x: float = 0.0
    var_inf_x: str = "";  sep_inf_x: float = 0.0
    var_sup_y: str = "";  sep_sup_y: float = 0.0
    var_inf_y: str = "";  sep_inf_y: float = 0.0

    # Punzonado (columna representativa más cargada)
    Pu_col:       float = 0.0
    Vu_punch:     float = 0.0
    phi_Vc_punch: float = 0.0
    ok_punzonado: bool  = True

    # Cortante unidireccional [kN/m]
    Vu_cx:    float = 0.0;  phi_Vc_cx: float = 0.0;  ok_cx: bool = True
    Vu_cy:    float = 0.0;  phi_Vc_cy: float = 0.0;  ok_cy: bool = True

    mensajes: list = field(default_factory=list)

    def msg(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"texto": texto, "tipo": tipo})


# ── Motor principal ───────────────────────────────────────────────────────────

class LosaFundacion:
    """Motor de cálculo para losa de fundación — 3 modos de entrada, ACI 318."""

    MODO_GLOBAL   = "global"
    MODO_GRILLA   = "grilla"
    MODO_UNIFORME = "uniforme"

    def __init__(
        self,
        modo:         str,
        carga,                    # CargaGlobal | CargaGrilla | CargaUniforme
        suelo:        SueloLosa,
        hormigon:     MaterialHormigon,
        acero:        MaterialAcero,
        norma:        NormaBase,
        geo:          GeometriaLosa,
        varilla_pref: str = "",
    ):
        self.modo         = modo
        self.carga        = carga
        self.suelo        = suelo
        self.hormigon     = hormigon
        self.acero        = acero
        self.norma        = norma
        self.geo          = geo
        self.varilla_pref = varilla_pref
        self.res          = ResultadosLosa()

    def calcular(self) -> ResultadosLosa:
        self._setup()
        if not self._presiones():
            return self.res
        for i in range(16):
            self._momentos()
            self._armadura()
            self._punzonado()
            self._cortante()
            ok = self.res.ok_punzonado and self.res.ok_cx and self.res.ok_cy
            if ok:
                break
            self.geo.h = math.ceil((self.geo.h + 0.05) / 0.05) * 0.05
            self.res.msg(f"↑ Iteración {i+1}: h → {self.geo.h:.2f} m por punzonado/cortante", "info")
        return self.res

    # ── 1. Setup de dimensiones ───────────────────────────────────────────────

    def _setup(self):
        res   = self.res
        suelo = self.suelo
        geo   = self.geo
        c     = self.carga

        # h mínimo si es 0
        if geo.h <= 0:
            lref = max(geo.lx_span, geo.ly_span)
            geo.h = math.ceil(max(0.30, lref / 20) / 0.05) * 0.05

        if self.modo == self.MODO_GRILLA:
            # Dimensiones y luces derivadas de la grilla
            geo.L       = round(c.L, 3)
            geo.B       = round(c.B, 3)
            geo.lx_span = c.spacing_x
            geo.ly_span = c.spacing_y
            geo.vuelo_x = c.vuelo_x
            geo.vuelo_y = c.vuelo_y

        elif self.modo == self.MODO_GLOBAL and (geo.L <= 0 or geo.B <= 0):
            # Auto-dimensionamiento básico
            q_neto = suelo.qa - suelo.Df * suelo.gamma_suelo
            if q_neto > 0:
                A_req = c.Pser * 1.10 / q_neto
                lado  = math.sqrt(A_req)
                geo.L = math.ceil(max(lado, 2.0) / 0.10) * 0.10
                geo.B = math.ceil(max(lado, 2.0) / 0.10) * 0.10

        res.L = geo.L
        res.B = geo.B
        res.h = geo.h
        res.d = geo.d
        res.A = geo.L * geo.B

    # ── 2. Presiones de servicio ─────────────────────────────────────────────

    def _presiones(self) -> bool:
        res   = self.res
        suelo = self.suelo
        geo   = self.geo
        c     = self.carga
        L, B  = geo.L, geo.B

        if L <= 0 or B <= 0:
            res.msg("ERROR: dimensiones de losa no válidas.", "error")
            return False

        Pp_m2 = geo.h * 24.0 + max(suelo.Df - geo.h, 0.0) * suelo.gamma_suelo

        # ── Modo Uniforme ────────────────────────────────────────────────────
        if self.modo == self.MODO_UNIFORME:
            q_soil = c.q_serv + Pp_m2
            res.q_max    = q_soil
            res.q_min    = q_soil
            res.q_prom   = q_soil
            res.ok_presion = q_soil <= suelo.qa
            # Presión neta última para diseño (edificio factorizado)
            res.qu_net_avg = c.qu_net
            res.qu_net_max = c.qu_net

        # ── Modos Global y Grilla ────────────────────────────────────────────
        else:
            Pser    = c.Pser
            P_total = Pser + L * B * Pp_m2

            qm  = P_total / (L * B)
            dqL = 6.0 * c.Mser_x / (B * L ** 2)   # variación a lo largo de X
            dqB = 6.0 * c.Mser_y / (L * B ** 2)   # variación a lo largo de Y

            q1 = qm + dqL + dqB   # esquina (+L/2, +B/2)
            q2 = qm + dqL - dqB
            q3 = qm - dqL + dqB
            q4 = qm - dqL - dqB

            res.q_max  = max(q1, q2, q3, q4)
            res.q_min  = min(q1, q2, q3, q4)
            res.q_prom = qm
            ex_rel = abs(c.Mser_x / Pser) / L if Pser > 0 else 0.0
            ey_rel = abs(c.Mser_y / Pser) / B if Pser > 0 else 0.0
            res.en_nucleo = (6 * ex_rel + 6 * ey_rel) <= 1.0

            if res.q_min < 0:
                res.msg(
                    f"⚠ Presión mínima negativa ({res.q_min:.1f} kN/m²): "
                    f"tracción en suelo — amplíe la losa o reduzca momentos.", "warn")

            res.ok_presion = res.q_max <= suelo.qa

            # Presión neta última para diseño (solo cargas estructurales, sin Pp)
            qu_avg = c.Pu / (L * B)
            dqL_u  = 6.0 * c.Mux / (B * L ** 2)
            dqB_u  = 6.0 * c.Muy / (L * B ** 2)
            res.qu_net_avg = qu_avg
            res.qu_net_max = qu_avg + abs(dqL_u) + abs(dqB_u)

        if res.ok_presion:
            res.msg(
                f"✔ Presión máx {res.q_max:.1f} kN/m² ≤ qa={suelo.qa:.0f} kN/m² "
                f"(ratio={res.q_max / suelo.qa * 100:.0f}%)", "ok")
        else:
            res.msg(
                f"✘ Presión máx {res.q_max:.1f} kN/m² > qa={suelo.qa:.0f} kN/m² "
                f"— ampliar losa", "error")
        return True

    # ── 3. Momentos de diseño ─────────────────────────────────────────────────

    def _momentos(self):
        """
        ACI 318 — strip method.
        M0  = wu · l² / 8  (momento estático por metro de ancho)
        M⁻  = 0.65 · M0   (apoyo → acero sup)
        M⁺  = 0.35 · M0   (vano  → acero inf)
        M_cant = wu · a² / 2  (voladizo → acero sup)
        """
        res = self.res
        geo = self.geo
        wu  = res.qu_net_avg   # presión neta última [kN/m²]

        lx  = geo.lx_span
        ly  = geo.ly_span
        ax  = geo.vuelo_x
        ay  = geo.vuelo_y

        M0x = wu * lx ** 2 / 8.0
        M0y = wu * ly ** 2 / 8.0

        Mu_neg_x  = 0.65 * M0x
        Mu_pos_x  = 0.35 * M0x
        Mu_neg_y  = 0.65 * M0y
        Mu_pos_y  = 0.35 * M0y
        Mu_cant_x = wu * ax ** 2 / 2.0 if ax > 0.001 else 0.0
        Mu_cant_y = wu * ay ** 2 / 2.0 if ay > 0.001 else 0.0

        res.lx_diseno  = lx
        res.ly_diseno  = ly
        res.Mu_neg_x   = Mu_neg_x
        res.Mu_neg_y   = Mu_neg_y
        res.Mu_cant_x  = Mu_cant_x
        res.Mu_cant_y  = Mu_cant_y
        res.Mu_inf_x   = Mu_pos_x
        res.Mu_inf_y   = Mu_pos_y
        # El acero superior debe resistir el mayor entre negativo interior y voladizo
        res.Mu_sup_x   = max(Mu_neg_x, Mu_cant_x)
        res.Mu_sup_y   = max(Mu_neg_y, Mu_cant_y)

    # ── 4. Armadura ──────────────────────────────────────────────────────────

    def _armadura(self):
        res   = self.res
        geo   = self.geo
        norma = self.norma
        fck   = self.hormigon.fck
        fy    = self.acero.fy
        d     = geo.d

        res.h = geo.h
        res.d = d

        As_min = norma.area_acero_minimo(fck, fy, 1.0, d)
        res.As_min = As_min

        def layer(Mu: float) -> float:
            if Mu < 0.01:
                return As_min
            return max(norma.area_acero_flexion(Mu, d, fck, fy), As_min)

        As_sup_x = layer(res.Mu_sup_x)
        As_inf_x = layer(res.Mu_inf_x)
        As_sup_y = layer(res.Mu_sup_y)
        As_inf_y = layer(res.Mu_inf_y)

        res.As_req_sup_x = As_sup_x
        res.As_req_inf_x = As_inf_x
        res.As_req_sup_y = As_sup_y
        res.As_req_inf_y = As_inf_y

        res.var_sup_x, res.sep_sup_x = _varilla(As_sup_x, self.varilla_pref)
        res.var_inf_x, res.sep_inf_x = _varilla(As_inf_x, self.varilla_pref)
        res.var_sup_y, res.sep_sup_y = _varilla(As_sup_y, self.varilla_pref)
        res.var_inf_y, res.sep_inf_y = _varilla(As_inf_y, self.varilla_pref)

        res.As_dis_sup_x = _dis_As(res.var_sup_x, res.sep_sup_x)
        res.As_dis_inf_x = _dis_As(res.var_inf_x, res.sep_inf_x)
        res.As_dis_sup_y = _dis_As(res.var_sup_y, res.sep_sup_y)
        res.As_dis_inf_y = _dis_As(res.var_inf_y, res.sep_inf_y)

    # ── 5. Punzonado ─────────────────────────────────────────────────────────

    def _punzonado(self):
        res  = self.res
        geo  = self.geo
        c    = self.carga
        d    = geo.d
        cx   = geo.cx
        cy   = geo.cy

        if self.modo == self.MODO_UNIFORME or c.n_col == 0:
            res.ok_punzonado = True
            res.msg("ℹ Punzonado: sin columnas — no aplica.", "info")
            return

        # Carga por columna representativa (promedio)
        Pu_col  = c.Pu / c.n_col
        qu_avg  = res.qu_net_avg
        # Fuerza neta de punzonado
        Vu = max(Pu_col - qu_avg * (cx + d) * (cy + d), 0.0)
        # Perímetro crítico a d/2 de la cara de la columna
        b0 = 2.0 * ((cx + d) + (cy + d))

        phi_Vc = self.norma.resistencia_punzonado(self.hormigon.fck, b0, d, cx, cy)

        res.Pu_col       = Pu_col
        res.Vu_punch     = Vu
        res.phi_Vc_punch = phi_Vc
        res.ok_punzonado = Vu <= phi_Vc

        if res.ok_punzonado:
            r = Vu / phi_Vc * 100 if phi_Vc > 0 else 0
            res.msg(f"✔ Punzonado: Vu={Vu:.1f} kN ≤ φVc={phi_Vc:.1f} kN (ratio={r:.0f}%)", "ok")
        else:
            res.msg(f"✘ Punzonado: Vu={Vu:.1f} kN > φVc={phi_Vc:.1f} kN — aumentar h", "error")

    # ── 6. Cortante unidireccional ────────────────────────────────────────────

    def _cortante(self):
        """Sección crítica a distancia d de la cara de columna."""
        res  = self.res
        geo  = self.geo
        d    = geo.d
        wu   = res.qu_net_avg
        cx   = geo.cx
        cy   = geo.cy

        def check(span, c_dim, attr_vu, attr_phi, attr_ok, dir_label):
            brazo = span / 2.0 - c_dim / 2.0 - d
            Vu    = max(wu * brazo, 0.0)
            phi_Vc = self.norma.resistencia_cortante_unidireccional(
                self.hormigon.fck, 1.0, d)
            setattr(res, attr_vu,  Vu)
            setattr(res, attr_phi, phi_Vc)
            setattr(res, attr_ok,  Vu <= phi_Vc)
            ok = Vu <= phi_Vc
            if ok:
                res.msg(f"✔ Cortante 1D dir.{dir_label}: Vu={Vu:.1f} kN/m ≤ φVc={phi_Vc:.1f} kN/m", "ok")
            else:
                res.msg(f"✘ Cortante 1D dir.{dir_label}: Vu={Vu:.1f} kN/m > φVc={phi_Vc:.1f} kN/m — aumentar h", "error")

        check(geo.lx_span, cx, "Vu_cx", "phi_Vc_cx", "ok_cx", "X")
        check(geo.ly_span, cy, "Vu_cy", "phi_Vc_cy", "ok_cy", "Y")
