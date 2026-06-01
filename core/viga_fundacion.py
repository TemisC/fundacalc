"""
Motor de cálculo para Viga de Fundación sobre suelo elástico (Winkler).

Método: MEF con elementos viga Euler-Bernoulli + resortes Winkler distribuidos.
  - N_elem = 100 elementos de igual longitud
  - Sistema lineal 2·(N_elem+1) DOFs: desplazamiento vertical + rotación por nodo
  - Convención: desplazamiento positivo = hacia abajo; momento positivo = cara inferior tensa
"""

import math
import numpy as np
from dataclasses import dataclass, field
from core.normas.base import NormaBase
from core.zapata_aislada import MaterialHormigon, MaterialAcero


# ─── Tabla de varillas ────────────────────────────────────────────────────────

_VARILLAS = [
    ("Ø8mm",  0.503), ("Ø10mm", 0.785), ("Ø12mm", 1.131),
    ("Ø16mm", 2.011), ("Ø20mm", 3.142), ("Ø25mm", 4.909), ("Ø32mm", 8.042),
]


def _varilla(As_cm2: float, pref: str = "") -> tuple:
    """
    Selecciona diámetro de varilla y separación para un As dado (cm²/m).

    Returns:
        (nombre, separacion_m)
    """
    if pref:
        for n, a in _VARILLAS:
            if pref in n:
                s = a / As_cm2 if As_cm2 > 0 else 0.20
                return n, max(0.07, min(0.50, math.floor(s * 100) / 100))
    for n, a in _VARILLAS:
        s = a / As_cm2 if As_cm2 > 0 else 0.25
        if 0.10 <= s <= 0.35:
            return n, math.floor(s * 100) / 100
    # Fuera de rango → Ø25mm con separación forzada
    a = 4.909
    s = min(max(a / As_cm2, 0.10), 0.35) if As_cm2 > 0 else 0.25
    return "Ø25mm", math.floor(s * 100) / 100


def _dis_As(var: str, sep: float) -> float:
    """Área de acero dispuesta [cm²/m] dada varilla y separación [m]."""
    for n, a in _VARILLAS:
        if n == var:
            return round(a / sep, 4) if sep > 0 else 0.0
    return 0.0


def _varilla_total(As_cm2_total: float, pref: str = "") -> tuple:
    """
    Selecciona varilla y número de barras para un As TOTAL (no por metro).
    Usado para armadura longitudinal de la viga (ancho fijo B).

    Returns:
        (nombre, n_barras, As_dispuesto_cm2, separacion_entre_barras_m)
    """
    candidatos = _VARILLAS if not pref else (
        [(n, a) for n, a in _VARILLAS if pref in n] or _VARILLAS
    )
    mejor = None
    for nombre, area in candidatos:
        n = max(2, math.ceil(As_cm2_total / area))
        As_disp = n * area
        if As_disp >= As_cm2_total:
            mejor = (nombre, n, As_disp)
            break
    if mejor is None:
        nombre, area = "Ø32mm", 8.042
        n = max(2, math.ceil(As_cm2_total / area))
        mejor = (nombre, n, n * area)
    return mejor


# ─── Estructuras de entrada ───────────────────────────────────────────────────

@dataclass
class CargaColumna:
    """Carga puntual de una columna sobre la viga de fundación."""
    x: float          # Posición a lo largo de la viga [m]
    Pd: float         # Carga muerta [kN]
    Pl: float         # Carga viva  [kN]
    etiqueta: str = ""  # ej. "C1", "C2"

    @property
    def Pser(self) -> float:
        return self.Pd + self.Pl

    @property
    def Pu(self) -> float:
        return 1.2 * self.Pd + 1.6 * self.Pl


@dataclass
class SueloViga:
    """Parámetros geotécnicos para la viga de fundación."""
    ks: float = 20000.0   # Coeficiente de balasto (subgrado) [kN/m³]
    qa: float = 150.0     # Presión admisible del suelo [kN/m²]


@dataclass
class GeometriaViga:
    """Dimensiones de la sección transversal y longitud de la viga."""
    L: float = 10.0            # Longitud total de la viga [m]
    B: float = 0.60            # Ancho de la viga [m]
    h: float = 0.80            # Altura total de la sección [m]
    recubrimiento: float = 0.075  # Recubrimiento libre [m]
    vuelo_izq: float = 0.50    # Vuelo más allá de la columna extrema izquierda [m]
    vuelo_der: float = 0.50    # Vuelo más allá de la columna extrema derecha [m]

    @property
    def d(self) -> float:
        """Peralte efectivo [m] (estribos Ø8mm, barra long. ~ Ø16mm)."""
        return max(self.h - self.recubrimiento - 0.016, 0.05)


# ─── Estructura de resultados ─────────────────────────────────────────────────

@dataclass
class ResultadosViga:
    """Resultados completos del análisis y diseño de la viga de fundación."""

    # Geometría procesada
    L: float = 0.0
    B: float = 0.0
    h: float = 0.0
    d: float = 0.0

    # Clasificación flexible / rígida
    lambda_char: float = 0.0   # λ = (ks·B / 4EI)^0.25  [1/m]
    L_char: float = 0.0        # λ·L (adimensional)
    flexible: bool = True      # True si λ·L > π (viga flexible)

    # Resultados FEM — arrays como listas Python
    x_grid: list = field(default_factory=list)   # Posiciones [m]
    y_grid: list = field(default_factory=list)   # Deflexión [m] (+ = bajada)
    q_grid: list = field(default_factory=list)   # Presión de contacto [kN/m²]
    M_grid: list = field(default_factory=list)   # Momento flector [kN·m]
    V_grid: list = field(default_factory=list)   # Cortante [kN]

    # Envolventes de diseño
    M_max_pos: float = 0.0    # Momento positivo máximo (cara inferior tensa) [kN·m]
    M_max_neg: float = 0.0    # Momento negativo máximo (cara superior tensa) |valor| [kN·m]
    V_max: float = 0.0        # Cortante máximo absoluto [kN]
    q_max: float = 0.0        # Presión de contacto máxima [kN/m²]
    ok_presion: bool = True

    # Armadura longitudinal
    As_min: float = 0.0
    As_req_inf: float = 0.0
    As_dis_inf: float = 0.0
    var_inf: str = ""
    n_inf: int = 0
    sep_inf: float = 0.0      # Separación entre barras inferiores [m]

    As_req_sup: float = 0.0
    As_dis_sup: float = 0.0
    var_sup: str = ""
    n_sup: int = 0
    sep_sup: float = 0.0      # Separación entre barras superiores [m]

    # Armadura transversal (estribos)
    Vu_max: float = 0.0       # Cortante de diseño a distancia d de columna [kN]
    phi_Vc: float = 0.0       # Resistencia del hormigón a cortante [kN]
    ok_cortante: bool = True
    Av_s: float = 0.0         # Av/s requerido [cm²/m]
    var_estribo: str = ""     # ej. "Ø8mm"
    s_estribo: float = 0.0    # Separación de estribos [m]

    mensajes: list = field(default_factory=list)

    def msg(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"texto": texto, "tipo": tipo})


# ─── Motor principal ──────────────────────────────────────────────────────────

class VigaFundacion:
    """
    Motor de cálculo MEF para viga de fundación sobre suelo elástico (Winkler).

    Parámetros
    ----------
    columnas   : lista de CargaColumna — mínimo 1, posiciones dentro de [0, L]
    suelo      : SueloViga
    geo        : GeometriaViga — L debe incluir los vuelos
    hormigon   : MaterialHormigon
    acero      : MaterialAcero
    norma      : NormaBase
    varilla_pref : diámetro preferido (ej. "Ø16mm") o "" para automático
    """

    N_ELEM = 100  # Número de elementos finitos (fijo)

    def __init__(
        self,
        columnas: list,
        suelo: SueloViga,
        geo: GeometriaViga,
        hormigon: MaterialHormigon,
        acero: MaterialAcero,
        norma: NormaBase,
        varilla_pref: str = "",
    ):
        self.columnas = columnas
        self.suelo = suelo
        self.geo = geo
        self.hormigon = hormigon
        self.acero = acero
        self.norma = norma
        self.varilla_pref = varilla_pref
        self.res = ResultadosViga()

        # Validar y ajustar posiciones de columnas al rango [0, L]
        for col in self.columnas:
            if col.x < 0:
                col.x = 0.0
            elif col.x > geo.L:
                col.x = geo.L

    # ── Métodos internos ──────────────────────────────────────────────────────

    def _setup_fem(self):
        """Calcula parámetros geométricos y materiales para el MEF."""
        geo = self.geo
        n = self.N_ELEM
        self._n_nodes = n + 1
        self._Le = geo.L / n  # Longitud de elemento [m]

        # Módulo de elasticidad del hormigón: E = 4700√fck [MPa] → [kN/m²]
        fck_MPa = self.hormigon.fck
        E_MPa = 4700.0 * math.sqrt(fck_MPa)
        self._E = E_MPa * 1000.0  # kN/m²

        # Inercia de la sección rectangular
        self._I = geo.B * geo.h ** 3 / 12.0  # m⁴
        self._EI = self._E * self._I           # kN·m²

    def _resolver_fem(self):
        """
        Ensambla y resuelve el sistema global K·u = F.

        DOFs por nodo: [v_i, θ_i]  →  DOF global nodo i: [2i, 2i+1]
        Convención de signo: v positivo = hacia abajo (dirección de carga).
        """
        n = self.N_ELEM
        nn = self._n_nodes
        Le = self._Le
        EI = self._EI
        ks = self.suelo.ks
        B = self.geo.B
        ndof = 2 * nn

        K = np.zeros((ndof, ndof))

        # ── 1. Rigidez de viga Euler-Bernoulli ───────────────────────────────
        c = EI / Le ** 3
        ke_local = c * np.array([
            [ 12.0,  6.0*Le, -12.0,  6.0*Le],
            [  6.0*Le,  4.0*Le**2,  -6.0*Le,  2.0*Le**2],
            [-12.0, -6.0*Le,  12.0, -6.0*Le],
            [  6.0*Le,  2.0*Le**2,  -6.0*Le,  4.0*Le**2],
        ])

        for e in range(n):
            i, j = e, e + 1
            dofs = [2*i, 2*i+1, 2*j, 2*j+1]
            for r, gr in enumerate(dofs):
                for s, gs in enumerate(dofs):
                    K[gr, gs] += ke_local[r, s]

        # ── 2. Resortes de Winkler ────────────────────────────────────────────
        # Rigidez de resorte en nodo extremo: ks·B·Le/2
        # Rigidez de resorte en nodo interior: ks·B·Le
        k_ext = ks * B * Le / 2.0
        k_int = ks * B * Le

        for i in range(nn):
            dof_v = 2 * i  # DOF de desplazamiento vertical
            if i == 0 or i == nn - 1:
                K[dof_v, dof_v] += k_ext
            else:
                K[dof_v, dof_v] += k_int

        # ── 3. Vector de cargas ───────────────────────────────────────────────
        F = np.zeros(ndof)
        Le_loc = self._Le

        for col in self.columnas:
            idx = int(round(col.x / Le_loc))
            idx = max(0, min(nn - 1, idx))
            # Positivo = hacia abajo (mismo sentido que deflexión positiva)
            F[2 * idx] += col.Pu

        # ── 4. Resolver ───────────────────────────────────────────────────────
        try:
            u = np.linalg.solve(K, F)
        except np.linalg.LinAlgError:
            u = np.linalg.lstsq(K, F, rcond=None)[0]

        self._u = u

    def _post_process(self):
        """
        Extrae deflexiones, presiones de contacto, momentos y cortantes
        del vector de desplazamientos nodales.
        """
        nn = self._n_nodes
        n = self.N_ELEM
        Le = self._Le
        EI = self._EI
        ks = self.suelo.ks
        B = self.geo.B
        u = self._u
        res = self.res

        # ── Deflexiones y presión de contacto ────────────────────────────────
        x_grid = [i * Le for i in range(nn)]

        # No tracción en suelo: limitar deflexión a >= 0
        y_grid = [max(float(u[2 * i]), 0.0) for i in range(nn)]
        q_grid = [ks * y for y in y_grid]   # kN/m² (presión por unidad de área)

        # ── Momentos y cortantes por elemento ────────────────────────────────
        # Para cada elemento se calculan momentos/cortantes en los extremos
        # mediante las fuerzas nodales: f_elem = ke · d_elem
        # Convención estándar Euler-Bernoulli:
        #   M_izq = -f_local[1]  (momento en nodo izquierdo del elemento)
        #   M_der =  f_local[3]  (momento en nodo derecho del elemento)
        #   V_izq = -f_local[0]  (cortante en nodo izquierdo)
        #   V_der =  f_local[2]  (cortante en nodo derecho)

        c = EI / Le ** 3
        ke_local = c * np.array([
            [ 12.0,  6.0*Le, -12.0,  6.0*Le],
            [  6.0*Le,  4.0*Le**2,  -6.0*Le,  2.0*Le**2],
            [-12.0, -6.0*Le,  12.0, -6.0*Le],
            [  6.0*Le,  2.0*Le**2,  -6.0*Le,  4.0*Le**2],
        ])

        # Acumular momentos y cortantes en nodos (promedio de elementos adyacentes)
        M_sum = np.zeros(nn)
        V_sum = np.zeros(nn)
        count = np.zeros(nn, dtype=int)

        for e in range(n):
            i, j = e, e + 1
            d_elem = np.array([u[2*i], u[2*i+1], u[2*j], u[2*j+1]])
            f_elem = ke_local @ d_elem

            # Momentos (signo: positivo = cara inferior tensa)
            M_i = -f_elem[1]
            M_j =  f_elem[3]

            # Cortantes
            V_i = -f_elem[0]
            V_j =  f_elem[2]

            M_sum[i] += M_i
            M_sum[j] += M_j
            V_sum[i] += V_i
            V_sum[j] += V_j
            count[i] += 1
            count[j] += 1

        M_grid = [float(M_sum[i] / count[i]) if count[i] > 0 else 0.0 for i in range(nn)]
        V_grid = [float(V_sum[i] / count[i]) if count[i] > 0 else 0.0 for i in range(nn)]

        # ── Guardar en resultado ──────────────────────────────────────────────
        res.x_grid = x_grid
        res.y_grid = y_grid
        res.q_grid = q_grid
        res.M_grid = M_grid
        res.V_grid = V_grid

        res.q_max = max(q_grid) if q_grid else 0.0
        res.ok_presion = res.q_max <= self.suelo.qa

        res.M_max_pos = max((m for m in M_grid if m > 0), default=0.0)
        res.M_max_neg = abs(min((m for m in M_grid if m < 0), default=0.0))
        res.V_max = max((abs(v) for v in V_grid), default=0.0)

        # Mensajes de verificación de presión
        if res.ok_presion:
            res.msg(
                f"Presion maxima: {res.q_max:.1f} kN/m2 <= qa={self.suelo.qa:.1f} kN/m2 — OK",
                "ok"
            )
        else:
            res.msg(
                f"ADVERTENCIA: Presion maxima {res.q_max:.1f} kN/m2 > qa={self.suelo.qa:.1f} kN/m2"
                f" - Aumentar B o h de la viga",
                "advertencia"
            )

        # Clasificación flexible / rígida (Hetenyi)
        EI_v = self._EI
        lam = (ks * B / (4.0 * EI_v)) ** 0.25 if EI_v > 0 else 0.0
        res.lambda_char = lam
        res.L_char = lam * self.geo.L
        res.flexible = res.L_char > math.pi
        clasificacion = "flexible" if res.flexible else "rigida"
        res.msg(
            f"Clasificacion: lambda={lam:.4f} 1/m, lambda*L={res.L_char:.3f}"
            f" ({'> pi (' + clasificacion + ')' if res.flexible else '<= pi (' + clasificacion + ')'})",
            "info"
        )

    def _armadura(self):
        """Diseña la armadura longitudinal inferior y superior."""
        res = self.res
        geo = self.geo
        fck = self.hormigon.fck
        fy = self.acero.fy
        B = geo.B
        d = geo.d
        phi = 0.90  # Factor de reducción flexión ACI

        # ── Acero mínimo ──────────────────────────────────────────────────────
        # ACI 318-19 §9.6.1.2: As_min = max(0.25√fck/fy, 1.4/fy) · bw · d
        rho_min = max(0.25 * math.sqrt(fck) / fy, 1.4 / fy)
        As_min_cm2 = rho_min * B * d * 10000.0  # cm²
        res.As_min = As_min_cm2

        def _rige(As_flex, As_min, ref="ACI 318-19 §9.6.1.2"):
            return "rige flexión" if As_flex >= As_min - 1e-9 else f"rige As_mín ({ref})"

        # ── Armadura inferior (M_max_pos) ────────────────────────────────────
        As_flex_inf = _As_flexion(res.M_max_pos, d, B, fck, fy, phi)
        As_req_inf  = max(As_flex_inf, As_min_cm2)
        res.As_req_inf = As_req_inf

        nombre_inf, n_inf, As_dis_inf = _varilla_total(As_req_inf, self.varilla_pref)
        # Separación entre barras
        db_inf_m = _db_m(nombre_inf)
        recub = geo.recubrimiento
        sep_inf = _separacion_barras(B, n_inf, db_inf_m, recub)

        res.var_inf = nombre_inf
        res.n_inf = n_inf
        res.As_dis_inf = As_dis_inf
        res.sep_inf = sep_inf

        res.msg(
            f"Armadura inferior: {n_inf}{nombre_inf} "
            f"(As={As_dis_inf:.2f} cm2, sep={sep_inf*100:.1f} cm) — {_rige(As_flex_inf, As_min_cm2)}",
            "ok"
        )

        # ── Armadura superior (M_max_neg) ────────────────────────────────────
        As_flex_sup = _As_flexion(res.M_max_neg, d, B, fck, fy, phi)
        As_req_sup  = max(As_flex_sup, As_min_cm2)
        res.As_req_sup = As_req_sup

        nombre_sup, n_sup, As_dis_sup = _varilla_total(As_req_sup, self.varilla_pref)
        db_sup_m = _db_m(nombre_sup)
        sep_sup = _separacion_barras(B, n_sup, db_sup_m, recub)

        res.var_sup = nombre_sup
        res.n_sup = n_sup
        res.As_dis_sup = As_dis_sup
        res.sep_sup = sep_sup

        res.msg(
            f"Armadura superior: {n_sup}{nombre_sup} "
            f"(As={As_dis_sup:.2f} cm2, sep={sep_sup*100:.1f} cm) — {_rige(As_flex_sup, As_min_cm2)}",
            "ok"
        )

    def _cortante(self):
        """Verifica cortante y diseña estribos si es necesario."""
        res = self.res
        geo = self.geo
        fck = self.hormigon.fck
        fy = self.acero.fy
        B = geo.B
        d = geo.d
        Le = self._Le
        phi_c = 0.75  # Factor de reducción cortante ACI

        # ── Cortante de diseño Vu a distancia d de la cara de columna ────────
        # Se toma el máximo cortante absoluto en el grid entre nodos a distancia
        # d de cualquier columna.
        V_grid = res.V_grid
        x_grid = res.x_grid

        Vu_critico = 0.0
        for col in self.columnas:
            x_col = col.x
            # Examinar puntos a distancia d del eje de columna
            for xi, vi in zip(x_grid, V_grid):
                if abs(xi - x_col) >= d:
                    Vu_critico = max(Vu_critico, abs(vi))
                    break  # Tomar el más cercano que cumpla la condición

        # Si no se encontró ninguno válido, usar V_max global
        if Vu_critico == 0.0:
            Vu_critico = res.V_max

        res.Vu_max = Vu_critico

        # ── Resistencia del hormigón a cortante (ACI 318 §22.5.5) ────────────
        # φVc = φ · 0.17 · √fck[MPa] · bw[m] · d[m] · 1000  → kN
        phi_Vc = phi_c * 0.17 * math.sqrt(fck) * B * d * 1000.0
        res.phi_Vc = phi_Vc

        if Vu_critico <= phi_Vc:
            res.ok_cortante = True
            res.Av_s = 0.0
            # Estribos mínimos ACI 318 §9.6.3: Av/s = 0.062√fck/fy · bw
            Av_s_min = 0.062 * math.sqrt(fck) / fy * B * 100.0  # cm²/m
            Av_s_min = max(Av_s_min, 0.35 * B * 100.0 / fy)
            res.Av_s = Av_s_min
            res.msg(
                f"Cortante OK: Vu={Vu_critico:.1f} kN <= phiVc={phi_Vc:.1f} kN "
                f"(estribos minimos Av/s={Av_s_min:.3f} cm2/m)",
                "ok"
            )
        else:
            res.ok_cortante = False
            # Av/s = (Vu - φVc) / (φ · fy · d)  en cm²/m
            Av_s = (Vu_critico - phi_Vc) / (phi_c * fy * d) * 100.0  # cm²/m
            res.Av_s = Av_s
            res.msg(
                f"Cortante FALLA: Vu={Vu_critico:.1f} kN > phiVc={phi_Vc:.1f} kN "
                f"- Se requiere Av/s={Av_s:.3f} cm2/m",
                "error"
            )

        # ── Selección de estribo ──────────────────────────────────────────────
        Av_s_req = res.Av_s
        estribo, s_est = _seleccionar_estribo(Av_s_req, B, d)
        res.var_estribo = estribo
        res.s_estribo = s_est
        res.msg(
            f"Estribos: {estribo} @ {s_est*100:.0f} cm "
            f"(Av/s req={Av_s_req:.3f} cm2/m)",
            "info"
        )

    # ── Método público principal ───────────────────────────────────────────────

    def calcular(self) -> ResultadosViga:
        """Ejecuta el análisis completo y devuelve ResultadosViga."""
        res = self.res
        geo = self.geo

        # Guardar geometría en resultado
        res.L = geo.L
        res.B = geo.B
        res.h = geo.h
        res.d = geo.d

        if not self.columnas:
            res.msg("ERROR: No hay columnas definidas.", "error")
            return res

        self._setup_fem()
        self._resolver_fem()
        self._post_process()
        self._armadura()
        self._cortante()

        return res


# ─── Funciones auxiliares ─────────────────────────────────────────────────────

def _As_flexion(Mu: float, d: float, B: float, fck: float, fy: float,
                phi: float = 0.90) -> float:
    """
    Área de acero por flexión (fórmula rectangular ACI, iteracion directa).

    Mu  : Momento ultimo [kN·m]  (total en la seccion de ancho B)
    d   : Peralte efectivo [m]
    B   : Ancho de la seccion [m]
    fck : Resistencia hormigon [MPa]
    fy  : Fluencia acero [MPa]
    phi : Factor de reduccion

    Returns:
        As [cm²]  (total en el ancho B)
    """
    if Mu <= 0.0 or d <= 0.0 or B <= 0.0:
        return 0.0

    # Mn requerido
    Mn = Mu / phi  # kN·m

    # Resolver: Mn = As·fy·(d - As·fy/(1.7·fck·B))  con fy[MPa], fck[MPa], B[m], d[m]
    # Convertir a unidades consistentes: fy → kN/m², fck → kN/m²
    fy_kPa = fy * 1000.0     # kN/m²
    fck_kPa = fck * 1000.0   # kN/m²

    # Cuadrática: a·As² + b·As + c = 0
    # a = fy²/(1.7·fck·B·10000)  [si As en cm²]  → operar en m²
    # As en m²: cuadrática
    a_coef = fy_kPa / (1.7 * fck_kPa * B)
    b_coef = -fy_kPa * d
    c_coef = Mn  # kN·m

    discriminante = b_coef ** 2 - 4.0 * a_coef * c_coef
    if discriminante < 0:
        discriminante = 0.0

    As_m2 = (-b_coef - math.sqrt(discriminante)) / (2.0 * a_coef)
    As_cm2 = As_m2 * 10000.0

    return max(As_cm2, 0.0)


def _db_m(nombre_varilla: str) -> float:
    """Diámetro nominal en metros a partir del nombre (ej. 'Ø16mm' → 0.016)."""
    try:
        mm = float(nombre_varilla.replace("Ø", "").replace("mm", ""))
        return mm / 1000.0
    except ValueError:
        return 0.016


def _separacion_barras(B: float, n: int, db: float, recub: float) -> float:
    """
    Separación libre entre barras distribuidas en el ancho B [m].

    s = (B - 2·recub - n·db) / (n - 1)  si n > 1
    """
    if n <= 1:
        return B - 2.0 * recub - db
    s = (B - 2.0 * recub - n * db) / (n - 1)
    return max(s, 0.025)  # mínimo 2.5 cm entre barras


def _seleccionar_estribo(Av_s_cm2_m: float, B: float, d: float) -> tuple:
    """
    Selecciona diámetro y separación de estribos de dos ramas.

    Av_s_cm2_m : Av/s requerido [cm²/m]
    B          : Ancho de la viga [m]
    d          : Peralte efectivo [m]

    Returns:
        (nombre_estribo, separacion_m)
    """
    # Estribos de 2 ramas
    opciones = [
        ("Ø8mm",  2 * 0.503),   # 2 ramas Ø8 → 1.006 cm²
        ("Ø10mm", 2 * 0.785),   # 2 ramas Ø10 → 1.571 cm²
        ("Ø12mm", 2 * 1.131),   # 2 ramas Ø12 → 2.262 cm²
    ]

    # Separación máxima ACI 318 §9.7.6.2: s_max = min(d/2, 600 mm)
    s_max = min(d / 2.0, 0.60)

    for nombre, Av2 in opciones:
        if Av_s_cm2_m <= 0.0:
            s = s_max
        else:
            s = Av2 / Av_s_cm2_m  # m
        s = min(s, s_max)
        s = max(s, 0.05)  # mínimo 5 cm
        s = math.floor(s * 20) / 20  # redondear a múltiplo de 5 cm
        if s >= 0.05:
            return nombre, s

    # Fallback
    return "Ø10mm", 0.10
