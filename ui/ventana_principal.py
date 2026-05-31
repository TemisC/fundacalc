"""
Ventana principal de FundaCalc.
Contiene: barra de menú, barra de herramientas, pestañas de módulos.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QMenuBar, QMenu, QStatusBar, QLabel, QComboBox,
    QHBoxLayout, QToolBar, QPushButton, QFileDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from ui.panel_zapata_aislada import PanelZapataAislada
from datos.gestor_proyectos import GestorProyectos
from config import Config


NORMAS_DISPONIBLES = {
    "ACI 318-19 (Internacional)": "ACI318",
    "CIRSOC 201-2005 (Argentina)": "CIRSOC201",
    "NCh 170 Of.2016 (Chile)": "NCH170",
    "NSR-10 (Colombia)": "NSR10",
    "NTE E.060-2009 (Perú)": "NTE_E060",
    "NTC-CDMX 2017 (México)": "NTC_CDMX",
    "EHE-08 (España)": "EHE08",
}


class VentanaPrincipal(QMainWindow):

    def __init__(self, config: Config | None = None):
        super().__init__()
        self.config = config or Config.cargar()
        self.setWindowTitle("FundaCalc v1.0 — Diseño de Fundaciones")
        self.setMinimumSize(1100, 750)
        self.gestor = GestorProyectos()
        self._norma_actual = self.config.norma_por_defecto

        self._crear_menu()
        self._crear_toolbar()
        self._crear_central()
        self._seleccionar_norma_default()
        self._crear_statusbar()

    def _crear_menu(self):
        menubar = self.menuBar()

        m_archivo = menubar.addMenu("&Archivo")
        a_nuevo = QAction("&Nuevo proyecto", self)
        a_nuevo.setShortcut("Ctrl+N")
        a_nuevo.triggered.connect(self._nuevo_proyecto)

        a_abrir = QAction("&Abrir proyecto...", self)
        a_abrir.setShortcut("Ctrl+O")
        a_abrir.triggered.connect(self._abrir_proyecto)

        a_guardar = QAction("&Guardar proyecto", self)
        a_guardar.setShortcut("Ctrl+S")
        a_guardar.triggered.connect(self._guardar_proyecto)

        a_salir = QAction("&Salir", self)
        a_salir.setShortcut("Ctrl+Q")
        a_salir.triggered.connect(self.close)

        m_archivo.addAction(a_nuevo)
        m_archivo.addAction(a_abrir)
        m_archivo.addAction(a_guardar)
        m_archivo.addSeparator()
        m_archivo.addAction(a_salir)

        m_reportes = menubar.addMenu("&Reportes")
        a_pdf = QAction("Exportar PDF...", self)
        a_pdf.setShortcut("Ctrl+P")
        a_pdf.triggered.connect(self._exportar_pdf)
        m_reportes.addAction(a_pdf)

        a_dxf = QAction("Exportar DXF...", self)
        a_dxf.setShortcut("Ctrl+D")
        a_dxf.triggered.connect(self._exportar_dxf)
        m_reportes.addAction(a_dxf)

        m_ayuda = menubar.addMenu("&Ayuda")
        a_acerca = QAction("Acerca de FundaCalc", self)
        a_acerca.triggered.connect(self._acerca_de)
        m_ayuda.addAction(a_acerca)

    def _crear_toolbar(self):
        toolbar = QToolBar("Herramientas principales")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        lbl_norma = QLabel("  Norma de diseño:  ")
        self.combo_norma = QComboBox()
        self.combo_norma.addItems(list(NORMAS_DISPONIBLES.keys()))
        self.combo_norma.setMinimumWidth(250)
        self.combo_norma.currentIndexChanged.connect(self._cambiar_norma)

        btn_calcular = QPushButton("▶  Calcular")
        btn_calcular.setObjectName("btn_calcular_primary")
        btn_calcular.clicked.connect(self._ejecutar_calculo)

        btn_pdf = QPushButton("📄  Exportar PDF")
        btn_pdf.clicked.connect(self._exportar_pdf)

        btn_dxf = QPushButton("📐  Exportar DXF")
        btn_dxf.clicked.connect(self._exportar_dxf)

        toolbar.addWidget(lbl_norma)
        toolbar.addWidget(self.combo_norma)
        toolbar.addSeparator()
        toolbar.addWidget(btn_calcular)
        toolbar.addWidget(btn_pdf)
        toolbar.addWidget(btn_dxf)

    def _buscar_indice_norma(self, codigo: str) -> int | None:
        for index, texto in enumerate(NORMAS_DISPONIBLES):
            if NORMAS_DISPONIBLES[texto] == codigo:
                return index
        return None

    def _seleccionar_norma_default(self):
        default_index = self._buscar_indice_norma(self._norma_actual)
        if default_index is not None:
            self.combo_norma.setCurrentIndex(default_index)

    def _crear_central(self):
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.panel_zapata_aislada = PanelZapataAislada(
            norma_codigo=self._norma_actual,
            config=self.config,
        )
        self.tabs.addTab(self.panel_zapata_aislada, "🏗  Zapata Aislada")

        tab_combinada = QWidget()
        self.tabs.addTab(tab_combinada, "Zapata Combinada")
        self.tabs.setTabEnabled(1, False)

        tab_corrida = QWidget()
        self.tabs.addTab(tab_corrida, "Zapata Corrida")
        self.tabs.setTabEnabled(2, False)

        tab_losa = QWidget()
        self.tabs.addTab(tab_losa, "Losa de Fundación")
        self.tabs.setTabEnabled(3, False)

        self.setCentralWidget(self.tabs)

    def _crear_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.lbl_status = QLabel("Listo")
        self.statusbar.addWidget(self.lbl_status)

    def _cambiar_norma(self, index):
        texto = self.combo_norma.currentText()
        self._norma_actual = NORMAS_DISPONIBLES[texto]
        self.panel_zapata_aislada.set_norma(self._norma_actual)
        self.lbl_status.setText(f"Norma: {texto}")

    def _ejecutar_calculo(self):
        tab_actual = self.tabs.currentIndex()
        if tab_actual == 0:
            self.panel_zapata_aislada.calcular()
            self.lbl_status.setText("Cálculo completado ✔")

    def _exportar_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar reporte PDF", "", "PDF (*.pdf)"
        )
        if path:
            tab_actual = self.tabs.currentIndex()
            if tab_actual == 0:
                self.panel_zapata_aislada.exportar_pdf(path)
                self.lbl_status.setText(f"PDF exportado: {path}")

    def _exportar_dxf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar archivo DXF", "", "DXF (*.dxf)"
        )
        if path:
            tab_actual = self.tabs.currentIndex()
            if tab_actual == 0:
                self.panel_zapata_aislada.exportar_dxf(path)
                self.lbl_status.setText(f"DXF exportado: {path}")

    def _nuevo_proyecto(self):
        self.panel_zapata_aislada.limpiar()
        self.lbl_status.setText("Nuevo proyecto")

    def _abrir_proyecto(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir proyecto", "datos/proyectos/", "JSON (*.json)"
        )
        if path:
            datos = self.gestor.cargar(path)
            if datos:
                self.panel_zapata_aislada.cargar_datos(datos)
                norma = datos.get("norma")
                if norma:
                    self._norma_actual = norma
                    self.panel_zapata_aislada.set_norma(norma)
                    indice = self._buscar_indice_norma(norma)
                    if indice is not None:
                        self.combo_norma.setCurrentIndex(indice)
                self.lbl_status.setText(f"Proyecto cargado: {path}")

    def _guardar_proyecto(self):
        datos = self.panel_zapata_aislada.obtener_datos()
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar proyecto", "datos/proyectos/", "JSON (*.json)"
        )
        if path:
            self.gestor.guardar(datos, path)
            self.lbl_status.setText(f"Guardado: {path}")

    def _acerca_de(self):
        QMessageBox.about(
            self, "Acerca de FundaCalc",
            "<h3>FundaCalc v1.0</h3>"
            "<p>Aplicación para el diseño estructural de fundaciones.</p>"
            "<p>Módulo 1: Zapata Aislada</p>"
            "<p>Normas: ACI 318, CIRSOC 201, NCh 170, NSR-10, NTE E.060, NTC-CDMX, EHE-08</p>"
        )
