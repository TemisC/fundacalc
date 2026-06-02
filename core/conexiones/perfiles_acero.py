"""
ESCALC — Base de datos de perfiles de acero.
Perfiles W (wide flange) — AISC Steel Construction Manual 16th Ed., Tabla 1-1.
Unidades: mm, mm², mm³, mm⁴.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PerfilW:
    nombre: str
    d:   float   # Altura total [mm]
    bf:  float   # Ancho del ala [mm]
    tf:  float   # Espesor del ala [mm]
    tw:  float   # Espesor del alma [mm]
    A:   float   # Área de la sección [mm²]
    Ix:  float   # Momento de inercia eje X [mm⁴]
    Sx:  float   # Módulo elástico eje X [mm³]
    Zx:  float   # Módulo plástico eje X [mm³]
    Iy:  float   # Momento de inercia eje Y [mm⁴]
    ry:  float   # Radio de giro eje Y [mm]
    kdes: float = 0.0  # k diseño (d/2 - distancia al centro del filete) [mm]


# Perfiles W — sistema métrico (denominación × kg/m)
PERFILES_W: dict[str, PerfilW] = {
    # W150
    "W150x24":  PerfilW("W150x24",  d=160, bf=102, tf=10.3, tw=6.6,  A=3060,  Ix=1.33e7, Sx=1.66e5, Zx=1.90e5, Iy=5.10e6, ry=40.9),
    "W150x37":  PerfilW("W150x37",  d=162, bf=154, tf=11.6, tw=8.1,  A=4740,  Ix=2.22e7, Sx=2.74e5, Zx=3.07e5, Iy=7.07e6, ry=38.6),
    # W200
    "W200x46":  PerfilW("W200x46",  d=203, bf=203, tf=11.0, tw=7.2,  A=5890,  Ix=4.52e7, Sx=4.45e5, Zx=5.03e5, Iy=1.55e7, ry=51.3),
    "W200x71":  PerfilW("W200x71",  d=216, bf=206, tf=17.4, tw=10.2, A=9100,  Ix=7.65e7, Sx=7.08e5, Zx=7.98e5, Iy=2.58e7, ry=53.2),
    "W200x100": PerfilW("W200x100", d=210, bf=206, tf=23.7, tw=12.6, A=12700, Ix=6.21e7, Sx=5.91e5, Zx=6.61e5, Iy=2.23e7, ry=42.0),
    # W250
    "W250x49":  PerfilW("W250x49",  d=247, bf=202, tf=11.0, tw=7.4,  A=6260,  Ix=8.70e7, Sx=7.04e5, Zx=7.97e5, Iy=3.97e7, ry=79.5),
    "W250x73":  PerfilW("W250x73",  d=253, bf=254, tf=14.2, tw=8.6,  A=9290,  Ix=1.13e8, Sx=8.93e5, Zx=1.01e6, Iy=3.88e7, ry=64.6),
    "W250x89":  PerfilW("W250x89",  d=260, bf=256, tf=17.3, tw=10.7, A=11400, Ix=1.42e8, Sx=1.09e6, Zx=1.23e6, Iy=4.79e7, ry=64.8),
    # W310
    "W310x60":  PerfilW("W310x60",  d=303, bf=203, tf=13.1, tw=7.5,  A=7580,  Ix=1.45e8, Sx=9.57e5, Zx=1.08e6, Iy=1.84e7, ry=49.3),
    "W310x97":  PerfilW("W310x97",  d=308, bf=305, tf=15.4, tw=9.9,  A=12300, Ix=2.22e8, Sx=1.44e6, Zx=1.64e6, Iy=7.27e7, ry=76.9),
    "W310x143": PerfilW("W310x143", d=323, bf=309, tf=22.9, tw=14.0, A=18200, Ix=3.47e8, Sx=2.15e6, Zx=2.45e6, Iy=1.12e8, ry=78.5),
    # W360
    "W360x64":  PerfilW("W360x64",  d=347, bf=203, tf=13.5, tw=7.7,  A=8130,  Ix=1.78e8, Sx=1.02e6, Zx=1.17e6, Iy=1.87e7, ry=48.0),
    "W360x91":  PerfilW("W360x91",  d=353, bf=254, tf=16.4, tw=9.8,  A=11600, Ix=3.35e8, Sx=1.90e6, Zx=2.14e6, Iy=4.41e7, ry=61.7),
    "W360x110": PerfilW("W360x110", d=360, bf=256, tf=19.9, tw=11.4, A=14100, Ix=4.16e8, Sx=2.31e6, Zx=2.61e6, Iy=5.50e7, ry=62.5),
    "W360x162": PerfilW("W360x162", d=375, bf=374, tf=21.8, tw=13.3, A=20600, Ix=6.15e8, Sx=3.28e6, Zx=3.73e6, Iy=1.76e8, ry=92.5),
    # W410
    "W410x60":  PerfilW("W410x60",  d=407, bf=178, tf=12.8, tw=7.7,  A=7590,  Ix=2.16e8, Sx=1.06e6, Zx=1.20e6, Iy=1.18e7, ry=39.5),
    "W410x85":  PerfilW("W410x85",  d=417, bf=181, tf=18.2, tw=10.9, A=10800, Ix=3.16e8, Sx=1.52e6, Zx=1.74e6, Iy=1.78e7, ry=40.6),
    "W410x100": PerfilW("W410x100", d=415, bf=260, tf=16.9, tw=10.0, A=12700, Ix=3.97e8, Sx=1.91e6, Zx=2.16e6, Iy=3.99e7, ry=56.1),
    # W460
    "W460x74":  PerfilW("W460x74",  d=457, bf=190, tf=14.5, tw=9.0,  A=9480,  Ix=3.33e8, Sx=1.46e6, Zx=1.67e6, Iy=1.71e7, ry=42.5),
    "W460x82":  PerfilW("W460x82",  d=460, bf=191, tf=16.0, tw=9.9,  A=10400, Ix=3.70e8, Sx=1.61e6, Zx=1.83e6, Iy=2.36e7, ry=47.6),
    "W460x113": PerfilW("W460x113", d=463, bf=280, tf=17.3, tw=10.8, A=14400, Ix=5.55e8, Sx=2.40e6, Zx=2.72e6, Iy=6.44e7, ry=66.8),
    # W530
    "W530x66":  PerfilW("W530x66",  d=525, bf=165, tf=11.4, tw=8.9,  A=8390,  Ix=3.51e8, Sx=1.34e6, Zx=1.54e6, Iy=1.04e7, ry=35.2),
    "W530x92":  PerfilW("W530x92",  d=533, bf=209, tf=15.6, tw=10.2, A=11800, Ix=5.54e8, Sx=2.08e6, Zx=2.37e6, Iy=2.39e7, ry=44.9),
    "W530x123": PerfilW("W530x123", d=544, bf=212, tf=21.2, tw=13.1, A=15700, Ix=7.62e8, Sx=2.80e6, Zx=3.19e6, Iy=3.39e7, ry=46.5),
    # W610
    "W610x82":  PerfilW("W610x82",  d=599, bf=178, tf=12.8, tw=10.0, A=10500, Ix=5.62e8, Sx=1.87e6, Zx=2.16e6, Iy=1.45e7, ry=37.1),
    "W610x101": PerfilW("W610x101", d=603, bf=228, tf=14.9, tw=10.5, A=12900, Ix=7.61e8, Sx=2.52e6, Zx=2.88e6, Iy=3.44e7, ry=51.6),
    "W610x155": PerfilW("W610x155", d=611, bf=324, tf=19.0, tw=12.7, A=19700, Ix=1.24e9, Sx=4.06e6, Zx=4.58e6, Iy=1.09e8, ry=74.4),
}


def get_perfil(nombre: str) -> Optional[PerfilW]:
    return PERFILES_W.get(nombre)


def seleccionar_perfil_W_por_Zx(Zx_req_mm3: float) -> Optional[tuple[str, PerfilW]]:
    """Selecciona el perfil W más liviano que cumple Zx_req."""
    candidatos = [(n, p) for n, p in PERFILES_W.items() if p.Zx >= Zx_req_mm3]
    if not candidatos:
        return None
    return min(candidatos, key=lambda x: x[1].A)
