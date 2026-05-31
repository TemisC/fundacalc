"""
Motor de cálculo para Zapata de Fachada / Excéntrica por Geometría.

La columna NO está centrada sobre la zapata por restricciones de terreno
(medianera, lindero, construcción existente, etc.).
La excentricidad geométrica (ex_geom, ey_geom) genera momentos equivalentes:
    Mser_x = Pser × ex_geom
    Mux    = Pu   × ex_geom   (derivado de Mdx=Pd·ex, Mlx=Pl·ex)

La distribución de presiones es idéntica a la zapata excéntrica por carga (Navier).
Diferencia principal: la restricción de auto-dimensionamiento incluye
    L ≥ 2·(|ex_geom| + cx/2 + a_borde)
para que la columna quede dentro de la zapata con el vuelo mínimo en el lado restringido.
"""
from dataclasses import dataclass
import math

from core.zapata_excentrica import (
    ZapataExcentricaRectangular,
    CargaExcentrica,
    ColumnaExcentrica,
    SueloExcentrica,
    GeometriaExcentrica,
)
from core.zapata_aislada import MaterialHormigon, MaterialAcero
from core.normas.base import NormaBase


# ─── Dataclasses propios ──────────────────────────────────────────────────────

@dataclass
class GeometriaFachada:
    """Geometría de zapata de fachada con excentricidad de posición."""
    ex_geom:  float = 0.60    # Offset col.→centroide zapata, dir. L [m] (ignorado en modo_ras)
    ey_geom:  float = 0.00    # Offset col.→centroide zapata, dir. B [m]
    a_borde:  float = 0.10    # Vuelo exacto en el lado restringido en modo_ras; mínimo en modo normal
    B_fijo:   float = 0.0     # 0 = auto
    L_fijo:   float = 0.0     # 0 = auto
    h:        float = 0.50
    recubrimiento: float = 0.075
    L_atado:  float = 5.0     # Luz asumida de viga de atado [m] (referencial)
    modo_ras: bool  = False   # True → ex_geom se deriva de L para mantener a_borde exacto

    @property
    def d(self) -> float:
        return self.h - self.recubrimiento - 0.010


# ─── Motor principal ──────────────────────────────────────────────────────────

class ZapataFachadaRectangular(ZapataExcentricaRectangular):
    """
    Zapata de fachada: columna descentrada por restricción geométrica.
    Hereda todo el cálculo de ZapataExcentricaRectangular y sólo redefine
    el auto-dimensionamiento para respetar la restricción de borde.
    """

    def __init__(
        self,
        Pd:         float,
        Pl:         float,
        columna:    ColumnaExcentrica,
        suelo:      SueloExcentrica,
        hormigon:   MaterialHormigon,
        acero:      MaterialAcero,
        norma:      NormaBase,
        geo_fachada: GeometriaFachada,
        varilla_pref: str = "",
    ):
        ex = geo_fachada.ex_geom
        ey = geo_fachada.ey_geom

        # Conversión a CargaExcentrica equivalente:
        #   Mdx = Pd·ex, Mlx = Pl·ex  →  Mser_x = Pser·ex  y  Mux = Pu·ex  ✓
        carga = CargaExcentrica(
            Pd=Pd,  Pl=Pl,
            Mdx=Pd * ex,  Mlx=Pl * ex,
            Mdy=Pd * ey,  Mly=Pl * ey,
        )

        geo_exc = GeometriaExcentrica(
            B_fijo=geo_fachada.B_fijo,
            L_fijo=geo_fachada.L_fijo,
            h=geo_fachada.h,
            recubrimiento=geo_fachada.recubrimiento,
        )

        super().__init__(
            carga, columna, suelo, hormigon, acero, norma, geo_exc, varilla_pref
        )

        # Atributos extra de fachada
        self.geo_fachada = geo_fachada
        self.ex_geom     = ex
        self.ey_geom     = ey
        self.a_borde     = geo_fachada.a_borde
        self.L_atado     = geo_fachada.L_atado
        self.T_atado     = 0.0   # calculado en _dimensionar
        self.Pd_orig     = Pd    # guardados para modo_ras (carga se recalcula con ex derivado)
        self.Pl_orig     = Pl

    # ── Override: re-size after h-adjustment (modo_ras only) ─────────────────
    # The parent's calcular() may bump geo.h for punching/shear, adding extra
    # self-weight that pushes q_max above qa.  If that happens, run _dimensionar
    # again with the finalized h so B is sized correctly.

    def calcular(self):
        super().calcular()
        if (self.geo_fachada.modo_ras
                and not self.res.ok_presion
                and self.geo.h > self.geo_fachada.h):
            self._dimensionar()
            self._presiones()
            self._verificar_punzonado()
            self._verificar_cortante()
            self._armadura()
        return self.res

    # ── Override: dimensionamiento con restricción geométrica ─────────────────

    def _dimensionar(self):
        res   = self.res
        suelo = self.suelo
        col   = self.columna
        geo   = self.geo
        ey    = abs(self.ey_geom)

        q_neto = suelo.qa - suelo.Df * suelo.gamma_suelo
        res.q_neto = q_neto

        if q_neto <= 0:
            res.agregar_mensaje("ERROR: presión neta ≤ 0. Revisar Df y γ del suelo.", "error")
            return

        # ── Branch 1: dimensiones fijas ──────────────────────────────────────
        if geo.B_fijo > 0 and geo.L_fijo > 0:
            B = geo.B_fijo
            L = geo.L_fijo
            if self.geo_fachada.modo_ras:
                ex = round(max(0.0, L / 2 - col.cx / 2 - self.a_borde), 8)
                self.ex_geom = ex
                self.carga = CargaExcentrica(
                    Pd=self.Pd_orig, Pl=self.Pl_orig,
                    Mdx=self.Pd_orig * ex, Mlx=self.Pl_orig * ex,
                    Mdy=self.Pd_orig * self.ey_geom, Mly=self.Pl_orig * self.ey_geom,
                )

        # ── Branch 2: modo_ras — ex se deriva de L en cada iteración ─────────
        # Las fórmulas de presión son iguales a las del padre (_presiones):
        #   contacto total:   q_max = P_total/(B·L) + 6·Pser·ex/(B·L²)
        #   contacto parcial: q_max = 2·P_total/(3·B·arm)  con arm = L/2 - ex (= cx/2+a_borde, constante)
        #   P_total = Pser + B·L·Pp_m2  (Pp_m2 = h·24 + max(Df-h,0)·γs)
        elif self.geo_fachada.modo_ras:
            Pser  = self.Pd_orig + self.Pl_orig
            Pp_m2 = geo.h * 24.0 + max(suelo.Df - geo.h, 0.0) * suelo.gamma_suelo
            # arm = brazo de contacto (constante en modo_ras: no depende de L)
            arm_c = col.cx / 2.0 + self.a_borde

            B_min = max(col.cy + 0.20 if ey <= 0.01
                        else 2.0 * (ey + col.cy / 2.0 + self.a_borde), 0.60)
            L_min = max(col.cx + 2.0 * self.a_borde, 0.60)

            L = math.ceil(L_min / 0.05) * 0.05
            B = B_min

            for _ in range(400):
                ex = round(max(0.0, L / 2.0 - col.cx / 2.0 - self.a_borde), 8)

                # B mínimo analítico que satisface la presión (misma fórmula que el padre)
                if ex <= L / 6.0:            # contacto total (Navier)
                    q_disp = suelo.qa - Pp_m2   # capacidad disponible para carga estructural
                    if q_disp <= 0:
                        L += 0.05; continue
                    B_calc = Pser * (1.0 + 6.0 * ex / L) / (L * q_disp)
                else:                        # contacto parcial (Meyerhof)
                    denom = 3.0 * arm_c * suelo.qa - 2.0 * L * Pp_m2
                    if denom <= 0:           # L supera límite físico → no hay solución mayor
                        break
                    B_calc = 2.0 * Pser / denom

                B0 = max(B_calc, B_min)
                B  = math.ceil(B0 / 0.05) * 0.05

                # Verificación completa (redondeo + ey)
                P_total = Pser + B * L * Pp_m2
                if ex <= L / 6.0:
                    q_test = (P_total / (B * L)
                              + 6.0 * Pser * ex / (B * L ** 2)
                              + (6.0 * Pser * ey / (B ** 2 * L) if ey > 0.01 else 0.0))
                else:
                    q_test = (2.0 * P_total / (3.0 * B * arm_c)
                              + (6.0 * Pser * ey / (B ** 2 * L) if ey > 0.01 else 0.0))

                if q_test <= suelo.qa:
                    break
                L += 0.05

            ex = round(max(0.0, L / 2.0 - col.cx / 2.0 - self.a_borde), 8)

            self.ex_geom = ex
            self.carga = CargaExcentrica(
                Pd=self.Pd_orig, Pl=self.Pl_orig,
                Mdx=self.Pd_orig * ex, Mlx=self.Pl_orig * ex,
                Mdy=self.Pd_orig * self.ey_geom, Mly=self.Pl_orig * self.ey_geom,
            )

        # ── Branch 3: modo normal — ex_geom es input fijo ────────────────────
        else:
            carga  = self.carga
            ex     = abs(self.ex_geom)
            Pp_est = 0.10 * carga.Pser
            A0     = (carga.Pser + Pp_est) / q_neto

            L_min_geom = 2.0 * (ex + col.cx / 2.0 + self.a_borde)
            B_min_geom = (2.0 * (ey + col.cy / 2.0 + self.a_borde)
                          if ey > 0.01 else col.cy + 0.20)

            L_min = max(L_min_geom, col.cx + 2 * 0.15, 0.60)
            B_min = max(B_min_geom, col.cy + 2 * 0.15, 0.60)

            L0 = max(math.sqrt(A0), L_min)
            B0 = max(A0 / L0, B_min)
            L  = math.ceil(L0 / 0.05) * 0.05
            B  = math.ceil(B0 / 0.05) * 0.05

            for _ in range(40):
                q_test = (carga.Pser / (B * L)) * (
                    1.0 + 6.0 * abs(carga.ex) / L + 6.0 * abs(carga.ey) / B)
                if q_test <= suelo.qa:
                    break
                if abs(carga.ex) / L >= abs(carga.ey) / B:
                    L += 0.05
                else:
                    B += 0.05

        # ── Resultados comunes (carga puede haber sido actualizada) ───────────
        carga = self.carga
        res.ex   = carga.ex
        res.ey   = carga.ey
        res.ex_u = carga.Mux / carga.Pu if carga.Pu > 0 else 0.0
        res.ey_u = carga.Muy / carga.Pu if carga.Pu > 0 else 0.0

        res.B = B
        res.L = L
        res.h = geo.h
        res.d = geo.d
        res.A = B * L

        ex = abs(self.ex_geom)
        Pser_total = carga.Pser + B * L * geo.h * 24.0
        self.T_atado = (Pser_total * ex / self.L_atado) if (self.L_atado > 0 and ex > 0) else 0.0

        vuelo_borde = L / 2.0 - ex - col.cx / 2.0
        res.agregar_mensaje(
            f"ℹ Dimensiones: B={B:.2f} m × L={L:.2f} m  "
            f"(ex_geom={self.ex_geom:.3f} m, ey_geom={self.ey_geom:.3f} m)", "info")
        res.agregar_mensaje(
            f"ℹ Vuelo lado restringido = {vuelo_borde:.3f} m  "
            f"({'exacto' if self.geo_fachada.modo_ras else 'mín.'} a_borde = {self.a_borde:.3f} m)", "info")
        res.agregar_mensaje(
            f"ℹ Momento equiv. servicio: Mx={carga.Mser_x:.1f} kN·m  |  "
            f"Viga de atado (L={self.L_atado:.1f} m): T ≈ {self.T_atado:.1f} kN", "info")
