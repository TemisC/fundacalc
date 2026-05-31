"""
Panel de resultados — muestra tabla de verificaciones y armadura.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QGroupBox, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from core.zapata_aislada import ResultadosZapata


class PanelResultados(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.grp_semaforo = QGroupBox("Estado del diseño")
        self.layout_semaforo = QHBoxLayout(self.grp_semaforo)
        self.lbl_presion = self._crear_indicador("Presión")
        self.lbl_punzonado = self._crear_indicador("Punzonado")
        self.lbl_cortante = self._crear_indicador("Cortante")
        self.lbl_desarrollo = self._crear_indicador("Desarrollo")
        for lbl in [self.lbl_presion, self.lbl_punzonado, self.lbl_cortante, self.lbl_desarrollo]:
            self.layout_semaforo.addWidget(lbl)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Parámetro", "Valor", "Unidad"])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)

        self.grp_mensajes = QGroupBox("Verificaciones")
        self.layout_msg = QVBoxLayout(self.grp_mensajes)

        layout.addWidget(self.grp_semaforo)
        layout.addWidget(self.tabla)
        layout.addWidget(self.grp_mensajes)

    def _crear_indicador(self, texto: str) -> QLabel:
        lbl = QLabel(f"⬤  {texto}\n—")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            "background: #e0e0e0; border-radius: 8px; padding: 8px; font-size: 11px;"
        )
        return lbl

    def _set_indicador(self, lbl: QLabel, texto: str, ok: bool):
        color = "#2e7d32" if ok else "#c62828"
        icono = "✔" if ok else "✘"
        lbl.setText(f"{icono}  {texto}")
        lbl.setStyleSheet(
            f"background: {color}; color: white; border-radius: 8px; "
            f"padding: 8px; font-size: 11px; font-weight: bold;"
        )

    def mostrar(self, res: ResultadosZapata):
        self._set_indicador(self.lbl_presion, "Presión", res.ok_presion)
        self._set_indicador(self.lbl_punzonado, "Punzonado", res.ok_punzonado)
        self._set_indicador(self.lbl_cortante, "Cortante", res.ok_cortante)
        self._set_indicador(self.lbl_desarrollo, "Desarrollo", res.ok_desarrollo)

        filas = [
            ("DIMENSIONES", "", ""),
            ("Largo B", f"{res.B_requerido:.2f}", "m"),
            ("Ancho L", f"{res.L_requerido:.2f}", "m"),
            ("Altura h", f"{res.h_requerido:.2f}", "m"),
            ("Área", f"{res.B_requerido * res.L_requerido:.2f}", "m²"),
            ("PRESIONES", "", ""),
            ("Presión máxima", f"{res.q_max:.1f}", "kN/m²"),
            ("Presión mínima", f"{res.q_min:.1f}", "kN/m²"),
            ("Presión última", f"{res.q_ultima:.1f}", "kN/m²"),
            ("PUNZONADO", "", ""),
            ("Vu punzonado", f"{res.Vu_punz:.1f}", "kN"),
            ("φVn punzonado", f"{res.phi_Vn_punz:.1f}", "kN"),
            ("Relación Vu/φVn", f"{res.relacion_punzonado:.3f}", ""),
            ("CORTANTE", "", ""),
            ("Vu cortante", f"{res.Vu_cort:.1f}", "kN"),
            ("φVn cortante", f"{res.phi_Vn_cort:.1f}", "kN"),
            ("FLEXIÓN — EJE X", "", ""),
            ("Momento último Mu_x", f"{res.Mu_x:.2f}", "kN·m/m"),
            ("As requerido", f"{res.As_x_requerido:.2f}", "cm²/m"),
            ("As diseño", f"{res.As_x_diseno:.2f}", "cm²/m"),
            ("Varilla", res.varilla_x, ""),
            ("Separación", f"{res.separacion_x * 100:.0f}", "cm"),
            ("FLEXIÓN — EJE Y", "", ""),
            ("Momento último Mu_y", f"{res.Mu_y:.2f}", "kN·m/m"),
            ("As requerido", f"{res.As_y_requerido:.2f}", "cm²/m"),
            ("As diseño", f"{res.As_y_diseno:.2f}", "cm²/m"),
            ("Varilla", res.varilla_y, ""),
            ("Separación", f"{res.separacion_y * 100:.0f}", "cm"),
        ]

        self.tabla.setRowCount(len(filas))
        for i, (param, valor, unidad) in enumerate(filas):
            if valor == "" and unidad == "":
                item = QTableWidgetItem(param)
                item.setBackground(QColor("#1565C0"))
                item.setForeground(QColor("white"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                self.tabla.setItem(i, 0, item)
                self.tabla.setSpan(i, 0, 1, 3)
            else:
                self.tabla.setItem(i, 0, QTableWidgetItem(param))
                self.tabla.setItem(i, 1, QTableWidgetItem(valor))
                self.tabla.setItem(i, 2, QTableWidgetItem(unidad))

        self.tabla.resizeColumnsToContents()

        for i in reversed(range(self.layout_msg.count())):
            widget = self.layout_msg.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for msg in res.mensajes:
            lbl = QLabel(msg["texto"])
            color = {"ok": "#2e7d32", "error": "#c62828",
                     "advertencia": "#e65100", "info": "#1565c0"}.get(msg["tipo"], "#000")
            lbl.setStyleSheet(f"color: {color}; padding: 2px 4px;")
            self.layout_msg.addWidget(lbl)

    def limpiar(self):
        self.tabla.setRowCount(0)
        for lbl in [self.lbl_presion, self.lbl_punzonado, self.lbl_cortante, self.lbl_desarrollo]:
            lbl.setText("⬤  —\n—")
            lbl.setStyleSheet(
                "background: #e0e0e0; border-radius: 8px; padding: 8px; font-size: 11px;"
            )
