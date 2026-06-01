"""
Benchmark tests — Módulo M9.5: Muro de Sótano.

Caso A — Biapoyado, sin nivel freático:
  H=3.0m, e_muro=0.25m, h_NF=99 (sin agua)
  φ_r=30°, c_r=0, γ_r=18, q_s=10 kPa
  fc=25 MPa, fy=420 MPa

Presiones verificadas:
  Ka = tan²(30°) = 1/3
  pa_top = Ka×q_s = (1/3)×10 = 3.333 kPa
  pa_bot = Ka×(γ_r×H + q_s) = (1/3)×(54+10) = 21.333 kPa
  p_total_base = pa_bot (sin agua)

Caso B — Empotrado en base, sin agua:
  Mismos parámetros pero condicion='empotrado_base'
  M_base (momento en empotramiento) debe ser mayor que en biapoyado

Referencia: Das, B.M. (2021) Cap. 13 — Muros de sótano / muros de contención.
"""
import math
import pytest
from core.muro_sotano import MuroSotano

TOL = 0.01


def _motor(condicion='biapoyado', h_NF=99.0, q_s=10.0, H=3.0):
    return MuroSotano().calcular(
        H=H, e_muro=0.25, h_NF=h_NF, condicion=condicion,
        phi_r=30.0, c_r=0.0, gamma_r=18.0, q_s=q_s,
        gamma_w=10.0, fc=25.0, fy=420.0, recub=0.07,
    )


@pytest.fixture(scope="module")
def motor_biap():
    return _motor('biapoyado')


@pytest.fixture(scope="module")
def motor_emp():
    return _motor('empotrado_base')


class TestPresionesLaterales:
    """Ka y distribución de presiones activas — Rankine."""

    def test_Ka(self, motor_biap):
        assert motor_biap.res.Ka == pytest.approx(1/3, rel=1e-4)

    def test_pa_corona(self, motor_biap):
        # pa_corona = Ka×q_s = (1/3)×10 = 3.333 kPa
        assert motor_biap.res.cargas.pa_corona == pytest.approx(3.333, rel=1e-3)

    def test_pa_base(self, motor_biap):
        # pa_base = Ka×(18×3+10) = (1/3)×64 = 21.333 kPa
        assert motor_biap.res.cargas.pa_base == pytest.approx(21.333, rel=1e-3)

    def test_p_total_base_sin_agua(self, motor_biap):
        # Sin NF: p_total = pa_base
        assert motor_biap.res.cargas.p_total_base == pytest.approx(21.333, rel=1e-3)

    def test_presion_con_agua_mayor(self):
        """Con NF a mitad de muro → presión hidrostática adicional."""
        m_seco  = _motor('biapoyado', h_NF=99.0)
        m_agua  = _motor('biapoyado', h_NF=1.5)
        assert m_agua.res.cargas.p_total_base > m_seco.res.cargas.p_total_base


class TestCondicionesBorde:
    """Biapoyado vs. empotrado_base — diferencias en diagrama de momentos."""

    def test_biapoyado_R_top_positivo(self, motor_biap):
        assert motor_biap.res.momentos.R_top > 0.0

    def test_biapoyado_R_bot_positivo(self, motor_biap):
        assert motor_biap.res.momentos.R_bot > 0.0

    def test_biapoyado_equilibrio(self, motor_biap):
        """R_top + R_bot ≈ fuerza horizontal total."""
        res = motor_biap.res
        F_total = res.cargas.Ea + res.cargas.Ew
        R_sum = res.momentos.R_top + res.momentos.R_bot
        assert R_sum == pytest.approx(F_total, rel=0.01)

    def test_empotrado_M_base_no_nulo(self, motor_emp):
        """El empotramiento genera momento en la base."""
        assert abs(motor_emp.res.momentos.M_base) > 0.0

    def test_empotrado_R_top_menor(self, motor_biap, motor_emp):
        """Empotramiento toma momento → reacción superior más pequeña."""
        assert motor_emp.res.momentos.R_top < motor_biap.res.momentos.R_top

    def test_M_max_positivo(self, motor_biap):
        assert motor_biap.res.momentos.M_max > 0.0


class TestDiseñoRC:
    def test_armadura_cara_suelo_positiva(self, motor_biap):
        assert motor_biap.res.vert_cara_suelo.As_dis > 0.0

    def test_armadura_cara_int_positiva(self, motor_biap):
        assert motor_biap.res.vert_cara_int.As_dis > 0.0

    def test_armadura_horizontal_positiva(self, motor_biap):
        assert motor_biap.res.horiz_temp.As_dis > 0.0

    def test_mayor_H_mayor_Mu(self):
        """Mayor altura → mayor empuje → mayor momento → más acero."""
        m3 = _motor('biapoyado', H=3.0)
        m5 = _motor('biapoyado', H=5.0)
        assert m5.res.momentos.M_max > m3.res.momentos.M_max
        assert m5.res.vert_cara_suelo.As_dis >= m3.res.vert_cara_suelo.As_dis


class TestValidacion:
    def test_condicion_invalida(self):
        with pytest.raises(ValueError):
            MuroSotano().calcular(
                H=3.0, e_muro=0.25, h_NF=99.0, condicion='invalida',
                phi_r=30.0, c_r=0.0, gamma_r=18.0, q_s=0.0,
                gamma_w=10.0, fc=25.0, fy=420.0, recub=0.07,
            )

    def test_H_cero_invalido(self):
        with pytest.raises(ValueError):
            MuroSotano().calcular(
                H=0.0, e_muro=0.25, h_NF=99.0, condicion='biapoyado',
                phi_r=30.0, c_r=0.0, gamma_r=18.0, q_s=0.0,
                gamma_w=10.0, fc=25.0, fy=420.0, recub=0.07,
            )
