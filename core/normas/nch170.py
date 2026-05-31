"""
NCh 170 Of. 2016 — Chile
Chile adopta ACI 318 con modificaciones menores.
Usa la misma metodología pero con nomenclatura local:
  - fck = resistencia característica (equivalente a f'c)
  - fy  = tensión de fluencia del acero
"""

from core.normas.aci318 import ACI318


class NCh170(ACI318):

    nombre = "NCh 170 Of.2016"
    pais = "Chile"
    year = 2016

    phi_flexion = 0.90
    phi_cortante = 0.75
