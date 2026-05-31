"""
Generador DXF — Encepado de Pilotes (Pile Cap).
Produce:
  - Vista en planta (contorno encepado + columna + pilotes + armadura)
  - Sección transversal (corte en X mostrando ancho B y altura h)
  - Cuadro de datos y armadura
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


class GeneradorDXFEncepado:

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
            "ENCEPADO": 4,
            "COLUMNA":  8,
            "PILOTES":  1,
            "ACERO_X":  3,
            "ACERO_Y":  5,
            "COTAS":    7,
            "TEXTOS":   7,
        }
        for name, color in layer_defs.items():
            if name not in doc.layers:
                doc.layers.new(name, dxfattribs={"color": color})

        res     = motor.res
        geo     = motor.geo
        pilote  = motor.pilote
        columna = motor.columna
        carga   = motor.carga

        r  = geo.recubrimiento
        L  = res.L
        B  = res.B
        h  = res.h
        d  = res.d
        cx = columna.cx
        cy = columna.cy
        D  = pilote.D
        Qa = pilote.Qa

        var_x      = res.var_x;  sep_x = res.sep_x or 0.20;  n_barras_x = res.n_barras_x
        var_y      = res.var_y;  sep_y = res.sep_y or 0.20;  n_barras_y = res.n_barras_y
        db_x = _parse_db(var_x);  db_y = _parse_db(var_y)

        pile_positions = res.pile_positions or []
        pile_loads_ser = res.pile_loads_ser or []

        ok_cap = "OK" if res.ok_capacidad else "FALLA"
        ok_pc  = "OK" if res.ok_punch_col else "FALLA"
        ok_pp  = "OK" if res.ok_punch_pil else "FALLA"
        Pser_v = getattr(carga, 'Pser', 0.0) or 0.0
        Pu_v   = getattr(carga, 'Pu',   0.0) or 0.0

        # ── LAYOUT ──────────────────────────────────────────────────────────────
        # Planta       : (0, 0) → (L, B)
        # Sección      : (L + GAP, 0) → (L + GAP + B, h)   [centrada verticalmente]
        # Cuadro/notas : debajo de la planta, y = -NOTA_Y  (coords negativas = abajo)
        # Leyenda       : a la derecha de la sección

        GAP  = max(B * 0.5, 1.5)   # espacio horizontal entre planta y sección
        ox, oy = 0.0, 0.0

        # ── PLANTA ──────────────────────────────────────────────────────────────
        self._rect(msp, ox, oy, L, B, "ENCEPADO", 4)

        # Columna centrada
        self._rect(msp, ox + L/2 - cx/2, oy + B/2 - cy/2, cx, cy, "COLUMNA", 8)

        # Pilotes
        for i, (px, py) in enumerate(pile_positions):
            xc = ox + L/2 + px
            yc = oy + B/2 + py
            msp.add_circle((xc, yc), D/2, dxfattribs={"layer": "PILOTES", "color": 1})
            lbl_sz = min(D * 0.35, 0.12)
            self._text(msp, xc - lbl_sz * 0.6, yc + D/2 * 0.1, f"P{i+1}", lbl_sz, "TEXTOS")
            pi_ser = pile_loads_ser[i] if i < len(pile_loads_ser) else 0.0
            self._text(msp, xc - lbl_sz * 1.2, yc - D/2 * 0.6, f"{pi_ser:.0f}kN", lbl_sz * 0.85, "TEXTOS")

        # Barras ACERO_X (horizontales)
        if n_barras_x > 0:
            usable_y = B - 2 * r
            for k in range(n_barras_x):
                yb = oy + r + (usable_y * k / (n_barras_x - 1) if n_barras_x > 1 else usable_y / 2)
                self._line(msp, ox + r, yb, ox + L - r, yb, "ACERO_X")

        # Barras ACERO_Y (verticales)
        if n_barras_y > 0:
            usable_x = L - 2 * r
            for k in range(n_barras_y):
                xb = ox + r + (usable_x * k / (n_barras_y - 1) if n_barras_y > 1 else usable_x / 2)
                self._line(msp, xb, oy + r, xb, oy + B - r, "ACERO_Y")

        # Cotas planta
        self._cota_h(msp, ox, ox + L, oy - 0.55, oy, f"L = {L:.2f} m")
        self._cota_v(msp, oy, oy + B, ox - 0.55, ox, f"B = {B:.2f} m")

        # ── SECCIÓN TRANSVERSAL ─────────────────────────────────────────────────
        # Centrada verticalmente respecto a la planta; separada por GAP
        sx = ox + L + GAP
        sy = oy + (B - h) / 2   # centrado vertical

        self._rect(msp, sx, sy, B, h, "ENCEPADO", 4)

        # Stub columna arriba
        self._rect(msp, sx + B/2 - cx/2, sy + h, cx, 0.25, "COLUMNA", 8)

        # Pilotes en sección: proyección en dirección Y del encepado
        unique_py = sorted(set(py for (_, py) in pile_positions))
        for py in unique_py:
            xp = sx + B/2 + py
            if sx + D/2 <= xp <= sx + B - D/2:
                self._rect(msp, xp - D/2, sy - 0.15, D, 0.15, "PILOTES", 1)

        # Barras en sección
        y_inf_y = sy + r + db_y / 2
        y_inf_x = sy + r + db_y + 0.005 + db_x / 2
        self._line(msp, sx + r, y_inf_x, sx + B - r, y_inf_x, "ACERO_X")
        if n_barras_y > 0:
            usable_b = B - 2 * r
            for k in range(n_barras_y):
                xc = sx + r + (usable_b * k / (n_barras_y - 1) if n_barras_y > 1 else usable_b / 2)
                msp.add_circle((xc, y_inf_y), db_y / 2, dxfattribs={"layer": "ACERO_Y", "color": 5})

        # Cotas sección
        self._cota_v(msp, sy, sy + h, sx - 0.45, sx, f"h = {h:.2f} m")
        self._cota_h(msp, sx, sx + B, sy - 0.55, sy, f"B = {B:.2f} m")
        self._cota_v(msp, sy, sy + r, sx + B + 0.35, sx + B, f"r={r*100:.0f}cm")

        # Etiqueta sección
        et_y = sy - 0.80
        self._text(msp, sx, et_y,        "SECCION TRANSVERSAL  (corte en X)", 0.13, "TEXTOS")
        self._text(msp, sx, et_y - 0.20, f"Arm.X(--): {var_x or '?'} n={n_barras_x}   Arm.Y(o): {var_y or '?'} n={n_barras_y}", 0.10, "TEXTOS")
        self._text(msp, sx, et_y - 0.36, f"d={d:.3f}m   r={r*100:.0f}cm   D_pil={D:.2f}m", 0.10, "TEXTOS")

        # ── CUADRO — debajo de la planta (y negativo) ────────────────────────────
        # Espacio suficiente debajo de la cota horizontal (oy - 0.55 - 0.25 label)
        nota_y0 = oy - 1.20   # punto de partida (decrece hacia abajo)
        paso    = 0.22

        cuadro = [
            (f"FundaCalc -- Encepado de Pilotes  |  Norma: {norma}  |  {datetime.now():%d/%m/%Y %H:%M}", 0.15),
            (f"L={L:.2f}m  B={B:.2f}m  h={h:.2f}m  d={d:.3f}m  r={r*100:.0f}cm", 0.11),
            (f"n={res.n} pilotes ({res.nx}x{res.ny})  D={D:.2f}m  Qa={Qa:.0f}kN  sx={res.spacing_x:.2f}m  sy={res.spacing_y:.2f}m  vx={res.vuelo_x:.2f}m  vy={res.vuelo_y:.2f}m", 0.11),
            (f"P_ser={Pser_v:.1f}kN  P_u={Pu_v:.1f}kN  P_max={res.P_max:.1f}kN  P_min={res.P_min:.1f}kN", 0.11),
            (f"Arm. X: {var_x or '?'} n={n_barras_x} @ {_sep_str(sep_x)}cm  |  Arm. Y: {var_y or '?'} n={n_barras_y} @ {_sep_str(sep_y)}cm", 0.11),
            (f"Capacidad pilotes: {ok_cap}   Punz.Col: {ok_pc}   Punz.Pil: {ok_pp}", 0.11),
        ]
        for i, (txt_c, ht) in enumerate(cuadro):
            self._text(msp, ox, nota_y0 - i * paso, txt_c, ht, "TEXTOS")

        # Leyenda de layers (a la derecha de sección + 0.50)
        lx = sx + B + 0.50
        leyenda = [
            (f"n={res.n} pilotes  D={D:.2f}m  Qa={Qa:.0f}kN",                                      0.12),
            (f"Arm. X: {var_x or '?'} n={n_barras_x} @ {_sep_str(sep_x)}cm  [ACERO_X verde]",      0.11),
            (f"Arm. Y: {var_y or '?'} n={n_barras_y} @ {_sep_str(sep_y)}cm  [ACERO_Y azul]",       0.11),
            (f"P_max={res.P_max:.1f}kN  P_min={res.P_min:.1f}kN",                                   0.11),
            (f"Columna: {cx:.2f}x{cy:.2f}m  [COLUMNA gris]",                                        0.11),
            (f"Capacidad: {ok_cap}  Punz.Col: {ok_pc}  Punz.Pil: {ok_pp}",                         0.11),
        ]
        for i, (txt_l, ht) in enumerate(leyenda):
            self._text(msp, lx, oy + B - i * 0.28, txt_l, ht, "TEXTOS")

        doc.saveas(ruta)

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
        self._line(msp, x1, y_cota, x2, y_cota, "COTAS")
        self._line(msp, x1, y_ref,  x1, y_cota, "COTAS")
        self._line(msp, x2, y_ref,  x2, y_cota, "COTAS")
        mx = (x1 + x2) / 2
        self._text(msp, mx - len(label) * 0.035, y_cota - 0.20, label, 0.11, "COTAS")

    def _cota_v(self, msp, y1, y2, x_cota, x_ref, label):
        self._line(msp, x_cota, y1, x_cota, y2, "COTAS")
        self._line(msp, x_ref,  y1, x_cota, y1, "COTAS")
        self._line(msp, x_ref,  y2, x_cota, y2, "COTAS")
        my = (y1 + y2) / 2
        self._text(msp, x_cota - 0.40, my, label, 0.11, "COTAS")

    # ── Fallback sin ezdxf ───────────────────────────────────────────────────────

    def _generar_dxf_basico(self, ruta: str, motor, norma: str):
        res     = motor.res
        geo     = motor.geo
        pilote  = motor.pilote
        columna = motor.columna
        carga   = motor.carga

        L  = res.L
        B  = res.B
        h  = res.h
        D  = pilote.D
        Qa = pilote.Qa
        cx = columna.cx
        cy = columna.cy

        var_x      = res.var_x
        sep_x      = res.sep_x or 0.20
        n_barras_x = res.n_barras_x
        var_y      = res.var_y
        sep_y      = res.sep_y or 0.20
        n_barras_y = res.n_barras_y

        lines = ["  0\nSECTION\n  2\nENTITIES\n"]

        def ln(x1, y1, x2, y2, layer="0"):
            lines.append(
                f"  0\nLINE\n  8\n{layer}\n"
                f" 10\n{x1:.4f}\n 20\n{y1:.4f}\n 30\n0.0\n"
                f" 11\n{x2:.4f}\n 21\n{y2:.4f}\n 31\n0.0\n"
            )

        def txt(x, y, text, h_txt=0.15, layer="0"):
            lines.append(
                f"  0\nTEXT\n  8\n{layer}\n"
                f" 10\n{x:.4f}\n 20\n{y:.4f}\n 30\n0.0\n"
                f" 40\n{h_txt:.4f}\n  1\n{text}\n"
            )

        # Contorno encepado (planta)
        for (x1, y1, x2, y2) in [
            (0, 0, L, 0), (L, 0, L, B), (L, B, 0, B), (0, B, 0, 0)
        ]:
            ln(x1, y1, x2, y2, "ENCEPADO")

        # Columna centrada
        hcx = L / 2 - cx / 2
        hcy = B / 2 - cy / 2
        for (x1, y1, x2, y2) in [
            (hcx, hcy, hcx + cx, hcy),
            (hcx + cx, hcy, hcx + cx, hcy + cy),
            (hcx + cx, hcy + cy, hcx, hcy + cy),
            (hcx, hcy + cy, hcx, hcy),
        ]:
            ln(x1, y1, x2, y2, "COLUMNA")

        # Pilotes
        pile_positions = res.pile_positions or []
        pile_loads_ser = res.pile_loads_ser or []
        for i, (px, py) in enumerate(pile_positions):
            cx_p = L / 2 + px
            cy_p = B / 2 + py
            carga_i = pile_loads_ser[i] if i < len(pile_loads_ser) else 0.0
            txt(cx_p - 0.05, cy_p + 0.05, f"P{i + 1}", 0.08, "PILOTES")
            txt(cx_p - 0.08, cy_p - 0.12, f"{carga_i:.0f}kN", 0.07, "PILOTES")

        # Barras X (horizontales)
        r = geo.recubrimiento
        if n_barras_x and n_barras_x > 0:
            usable_y = B - 2 * r
            for k in range(n_barras_x):
                if n_barras_x > 1:
                    y_bar = r + usable_y * k / (n_barras_x - 1)
                else:
                    y_bar = B / 2
                ln(r, y_bar, L - r, y_bar, "ACERO_X")

        # Barras Y (verticales)
        if n_barras_y and n_barras_y > 0:
            usable_x = L - 2 * r
            for k in range(n_barras_y):
                if n_barras_y > 1:
                    x_bar = r + usable_x * k / (n_barras_y - 1)
                else:
                    x_bar = L / 2
                ln(x_bar, r, x_bar, B - r, "ACERO_Y")

        # Textos informativos
        ok_cap = "OK" if res.ok_capacidad else "FALLA"
        ok_pc  = "OK" if res.ok_punch_col else "FALLA"
        ok_pp  = "OK" if res.ok_punch_pil else "FALLA"
        Pser_v = getattr(carga, 'Pser', 0.0) or 0.0

        txt(0, -0.40, f"FundaCalc - Encepado de Pilotes  [{norma}]  {datetime.now():%d/%m/%Y}")
        txt(0, -0.60, f"L={L:.2f}m  B={B:.2f}m  h={h:.2f}m  n={res.n} pilotes  D={D:.2f}m  Qa={Qa:.0f}kN")
        txt(0, -0.80, f"Arm. X: {var_x or '—'} n={n_barras_x} @ {_sep_str(sep_x)}cm  |  Arm. Y: {var_y or '—'} n={n_barras_y} @ {_sep_str(sep_y)}cm")
        txt(0, -1.00, f"P_max={res.P_max:.1f}kN  P_min={res.P_min:.1f}kN  P_ser={Pser_v:.1f}kN")
        txt(0, -1.20, f"Capacidad: {ok_cap}   Punz.Col: {ok_pc}   Punz.Pil: {ok_pp}")

        lines.append("  0\nENDSEC\n  0\nEOF\n")
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("".join(lines))
