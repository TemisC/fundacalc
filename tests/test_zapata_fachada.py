"""
Benchmark tests — Módulo M5: Zapata de Fachada.

La zapata de fachada convierte un offset geométrico en momento equivalente:
  Mdx = Pd × ex_geom,  Mlx = Pl × ex_geom   (desplazamiento horizontal en X)
  Mdy = Pd × ey_geom,  Mly = Pl × ey_geom   (desplazamiento en Y, si aplica)

Caso de referencia:
  Pd=500 kN, Pl=250 kN → Pser=750 kN, Pu=1000 kN
  ex_geom=0.30m, ey_geom=0
  Mser_x = 750×0.30 = 225 kN·m  → ex_equivalente = 225/750 = 0.30m
  Columna: cx=cy=0.30m
  Suelo: qa=200 kPa, Df=1.0m, γ=18 kN/m³
  Geometría: B_fijo=2.0m, L_fijo=2.5m, h=0.55m, a_borde=0.10m

Viga de atado (informativa):
  T_atado = Pser × ex / L_atado = 750×0.30/5.0 = 45 kN

Referencia: Das, B.M. (2021) — zapata de fachada con viga de amarre.
"""
import pytest
from core.zapata_fachada import (
    GeometriaFachada, ZapataFachadaRectangular,
)
from core.zapata_excentrica import (
    ColumnaExcentrica, SueloExcentrica,
)
from core.zapata_aislada import MaterialHormigon, MaterialAcero
from core.normas.aci318 import ACI318

TOL = 0.02


# ─── Fixture base ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def res_fach():
    motor = ZapataFachadaRectangular(
        Pd      = 500.0,
        Pl      = 250.0,
        columna = ColumnaExcentrica(cx=0.30, cy=0.30),
        suelo   = SueloExcentrica(qa=200.0, Df=1.0, gamma_suelo=18.0),
        hormigon= MaterialHormigon(fck=25.0),
        acero   = MaterialAcero(fy=420.0),
        norma   = ACI318(),
        geo_fachada = GeometriaFachada(
            ex_geom=0.20, ey_geom=0.0,
            a_borde=0.10,
            B_fijo=2.0, L_fijo=3.0,
            h=0.55, recubrimiento=0.07,
            L_atado=5.0, modo_ras=False,
        ),
    )
    return motor.calcular()


# ─── Conversión geométrica a momento ─────────────────────────────────────────

class TestConversionGeometricaFachada:
    """
    ex = ex_geom cuando la resultante coincide con el offset geométrico.
    Mdx = Pd×ex_geom, Mlx = Pl×ex_geom → ex = Mser_x/Pser = ex_geom.
    """

    def test_ex_igual_a_ex_geom(self, res_fach):
        # ex_equiv = Mser_x/Pser = (Pd+Pl)×ex_geom/(Pd+Pl) = ex_geom = 0.20m
        assert res_fach.ex == pytest.approx(0.20, rel=TOL)

    def test_ey_cero(self, res_fach):
        assert res_fach.ey == pytest.approx(0.0, abs=1e-6)


# ─── Excentricidad fuera del núcleo ──────────────────────────────────────────

class TestNucleoFachada:
    """
    La zapata de fachada típicamente tiene ex > L/6 (diseñada para ello).
    L=2.5m → L/6 = 0.417m. Con ex=0.30m < 0.417m → en núcleo.
    """

    def test_ex_consistente_con_offset(self, res_fach):
        assert res_fach.ex > 0.0

    def test_q_max_mayor_q_min(self, res_fach):
        assert res_fach.q_max > res_fach.q_min

    def test_ok_presion(self, res_fach):
        assert res_fach.ok_presion


# ─── Offset cero equivale a zapata centrada ────────────────────────────────────

class TestFachadaSinOffset:
    def test_offset_cero_presion_uniforme(self):
        res = ZapataFachadaRectangular(
            Pd      = 500.0,
            Pl      = 250.0,
            columna = ColumnaExcentrica(cx=0.30, cy=0.30),
            suelo   = SueloExcentrica(qa=200.0, Df=1.0, gamma_suelo=18.0),
            hormigon= MaterialHormigon(fck=25.0),
            acero   = MaterialAcero(fy=420.0),
            norma   = ACI318(),
            geo_fachada = GeometriaFachada(
                ex_geom=0.0, ey_geom=0.0,
                a_borde=0.10,
                B_fijo=2.0, L_fijo=2.5,
                h=0.55, recubrimiento=0.07,
                L_atado=5.0, modo_ras=False,
            ),
        ).calcular()
        # Sin offset → q1=q2=q3=q4
        assert res.q_max == pytest.approx(res.q_min, rel=0.01)


# ─── Mayor offset → mayor q_max ─────────────────────────────────────────────

class TestSensibilidadFachada:

    def _motor(self, ex_geom):
        return ZapataFachadaRectangular(
            Pd      = 500.0,
            Pl      = 250.0,
            columna = ColumnaExcentrica(cx=0.30, cy=0.30),
            suelo   = SueloExcentrica(qa=250.0, Df=1.0, gamma_suelo=18.0),
            hormigon= MaterialHormigon(fck=25.0),
            acero   = MaterialAcero(fy=420.0),
            norma   = ACI318(),
            geo_fachada = GeometriaFachada(
                ex_geom=ex_geom, ey_geom=0.0,
                a_borde=0.10,
                B_fijo=2.0, L_fijo=3.0,
                h=0.55, recubrimiento=0.07,
                L_atado=5.0, modo_ras=False,
            ),
        ).calcular()

    def test_mayor_offset_mayor_ex(self):
        r1 = self._motor(0.10)
        r2 = self._motor(0.25)
        assert r2.ex > r1.ex

    def test_mayor_offset_mayor_q_max(self):
        r1 = self._motor(0.10)
        r2 = self._motor(0.25)
        assert r2.q_max > r1.q_max


# ─── Verificaciones estructurales ────────────────────────────────────────────

class TestVerificacionesFachada:
    def test_ok_punzonado(self, res_fach):
        assert res_fach.ok_punzonado

    def test_ok_cortante_L(self, res_fach):
        assert res_fach.ok_cortante_L

    def test_ok_cortante_B(self, res_fach):
        assert res_fach.ok_cortante_B

    def test_armadura_positiva(self, res_fach):
        assert res_fach.As_dis_L > 0.0
        assert res_fach.As_dis_B > 0.0

    def test_As_ge_minimo(self, res_fach):
        assert res_fach.As_dis_L >= res_fach.As_min_L
        assert res_fach.As_dis_B >= res_fach.As_min_B
