"""
EHE-08 — España
Instrucción de Hormigón Estructural.
Usa el sistema europeo (Eurocódigo base):
  - fck en MPa
  - γc = 1.5 (hormigón), γs = 1.15 (acero)
  - fcd = fck / γc,  fyd = fyk / γs
"""

import numpy as np
from core.normas.base import NormaBase


class EHE08(NormaBase):

    nombre = "EHE-08"
    pais = "España"
    year = 2008
    gamma_c = 1.5
    gamma_s = 1.15
    phi_flexion = 1.0 / 1.15
    phi_cortante = 1.0 / 1.5

    @property
    def alpha_cc(self):
        return 0.85

    def fcd(self, fck):
        return self.alpha_cc * fck / self.gamma_c

    def fyd(self, fyk):
        return min(fyk / self.gamma_s, 400.0)

    def resistencia_punzonado(self, fck, b0, d, c1, c2) -> float:
        b0_mm = b0 * 1000
        d_mm = d * 1000
        xi = min(1 + np.sqrt(200 / d_mm), 2.0)
        rho_l = 0.005

        tau_Rd = (0.18 / self.gamma_c) * xi * (100 * rho_l * fck) ** (1/3)
        Vrd = tau_Rd * b0_mm * d_mm
        return Vrd / 1000

    def resistencia_cortante_unidireccional(self, fck, bw, d) -> float:
        bw_mm = bw * 1000
        d_mm = d * 1000
        xi = min(1 + np.sqrt(200 / d_mm), 2.0)
        rho_l = 0.005

        tau_cu = (0.18 / self.gamma_c) * xi * (100 * rho_l * fck) ** (1/3)
        Vcu = tau_cu * bw_mm * d_mm
        return Vcu / 1000

    def area_acero_flexion(self, Mu, d, fck, fy) -> float:
        fcd_val = self.fcd(fck)
        fyd_val = self.fyd(fy)
        d_m = d
        b = 1.0

        mu = Mu / (b * d_m**2 * fcd_val * 1000)
        mu = min(mu, 0.30)

        omega = 1 - np.sqrt(max(1 - 2 * mu, 0))
        As_m2 = omega * b * d_m * fcd_val * 1000 / fyd_val
        return As_m2 * 10000

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        fyd_val = self.fyd(fy)
        rho_min = max(0.0028, 0.0028 * (30 / fck) if fck < 30 else 0.0028)
        bw_mm = bw * 1000
        d_mm = d * 1000
        return rho_min * bw_mm * d_mm / 100

    def longitud_desarrollo(self, db, fck, fy) -> float:
        fctd = 0.21 * fck**(2/3) / self.gamma_c
        fbd = 2.25 * fctd
        db_mm = db * 1000
        fyd_val = self.fyd(fy)
        lb_mm = (fyd_val / (4 * fbd)) * db_mm
        return max(lb_mm, 300) / 1000

    def combinaciones_carga(self) -> dict:
        return {
            "fundamental": {"G": 1.35, "Q": 1.5},
            "accidental": {"G": 1.0, "Q": 1.0, "A": 1.0},
        }
