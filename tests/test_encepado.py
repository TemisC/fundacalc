"""
Benchmark tests — Módulo M6A: Encepado de Pilotes.

Caso de referencia:
  Pd=600 kN, Pl=300 kN → Pser=900 kN, Pu=1200 kN
  Qa=200 kN/pilote, modo='auto'
  n_req = ceil(900×1.10/200) = ceil(4.95) = 5 pilotes
  Grid: nx=2, ny=3 (minimiza |nx-ny|=1, producto=6 ≥ 5)
  n_total = 6 pilotes

  D=0.40m, spacing → 3D = 1.20m, vuelo → max(D, 0.50) = 0.50m
  B = 1×1.20 + 2×0.50 = 2.20m  (nx=2 → 1 vano)
  L = 2×1.20 + 2×0.50 = 3.40m  (ny=3 → 2 vanos)

Carga por pilote (servicio, sin momentos):
  P_prom = Pser / n = 900/6 = 150 kN ≤ Qa=200 kN ✓

Factores de carga ACI:
  Pu = 1.2×600 + 1.6×300 = 720+480 = 1200 kN

Referencia: Das, B.M. (2021) Cap. 11 — Encepados.
"""
import math
import pytest
from core.encepado import (
    Encepado, CargaEncepado, ColumnaEncepado, PiloteConfig, GeometriaEncepado,
)
from core.zapata_aislada import MaterialHormigon, MaterialAcero
from core.normas.aci318 import ACI318

TOL = 0.02


@pytest.fixture(scope="module")
def enc():
    motor = Encepado(
        carga   = CargaEncepado(Pd=600.0, Pl=300.0),
        columna = ColumnaEncepado(cx=0.40, cy=0.40),
        pilote  = PiloteConfig(D=0.40, Qa=200.0, modo='auto'),
        geo     = GeometriaEncepado(h=0.70, recubrimiento=0.075),
        hormigon= MaterialHormigon(fck=25.0),
        acero   = MaterialAcero(fy=420.0),
        norma   = ACI318(),
    )
    return motor.calcular()


class TestCargasEncepado:
    """Factores de carga ACI 318."""

    def test_Pser(self):
        c = CargaEncepado(Pd=600.0, Pl=300.0)
        assert c.Pser == pytest.approx(900.0, rel=1e-6)

    def test_Pu(self):
        c = CargaEncepado(Pd=600.0, Pl=300.0)
        assert c.Pu == pytest.approx(1200.0, rel=1e-6)

    def test_Mux_sin_momentos(self):
        c = CargaEncepado(Pd=600.0, Pl=300.0)
        assert c.Mux == pytest.approx(0.0, abs=1e-9)


class TestGrillaPilotes:
    """Auto-dimensionamiento de la grilla."""

    def test_n_pilotes_suficiente(self, enc):
        # n × Qa ≥ 1.1 × Pser
        assert enc.n * 200.0 >= 900.0 * 1.10

    def test_grilla_2x3_o_mayor(self, enc):
        assert enc.nx * enc.ny >= 5

    def test_carga_por_pilote_menor_Qa(self, enc):
        """Carga promedio de servicio ≤ Qa."""
        P_prom = 900.0 / enc.n
        assert P_prom <= 200.0 * 1.01

    def test_grilla_cuadrada_si_cargas_iguales(self):
        """Cargas iguales → grilla lo más cuadrada posible."""
        motor = Encepado(
            carga   = CargaEncepado(Pd=800.0, Pl=400.0),
            columna = ColumnaEncepado(cx=0.40, cy=0.40),
            pilote  = PiloteConfig(D=0.40, Qa=500.0, modo='auto'),
            geo     = GeometriaEncepado(h=0.70),
            hormigon= MaterialHormigon(fck=25.0),
            acero   = MaterialAcero(fy=420.0),
            norma   = ACI318(),
        ).calcular()
        # nx y ny no deben diferir en más de 1
        assert abs(motor.nx - motor.ny) <= 1


class TestGeometriaEncepado:
    def test_B_positivo(self, enc):
        assert enc.B > 0.0

    def test_L_positivo(self, enc):
        assert enc.L > 0.0

    def test_h_respetado(self, enc):
        assert enc.h >= 0.70 - 0.01  # puede haber ajuste por punzonado

    def test_pilotes_numero_correcto(self, enc):
        """El número de posiciones coincide con nx×ny."""
        assert len(enc.pile_positions) == enc.nx * enc.ny


class TestVerificacionesEncepado:
    def test_ok_punzonado_col(self, enc):
        assert enc.ok_punch_col

    def test_ok_cortante_x(self, enc):
        assert enc.ok_cx

    def test_ok_cortante_y(self, enc):
        assert enc.ok_cy

    def test_carga_max_pilote_menor_Qa(self, enc):
        """Carga máxima de servicio por pilote ≤ Qa."""
        assert enc.P_max <= 200.0 * 1.01


class TestArmaduraEncepado:
    def test_As_x_ge_minimo(self, enc):
        assert enc.As_dis_x >= enc.As_min

    def test_As_y_ge_minimo(self, enc):
        assert enc.As_dis_y >= enc.As_min

    def test_n_barras_x_positivo(self, enc):
        assert enc.n_barras_x > 0

    def test_n_barras_y_positivo(self, enc):
        assert enc.n_barras_y > 0


class TestSensibilidadEncepado:
    def _enc(self, Qa):
        return Encepado(
            carga   = CargaEncepado(Pd=600.0, Pl=300.0),
            columna = ColumnaEncepado(cx=0.40, cy=0.40),
            pilote  = PiloteConfig(D=0.40, Qa=Qa, modo='auto'),
            geo     = GeometriaEncepado(h=0.70),
            hormigon= MaterialHormigon(fck=25.0),
            acero   = MaterialAcero(fy=420.0),
            norma   = ACI318(),
        ).calcular()

    def test_menor_Qa_mas_pilotes(self):
        """Qa menor → más pilotes necesarios."""
        enc_alto = self._enc(Qa=400.0)
        enc_bajo = self._enc(Qa=200.0)
        assert enc_bajo.n >= enc_alto.n
