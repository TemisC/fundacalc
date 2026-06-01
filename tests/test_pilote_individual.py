"""
Benchmark tests — Módulo 6B: Pilote Individual.

Casos calculados a mano:

CASO A — Arcilla pura (método α, API 1984)
  D=0.40m, L=10.0m, vaciado_in_situ
  Capa única: cu=50 kPa, γ=18 kN/m³
  α = 1.0 - 0.5×(50-25)/(70-25) = 0.7222
  fs = α×cu = 36.11 kPa
  perim = π×0.40 = 1.2566 m
  Qs = 36.11×1.2566×10 = 453.78 kN
  Qp = 9×cu×Ag = 9×50×π/4×0.16 = 56.55 kN
  Qu = 510.33 kN

CASO B — Arena pura (método β, vaciado_in_situ)
  D=0.50m, L=12.0m, vaciado_in_situ, φ=32°
  delta = 0.75×32 = 24°, K=0.70, beta_factor=0.65
  β = 0.70×tan(24°)×0.65 = 0.2026
  σv_mid = 18×6 = 108 kPa
  fs = β×σv = 21.88 kPa
  Qs = 21.88×π×0.50×12 = 412.5 kN
  Nq(32°) = exp(π·tan32°)×tan²(61°) ≈ 23.20
  σv_base = 18×12=216 kPa → cap 200 kPa
  Qp = 23.20×200×π/4×0.25 = 910.5 kN
"""
import math
import pytest
from core.pilote_individual import PiloteIndividual

TOL = 0.01   # 1% — tolerancia general para capacidades


# ─── Caso A: Arcilla pura, α-method ──────────────────────────────────────

@pytest.fixture(scope="module")
def pilote_arcilla():
    return PiloteIndividual().calcular(
        D=0.40, L=10.0, tipo='vaciado_in_situ',
        capas_inp=[{'tipo': 'arcilla', 'espesor': 10.0, 'gamma': 18.0,
                    'cu': 50.0, 'phi': 0.0}],
        Qa_dis=200.0, FS_min=2.5,
        H_lat=0.0, e_lat=0.0,
        tipo_lat='cohesivo', cu_lat=50.0,
    )


class TestAlphaMethod:
    """Método α (API 1984) para arcilla."""

    def test_alpha_calculado(self, pilote_arcilla):
        # α = 1.0 - 0.5*(50-25)/(70-25) = 0.72222
        capa = pilote_arcilla.res.axial.capas[0]
        assert capa.alpha == pytest.approx(0.72222, rel=1e-4)

    def test_friccion_unitaria(self, pilote_arcilla):
        # fs = α × cu = 0.72222 × 50 = 36.111 kPa
        capa = pilote_arcilla.res.axial.capas[0]
        assert capa.fs == pytest.approx(36.111, rel=1e-4)

    def test_Qs_total(self, pilote_arcilla):
        # Qs = 36.111 × π×0.40 × 10 = 453.78 kN
        assert pilote_arcilla.res.axial.Qs_total == pytest.approx(453.78, rel=TOL)

    def test_Qp_arcilla(self, pilote_arcilla):
        # Qp = 9 × cu × Ag = 9×50×(π/4×0.16) = 56.55 kN
        expected_Qp = 9.0 * 50.0 * math.pi / 4 * 0.40 ** 2
        assert pilote_arcilla.res.axial.Qp == pytest.approx(expected_Qp, rel=TOL)

    def test_Qu(self, pilote_arcilla):
        ax = pilote_arcilla.res.axial
        assert ax.Qu == pytest.approx(ax.Qs_total + ax.Qp, rel=1e-6)
        assert ax.Qu == pytest.approx(510.33, rel=TOL)

    def test_Qa_con_FS(self, pilote_arcilla):
        ax = pilote_arcilla.res.axial
        assert ax.Qa == pytest.approx(ax.Qu / 2.5, rel=1e-6)


class TestAlphaBoundaries:
    """Comprobación de los tramos de la función α."""

    def _cu_to_alpha(self, cu):
        m = PiloteIndividual().calcular(
            D=0.40, L=5.0, tipo='vaciado_in_situ',
            capas_inp=[{'tipo': 'arcilla', 'espesor': 5.0,
                        'gamma': 18.0, 'cu': cu, 'phi': 0.0}],
            Qa_dis=100.0,
        )
        return m.res.axial.capas[0].alpha

    def test_alpha_cu_menor_25_es_1(self):
        assert self._cu_to_alpha(20.0) == pytest.approx(1.0, abs=1e-9)

    def test_alpha_cu_igual_25_es_1(self):
        assert self._cu_to_alpha(25.0) == pytest.approx(1.0, abs=1e-9)

    def test_alpha_cu_mayor_70_es_0_5(self):
        assert self._cu_to_alpha(80.0) == pytest.approx(0.5, abs=1e-9)

    def test_alpha_cu_70_es_0_5(self):
        assert self._cu_to_alpha(70.0) == pytest.approx(0.5, abs=1e-9)

    def test_alpha_cu_47_5_es_0_75(self):
        # Punto medio: cu=47.5 → α = 1 - 0.5*(47.5-25)/45 = 1 - 0.25 = 0.75
        assert self._cu_to_alpha(47.5) == pytest.approx(0.75, rel=1e-4)


# ─── Caso B: Arena pura, β-method ─────────────────────────────────────────

@pytest.fixture(scope="module")
def pilote_arena():
    return PiloteIndividual().calcular(
        D=0.50, L=12.0, tipo='vaciado_in_situ',
        capas_inp=[{'tipo': 'arena', 'espesor': 12.0, 'gamma': 18.0,
                    'cu': 0.0, 'phi': 32.0}],
        Qa_dis=500.0, FS_min=2.5,
        H_lat=0.0, e_lat=0.0,
        tipo_lat='granular', phi_lat=32.0, gamma_lat=18.0,
    )


class TestBetaMethod:
    """Método β (K·tan δ) para arena, vaciado_in_situ."""

    def test_beta_calculado(self, pilote_arena):
        # delta=24°, K=0.70, beta_factor=0.65
        # β = 0.70 × tan(24°) × 0.65
        expected_beta = 0.70 * math.tan(math.radians(24.0)) * 0.65
        capa = pilote_arena.res.axial.capas[0]
        assert capa.beta == pytest.approx(expected_beta, rel=1e-4)

    def test_sigma_v_centroide(self, pilote_arena):
        # σv en centroide (z=6m): gamma×h/2 = 18×12/2 = 108 kPa
        capa = pilote_arena.res.axial.capas[0]
        assert capa.sigma_v == pytest.approx(108.0, rel=1e-4)

    def test_friccion_unitaria_arena(self, pilote_arena):
        beta = 0.70 * math.tan(math.radians(24.0)) * 0.65
        expected_fs = beta * 108.0
        capa = pilote_arena.res.axial.capas[0]
        assert capa.fs == pytest.approx(expected_fs, rel=1e-4)

    def test_Qs_arena(self, pilote_arena):
        beta = 0.70 * math.tan(math.radians(24.0)) * 0.65
        expected_Qs = beta * 108.0 * math.pi * 0.50 * 12.0
        assert pilote_arena.res.axial.Qs_total == pytest.approx(expected_Qs, rel=TOL)

    def test_Qp_arena_Nq(self, pilote_arena):
        # Nq(32°) = exp(π·tan32°) × tan²(61°)
        phi = 32.0
        Nq = math.exp(math.pi * math.tan(math.radians(phi))) * \
             math.tan(math.radians(45 + phi / 2)) ** 2
        sigma_v_base_cap = min(18.0 * 12.0, 200.0)   # 200 kPa (cap bored)
        Ag = math.pi / 4 * 0.50 ** 2
        expected_Qp = Nq * sigma_v_base_cap * Ag
        assert pilote_arena.res.axial.Qp == pytest.approx(expected_Qp, rel=TOL)


# ─── Test de sensibilidades físicas ────────────────────────────────────────

class TestSensibilidadPilote:

    def _pilote(self, L, cu=50):
        return PiloteIndividual().calcular(
            D=0.40, L=L, tipo='vaciado_in_situ',
            capas_inp=[{'tipo': 'arcilla', 'espesor': L,
                        'gamma': 18.0, 'cu': cu, 'phi': 0.0}],
            Qa_dis=200.0,
        )

    def test_mayor_longitud_mayor_Qs(self):
        """Más longitud → más superficie de fuste → Qs mayor."""
        assert self._pilote(10).res.axial.Qs_total < self._pilote(15).res.axial.Qs_total

    def test_mayor_cu_mayor_fs(self):
        """Mayor cu → mayor α×cu → fs mayor."""
        capa_30 = self._pilote(10, cu=30).res.axial.capas[0]
        capa_60 = self._pilote(10, cu=60).res.axial.capas[0]
        assert capa_60.fs > capa_30.fs

    def test_Qu_mayor_que_Qs(self):
        """Qu = Qs + Qp > Qs siempre (Qp > 0)."""
        ax = self._pilote(10).res.axial
        assert ax.Qu > ax.Qs_total
        assert ax.Qp > 0.0
