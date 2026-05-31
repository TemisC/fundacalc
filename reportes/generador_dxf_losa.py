"""
Generador DXF — Losa de Fundación (Mat Foundation).
Produce:
  - Vista en planta (contorno losa + posición columnas + malla armadura)
  - Sección transversal con 4 capas de armadura
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
        return 0.012
    m = re.search(r'(\d+)', varilla)
    return int(m.group(1)) / 1000.0 if m else 0.012


def _sep_str(sep: float) -> str:
    return f"{sep * 100:.0f}" if sep else "—"


class GeneradorDXFLosa:

    def generar(self, ruta: str, motor, norma: str):
        if ezdxf:
            self._generar_con_ezdxf(ruta, motor, norma)
        else:
            self._generar_dxf_basico(ruta, motor, norma)

    # ── ezdxf ────────────────────────────────────────────────────────────────────

    def _generar_con_ezdxf(self, ruta: str, motor, norma: str):
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        layer_defs = {
            "LOSA":        4,   # cyan
            "COLUMNA":     8,   # gray
            "ACERO_INF_X": 3,   # green
            "ACERO_INF_Y": 5,   # blue
            "ACERO_SUP_X": 1,   # red
            "ACERO_SUP_Y": 6,   # magenta
            "COTAS":       7,
            "TEXTOS":      7,
        }
        for name, color in layer_defs.items():
            if name not in doc.layers:
                doc.layers.new(name, dxfattribs={"color": color})

        res = motor.res
        geo = motor.geo
        r   = geo.recubrimiento
        L   = res.L
        B   = res.B
        h   = res.h
        cx  = geo.cx
        cy  = geo.cy

        db_sx = _parse_db(res.var_sup_x);  sep_sx = res.sep_sup_x or 0.20
        db_sy = _parse_db(res.var_sup_y);  sep_sy = res.sep_sup_y or 0.20
        db_ix = _parse_db(res.var_inf_x);  sep_ix = res.sep_inf_x or 0.20
        db_iy = _parse_db(res.var_inf_y);  sep_iy = res.sep_inf_y or 0.20

        # ── PLANTA ──────────────────────────────────────────────────────────────
        ox, oy = 0.0, 0.0

        # Contorno losa
        self._rect(msp, ox, oy, L, B, "LOSA", 4)

        # Posición de columnas
        col_pos = self._col_positions(motor, L, B, cx, cy)
        for (xc, yc) in col_pos:
            self._rect(msp, ox + xc - cx / 2, oy + yc - cy / 2, cx, cy, "COLUMNA", 8)

        # Malla inferior X (líneas horizontales - verde)
        self._bars_h(msp, ox, oy, L, B, r, sep_ix, "ACERO_INF_X")
        # Malla inferior Y (líneas verticales - azul)
        self._bars_v(msp, ox, oy, L, B, r, sep_iy, "ACERO_INF_Y")
        # Malla superior X (horizontal - rojo)
        self._bars_h(msp, ox, oy, L, B, r, sep_sx, "ACERO_SUP_X")
        # Malla superior Y (vertical - magenta)
        self._bars_v(msp, ox, oy, L, B, r, sep_sy, "ACERO_SUP_Y")

        # Cotas planta
        self._cota_h(msp, ox, ox + L, oy - 0.50, oy, f"L = {L:.2f} m")
        self._cota_v(msp, oy, oy + B, ox - 0.50, ox, f"B = {B:.2f} m")

        # Leyenda planta
        lx = ox + L + 0.40
        leyenda = [
            (f"Arm. Inf-X ({res.var_inf_x or '—'} @ {_sep_str(sep_ix)} cm)  — verde  [capa: ACERO_INF_X]",  0.13),
            (f"Arm. Inf-Y ({res.var_inf_y or '—'} @ {_sep_str(sep_iy)} cm)  — azul   [capa: ACERO_INF_Y]",  0.13),
            (f"Arm. Sup-X ({res.var_sup_x or '—'} @ {_sep_str(sep_sx)} cm)  — rojo   [capa: ACERO_SUP_X]",  0.13),
            (f"Arm. Sup-Y ({res.var_sup_y or '—'} @ {_sep_str(sep_sy)} cm)  — magenta [capa: ACERO_SUP_Y]", 0.13),
            (f"Columna ({cx:.2f} × {cy:.2f} m) — gris [capa: COLUMNA]",                                     0.13),
        ]
        for i, (txt, ht) in enumerate(leyenda):
            self._text(msp, lx, oy + B - i * 0.30, txt, ht, "TEXTOS")

        # ── SECCIÓN TRANSVERSAL ─────────────────────────────────────────────────
        # Corte representativo en X mostrando ancho B y espesor h
        sx = ox
        sy = oy + B + 1.50

        # Contorno sección
        self._rect(msp, sx, sy, B, h, "LOSA", 4)

        # Capas de acero (desde inferior hasta superior)
        # Inf-Y (más profunda, círculos — barras perpendiculares al corte)
        y_iy = sy + r + db_iy / 2
        self._bar_circles(msp, sx, B, r, sep_iy, db_iy, y_iy, "ACERO_INF_Y")

        # Inf-X (por encima de Inf-Y, línea — barras paralelas al corte)
        y_ix = sy + r + db_iy + 0.005 + db_ix / 2
        self._line(msp, sx + r, y_ix, sx + B - r, y_ix, "ACERO_INF_X")

        # Sup-Y (bajo cara superior, círculos)
        y_sy = sy + h - r - db_sy / 2
        self._bar_circles(msp, sx, B, r, sep_sy, db_sy, y_sy, "ACERO_SUP_Y")

        # Sup-X (debajo de Sup-Y, línea)
        y_sx = sy + h - r - db_sy - 0.005 - db_sx / 2
        self._line(msp, sx + r, y_sx, sx + B - r, y_sx, "ACERO_SUP_X")

        # Cotas sección
        self._cota_v(msp, sy, sy + h, sx - 0.35, sx, f"h = {h:.2f} m")
        self._cota_h(msp, sx, sx + B, sy - 0.40, sy, f"B = {B:.2f} m")
        self._cota_v(msp, sy, y_iy, sx + B + 0.30, sx + B, f"r = {r*100:.0f} cm")

        # Etiqueta sección
        self._text(msp, sx, sy - 0.65, "SECCIÓN TRANSVERSAL  (corte en dirección X)", 0.13, "TEXTOS")
        self._text(msp, sx, sy - 0.85, f"Inf-X (—): {res.var_inf_x or '—'} @ {_sep_str(sep_ix)} cm  |  Inf-Y (●): {res.var_inf_y or '—'} @ {_sep_str(sep_iy)} cm", 0.10, "TEXTOS")
        self._text(msp, sx, sy - 1.00, f"Sup-X (—): {res.var_sup_x or '—'} @ {_sep_str(sep_sx)} cm  |  Sup-Y (●): {res.var_sup_y or '—'} @ {_sep_str(sep_sy)} cm", 0.10, "TEXTOS")

        # ── CUADRO DE ARMADURA ───────────────────────────────────────────────────
        ty = sy + h + 1.20
        header = [
            (f"FundaCalc — Losa de Fundación",                                                        0.18),
            (f"Norma: {norma}    Fecha: {datetime.now():%d/%m/%Y %H:%M}",                             0.12),
            (f"L = {L:.2f} m    B = {B:.2f} m    h = {h:.2f} m    d = {res.d:.3f} m    r = {r*100:.0f} cm",  0.11),
        ]
        for i, (txt, ht) in enumerate(header):
            self._text(msp, ox, ty + i * 0.28, txt, ht, "TEXTOS")

        ty2 = ty + len(header) * 0.28 + 0.20
        filas = [
            ("CUADRO DE ARMADURA",                                                                                                      0.14),
            (f"Capa Sup-X:  {res.var_sup_x or '—'} @ {_sep_str(sep_sx)} cm    As_req = {res.As_req_sup_x:.2f} cm²/m    As_dis = {res.As_dis_sup_x:.2f} cm²/m", 0.11),
            (f"Capa Sup-Y:  {res.var_sup_y or '—'} @ {_sep_str(sep_sy)} cm    As_req = {res.As_req_sup_y:.2f} cm²/m    As_dis = {res.As_dis_sup_y:.2f} cm²/m", 0.11),
            (f"Capa Inf-X:  {res.var_inf_x or '—'} @ {_sep_str(sep_ix)} cm    As_req = {res.As_req_inf_x:.2f} cm²/m    As_dis = {res.As_dis_inf_x:.2f} cm²/m", 0.11),
            (f"Capa Inf-Y:  {res.var_inf_y or '—'} @ {_sep_str(sep_iy)} cm    As_req = {res.As_req_inf_y:.2f} cm²/m    As_dis = {res.As_dis_inf_y:.2f} cm²/m", 0.11),
            (f"As mín = {res.As_min:.2f} cm²/m    q_max = {res.q_max:.1f} kN/m²    qu_net_avg = {res.qu_net_avg:.1f} kN/m²",           0.10),
        ]
        for i, (txt, ht) in enumerate(filas):
            self._text(msp, ox, ty2 + i * 0.22, txt, ht, "TEXTOS")

        doc.saveas(ruta)

    # ── Helpers de geometría ─────────────────────────────────────────────────────

    def _col_positions(self, motor, L, B, cx, cy):
        """Returns list of (x_center, y_center) for each column in the losa."""
        c = motor.carga
        nx = getattr(c, 'nx', None)
        if nx is not None:
            ny      = c.ny
            sx      = c.spacing_x
            sy      = c.spacing_y
            vx      = c.vuelo_x
            vy      = c.vuelo_y
            return [(vx + i * sx, vy + j * sy)
                    for i in range(nx) for j in range(ny)]
        # global/uniforme: no specific positions known
        n_col = getattr(c, 'n_col', 4) or 4
        import math
        nc = max(1, round(math.sqrt(n_col)))
        nr = max(1, (n_col + nc - 1) // nc)
        xs = [L / (nc + 1) * (i + 1) for i in range(nc)]
        ys = [B / (nr + 1) * (j + 1) for j in range(nr)]
        return [(x, y) for x in xs for y in ys][:n_col]

    def _bars_h(self, msp, ox, oy, L, B, r, sep, layer):
        if not sep or sep <= 0:
            return
        y = oy + r
        while y <= oy + B - r + 1e-6:
            self._line(msp, ox + r, y, ox + L - r, y, layer)
            y += sep

    def _bars_v(self, msp, ox, oy, L, B, r, sep, layer):
        if not sep or sep <= 0:
            return
        x = ox + r
        while x <= ox + L - r + 1e-6:
            self._line(msp, x, oy + r, x, oy + B - r, layer)
            x += sep

    def _bar_circles(self, msp, sx, width, r, sep, db, y_center, layer):
        if not sep or sep <= 0 or not ezdxf:
            return
        x = sx + r
        while x <= sx + width - r + 1e-6:
            msp.add_circle((x, y_center), db / 2,
                           dxfattribs={"layer": layer})
            x += sep

    # ── Primitivos DXF ───────────────────────────────────────────────────────────

    def _rect(self, msp, x, y, w, h, layer, color):
        msp.add_lwpolyline(
            [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)],
            dxfattribs={"layer": layer, "color": color},
        )

    def _line(self, msp, x1, y1, x2, y2, layer):
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})

    def _text(self, msp, x, y, txt, h=0.12, layer="TEXTOS"):
        msp.add_text(txt, dxfattribs={"height": h, "layer": layer, "insert": (x, y)})

    def _cota_h(self, msp, x1, x2, y_cota, y_ref, label):
        arr = abs(x2 - x1) * 0.025
        self._line(msp, x1, y_cota, x2, y_cota, "COTAS")
        self._line(msp, x1, y_ref,  x1, y_cota, "COTAS")
        self._line(msp, x2, y_ref,  x2, y_cota, "COTAS")
        mx = (x1 + x2) / 2
        self._text(msp, mx - len(label) * 0.035, y_cota - 0.20, label, 0.11, "COTAS")

    def _cota_v(self, msp, y1, y2, x_cota, x_ref, label):
        arr = abs(y2 - y1) * 0.04
        self._line(msp, x_cota, y1, x_cota, y2, "COTAS")
        self._line(msp, x_ref,  y1, x_cota, y1, "COTAS")
        self._line(msp, x_ref,  y2, x_cota, y2, "COTAS")
        my = (y1 + y2) / 2
        self._text(msp, x_cota - 0.40, my, label, 0.11, "COTAS")

    # ── Fallback sin ezdxf ───────────────────────────────────────────────────────

    def _generar_dxf_basico(self, ruta: str, motor, norma: str):
        res = motor.res
        geo = motor.geo
        L, B, h = res.L, res.B, res.h

        def ent(t, **kw):
            attrs = "".join(f"\n  8\n{kw.get('layer','0')}")
            return f"  0\n{t}{attrs}\n"

        lines = ["  0\nSECTION\n  2\nENTITIES\n"]

        def ln(x1, y1, x2, y2, layer="0"):
            lines.append(f"  0\nLINE\n  8\n{layer}\n 10\n{x1:.4f}\n 20\n{y1:.4f}\n 30\n0.0\n 11\n{x2:.4f}\n 21\n{y2:.4f}\n 31\n0.0\n")

        def txt(x, y, text, h=0.15, layer="0"):
            lines.append(f"  0\nTEXT\n  8\n{layer}\n 10\n{x:.4f}\n 20\n{y:.4f}\n 30\n0.0\n 40\n{h:.4f}\n  1\n{text}\n")

        # Contorno losa
        for (x1, y1, x2, y2) in [(0, 0, L, 0), (L, 0, L, B), (L, B, 0, B), (0, B, 0, 0)]:
            ln(x1, y1, x2, y2, "LOSA")

        txt(0, -0.40, f"L={L:.2f}m  B={B:.2f}m  h={h:.2f}m")
        txt(0, -0.60, f"Sup-X: {res.var_sup_x} @{_sep_str(res.sep_sup_x)}cm  Sup-Y: {res.var_sup_y} @{_sep_str(res.sep_sup_y)}cm")
        txt(0, -0.80, f"Inf-X: {res.var_inf_x} @{_sep_str(res.sep_inf_x)}cm  Inf-Y: {res.var_inf_y} @{_sep_str(res.sep_inf_y)}cm")

        lines.append("  0\nENDSEC\n  0\nEOF\n")
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("".join(lines))
