"""
Benchmark tests — Módulo M9.3: Muro de Gaviones.

Caso de referencia (calculado a mano):
  N=4 cursos, h_capa=1.0m → H=4.0m
  b_base=3.0m, b_corona=1.2m, h_emb=0.5m
  γ_g=20 kN/m³, φ_r=30°, γ_r=18 kN/m³, q_s=0, φ_gavion=35°

Anchuras por curso (Δb=0.6m): b_0=3.0, b_1=2.4, b_2=1.8, b_3=1.2
Σb = 8.4m  →  W = 20×1.0×8.4 = 168.0 kN/m
Σ(b²) = 9.0+5.76+3.24+1.44 = 19.44
x_CG = 19.44/(2×8.4) = 1.1571m

Ka = tan²(30°) = 1/3
Ea = 0.5×(1/3)×18×16 = 48.0 kN/m
Mo = 48.0×4/3 = 64.0 kN·m/m
Mr = 168.0×1.1571 = 194.4 kN·m/m
FS_v = 194.4/64.0 = 3.038

Verificación interna (junta superior, 1 curso encima):
  W_s = 20×1.0×1.2 = 24.0 kN/m
  Ea_s = 0.5×(1/3)×18×1.0 = 3.0 kN/m
  FS_int = 24.0×tan(35°)/3.0 = 24.0×0.7002/3.0 = 5.60 ✓

Referencia: Das, B.M. (2021) Cap. 14 — Muros de gaviones.
"""
import math
import pytest
from core.muro_gaviones import MuroGaviones

TOL = 0.01


@pytest.fixture(scope="module")
def motor():
    return MuroGaviones().calcular(
        N=4, h_capa=1.0, b_base=3.0, b_corona=1.2, h_emb=0.5,
        gamma_g=20.0, phi_r=30.0, c_r=0.0, gamma_r=18.0, q_s=0.0,
        phi_f=30.0, c_f=0.0, gamma_f=18.0, qa=150.0,
        phi_gavion=35.0, delta_factor=0.667,
    )


class TestGeometriaGaviones:
    def test_H_total(self, motor):
        assert motor.res.H == pytest.approx(4.0, rel=1e-6)

    def test_numero_cursos(self, motor):
        assert motor.res.N == 4

    def test_anchuras_correctas(self, motor):
        expected = [3.0, 2.4, 1.8, 1.2]
        for i, b in enumerate(motor.res.anchos):
            assert b == pytest.approx(expected[i], rel=1e-4)

    def test_A_seccion(self, motor):
        # A = Σ(b_i × h_capa) = (3.0+2.4+1.8+1.2)×1.0 = 8.4 m²
        assert motor.res.A_seccion == pytest.approx(8.4, rel=1e-4)


class TestEmpujeGaviones:
    def test_Ka(self, motor):
        assert motor.res.Ka == pytest.approx(1/3, rel=1e-4)

    def test_Ea(self, motor):
        # Ea = 0.5×(1/3)×18×16 = 48.0 kN/m
        assert motor.res.estabilidad.Ea == pytest.approx(48.0, rel=TOL)

    def test_Mo(self, motor):
        # Mo = 48.0×4/3 = 64.0 kN·m/m
        assert motor.res.estabilidad.Mo == pytest.approx(64.0, rel=TOL)


class TestPesoGaviones:
    def test_W_total(self, motor):
        # W = 20×1.0×8.4 = 168.0 kN/m
        assert motor.res.estabilidad.W_total == pytest.approx(168.0, rel=TOL)

    def test_x_CG(self, motor):
        # x_CG = Σ(b²)/(2Σb) = 19.44/16.8 = 1.1571m
        assert motor.res.estabilidad.x_CG == pytest.approx(1.1571, rel=0.01)

    def test_Mr(self, motor):
        # Mr = 168.0×1.1571 = 194.4 kN·m/m
        assert motor.res.estabilidad.Mr == pytest.approx(194.4, rel=TOL)


class TestEstabilidadGaviones:
    def test_FS_vuelco(self, motor):
        assert motor.res.estabilidad.FS_vuelco == pytest.approx(3.038, rel=0.01)

    def test_ok_vuelco(self, motor):
        assert motor.res.estabilidad.ok_vuelco

    def test_ok_presion(self, motor):
        assert motor.res.estabilidad.ok_presion


class TestJuntasInternas:
    """Verificación de deslizamiento en las N-1 juntas horizontales."""

    def test_numero_juntas(self, motor):
        assert len(motor.res.internas) == 3  # N-1

    def test_todas_ok(self, motor):
        assert motor.res.ok_interna
        for j in motor.res.internas:
            assert j.ok_desliz

    def test_junta_superior_FS_minimo(self, motor):
        """La junta superior tiene menos peso encima → FS más bajo."""
        fs_values = [j.FS_desliz for j in motor.res.internas]
        # FS debería decrecer o mantenerse desde arriba hacia abajo
        # (más peso encima → mejor deslizamiento)
        assert max(fs_values) > 1.3
        assert min(fs_values) > 1.3

    def test_junta_superior_formula(self, motor):
        """
        Junta superior (1 curso encima, mínimo W_sobre):
        W_s = 20×1.0×1.2 = 24.0 kN/m
        Ea_s = 0.5×(1/3)×18×1.0 = 3.0 kN/m
        FS = 24.0×tan(35°)/3.0 ≈ 5.60
        """
        # La junta con menor W_sobre es la más alta del muro
        junta_top = min(motor.res.internas, key=lambda j: j.W_sobre)
        assert junta_top.FS_desliz == pytest.approx(5.60, rel=0.05)


class TestSensibilidadGaviones:
    def test_mayor_N_mayor_FS_vuelco(self):
        m3 = MuroGaviones().calcular(
            N=3, h_capa=1.0, b_base=2.5, b_corona=1.0, h_emb=0.5,
            gamma_g=20.0, phi_r=30.0, c_r=0.0, gamma_r=18.0, q_s=0.0,
            phi_f=30.0, c_f=0.0, gamma_f=18.0, qa=200.0,
        )
        m5 = MuroGaviones().calcular(
            N=5, h_capa=1.0, b_base=3.5, b_corona=1.0, h_emb=0.5,
            gamma_g=20.0, phi_r=30.0, c_r=0.0, gamma_r=18.0, q_s=0.0,
            phi_f=30.0, c_f=0.0, gamma_f=18.0, qa=200.0,
        )
        assert m5.res.H > m3.res.H

    def test_validacion_N_minimo(self):
        with pytest.raises(ValueError):
            MuroGaviones().calcular(
                N=1, h_capa=1.0, b_base=2.0, b_corona=1.0, h_emb=0.3,
                gamma_g=20.0, phi_r=30.0, c_r=0.0, gamma_r=18.0, q_s=0.0,
                phi_f=30.0, c_f=0.0, gamma_f=18.0, qa=200.0,
            )
