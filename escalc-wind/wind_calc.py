"""
ESCALC Wind — ASCE 7-22 Wind Pressure Calculator
Version 1.0 | Engineering Software CALC
Units: ft, lb, psf, mph

Verification target (MecaWind v2542 — 15755 SW 168 AVE, Miami FL 33187):
  V=175 mph, Exp C, ASD → qh=40.04 psf, G=0.850
  Walls (GCpi+): WW=17.02, LW=-20.59, Side=-26.38, Total=37.61
  T-1 area=182.68 ft², Zone 1 → Pmax=16.34, Pmin=-34.38
  Overhang Zone 3_OHS → Pmax=9.60, Pmin=-128.64
"""
import math
import json
from asce7_tables import (
    EXPOSURE_CONSTANTS, GCpi_TABLE, get_GCp_roof, GCp_wall,
)


class WindCalculator:
    def __init__(self, inputs: dict):
        self.V          = float(inputs['V'])
        self.exposure   = inputs['exposure']          # 'B', 'C', 'D'
        self.risk_cat   = inputs.get('risk_cat', 'II')
        self.wind_basis = inputs.get('wind_basis', 'ASD')
        self.Kd         = float(inputs.get('Kd', 0.85))
        self.Kzt        = float(inputs.get('Kzt', 1.0))
        self.Ke         = float(inputs.get('Ke', 1.0))

        self.W          = float(inputs['W'])
        self.L          = float(inputs['L'])
        self.eave_h     = float(inputs['eave_h'])
        self.ridge_h    = float(inputs['ridge_h'])
        self.roof_type  = inputs.get('roof_type', 'Hipped')
        self.pitch_x    = float(inputs.get('pitch_x', 0.0))
        self.overhang   = float(inputs.get('overhang', 0.0))
        self.enclosure  = inputs.get('enclosure', 'Enclosed')
        self.components = inputs.get('components', [])

        self.LF = 0.60 if self.wind_basis == 'ASD' else 1.00
        self._calc_geometry()

    def _calc_geometry(self):
        if self.roof_type == 'Flat' or self.pitch_x == 0:
            self.h = self.eave_h
        else:
            self.h = self.eave_h + (self.ridge_h - self.eave_h) / 2.0

        self.theta = math.degrees(math.atan(self.pitch_x / 12.0)) if self.pitch_x > 0 else 0.0

        a1 = min(0.1 * min(self.W, self.L), 0.4 * self.h)
        self.a = max(a1, 0.04 * min(self.W, self.L), 3.0)
        self.A_roof = self.W * self.L

    # ── Base Parameters ──────────────────────────────────────────────────────

    def calc_Kh(self) -> float:
        """Kh via Eq. C26.10-2: Kh = 2.41 × (z/zg)^(2/α)"""
        exp = EXPOSURE_CONSTANTS[self.exposure]
        z   = max(self.h, float(exp['Zmin']))
        return round(2.41 * (z / exp['zg']) ** (2.0 / exp['alpha']), 3)

    def calc_qh(self, Kh: float) -> float:
        """
        Velocity pressure at mean roof height (Eq. 26.10-1, with ASD factor).
        qh = 0.00256 × Kh × Kzt × Ke × V² × LF
        NOTE: Kd is NOT included here — applied separately in pressure equations.
        Verification: V=175, Kh=0.851, Kzt=1, Ke=1, LF=0.6 → qh=40.04 psf ✓
        """
        return round(0.00256 * Kh * self.Kzt * self.Ke * self.V ** 2 * self.LF, 3)

    def calc_G(self, B_perp: float) -> dict:
        """
        Gust factor §26.11. B_perp = building dimension NORMAL to wind direction.
        G = min(G1_simplified=0.85, G2_complete_analysis).
        """
        G1  = 0.85
        exp = EXPOSURE_CONSTANTS[self.exposure]
        Zmin = float(exp['Zmin'])

        Zm  = max(0.6 * self.h, Zmin)
        Izm = exp['c'] * (33.0 / Zm) ** (1.0 / 6.0)
        Lzm = exp['l'] * (Zm / 33.0) ** exp['epsilon']
        Q   = math.sqrt(1.0 / (1.0 + 0.63 * ((B_perp + self.h) / Lzm) ** 0.63))

        gq = gv = 3.4
        G2 = 0.925 * (1.0 + 1.7 * gq * Izm * Q) / (1.0 + 1.7 * gv * Izm)
        G  = min(G1, G2)

        return {
            'G1': round(G1, 3), 'G2': round(G2, 3), 'G': round(G, 3),
            'Zm': round(Zm, 3), 'Izm': round(Izm, 3),
            'Lzm': round(Lzm, 3), 'Q': round(Q, 3),
        }

    def calc_GCpi(self) -> float:
        return GCpi_TABLE.get(self.enclosure, 0.18)

    def _Cp_leeward(self, LB_ratio: float) -> float:
        """Leeward wall Cp, Table 27.3-1. L = depth along wind, B = width."""
        if LB_ratio <= 1.0:   return -0.5
        elif LB_ratio <= 2.0: return -0.5 + 0.2  * (LB_ratio - 1.0)
        elif LB_ratio <= 4.0: return -0.3 + 0.05 * (LB_ratio - 2.0)
        else:                  return -0.2

    # ── MWFRS Walls ──────────────────────────────────────────────────────────

    def _mwfrs_walls_direction(self, qh, G, GCpi, wind_along: str) -> list:
        """
        Wall pressures for one wind direction (Eq. 27.3-1):
        p = qz × Kd × G × Cp - qi × Kd × GCpi
        wind_along: 'W' (normal to ridge) or 'L' (parallel to ridge)
        """
        Kh  = self.calc_Kh()
        CpWW, CpSW = 0.80, -0.70

        if wind_along == 'W':
            LB = self.W / self.L   # wind depth / building width
        else:
            LB = self.L / self.W

        CpLW = self._Cp_leeward(LB)
        rows = []

        for gcpi_sign, gcpi_val in [('+', GCpi), ('-', -GCpi)]:
            qi   = qh
            pWW  = qh * self.Kd * G * CpWW - qi * self.Kd * gcpi_val
            pLW  = qh * self.Kd * G * CpLW - qi * self.Kd * gcpi_val
            pSW  = qh * self.Kd * G * CpSW - qi * self.Kd * gcpi_val
            pTot = pWW - pLW
            rows.append({
                'wind_along': wind_along, 'GCpi_sign': gcpi_sign,
                'GCpi': round(gcpi_val, 2), 'LB': round(LB, 3),
                'Kz': round(Kh, 3), 'qz': round(qh, 2), 'G': round(G, 3),
                'CpWW': CpWW, 'CpLW': round(CpLW, 3), 'CpSW': CpSW,
                'windward': round(pWW, 2), 'leeward': round(pLW, 2),
                'side':     round(pSW, 2), 'total':   round(pTot, 2),
                'min_p': 9.60,
            })
        return rows

    def calc_mwfrs_walls(self, qh, G_normal, G_parallel, GCpi) -> dict:
        return {
            'normal':   self._mwfrs_walls_direction(qh, G_normal,   GCpi, 'W'),
            'parallel': self._mwfrs_walls_direction(qh, G_parallel, GCpi, 'L'),
        }

    # ── MWFRS Roof ───────────────────────────────────────────────────────────

    def _Cp_roof_ww(self) -> tuple:
        """
        Windward roof Cp range from Table 27.3-2.
        Returns (Cp_min, Cp_max).
        """
        t = self.theta
        if t <= 10.0:
            return -0.9, -0.18
        elif t <= 15.0:
            f = (t - 10.0) / 5.0
            return (-0.9 + f * 0.3), (-0.18 + f * 0.38)
        elif t <= 20.0:
            return -0.6, 0.2
        elif t <= 25.0:
            return -0.5, 0.3
        elif t <= 30.0:
            return -0.3, 0.4
        elif t <= 45.0:
            return 0.0, 0.4
        else:
            return 0.0, 0.4

    def _mwfrs_roof_normal(self, qh, G, GCpi) -> list:
        """MWFRS roof — wind normal to ridge (Windward + Leeward slopes)."""
        hL_ratio = self.h / self.W
        Cp_ww_min, Cp_ww_max = self._Cp_roof_ww()
        CpLW = -0.3 if hL_ratio <= 0.25 else (-0.5 if hL_ratio <= 0.5 else -0.6)

        rows = []
        for gcpi_sign, gcpi_val in [('+', GCpi), ('-', -GCpi)]:
            for label, Cp in [('Windward (lower)', Cp_ww_min), ('Windward (upper)', Cp_ww_max)]:
                P = qh * self.Kd * G * Cp - qh * self.Kd * gcpi_val
                rows.append({
                    'surface': label, 'zone': 'WW',
                    'GCpi_sign': gcpi_sign, 'GCpi': gcpi_val,
                    'Cp': round(Cp, 3), 'P': round(P, 2), 'min_p': 4.80,
                    'theta': round(self.theta, 2), 'hL': round(hL_ratio, 3),
                })
            P_LW = qh * self.Kd * G * CpLW - qh * self.Kd * gcpi_val
            rows.append({
                'surface': 'Leeward', 'zone': 'LW',
                'GCpi_sign': gcpi_sign, 'GCpi': gcpi_val,
                'Cp': round(CpLW, 3), 'P': round(P_LW, 2), 'min_p': 4.80,
                'theta': round(self.theta, 2), 'hL': round(hL_ratio, 3),
            })
        return rows

    def _mwfrs_roof_parallel(self, qh, G, GCpi) -> list:
        """MWFRS roof — wind parallel to ridge (distance zones)."""
        h = self.h
        zones = [
            ('0 to h', -0.9, f'0 – {h:.2f} ft'),
            ('h to 2h', -0.5, f'{h:.2f} – {2*h:.2f} ft'),
            ('≥ 2h', -0.3, f'≥ {2*h:.2f} ft'),
        ]
        rows = []
        for gcpi_sign, gcpi_val in [('+', GCpi), ('-', -GCpi)]:
            for zone_id, Cp, dist in zones:
                P = qh * self.Kd * G * Cp - qh * self.Kd * gcpi_val
                rows.append({
                    'surface': f'Roof {dist}', 'zone': zone_id,
                    'GCpi_sign': gcpi_sign, 'GCpi': gcpi_val,
                    'Cp': Cp, 'P': round(P, 2), 'min_p': 4.80,
                })
        return rows

    # ── C&C Components ───────────────────────────────────────────────────────

    def calc_cc_component(self, comp: dict, qh: float) -> dict:
        """
        C&C pressure per Eq. 30.3-1:
        Pmax = qh × Kd × (GCpd + GCpi)   [toward surface, downward]
        Pmin = qh × Kd × (GCpu - GCpi)   [away from surface, uplift]
        Min per §30.2.2: ±9.60 psf
        """
        zone  = int(comp['zone'])
        width = float(comp['width'])
        span  = float(comp['span'])

        if comp.get('one_third', True):
            width = min(width, span / 3.0)
        area = span * width

        ctype = comp.get('type', 'Truss').lower()
        is_wall = any(w in ctype for w in ('wall', 'opening', 'door', 'garage'))
        if is_wall:
            GCpd, GCpu = GCp_wall(area, zone)
            ref = 'Fig. 30.3-1'
        else:
            GCpd, GCpu = get_GCp_roof(area, zone, self.theta, self.roof_type)
            ref = 'Fig. 30.3-2E'

        GCpi = self.calc_GCpi()
        Pmax = qh * self.Kd * (GCpd + GCpi)
        Pmin = qh * self.Kd * (GCpu - GCpi)
        Pmax = max(Pmax, 9.60)
        Pmin = min(Pmin, -9.60)

        return {
            'id':        comp['id'],
            'type':      comp.get('type', '—'),
            'zone':      zone,
            'width':     round(width, 3),
            'span':      round(span, 3),
            'area':      round(area, 2),
            'one_third': comp.get('one_third', True),
            'ref':       ref,
            'a':         round(self.a, 2),
            'GCpi':      round(GCpi, 2),
            'GCpd':      round(GCpd, 3),
            'GCpu':      round(GCpu, 3),
            'Pmax':      round(Pmax, 2),
            'Pmin':      round(Pmin, 2),
        }

    # ── Overhangs ────────────────────────────────────────────────────────────

    def calc_overhang(self, qh: float) -> list:
        """
        Roof overhang uplift — Ch. 30 Pt. 4, Zone 3_OHS.
        GCpu = -3.60 (most critical zone).
        Verification: qh=40.04, Kd=0.85 → Pmin=-128.64 psf ✓
        """
        if self.overhang <= 0:
            return []
        GCpi     = self.calc_GCpi()
        GCpu_oh  = -3.60
        GCpd_oh  = 0.00
        Pmax = qh * self.Kd * (GCpd_oh + GCpi)
        Pmin = qh * self.Kd * (GCpu_oh - GCpi)
        return [{
            'zone':  '3_OHS',
            'span':  round(self.overhang, 3),
            'a':     round(self.a, 2),
            'GCpi':  round(GCpi, 2),
            'GCpd':  GCpd_oh,
            'GCpu':  GCpu_oh,
            'Pmax':  round(max(Pmax, 9.60), 2),
            'Pmin':  round(Pmin, 2),
        }]

    # ── Main ─────────────────────────────────────────────────────────────────

    def run(self) -> dict:
        Kh   = self.calc_Kh()
        qh   = self.calc_qh(Kh)
        GCpi = self.calc_GCpi()

        # G for each wind direction:
        # Normal to ridge → wind along W → B_perpendicular = L
        # Parallel to ridge → wind along L → B_perpendicular = W
        G_n_dict = self.calc_G(self.L)
        G_p_dict = self.calc_G(self.W)

        walls = self.calc_mwfrs_walls(qh, G_n_dict['G'], G_p_dict['G'], GCpi)
        roof  = {
            'normal':   self._mwfrs_roof_normal(qh, G_n_dict['G'], GCpi),
            'parallel': self._mwfrs_roof_parallel(qh, G_p_dict['G'], GCpi),
        }
        cc_results  = [self.calc_cc_component(c, qh) for c in self.components]
        overhangs   = self.calc_overhang(qh)

        return {
            'status': 'ok',
            'params': {
                'h':        round(self.h, 3),
                'theta':    round(self.theta, 2),
                'a':        round(self.a, 3),
                'A_roof':   round(self.A_roof, 2),
                'Kh':       Kh,
                'Kzt':      self.Kzt,
                'Kd':       self.Kd,
                'Ke':       self.Ke,
                'GCpi_val': round(GCpi, 2),
                'LF':       self.LF,
                'qh':       qh,
                'G_normal':   G_n_dict,
                'G_parallel': G_p_dict,
                'V':        self.V,
                'exposure': self.exposure,
                'risk_cat': self.risk_cat,
                'wind_basis': self.wind_basis,
                'enclosure':  self.enclosure,
                'roof_type':  self.roof_type,
            },
            'walls':      walls,
            'roof':       roof,
            'cc':         cc_results,
            'overhangs':  overhangs,
        }


def calculate(inputs_json: str) -> str:
    """Pyodide entry point. Receives and returns JSON strings."""
    try:
        inputs = json.loads(inputs_json)
        result = WindCalculator(inputs).run()
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'message': str(e),
            'trace': traceback.format_exc(),
        })
