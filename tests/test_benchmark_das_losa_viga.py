"""
Benchmark tests — Losa de Fundación · Viga Winkler · Capacidad Portante E3.5
==============================================================================
Fuente: Braja M. Das — "Principios de Ingeniería de Cimentaciones", 5ª Ed.
  Cap. 3 §3.7 — Ejemplo 3.5 (Meyerhof con excentricidad, φ=30°)
  Cap. 5 §5.7 — Viga sobre suelo elástico (Winkler/Hetenyi)

═══════════════════════════════════════════════════════════════════════════════
RESUMEN DE HALLAZGOS:
═══════════════════════════════════════════════════════════════════════════════

EJEMPLO 3.5 (Meyerhof excéntrico, φ=30°):
  Das Q_ult = 988 kN  →  FundaCalc Q_ult = 985.6 kN  →  DIFERENCIA: 0.2% ✓
  A pesar de usar distintas fórmulas de factores de forma, el resultado coincide.
  (Compensación entre sq mayor y sγ menor en FundaCalc vs Das.)

VIGA WINKLER — Factores de rigidez (λ, clasificación):
  Das λ = 0.2014 m⁻¹  →  FundaCalc λ = 0.2001 m⁻¹  →  DIFERENCIA: 0.65% ✓
  Pequeña diferencia por distinta fórmula del módulo elástico:
    Das:       E = 3,000,000 psi = 20,685 MPa  (ACI 318 fórmula americana)
    FundaCalc: E = 4700·√fck MPa               (norma SI, da ~21,385 MPa para fck=20.7 MPa)

VIGA WINKLER — Deflexión y momento:
  Das usa CARGAS DE SERVICIO (Pser). FundaCalc analiza con CARGAS FACTORADAS (Pu).
  Con Pser=500 kN → Pu=680 kN (factor 1.36):
    Das z_max   = 0.615 mm   (Pser=500 kN)
    FundaCalc   = 0.849 mm   (Pu=680 kN)  → 0.615 × 1.36 = 0.836 mm ≈ 0.849 ✓
    Das M_max   = 625 kN·m   (Pser=500 kN)
    FundaCalc   = 846 kN·m   (Pu=680 kN)  → 625 × 1.36 = 850 kN·m ≈ 846 ✓
  Las fórmulas Winkler son CORRECTAS — la diferencia es solo la carga base usada.
═══════════════════════════════════════════════════════════════════════════════
"""
import math
import pytest
from core.capacidad_portante import CapacidadPortante
from core.viga_fundacion import (
    VigaFundacion, CargaColumna, SueloViga, GeometriaViga,
)
from core.zapata_aislada import MaterialHormigon, MaterialAcero
from core.normas.aci318 import ACI318


# ═══════════════════════════════════════════════════════════════
#  DAS EJEMPLO 3.5 — Meyerhof con excentricidad, φ=30°
#  Das Q_ult = 988 kN  →  FundaCalc: 985.6 kN (0.2% diferencia) ✓
# ═══════════════════════════════════════════════════════════════

class TestDasEjemplo35_MeyerhofPhi30:
    """
    Das Cap. 3, Ejemplo 3.5 (pág. 185) — Carga excéntrica en una dirección.

    DATOS:
      B=L=1.5m, e=0.15m → B'=1.20m, L'=1.50m, A'=1.80m²
      Df=0.70m, φ=30°, c=0, γ=18 kN/m³

    RESULTADO DAS: Q_ult = 988 kN

    FundaCalc da Q_ult = 985.6 kN → diferencia 0.2% ✓
    (Los factores de forma difieren en fórmula pero se compensan.)
    """

    @pytest.fixture(scope="class")
    def res(self):
        return CapacidadPortante().calcular(
            phi_deg=30.0, c=0.0, gamma=18.0, Df=0.70,
            B=1.2, L=1.5, forma='rectangular', FS=1.0,
        ).res

    def test_Q_ult_vs_Das(self, res):
        """Das Q_ult = 988 kN. FundaCalc debe coincidir dentro del ±1%."""
        mey = res.metodos[1]  # Meyerhof
        Q_fc = mey.q_ult * 1.2 * 1.5
        assert Q_fc == pytest.approx(988.0, rel=0.01), \
            f"Das=988 kN, FundaCalc={Q_fc:.1f} kN"

    def test_Nq_phi30_coincide_con_Das(self, res):
        """Nq(30°) = 18.40 — Das Tabla 3.4 (Vesic). FundaCalc debe dar igual."""
        mey = res.metodos[1]
        assert mey.Nq == pytest.approx(18.40, rel=0.005)

    def test_Ngamma_phi30_Das_vs_FundaCalc(self, res):
        """
        Das usa Nγ=22.40 (Vesic), FundaCalc usa Nγ=15.67 (Meyerhof 1963).
        El resultado FINAL es casi idéntico porque los demás factores compensan.
        """
        mey = res.metodos[1]
        # FundaCalc Meyerhof Nγ < Das Nγ, pero resultado final Q_ult ≈ mismo
        assert mey.Ngamma == pytest.approx(15.67, rel=0.01)   # Meyerhof 1963
        assert mey.Ngamma < 22.40  # menor que Vesic (Das)

    def test_B_prima_y_area_efectiva(self, res):
        """B'=1.2m, L'=1.5m, A'=1.8m² — el área efectiva es el input directo."""
        mey = res.metodos[1]
        # q_ult × A' = Q_ult → verificar consistencia
        A_prima = 1.2 * 1.5
        assert mey.q_ult * A_prima == pytest.approx(988.0, rel=0.01)


# ═══════════════════════════════════════════════════════════════
#  DAS CAP. 5 §5.7 — VIGA SOBRE SUELO ELÁSTICO (WINKLER)
#  Factor λ y clasificación flexible/rígida
# ═══════════════════════════════════════════════════════════════

class TestDasVigaWinkler_Lambda:
    """
    Das Cap. 5, §5.7 — Factor de rigidez λ y clasificación de la viga.

    DATOS (ejercicio derivado del Ejemplo 5.5/5.6):
      ks = 10,261 kN/m³  (coef. balasto para B=23.17m en arena media)
      B  = 7.93 m  (ancho de franja analizada)
      h  = 0.965 m (espesor losa del Ej. 5.6)
      L  = 29.26 m (longitud franja)
      fck ≈ 20.7 MPa (f'c = 3000 psi)

    RESULTADO DAS: λ = 0.2014 m⁻¹, λ·L = 5.89 > π → viga flexible.
    FundaCalc: λ = 0.2001 m⁻¹ (0.65% diferencia por distinta fórmula de E)
    """

    @pytest.fixture(scope="class")
    def viga(self):
        motor = VigaFundacion(
            columnas=[CargaColumna(x=14.63, Pd=10000, Pl=0, etiqueta="Q_total")],
            suelo=SueloViga(ks=10261.0, qa=200.0),
            geo=GeometriaViga(L=29.26, B=7.93, h=0.965,
                               vuelo_izq=0.0, vuelo_der=0.0),
            hormigon=MaterialHormigon(fck=20.7),
            acero=MaterialAcero(fy=420.0),
            norma=ACI318(),
        )
        return motor.calcular()

    def test_lambda_vs_Das(self, viga):
        """Das λ = 0.2014 m⁻¹. FundaCalc debe dar ≈0.2001 (0.65% diferencia)."""
        assert viga.lambda_char == pytest.approx(0.2014, rel=0.01), \
            f"λ FundaCalc={viga.lambda_char:.4f}, Das=0.2014"

    def test_lambda_L_mayor_pi(self, viga):
        """λ·L = 5.89 > π = 3.14159 → viga flexible — Das §5.7."""
        assert viga.L_char > math.pi, \
            f"λ·L={viga.L_char:.3f} debería ser > π={math.pi:.3f}"

    def test_clasificacion_flexible(self, viga):
        """FundaCalc debe clasificar esta viga como FLEXIBLE."""
        assert viga.flexible is True

    def test_lambda_formula_directa(self):
        """
        λ = (ks·B/(4·EF·IF))^0.25 — Das Ec. (5.43)
        Verificar con parámetros exactos de Das.
        """
        ks  = 10261.0
        B   = 7.93
        EF_das = 20685.0 * 1000   # kN/m² (E = 3000 ksi convertido a SI)
        IF  = B * 0.965**3 / 12   # m⁴
        lam_das = (ks * B / (4 * EF_das * IF))**0.25
        assert lam_das == pytest.approx(0.2014, rel=0.005)

    def test_lambda_EI_FundaCalc_vs_Das(self):
        """
        FundaCalc usa E = 4700·√fck MPa (SI). Das usa E=3000 ksi (imperial).
        Para fck=20.7 MPa: E_fc ≈ 21,385 MPa vs E_das ≈ 20,685 MPa (+3.4%).
        La diferencia en λ resultante es solo ~0.65%.
        """
        fck = 20.7
        E_fc = 4700 * math.sqrt(fck) * 1000   # kN/m²
        E_das = 20685.0 * 1000                  # kN/m²
        # E_fc debe ser ~3% mayor que E_das
        assert E_fc > E_das
        assert abs(E_fc - E_das) / E_das < 0.05   # < 5% diferencia


# ═══════════════════════════════════════════════════════════════
#  DAS CAP. 5 §5.7 — DEFLEXIÓN Y MOMENTO WINKLER
#  Fórmulas: z = Q·λ/(2k') · A(λx),  M = Q/(4λ) · C(λx)
# ═══════════════════════════════════════════════════════════════

class TestDasVigaWinkler_Deflexion:
    """
    Das Cap. 5, Caso de prueba Winkler (viga infinita, carga puntual central).

    DATOS:
      Q_total = 500 kN (carga de servicio)
      λ = 0.20 m⁻¹ (redondeado), k' = 81,370 kN/m²/m

    RESULTADO DAS (cargas de SERVICIO):
      z_max = Q·λ/(2k') = 500×0.20/(2×81370) = 0.615 mm
      M_max = Q/(4λ)    = 500/(4×0.20)        = 625 kN·m

    NOTA IMPORTANTE: FundaCalc usa cargas FACTORADAS (Pu) en el FEM.
    Con Pser=500 kN → Pd=300, Pl=200 → Pu=1.2×300+1.6×200=680 kN.
    Los resultados del FEM reflejan Pu, no Pser.

    VERFICACIÓN: |M_FEM| ≈ Pu/(4λ) = 680/(4×0.2001) ≈ 849 kN·m
    """

    @pytest.fixture(scope="class")
    def viga(self):
        motor = VigaFundacion(
            columnas=[CargaColumna(x=15.0, Pd=300, Pl=200, etiqueta="Q=500kN_svc")],
            suelo=SueloViga(ks=10261.0, qa=200.0),
            geo=GeometriaViga(L=30.0, B=7.93, h=0.965,
                               vuelo_izq=0.0, vuelo_der=0.0),
            hormigon=MaterialHormigon(fck=20.7),
            acero=MaterialAcero(fy=420.0),
            norma=ACI318(),
        )
        return motor.calcular()

    def test_formula_z_analitica_coincide_Das(self):
        """
        Verifica la fórmula z = Q·λ/(2k') directamente (sin FEM).
        Q=500 kN, λ=0.20 m⁻¹, k'=81370 kN/m²/m → z=0.615 mm (Das).
        """
        Q   = 500.0
        lam = 0.20
        kp  = 81370.0
        z = Q * lam / (2 * kp)
        assert z * 1000 == pytest.approx(0.615, rel=0.005)

    def test_formula_M_analitica_coincide_Das(self):
        """
        Verifica M = Q/(4λ) directamente (sin FEM).
        Q=500 kN, λ=0.20 → M=625 kN·m (Das).
        """
        Q   = 500.0
        lam = 0.20
        M = Q / (4 * lam)
        assert M == pytest.approx(625.0, rel=0.005)

    def test_FEM_usa_carga_factorada(self, viga):
        """
        FundaCalc FEM usa Pu=680 kN (no Pser=500 kN).
        El momento FEM ≈ Pu/(4λ) ≈ 849 kN·m (no 625 kN·m).
        Verificar que FEM es internamente consistente con la carga factorada.
        """
        Pu  = 1.2 * 300 + 1.6 * 200   # = 680 kN
        lam = viga.lambda_char
        M_expected_factorado = Pu / (4 * lam)
        # M_max_neg es el momento de diseño (negativo = centro bajo carga puntual)
        assert abs(viga.M_max_neg) == pytest.approx(M_expected_factorado, rel=0.02), \
            f"|M_FEM|={abs(viga.M_max_neg):.1f}, Pu/(4λ)={M_expected_factorado:.1f}"

    def test_FEM_deflexion_consistente_con_carga_factorada(self, viga):
        """
        z_max_FEM ≈ Pu·λ/(2k') (usando carga factorada, no de servicio).
        Verificar consistencia interna del FEM.
        """
        Pu  = 680.0  # kN
        lam = viga.lambda_char
        kp  = 10261.0 * 7.93   # k' = ks × B
        z_expected = Pu * lam / (2 * kp)
        z_FEM = max(viga.y_grid)
        assert z_FEM == pytest.approx(z_expected, rel=0.03), \
            f"z_FEM={z_FEM*1000:.3f} mm, z_analítico(Pu)={z_expected*1000:.3f} mm"

    def test_clasificacion_viga_larga_flexible(self, viga):
        """λ·L > π → viga flexible (Das Ec. 5.43, §5.7)."""
        assert viga.flexible is True
        assert viga.L_char > math.pi

    def test_funciones_auxiliares_Winkler_A_C(self):
        """
        Das Tabla 5.3 — Funciones auxiliares Winkler:
        A(0)=1.000, C(0)=1.000  (bajo la carga)
        A(1.0)=0.508, C(1.0)=−0.111  (a 1/λ de la carga)
        Verificar fórmulas directamente.
        """
        import math

        def A_lx(lx): return math.exp(-lx) * (math.cos(lx) + math.sin(lx))
        def C_lx(lx): return math.exp(-lx) * (math.cos(lx) - math.sin(lx))

        # Das Tabla 5.3
        assert A_lx(0.0) == pytest.approx(1.000, abs=0.001)
        assert C_lx(0.0) == pytest.approx(1.000, abs=0.001)
        assert A_lx(1.0) == pytest.approx(0.508, abs=0.002)
        assert C_lx(1.0) == pytest.approx(-0.111, abs=0.002)
        assert A_lx(2.0) == pytest.approx(0.067, abs=0.002)

    def test_coef_balasto_formula_arena(self):
        """
        Das Ec. (5.45) — k = k₀.₃ × ((B+0.3)/(2B))²  (suelos arenosos).
        Para B=23.17m, k₀.₃=40,000 kN/m³ → k=10,261 kN/m³
        """
        k_0_3 = 40000.0   # kN/m³ (arena media)
        B = 23.17          # m (losa Das E5.5)
        k = k_0_3 * ((B + 0.3) / (2 * B))**2
        assert k == pytest.approx(10261.0, rel=0.01)


# ═══════════════════════════════════════════════════════════════
#  SENSIBILIDADES FÍSICAS — VIGA
# ═══════════════════════════════════════════════════════════════

class TestVigaWinklerSensibilidad:
    """Verificar que la viga se comporta físicamente correcto."""

    def _viga(self, ks, L=20.0, Q_pd=500):
        return VigaFundacion(
            columnas=[CargaColumna(x=L/2, Pd=Q_pd, Pl=0)],
            suelo=SueloViga(ks=ks, qa=500),
            geo=GeometriaViga(L=L, B=2.0, h=0.60),
            hormigon=MaterialHormigon(fck=25.0),
            acero=MaterialAcero(fy=420.0),
            norma=ACI318(),
        ).calcular()

    def test_mayor_ks_menor_deflexion(self):
        """Suelo más rígido → menos deflexión."""
        v_blando = self._viga(ks=5000)
        v_rigido = self._viga(ks=50000)
        assert max(v_rigido.y_grid) < max(v_blando.y_grid)

    def test_mayor_ks_viga_mas_rigida(self):
        """Mayor ks → λ·L más grande → más flexible (o misma clas. para L suficiente)."""
        v_blando = self._viga(ks=5000, L=30)
        v_rigido = self._viga(ks=50000, L=30)
        assert v_rigido.lambda_char > v_blando.lambda_char

    def test_mayor_carga_mayor_deflexion(self):
        """Mayor carga → mayor deflexión."""
        v_light = self._viga(ks=20000, Q_pd=200)
        v_heavy = self._viga(ks=20000, Q_pd=800)
        assert max(v_heavy.y_grid) > max(v_light.y_grid)

    def test_deflexion_maxima_en_columna(self):
        """La deflexión máxima ocurre bajo la columna (x=L/2)."""
        res = self._viga(ks=20000, L=20, Q_pd=500)
        y = res.y_grid
        # El máximo debe estar en el nodo central (índice 50 de 101)
        idx_max = y.index(max(y))
        # Debe estar cerca del centro (±5 nodos de los 101)
        assert abs(idx_max - 50) <= 5
