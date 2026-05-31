"""
FundaCalc — Punto de entrada principal.
Inicializa la aplicación PyQt6.
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.ventana_principal import VentanaPrincipal
from config import Config


def main():
    config = Config.cargar()
    app = QApplication(sys.argv)
    app.setApplicationName("FundaCalc")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FundaCalc Dev")

    # Cargar hoja de estilos global
    try:
        with open("ui/estilos.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    ventana = VentanaPrincipal(config=config)
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
