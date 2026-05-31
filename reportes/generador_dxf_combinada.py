"""
Generador DXF con bloques para Zapata Combinada Rectangular.
Vistas incluidas:
  1. Vista en Planta  — armadura long. superior + barras transversales + perímetros punzonado
  2. Sección A-A      — sección longitudinal con barras sup/inf como círculos
  3. Sección B-B      — sección transversal bajo Col1
  4. Sección C-C      — sección transversal bajo Col2
  5. Cuadro de Armadura — tabla con marcas, diámetros, separaciones, cantidades y pesos
Capas DXF: ZAPATA, COLUMNAS, ACERO_LONG_SUP, ACERO_LONG_INF, ACERO_TRANS,
           PERIM_PUNZ, EJES, COTAS, TEXTOS, CUADRO_ARM
"""

import re
import math
from datetime import datetime

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

# DXF color index: 1=red, 2=yellow, 3=green, 4=cyan, 5=blue, 6=magenta, 7=white, 8=dark-gray
_LAYERS = [
    ("ZAPATA",          5,  "Continuous"),
    ("COLUMNAS",        8,  "Continuous"),
    ("ACERO_LONG_SUP",  1,  "Continuous"),
    ("ACERO_LONG_INF",  3,  "Continuous"),
    ("ACERO_TRANS",     6,  "Continuous"),
    ("PERIM_PUNZ",      4,  "DASHED"),
    ("EJES",            4,  "CENTER"),
    ("COTAS",           7,  "Continuous"),
    ("TEXTOS",          7,  "Continuous"),
    ("CUADRO_ARM",      7,  "Continuous"),
]

_BAR_KG_M = {
    8: 0.395, 10: 0.617, 12: 0.888, 16: 1.578,
    20: 2.466, 25: 3.854, 32: 6.313,
}


def _db_mm(varilla: str) -> int:
    m = re.search(r'(\d+)mm', varilla or '')
    return int(m.group(1)) if m else 16

def _db_m(varilla: str) -> float:
    return _db_mm(varilla) / 1000


class GeneradorDXFCombinada:

    def generar(self, ruta: str, motor, norma: str = "ACI318"):
        if not HAS_EZDXF:
            raise RuntimeError("ezdxf no instalado. Ejecute: pip install ezdxf")
        self._motor = motor
        self._norma = norma
        self._ruta  = ruta
        self._build()

    # ══════════════════════════════════════════════════════════════════════════
    # Entry point
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        motor = self._motor
        res   = motor.res
        col1, col2 = motor.col1, motor.col2
        geo   = motor.geo
        B, L  = res.B, res.L
        d1, d2 = res.d1, res.d2
        h, r  = res.h, geo.recubrimiento
        d     = geo.d

        doc = ezdxf.new(dxfversion="R2010")
        doc.header["$INSUNITS"] = 6   # metros

        # ── Layers ──
        for name, color, lt in _LAYERS:
            lyr = doc.layers.add(name)
            lyr.color = color
            try:
                if lt != "Continuous":
                    doc.linetypes.add(lt, pattern=[0.5, 0.125, -0.125])
                lyr.linetype = lt
            except Exception:
                pass

        msp = doc.modelspace()
        GAP = max(1.5, h * 2.5)   # gap between views

        # ── Disposición de vistas ──
        # (0,0)           → planta (L × B)
        # (0, -(h+GAP))   → sección longitudinal A-A
        # (L+GAP, 0)      → sección transversal B-B (Col1)
        # (L+GAP,-(B+GAP))→ sección transversal C-C (Col2)
        # (L+GAP+B+GAP,0) → cuadro de armadura

        self._planta(msp, 0, 0, B, L, d1, d2, col1, col2, d, r, res)
        self._sec_longitudinal(msp, 0, -(h + GAP), L, h, d1, d2, col1, col2, r, res)
        self._sec_transversal(msp, L+GAP, 0,        B, h, col1, r, res,
                               "B-B", "Col1", res.varilla_trans1, res.sep_trans1,
                               res.vol_trans1)
        self._sec_transversal(msp, L+GAP, -(B+GAP), B, h, col2, r, res,
                               "C-C", "Col2", res.varilla_trans2, res.sep_trans2,
                               res.vol_trans2)
        self._cuadro(msp, L + GAP + B + GAP, 0, B, L, h, r, col1, col2, res)

        doc.saveas(self._ruta)

    # ══════════════════════════════════════════════════════════════════════════
    # Primitivos
    # ══════════════════════════════════════════════════════════════════════════

    def _rect(self, msp, ox, oy, w, h, layer):
        pts = [(ox, oy), (ox+w, oy), (ox+w, oy+h), (ox, oy+h), (ox, oy)]
        msp.add_lwpolyline(pts, dxfattribs={"layer": layer})

    def _line(self, msp, x1, y1, x2, y2, layer):
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})

    def _circle(self, msp, cx, cy, radius, layer):
        msp.add_circle((cx, cy), radius, dxfattribs={"layer": layer})

    def _text(self, msp, x, y, txt, h=0.12, layer="TEXTOS"):
        msp.add_text(txt, dxfattribs={"height": h, "layer": layer, "insert": (x, y)})

    def _text_c(self, msp, x, y, txt, h=0.12, layer="TEXTOS"):
        """Text centered horizontally."""
        msp.add_text(txt, dxfattribs={
            "height": h, "layer": layer, "insert": (x, y),
            "halign": 4, "valign": 0, "align_point": (x, y),
        })

    def _dim_h(self, msp, x1, x2, y_dim, y_ref, label, layer="COTAS"):
        """Horizontal dimension line with witness lines and centered label."""
        if abs(x2 - x1) < 1e-6:
            return
        y0, y1_ = (y_ref, y_dim) if y_dim < y_ref else (y_dim, y_ref)
        self._line(msp, x1, y_dim, x2, y_dim, layer)
        self._line(msp, x1, y0,   x1, y1_,   layer)
        self._line(msp, x2, y0,   x2, y1_,   layer)
        arr = abs(x2-x1) * 0.018
        for sx, sign in [(x1, 1), (x2, -1)]:
            self._line(msp, sx, y_dim, sx + sign*arr, y_dim + arr*0.35, layer)
            self._line(msp, sx, y_dim, sx + sign*arr, y_dim - arr*0.35, layer)
        self._text_c(msp, (x1+x2)/2, y_dim - 0.13, label, h=0.11, layer=layer)

    def _dim_v(self, msp, x_dim, y1, y2, x_ref, label, layer="COTAS"):
        """Vertical dimension line."""
        if abs(y2 - y1) < 1e-6:
            return
        x0, x1_ = (x_ref, x_dim) if x_dim < x_ref else (x_dim, x_ref)
        self._line(msp, x_dim, y1, x_dim, y2, layer)
        self._line(msp, x0, y1, x1_, y1, layer)
        self._line(msp, x0, y2, x1_, y2, layer)
        arr = abs(y2-y1) * 0.018
        for sy, sign in [(y1, 1), (y2, -1)]:
            self._line(msp, x_dim, sy, x_dim + arr*0.35, sy + sign*arr, layer)
            self._line(msp, x_dim, sy, x_dim - arr*0.35, sy + sign*arr, layer)
        self._text(msp, x_dim - 0.18, (y1+y2)/2, label, h=0.11, layer=layer)

    # ══════════════════════════════════════════════════════════════════════════
    # 1. Vista en Planta
    # ══════════════════════════════════════════════════════════════════════════

    def _planta(self, msp, ox, oy, B, L, d1, d2, col1, col2, d, r, res):
        # Zapata
        self._rect(msp, ox, oy, L, B, "ZAPATA")

        # Ejes de columnas
        for xc in [d1, d2]:
            self._line(msp, ox+xc, oy-0.3, ox+xc, oy+B+0.3, "EJES")
        self._line(msp, ox-0.3, oy+B/2, ox+L+0.3, oy+B/2, "EJES")

        # Columnas + perímetros punzonado
        for xc, col, lbl in [(d1, col1, "Col1"), (d2, col2, "Col2")]:
            self._rect(msp, ox+xc-col.ancho/2, oy+B/2-col.largo/2,
                       col.ancho, col.largo, "COLUMNAS")
            self._rect(msp, ox+xc-(col.ancho+d)/2, oy+B/2-(col.largo+d)/2,
                       col.ancho+d, col.largo+d, "PERIM_PUNZ")
            self._text(msp, ox+xc-col.ancho/2,
                       oy+B/2+col.largo/2+0.06,
                       f"{lbl}  {col.ancho*100:.0f}x{col.largo*100:.0f} cm",
                       h=0.13, layer="TEXTOS")

        # ── Barras long. superiores (líneas horizontales a lo largo de L) ──
        db_A = _db_m(res.varilla_long_top)
        sep_A = res.sep_long_top
        n_A = res.n_long_top
        y0_A = oy + r + db_A / 2
        for i in range(n_A):
            yb = y0_A + i * sep_A
            if yb <= oy + B - r:
                self._line(msp, ox, yb, ox + L, yb, "ACERO_LONG_SUP")

        # ── Barras transversales (líneas verticales en franja de cada columna) ──
        for xc, col, sep_t, var_t in [
            (d1, col1, res.sep_trans1, res.varilla_trans1),
            (d2, col2, res.sep_trans2, res.varilla_trans2),
        ]:
            strip_w = col.ancho + 2 * min(res.vol_trans1, 0.40)
            n_t = max(3, int(strip_w / sep_t) + 1)
            x0_t = ox + xc - strip_w / 2
            for i in range(n_t):
                xb = x0_t + i * sep_t
                if ox <= xb <= ox + L:
                    self._line(msp, xb, oy, xb, oy + B, "ACERO_TRANS")

        # ── Leyenda de barras ──
        lx = ox + L + 0.15
        for i, (mark, desc, var, sep) in enumerate([
            ("A", "Long. superior", res.varilla_long_top, res.sep_long_top),
            ("C", "Trans. Col1",    res.varilla_trans1,   res.sep_trans1),
            ("D", "Trans. Col2",    res.varilla_trans2,   res.sep_trans2),
        ]):
            self._text(msp, lx, oy + B - 0.25 - i*0.28,
                       f"({mark}) {var} @ {sep*100:.0f} cm — {desc}",
                       h=0.12, layer="TEXTOS")

        # ── Cotas ──
        self._dim_h(msp, ox, ox+L,  oy-0.45, oy, f"L = {L:.2f} m",  "COTAS")
        self._dim_h(msp, ox, ox+d1, oy-0.85, oy, f"{d1:.3f} m",     "COTAS")
        self._dim_h(msp, ox+d1, ox+d2, oy-0.85, oy,
                    f"L_entre = {d2-d1:.2f} m", "COTAS")
        self._dim_h(msp, ox+d2, ox+L, oy-0.85, oy, f"{L-d2:.3f} m", "COTAS")
        self._dim_v(msp, ox-0.45, oy, oy+B, ox, f"B = {B:.2f} m",   "COTAS")

        # ── Indicadores de corte ──
        for xpos in [ox-0.1, ox+L+0.05]:
            self._text(msp, xpos, oy-0.05, "A", h=0.20, layer="TEXTOS")
            self._line(msp, ox, oy-0.05, ox+L, oy-0.05, "TEXTOS")

        # ── Título ──
        self._text_c(msp, ox+L/2, oy+B+0.45, "VISTA EN PLANTA", h=0.20, layer="TEXTOS")

    # ══════════════════════════════════════════════════════════════════════════
    # 2. Sección Longitudinal A-A
    # ══════════════════════════════════════════════════════════════════════════

    def _sec_longitudinal(self, msp, ox, oy, L, h, d1, d2, col1, col2, r, res):
        # Zapata
        self._rect(msp, ox, oy, L, h, "ZAPATA")

        # Stub columnas
        stub = 0.5
        for xc, col in [(d1, col1), (d2, col2)]:
            self._rect(msp, ox+xc-col.ancho/2, oy+h, col.ancho, stub, "COLUMNAS")
            self._line(msp, ox+xc, oy, ox+xc, oy+h, "EJES")

        # Líneas de cubierta (referencias)
        self._line(msp, ox+r, oy+r,   ox+L-r, oy+r,   "EJES")
        self._line(msp, ox+r, oy+h-r, ox+L-r, oy+h-r, "EJES")

        # ── Barras Superiores (círculos en sección) ──
        db_A = _db_m(res.varilla_long_top)
        y_A  = oy + h - r - db_A / 2
        sep_A = res.sep_long_top
        n_A  = min(res.n_long_top, 30)
        x0   = ox + r + db_A / 2
        shown_A = 0
        for i in range(n_A):
            xb = x0 + i * sep_A
            if xb <= ox + L - r:
                self._circle(msp, xb, y_A, db_A / 2, "ACERO_LONG_SUP")
                shown_A += 1

        # ── Barras Inferiores ──
        db_B = _db_m(res.varilla_long_bot)
        y_B  = oy + r + db_B / 2
        sep_B = res.sep_long_bot
        n_B  = min(res.n_long_bot, 35)
        for i in range(n_B):
            xb = x0 + i * sep_B
            if xb <= ox + L - r:
                self._circle(msp, xb, y_B, db_B / 2, "ACERO_LONG_INF")

        # ── Anotaciones de barras ──
        annot_x = ox + L + 0.12
        self._line(msp, ox+L, y_A, annot_x-0.02, y_A, "TEXTOS")
        self._text(msp, annot_x, y_A - 0.05,
                   f"(A) {res.varilla_long_top} @ {res.sep_long_top*100:.0f}cm",
                   h=0.12, layer="ACERO_LONG_SUP")
        self._line(msp, ox+L, y_B, annot_x-0.02, y_B, "TEXTOS")
        self._text(msp, annot_x, y_B - 0.05,
                   f"(B) {res.varilla_long_bot} @ {res.sep_long_bot*100:.0f}cm",
                   h=0.12, layer="ACERO_LONG_INF")

        # Recubrimiento
        self._text(msp, ox + 0.02, oy + r/2, f"r={r*100:.0f}cm", h=0.10, layer="TEXTOS")

        # ── Cotas ──
        self._dim_h(msp, ox, ox+L,  oy-0.40, oy, f"L = {L:.2f} m",    "COTAS")
        self._dim_h(msp, ox, ox+d1, oy-0.80, oy, f"{d1:.3f} m",       "COTAS")
        self._dim_h(msp, ox+d1, ox+d2, oy-0.80, oy, f"{d2-d1:.2f} m", "COTAS")
        self._dim_h(msp, ox+d2, ox+L,  oy-0.80, oy, f"{L-d2:.3f} m",  "COTAS")
        self._dim_v(msp, ox-0.40, oy, oy+h, ox, f"h = {h:.2f} m",     "COTAS")
        self._dim_v(msp, ox-0.75, oy, y_B, ox,  f"r={r*100:.0f}cm",    "COTAS")

        # ── Título ──
        self._text_c(msp, ox+L/2, oy-1.10, "SECCIÓN A-A  (Longitudinal)", h=0.18, layer="TEXTOS")

    # ══════════════════════════════════════════════════════════════════════════
    # 3 & 4. Sección Transversal (B-B o C-C)
    # ══════════════════════════════════════════════════════════════════════════

    def _sec_transversal(self, msp, ox, oy, B, h, col,
                          r, res, code, col_label, varilla_t, sep_t, vol_t):
        # Zapata
        self._rect(msp, ox, oy, B, h, "ZAPATA")

        # Columna stub (centrada en B)
        stub = 0.5
        cx0 = ox + (B - col.largo) / 2
        self._rect(msp, cx0, oy+h, col.largo, stub, "COLUMNAS")
        self._line(msp, ox+B/2, oy, ox+B/2, oy+h, "EJES")

        # Líneas de cubierta
        self._line(msp, ox+r, oy+r,   ox+B-r, oy+r,   "EJES")
        self._line(msp, ox+r, oy+h-r, ox+B-r, oy+h-r, "EJES")

        # ── Barras transversales (visión en sección = círculos a lo largo de B) ──
        db_t = _db_m(varilla_t)
        y_t  = oy + h - r - db_t / 2
        n_t  = max(3, int((B - 2*r) / sep_t) + 1)
        x0_t = ox + r + db_t / 2
        for i in range(n_t):
            xb = x0_t + i * sep_t
            if xb <= ox + B - r:
                self._circle(msp, xb, y_t, db_t / 2, "ACERO_TRANS")

        # ── Barras long. superiores e inferiores (perpendiculares a sección = círculos) ──
        db_A = _db_m(res.varilla_long_top)
        db_B = _db_m(res.varilla_long_bot)
        for y_bar, db, layer in [
            (oy + h - r - db_A / 2, db_A, "ACERO_LONG_SUP"),
            (oy + r + db_B / 2,     db_B, "ACERO_LONG_INF"),
        ]:
            # Mostrar 2 barras extremas y línea indicativa entre ellas
            self._circle(msp, ox + r + db/2,     y_bar, db/2, layer)
            self._circle(msp, ox + B - r - db/2, y_bar, db/2, layer)
            self._line(msp, ox+r+db, y_bar, ox+B-r-db, y_bar, layer)

        # ── Anotaciones ──
        ann_x = ox + B + 0.12
        self._line(msp, ox+B, y_t, ann_x-0.02, y_t, "TEXTOS")
        self._text(msp, ann_x, y_t - 0.05,
                   f"(C/D) {varilla_t} @ {sep_t*100:.0f}cm  (trans.)",
                   h=0.12, layer="ACERO_TRANS")
        self._text(msp, ox + 0.02, oy + r/2, f"r={r*100:.0f}cm", h=0.10, layer="TEXTOS")

        # ── Cotas ──
        self._dim_h(msp, ox, ox+B, oy-0.40, oy, f"B = {B:.2f} m", "COTAS")
        # Voladizo | columna | voladizo
        self._dim_h(msp, ox,  ox+vol_t,          oy-0.80, oy, f"vol={vol_t:.2f}", "COTAS")
        self._dim_h(msp, ox+vol_t, ox+vol_t+col.largo, oy-0.80, oy,
                    f"{col.largo:.2f} m", "COTAS")
        self._dim_h(msp, ox+vol_t+col.largo, ox+B, oy-0.80, oy,
                    f"vol={vol_t:.2f}", "COTAS")
        self._dim_v(msp, ox-0.40, oy, oy+h, ox, f"h = {h:.2f} m", "COTAS")

        # ── Título ──
        self._text_c(msp, ox+B/2, oy+h+stub+0.25,
                     f"SECCIÓN {code} — {col_label}", h=0.17, layer="TEXTOS")

    # ══════════════════════════════════════════════════════════════════════════
    # 5. Cuadro de Armadura
    # ══════════════════════════════════════════════════════════════════════════

    def _cuadro(self, msp, ox, oy, B, L, h, r, col1, col2, res):
        T = 0.34   # row height
        # Rule: col_width >= len(header) * 0.09m + 0.14m margin
        # Using single-word short headers to minimize required width
        # M | Descripcion | Ø(mm) | sep(cm) | L(m) | n | kg/m | Total(kg)
        cw   = [0.28, 1.40, 0.36, 0.52, 0.52, 0.30, 0.54, 0.76]
        hdrs = ["M",  "Descripcion", "Ø(mm)", "sep(cm)", "L(m)", "n", "kg/m", "Total(kg)"]
        total_w = sum(cw)

        db_A = _db_mm(res.varilla_long_top);  db_B = _db_mm(res.varilla_long_bot)
        db_C = _db_mm(res.varilla_trans1);    db_D = _db_mm(res.varilla_trans2)

        len_A = round(L + 2 * 0.10, 2)
        len_B = round(L + 2 * 0.10, 2)
        len_C = round(B + 2 * 0.10, 2)
        len_D = round(B + 2 * 0.10, 2)

        strip1 = col1.ancho + 2 * min(float(res.vol_trans1), 0.40)
        strip2 = col2.ancho + 2 * min(float(res.vol_trans2), 0.40)
        n_C = max(2, int(strip1 / res.sep_trans1) + 1)
        n_D = max(2, int(strip2 / res.sep_trans2) + 1)

        def wperm(db): return _BAR_KG_M.get(db, 1.578)

        rows = [
            ("A", "Long. Superior",  db_A, res.sep_long_top*100, len_A, res.n_long_top, wperm(db_A)),
            ("B", "Long. Inferior",  db_B, res.sep_long_bot*100, len_B, res.n_long_bot, wperm(db_B)),
            ("C", "Trans. Col1",     db_C, res.sep_trans1*100,   len_C, n_C,             wperm(db_C)),
            ("D", "Trans. Col2",     db_D, res.sep_trans2*100,   len_D, n_D,             wperm(db_D)),
        ]

        # Title
        self._text(msp, ox, oy + 0.15, "CUADRO DE ARMADURA", h=0.20, layer="CUADRO_ARM")

        y = oy - 0.10  # start y of table (going down)

        def draw_row(vals, y_top, bold=False):
            x = ox
            self._line(msp, ox, y_top, ox+total_w, y_top, "CUADRO_ARM")
            for val, w in zip(vals, cw):
                self._line(msp, x, y_top, x, y_top-T, "CUADRO_ARM")
                self._text(msp, x+0.07, y_top-T+0.10, str(val),
                           h=0.09 if not bold else 0.10, layer="CUADRO_ARM")
                x += w
            self._line(msp, ox+total_w, y_top, ox+total_w, y_top-T, "CUADRO_ARM")
            self._line(msp, ox, y_top-T, ox+total_w, y_top-T, "CUADRO_ARM")
            return y_top - T

        y = draw_row(hdrs, y, bold=True)

        total_kg = 0.0
        for mark, desc, db, sep, length, n, wpm in rows:
            kg = float(n) * length * wpm
            total_kg += kg
            y = draw_row([mark, desc, db, f"{sep:.0f}", f"{length:.2f}",
                          n, f"{wpm:.3f}", f"{kg:.1f}"], y)

        # Total row
        y = draw_row(["", "TOTAL ACERO", "", "", "", "", "",
                      f"{total_kg:.1f} kg"], y, bold=True)

        # Info block
        y -= 0.20
        motor = self._motor
        info = [
            f"FundaCalc — Zapata Combinada Rectangular",
            f"Norma: {self._norma}",
            f"Col1: Pd={motor.col1.Pd:.0f} kN | Pl={motor.col1.Pl:.0f} kN | "
            f"{motor.col1.ancho*100:.0f}x{motor.col1.largo*100:.0f} cm",
            f"Col2: Pd={motor.col2.Pd:.0f} kN | Pl={motor.col2.Pl:.0f} kN | "
            f"{motor.col2.ancho*100:.0f}x{motor.col2.largo*100:.0f} cm",
            f"B = {B:.2f} m  |  L = {L:.2f} m  |  h = {h:.2f} m",
            f"f'c = {motor.hormigon.fck:.0f} MPa  |  fy = {motor.acero.fy:.0f} MPa  |  "
            f"recubrimiento = {r*100:.0f} cm",
            f"q_max = {motor.res.q_max:.1f} kN/m² ≤ qa = {motor.suelo.qa:.1f} kN/m²",
            f"Generado: {datetime.now():%d/%m/%Y  %H:%M}",
        ]
        for line in info:
            self._text(msp, ox, y, line, h=0.12, layer="CUADRO_ARM")
            y -= 0.22
