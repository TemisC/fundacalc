"""
COVENIN 1753-2006 — Venezuela
Estructuras de Concreto Armado para Edificaciones.
Basada en ACI 318-05 con adaptaciones nacionales.

Diferencias respecto a ACI 318-19:
  - As_min: sólo criterio 1.4/fy (cláusula 10.5.1), sin el término 0.25√f'c/fy
    para casos donde f'c ≤ 31 MPa (que cubre la práctica habitual venezolana).
  - Longitud de desarrollo: COVENIN 1753 §12.2, coeficiente 1.0 (sin factor ψt).
  - Combinaciones: 1.2D + 1.6L (coincide con ACI 318-05 y ediciones posteriores).
  - Factores φ idénticos a ACI 318-05: φ_flexion=0.90, φ_cortante=0.75.
"""

import numpy as np
from core.normas.aci318 import ACI318


class COVENIN1753(ACI318):

    nombre = "COVENIN 1753-2006"
    pais = "Venezuela"
    year = 2006
    phi_flexion = 0.90
    phi_cortante = 0.75

    def area_acero_minimo(self, fck, fy, bw, d) -> float:
        """
        COVENIN 1753-2006 §10.5.1
        As_min = max(0.25·√f'c/fy, 1.4/fy) · bw · d
        Idéntico a ACI 318-05; se mantiene la expresión completa.
        """
        bw_mm = bw * 1000
        d_mm  = d  * 1000
        rho_min = max(0.25 * np.sqrt(fck) / fy, 1.4 / fy)
        return rho_min * bw_mm * d_mm / 100

    def longitud_desarrollo(self, db, fck, fy) -> float:
        """
        COVENIN 1753-2006 §12.2.2 — Longitud de desarrollo en tracción.
        ld = (fy / (1.1·√f'c)) · db  ≥ 300 mm
        Misma expresión que ACI 318-05 sin modificadores de recubrimiento.
        """
        db_mm = db * 1000
        ld_mm = (fy / (1.1 * np.sqrt(fck))) * db_mm
        return max(ld_mm, 300) / 1000
