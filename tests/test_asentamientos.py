"""
Benchmark tests — Módulo 8B: Asentamientos.

SCHMERTMANN (1978) — caso de referencia:
  Zapata cuadrada B=L=2m, Df=1m
  q_total=120 kPa, γ=18 kN/m³, t=5 años
  Capa única: N60=20, tipo='arena', espesor=6m

  σv0 = 18×1 = 18 kPa  →  q_net = 102 kPa
  C1 = 1 - 0.5×(18/102) = 0.9118
  C2 = 1 + 0.2×log10(5/0.1) = 1.3398
  z_peak = B/2 = 1m  (zapata cuadrada)
  z_max  = 2B   = 4m
  Iz_peak = 0.5 + 0.1×√(102/36) = 0.6683
  Iz(z_mid=3m) = 0.6683×(4-3)/(4-1) = 0.2228  (post-pico)
  Es = 500×(20+15) = 17500 kPa
  δ = C1×C2×q_net×(Iz×h_eff/Es)×1000 ≈ 6.34 mm

TERZAGHI — arcilla NC:
  B=L=2m, q_net=100 kPa, z_mid=3m, H_c=6m
  Cc=0.35, e0=0.90, OCR=1.0, σ'0=60 kPa, Cs=0.07
  Cv=2.0 m²/año, doble drenaje
  Δσ = 100×4/25 = 16 kPa  (método 2:1)
  δ_c = Cc/(1+e0)×H_c×log10(76/60) = 0.35/1.9×6×0.1028 ≈ 113.6 mm
  t50 = (π/4×0.25) × 9 / 2 = 0.884 años
  t90 = 0.848 × 9 / 2 = 3.82 años
"""
import math
import pytest
from core.asentamientos import AsentamientoSchmertmann, AsentamientoTerzaghi

TOL = 0.02   # 2%


# ─── SCHMERTMANN ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def motor_sch():
    return AsentamientoSchmertmann().calcular(
        B=2.0, L=2.0, Df=1.0,
        q_total=120.0, gamma=18.0, t=5.0,
        capas_inp=[{'espesor': 6.0, 'N60': 20, 'tipo': 'arena'}],
    )


class TestSchmertmannFactores:
    """C1, C2 y diagrama Iz."""

    def test_q_net(self, motor_sch):
        assert motor_sch.res.q_net == pytest.approx(102.0, rel=1e-4)

    def test_C1(self, motor_sch):
        # C1 = 1 - 0.5×(18/102)
        expected = 1.0 - 0.5 * 18 / 102
        assert motor_sch.res.C1 == pytest.approx(expected, rel=1e-4)

    def test_C2(self, motor_sch):
        # C2 = 1 + 0.2×log10(50)
        expected = 1.0 + 0.2 * math.log10(50.0)
        assert motor_sch.res.C2 == pytest.approx(expected, rel=1e-4)

    def test_z_peak_cuadrada(self, motor_sch):
        # z_peak = B/2 = 1.0m para zapata cuadrada
        assert motor_sch.res.z_peak == pytest.approx(1.0, rel=1e-4)

    def test_z_max_cuadrada(self, motor_sch):
        # z_max = 2B = 4.0m para zapata cuadrada
        assert motor_sch.res.z_max == pytest.approx(4.0, rel=1e-4)

    def test_Iz_peak(self, motor_sch):
        # σvp = 18×(1+1) = 36 kPa
        # Iz_peak = 0.5 + 0.1×√(102/36)
        sigma_vp = 18.0 * (1.0 + 1.0)
        expected = 0.5 + 0.1 * math.sqrt(102.0 / sigma_vp)
        assert motor_sch.res.Iz_peak == pytest.approx(expected, rel=1e-4)


class TestSchmertmannEs:
    """Es = f(N60, tipo) — Das/Schmertmann."""

    def test_Es_arena(self, motor_sch):
        # Es = 500×(N60+15) = 500×35 = 17500 kPa
        capa = motor_sch.res.capas[0]
        assert capa.Es == pytest.approx(17500.0, rel=1e-6)

    def test_Es_arcilla_arenosa(self):
        m = AsentamientoSchmertmann().calcular(
            B=2.0, L=2.0, Df=1.0,
            q_total=100.0, gamma=18.0, t=1.0,
            capas_inp=[{'espesor': 5.0, 'N60': 10, 'tipo': 'arcilla_arenosa'}],
        )
        # Es = 300×(10+6) = 4800 kPa
        assert m.res.capas[0].Es == pytest.approx(4800.0, rel=1e-6)


class TestSchmertmannAsentamiento:
    """Asentamiento final δ_i."""

    def test_delta_i_caso_base(self, motor_sch):
        # Calculado a mano: ≈ 6.34 mm (con una sola capa, z_mid=3m)
        assert motor_sch.res.delta_i == pytest.approx(6.34, rel=0.05)

    def test_mayor_carga_mayor_delta(self):
        m_baja  = AsentamientoSchmertmann().calcular(
            B=2.0, L=2.0, Df=1.0, q_total=100.0, gamma=18.0, t=1.0,
            capas_inp=[{'espesor': 5.0, 'N60': 15, 'tipo': 'arena'}])
        m_alta  = AsentamientoSchmertmann().calcular(
            B=2.0, L=2.0, Df=1.0, q_total=200.0, gamma=18.0, t=1.0,
            capas_inp=[{'espesor': 5.0, 'N60': 15, 'tipo': 'arena'}])
        assert m_alta.res.delta_i > m_baja.res.delta_i

    def test_mayor_N60_menor_delta(self):
        m_suelto  = AsentamientoSchmertmann().calcular(
            B=2.0, L=2.0, Df=1.0, q_total=120.0, gamma=18.0, t=1.0,
            capas_inp=[{'espesor': 5.0, 'N60': 5, 'tipo': 'arena'}])
        m_denso   = AsentamientoSchmertmann().calcular(
            B=2.0, L=2.0, Df=1.0, q_total=120.0, gamma=18.0, t=1.0,
            capas_inp=[{'espesor': 5.0, 'N60': 30, 'tipo': 'arena'}])
        assert m_denso.res.delta_i < m_suelto.res.delta_i


# ─── TERZAGHI ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def motor_terz():
    return AsentamientoTerzaghi().calcular(
        B=2.0, L=2.0, q_net=100.0,
        z_mid=3.0, H_c=6.0,
        Cc=0.35, e0=0.90, OCR=1.0,
        sigma0=60.0, Cs=0.07,
        Cv=2.0, doble_dren=True,
    )


class TestTerzaghiAsentamiento:
    """Asentamiento de consolidación primaria — NC."""

    def test_incremento_tension_2_1(self, motor_terz):
        # Δσ = q_net×B×L / ((B+z)(L+z)) = 100×4/25 = 16 kPa
        assert motor_terz.res.delta_sig == pytest.approx(16.0, rel=1e-4)

    def test_caso_NC(self, motor_terz):
        assert motor_terz.res.es_NC is True

    def test_delta_c_NC(self, motor_terz):
        # δ_c = Cc/(1+e0)×H_c×log10(76/60)
        coef = 0.35 / (1 + 0.90) * 6.0
        expected_m = coef * math.log10(76.0 / 60.0)
        expected_mm = expected_m * 1000
        assert motor_terz.res.delta_c == pytest.approx(expected_mm, rel=TOL)

    def test_H_dr_doble(self, motor_terz):
        # H_dr = H_c/2 = 3m para drenaje doble
        assert motor_terz.res.H_dr == pytest.approx(3.0, rel=1e-6)


class TestTerzaghiTiempos:
    """
    t50 y t90 — verificación con fórmula correcta.

    NOTA: Si estos tests fallan con el código original, indica que
    las funciones Tv_de_U / U_de_Tv tienen un error de implementación.
    Ver corrección aplicada en core/asentamientos.py.

    Fórmulas de referencia (Das, 9ª ed.):
      U ≤ 60%: Tv = π/4 · U²
      U > 60%: Tv = 1.781 - 0.933·log10(100·(1−U))
                  = -0.085 - 0.933·log10(1−U_frac)
    """

    def test_t50_formula(self, motor_terz):
        # Tv(50%) = π/4 × 0.25 = 0.1963
        Tv50 = math.pi / 4 * 0.50 ** 2
        expected_t50 = Tv50 * 3.0 ** 2 / 2.0   # H_dr=3, Cv=2
        assert motor_terz.res.t50 == pytest.approx(expected_t50, rel=1e-4)

    def test_t90_formula(self, motor_terz):
        # Tv(90%) = -0.085 - 0.933×log10(0.1) = -0.085 + 0.933 = 0.848
        Tv90 = -0.085 - 0.933 * math.log10(0.10)
        expected_t90 = Tv90 * 3.0 ** 2 / 2.0   # H_dr=3, Cv=2
        assert motor_terz.res.t90 == pytest.approx(expected_t90, rel=0.005)

    def test_t90_mayor_que_t50(self, motor_terz):
        assert motor_terz.res.t90 > motor_terz.res.t50

    def test_curva_monotona_creciente(self, motor_terz):
        curva = motor_terz.res.curva
        deltas = [p.delta for p in curva]
        assert all(deltas[i] <= deltas[i + 1] for i in range(len(deltas) - 1))

    def test_curva_U_de_Tv_correcta(self, motor_terz):
        """
        En Tv ≈ 0.197 (U debería ser ≈ 50%).
        Si falla: U_de_Tv tiene error — debe usar (1+b)^(1/5.6), no (1+b^0.179)^(1/0.358).
        """
        Tv_50 = math.pi / 4 * 0.50 ** 2   # 0.1963
        # Buscar el punto de la curva más cercano a Tv_50
        curva = motor_terz.res.curva
        punto = min(curva, key=lambda p: abs(p.Tv - Tv_50))
        assert punto.U == pytest.approx(50.0, abs=5.0)   # ±5% tolerancia


# ─── OC: sobreconsolidado puro ─────────────────────────────────────────────

class TestTerzaghiOC:
    """Arcilla OC pura: σ'f ≤ σ'p → usa Cs únicamente."""

    def test_OC_puro_usa_solo_Cs(self):
        m = AsentamientoTerzaghi().calcular(
            B=2.0, L=2.0, q_net=20.0,
            z_mid=3.0, H_c=4.0,
            Cc=0.40, e0=1.0, OCR=3.0,
            sigma0=80.0, Cs=0.08,
            Cv=1.5, doble_dren=True,
        )
        # σ'p = 3×80 = 240 kPa; σ'f = 80 + Δσ(pequeño) < 240 → OC puro
        assert m.res.es_NC is False
        assert m.res.delta_c1 > 0.0
        assert m.res.delta_c2 == pytest.approx(0.0, abs=1e-9)

    def test_OC_que_cruza_sigma_p(self):
        """σ'f supera σ'p → tramo OC (Cs) + tramo NC (Cc)."""
        m = AsentamientoTerzaghi().calcular(
            B=4.0, L=4.0, q_net=150.0,
            z_mid=2.0, H_c=4.0,
            Cc=0.40, e0=1.0, OCR=1.5,
            sigma0=80.0, Cs=0.08,
            Cv=1.5, doble_dren=True,
        )
        assert m.res.es_NC is False
        assert m.res.delta_c1 > 0.0
        assert m.res.delta_c2 > 0.0
