"""
Módulo 8B — Asentamientos de Fundaciones.

Métodos implementados:
  · Schmertmann (1978)  — asentamiento inmediato en arenas/gravas a partir de SPT
  · Terzaghi (1943)     — asentamiento por consolidación primaria en arcillas

Referencias:
  · Schmertmann, J.H., Hartman, J.P. & Brown, P.R. (1978). Improved strain influence factor diagrams.
  · Terzaghi, K. (1943). Theoretical Soil Mechanics.
  · Das, B.M. (2021). Principles of Foundation Engineering, 9th ed.
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple


# ═══════════════════════════════════════════════════════════════════════════
#  SCHMERTMANN — Asentamiento inmediato
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CapaSchmertmann:
    espesor:   float   # [m]
    N60:       float   # golpes SPT corregidos al 60%
    tipo:      str     # 'arena' | 'arcilla_arenosa'
    Es:        float   # módulo de elasticidad [kPa] (calculado automáticamente)
    z_top:     float   # profundidad inicio de la capa desde NDF [m]
    z_mid:     float   # profundidad centroide [m]
    Iz_mid:    float   # factor de influencia en el centroide [-]
    contrib:   float   # Iz × Δz / Es [m/kPa] aportación a la suma


@dataclass
class ResultadoSchmertmann:
    # Factores
    C1:        float   # corrección por profundidad de empotramiento
    C2:        float   # corrección por fluencia (creep)
    q_net:     float   # incremento neto de carga [kPa]
    Iz_peak:   float   # valor pico del factor de influencia
    z_peak:    float   # profundidad del pico Iz [m]
    z_max:     float   # profundidad máxima de influencia [m]

    capas:     List[CapaSchmertmann]
    suma_Iz_Es: float  # Σ (Iz/Es × Δz) [m/kPa]
    delta_i:   float   # asentamiento inmediato [mm]


class AsentamientoSchmertmann:
    """
    Método Schmertmann (1978) para asentamiento inmediato en suelos granulares.

    Factor de influencia Iz (perfil bilineal para zapata cuadrada/circular):
      · En la NDF (z=0):   Iz = 0.1
      · Pico en z = B/2:   Iz = Iz_peak = 0.5 + 0.1 × √(q_net / σ'vp)
      · En z = 2B:         Iz = 0
    """

    def calcular(
        self,
        B:         float,          # ancho de la zapata [m]
        L:         float,          # largo de la zapata [m]
        Df:        float,          # profundidad de desplante [m]
        q_total:   float,          # presión total en la NDF [kPa]
        gamma:     float,          # peso unitario del suelo [kN/m³]
        t:         float,          # tiempo de evaluación [años] (para C2)
        capas_inp: List[dict],     # lista de {'espesor':_, 'N60':_, 'tipo':_}
    ) -> "AsentamientoSchmertmann":

        if B <= 0 or L <= 0:
            raise ValueError("B y L deben ser positivos")
        if not capas_inp:
            raise ValueError("Se necesita al menos una capa de suelo")

        # ── Incremento neto de carga ─────────────────────────────────────
        sigma_v0 = gamma * Df   # tensión geoestática en NDF
        q_net    = max(q_total - sigma_v0, 0.0)

        # ── Factores C1 y C2 ─────────────────────────────────────────────
        C1 = max(1.0 - 0.5 * (sigma_v0 / q_net) if q_net > 1e-6 else 1.0, 0.5)
        C2 = 1.0 + 0.2 * math.log10(max(t, 0.1) / 0.1)

        # ── Diagrama de Iz (zapata rectangular, interpolada entre cuadrada y franja) ──
        ratio = min(L / B, 10.0) if B > 0 else 1.0

        # Para zapata cuadrada (ratio=1): z_peak=B/2, z_max=2B
        # Para franja (ratio→∞):         z_peak=B,   z_max=4B
        # Interpolación logarítmica
        f = min((math.log10(ratio) / math.log10(10.0)), 1.0)  # 0 para cuadrada, 1 para franja
        z_peak_fac = 0.5 + 0.5 * f   # 0.5B → 1.0B
        z_max_fac  = 2.0 + 2.0 * f   # 2.0B → 4.0B

        z_peak = z_peak_fac * B
        z_max  = z_max_fac  * B

        # Iz_peak depende de la tensión efectiva al nivel del pico
        sigma_vp = gamma * (Df + z_peak)   # aproximación: sin NF
        Iz_peak  = 0.5 + 0.1 * math.sqrt(q_net / max(sigma_vp, 1.0))

        def Iz_en(z):
            """Iz en función de z (desde la NDF)."""
            if z <= 0:
                return 0.1
            elif z <= z_peak:
                return 0.1 + (Iz_peak - 0.1) * z / z_peak
            elif z < z_max:
                return Iz_peak * (z_max - z) / (z_max - z_peak)
            else:
                return 0.0

        # ── Es por tipo de suelo (Schmertmann 1970 y Das 2021) ───────────
        def Es_de_N60(N60, tipo):
            N = max(N60, 1.0)
            if tipo == 'arena':
                return 500.0 * (N + 15.0)     # kPa
            else:  # arcilla_arenosa / limo
                return 300.0 * (N + 6.0)      # kPa

        # ── Suma por capas dentro de z_max ───────────────────────────────
        capas_out: List[CapaSchmertmann] = []
        suma = 0.0
        z_acum = 0.0

        for c in capas_inp:
            h   = float(c['espesor'])
            N60 = float(c['N60'])
            tip = str(c.get('tipo', 'arena'))
            Es  = Es_de_N60(N60, tip)

            z_top = z_acum
            z_bot = z_acum + h
            z_mid = (z_top + z_bot) / 2

            # Solo capas dentro de z_max
            if z_top >= z_max:
                break

            z_bot_eff = min(z_bot, z_max)
            h_eff     = z_bot_eff - z_top
            Iz_m      = Iz_en(z_mid)
            contrib   = Iz_m * h_eff / Es

            capas_out.append(CapaSchmertmann(
                espesor=h, N60=N60, tipo=tip, Es=Es,
                z_top=z_top, z_mid=z_mid,
                Iz_mid=Iz_m, contrib=contrib,
            ))
            suma    += contrib
            z_acum  += h

        delta_i = C1 * C2 * q_net * suma * 1000.0  # [mm]

        self.res = ResultadoSchmertmann(
            C1=C1, C2=C2, q_net=q_net,
            Iz_peak=Iz_peak, z_peak=z_peak, z_max=z_max,
            capas=capas_out, suma_Iz_Es=suma,
            delta_i=delta_i,
        )
        self._inp = dict(
            B=B, L=L, Df=Df, q_total=q_total,
            gamma=gamma, t=t, q_net=q_net,
        )
        return self


# ═══════════════════════════════════════════════════════════════════════════
#  TERZAGHI — Asentamiento por consolidación primaria
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PuntoTiempo:
    t:      float   # [años]
    Tv:     float   # factor de tiempo [-]
    U:      float   # grado de consolidación [%]
    delta:  float   # asentamiento [mm]


@dataclass
class ResultadoTerzaghi:
    # Esfuerzos
    sigma0:    float   # tensión efectiva inicial en el centro de la arcilla [kPa]
    delta_sig: float   # incremento de tensión en el centro (método 2:1) [kPa]
    sigma_f:   float   # tensión final = σ'₀ + Δσ [kPa]

    # Tipo de consolidación
    es_NC:     bool    # True = normalmente consolidada, False = sobreconsolidada
    sigma_p:   float   # tensión de preconsolidación [kPa]

    # Asentamientos
    delta_c:   float   # asentamiento total de consolidación [mm]
    delta_c1:  float   # componente OC (si aplica) [mm]
    delta_c2:  float   # componente NC (si aplica, OC→NC) [mm]

    # Tiempos
    H_dr:      float   # longitud de drenaje [m]
    t50:       float   # tiempo para U=50% [años]
    t90:       float   # tiempo para U=90% [años]

    # Curva δ(t)
    curva:     List[PuntoTiempo]


class AsentamientoTerzaghi:
    """
    Asentamiento por consolidación primaria (Terzaghi, 1943).

    Incremento de tensión: método 2:1 (Δσ = q_net·B·L / (B+z)·(L+z)).
    Para arcilla normalmente consolidada (NC):
        δ_c = Cc/(1+e₀) · H_c · log₁₀((σ'₀+Δσ)/σ'₀)
    Para sobreconsolidada (OC) con σ'₀ + Δσ > σ'p:
        δ_c = Cs/(1+e₀) · H_c · log₁₀(σ'p/σ'₀)
             + Cc/(1+e₀) · H_c · log₁₀((σ'₀+Δσ)/σ'p)
    Para OC con σ'₀ + Δσ ≤ σ'p:
        δ_c = Cs/(1+e₀) · H_c · log₁₀((σ'₀+Δσ)/σ'₀)
    """

    def calcular(
        self,
        # Zapata (para calcular Δσ por 2:1)
        B:          float,   # [m]
        L:          float,   # [m]
        q_net:      float,   # presión neta en NDF [kPa]
        # Capa de arcilla
        z_mid:      float,   # profundidad al centroide de la capa [m] (desde NDF)
        H_c:        float,   # espesor total de la capa [m]
        # Parámetros de compresibilidad
        Cc:         float,   # índice de compresión [-]
        e0:         float,   # relación de vacíos inicial [-]
        OCR:        float,   # relación de sobreconsolidación σ'p/σ'₀ ≥ 1
        sigma0:     float,   # tensión efectiva vertical inicial en el centro [kPa]
        Cs:         float,   # índice de hinchamiento (default ≈ Cc/5)
        # Parámetros de tiempo
        Cv:         float,   # coeficiente de consolidación [m²/año]
        doble_dren: bool,    # True = drenaje doble, False = drenaje simple
        n_puntos:   int = 40,
    ) -> "AsentamientoTerzaghi":

        if H_c <= 0 or Cc <= 0 or e0 <= 0:
            raise ValueError("H_c, Cc y e₀ deben ser positivos")
        if OCR < 1.0:
            raise ValueError("OCR debe ser ≥ 1.0")

        # ── Incremento de tensión (método 2:1) ───────────────────────────
        z  = z_mid
        delta_sig = q_net * B * L / ((B + z) * (L + z)) if z > 0 else q_net
        sigma_f   = sigma0 + delta_sig
        sigma_p   = OCR * sigma0   # tensión de preconsolidación

        # ── Asentamiento de consolidación ────────────────────────────────
        coef = 1.0 / (1.0 + e0) * H_c

        if sigma_f <= sigma_p:
            # Totalmente sobreconsolidado (OC puro)
            es_NC  = False
            dc1    = coef * Cs * math.log10(sigma_f / sigma0)
            dc2    = 0.0
            delta_c = dc1
        elif sigma0 >= sigma_p:
            # Normalmente consolidado
            es_NC  = True
            dc1    = 0.0
            dc2    = coef * Cc * math.log10(sigma_f / sigma0)
            delta_c = dc2
        else:
            # Sobreconsolidado que cruza σ'p
            es_NC  = False
            dc1    = coef * Cs * math.log10(sigma_p / sigma0)
            dc2    = coef * Cc * math.log10(sigma_f / sigma_p)
            delta_c = dc1 + dc2

        delta_c_mm = delta_c * 1000.0   # [mm]

        # ── Parámetros de tiempo ──────────────────────────────────────────
        H_dr = H_c / 2.0 if doble_dren else H_c

        def Tv_de_U(U_frac):
            """T_v dado el grado de consolidación U [0..1] — Das 9ª ed."""
            if U_frac <= 0.524:
                return math.pi / 4 * U_frac ** 2
            else:
                # Tv = 1.781 - 0.933·log10(100·(1-U))
                #    = -0.085 - 0.933·log10(1-U_frac)
                return -0.085 - 0.933 * math.log10(1.0 - U_frac)

        def U_de_Tv(Tv):
            """U [0..1] dado T_v — Sivaram & Swamee (1977)."""
            a = (4 * Tv / math.pi) ** 0.5
            b = (4 * Tv / math.pi) ** 2.8
            # U = (4Tv/π)^0.5 / (1 + (4Tv/π)^2.8)^(1/5.6)
            return a / (1 + b) ** (1.0 / 5.6) if Tv < 5 else 1.0

        t50 = Tv_de_U(0.50) * H_dr ** 2 / max(Cv, 1e-9)
        t90 = Tv_de_U(0.90) * H_dr ** 2 / max(Cv, 1e-9)

        # ── Curva δ(t) ───────────────────────────────────────────────────
        t_max = t90 * 2.5
        puntos: List[PuntoTiempo] = []
        for i in range(n_puntos + 1):
            t_i  = (i / n_puntos) ** 2 * t_max   # escala cuadrática (más detalle en t pequeño)
            Tv_i = max(Cv * t_i / H_dr ** 2, 0.0)
            U_i  = U_de_Tv(Tv_i)
            puntos.append(PuntoTiempo(
                t=round(t_i, 4),
                Tv=round(Tv_i, 4),
                U=round(U_i * 100, 2),
                delta=round(U_i * delta_c_mm, 3),
            ))

        self.res = ResultadoTerzaghi(
            sigma0=sigma0, delta_sig=delta_sig, sigma_f=sigma_f,
            es_NC=es_NC, sigma_p=sigma_p,
            delta_c=delta_c_mm, delta_c1=dc1 * 1000, delta_c2=dc2 * 1000,
            H_dr=H_dr, t50=t50, t90=t90,
            curva=puntos,
        )
        self._inp = dict(
            B=B, L=L, q_net=q_net, z_mid=z_mid, H_c=H_c,
            Cc=Cc, e0=e0, OCR=OCR, sigma0=sigma0, Cs=Cs,
            Cv=Cv, doble_dren=doble_dren,
        )
        return self
