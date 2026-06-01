"""
Motor de cálculo para Encepado de Pilotes (Pile Cap).

Modos:
  'auto'   — El software determina n_pilotes = ceil(Pser * 1.10 / Qa)
             y elige la grilla nx×ny óptima (más cuadrada posible).
  'manual' — El usuario especifica nx, ny, spacing_x, spacing_y,
             vuelo_x, vuelo_y.

Método estructural: ACI 318 — Método de bielas y tirantes / flexión directa.
  Distribución de cargas: modelo rígido (pilote i recibe Pi = P/n ± M·x/Σx²).
  Cortante unidireccional: sección crítica a d de cara de columna.
  Punzonado de columna: perímetro a d/2 de cara de columna.
  Punzonado de pilote:  perímetro circular a d/2 de cara de pilote.
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


# ── Grilla automática ─────────────────────────────────────────────────────────

def _auto_grilla(n_req: int) -> tuple:
    """Square-first arrangement: minimize |nx-ny| first, then minimize total piles."""
    n_req = max(n_req, 2)
    best = None
    for ny in range(1, n_req + 1):
        nx = math.ceil(n_req / ny)
        total = nx * ny
        diff  = abs(nx - ny)
        # Primary: most square (min diff). Secondary: least waste (min total).
        if best is None or diff < best[3] or (diff == best[3] and total < best[2]):
            best = (nx, ny, total, diff)
    return max(best[0], best[1]), min(best[0], best[1])


# ── Estructuras de entrada ────────────────────────────────────────────────────

@dataclass
class CargaEncepado:
    """Cargas aplicadas en la base de la columna (nivel de encepado)."""
    Pd:  float = 0.0   # Carga axial muerta [kN]
    Pl:  float = 0.0   # Carga axial viva  [kN]
    Mdx: float = 0.0   # Momento muerto respecto a eje X [kN·m]
    Mlx: float = 0.0   # Momento vivo  respecto a eje X [kN·m]
    Mdy: float = 0.0   # Momento muerto respecto a eje Y [kN·m]
    Mly: float = 0.0   # Momento vivo  respecto a eje Y [kN·m]

    @property
    def Pser(self):    return self.Pd + self.Pl
    @property
    def Pu(self):      return 1.2 * self.Pd + 1.6 * self.Pl
    @property
    def Mser_x(self):  return self.Mdx + self.Mlx
    @property
    def Mser_y(self):  return self.Mdy + self.Mly
    @property
    def Mux(self):     return 1.2 * self.Mdx + 1.6 * self.Mlx
    @property
    def Muy(self):     return 1.2 * self.Mdy + 1.6 * self.Mly


@dataclass
class ColumnaEncepado:
    """Geometría de la columna que apoya sobre el encepado."""
    cx: float = 0.40   # Dimensión en dirección X [m]
    cy: float = 0.40   # Dimensión en dirección Y [m]


@dataclass
class PiloteConfig:
    """Configuración geométrica y capacidad de los pilotes."""
    D:         float = 0.40    # Diámetro del pilote [m]
    Qa:        float = 400.0   # Carga admisible de servicio por pilote [kN]
    modo:      str   = 'auto'  # 'auto' o 'manual'
    nx:        int   = 2       # Pilotes en dirección X (modo manual)
    ny:        int   = 2       # Pilotes en dirección Y (modo manual)
    spacing_x: float = 0.0     # Separación en X (0 = auto → 3*D) [m]
    spacing_y: float = 0.0     # Separación en Y (0 = auto → 3*D) [m]
    vuelo_x:   float = 0.0     # Vuelo borde X (0 = auto → max(D, 0.50)) [m]
    vuelo_y:   float = 0.0     # Vuelo borde Y (0 = auto → max(D, 0.50)) [m]


@dataclass
class GeometriaEncepado:
    """Geometría de la losa del encepado."""
    h:             float = 0.60    # Altura total del encepado [m]
    recubrimiento: float = 0.075   # Recubrimiento nominal [m]

    @property
    def d(self) -> float:
        return max(self.h - self.recubrimiento - 0.016, 0.05)


# ── Resultados ────────────────────────────────────────────────────────────────

@dataclass
class ResultadosEncepado:
    # Configuración de pilotes
    n:  int = 0
    nx: int = 0
    ny: int = 0
    spacing_x: float = 0.0
    spacing_y: float = 0.0
    vuelo_x:   float = 0.0
    vuelo_y:   float = 0.0

    # Geometría del encepado
    L: float = 0.0
    B: float = 0.0
    h: float = 0.0
    d: float = 0.0
    A: float = 0.0

    # Posiciones y cargas de pilotes
    pile_positions:  list = field(default_factory=list)   # [(x, y), ...]
    pile_loads_ser:  list = field(default_factory=list)   # [Pi_servicio, ...]
    pile_loads_ult:  list = field(default_factory=list)   # [Pi_último, ...]

    # Envolvente de cargas en pilotes
    P_max:   float = 0.0
    P_min:   float = 0.0
    P_max_u: float = 0.0
    P_min_u: float = 0.0

    # Verificaciones geotécnicas
    ok_capacidad: bool = False
    ok_tension:   bool = True

    # Momentos totales de diseño [kN·m]
    Mu_x: float = 0.0
    Mu_y: float = 0.0

    # Armadura
    As_min:   float = 0.0   # [cm²/m]
    As_req_x: float = 0.0
    As_dis_x: float = 0.0
    var_x:    str   = ""
    sep_x:    float = 0.0
    As_req_y: float = 0.0
    As_dis_y: float = 0.0
    var_y:    str   = ""
    sep_y:    float = 0.0
    n_barras_x: int = 0
    n_barras_y: int = 0

    # Cortante unidireccional
    Vu_x:     float = 0.0
    phi_Vc_x: float = 0.0
    ok_cx:    bool  = True
    Vu_y:     float = 0.0
    phi_Vc_y: float = 0.0
    ok_cy:    bool  = True

    # Punzonado por columna
    b0_col:        float = 0.0
    Vu_punch_col:  float = 0.0
    phi_Vc_col:    float = 0.0
    ok_punch_col:  bool  = True

    # Punzonado por pilote
    b0_pil:        float = 0.0
    Vu_punch_pil:  float = 0.0
    phi_Vc_pil:    float = 0.0
    ok_punch_pil:  bool  = True

    mensajes: list = field(default_factory=list)

    def msg(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"texto": texto, "tipo": tipo})


# ── Motor principal ───────────────────────────────────────────────────────────

class Encepado:
    """Motor de cálculo para encepado de pilotes — ACI 318, modelo rígido."""

    def __init__(
        self,
        carga:        CargaEncepado,
        columna:      ColumnaEncepado,
        pilote:       PiloteConfig,
        geo:          GeometriaEncepado,
        hormigon:     MaterialHormigon,
        acero:        MaterialAcero,
        norma:        NormaBase,
        varilla_pref: str = "",
    ):
        self.carga        = carga
        self.columna      = columna
        self.pilote       = pilote
        self.geo          = geo
        self.hormigon     = hormigon
        self.acero        = acero
        self.norma        = norma
        self.varilla_pref = varilla_pref
        self.res          = ResultadosEncepado()

    def calcular(self) -> ResultadosEncepado:
        self._setup()
        for i in range(16):
            if i > 0:
                self.res.mensajes = [
                    m for m in self.res.mensajes
                    if '↑' in m['texto']
                ]
            self._distribucion_cargas()
            self._momentos()
            self._armadura()
            self._cortante()
            self._punzonado_columna()
            self._punzonado_pilote()
            ok = (
                self.res.ok_cx and self.res.ok_cy
                and self.res.ok_punch_col and self.res.ok_punch_pil
                and self.res.ok_capacidad
            )
            if ok:
                break
            if not (self.res.ok_cx and self.res.ok_cy
                    and self.res.ok_punch_col and self.res.ok_punch_pil):
                geo_h_new = math.ceil((self.geo.h + 0.05) / 0.05) * 0.05
                self.res.msg(f"↑ Iter {i+1}: h → {geo_h_new:.2f} m (cortante/punzonado)", "info")
                self.geo.h = geo_h_new
            else:
                break
        self.res.h = self.geo.h
        self.res.d = self.geo.d
        return self.res

    # ── 1. Setup de geometría y grilla de pilotes ─────────────────────────────

    def _setup(self):
        pil = self.pilote
        geo = self.geo
        res = self.res
        D   = pil.D

        # Separaciones efectivas
        sx = pil.spacing_x if pil.spacing_x > 0 else max(3.0 * D, D + 0.50)
        sy = pil.spacing_y if pil.spacing_y > 0 else max(3.0 * D, D + 0.50)

        # Vuelos efectivos
        vx = pil.vuelo_x if pil.vuelo_x > 0 else max(D, 0.50)
        vy = pil.vuelo_y if pil.vuelo_y > 0 else max(D, 0.50)

        # Número y distribución de pilotes
        if pil.modo == 'auto':
            n_req = max(2, math.ceil(self.carga.Pser * 1.10 / pil.Qa))
            nx, ny = _auto_grilla(n_req)
        else:
            nx = max(1, pil.nx)
            ny = max(1, pil.ny)

        n = nx * ny
        L = (nx - 1) * sx + 2 * vx
        B = (ny - 1) * sy + 2 * vy

        # Posiciones de pilotes centradas en el origen
        positions = []
        for i in range(nx):
            for j in range(ny):
                x = -(nx - 1) / 2.0 * sx + i * sx
                y = -(ny - 1) / 2.0 * sy + j * sy
                positions.append((x, y))

        res.n          = n
        res.nx         = nx
        res.ny         = ny
        res.spacing_x  = sx
        res.spacing_y  = sy
        res.vuelo_x    = vx
        res.vuelo_y    = vy
        res.L          = L
        res.B          = B
        res.h          = geo.h
        res.d          = geo.d
        res.A          = L * B
        res.pile_positions = positions

        res.msg(
            f"ℹ Configuración: {nx}×{ny} = {n} pilotes  | "
            f"L={L:.2f} m  B={B:.2f} m  "
            f"sx={sx:.2f} m  sy={sy:.2f} m  "
            f"vx={vx:.2f} m  vy={vy:.2f} m",
            "info"
        )

    # ── 2. Distribución de cargas sobre pilotes ───────────────────────────────

    def _distribucion_cargas(self):
        res      = self.res
        carga    = self.carga
        geo      = self.geo
        n        = res.n
        L        = res.L
        B        = res.B
        positions = res.pile_positions

        # Peso propio del encepado
        Pp = L * B * geo.h * 24.0

        Pser_total = carga.Pser + Pp
        Pu_total   = carga.Pu + 1.2 * Pp

        sum_x2 = sum(x * x for x, y in positions) or 1e-12
        sum_y2 = sum(y * y for x, y in positions) or 1e-12

        loads_ser = []
        loads_ult = []
        for x, y in positions:
            Pi  = (Pser_total / n
                   + carga.Mser_x * y / sum_y2
                   + carga.Mser_y * x / sum_x2)
            Pui = (Pu_total / n
                   + carga.Mux * y / sum_y2
                   + carga.Muy * x / sum_x2)
            loads_ser.append(Pi)
            loads_ult.append(Pui)

        res.pile_loads_ser = loads_ser
        res.pile_loads_ult = loads_ult
        res.P_max   = max(loads_ser)
        res.P_min   = min(loads_ser)
        res.P_max_u = max(loads_ult)
        res.P_min_u = min(loads_ult)

        res.ok_capacidad = res.P_max <= self.pilote.Qa
        res.ok_tension   = res.P_min >= 0.0

        if res.ok_capacidad:
            ratio = res.P_max / self.pilote.Qa * 100 if self.pilote.Qa > 0 else 0
            res.msg(
                f"✔ Capacidad: P_max={res.P_max:.1f} kN ≤ Qa={self.pilote.Qa:.0f} kN "
                f"(ratio={ratio:.0f}%)", "ok"
            )
        else:
            res.msg(
                f"✘ Capacidad: P_max={res.P_max:.1f} kN > Qa={self.pilote.Qa:.0f} kN "
                f"— aumentar número de pilotes o Qa", "error"
            )

        if not res.ok_tension:
            res.msg(
                f"⚠ Tensión: P_min={res.P_min:.1f} kN < 0 — pilote en tracción", "warn"
            )

    # ── 3. Momentos de diseño ─────────────────────────────────────────────────

    def _momentos(self):
        res      = self.res
        cx       = self.columna.cx
        cy       = self.columna.cy
        positions = res.pile_positions
        loads_ult = res.pile_loads_ult

        # Mu_x: momento en la sección a la cara de la columna (x = ±cx/2)
        mu_x_pos = sum(
            Pui * (x - cx / 2.0)
            for (x, y), Pui in zip(positions, loads_ult)
            if x > cx / 2.0
        )
        mu_x_neg = sum(
            Pui * (-x - cx / 2.0)
            for (x, y), Pui in zip(positions, loads_ult)
            if x < -cx / 2.0
        )
        res.Mu_x = max(mu_x_pos, mu_x_neg, 0.0)

        # Mu_y: momento en la sección a la cara de la columna (y = ±cy/2)
        mu_y_pos = sum(
            Pui * (y - cy / 2.0)
            for (x, y), Pui in zip(positions, loads_ult)
            if y > cy / 2.0
        )
        mu_y_neg = sum(
            Pui * (-y - cy / 2.0)
            for (x, y), Pui in zip(positions, loads_ult)
            if y < -cy / 2.0
        )
        res.Mu_y = max(mu_y_pos, mu_y_neg, 0.0)

        res.msg(
            f"ℹ Momentos: Mu_x={res.Mu_x:.1f} kN·m  |  Mu_y={res.Mu_y:.1f} kN·m",
            "info"
        )

    # ── 4. Armadura de flexión ────────────────────────────────────────────────

    def _armadura(self):
        res   = self.res
        geo   = self.geo
        norma = self.norma
        fck   = self.hormigon.fck
        fy    = self.acero.fy
        d     = geo.d
        L     = res.L
        B     = res.B

        res.h = geo.h
        res.d = d

        As_min      = norma.area_acero_minimo(fck, fy, 1.0, d)
        res.As_min  = As_min

        # As por metro de ancho: Mu_x actúa sobre el ancho B; Mu_y actúa sobre el largo L
        As_flex_x = norma.area_acero_flexion(res.Mu_x / B if B > 0 else 0.0, d, fck, fy)
        As_flex_y = norma.area_acero_flexion(res.Mu_y / L if L > 0 else 0.0, d, fck, fy)
        As_req_x  = max(As_flex_x, As_min)
        As_req_y  = max(As_flex_y, As_min)

        res.As_req_x = As_req_x
        res.As_req_y = As_req_y

        res.var_x, res.sep_x = _varilla(As_req_x, self.varilla_pref)
        res.var_y, res.sep_y = _varilla(As_req_y, self.varilla_pref)

        res.As_dis_x = _dis_As(res.var_x, res.sep_x)
        res.As_dis_y = _dis_As(res.var_y, res.sep_y)

        res.n_barras_x = max(2, math.ceil(B / res.sep_x)) if res.sep_x > 0 else 0
        res.n_barras_y = max(2, math.ceil(L / res.sep_y)) if res.sep_y > 0 else 0

        rige_x = norma.rige_label(As_flex_x, As_min)
        rige_y = norma.rige_label(As_flex_y, As_min)
        res.msg(
            f"✔ Armadura X: {res.var_x} @ {res.sep_x*100:.0f} cm "
            f"(As={res.As_dis_x:.2f} cm²/m, n={res.n_barras_x}) — {rige_x}",
            "ok"
        )
        res.msg(
            f"✔ Armadura Y: {res.var_y} @ {res.sep_y*100:.0f} cm "
            f"(As={res.As_dis_y:.2f} cm²/m, n={res.n_barras_y}) — {rige_y}",
            "ok"
        )

    # ── 5. Cortante unidireccional ────────────────────────────────────────────

    def _cortante(self):
        """
        Sección crítica a d de la cara de la columna.
        Se suman las reacciones de pilotes cuyo centro cae más allá de la sección crítica.
        ACI 318-19 §13.2.7: pilote se cuenta completo si su centro está a más de d/2
        de la sección crítica (es decir, si |x_pil| >= c/2 + d/2).
        """
        res       = self.res
        geo       = self.geo
        cx        = self.columna.cx
        cy        = self.columna.cy
        d         = geo.d
        B         = res.B
        L         = res.L
        positions = res.pile_positions
        loads_ult = res.pile_loads_ult
        fck       = self.hormigon.fck
        norma     = self.norma

        # Dir X: sección a x = ±(cx/2 + d); pilotes contribuyen si |x| >= cx/2 + d/2
        x_crit = cx / 2.0 + d / 2.0
        Vu_x = sum(
            Pui for (x, y), Pui in zip(positions, loads_ult)
            if abs(x) >= x_crit
        )
        phi_Vc_x = norma.resistencia_cortante_unidireccional(fck, B, d)
        res.Vu_x     = Vu_x
        res.phi_Vc_x = phi_Vc_x
        res.ok_cx    = Vu_x <= phi_Vc_x

        if res.ok_cx:
            ratio = Vu_x / phi_Vc_x * 100 if phi_Vc_x > 0 else 0
            res.msg(
                f"✔ Cortante dir.X: Vu={Vu_x:.1f} kN ≤ φVc={phi_Vc_x:.1f} kN "
                f"(ratio={ratio:.0f}%)", "ok"
            )
        else:
            res.msg(
                f"✘ Cortante dir.X: Vu={Vu_x:.1f} kN > φVc={phi_Vc_x:.1f} kN "
                f"— aumentar h", "error"
            )

        # Dir Y: sección a y = ±(cy/2 + d); pilotes contribuyen si |y| >= cy/2 + d/2
        y_crit = cy / 2.0 + d / 2.0
        Vu_y = sum(
            Pui for (x, y), Pui in zip(positions, loads_ult)
            if abs(y) >= y_crit
        )
        phi_Vc_y = norma.resistencia_cortante_unidireccional(fck, L, d)
        res.Vu_y     = Vu_y
        res.phi_Vc_y = phi_Vc_y
        res.ok_cy    = Vu_y <= phi_Vc_y

        if res.ok_cy:
            ratio = Vu_y / phi_Vc_y * 100 if phi_Vc_y > 0 else 0
            res.msg(
                f"✔ Cortante dir.Y: Vu={Vu_y:.1f} kN ≤ φVc={phi_Vc_y:.1f} kN "
                f"(ratio={ratio:.0f}%)", "ok"
            )
        else:
            res.msg(
                f"✘ Cortante dir.Y: Vu={Vu_y:.1f} kN > φVc={phi_Vc_y:.1f} kN "
                f"— aumentar h", "error"
            )

    # ── 6. Punzonado por columna ──────────────────────────────────────────────

    def _punzonado_columna(self):
        res       = self.res
        geo       = self.geo
        cx        = self.columna.cx
        cy        = self.columna.cy
        d         = geo.d
        positions = res.pile_positions
        loads_ult = res.pile_loads_ult
        fck       = self.hormigon.fck
        norma     = self.norma

        b0_col = 2.0 * (cx + d) + 2.0 * (cy + d)

        # Pilotes dentro del perímetro crítico (no contribuyen a Vu)
        piles_inside = sum(
            Pui for (x, y), Pui in zip(positions, loads_ult)
            if abs(x) <= (cx + d) / 2.0 and abs(y) <= (cy + d) / 2.0
        )
        Vu_col     = max(sum(loads_ult) - piles_inside, 0.0)
        phi_Vc_col = norma.resistencia_punzonado(fck, b0_col, d, cx, cy)

        res.b0_col       = b0_col
        res.Vu_punch_col = Vu_col
        res.phi_Vc_col   = phi_Vc_col
        res.ok_punch_col = Vu_col <= phi_Vc_col

        if res.ok_punch_col:
            ratio = Vu_col / phi_Vc_col * 100 if phi_Vc_col > 0 else 0
            res.msg(
                f"✔ Punzonado columna: Vu={Vu_col:.1f} kN ≤ φVc={phi_Vc_col:.1f} kN "
                f"(b0={b0_col:.2f} m, ratio={ratio:.0f}%)", "ok"
            )
        else:
            res.msg(
                f"✘ Punzonado columna: Vu={Vu_col:.1f} kN > φVc={phi_Vc_col:.1f} kN "
                f"— aumentar h", "error"
            )

    # ── 7. Punzonado por pilote ───────────────────────────────────────────────

    def _punzonado_pilote(self):
        res     = self.res
        geo     = self.geo
        D       = self.pilote.D
        d       = geo.d
        fck     = self.hormigon.fck
        norma   = self.norma

        # Perímetro crítico a d/2 de la cara del pilote circular
        b0_pil    = math.pi * (D + d)
        Vu_pil    = max(res.pile_loads_ult) if res.pile_loads_ult else 0.0
        phi_Vc_pil = norma.resistencia_punzonado(fck, b0_pil, d, D, D)

        res.b0_pil       = b0_pil
        res.Vu_punch_pil = Vu_pil
        res.phi_Vc_pil   = phi_Vc_pil
        res.ok_punch_pil = Vu_pil <= phi_Vc_pil

        if res.ok_punch_pil:
            ratio = Vu_pil / phi_Vc_pil * 100 if phi_Vc_pil > 0 else 0
            res.msg(
                f"✔ Punzonado pilote: Vu={Vu_pil:.1f} kN ≤ φVc={phi_Vc_pil:.1f} kN "
                f"(b0={b0_pil:.2f} m, ratio={ratio:.0f}%)", "ok"
            )
        else:
            res.msg(
                f"✘ Punzonado pilote: Vu={Vu_pil:.1f} kN > φVc={phi_Vc_pil:.1f} kN "
                f"— aumentar h", "error"
            )
