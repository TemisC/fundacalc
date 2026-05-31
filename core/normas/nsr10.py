"""
NSR-10 Título C — Colombia
Norma Colombiana de Construcción Sismo-Resistente.
Título C basado en ACI 318-05 con adaptaciones.
"""

from core.normas.aci318 import ACI318


class NSR10(ACI318):

    nombre = "NSR-10 Título C"
    pais = "Colombia"
    year = 2010
    phi_flexion = 0.90
    phi_cortante = 0.75

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """
        NSR-10 C.10.5 — igual que ACI 318 con cuantía mínima.
        """
        return super().area_acero_minimo(fck, fy, bw, d)
