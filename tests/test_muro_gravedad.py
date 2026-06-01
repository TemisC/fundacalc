"""
Benchmark tests — Módulo M9.2: Muro de Gravedad.

Caso de referencia (calculado a mano):
  H=3.0m, b_base=2.5m, b_corona=0.7m, h_emb=0.5m
  γ_muro=24 kN/m³, γ_r=18 kN/m³, φ_r=30°, q_s=0, γ_f=18, φ_f=30°, c_f=0
  qa=200 kPa, δ_factor=0.667

Fórmulas verificadas (Das, 9ª ed., Cap. 14):
  Ka = tan²(45-15°) = tan²(30°) = 1/3
  Ea = 0.5×Ka×γ×H² = 0.5×(1/3)×18×9 = 27.0 kN/m
  Mo = Ea×H/3 = 27.0×1.0 = 27.0 kN·m/m
  A_sec = (2.5+0.7)/2 × 3.0 = 4.8 m²
  W = 24×4.8 = 115.2 kN/m
  x_CG = (b·bc + (b-bc)²/3) / (b+bc) = (1.75+1.08)/3.2 = 0.8844m
  Mr = 115.2×0.8844 = 101.88 kN·m/m
  FS_v = 101.88/27.0 = 3.774
  FS_d ≈ 1.804  (con δ=20°, Ep=6.75 kN/m)
"""
import math
import pytest
from core.muro_gravedad import MuroGravedad

TOL = 0.005  # 0.5%


@pytest.fixture(scope="module")
def motor():
    return MuroGravedad().calcular(
        H=3.0, b_base=2.5, b_corona=0.7, h_emb=0.5,
        gamma_muro=24.0, gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
        gamma_f=18.0, phi_f=30.0, c_f=0.0, qa=200.0, delta_factor=0.667,
    )


class TestKaGravedad:
    def test_Ka_Rankine(self, motor):
        assert motor.res.Ka == pytest.approx(1/3, rel=1e-4)

    def test_Ka_varios_phi(self):
        for phi in [20.0, 25.0, 35.0]:
            m = MuroGravedad().calcular(
                H=3.0, b_base=2.0, b_corona=0.6, h_emb=0.3,
                gamma_muro=22.0, gamma_r=18.0, phi_r=phi, c_r=0.0, q_s=0.0,
                gamma_f=18.0, phi_f=phi, c_f=0.0, qa=200.0,
            )
            expected = math.tan(math.radians(45 - phi/2))**2
            assert m.res.Ka == pytest.approx(expected, rel=1e-4)


class TestEmpujeGravedad:
    def test_Ea_gamma(self, motor):
        # Ea_gamma = 0.5×Ka×γ×H² = 0.5×(1/3)×18×9 = 27.0 kN/m
        assert motor.res.estabilidad.Ea_gamma == pytest.approx(27.0, rel=TOL)

    def test_Ea_q_cero_sin_sobrecarga(self, motor):
        assert motor.res.estabilidad.Ea_q == pytest.approx(0.0, abs=1e-6)

    def test_Ea_total(self, motor):
        assert motor.res.estabilidad.Ea == pytest.approx(27.0, rel=TOL)

    def test_momento_volcador(self, motor):
        # Mo = Ea×H/3 = 27.0×1.0 = 27.0 kN·m/m
        assert motor.res.estabilidad.Mo == pytest.approx(27.0, rel=TOL)

    def test_Ea_aumenta_con_sobrecarga(self):
        m = MuroGravedad().calcular(
            H=3.0, b_base=2.5, b_corona=0.7, h_emb=0.5,
            gamma_muro=24.0, gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=10.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0, qa=200.0,
        )
        assert m.res.estabilidad.Ea > 27.0


class TestPesoYCentroide:
    def test_W_muro(self, motor):
        # W = 24 × (2.5+0.7)/2 × 3.0 = 115.2 kN/m
        assert motor.res.estabilidad.W_muro == pytest.approx(115.2, rel=TOL)

    def test_x_CG_formula(self, motor):
        # x_CG = (b_base×b_corona + (b_base−b_corona)²/3) / (b_base+b_corona)
        b, bc = 2.5, 0.7
        expected = (b*bc + (b-bc)**2/3) / (b+bc)
        assert motor.res.estabilidad.x_CG == pytest.approx(expected, rel=1e-4)

    def test_momento_resistente(self, motor):
        # Mr = W × x_CG = 115.2 × 0.8844 ≈ 101.88 kN·m/m
        assert motor.res.estabilidad.Mr == pytest.approx(101.88, rel=TOL)


class TestEstabilidadGravedad:
    def test_FS_vuelco(self, motor):
        assert motor.res.estabilidad.FS_vuelco == pytest.approx(3.774, rel=0.01)

    def test_FS_deslizamiento(self, motor):
        assert motor.res.estabilidad.FS_desliz == pytest.approx(1.804, rel=0.01)

    def test_ok_vuelco(self, motor):
        assert motor.res.estabilidad.ok_vuelco

    def test_ok_desliz(self, motor):
        assert motor.res.estabilidad.ok_desliz

    def test_ok_presion(self, motor):
        assert motor.res.estabilidad.ok_presion

    def test_q_max_no_supera_qa(self, motor):
        assert motor.res.estabilidad.q_max <= 200.0 * 1.01


class TestSensibilidadGravedad:
    def _motor(self, b_base, b_corona=0.7):
        return MuroGravedad().calcular(
            H=3.0, b_base=b_base, b_corona=b_corona, h_emb=0.5,
            gamma_muro=24.0, gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0, qa=200.0,
        )

    def test_mayor_base_mayor_FS_vuelco(self):
        m1 = self._motor(2.0)
        m2 = self._motor(3.0)
        assert m2.res.estabilidad.FS_vuelco > m1.res.estabilidad.FS_vuelco

    def test_mayor_phi_menor_empuje(self):
        m30 = MuroGravedad().calcular(
            H=3.0, b_base=2.5, b_corona=0.7, h_emb=0.5,
            gamma_muro=24.0, gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0, qa=200.0,
        )
        m38 = MuroGravedad().calcular(
            H=3.0, b_base=2.5, b_corona=0.7, h_emb=0.5,
            gamma_muro=24.0, gamma_r=18.0, phi_r=38.0, c_r=0.0, q_s=0.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0, qa=200.0,
        )
        assert m38.res.estabilidad.Ea < m30.res.estabilidad.Ea

    def test_validacion_b_corona_mayor_base(self):
        with pytest.raises(ValueError):
            MuroGravedad().calcular(
                H=3.0, b_base=1.0, b_corona=2.0, h_emb=0.5,
                gamma_muro=24.0, gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
                gamma_f=18.0, phi_f=30.0, c_f=0.0, qa=200.0,
            )
