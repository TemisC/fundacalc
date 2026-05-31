"""
Motor de cálculo para Zapata Corrida (Strip Footing).

Modelo: voladizo simple a cada lado del muro.
  - Cargas por metro lineal de muro [kN/m]
  - Presión uniforme de suelo
  - Diseño de armadura transversal (principal) y longitudinal (mínima)
"""

from dataclasses import dataclass, field
import math
import numpy as np
from core.normas.base import NormaBase
from core.zapata_aislada import MaterialHormigon, MaterialAcero


# ─── Estructuras de entrada ──────────────────────────────────────────────────

@dataclass
class CargaMuro:
    """Carga por metro lineal de muro."""
    Pd: float = 100.0   # Carga muerta [kN/m]
    Pl: float = 60.0    # Carga viva  [kN/m]

    @property
    def Pser(self) -> float:
        return self.Pd + self.Pl

    @property
    def Pu(self) -> float:
        return 1.2 * self.Pd + 1.6 * self.Pl


@dataclass
class MuroCorrida:
    """Geometría del muro portante."""
    espesor: float = 0.20   # Espesor del muro [m]


@dataclass
class SueloCorrida:
    """Parámetros del suelo de fundación."""
    qa: float = 100.0           # Presión admisible [kN/m²]
    Df: float = 0.80            # Profundidad de empotramiento [m]
    gamma_suelo: float = 18.0   # Peso específico [kN/m³]


@dataclass
class GeometriaCorrida:
    """Dimensiones de la zapata corrida."""
    B_fijo: float = 0.0         # Ancho fijo (0 = calcular automáticamente) [m]
    h: float = 0.40             # Peralte total [m]
    recubrimiento: float = 0.075

    @property
    def d(self) -> float:
        return self.h - self.recubrimiento - 0.008   # ~ ø16 mm / 2


# ─── Resultado ───────────────────────────────────────────────────────────────

@dataclass
class ResultadosZapataCorrida:
    B: float = 0.0
    h: float = 0.0
    d: float = 0.0
    a: float = 0.0              # Voladizo = (B - t_muro) / 2 [m]

    q_neto: float = 0.0         # Presión neta admisible [kN/m²]
    q_max: float = 0.0          # Presión máxima de servicio [kN/m²]
    q_ultima: float = 0.0       # Presión última factorizada [kN/m²]
    ok_presion: bool = False

    Mu: float = 0.0             # Momento último de diseño [kN·m/m]
    Vu: float = 0.0             # Cortante último a distancia d [kN/m]
    phi_Vn: float = 0.0         # Capacidad de corte [kN/m]
    ok_cortante: bool = False
    rel_cortante: float = 0.0

    As_req: float = 0.0         # Acero requerido por flexión [cm²/m]
    As_min: float = 0.0         # Acero mínimo [cm²/m]
    As_diseno: float = 0.0      # Acero de diseño (máx de los anteriores) [cm²/m]
    varilla: str = ""           # Ej: "Ø16mm"
    separacion: float = 0.0     # Separación transversal [m]
    n_barras_por_metro: int = 0

    As_long: float = 0.0        # Acero longitudinal mínimo [cm²/m] (por h)
    varilla_long: str = ""
    sep_long: float = 0.0

    mensajes: list = field(default_factory=list)

    def agregar_mensaje(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"tipo": tipo, "texto": texto})


# ─── Motor principal ──────────────────────────────────────────────────────────

class ZapataCorridaRectangular:
    """
    Diseña una zapata corrida (strip footing) bajo muro portante.

    Uso:
        motor = ZapataCorridaRectangular(carga, muro, suelo, hormigon, acero, norma, geo)
        motor.calcular()
    """

    def __init__(
        self,
        carga: CargaMuro,
        muro: MuroCorrida,
        suelo: SueloCorrida,
        hormigon: MaterialHormigon,
        acero: MaterialAcero,
        norma: NormaBase,
        geo: GeometriaCorrida,
        varilla_pref: str = "",
    ):
        self.carga = carga
        self.muro = muro
        self.suelo = suelo
        self.hormigon = hormigon
        self.acero = acero
        self.norma = norma
        self.geo = geo
        self.res = ResultadosZapataCorrida()
        self.varilla_pref = varilla_pref

    # ── Método principal ────────────────────────────────────────────────────

    def calcular(self) -> ResultadosZapataCorrida:
        self._dimensionar()
        if self.res.B == 0:
            return self.res

        for i in range(8):
            self._presiones()
            self._verificar_cortante()
            if self.res.ok_cortante:
                break
            self.geo.h += 0.05
            self.res.agregar_mensaje(
                f"↑ Iteración {i+1}: aumentando h a {self.geo.h:.2f} m", "info")

        self.geo.h = math.ceil(self.geo.h / 0.05) * 0.05
        self._presiones()
        self._verificar_cortante()
        self._armadura()
        return self.res

    # ── 1. Dimensionamiento en planta ───────────────────────────────────────

    def _dimensionar(self):
        res = self.res
        carga = self.carga
        suelo = self.suelo
        geo = self.geo

        q_neto = suelo.qa - suelo.Df * suelo.gamma_suelo
        res.q_neto = q_neto

        if q_neto <= 0:
            res.agregar_mensaje(
                "ERROR: presión neta ≤ 0. Revisar Df y γ del suelo.", "error")
            return

        if geo.B_fijo > 0:
            B = geo.B_fijo
        else:
            Pp_est = 0.10 * carga.Pser
            B_req = (carga.Pser + Pp_est) / q_neto
            B_min = self.muro.espesor + 2 * 0.15   # mínimo 15 cm de vuelo a cada lado
            B = max(B_req, B_min)
            B = math.ceil(B / 0.05) * 0.05

        res.B = B
        res.h = geo.h
        res.d = geo.d
        res.agregar_mensaje(
            f"ℹ Ancho calculado: B = {B:.2f} m  "
            f"(q_neto = {q_neto:.1f} kN/m²)", "info")

    # ── 2. Presiones ────────────────────────────────────────────────────────

    def _presiones(self):
        res = self.res
        B = res.B
        carga = self.carga
        suelo = self.suelo
        geo = self.geo

        Pp = B * geo.h * 24.0        # peso propio del hormigón [kN/m]
        Ps = B * (suelo.Df - geo.h) * suelo.gamma_suelo if suelo.Df > geo.h else 0.0
        q_max = (carga.Pser + Pp + Ps) / B
        res.q_max = q_max
        res.ok_presion = q_max <= suelo.qa

        if res.ok_presion:
            res.agregar_mensaje(
                f"✔ Presión máx {q_max:.1f} kN/m² ≤ qa={suelo.qa:.1f} kN/m² "
                f"(ratio={q_max/suelo.qa*100:.0f}%)", "ok")
        else:
            res.agregar_mensaje(
                f"✘ Presión {q_max:.1f} kN/m² > qa={suelo.qa:.1f} kN/m² — ampliar zapata", "error")

        res.q_ultima = carga.Pu / B
        res.h = geo.h
        res.d = geo.d
        res.a = (B - self.muro.espesor) / 2

        # Momento y cortante en voladizo
        qu = res.q_ultima
        a  = res.a
        d  = geo.d
        res.Mu = qu * a ** 2 / 2
        res.Vu = qu * max(a - d, 0.0)

    # ── 3. Verificación de cortante ─────────────────────────────────────────

    def _verificar_cortante(self):
        res = self.res
        d = self.geo.d
        phi_Vn = self.norma.resistencia_cortante_unidireccional(
            fck=self.hormigon.fck, bw=1.0, d=d)
        res.phi_Vn = phi_Vn
        res.ok_cortante = res.Vu <= phi_Vn
        res.rel_cortante = res.Vu / phi_Vn if phi_Vn > 0 else 0.0

        if res.ok_cortante:
            res.agregar_mensaje(
                f"✔ Cortante: Vu={res.Vu:.1f} kN/m ≤ φVn={phi_Vn:.1f} kN/m "
                f"(ratio={res.rel_cortante*100:.0f}%)", "ok")
        else:
            res.agregar_mensaje(
                f"✘ Cortante: Vu={res.Vu:.1f} kN/m > φVn={phi_Vn:.1f} kN/m — aumentar h", "error")

    # ── 4. Diseño de armadura ────────────────────────────────────────────────

    def _armadura(self):
        res = self.res
        fck = self.hormigon.fck
        fy = self.acero.fy
        d = self.geo.d

        # Armadura transversal (principal, perpendicular al muro)
        As_req = self.norma.area_acero_flexion(Mu=res.Mu, d=d, fck=fck, fy=fy)
        As_min = self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d)
        As_dis = max(As_req, As_min)
        res.As_req = As_req
        res.As_min = As_min
        res.As_diseno = As_dis

        varilla, sep = _seleccionar_varilla(As_dis, self.varilla_pref)
        res.varilla = varilla
        res.separacion = sep
        res.n_barras_por_metro = round(1.0 / sep) if sep > 0 else 0

        # Warn if forced bar gives unusual spacing
        if self.varilla_pref and (sep < 0.10 or sep > 0.35):
            res.agregar_mensaje(
                f"⚠ Varilla forzada {varilla}: separación {sep*100:.0f} cm "
                f"{'(muy estrecha)' if sep < 0.10 else '(muy amplia)'}", "info")

        res.agregar_mensaje(
            f"✔ Armadura trans.: {varilla} @ {sep*100:.0f} cm  "
            f"(As={As_dis:.2f} cm²/m)", "ok")

        # Armadura longitudinal mínima (paralela al muro)
        As_long = self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d)
        res.As_long = As_long
        varilla_l, sep_l = _seleccionar_varilla(As_long, self.varilla_pref)
        res.varilla_long = varilla_l
        res.sep_long = sep_l

        res.agregar_mensaje(
            f"✔ Armadura long.:  {varilla_l} @ {sep_l*100:.0f} cm  "
            f"(As_min={As_long:.2f} cm²/m)", "ok")


# ─── Helper ───────────────────────────────────────────────────────────────────

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
