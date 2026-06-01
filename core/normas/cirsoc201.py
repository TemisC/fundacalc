"""
CIRSOC 201-2005 — Argentina
Basado en ACI 318-99 con adaptaciones locales.
Resistencias características usan fck (equivalente a f'c).
"""

from core.normas.aci318 import ACI318


class CIRSOC201(ACI318):
    """
    CIRSOC 201-2005 Argentina.
    Hereda de ACI318 con modificaciones según CIRSOC.
    """

    nombre = "CIRSOC 201-2005"
    pais = "Argentina"
    year = 2005
    phi_flexion = 0.90
    phi_cortante = 0.75
    seccion_as_min = "Art. 10.5.1"

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """
        CIRSOC 201 Art. 10.5 — mismo criterio que ACI.
        Cuantía mínima: ρ_min = 0.0020 para As de temperatura y retracción.
        Para flexión: igual que ACI.
        """
        return super().area_acero_minimo(fck, fy, bw, d)

    def combinaciones_carga(self) -> dict:
        """CIRSOC 103 combinaciones de carga."""
        return {
            "principal": {"D": 1.4, "L": 1.7},
            "con_viento": {"D": 1.05, "L": 1.275, "W": 1.275},
            "con_sismo": {"D": 1.05, "L": 1.275, "E": 1.4},
        }
