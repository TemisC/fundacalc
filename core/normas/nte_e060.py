"""
NTE E.060-2009 — Perú
Norma Técnica de Edificación — Concreto Armado.
Basada en ACI 318-99.
"""

from core.normas.aci318 import ACI318


class NTE_E060(ACI318):

    nombre = "NTE E.060-2009"
    pais = "Perú"
    year = 2009
    phi_flexion = 0.90
    phi_cortante = 0.85
