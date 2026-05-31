"""
NTC-CDMX 2017 — México (Ciudad de México)
Normas Técnicas Complementarias para Diseño y Construcción de Estructuras de Concreto.
México tiene un sistema distinto: usa f'c en kg/cm² y fy en kg/cm².
Esta implementación convierte internamente a MPa para mantener la interfaz unificada.
"""

import numpy as np
from core.normas.base import NormaBase


class NTC_CDMX(NormaBase):

    nombre = "NTC-CDMX 2017"
    pais = "México"
    year = 2017
    phi_flexion = 0.90
    phi_cortante = 0.80

    def resistencia_punzonado(self, fck, b0, d, c1, c2) -> float:
        """
        NTC-CDMX §6.5 — Resistencia al punzonamiento.
        vcu = 0.5 · (fck)^0.5  [MPa]  → mismo orden que ACI
        """
        b0_mm = b0 * 1000
        d_mm = d * 1000
        vcu = 0.5 * np.sqrt(fck)
        Vcu = vcu * b0_mm * d_mm
        return self.phi_cortante * Vcu / 1000

    def resistencia_cortante_unidireccional(self, fck, bw, d) -> float:
        """
        NTC-CDMX §6.4 — Cortante en vigas y losas.
        """
        bw_mm = bw * 1000
        d_mm = d * 1000
        Vcu = 0.5 * np.sqrt(fck) * bw_mm * d_mm
        return self.phi_cortante * Vcu / 1000

    def area_acero_flexion(self, Mu, d, fck, fy) -> float:
        """
        NTC-CDMX §7.2 — Diseño por flexión.
        Mismo procedimiento que ACI con factores locales.
        """
        phi = self.phi_flexion
        Mu_Nmm = Mu * 1e6
        d_mm = d * 1000
        Rn = Mu_Nmm / (phi * 1000 * d_mm**2)
        m = fy / (0.85 * fck)
        disc = max(1 - 2 * Rn / (0.85 * fck), 0)
        rho = (1 / m) * (1 - np.sqrt(disc))
        return rho * 1000 * d_mm / 100

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """NTC-CDMX: ρ_min = 0.001 para losas y zapatas."""
        bw_mm = bw * 1000
        d_mm = d * 1000
        rho_min = max(0.25 * np.sqrt(fck) / fy, 0.001)
        return rho_min * bw_mm * d_mm / 100

    def longitud_desarrollo(self, db, fck, fy) -> float:
        """NTC-CDMX §8.4 — Desarrollo de refuerzo."""
        db_mm = db * 1000
        ld_mm = (fy / (1.1 * np.sqrt(fck))) * db_mm
        return max(ld_mm, 300) / 1000
