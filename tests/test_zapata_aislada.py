"""
Pruebas unitarias del motor de cálculo.
Ejecutar con: python -m pytest tests/ -v
"""

import pytest
from core.zapata_aislada import (
    ZapataAislada, CargasColumna, Columna, Suelo,
    MaterialHormigon, MaterialAcero, GeometriaZapata
)
from core.normas.aci318 import ACI318
from core.normas.cirsoc201 import CIRSOC201
from core.normas.ehe08 import EHE08


@pytest.fixture
def caso_base():
    return {
        "cargas": CargasColumna(Pd=500, Pl=300),
        "columna": Columna(ancho=0.30, largo=0.30),
        "suelo": Suelo(qa=150, Df=1.20, gamma_suelo=18.0),
        "hormigon": MaterialHormigon(fck=25.0),
        "acero": MaterialAcero(fy=420.0),
        "geometria": GeometriaZapata(h=0.50, cuadrada=True),
    }


class TestDimensionamiento:

    def test_area_requerida_positiva(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.area_requerida > 0

    def test_zapata_cuadrada(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert abs(res.B_requerido - res.L_requerido) < 0.01

    def test_presion_no_supera_admisible(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.q_max <= caso_base["suelo"].qa * 1.05


class TestVerificaciones:

    def test_punzonado_ok(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.ok_punzonado

    def test_cortante_ok(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.ok_cortante


class TestNormas:

    def test_aci_vs_cirsoc_resultados_similares(self, caso_base):
        res_aci = ZapataAislada(**caso_base, norma=ACI318()).calcular()
        res_cirsoc = ZapataAislada(**caso_base, norma=CIRSOC201()).calcular()
        ratio = res_aci.area_requerida / res_cirsoc.area_requerida
        assert 0.70 <= ratio <= 1.30

    def test_ehe08_calcula_sin_error(self, caso_base):
        motor = ZapataAislada(**caso_base, norma=EHE08())
        res = motor.calcular()
        assert res.B_requerido > 0


class TestArmadura:

    def test_as_diseno_mayor_que_minimo(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert res.As_x_diseno >= res.As_x_minimo
        assert res.As_y_diseno >= res.As_y_minimo

    def test_separacion_en_rango(self, caso_base):
        norma = ACI318()
        motor = ZapataAislada(**caso_base, norma=norma)
        res = motor.calcular()
        assert 0.10 <= res.separacion_x <= 0.35
        assert 0.10 <= res.separacion_y <= 0.35
