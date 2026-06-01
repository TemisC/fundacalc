"""
Benchmark tests — Módulo M9.4: Muro con Contrafuertes.

Caso de referencia:
  H=5.0m, h_zapata=0.60m, e_pantalla=0.25m, e_contrafuerte=0.40m
  B_punta=0.80m, B_talon=2.60m, s=3.50m (separación entre contrafuertes)
  γ_r=18 kN/m³, φ_r=30°, q_s=0, γ_f=18, φ_f=30°, qa=200 kPa
  fc=25 MPa, fy=420 MPa

Verificaciones clave:
  h_fuste = H − h_zapata = 4.40m
  B_total = B_punta + e_pantalla + B_talon = 3.65m
  L_libre = s − e_contrafuerte = 3.10m
  Ka = tan²(30°) = 1/3

Diseño pantalla (ACI 8.3.3 — losa continua):
  p_base = Ka × γ_r × h_fuste = (1/3)×18×4.40 = 26.40 kPa
  wu_pant = 1.6×p_base = 42.24 kN/m²
  Mu_neg = wu×L²/10 = 42.24×9.61/10 = 40.59 kN·m/m  (en contrafuerte)
  Mu_pos = wu×L²/14 = 42.24×9.61/14 = 28.99 kN·m/m  (vano)

Referencia: Das, B.M. (2021) Cap. 14 — Muros de contrafuertes.
"""
import math
import pytest
from core.muro_contrafuertes import MuroContrafuertes

TOL = 0.01


@pytest.fixture(scope="module")
def motor():
    return MuroContrafuertes().calcular(
        H=5.0, h_zapata=0.60, e_pantalla=0.25, e_contrafuerte=0.40,
        B_punta=0.80, B_talon=2.60, s=3.50,
        gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
        gamma_f=18.0, phi_f=30.0, c_f=0.0, qa=200.0,
        gamma_c=24.0, fc=25.0, fy=420.0, recub=0.07, delta_factor=0.667,
    )


class TestGeometriaContrafuertes:
    def test_h_fuste(self, motor):
        assert motor.res.h_fuste == pytest.approx(4.40, rel=1e-4)

    def test_B_total(self, motor):
        assert motor.res.B_total == pytest.approx(3.65, rel=1e-4)

    def test_L_libre(self, motor):
        assert motor.res.L_libre == pytest.approx(3.10, rel=1e-4)


class TestEmpujeContrafuertes:
    def test_Ka(self, motor):
        assert motor.res.Ka == pytest.approx(1/3, rel=1e-4)

    def test_Ea_total(self, motor):
        # Ea = 0.5×(1/3)×18×(5.0)² = 75.0 kN/m
        assert motor.res.estabilidad.Ea == pytest.approx(75.0, rel=TOL)


class TestEstabilidadContrafuertes:
    def test_ok_vuelco(self, motor):
        assert motor.res.estabilidad.ok_vuelco

    def test_ok_desliz(self, motor):
        assert motor.res.estabilidad.ok_desliz

    def test_ok_presion(self, motor):
        assert motor.res.estabilidad.ok_presion

    def test_FS_vuelco_mayor_2(self, motor):
        assert motor.res.estabilidad.FS_vuelco >= 2.0

    def test_FS_desliz_mayor_1_5(self, motor):
        assert motor.res.estabilidad.FS_desliz >= 1.5


class TestDiseñoPantallaContrafuertes:
    """Pantalla diseñada como losa continua — ACI 8.3.3."""

    def test_Mu_neg_mayor_que_cero(self, motor):
        assert motor.res.pantalla_neg.Mu > 0.0

    def test_Mu_pos_mayor_que_cero(self, motor):
        assert motor.res.pantalla_pos.Mu > 0.0

    def test_Mu_neg_mayor_que_Mu_pos(self, motor):
        """El momento de apoyo (neg.) debe ser mayor que el de vano (pos.)."""
        assert motor.res.pantalla_neg.Mu > motor.res.pantalla_pos.Mu

    def test_Mu_neg_formula(self, motor):
        """Mu_neg = wu×L²/10 — ACI losa continua."""
        Ka = motor.res.Ka
        p_base = Ka * 18.0 * motor.res.h_fuste
        wu = 1.6 * p_base
        L = motor.res.L_libre
        expected = wu * L**2 / 10.0
        assert motor.res.pantalla_neg.Mu == pytest.approx(expected, rel=TOL)

    def test_Mu_pos_formula(self, motor):
        """Mu_pos = wu×L²/14 — ACI losa continua."""
        Ka = motor.res.Ka
        p_base = Ka * 18.0 * motor.res.h_fuste
        wu = 1.6 * p_base
        L = motor.res.L_libre
        expected = wu * L**2 / 14.0
        assert motor.res.pantalla_pos.Mu == pytest.approx(expected, rel=TOL)


class TestDiseñoZapataContrafuertes:
    def test_punta_As_positivo(self, motor):
        assert motor.res.punta.As_dis > 0.0

    def test_talon_As_positivo(self, motor):
        assert motor.res.talon.As_dis > 0.0

    def test_contrafuerte_Mu_positivo(self, motor):
        assert motor.res.contrafuerte.Mu > 0.0


class TestSensibilidadContrafuertes:
    def _motor(self, s):
        return MuroContrafuertes().calcular(
            H=5.0, h_zapata=0.60, e_pantalla=0.25, e_contrafuerte=0.40,
            B_punta=0.80, B_talon=2.60, s=s,
            gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0, qa=200.0,
        )

    def test_mayor_separacion_mayor_Mu_pantalla(self):
        """Mayor separación entre contrafuertes → mayor luz → mayor Mu_neg."""
        m3 = self._motor(3.0)
        m5 = self._motor(5.0)
        assert m5.res.pantalla_neg.Mu > m3.res.pantalla_neg.Mu
