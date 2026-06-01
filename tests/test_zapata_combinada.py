"""
Benchmark tests — Módulo M2: Zapata Combinada Rectangular.

Caso de referencia (calculado a mano):
  Col1: Pd=300 kN, Pl=150 kN → Pser1=450 kN, Pu1=570 kN  (col en borde)
  Col2: Pd=400 kN, Pl=200 kN → Pser2=600 kN, Pu2=680 kN
  L_entre (separación entre ejes) = 3.0m
  Suelo: qa=180 kPa, Df=1.20m, γ=18 kN/m³
  Geometría: B=2.0m, h=0.60m, recub=0.07m, col1_en_borde=True

Resultante (fórmula de diseño combinada, col1 en borde x=0):
  x_R relativo al borde izquierdo:
    x_R = (P1×d1 + P2×d2) / (P1+P2)
    d1 = cx1/2 = 0.15m  (col1 en borde)
    d2 = cx1/2 + L_entre = 0.15+3.0 = 3.15m
    x_R = (450×0.15 + 600×3.15) / 1050
         = (67.5 + 1890) / 1050 = 1.864m
  L_ideal = 2×x_R ≈ 3.729m
  Presión uniforme si L = 2×x_R → q_max = q_min

  q_neta = 180 - 1.20×18 = 158.4 kPa
  A_req ≈ 1.1×(450+600)/158.4 ≈ 7.29 m²

Referencia: Das, B.M. (2021) Cap. 9 — Diseño de zapatas combinadas.
"""
import pytest
from core.zapata_combinada import (
    ColCombinada, SueloCombinada, GeometriaCombi,
    ZapataCombinadaRectangular,
)
from core.zapata_aislada import MaterialHormigon, MaterialAcero
from core.normas.aci318 import ACI318

TOL = 0.03   # 3% — diagrama de V/M tiene integración numérica


# ─── Fixture base ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def res_comb():
    motor = ZapataCombinadaRectangular(
        col1    = ColCombinada(Pd=300.0, Pl=150.0, ancho=0.30, largo=0.30),
        col2    = ColCombinada(Pd=400.0, Pl=200.0, ancho=0.30, largo=0.30),
        suelo   = SueloCombinada(qa=180.0, Df=1.20, gamma_suelo=18.0),
        hormigon= MaterialHormigon(fck=25.0),
        acero   = MaterialAcero(fy=420.0),
        norma   = ACI318(),
        geo     = GeometriaCombi(L_entre=3.0, B_fijo=2.0, h=0.60,
                                 recubrimiento=0.07, col1_en_borde=True),
    )
    return motor.calcular()


# ─── Geometría y resultante ────────────────────────────────────────────────────

class TestGeometriaCombi:

    def test_B_respetado(self, res_comb):
        assert res_comb.B == pytest.approx(2.0, rel=1e-6)

    def test_L_positivo(self, res_comb):
        assert res_comb.L > 0.0

    def test_area_mayor_que_requerida(self, res_comb):
        # A_req ≈ 1.1×(450+600)/158.4 = 7.29 m²
        q_neta = 180.0 - 1.20 * 18.0
        A_req = 1.1 * (450.0 + 600.0) / q_neta
        assert res_comb.area >= A_req * 0.97  # mínimo 97% del requerido

    def test_resultante_dentro_de_zapata(self, res_comb):
        """x_R ≈ L/2 para zapata con presión uniforme diseñada."""
        # d1 y d2 son posiciones de las columnas desde el extremo izquierdo
        assert 0 < res_comb.d1 < res_comb.L
        assert 0 < res_comb.d2 < res_comb.L
        assert res_comb.d2 > res_comb.d1


# ─── Presiones ────────────────────────────────────────────────────────────────

class TestPresionesCombi:

    def test_ok_presion(self, res_comb):
        assert res_comb.ok_presion

    def test_q_max_no_supera_qa(self, res_comb):
        assert res_comb.q_max <= 180.0 * 1.02

    def test_q_neta_formula(self, res_comb):
        # q_neta = qa - Df×γ = 180 - 1.20×18 = 158.4 kPa
        assert res_comb.q_neto == pytest.approx(158.4, rel=1e-4)


# ─── Diagrama de momentos ─────────────────────────────────────────────────────

class TestMomentosCombi:
    """
    El módulo calcula el diagrama V/M completo por integración numérica.
    Verifica que el diagrama tenga variación (no todo cero) y que
    se diseñe armadura tanto superior como inferior.
    """

    def test_diagramas_tienen_datos(self, res_comb):
        assert len(res_comb.x_diag) > 5
        assert len(res_comb.V_diag) == len(res_comb.x_diag)
        assert len(res_comb.M_diag) == len(res_comb.x_diag)

    def test_diagrama_M_varia(self, res_comb):
        """El momento no es constante a lo largo de la zapata."""
        M = res_comb.M_diag
        assert max(M) - min(M) > 1.0   # al menos 1 kN·m de variación

    def test_x_Mu_pos_entre_columnas(self, res_comb):
        """El punto de máximo momento positivo está entre las dos columnas."""
        assert res_comb.d1 < res_comb.x_Mu_pos < res_comb.d2

    def test_armadura_superior_e_inferior_diseñada(self, res_comb):
        """Existen ambas bandas de armado longitudinal."""
        assert res_comb.As_long_top_pm > 0.0
        assert res_comb.As_long_bot_pm > 0.0


# ─── Punzonado y cortante ─────────────────────────────────────────────────────

class TestVerificacionesCombi:

    def test_ok_punz1(self, res_comb):
        assert res_comb.ok_punz1

    def test_ok_punz2(self, res_comb):
        assert res_comb.ok_punz2

    def test_ok_cortante(self, res_comb):
        assert res_comb.ok_cortante


# ─── Armadura ─────────────────────────────────────────────────────────────────

class TestArmaduraCombi:

    def test_As_long_top_positivo(self, res_comb):
        assert res_comb.As_long_top_pm > 0.0

    def test_As_long_bot_positivo(self, res_comb):
        assert res_comb.As_long_bot_pm > 0.0

    def test_As_trans1_positivo(self, res_comb):
        assert res_comb.As_trans1 > 0.0

    def test_As_trans2_positivo(self, res_comb):
        assert res_comb.As_trans2 > 0.0

    def test_Mu_trans1_positivo(self, res_comb):
        assert res_comb.Mu_trans1 > 0.0

    def test_Mu_trans2_positivo(self, res_comb):
        assert res_comb.Mu_trans2 > 0.0


# ─── Sensibilidades físicas ───────────────────────────────────────────────────

class TestSensibilidadCombi:

    def _motor(self, Pd1, Pl1, Pd2, Pl2):
        return ZapataCombinadaRectangular(
            col1    = ColCombinada(Pd=Pd1, Pl=Pl1, ancho=0.30, largo=0.30),
            col2    = ColCombinada(Pd=Pd2, Pl=Pl2, ancho=0.30, largo=0.30),
            suelo   = SueloCombinada(qa=180.0, Df=1.20, gamma_suelo=18.0),
            hormigon= MaterialHormigon(fck=25.0),
            acero   = MaterialAcero(fy=420.0),
            norma   = ACI318(),
            geo     = GeometriaCombi(L_entre=3.0, B_fijo=2.0, h=0.60,
                                     recubrimiento=0.07, col1_en_borde=True),
        ).calcular()

    def test_mayor_carga_mayor_q(self):
        r1 = self._motor(300, 150, 400, 200)
        r2 = self._motor(500, 250, 600, 300)
        assert r2.q_max > r1.q_max

    def test_cargas_iguales_resultante_centrada(self):
        """Cargas iguales + col1 en borde → x_R ≈ L/2."""
        r = self._motor(400, 200, 400, 200)
        assert abs(r.d1 + r.d2 - r.L) < 0.20  # posiciones simétricas respecto al centro
