"""
Panel de ingreso de datos y visualización de resultados para Zapata Aislada.
Layout: Izquierda = formulario de entrada | Derecha = resultados + gráfico.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox,
    QFormLayout, QLabel, QDoubleSpinBox,
    QCheckBox, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt

from core.zapata_aislada import (
    ZapataAislada, CargasColumna, Columna, Suelo,
    MaterialHormigon, MaterialAcero, GeometriaZapata
)
from core.normas.aci318 import ACI318
from core.normas.cirsoc201 import CIRSOC201
from core.normas.nch170 import NCh170
from core.normas.nsr10 import NSR10
from core.normas.nte_e060 import NTE_E060
from core.normas.ntc_cdmx import NTC_CDMX
from core.normas.ehe08 import EHE08

from ui.panel_resultados import PanelResultados
from ui.panel_grafico import PanelGrafico
from reportes.generador_pdf import GeneradorPDF
from reportes.generador_dxf import GeneradorDXF
from config import Config


NORMAS_MAP = {
    "ACI318": ACI318,
    "CIRSOC201": CIRSOC201,
    "NCH170": NCh170,
    "NSR10": NSR10,
    "NTE_E060": NTE_E060,
    "NTC_CDMX": NTC_CDMX,
    "EHE08": EHE08,
}


def _spinbox(min_val=0.0, max_val=9999.0, decimals=2, valor=0.0, sufijo=""):
    sb = QDoubleSpinBox()
    sb.setRange(min_val, max_val)
    sb.setDecimals(decimals)
    sb.setValue(valor)
    if sufijo:
        sb.setSuffix(f"  {sufijo}")
    return sb


class PanelZapataAislada(QWidget):

    def __init__(self, norma_codigo="ACI318", config: Config | None = None):
        super().__init__()
        self.config = config or Config.cargar()
        self._norma_codigo = norma_codigo
        self._ultimo_resultado = None
        self._ultimo_calculo = None
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(10)

        form_layout.addWidget(self._grupo_cargas())
        form_layout.addWidget(self._grupo_columna())
        form_layout.addWidget(self._grupo_suelo())
        form_layout.addWidget(self._grupo_materiales())
        form_layout.addWidget(self._grupo_geometria())
        form_layout.addStretch()

        scroll.setWidget(form_widget)
        splitter.addWidget(scroll)

        panel_derecho = QWidget()
        layout_der = QVBoxLayout(panel_derecho)
        self.panel_resultados = PanelResultados()
        self.panel_grafico = PanelGrafico()
        layout_der.addWidget(self.panel_grafico, stretch=2)
        layout_der.addWidget(self.panel_resultados, stretch=3)
        splitter.addWidget(panel_derecho)

        splitter.setSizes([400, 700])
        layout.addWidget(splitter)

    def _grupo_cargas(self) -> QGroupBox:
        grp = QGroupBox("Cargas en la columna")
        form = QFormLayout(grp)

        self.sb_Pd = _spinbox(0, 50000, 1, 500.0, "kN")
        self.sb_Pl = _spinbox(0, 50000, 1, 300.0, "kN")
        self.sb_Mxd = _spinbox(0, 5000, 2, 0.0, "kN·m")
        self.sb_Mxl = _spinbox(0, 5000, 2, 0.0, "kN·m")
        self.sb_Myd = _spinbox(0, 5000, 2, 0.0, "kN·m")
        self.sb_Myl = _spinbox(0, 5000, 2, 0.0, "kN·m")

        form.addRow("Carga muerta Pd:", self.sb_Pd)
        form.addRow("Carga viva Pl:", self.sb_Pl)
        form.addRow("Momento muerto Mxd:", self.sb_Mxd)
        form.addRow("Momento vivo Mxl:", self.sb_Mxl)
        form.addRow("Momento muerto Myd:", self.sb_Myd)
        form.addRow("Momento vivo Myl:", self.sb_Myl)
        return grp

    def _grupo_columna(self) -> QGroupBox:
        grp = QGroupBox("Geometría de la columna")
        form = QFormLayout(grp)
        self.sb_col_ancho = _spinbox(0.10, 5.0, 2, 0.30, "m")
        self.sb_col_largo = _spinbox(0.10, 5.0, 2, 0.30, "m")
        form.addRow("Ancho (bx):", self.sb_col_ancho)
        form.addRow("Largo (by):", self.sb_col_largo)
        return grp

    def _grupo_suelo(self) -> QGroupBox:
        grp = QGroupBox("Parámetros del suelo")
        form = QFormLayout(grp)
        self.sb_qa = _spinbox(10, 5000, 1, 150.0, "kN/m²")
        self.sb_Df = _spinbox(0.30, 10.0, 2, 1.20, "m")
        self.sb_gamma_s = _spinbox(10, 30, 1, 18.0, "kN/m³")
        form.addRow("Capacidad admisible qa:", self.sb_qa)
        form.addRow("Profundidad de desplante Df:", self.sb_Df)
        form.addRow("Peso unitario del suelo γ:", self.sb_gamma_s)
        return grp

    def _grupo_materiales(self) -> QGroupBox:
        grp = QGroupBox("Materiales")
        form = QFormLayout(grp)
        self.sb_fck = _spinbox(15, 80, 1, 25.0, "MPa")
        self.sb_fy = _spinbox(200, 600, 1, 420.0, "MPa")
        self.sb_recub = _spinbox(0.03, 0.15, 3, self.config.recubrimiento_por_defecto, "m")
        form.addRow("Resistencia hormigón fck:", self.sb_fck)
        form.addRow("Fluencia acero fy:", self.sb_fy)
        form.addRow("Recubrimiento libre:", self.sb_recub)
        return grp

    def _grupo_geometria(self) -> QGroupBox:
        grp = QGroupBox("Geometría de la zapata (opcional)")
        form = QFormLayout(grp)
        self.cb_cuadrada = QCheckBox("Forzar zapata cuadrada")
        self.cb_cuadrada.setChecked(True)
        self.sb_h = _spinbox(0.20, 3.0, 2, self.config.alturas_por_defecto[0], "m")
        form.addRow("", self.cb_cuadrada)
        form.addRow("Altura inicial h:", self.sb_h)
        return grp

    def set_norma(self, codigo: str):
        self._norma_codigo = codigo

    def calcular(self):
        cargas = CargasColumna(
            Pd=self.sb_Pd.value(),
            Pl=self.sb_Pl.value(),
            Mxd=self.sb_Mxd.value(),
            Mxl=self.sb_Mxl.value(),
            Myd=self.sb_Myd.value(),
            Myl=self.sb_Myl.value(),
        )
        columna = Columna(
            ancho=self.sb_col_ancho.value(),
            largo=self.sb_col_largo.value(),
        )
        suelo = Suelo(
            qa=self.sb_qa.value(),
            Df=self.sb_Df.value(),
            gamma_suelo=self.sb_gamma_s.value(),
        )
        hormigon = MaterialHormigon(fck=self.sb_fck.value())
        acero = MaterialAcero(fy=self.sb_fy.value())
        geometria = GeometriaZapata(
            h=self.sb_h.value(),
            recubrimiento=self.sb_recub.value(),
            cuadrada=self.cb_cuadrada.isChecked(),
        )

        norma_cls = NORMAS_MAP.get(self._norma_codigo, ACI318)
        norma = norma_cls()

        motor = ZapataAislada(cargas, columna, suelo, hormigon, acero, norma, geometria)
        resultado = motor.calcular()

        self._ultimo_resultado = resultado
        self._ultimo_calculo = {
            "cargas": cargas,
            "columna": columna,
            "suelo": suelo,
            "hormigon": hormigon,
            "acero": acero,
            "geometria": motor.geo,
            "norma": norma,
        }

        self.panel_resultados.mostrar(resultado)
        self.panel_grafico.dibujar(motor.geo, columna, resultado)

    def exportar_pdf(self, ruta: str):
        if self._ultimo_resultado and self._ultimo_calculo:
            gen = GeneradorPDF()
            gen.generar(
                ruta=ruta,
                resultado=self._ultimo_resultado,
                datos=self._ultimo_calculo,
            )

    def exportar_dxf(self, ruta: str):
        if self._ultimo_resultado and self._ultimo_calculo:
            gen = GeneradorDXF()
            gen.generar(
                ruta=ruta,
                geo=self._ultimo_calculo["geometria"],
                columna=self._ultimo_calculo["columna"],
                resultado=self._ultimo_resultado,
                norma=self._ultimo_calculo["norma"].__class__.__name__,
            )

    def limpiar(self):
        self.sb_Pd.setValue(500.0)
        self.sb_Pl.setValue(300.0)
        self.sb_fck.setValue(25.0)
        self.sb_fy.setValue(420.0)
        self.sb_recub.setValue(self.config.recubrimiento_por_defecto)
        self.sb_h.setValue(self.config.alturas_por_defecto[0])
        self.cb_cuadrada.setChecked(True)
        self.panel_resultados.limpiar()
        self._ultimo_resultado = None
        self._ultimo_calculo = None

    def obtener_datos(self) -> dict:
        return {
            "Pd": self.sb_Pd.value(),
            "Pl": self.sb_Pl.value(),
            "Mxd": self.sb_Mxd.value(),
            "Mxl": self.sb_Mxl.value(),
            "col_ancho": self.sb_col_ancho.value(),
            "col_largo": self.sb_col_largo.value(),
            "qa": self.sb_qa.value(),
            "Df": self.sb_Df.value(),
            "gamma_s": self.sb_gamma_s.value(),
            "fck": self.sb_fck.value(),
            "fy": self.sb_fy.value(),
            "recubrimiento": self.sb_recub.value(),
            "h": self.sb_h.value(),
            "cuadrada": self.cb_cuadrada.isChecked(),
            "norma": self._norma_codigo,
        }

    def cargar_datos(self, datos: dict):
        self.sb_Pd.setValue(datos.get("Pd", 500))
        self.sb_Pl.setValue(datos.get("Pl", 300))
        self.sb_Mxd.setValue(datos.get("Mxd", 0))
        self.sb_Mxl.setValue(datos.get("Mxl", 0))
        self.sb_col_ancho.setValue(datos.get("col_ancho", 0.30))
        self.sb_col_largo.setValue(datos.get("col_largo", 0.30))
        self.sb_qa.setValue(datos.get("qa", 150))
        self.sb_Df.setValue(datos.get("Df", 1.20))
        self.sb_gamma_s.setValue(datos.get("gamma_s", 18))
        self.sb_fck.setValue(datos.get("fck", 25))
        self.sb_fy.setValue(datos.get("fy", 420))
        self.sb_recub.setValue(datos.get("recubrimiento", 0.075))
        self.sb_h.setValue(datos.get("h", 0.50))
        self.cb_cuadrada.setChecked(datos.get("cuadrada", True))
        norma = datos.get("norma")
        if norma:
            self._norma_codigo = norma
