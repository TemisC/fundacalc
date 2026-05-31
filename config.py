"""
Carga de configuración global para FundaCalc.
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    norma_por_defecto: str = "ACI318"
    idioma: str = "es"
    recubrimiento_por_defecto: float = 0.075
    alturas_por_defecto: list[float] = (0.40, 0.45, 0.50)
    unidad_longitud: str = "m"

    @classmethod
    def cargar(cls, ruta: str = "config.json") -> "Config":
        path = Path(ruta)
        if not path.exists():
            return cls()

        try:
            with path.open("r", encoding="utf-8") as f:
                datos = json.load(f)
        except (json.JSONDecodeError, OSError):
            return cls()

        return cls(
            norma_por_defecto=datos.get("norma_por_defecto", cls.norma_por_defecto),
            idioma=datos.get("idioma", cls.idioma),
            recubrimiento_por_defecto=datos.get("recubrimiento_por_defecto", cls.recubrimiento_por_defecto),
            alturas_por_defecto=tuple(datos.get("alturas_por_defecto", cls.alturas_por_defecto)),
            unidad_longitud=datos.get("unidad_longitud", cls.unidad_longitud),
        )
