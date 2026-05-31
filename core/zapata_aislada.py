"""
Motor de cálculo para Zapata Aislada.
Compatible con cualquier norma que implemente NormaBase.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from core.normas.base import NormaBase


@dataclass
class CargasColumna:
    """Cargas aplicadas en la base de la columna (nivel de terreno)."""
    Pd: float = 0.0
    Pl: float = 0.0
    Mxd: float = 0.0
    Mxl: float = 0.0
    Myd: float = 0.0
    Myl: float = 0.0
    Vxd: float = 0.0
    Vxl: float = 0.0

    @property
    def Pu(self) -> float:
        return 1.2 * self.Pd + 1.6 * self.Pl

    @property
    def Pser(self) -> float:
        return self.Pd + self.Pl

    @property
    def Mxu(self) -> float:
        return 1.2 * self.Mxd + 1.6 * self.Mxl

    @property
    def Myu(self) -> float:
        return 1.2 * self.Myd + 1.6 * self.Myl


@dataclass
class Columna:
    """Geometría de la columna."""
    ancho: float = 0.30
    largo: float = 0.30
    Es_circular: bool = False
    diametro: float = 0.30


@dataclass
class Suelo:
    """Parámetros geotécnicos del suelo de fundación."""
    qa: float = 150.0
    Df: float = 1.20
    gamma_suelo: float = 18.0
    gamma_relleno: float = 18.0


@dataclass
class MaterialHormigon:
    """Propiedades del hormigón."""
    fck: float = 25.0
    nombre: str = "H-25"

    @property
    def fcd(self) -> float:
        return 0.85 * self.fck


@dataclass
class MaterialAcero:
    """Propiedades del acero de refuerzo."""
    fy: float = 420.0
    nombre: str = "ADN420"


@dataclass
class GeometriaZapata:
    """
    Dimensiones de la zapata.
    Si se fija 'cuadrada=True' solo se usa 'B' para ambas dimensiones.
    Si 'dimensiones_fijas=True' se usan B y L tal como vienen sin redimensionar.
    """
    B: float = 0.0
    L: float = 0.0
    h: float = 0.50
    recubrimiento: float = 0.075
    cuadrada: bool = True
    dimensiones_fijas: bool = False

    @property
    def d(self) -> float:
        return self.h - self.recubrimiento - 0.008

    @property
    def Area(self) -> float:
        return self.B * self.L


@dataclass
class GeometriaPedestal:
    """Dimensiones del pedestal (plinto). Bp/Lp=0 → auto-calcular."""
    Bp: float = 0.0
    Lp: float = 0.0
    hp: float = 0.40
    recubrimiento: float = 0.040


@dataclass
class ResultadosPedestal:
    Bp: float = 0.0
    Lp: float = 0.0
    hp: float = 0.0
    Pu: float = 0.0
    ok_aplastamiento_col: bool = False
    phi_Bn_col: float = 0.0
    ok_aplastamiento_zap: bool = False
    phi_Bn_zap: float = 0.0
    Ag: float = 0.0
    As_min: float = 0.0
    As_diseno: float = 0.0
    n_barras: int = 0
    varilla_long: str = ""
    varilla_estribo: str = ""
    separacion_estribo: float = 0.0
    n_esperas: int = 0
    varilla_espera: str = ""
    As_esperas: float = 0.0
    ld_espera_comp: float = 0.0
    ok_esperas_en_zapata: bool = True
    mensajes: list = field(default_factory=list)

    def agregar_mensaje(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"tipo": tipo, "texto": texto})


@dataclass
class ResultadosZapata:
    B_requerido: float = 0.0
    L_requerido: float = 0.0
    h_requerido: float = 0.0
    area_requerida: float = 0.0
    q_neto: float = 0.0
    q_max: float = 0.0
    q_min: float = 0.0
    q_ultima: float = 0.0
    ok_presion: bool = False
    ok_punzonado: bool = False
    ok_cortante: bool = False
    Vu_punz: float = 0.0
    phi_Vn_punz: float = 0.0
    relacion_punzonado: float = 0.0
    Vu_cort: float = 0.0
    phi_Vn_cort: float = 0.0
    relacion_cortante: float = 0.0
    Mu_x: float = 0.0
    As_x_requerido: float = 0.0
    As_x_minimo: float = 0.0
    As_x_diseno: float = 0.0
    varilla_x: str = ""
    separacion_x: float = 0.0
    Mu_y: float = 0.0
    As_y_requerido: float = 0.0
    As_y_minimo: float = 0.0
    As_y_diseno: float = 0.0
    varilla_y: str = ""
    separacion_y: float = 0.0
    ld_requerido: float = 0.0
    ld_disponible: float = 0.0
    ok_desarrollo: bool = False
    mensajes: list = field(default_factory=list)

    def agregar_mensaje(self, texto: str, tipo: str = "info"):
        self.mensajes.append({"tipo": tipo, "texto": texto})


class ZapataAislada:
    """Calcula y diseña una zapata aislada cuadrada o rectangular."""

    def __init__(
        self,
        cargas: CargasColumna,
        columna: Columna,
        suelo: Suelo,
        hormigon: MaterialHormigon,
        acero: MaterialAcero,
        norma: NormaBase,
        geometria: Optional[GeometriaZapata] = None,
        geo_pedestal: Optional[GeometriaPedestal] = None,
        varilla_pref: str = "",
    ):
        self.cargas = cargas
        self.columna = columna
        self.suelo = suelo
        self.hormigon = hormigon
        self.acero = acero
        self.norma = norma
        self.geo = geometria or GeometriaZapata()
        self.geo_pedestal = geo_pedestal or GeometriaPedestal()
        self.resultados = ResultadosZapata()
        self.resultados_pedestal: Optional[ResultadosPedestal] = None
        self.varilla_pref = varilla_pref

    def dimensionar_planta(self) -> None:
        res = self.resultados
        Pp_zapata = 0.10 * self.cargas.Pser
        P_total = self.cargas.Pser + Pp_zapata
        q_neta = self.suelo.qa - (self.suelo.Df * self.suelo.gamma_suelo)
        res.q_neto = q_neta

        if q_neta <= 0:
            res.agregar_mensaje(
                "ERROR: La presión neta es ≤ 0. Revisar Df y γ del suelo.", "error"
            )
            return

        area_req = P_total / q_neta
        res.area_requerida = area_req

        if self.geo.dimensiones_fijas:
            res.B_requerido = self.geo.B
            res.L_requerido = self.geo.L
            area_fija = self.geo.B * self.geo.L
            lado_min = np.sqrt(area_req)
            if area_fija < area_req * 0.99:
                res.agregar_mensaje(
                    f"⚠ Dimensiones fijadas {self.geo.B:.2f}×{self.geo.L:.2f} m "
                    f"(área={area_fija:.2f} m²) < área mínima requerida {area_req:.2f} m² "
                    f"(lado mín. {lado_min:.2f} m). La presión puede superar qa.", "advertencia"
                )
            else:
                res.agregar_mensaje(
                    f"ℹ Dimensiones fijadas: {self.geo.B:.2f}×{self.geo.L:.2f} m "
                    f"(área mín. req. {area_req:.2f} m², lado mín. {lado_min:.2f} m)", "info"
                )
            return

        # B mínimo por longitud de desarrollo (barra Ø16 de referencia)
        db = 0.016
        ld_req_desarro = self.norma.longitud_desarrollo(db=db, fck=self.hormigon.fck, fy=self.acero.fy)
        c1_col, recub = self.columna.ancho, self.geo.recubrimiento
        B_min_desarro = np.ceil(((ld_req_desarro + c1_col / 2 + recub) * 2) / 0.05) * 0.05

        if self.geo.cuadrada:
            lado = np.sqrt(area_req)
            lado_redond = np.ceil(lado / 0.05) * 0.05
            if lado_redond < B_min_desarro:
                res.agregar_mensaje(
                    f"ℹ B aumentado de {lado_redond:.2f} m a {B_min_desarro:.2f} m "
                    f"para cumplir longitud de desarrollo (ld={ld_req_desarro*100:.0f} cm).", "info"
                )
                lado_redond = B_min_desarro
            self.geo.B = lado_redond
            self.geo.L = lado_redond
        else:
            if self.geo.B > 0 and self.geo.L > 0:
                ratio = self.geo.L / self.geo.B
                B_calc = np.ceil(np.sqrt(area_req / ratio) / 0.05) * 0.05
                B_calc = max(B_calc, B_min_desarro)
                self.geo.B = B_calc
                self.geo.L = np.ceil(self.geo.B * ratio / 0.05) * 0.05
            else:
                lado = np.ceil(np.sqrt(area_req) / 0.05) * 0.05
                lado = max(lado, B_min_desarro)
                self.geo.B = lado
                self.geo.L = lado

        res.B_requerido = self.geo.B
        res.L_requerido = self.geo.L

    def calcular_presiones(self) -> None:
        res = self.resultados
        B, L = self.geo.B, self.geo.L
        d = self.geo.d

        gamma_horm = 24.0
        Pp = B * L * self.geo.h * gamma_horm
        Ps = self.suelo.Df * self.suelo.gamma_suelo * B * L - Pp
        P_total = self.cargas.Pser + Pp + Ps
        Mx_total = self.cargas.Mxd + self.cargas.Mxl
        My_total = self.cargas.Myd + self.cargas.Myl

        q_med = P_total / (B * L)
        q_ex = abs(Mx_total) / (B * L**2 / 6)
        q_ey = abs(My_total) / (L * B**2 / 6)

        res.q_max = q_med + q_ex + q_ey
        res.q_min = q_med - q_ex - q_ey

        if res.q_max <= self.suelo.qa:
            res.ok_presion = True
            res.agregar_mensaje(
                f"✔ Presión máxima {res.q_max:.1f} kN/m² ≤ qa={self.suelo.qa:.1f} kN/m²"
                f" (ratio={res.q_max/self.suelo.qa*100:.0f}%)", "ok"
            )
        else:
            res.ok_presion = False
            res.agregar_mensaje(
                f"✘ Presión máxima {res.q_max:.1f} kN/m² > qa={self.suelo.qa:.1f} kN/m²"
                f" (ratio={res.q_max/self.suelo.qa*100:.0f}%) — Ampliar zapata", "error"
            )

        Pu = self.cargas.Pu
        res.q_ultima = Pu / (B * L)

    def verificar_punzonado(self) -> None:
        res = self.resultados
        d = self.geo.d
        c1 = self.columna.ancho
        c2 = self.columna.largo
        B, L = self.geo.B, self.geo.L

        b0 = 2 * ((c1 + d) + (c2 + d))
        A_critica = (c1 + d) * (c2 + d)
        Vu_punz = res.q_ultima * (B * L - A_critica)
        res.Vu_punz = Vu_punz

        phi_Vn = self.norma.resistencia_punzonado(
            fck=self.hormigon.fck,
            b0=b0,
            d=d,
            c1=c1,
            c2=c2,
        )
        res.phi_Vn_punz = phi_Vn
        res.relacion_punzonado = Vu_punz / phi_Vn if phi_Vn else float('inf')

        if Vu_punz <= phi_Vn:
            res.ok_punzonado = True
            res.agregar_mensaje(
                f"✔ Punzonado: Vu={Vu_punz:.1f} kN ≤ φVn={phi_Vn:.1f} kN "
                f"(ratio={res.relacion_punzonado:.2f})", "ok"
            )
        else:
            res.ok_punzonado = False
            res.agregar_mensaje(
                f"✘ Punzonado FALLA: Vu={Vu_punz:.1f} kN > φVn={phi_Vn:.1f} kN. "
                f"Aumentar h o usar hormigón de mayor resistencia.", "error"
            )

    def verificar_cortante_unidireccional(self) -> None:
        res = self.resultados
        d = self.geo.d
        B, L = self.geo.B, self.geo.L
        c1, c2 = self.columna.ancho, self.columna.largo

        av_x = (L / 2) - (c2 / 2) - d
        av_y = (B / 2) - (c1 / 2) - d

        Vu_x = res.q_ultima * B * av_x
        Vu_y = res.q_ultima * L * av_y

        Vu_crit = max(Vu_x, Vu_y)
        bw_crit = B if Vu_x >= Vu_y else L
        res.Vu_cort = Vu_crit

        phi_Vn = self.norma.resistencia_cortante_unidireccional(
            fck=self.hormigon.fck,
            bw=bw_crit,
            d=d,
        )
        res.phi_Vn_cort = phi_Vn
        res.relacion_cortante = Vu_crit / phi_Vn if phi_Vn else float('inf')

        if Vu_crit <= phi_Vn:
            res.ok_cortante = True
            res.agregar_mensaje(
                f"✔ Cortante: Vu={Vu_crit:.1f} kN ≤ φVn={phi_Vn:.1f} kN "
                f"(ratio={res.relacion_cortante:.2f})", "ok"
            )
        else:
            res.ok_cortante = False
            res.agregar_mensaje(
                f"✘ Cortante FALLA: Aumentar d (altura de la zapata).", "error"
            )

    def diseno_flexion(self) -> None:
        res = self.resultados
        d = self.geo.d
        B, L = self.geo.B, self.geo.L
        c1, c2 = self.columna.ancho, self.columna.largo
        qu = res.q_ultima
        fck = self.hormigon.fck
        fy = self.acero.fy

        vol_x = (B / 2) - (c1 / 2)
        vol_y = (L / 2) - (c2 / 2)

        Mu_x = qu * vol_x**2 / 2
        Mu_y = qu * vol_y**2 / 2

        res.Mu_x = Mu_x
        res.Mu_y = Mu_y

        res.As_x_requerido = self.norma.area_acero_flexion(Mu=Mu_x, d=d, fck=fck, fy=fy)
        res.As_y_requerido = self.norma.area_acero_flexion(Mu=Mu_y, d=d, fck=fck, fy=fy)

        res.As_x_minimo = self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d)
        res.As_y_minimo = self.norma.area_acero_minimo(fck=fck, fy=fy, bw=1.0, d=d)

        res.As_x_diseno = max(res.As_x_requerido, res.As_x_minimo)
        res.As_y_diseno = max(res.As_y_requerido, res.As_y_minimo)

        res.varilla_x, res.separacion_x = self._seleccionar_varilla(res.As_x_diseno)
        res.varilla_y, res.separacion_y = self._seleccionar_varilla(res.As_y_diseno)

        res.agregar_mensaje(
            f"✔ Armadura inf. X: {res.varilla_x} @ {res.separacion_x*100:.0f} cm "
            f"(As={res.As_x_diseno:.2f} cm²/m)", "ok"
        )
        res.agregar_mensaje(
            f"✔ Armadura inf. Y: {res.varilla_y} @ {res.separacion_y*100:.0f} cm "
            f"(As={res.As_y_diseno:.2f} cm²/m)", "ok"
        )

    def _seleccionar_varilla(self, As_cm2_por_m: float) -> tuple[str, float]:
        return _seleccionar_varilla(As_cm2_por_m, self.varilla_pref)

    def verificar_longitud_desarrollo(self) -> None:
        res = self.resultados
        B = self.geo.B
        c1 = self.columna.ancho
        recub = self.geo.recubrimiento

        ld_disponible = (B / 2) - (c1 / 2) - recub
        res.ld_disponible = ld_disponible

        db = 0.016
        ld_req = self.norma.longitud_desarrollo(db=db, fck=self.hormigon.fck, fy=self.acero.fy)
        res.ld_requerido = ld_req

        if ld_disponible >= ld_req:
            res.ok_desarrollo = True
            res.agregar_mensaje(
                f"✔ Desarrollo: ld_disp={ld_disponible*100:.0f} cm ≥ ld_req={ld_req*100:.0f} cm", "ok"
            )
        else:
            res.ok_desarrollo = False
            B_minimo = np.ceil(((ld_req + c1 / 2 + recub) * 2) / 0.05) * 0.05
            if self.geo.dimensiones_fijas:
                res.agregar_mensaje(
                    f"✘ Desarrollo insuficiente: ld_disponible={ld_disponible*100:.0f} cm "
                    f"< ld_requerido={ld_req*100:.0f} cm. "
                    f"Las dimensiones están fijadas manualmente. "
                    f"Opciones: (1) Aumentar B a ≥ {B_minimo:.2f} m en 'Fijar dimensiones', "
                    f"o (2) usar ganchos estándar (reducen ld ~30%).",
                    "advertencia"
                )
            else:
                res.agregar_mensaje(
                    f"✘ Desarrollo insuficiente: ld_disponible={ld_disponible*100:.0f} cm "
                    f"< ld_requerido={ld_req*100:.0f} cm. B mínimo necesario = {B_minimo:.2f} m.",
                    "error"
                )

    def _seleccionar_barras_pedestal(self, As_cm2: float, n_min: int = 4) -> tuple:
        barras = [
            ("Ø12mm", 1.131), ("Ø16mm", 2.011), ("Ø20mm", 3.142),
            ("Ø25mm", 4.909), ("Ø32mm", 8.042),
        ]
        for nombre, area in barras:
            n = max(n_min, int(np.ceil(As_cm2 / area)))
            if n % 2 != 0 and n > 4:
                n += 1
            if n * area >= As_cm2:
                return nombre, n, round(n * area, 3)
        nombre, area = "Ø32mm", 8.042
        n = max(n_min, int(np.ceil(As_cm2 / area)))
        return nombre, n, round(n * area, 3)

    def calcular_pedestal(self) -> ResultadosPedestal:
        res = ResultadosPedestal()
        ped = self.geo_pedestal
        fck, fy = self.hormigon.fck, self.acero.fy
        Pu = self.cargas.Pu
        phi_c = 0.65  # ACI 318 §21.2.1 bearing

        # Auto-dimensionar pedestal (mín. 10 cm vuelo cada lado)
        if ped.Bp <= 0:
            ped.Bp = np.ceil((self.columna.ancho + 0.20) / 0.05) * 0.05
        if ped.Lp <= 0:
            ped.Lp = np.ceil((self.columna.largo + 0.20) / 0.05) * 0.05

        res.Bp, res.Lp, res.hp, res.Pu = ped.Bp, ped.Lp, ped.hp, Pu

        # ---- Aplastamiento columna → pedestal (ACI 318 §22.8) ----
        A1_col = self.columna.ancho * self.columna.largo
        A2_ped = ped.Bp * ped.Lp
        f_col = min(np.sqrt(A2_ped / A1_col), 2.0)
        phi_Bn_col = phi_c * 0.85 * fck * A1_col * f_col * 1000  # kN
        res.phi_Bn_col = float(phi_Bn_col)
        res.ok_aplastamiento_col = bool(Pu <= phi_Bn_col)
        res.agregar_mensaje(
            f"{'✔' if res.ok_aplastamiento_col else '✘'} Aplastamiento col→pedestal: "
            f"Pu={Pu:.1f} kN {'≤' if res.ok_aplastamiento_col else '>'} "
            f"φBn={phi_Bn_col:.1f} kN (√A2/A1={f_col:.2f})",
            "ok" if res.ok_aplastamiento_col else "error"
        )

        # ---- Aplastamiento pedestal → zapata ----
        A1_ped = ped.Bp * ped.Lp
        A2_zap = self.geo.B * self.geo.L
        f_zap = min(np.sqrt(A2_zap / A1_ped), 2.0)
        phi_Bn_zap = phi_c * 0.85 * fck * A1_ped * f_zap * 1000  # kN
        res.phi_Bn_zap = float(phi_Bn_zap)
        res.ok_aplastamiento_zap = bool(Pu <= phi_Bn_zap)
        res.agregar_mensaje(
            f"{'✔' if res.ok_aplastamiento_zap else '✘'} Aplastamiento pedestal→zapata: "
            f"Pu={Pu:.1f} kN {'≤' if res.ok_aplastamiento_zap else '>'} "
            f"φBn={phi_Bn_zap:.1f} kN (√A2/A1={f_zap:.2f})",
            "ok" if res.ok_aplastamiento_zap else "error"
        )

        # ---- Armadura longitudinal (ACI 318 §22.4, ρ_min=0.5%) ----
        Ag_cm2 = ped.Bp * ped.Lp * 10000
        res.Ag = Ag_cm2
        As_min = max(0.005 * Ag_cm2, 4 * 1.131)
        res.As_min = As_min
        varilla_l, n_barras, As_long = self._seleccionar_barras_pedestal(As_min, n_min=4)
        res.varilla_long = varilla_l
        res.n_barras = n_barras
        res.As_diseno = As_long
        res.agregar_mensaje(
            f"✔ Armadura long.: {n_barras}{varilla_l} "
            f"(As={As_long:.2f} cm², ρ={As_long/Ag_cm2*100:.2f}%)", "ok"
        )

        # ---- Estribos (ACI 318 §25.7.2) ----
        db_long_mm = float(varilla_l.replace("Ø", "").replace("mm", ""))
        sep_tie_m = min(16 * db_long_mm, 48 * 8.0, min(ped.Bp, ped.Lp) * 1000) / 1000
        sep_tie_m = np.floor(sep_tie_m / 0.01) * 0.01
        res.varilla_estribo = "Ø8mm"
        res.separacion_estribo = sep_tie_m
        res.agregar_mensaje(
            f"✔ Estribos: Ø8mm @ {sep_tie_m*100:.0f} cm "
            f"[min(16×{db_long_mm:.0f}={16*db_long_mm:.0f}, 48×8=384, "
            f"lado={min(ped.Bp,ped.Lp)*100:.0f}) mm]", "ok"
        )

        # ---- Esperas zapata → pedestal (ACI 318 §16.3) ----
        As_esp_min = max(0.005 * Ag_cm2, 4 * 1.131)
        varilla_e, n_esp, As_esp = self._seleccionar_barras_pedestal(As_esp_min, n_min=4)
        res.varilla_espera = varilla_e
        res.n_esperas = n_esp
        res.As_esperas = As_esp

        db_esp_mm = float(varilla_e.replace("Ø", "").replace("mm", ""))
        ld_comp_mm = max(0.24 * fy * db_esp_mm / np.sqrt(fck), 0.043 * fy * db_esp_mm, 200.0)
        ld_comp = ld_comp_mm / 1000  # m
        res.ld_espera_comp = ld_comp

        disp_zapata = self.geo.h - self.geo.recubrimiento
        res.ok_esperas_en_zapata = bool(disp_zapata >= ld_comp)
        res.agregar_mensaje(
            f"{'✔' if res.ok_esperas_en_zapata else '✘'} Esperas: {n_esp}{varilla_e} "
            f"(As={As_esp:.2f} cm²); ld_comp={ld_comp*100:.0f} cm "
            f"{'≤' if res.ok_esperas_en_zapata else '>'} "
            f"h_zap-recub={disp_zapata*100:.0f} cm"
            + ("" if res.ok_esperas_en_zapata else " → Aumentar h zapata"),
            "ok" if res.ok_esperas_en_zapata else "advertencia"
        )

        return res

    def calcular(self) -> ResultadosZapata:
        self.dimensionar_planta()
        if self.resultados.q_neto <= 0 or self.geo.B == 0:
            return self.resultados
        self.calcular_presiones()

        max_iter = 5
        for i in range(max_iter):
            self.verificar_punzonado()
            self.verificar_cortante_unidireccional()

            if self.resultados.ok_punzonado and self.resultados.ok_cortante:
                break
            else:
                self.geo.h += 0.05
                self.resultados.agregar_mensaje(
                    f"ℹ Iteración {i+1}: Aumentando h a {self.geo.h:.2f} m", "info"
                )

        self.geo.h = np.ceil(self.geo.h / 0.05) * 0.05
        self.resultados.h_requerido = self.geo.h

        self.diseno_flexion()
        self.verificar_longitud_desarrollo()
        self.resultados_pedestal = self.calcular_pedestal()

        return self.resultados


# ─── Helper compartido ────────────────────────────────────────────────────────

_VARILLAS = [
    ('Ø8mm',  0.503), ('Ø10mm', 0.785), ('Ø12mm', 1.131),
    ('Ø16mm', 2.011), ('Ø20mm', 3.142), ('Ø25mm', 4.909), ('Ø32mm', 8.042),
]


def _seleccionar_varilla(As_cm2_por_m: float, varilla_forzada: str = '') -> tuple:
    import numpy as np
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
        mejor = ('Ø25mm', sep)
    return mejor[0], np.floor(mejor[1] * 100) / 100
