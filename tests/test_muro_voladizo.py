"""
Benchmark tests — Módulo 9.1: Muro en Voladizo (MuroVoladizo).

Caso de referencia calculado a mano:
  H=5.0m  h_zapata=0.50m  b_base=0.40m  b_corona=0.30m
  B_punta=0.80m  B_talon=2.30m  γr=18 kN/m³  φr=30°  γc=24 kN/m³

Fórmulas verificadas:
  Ka = tan²(45-φ/2)                               [Rankine]
  Ea = ½·Ka·γ·H²                                  (q_s=0)
  Mo = Ea·H/3
  Mr = ΣWi·xi  (pesos × brazos al pie del muro)
  FS_v = Mr/Mo ≥ 2.0
  FS_d = (ΣW·tan δ + c·B + Ep) / Ea  ≥ 1.5
  q_max = (W/B)·(1 + 6e/B)
"""
import math
import pytest
from core.muro_voladizo import MuroVoladizo


# ─── Fixture: motor con caso base ────────────────────────────────────────────

@pytest.fixture(scope="module")
def motor():
    return MuroVoladizo().calcular(
        H=5.0, h_zapata=0.50,
        b_base=0.40, b_corona=0.30,
        B_punta=0.80, B_talon=2.30,
        gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
        gamma_f=18.0, phi_f=30.0, c_f=0.0,
        gamma_c=24.0, qa=150.0,
        fc=25.0, fy=420.0, recub=0.07,
        delta_factor=0.667,
    )


# ─── Test 1: Ka de Rankine ─────────────────────────────────────────────────────

class TestRankineKa:
    """Ka = tan²(45 - φ/2)  — Rankine (1857)."""

    def test_phi_30(self, motor):
        # tan²(30°) = (1/√3)² = 1/3
        assert motor.res.Ka == pytest.approx(1 / 3, rel=1e-4)

    @pytest.mark.parametrize("phi, ka_expected", [
        (20.0, math.tan(math.radians(35)) ** 2),   # tan²(35°) ≈ 0.4903
        (25.0, math.tan(math.radians(32.5)) ** 2), # tan²(32.5°) ≈ 0.4058
        (38.0, math.tan(math.radians(26)) ** 2),   # tan²(26°) ≈ 0.2388
    ])
    def test_ka_varios_phi(self, phi, ka_expected):
        m = MuroVoladizo().calcular(
            H=4.0, h_zapata=0.40,
            b_base=0.35, b_corona=0.25,
            B_punta=0.60, B_talon=1.80,
            gamma_r=18.0, phi_r=phi, c_r=0.0, q_s=0.0,
            gamma_f=18.0, phi_f=phi, c_f=0.0,
            gamma_c=24.0, qa=150.0,
        )
        assert m.res.Ka == pytest.approx(ka_expected, rel=1e-4)


# ─── Test 2: Empuje activo ──────────────────────────────────────────────────

class TestEmpujeActivo:
    """
    Ea = ½·Ka·γ·H²  (sin sobrecarga)
    Ka = 1/3, γ=18, H=5 → Ea = 0.5 × (1/3) × 18 × 25 = 75.0 kN/m
    Mo = Ea × H/3 = 75 × 5/3 = 125.0 kN·m/m
    """

    def test_ea_total(self, motor):
        est = motor.res.estabilidad
        assert est.Ea == pytest.approx(75.0, rel=0.005)

    def test_momento_volcador(self, motor):
        est = motor.res.estabilidad
        assert est.Mo == pytest.approx(125.0, rel=0.005)


# ─── Test 3: Pesos y momento resistente ────────────────────────────────────

class TestPesosYMr:
    """
    b_avg = (0.40+0.30)/2 = 0.35m
    W_fuste      = 24 × 0.35 × 4.50  =  37.8 kN/m   x=0.975m
    W_zapata     = 24 × 3.50 × 0.50  =  42.0 kN/m   x=1.750m
    W_talon_soil = 18 × 2.30 × 4.50  = 186.3 kN/m   x=2.350m
    W_total = 266.1 kN/m
    Mr = 36.855 + 73.500 + 437.805 = 548.16 kN·m/m
    """

    def test_peso_total(self, motor):
        assert motor.res.estabilidad.W_total == pytest.approx(266.1, rel=0.005)

    def test_momento_resistente(self, motor):
        assert motor.res.estabilidad.Mr == pytest.approx(548.16, rel=0.005)


# ─── Test 4: Factores de seguridad ────────────────────────────────────────

class TestFactoresDeSeguridadEstabilidad:
    """
    FS_v = 548.16 / 125.0 = 4.385
    FS_d: F_resist = W·tan(δ) + Ep, δ=20.01°, Ep=6.75 kN/m → FS_d ≈ 1.382
    q_max ≈ 96.88 kPa
    |e| = 0.1598m < B/6 = 0.583m  → ok
    """

    def test_fs_vuelco(self, motor):
        assert motor.res.estabilidad.FS_vuelco == pytest.approx(4.385, rel=0.005)

    def test_fs_deslizamiento(self, motor):
        assert motor.res.estabilidad.FS_desliz == pytest.approx(1.382, rel=0.01)

    def test_presion_maxima_base(self, motor):
        assert motor.res.estabilidad.q_max == pytest.approx(96.88, rel=0.01)

    def test_excentricidad_dentro_tercio_medio(self, motor):
        est = motor.res.estabilidad
        B_total = motor.res.B_total
        assert abs(est.e) <= B_total / 6

    def test_checks_globales_pasan(self, motor):
        # Caso base: vuelco, presión y excentricidad OK.
        # FS_desliz=1.382 < 1.5 → ok_desliz=False es comportamiento correcto
        # (B_talon=2.30m insuficiente para este suelo/geometría).
        est = motor.res.estabilidad
        assert est.ok_vuelco
        assert est.ok_presion
        assert est.ok_excentricidad
        assert not est.ok_desliz          # esperado: FS_d=1.38 < 1.50

    def test_talón_mayor_mejora_deslizamiento(self):
        """Aumentar B_talon → más peso → FS_d aumenta."""
        m_angosto = MuroVoladizo().calcular(
            H=5.0, h_zapata=0.50, b_base=0.40, b_corona=0.30,
            B_punta=0.80, B_talon=2.30,
            gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0,
            gamma_c=24.0, qa=150.0,
        )
        m_ancho = MuroVoladizo().calcular(
            H=5.0, h_zapata=0.50, b_base=0.40, b_corona=0.30,
            B_punta=0.80, B_talon=3.50,
            gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0,
            gamma_c=24.0, qa=150.0,
        )
        assert m_ancho.res.estabilidad.FS_desliz > m_angosto.res.estabilidad.FS_desliz
        assert m_ancho.res.estabilidad.ok_desliz


# ─── Test 5: Geometría ───────────────────────────────────────────────────────

class TestGeometria:
    def test_B_total(self, motor):
        assert motor.res.B_total == pytest.approx(3.50, rel=1e-6)

    def test_h_fuste(self, motor):
        assert motor.res.h_fuste == pytest.approx(4.50, rel=1e-6)

    def test_Ka_campo_resultado(self, motor):
        assert motor.res.Ka == pytest.approx(1 / 3, rel=1e-4)


# ─── Test 6: Sensibilidades físicas esperadas ───────────────────────────────

class TestSensibilidad:
    """Aumentar φ_r → Ka menor → Ea menor → FS_v mayor."""

    def _motor_con_phi(self, phi):
        return MuroVoladizo().calcular(
            H=5.0, h_zapata=0.50,
            b_base=0.40, b_corona=0.30,
            B_punta=0.80, B_talon=2.30,
            gamma_r=18.0, phi_r=phi, c_r=0.0, q_s=0.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0,
            gamma_c=24.0, qa=150.0,
        )

    def test_mayor_phi_menor_Ka(self):
        m20 = self._motor_con_phi(20)
        m35 = self._motor_con_phi(35)
        assert m35.res.Ka < m20.res.Ka

    def test_mayor_phi_mayor_FS_vuelco(self):
        m25 = self._motor_con_phi(25)
        m35 = self._motor_con_phi(35)
        assert m35.res.estabilidad.FS_vuelco > m25.res.estabilidad.FS_vuelco

    def test_sobrecarga_aumenta_empuje(self):
        m0 = MuroVoladizo().calcular(
            H=5.0, h_zapata=0.50, b_base=0.40, b_corona=0.30,
            B_punta=0.80, B_talon=2.30,
            gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0,
            gamma_c=24.0, qa=150.0,
        )
        m10 = MuroVoladizo().calcular(
            H=5.0, h_zapata=0.50, b_base=0.40, b_corona=0.30,
            B_punta=0.80, B_talon=2.30,
            gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=10.0,
            gamma_f=18.0, phi_f=30.0, c_f=0.0,
            gamma_c=24.0, qa=150.0,
        )
        assert m10.res.estabilidad.Ea > m0.res.estabilidad.Ea
        assert m10.res.estabilidad.FS_vuelco < m0.res.estabilidad.FS_vuelco


# ─── Test 7: Errores de entrada ────────────────────────────────────────────

class TestValidacionEntrada:
    def test_h_zapata_mayor_que_H(self):
        with pytest.raises(ValueError):
            MuroVoladizo().calcular(
                H=3.0, h_zapata=3.5,
                b_base=0.40, b_corona=0.30,
                B_punta=0.80, B_talon=1.50,
                gamma_r=18.0, phi_r=30.0, c_r=0.0, q_s=0.0,
                gamma_f=18.0, phi_f=30.0, c_f=0.0,
                gamma_c=24.0, qa=150.0,
            )
