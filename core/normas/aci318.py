"""
ACI 318-19 — American Concrete Institute
Base para Chile (NCh), Uruguay (UNIT) y Perú (NTE E.060 usa ACI como referencia).
"""

import numpy as np
from core.normas.base import NormaBase


class ACI318(NormaBase):

    nombre = "ACI 318-19"
    pais = "USA / Internacional"
    year = 2019
    phi_flexion = 0.90
    phi_cortante = 0.75

    def resistencia_punzonado(self, fck, b0, d, c1, c2) -> float:
        """
        ACI 318-19 §22.6.5.2
        Vc = mínimo de tres expresiones.
        Unidades: fck en MPa, b0 y d en m → resultado en kN
        """
        beta = max(c1, c2) / min(c1, c2) if min(c1, c2) > 0 else 1.0
        alpha_s = 40.0

        b0_mm = b0 * 1000
        d_mm = d * 1000

        Vc1 = (0.33 * np.sqrt(fck)) * b0_mm * d_mm
        Vc2 = (0.17 * (1 + 2 / beta) * np.sqrt(fck)) * b0_mm * d_mm
        Vc3 = (0.083 * (2 + alpha_s * d_mm / b0_mm) * np.sqrt(fck)) * b0_mm * d_mm

        Vc = min(Vc1, Vc2, Vc3)
        return self.phi_cortante * Vc / 1000

    def resistencia_cortante_unidireccional(self, fck, bw, d) -> float:
        """
        ACI 318-19 §22.5.5.1 (tabla simplificada)
        Vc = 0.17 · √fck · bw · d  (sin refuerzo de cortante)
        """
        bw_mm = bw * 1000
        d_mm = d * 1000
        Vc = 0.17 * np.sqrt(fck) * bw_mm * d_mm
        return self.phi_cortante * Vc / 1000

    def area_acero_flexion(self, Mu, d, fck, fy) -> float:
        """
        Diseño por flexión — método simplificado ACI.
        Mu en kN·m/m, d en m → As en cm²/m
        """
        phi = self.phi_flexion
        Mu_Nmm = Mu * 1e6
        d_mm = d * 1000

        Rn = Mu_Nmm / (phi * 1000 * d_mm**2)

        m = fy / (0.85 * fck)
        discriminante = 1 - 2 * Rn / (0.85 * fck)
        if discriminante < 0:
            discriminante = 0

        rho = (1 / m) * (1 - np.sqrt(discriminante))
        As_mm2 = rho * 1000 * d_mm
        return As_mm2 / 100

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """
        ACI 318-19 §9.6.1.2
        As_min = max(0.25√fck/fy, 1.4/fy) · bw · d
        """
        bw_mm = bw * 1000
        d_mm = d * 1000
        rho_min = max(0.25 * np.sqrt(fck) / fy, 1.4 / fy)
        As_min = rho_min * bw_mm * d_mm
        return As_min / 100

    def longitud_desarrollo(self, db, fck, fy) -> float:
        """
        ACI 318-19 §25.5.2 — Longitud de desarrollo simplificada.
        db en m → ld en m
        """
        db_mm = db * 1000
        ld_mm = (fy / (1.1 * np.sqrt(fck))) * db_mm
        ld_mm = max(ld_mm, 300)
        return ld_mm / 1000
