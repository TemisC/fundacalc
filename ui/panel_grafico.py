"""
Visualización gráfica de la zapata usando Matplotlib embebido en PyQt6.
Muestra: planta de la zapata, columna centrada, cotas, perímetro de punzonado.
"""

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from core.zapata_aislada import GeometriaZapata, Columna, ResultadosZapata


class PanelGrafico(QWidget):

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(280)
        self.figura = Figure(figsize=(8, 3.5), dpi=90)
        self.canvas = FigureCanvas(self.figura)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def dibujar(self, geo: GeometriaZapata, col: Columna, res: ResultadosZapata):
        self.figura.clear()

        ax1 = self.figura.add_subplot(1, 2, 1)
        ax2 = self.figura.add_subplot(1, 2, 2)

        self._dibujar_planta(ax1, geo, col, res)
        self._dibujar_seccion(ax2, geo, col, res)

        self.figura.tight_layout(pad=1.5)
        self.canvas.draw()

    def _dibujar_planta(self, ax, geo, col, res):
        B, L = geo.B, geo.L
        c1, c2 = col.ancho, col.largo
        d = geo.d

        zapata = mpatches.Rectangle(
            (-B/2, -L/2), B, L,
            linewidth=2, edgecolor='#1565C0', facecolor='#BBDEFB', alpha=0.5
        )
        ax.add_patch(zapata)

        columna = mpatches.Rectangle(
            (-c1/2, -c2/2), c1, c2,
            linewidth=2, edgecolor='#37474F', facecolor='#90A4AE'
        )
        ax.add_patch(columna)

        B_punz = c1 + d
        L_punz = c2 + d
        punzonado = mpatches.Rectangle(
            (-B_punz/2, -L_punz/2), B_punz, L_punz,
            linewidth=1.5, edgecolor='#C62828', facecolor='none',
            linestyle='--', label=f"Perímetro punzonado\n(a d/2={d*100:.0f}cm)"
        )
        ax.add_patch(punzonado)

        ax.annotate('', xy=(B/2, -L/2 - 0.15), xytext=(-B/2, -L/2 - 0.15),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.5))
        ax.text(0, -L/2 - 0.25, f"B = {B:.2f} m", ha='center', fontsize=8, color='#1565C0')

        ax.annotate('', xy=(B/2 + 0.15, L/2), xytext=(B/2 + 0.15, -L/2),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.5))
        ax.text(B/2 + 0.30, 0, f"L = {L:.2f} m", ha='center', fontsize=8,
                color='#1565C0', rotation=90, va='center')

        ax.set_xlim(-B/2 - 0.5, B/2 + 0.6)
        ax.set_ylim(-L/2 - 0.45, L/2 + 0.3)
        ax.set_aspect('equal')
        ax.set_title("Vista en Planta", fontweight='bold', fontsize=10)
        ax.legend(loc='upper left', fontsize=7)
        ax.axis('off')

    def _dibujar_seccion(self, ax, geo, col, res):
        B, h = geo.B, geo.h
        recub = geo.recubrimiento
        d = geo.d
        c1 = col.ancho

        zapata = mpatches.Rectangle(
            (-B/2, 0), B, h,
            linewidth=2, edgecolor='#1565C0', facecolor='#BBDEFB', alpha=0.5
        )
        ax.add_patch(zapata)

        col_rect = mpatches.Rectangle(
            (-c1/2, h), c1, 0.40,
            linewidth=2, edgecolor='#37474F', facecolor='#90A4AE'
        )
        ax.add_patch(col_rect)

        y_arm = recub + 0.008
        ax.axhline(y=y_arm, xmin=0.05, xmax=0.95, color='#C62828', linewidth=2,
                   label=f"Armadura ({res.varilla_x} @ {res.separacion_x*100:.0f}cm)")

        ax.annotate('', xy=(B/2 + 0.10, h), xytext=(B/2 + 0.10, 0),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.5))
        ax.text(B/2 + 0.25, h/2, f"h = {h:.2f} m", ha='left', fontsize=8,
                color='#1565C0', va='center')

        ax.annotate('', xy=(-B/2 - 0.10, y_arm), xytext=(-B/2 - 0.10, 0),
                    arrowprops=dict(arrowstyle='<->', color='#C62828', lw=1.0))
        ax.text(-B/2 - 0.35, y_arm/2, f"r={recub*100:.0f}cm", ha='center',
                fontsize=7, color='#C62828', va='center')

        ax.set_xlim(-B/2 - 0.5, B/2 + 0.5)
        ax.set_ylim(-0.2, h + 0.7)
        ax.set_aspect('equal')
        ax.set_title("Sección Transversal", fontweight='bold', fontsize=10)
        ax.legend(loc='upper right', fontsize=7)
        ax.axis('off')
