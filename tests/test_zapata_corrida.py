"""
Benchmark tests — Módulo M3: Zapata Corrida.

Caso de referencia (calculado a mano):
  Pd=120 kN/m, Pl=80 kN/m → Pser=200, Pu=1.2×120+1.6×80=272 kN/m
  Suelo: qa=150 kPa, Df=0.80m, γ=18 kN/m³
  Muro: espesor=0.20m
  Geometría: B=1.60m (fijo), h=0.40m, recub=0.07m

Verificaciones clave:
  q_neta = 150 - 0.80×18 = 135.6 kPa
  Pp     = 1.60×0.40×24  = 15.36 kN/m
  Ps     = 1.60×0.40×18  = 11.52 kN/m  (Df-h=0.40m)
  q_max  = (200+15.36+11.52)/1.60 = 141.8 kPa < 150  ✓
  qu     = 272/1.60 = 170.0 kPa
  a      = (1.60-0.20)/2 = 0.70m
  Mu     = 170.0×0.70²/2 = 41.65 kN·m/m
  Vu_cara= 170.0×0.70    = 119.0 kN/m

Referencia: Das, B.M. (2021) Principles of Foundation Engineering, 9ª ed., Ejemplo cap.13.
"""
import pytest
from core.zapata_corrida import (
    CargaMuro, MuroCorrida, SueloCorrida, GeometriaCorrida,
    ZapataCorridaRectangular,
)
from core.zapata_aislada import MaterialHormigon, MaterialAcero
from core.normas.aci318 import ACI318

TOL = 0.02   # 2%


# ─── Fixture base ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def res_base():
    motor = ZapataCorridaRectangular(
        carga   = CargaMuro(Pd=120.0, Pl=80.0),
        muro    = MuroCorrida(espesor=0.20),
        suelo   = SueloCorrida(qa=150.0, Df=0.80, gamma_suelo=18.0),
        hormigon= MaterialHormigon(fck=25.0),
        acero   = MaterialAcero(fy=420.0),
        norma   = ACI318(),
        geo     = GeometriaCorrida(B_fijo=1.60, h=0.40, recubrimiento=0.07),
    )
    return motor.calcular()


# ─── Geometría ─────────────────────────────────────────────────────────────────

class TestGeometriaCorrida:
    def test_B_fijo_respetado(self, res_base):
        assert res_base.B == pytest.approx(1.60, rel=1e-6)

    def test_voladizo(self, res_base):
        # a = (B - espesor_muro)/2 = (1.60-0.20)/2 = 0.70m
        assert res_base.a == pytest.approx(0.70, rel=1e-4)


# ─── Presiones de servicio ─────────────────────────────────────────────────────

class TestPresionServicioCorrida:
    """q_max ≤ qa — Das cap.13."""

    def test_q_max_no_supera_admisible(self, res_base):
        assert res_base.q_max <= 150.0 * 1.01  # 1% tolerancia de redondeo

    def test_q_max_aprox(self, res_base):
        # q_max = (Pser + Pp + Ps) / B ≈ 141.8 kPa
        assert res_base.q_max == pytest.approx(141.8, rel=TOL)

    def test_ok_presion(self, res_base):
        assert res_base.ok_presion


# ─── Presión ultima y momento ──────────────────────────────────────────────────

class TestMomentoYCortanteCorrida:
    """
    qu = Pu / B = 272/1.60 = 170.0 kPa
    Mu = qu × a²/2 = 170.0×0.49/2 = 41.65 kN·m/m
    """

    def test_q_ultima(self, res_base):
        # qu = Pu/B = 272/1.60 = 170 kPa
        assert res_base.q_ultima == pytest.approx(170.0, rel=1e-4)

    def test_Mu(self, res_base):
        # Mu = qu × a²/2 = 170 × 0.70²/2 = 41.65 kN·m/m
        assert res_base.Mu == pytest.approx(41.65, rel=TOL)

    def test_ok_cortante(self, res_base):
        assert res_base.ok_cortante


# ─── Armadura ─────────────────────────────────────────────────────────────────

class TestArmaduraCorrida:
    def test_As_diseno_ge_As_min(self, res_base):
        assert res_base.As_diseno >= res_base.As_min

    def test_separacion_en_rango(self, res_base):
        assert 0.08 <= res_base.separacion <= 0.40


# ─── Sensibilidades físicas ───────────────────────────────────────────────────

class TestSensibilidadCorrida:

    def _motor(self, Pd, Pl, B=1.60):
        return ZapataCorridaRectangular(
            carga   = CargaMuro(Pd=Pd, Pl=Pl),
            muro    = MuroCorrida(espesor=0.20),
            suelo   = SueloCorrida(qa=150.0, Df=0.80, gamma_suelo=18.0),
            hormigon= MaterialHormigon(fck=25.0),
            acero   = MaterialAcero(fy=420.0),
            norma   = ACI318(),
            geo     = GeometriaCorrida(B_fijo=B, h=0.40, recubrimiento=0.07),
        ).calcular()

    def test_mayor_carga_mayor_qu(self):
        r1 = self._motor(120, 80)
        r2 = self._motor(200, 120)
        assert r2.q_ultima > r1.q_ultima

    def test_mayor_carga_mayor_Mu(self):
        r1 = self._motor(120, 80)
        r2 = self._motor(200, 120)
        assert r2.Mu > r1.Mu

    def test_mayor_B_menor_qu(self):
        r160 = self._motor(120, 80, B=1.60)
        r200 = self._motor(120, 80, B=2.00)
        assert r200.q_ultima < r160.q_ultima


# ─── Autodimensionamiento ─────────────────────────────────────────────────────

class TestAutodimensionamientoCorrida:
    """Con B_fijo=0 el motor elige B automáticamente."""

    def test_auto_B_positivo(self):
        res = ZapataCorridaRectangular(
            carga   = CargaMuro(Pd=150.0, Pl=100.0),
            muro    = MuroCorrida(espesor=0.25),
            suelo   = SueloCorrida(qa=120.0, Df=1.00, gamma_suelo=18.0),
            hormigon= MaterialHormigon(fck=25.0),
            acero   = MaterialAcero(fy=420.0),
            norma   = ACI318(),
            geo     = GeometriaCorrida(B_fijo=0.0, h=0.45, recubrimiento=0.07),
        ).calcular()
        assert res.B > 0.0
        assert res.ok_presion
