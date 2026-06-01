"""
Benchmark tests — Casos con resultado PUBLICADO en fuentes de acceso libre.

Todos los valores esperados fueron tomados de la fuente indicada y verificados
aritméticamente de forma independiente antes de escribir el test.

═══════════════════════════════════════════════════════════════════════════════
CASO 1 — Asentamiento por Consolidación Primaria (NC)
Fuente: EngineeringHulk.com — Consolidation Settlement
URL:    https://engineeringhulk.com/civil/geotechnical/consolidation/
Texto:  Example 1 (Normally Consolidated Clay)
───────────────────────────────────────────────────────────────────────────────
Datos del ejemplo publicado:
  H_c = 4 m,  e₀ = 0.90,  Cc = 0.35
  σ'₀ = 80 kPa,  Δσ = 60 kPa  (carga directa, sin 2:1)
Resultado publicado:  Sc = 179 mm

Verificación aritmética independiente:
  δ_c = Cc/(1+e₀)·H_c·log10((σ'₀+Δσ)/σ'₀)
      = 0.35/1.90 × 4 × log10(140/80)
      = 0.73684 × 0.24304
      = 0.17899 m  →  179 mm  ✓

═══════════════════════════════════════════════════════════════════════════════
CASO 2 — Asentamiento por Consolidación Primaria (OC que cruza σ'p)
Fuente: EngineeringHulk.com — Consolidation Settlement
URL:    https://engineeringhulk.com/civil/geotechnical/consolidation/
Texto:  Example 2 (Overconsolidated Clay)
───────────────────────────────────────────────────────────────────────────────
Datos del ejemplo publicado:
  H_c = 3 m,  e₀ = 1.10,  Cc = 0.42,  Cs = 0.07
  σ'₀ = 60 kPa,  σ'p = 120 kPa  (OCR=2),  Δσ = 100 kPa
  σ'f = 160 kPa > σ'p → tramo OC + tramo NC
Resultado publicado:  Sc = 105 mm

Verificación aritmética independiente:
  coef = 3/(1+1.10) = 1.42857 m
  δ_c1 = 1.42857 × 0.07 × log10(120/60)  = 0.03010 m   (tramo OC)
  δ_c2 = 1.42857 × 0.42 × log10(160/120) = 0.07496 m   (tramo NC)
  δ_c  = 30.10 + 74.96  =  105.1 mm  ✓

═══════════════════════════════════════════════════════════════════════════════
CASO 3 — Capacidad Axial de Pilote en Arcilla (Método α)
Fuente: PEwise.com — PE Geotech Exam Prep (referencia FHWA NHI-16-009)
URL:    https://pewise.com/blog/pe-geotech-foundations-bearing-capacity-pile
Texto:  Single Pile in Clay — Alpha Method
───────────────────────────────────────────────────────────────────────────────
Datos del ejemplo publicado (convertidos a SI):
  D  = 1.0 ft  = 0.3048 m
  L  = 50 ft   = 15.24 m
  su = 1500 psf = 71.82 kPa   (≥ 70 kPa → α = 0.5 en ACI/API)
  FS = 3  (no se verifica aquí, solo Qu)

Resultado publicado:
  Qs = 118 kip = 524.9 kN   (fs = α·su = 0.5×71.82 = 35.91 kPa)
  Qp = 10.6 kip = 47.1 kN   (qp = 9·su·Ag)
  Qu = 128.6 kip = 571.9 kN

Verificación aritmética independiente:
  perim = π×0.3048 = 0.9576 m
  Qs = 35.91 × 0.9576 × 15.24 = 524.6 kN  ✓
  Ag = π/4 × 0.3048² = 0.07297 m²
  Qp = 9 × 71.82 × 0.07297 = 47.18 kN     ✓
  Qu = 524.6 + 47.18 = 571.8 kN            ✓

═══════════════════════════════════════════════════════════════════════════════
CASO 4 — Asentamiento por Consolidación NC (fuente alternativa)
Fuente: EasyGeo/Civil Engineering Things Undergrads (blogspot)
URL:    http://civilengineeringthingsforundergrads.blogspot.com/2018/10/consolidation-settlement-part-02.html
Texto:  Example — Normally Consolidated Clay
───────────────────────────────────────────────────────────────────────────────
Datos del ejemplo publicado:
  H_c = 5 m,  e₀ = 0.60,  Cc = 0.11
  σ'₀ = 75 kPa,  Δσ = 25 kPa
Resultado publicado:  S = 43 mm

Verificación aritmética independiente:
  δ_c = 0.11/1.60 × 5 × log10(100/75)
      = 0.34375 × 0.12494
      = 0.04295 m  →  42.95 mm ≈ 43 mm  ✓
"""
import math
import pytest
from core.asentamientos import AsentamientoTerzaghi
from core.pilote_individual import PiloteIndividual

TOL_ASEN  = 0.02   # ±2 mm sobre 100+ mm → más que suficiente
TOL_PILOTE = 0.01  # ±1% en capacidades


# ═══════════════════════════════════════════════════════════════
#  CASO 1 — Terzaghi NC  (EngineeringHulk, H=4m, Cc=0.35)
# ═══════════════════════════════════════════════════════════════

class TestTerzaghiNC_EngineeringHulk:
    """
    Fuente: EngineeringHulk.com — Consolidation Settlement, Example 1.
    URL: https://engineeringhulk.com/civil/geotechnical/consolidation/
    Resultado publicado: Sc = 179 mm
    """

    @pytest.fixture(scope="class")
    def res(self):
        # z_mid=0 → Δσ = q_net directamente (sin distribución 2:1)
        return AsentamientoTerzaghi().calcular(
            B=2.0, L=2.0, q_net=60.0,
            z_mid=0.0, H_c=4.0,
            Cc=0.35, e0=0.90, OCR=1.0,
            sigma0=80.0, Cs=0.07,
            Cv=1.0, doble_dren=True,
        ).res

    def test_Sc_publicado_179mm(self, res):
        """Valor publicado: 179 mm — EngineeringHulk.com."""
        assert res.delta_c == pytest.approx(179.0, abs=TOL_ASEN * 179)

    def test_caso_NC(self, res):
        assert res.es_NC is True

    def test_delta_sig(self, res):
        # z_mid=0 → Δσ = q_net = 60 kPa
        assert res.delta_sig == pytest.approx(60.0, rel=1e-4)

    def test_formula_explicita(self):
        """Verificación aritmética directa de la fórmula publicada."""
        Cc, e0, H_c = 0.35, 0.90, 4.0
        sigma0, delta_sig = 80.0, 60.0
        expected_m = Cc / (1 + e0) * H_c * math.log10((sigma0 + delta_sig) / sigma0)
        assert expected_m * 1000 == pytest.approx(179.0, abs=0.5)


# ═══════════════════════════════════════════════════════════════
#  CASO 2 — Terzaghi OC  (EngineeringHulk, cruce σ'p)
# ═══════════════════════════════════════════════════════════════

class TestTerzaghiOC_EngineeringHulk:
    """
    Fuente: EngineeringHulk.com — Consolidation Settlement, Example 2 (OC Clay).
    URL: https://engineeringhulk.com/civil/geotechnical/consolidation/
    Resultado publicado: Sc = 105 mm
    """

    @pytest.fixture(scope="class")
    def res(self):
        return AsentamientoTerzaghi().calcular(
            B=2.0, L=2.0, q_net=100.0,
            z_mid=0.0, H_c=3.0,
            Cc=0.42, e0=1.10, OCR=2.0,
            sigma0=60.0, Cs=0.07,
            Cv=1.0, doble_dren=True,
        ).res

    def test_Sc_publicado_105mm(self, res):
        """Valor publicado: 105 mm — EngineeringHulk.com."""
        assert res.delta_c == pytest.approx(105.0, abs=TOL_ASEN * 105)

    def test_caso_OC_que_cruza(self, res):
        assert res.es_NC is False
        assert res.delta_c1 > 0.0   # tramo OC (Cs)
        assert res.delta_c2 > 0.0   # tramo NC (Cc)

    def test_sigma_p(self, res):
        # OCR=2, sigma0=60 → σ'p = 120 kPa
        assert res.sigma_p == pytest.approx(120.0, rel=1e-6)

    def test_sigma_f(self, res):
        # σ'f = 60+100 = 160 kPa > σ'p → cruza preconsolidación
        assert res.sigma_f > res.sigma_p

    def test_formula_explicita_dc1_dc2(self):
        """Verificación aritmética de ambos tramos."""
        Cc, Cs, e0, H_c = 0.42, 0.07, 1.10, 3.0
        sigma0, sigma_p, sigma_f = 60.0, 120.0, 160.0
        coef = H_c / (1 + e0)
        dc1 = coef * Cs * math.log10(sigma_p / sigma0)   # ≈ 30.1 mm
        dc2 = coef * Cc * math.log10(sigma_f / sigma_p)  # ≈ 75.0 mm
        total = (dc1 + dc2) * 1000
        assert total == pytest.approx(105.0, abs=0.5)


# ═══════════════════════════════════════════════════════════════
#  CASO 3 — Pilote en Arcilla, Método α  (PEwise/FHWA NHI-16-009)
# ═══════════════════════════════════════════════════════════════

class TestPiloteAlpha_PEwiseFHWA:
    """
    Fuente: PEwise.com PE Exam Prep — Single Pile in Clay, Alpha Method.
    URL: https://pewise.com/blog/pe-geotech-foundations-bearing-capacity-pile
    Referencia normativa citada: FHWA NHI-16-009 (Design & Construction of Driven Pile Foundations)
    Resultado publicado: Qs=118 kip, Qp=10.6 kip, Qu=128.6 kip

    Conversión a SI:  1 kip = 4.44822 kN
      Qs = 118 × 4.44822 = 524.9 kN
      Qp = 10.6 × 4.44822 = 47.15 kN
      Qu = 128.6 × 4.44822 = 571.9 kN

    Parámetros en SI:
      D  = 1.0 ft = 0.3048 m
      L  = 50 ft  = 15.24 m
      su = 1500 psf = 71.82 kPa   (cu > 70 kPa → α = 0.5 en FundaCalc)
    """

    @pytest.fixture(scope="class")
    def motor(self):
        su_kpa = 1500 * 0.04788   # psf → kPa = 71.82 kPa
        return PiloteIndividual().calcular(
            D=0.3048, L=15.24, tipo='vaciado_in_situ',
            capas_inp=[{
                'tipo': 'arcilla', 'espesor': 15.24,
                'gamma': 18.85, 'cu': su_kpa, 'phi': 0.0,
            }],
            Qa_dis=200.0, FS_min=2.5,
            H_lat=0.0, e_lat=0.0, tipo_lat='cohesivo', cu_lat=su_kpa,
        )

    def test_alpha_es_0_5(self, motor):
        """cu > 70 kPa → α = 0.5 — límite API/FHWA."""
        capa = motor.res.axial.capas[0]
        assert capa.alpha == pytest.approx(0.5, abs=1e-9)

    def test_Qs_publicado_118kip(self, motor):
        """Qs publicado = 118 kip = 524.9 kN."""
        Qs_kip = motor.res.axial.Qs_total / 4.44822
        assert Qs_kip == pytest.approx(118.0, rel=TOL_PILOTE)

    def test_Qp_publicado_10_6kip(self, motor):
        """Qp publicado = 10.6 kip = 47.15 kN."""
        Qp_kip = motor.res.axial.Qp / 4.44822
        assert Qp_kip == pytest.approx(10.6, rel=0.02)

    def test_Qu_publicado_128_6kip(self, motor):
        """Qu publicado = 128.6 kip = 571.9 kN."""
        Qu_kip = motor.res.axial.Qu / 4.44822
        assert Qu_kip == pytest.approx(128.6, rel=TOL_PILOTE)

    def test_fs_unitaria(self, motor):
        """fs = α·su = 0.5 × 71.82 = 35.91 kPa."""
        capa = motor.res.axial.capas[0]
        su_kpa = 1500 * 0.04788
        assert capa.fs == pytest.approx(0.5 * su_kpa, rel=1e-4)


# ═══════════════════════════════════════════════════════════════
#  CASO 4 — Terzaghi NC  (EasyGeo Blog, H=5m, Cc=0.11)
# ═══════════════════════════════════════════════════════════════

class TestTerzaghiNC_EasyGeo:
    """
    Fuente: Civil Engineering Things for Undergrads (blogspot) — Consolidation Part 02.
    URL: http://civilengineeringthingsforundergrads.blogspot.com/2018/10/consolidation-settlement-part-02.html
    Resultado publicado: S = 43 mm
    """

    @pytest.fixture(scope="class")
    def res(self):
        return AsentamientoTerzaghi().calcular(
            B=2.0, L=2.0, q_net=25.0,
            z_mid=0.0, H_c=5.0,
            Cc=0.11, e0=0.60, OCR=1.0,
            sigma0=75.0, Cs=0.022,
            Cv=1.0, doble_dren=True,
        ).res

    def test_Sc_publicado_43mm(self, res):
        """Valor publicado: 43 mm — EasyGeo blog."""
        assert res.delta_c == pytest.approx(43.0, abs=1.0)

    def test_caso_NC(self, res):
        assert res.es_NC is True

    def test_formula_explicita(self):
        """Verificación aritmética directa — base de todo el test."""
        Cc, e0, H_c = 0.11, 0.60, 5.0
        sigma0, delta_sig = 75.0, 25.0
        expected_mm = Cc / (1 + e0) * H_c * math.log10((sigma0 + delta_sig) / sigma0) * 1000
        assert expected_mm == pytest.approx(43.0, abs=0.5)
