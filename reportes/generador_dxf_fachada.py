"""
Generador DXF para Zapata de Fachada / Excéntrica por Geometría.
Vista en planta con columna descentrada, sección en L con diagrama de presiones,
línea de límite del predio y cuadro de armadura.
"""
import re
from datetime import datetime

try:
    import ezdxf
except ImportError:
    ezdxf = None


def _parse_db(varilla: str) -> float:
    if not varilla:
        return 0.016
    m = re.search(r'(\d+)', varilla)
    return int(m.group(1)) / 1000.0 if m else 0.016


class GeneradorDXFFachada:

    def generar(self, ruta: str, motor, norma: str):
        if ezdxf:
            self._generar_ezdxf(ruta, motor, norma)
        else:
            self._generar_basico(ruta, motor, norma)

    def _generar_ezdxf(self, ruta: str, motor, norma: str):
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        capas = {
            "ZAPATA":    5,
            "COLUMNA":   8,
            "ACERO_L":   1,
            "ACERO_B":   6,
            "PRESIONES": 2,
            "COTAS":     7,
            "TEXTOS":    7,
            "LINDERO":   4,   # cyan — límite de predio
        }
        for nombre, color in capas.items():
            if nombre not in doc.layers:
                doc.layers.new(nombre, dxfattribs={"color": color})

        res  = motor.res
        col  = motor.columna
        geo  = motor.geo
        gf   = motor.geo_fachada

        B, L, h  = res.B, res.L, res.h
        cx, cy   = col.cx, col.cy
        r        = geo.recubrimiento
        sep_L    = res.sep_L or 0.20
        sep_B    = res.sep_B or 0.20
        var_L    = res.varilla_L or "—"
        var_B    = res.varilla_B or "—"
        db_L     = _parse_db(var_L)
        db_B     = _parse_db(var_B)
        ex       = gf.ex_geom   # column offset from footing centroid (+ = right)
        ey       = gf.ey_geom

        # ── PLANTA ───────────────────────────────────────────────────────────
        ox, oy = 0.0, 0.0

        # Zapata
        self._rect(msp, ox - B/2, oy - L/2, B, L, "ZAPATA", 5)

        # Columna (centroide en ex, ey desde el centroide de la zapata)
        col_x = ox + ex
        col_y = oy + ey
        self._rect(msp, col_x - cx/2, col_y - cy/2, cx, cy, "COLUMNA", 8)

        # Línea de lindero (lado restringido = derecha: x = ox + L/2)
        lindero_x = ox + L/2
        msp.add_line(
            (lindero_x + 0.05, oy - L/2 - 0.30, 0),
            (lindero_x + 0.05, oy + L/2 + 0.30, 0),
            dxfattribs={"layer": "LINDERO", "color": 4, "lineweight": 35}
        )
        msp.add_text(
            "LINDERO",
            dxfattribs={"layer": "LINDERO", "height": 0.04,
                        "insert": (lindero_x + 0.10, oy + L/2 + 0.20, 0)}
        )

        # Flecha de excentricidad (del centroide zapata al centroide columna)
        if abs(ex) > 0.001:
            msp.add_line((ox, oy, 0), (col_x, oy, 0),
                         dxfattribs={"layer": "COTAS", "color": 2})
            msp.add_text(f"ex={ex:.3f}m",
                         dxfattribs={"layer": "TEXTOS", "height": 0.05,
                                     "insert": ((ox + col_x) / 2, oy + 0.06, 0)})
        if abs(ey) > 0.001:
            msp.add_line((ox, oy, 0), (ox, col_y, 0),
                         dxfattribs={"layer": "COTAS", "color": 2})
            msp.add_text(f"ey={ey:.3f}m",
                         dxfattribs={"layer": "TEXTOS", "height": 0.05,
                                     "insert": (ox + 0.03, (oy + col_y) / 2, 0)})

        # Perímetro de punzonado
        d = geo.d
        self._rect(msp, col_x - (cx+d)/2, col_y - (cy+d)/2,
                   cx+d, cy+d, "ZAPATA", 3)

        # Barras dir. L
        n_L = max(2, round(B / sep_L))
        for i in range(n_L + 1):
            yb = oy - L/2 + r + i * (L - 2*r) / max(n_L, 1)
            msp.add_line(
                (ox - B/2 + r, yb, 0),
                (ox + B/2 - r, yb, 0),
                dxfattribs={"layer": "ACERO_L", "color": 1}
            )

        # Barras dir. B
        n_B = max(2, round(L / sep_B))
        for i in range(n_B + 1):
            xb = ox - B/2 + r + i * (B - 2*r) / max(n_B, 1)
            msp.add_line(
                (xb, oy - L/2 + r, 0),
                (xb, oy + L/2 - r, 0),
                dxfattribs={"layer": "ACERO_B", "color": 6}
            )

        # Cotas B y L
        self._cota_h(msp, ox - B/2, ox + B/2, oy + L/2 + 0.30, f"B = {B:.2f} m")
        self._cota_v(msp, ox + B/2 + 0.60, oy - L/2, oy + L/2, f"L = {L:.2f} m")

        # ── SECCIÓN EN L ──────────────────────────────────────────────────────
        sx = ox + B/2 + 1.60

        self._rect(msp, sx - L/2, 0, L, h, "ZAPATA", 5)

        # Columna descentrada en sección
        col_h = 0.40
        self._rect(msp, sx + ex - cx/2, h, cx, col_h, "COLUMNA", 8)

        # Barras en L
        y_barL = r + db_L / 2
        msp.add_line((sx - L/2 + r, y_barL, 0), (sx + L/2 - r, y_barL, 0),
                     dxfattribs={"layer": "ACERO_L", "color": 1, "lineweight": 50})

        # Barras en B (círculos)
        y_barB = r + db_L + db_B / 2
        n_show = min(12, max(3, round((L - 2*r) / sep_B)))
        for i in range(n_show + 1):
            xb = sx - L/2 + r + i * (L - 2*r) / max(n_show, 1)
            msp.add_circle(center=(xb, y_barB, 0), radius=db_B / 2,
                           dxfattribs={"layer": "ACERO_B", "color": 6})

        # Diagrama de presiones trapezoidal
        escala_p = 0.003
        q_max = res.q_max_u
        q_min = max(res.q_min_u, 0.0)
        # el lado de mayor presión coincide con el lado de la columna (ex > 0 → derecha)
        if ex >= 0:
            py_right = -(q_max * escala_p)
            py_left  = -(q_min * escala_p)
        else:
            py_right = -(q_min * escala_p)
            py_left  = -(q_max * escala_p)

        msp.add_lwpolyline(
            [(sx - L/2, 0), (sx - L/2, py_left),
             (sx + L/2, py_right), (sx + L/2, 0), (sx - L/2, 0)],
            dxfattribs={"layer": "PRESIONES", "color": 2}
        )
        msp.add_text(f"qu,max={q_max:.0f}kPa",
                     dxfattribs={"layer": "TEXTOS", "height": 0.04,
                                 "insert": (sx + L/2 + 0.05, py_right / 2, 0)})
        if q_min > 0:
            msp.add_text(f"qu,min={q_min:.0f}kPa",
                         dxfattribs={"layer": "TEXTOS", "height": 0.04,
                                     "insert": (sx - L/2 - 0.55, py_left / 2, 0)})

        # Lindero en sección
        msp.add_line((sx + L/2 + 0.05, -0.40, 0),
                     (sx + L/2 + 0.05, h + col_h + 0.20, 0),
                     dxfattribs={"layer": "LINDERO", "color": 4})
        msp.add_text("LINDERO",
                     dxfattribs={"layer": "LINDERO", "height": 0.035,
                                 "insert": (sx + L/2 + 0.08, h + col_h, 0)})

        self._cota_v(msp, sx + L/2 + 0.30, 0, h, f"h={h:.2f}m")
        self._cota_h(msp, sx - L/2, sx + L/2, min(py_left, py_right) - 0.25, f"L={L:.2f}m")

        # ── CUADRO DE ARMADURA ────────────────────────────────────────────────
        tx = sx + L/2 + 1.20
        ty = h + 0.40

        encabezados = [
            "CUADRO DE ARMADURA — ZAPATA FACHADA / EXCÉNTRICA POR GEOMETRÍA",
            f"Norma: {norma}    Fecha: {datetime.now().strftime('%d/%m/%Y')}",
            "",
            f"B = {B:.2f} m   L = {L:.2f} m   h = {h:.2f} m   recub. = {geo.recubrimiento*100:.0f} cm",
            f"ex_geom = {ex:.4f} m   ey_geom = {ey:.4f} m   Contacto: {res.tipo_contacto}",
            f"Mx_equiv = {motor.carga.Mser_x:.1f} kN·m   "
            f"Viga atado T ≈ {motor.T_atado:.1f} kN  (L_at={motor.L_atado:.1f}m)",
            "",
            f"Arm. dir.L:  {var_L} @ {sep_L*100:.0f} cm   As={res.As_dis_L:.2f} cm²/m   n={res.n_barras_L}",
            f"Arm. dir.B:  {var_B} @ {sep_B*100:.0f} cm   As={res.As_dis_B:.2f} cm²/m   n={res.n_barras_B}",
            "",
            f"q_max_serv = {res.q_max:.1f} kN/m²   q_min_serv = {res.q_min:.1f} kN/m²",
            f"Punzonado: {'OK' if res.ok_punzonado else 'FALLA'}   "
            f"Cortante L: {'OK' if res.ok_cortante_L else 'FALLA'}   "
            f"Cortante B: {'OK' if res.ok_cortante_B else 'FALLA'}",
        ]
        for i, txt in enumerate(encabezados):
            msp.add_text(
                txt,
                dxfattribs={"layer": "TEXTOS",
                            "height": 0.035 if i == 0 else 0.028,
                            "insert": (tx, ty - i * 0.08, 0)}
            )

        doc.saveas(ruta)

    def _rect(self, msp, x, y, w, h, layer, color):
        pts = [(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)]
        msp.add_lwpolyline(pts, dxfattribs={"layer": layer, "color": color})

    def _cota_h(self, msp, x1, x2, y, texto):
        msp.add_line((x1, y, 0), (x2, y, 0), dxfattribs={"layer": "COTAS", "color": 7})
        msp.add_text(texto, dxfattribs={"layer": "TEXTOS", "height": 0.05,
                     "insert": ((x1+x2)/2, y + 0.06, 0), "halign": 4,
                     "align_point": ((x1+x2)/2, y + 0.06, 0)})

    def _cota_v(self, msp, x, y1, y2, texto):
        msp.add_line((x, y1, 0), (x, y2, 0), dxfattribs={"layer": "COTAS", "color": 7})
        msp.add_text(texto, dxfattribs={"layer": "TEXTOS", "height": 0.05,
                     "insert": (x + 0.06, (y1+y2)/2, 0)})

    def _generar_basico(self, ruta: str, motor, norma: str):
        res = motor.res
        lines = [
            "0\nSECTION\n2\nHEADER\n0\nENDSEC",
            "0\nSECTION\n2\nENTITIES",
            f"0\nTEXT\n8\nTEXTOS\n10\n0\n20\n0\n30\n0\n40\n0.1\n1\n"
            f"FundaCalc - Zapata Fachada",
            f"0\nTEXT\n8\nTEXTOS\n10\n0\n20\n-0.2\n30\n0\n40\n0.07\n1\n"
            f"B={res.B:.2f}m L={res.L:.2f}m h={res.h:.2f}m "
            f"ex={motor.ex_geom:.3f}m",
            "0\nENDSEC\n0\nEOF",
        ]
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
