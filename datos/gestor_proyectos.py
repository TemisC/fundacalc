"""
Guardar y cargar proyectos en formato JSON.
"""

import json
import os
from datetime import datetime


class GestorProyectos:

    def guardar(self, datos: dict, ruta: str) -> bool:
        datos = dict(datos)
        datos["_meta"] = {
            "version": "1.0",
            "fecha": datetime.now().isoformat(),
            "app": "FundaCalc",
        }
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return True

    def cargar(self, ruta: str) -> dict | None:
        if not os.path.exists(ruta):
            return None
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
