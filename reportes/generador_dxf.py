"""
Generador DXF para Zapata Aislada.
Produce:
  - Vista en planta con barras X e Y individuales a escala real
  - Sección transversal con barras representadas (línea + círculos)
  - Cuadro de armadura con especificaciones calculadas
"""

import re
from datetime import datetime
from core.zapata_aislada import GeometriaZapata, Columna, ResultadosZapata

try:
    import ezdxf
except ImportError:
    ezdxf = None


def _parse_db(varilla: str) -> float:
    """'Ø16mm' → 0.016 m"""
    if not varilla:
        return 0.012
    m = re.search(r'(\d+)', varilla)
    return int(m.group(1)) / 1000.0 if m else 0.012


class GeneradorDXF:

    def generar(self, ruta: str, geo: GeometriaZapata, columna: Columna,
                resultado: ResultadosZapata, norma: str):
        if ezdxf:
            self._generar_con_ezdxf(ruta, geo, columna, resultado, norma)
        else:
            self._generar_dxf_basico(ruta, geo, columna, resultado, norma)

    # ── ezdxf version ────────────────────────────────────────────────────────

    def _generar_con_ezdxf(self, ruta: str, geo: GeometriaZapata, columna: Columna,
                            resultado: ResultadosZapata, norma: str):
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        # layers
        layer_defs = {
            "ZAPATA":    5,
            "COLUMNA":   8,
            "PUNZONADO": 1,
            "ACERO_X":   1,
            "ACERO_Y":   6,
            "COTAS":     7,
            "TEXTOS":    7,
        }
        for name, color in layer_defs.items():
            if name not in doc.layers:
                doc.layers.new(name, dxfattribs={"color": color})

        B, L, h = geo.B, geo.L, geo.h
        r  = geo.recubrimiento
        d  = geo.d
        cx = columna.ancho
        cy = columna.largo

        sep_x  = resultado.separacion_x
        sep_y  = resultado.separacion_y
        var_x  = resultado.varilla_x  or "—"
        var_y  = resultado.varilla_y  or "—"
        As_x   = resultado.As_x_diseno
        As_y   = resultado.As_y_diseno
        db_x   = _parse_db(var_x)
        db_y   = _parse_db(var_y)

        # ── PLANTA ───────────────────────────────────────────────────────────
        ox, oy = 0.0, 0.0

        # contorno zapata
        self._rect(msp, ox, oy, B, L, "ZAPATA", 5)

        # columna
        self._rect(msp, ox + (B - cx)/2, oy + (L - cy)/2, cx, cy, "COLUMNA", 8)

        # perímetro punzonado (d/2)
        pw = cx + d;  ph = cy + d
        self._rect(msp, ox + (B - pw)/2, oy + (L - ph)/2, pw, ph, "PUNZONADO", 1)

        # barras X: líneas horizontales (corren en dirección B), espaciadas sep_x en Y
        if sep_x > 0:
            y = oy + r
            while y <= oy + L - r + 1e-6:
                self._line(msp, ox + r, y, ox + B - r, y, "ACERO_X")
                y += sep_x

        # barras Y: líneas verticales (corren en dirección L), espaciadas sep_y en X
        if sep_y > 0:
            x = ox + r
            while x <= ox + B - r + 1e-6:
                self._line(msp, x, oy + r, x, oy + L - r, "ACERO_Y")
                x += sep_y

        # cotas planta
        self._cota_h(msp, ox, ox + B, oy - 0.35, oy, f"B = {B:.2f} m")
        self._cota_v(msp, oy, oy + L, ox - 0.35, ox, f"L = {L:.2f} m")

        # leyenda barras en planta
        lx = ox + B + 0.25
        self._text(msp, lx, oy + L - 0.0,  f"Arm. X (—):  {var_x} @ {sep_x*100:.0f} cm   As={As_x:.2f} cm²/m", 0.10, "TEXTOS")
        self._text(msp, lx, oy + L - 0.18, f"Arm. Y ( | ): {var_y} @ {sep_y*100:.0f} cm   As={As_y:.2f} cm²/m", 0.10, "TEXTOS")

        # ── SECCIÓN TRANSVERSAL ──────────────────────────────────────────────
        # Corte a lo largo de B (dirección X): las barras X se ven como línea,
        # las barras Y se ven como círculos (cortadas en su sección)
        sx = ox                 # alineada horizontalmente con la planta
        sy = oy + L + 1.20      # debajo de la planta con separación

        y_acero = sy + h - d    # cara inferior: recubrimiento + radio_barra desde abajo

        # contorno zapata
        self._rect(msp, sx, sy, B, h, "ZAPATA", 5)

        # stub de columna (altura representativa 0.4 m)
        self._rect(msp, sx + (B - cx)/2, sy + h, cx, 0.40, "COLUMNA", 8)

        # línea barra X (corre a lo largo de B, se ve como línea en esta sección)
        self._line(msp, sx + r, y_acero, sx + B - r, y_acero, "ACERO_X")

        # círculos para barras Y (perpendiculares al corte)
        if sep_y > 0 and db_y > 0:
            rad = db_y / 2.0
            x = sx + r
            while x <= sx + B - r + 1e-6:
                msp.add_circle((x, y_acero), rad,
                               dxfattribs={"layer": "ACERO_Y", "color": 6})
                x += sep_y

        # cota de recubrimiento en sección
        self._cota_v(msp, sy, y_acero, sx - 0.30, sx, f"r={r*100:.0f}cm")
        self._cota_v(msp, sy, sy + h,  sx + B + 0.25, sx + B, f"h={h:.2f}m")

        # etiqueta sección
        self._text(msp, sx, sy - 0.22, "SECCIÓN A-A  (corte por eje B)", 0.12, "TEXTOS")
        self._text(msp, sx, sy - 0.38, f"Arm. X: {var_x} @ {sep_x*100:.0f} cm    (línea verde)", 0.09, "TEXTOS")
        self._text(msp, sx, sy - 0.52, f"Arm. Y: {var_y} @ {sep_y*100:.0f} cm    (círculos magenta)", 0.09, "TEXTOS")

        # ── CUADRO DE ARMADURA ───────────────────────────────────────────────
        tx = ox
        ty = sy + h + 0.90

        encabezado = [
            ("FundaCalc — Zapata Aislada", 0.14),
            (f"Norma: {norma}    Fecha: {datetime.now():%d/%m/%Y %H:%M}", 0.10),
            (f"B = {B:.2f} m    L = {L:.2f} m    h = {h:.2f} m    d = {d:.3f} m", 0.10),
            (f"Recubrimiento = {r*100:.1f} cm", 0.10),
        ]
        for i, (txt, ht) in enumerate(encabezado):
            self._text(msp, tx, ty + i*0.18, txt, ht, "TEXTOS")

        ty2 = ty + len(encabezado) * 0.18 + 0.20
        filas = [
            ("CUADRO DE ARMADURA INFERIOR", 0.12),
            (f"Dirección X  (paralela a B):  {var_x} @ {sep_x*100:.0f} cm    As = {As_x:.2f} cm²/m", 0.10),
            (f"Dirección Y  (paralela a L):  {var_y} @ {sep_y*100:.0f} cm    As = {As_y:.2f} cm²/m", 0.10),
        ]
        for i, (txt, ht) in enumerate(filas):
            self._text(msp, tx, ty2 + i*0.18, txt, ht, "TEXTOS")

        doc.saveas(ruta)

    # ── primitivos ───────────────────────────────────────────────────────────

    def _rect(self, msp, x, y, w, h, layer, color):
        msp.add_lwpolyline(
            [(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)],
            dxfattribs={"layer": layer, "color": color},
        )

    def _line(self, msp, x1, y1, x2, y2, layer):
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})

    def _text(self, msp, x, y, txt, h=0.12, layer="TEXTOS"):
        msp.add_text(txt, dxfattribs={"height": h, "layer": layer, "insert": (x, y)})

    def _cota_h(self, msp, x1, x2, y_cota, y_ref, label):
        """Cota horizontal con líneas de referencia y texto centrado."""
        arr = abs(x2 - x1) * 0.02
        self._line(msp, x1, y_cota, x2, y_cota, "COTAS")
        self._line(msp, x1, y_ref,  x1, y_cota, "COTAS")
        self._line(msp, x2, y_ref,  x2, y_cota, "COTAS")
        self._line(msp, x1, y_cota, x1 + arr, y_cota + arr*0.4, "COTAS")
        self._line(msp, x2, y_cota, x2 - arr, y_cota + arr*0.4, "COTAS")
        mx = (x1 + x2) / 2
        self._text(msp, mx - len(label)*0.035, y_cota - 0.18, label, 0.10, "COTAS")

    def _cota_v(self, msp, y1, y2, x_cota, x_ref, label):
        """Cota vertical con líneas de referencia y texto."""
        arr = abs(y2 - y1) * 0.04
        self._line(msp, x_cota, y1, x_cota, y2, "COTAS")
        self._line(msp, x_ref,  y1, x_cota, y1, "COTAS")
        self._line(msp, x_ref,  y2, x_cota, y2, "COTAS")
        self._line(msp, x_cota, y1, x_cota + arr*0.4, y1 + arr, "COTAS")
        self._line(msp, x_cota, y2, x_cota + arr*0.4, y2 - arr, "COTAS")
        my = (y1 + y2) / 2
        self._text(msp, x_cota - 0.35, my, label, 0.10, "COTAS")

    # ── fallback básico ASCII ────────────────────────────────────────────────

    def _generar_dxf_basico(self, ruta: str, geo: GeometriaZapata, columna: Columna,
                             resultado: ResultadosZapata, norma: str):
        lines = [
            "0", "SECTION", "2", "HEADER",
            "9", "$ACADVER", "1", "AC1021",
            "0", "ENDSEC",
            "0", "SECTION", "2", "TABLES",
            "0", "ENDSEC",
            "0", "SECTION", "2", "BLOCKS",
            "0", "ENDSEC",
            "0", "SECTION", "2", "ENTITIES",
        ]

        def poly(vertices, layer="0", closed=True):
            lines.extend(["0", "LWPOLYLINE", "8", layer,
                           "90", str(len(vertices)), "70", "1" if closed else "0"])
            for x, y in vertices:
                lines.extend(["10", f"{x:.6f}", "20", f"{y:.6f}"])

        def txt(t, x, y, h=0.12, layer="0"):
            lines.extend(["0", "TEXT", "8", layer,
                           "10", f"{x:.6f}", "20", f"{y:.6f}", "40", f"{h:.6f}", "1", t])

        B, L, h = geo.B, geo.L, geo.h
        r = geo.recubrimiento
        d = geo.d
        cx, cy = columna.ancho, columna.largo
        sep_x = resultado.separacion_x
        sep_y = resultado.separacion_y
        var_x = resultado.varilla_x or "?"
        var_y = resultado.varilla_y or "?"

        # planta
        poly([(0,0),(B,0),(B,L),(0,L)], "ZAPATA")
        poly([(( B-cx)/2,(L-cy)/2),((B+cx)/2,(L-cy)/2),
              ((B+cx)/2,(L+cy)/2),((B-cx)/2,(L+cy)/2)], "COLUMNA")

        # barras X en planta
        if sep_x > 0:
            y = r
            while y <= L - r + 1e-6:
                poly([(r, y),(B-r, y)], "ACERO_X", closed=False)
                y += sep_x

        # barras Y en planta
        if sep_y > 0:
            x = r
            while x <= B - r + 1e-6:
                poly([(x, r),(x, L-r)], "ACERO_Y", closed=False)
                x += sep_y

        # sección
        sx = 0.0;  sy = L + 1.0
        y_acero = sy + h - d
        poly([(sx,sy),(sx+B,sy),(sx+B,sy+h),(sx,sy+h)], "ZAPATA")
        poly([(sx+(B-cx)/2, sy+h),(sx+(B+cx)/2, sy+h),
              (sx+(B+cx)/2, sy+h+0.4),(sx+(B-cx)/2, sy+h+0.4)], "COLUMNA")
        poly([(sx+r, y_acero),(sx+B-r, y_acero)], "ACERO_X", closed=False)

        # textos
        txt("FundaCalc — Zapata Aislada", 0.0, -0.4, 0.14, "TEXTOS")
        txt(f"Norma: {norma}", 0.0, -0.65, 0.10, "TEXTOS")
        txt(f"B={B:.2f}m  L={L:.2f}m  h={h:.2f}m", 0.0, -0.85, 0.10, "TEXTOS")
        txt(f"Arm.X: {var_x} @ {sep_x*100:.0f}cm  As={resultado.As_x_diseno:.2f}cm2/m", 0.0, -1.05, 0.10, "TEXTOS")
        txt(f"Arm.Y: {var_y} @ {sep_y*100:.0f}cm  As={resultado.As_y_diseno:.2f}cm2/m", 0.0, -1.25, 0.10, "TEXTOS")
        txt(f"Fecha: {datetime.now():%d/%m/%Y %H:%M}", 0.0, -1.45, 0.10, "TEXTOS")

        lines.extend(["0", "ENDSEC", "0", "EOF"])
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
