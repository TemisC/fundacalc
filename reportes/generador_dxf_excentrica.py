"""
Generador DXF para Zapata Excéntrica.
Produce:
  - Vista en planta (B×L) con barras en dos direcciones y flecha de excentricidad
  - Sección en dirección L con diagrama de presiones trapezoidal
  - Cuadro de armadura
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


class GeneradorDXFExcentrica:

    def generar(self, ruta: str, motor, norma: str):
        if ezdxf:
            self._generar_ezdxf(ruta, motor, norma)
        else:
            self._generar_basico(ruta, motor, norma)

    # ── ezdxf ────────────────────────────────────────────────────────────────

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
        }
        for nombre, color in capas.items():
            if nombre not in doc.layers:
                doc.layers.new(nombre, dxfattribs={"color": color})

        res   = motor.res
        col   = motor.columna
        geo   = motor.geo
        carga = motor.carga

        B, L, h    = res.B, res.L, res.h
        cx, cy     = col.cx, col.cy
        r          = geo.recubrimiento
        sep_L      = res.sep_L or 0.20
        sep_B      = res.sep_B or 0.20
        var_L      = res.varilla_L or "—"
        var_B      = res.varilla_B or "—"
        db_L       = _parse_db(var_L)
        db_B       = _parse_db(var_B)
        ex         = res.ex
        ey         = res.ey

        # ── PLANTA ───────────────────────────────────────────────────────────
        ox, oy = 0.0, 0.0

        # Zapata
        self._rect(msp, ox - B/2, oy - L/2, B, L, "ZAPATA", 5)

        # Columna
        self._rect(msp, ox - cx/2, oy - cy/2, cx, cy, "COLUMNA", 8)

        # Perimetro de punzonado (d/2 desde caras)
        d = geo.d
        self._rect(msp, ox - (cx+d)/2, oy - (cy+d)/2,
                   cx+d, cy+d, "ZAPATA", 3)

        # Barras dir. L (paralelas a L — corren en L, espaciadas en B)
        n_L = max(2, round(B / sep_L))
        for i in range(n_L + 1):
            yb = oy - L/2 + r + i * (L - 2*r) / max(n_L, 1) if n_L > 0 else oy
            msp.add_line(
                (ox - B/2 + r, yb, 0),
                (ox + B/2 - r, yb, 0),
                dxfattribs={"layer": "ACERO_L", "color": 1}
            )

        # Barras dir. B (paralelas a B — corren en B, espaciadas en L)
        n_B = max(2, round(L / sep_B))
        for i in range(n_B + 1):
            xb = ox - B/2 + r + i * (B - 2*r) / max(n_B, 1) if n_B > 0 else ox
            msp.add_line(
                (xb, oy - L/2 + r, 0),
                (xb, oy + L/2 - r, 0),
                dxfattribs={"layer": "ACERO_B", "color": 6}
            )

        # Flecha de excentricidad
        if abs(ex) > 0.001:
            msp.add_line(
                (ox, oy, 0),
                (ox + ex * 3, oy, 0),  # escala visual ×3
                dxfattribs={"layer": "COTAS", "color": 2}
            )
            msp.add_text(
                f"ex={ex:.3f}m",
                dxfattribs={"layer": "TEXTOS", "height": 0.05,
                            "insert": (ox + ex * 3 + 0.05, oy + 0.03, 0)}
            )
        if abs(ey) > 0.001:
            msp.add_line(
                (ox, oy, 0),
                (ox, oy + ey * 3, 0),
                dxfattribs={"layer": "COTAS", "color": 2}
            )
            msp.add_text(
                f"ey={ey:.3f}m",
                dxfattribs={"layer": "TEXTOS", "height": 0.05,
                            "insert": (ox + 0.03, oy + ey * 3 + 0.03, 0)}
            )

        # Cotas B y L
        self._cota_h(msp, ox - B/2, ox + B/2, oy + L/2 + 0.30, f"B = {B:.2f} m")
        self._cota_v(msp, ox + B/2 + 0.30, oy - L/2, oy + L/2, f"L = {L:.2f} m")

        # ── SECCIÓN EN L (desplazada en X) ───────────────────────────────────
        sx = ox + B/2 + 1.20

        # Cuerpo zapata
        self._rect(msp, sx - L/2, 0, L, h, "ZAPATA", 5)

        # Columna (stub)
        col_h = 0.40
        self._rect(msp, sx - cx/2, h, cx, col_h, "COLUMNA", 8)

        # Barras en L (línea horizontal al fondo)
        y_barL = r + db_L / 2
        msp.add_line(
            (sx - L/2 + r, y_barL, 0),
            (sx + L/2 - r, y_barL, 0),
            dxfattribs={"layer": "ACERO_L", "color": 1, "lineweight": 50}
        )

        # Barras en B (círculos perpendiculares)
        y_barB = r + db_L + db_B / 2
        n_show = min(12, max(3, round((L - 2*r) / sep_B)))
        for i in range(n_show + 1):
            xb = sx - L/2 + r + i * (L - 2*r) / max(n_show, 1)
            msp.add_circle(
                center=(xb, y_barB, 0),
                radius=db_B / 2,
                dxfattribs={"layer": "ACERO_B", "color": 6}
            )

        # Diagrama de presiones trapezoidal (escala 1kN = 0.003m)
        escala_p = 0.003
        q_max = res.q_max_u
        q_min = max(res.q_min_u, 0.0)
        py_max = -(q_max * escala_p)
        py_min = -(q_min * escala_p)

        msp.add_lwpolyline(
            [(sx - L/2, 0), (sx - L/2, py_min),
             (sx + L/2, py_max), (sx + L/2, 0), (sx - L/2, 0)],
            dxfattribs={"layer": "PRESIONES", "color": 2}
        )
        # Labels
        msp.add_text(
            f"qu,max={q_max:.0f}kPa",
            dxfattribs={"layer": "TEXTOS", "height": 0.04,
                        "insert": (sx + L/2 + 0.05, py_max / 2, 0)}
        )
        if q_min > 0:
            msp.add_text(
                f"qu,min={q_min:.0f}kPa",
                dxfattribs={"layer": "TEXTOS", "height": 0.04,
                            "insert": (sx - L/2 - 0.50, py_min / 2, 0)}
            )

        # Dim h
        self._cota_v(msp, sx + L/2 + 0.25, 0, h, f"h={h:.2f}m")
        # Dim L
        self._cota_h(msp, sx - L/2, sx + L/2, py_max - 0.25, f"L={L:.2f}m")

        # ── CUADRO DE ARMADURA ────────────────────────────────────────────────
        tx = sx + L/2 + 1.20
        ty = h + 0.40

        encabezados = [
            "CUADRO DE ARMADURA — ZAPATA EXCÉNTRICA",
            f"Norma: {norma}    Fecha: {datetime.now().strftime('%d/%m/%Y')}",
            "",
            f"B = {B:.2f} m   L = {L:.2f} m   h = {h:.2f} m   recub. = {geo.recubrimiento*100:.0f} cm",
            f"ex = {ex:.4f} m   ey = {ey:.4f} m   Contacto: {res.tipo_contacto}",
            "",
            f"Arm. dir.L (⊙ en sección):  {var_L} @ {sep_L*100:.0f} cm   As={res.As_dis_L:.2f} cm²/m   n={res.n_barras_L}",
            f"Arm. dir.B (— en sección):  {var_B} @ {sep_B*100:.0f} cm   As={res.As_dis_B:.2f} cm²/m   n={res.n_barras_B}",
            "",
            f"q_max_serv = {res.q_max:.1f} kN/m²   q_min_serv = {res.q_min:.1f} kN/m²",
            f"Punzonado: {'OK' if res.ok_punzonado else 'FALLA'}   Cortante L: {'OK' if res.ok_cortante_L else 'FALLA'}   Cortante B: {'OK' if res.ok_cortante_B else 'FALLA'}",
        ]
        for i, txt in enumerate(encabezados):
            msp.add_text(
                txt,
                dxfattribs={"layer": "TEXTOS", "height": 0.035 if i == 0 else 0.028,
                            "insert": (tx, ty - i * 0.08, 0)}
            )

        doc.saveas(ruta)

    # ── Helpers ──────────────────────────────────────────────────────────────

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

    # ── Fallback básico ───────────────────────────────────────────────────────

    def _generar_basico(self, ruta: str, motor, norma: str):
        res = motor.res
        lines = [
            "0\nSECTION\n2\nHEADER\n0\nENDSEC",
            "0\nSECTION\n2\nENTITIES",
            f"0\nTEXT\n8\nTEXTOS\n10\n0\n20\n0\n30\n0\n40\n0.1\n1\nFundaCalc - Zapata Excentrica",
            f"0\nTEXT\n8\nTEXTOS\n10\n0\n20\n-0.2\n30\n0\n40\n0.07\n1\nB={res.B:.2f}m L={res.L:.2f}m h={res.h:.2f}m",
            "0\nENDSEC\n0\nEOF",
        ]
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
