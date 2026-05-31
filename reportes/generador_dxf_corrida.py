"""
Generador DXF para Zapata Corrida.
Produce:
  - Vista en planta (franja de 1 m de muro con barras)
  - Sección transversal con armadura
  - Cuadro de armadura
"""

import re
from datetime import datetime

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


class GeneradorDXFCorrida:

    def generar(self, ruta: str, motor, norma: str):
        if ezdxf:
            self._generar_con_ezdxf(ruta, motor, norma)
        else:
            self._generar_dxf_basico(ruta, motor, norma)

    # ── ezdxf version ────────────────────────────────────────────────────────

    def _generar_con_ezdxf(self, ruta: str, motor, norma: str):
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        layer_defs = {
            "ZAPATA":    5,
            "MURO":      8,
            "ACERO_T":   1,   # transversal (⊥ muro) — rojo
            "ACERO_L":   6,   # longitudinal (‖ muro) — magenta
            "COTAS":     7,
            "TEXTOS":    7,
        }
        for name, color in layer_defs.items():
            if name not in doc.layers:
                doc.layers.new(name, dxfattribs={"color": color})

        res  = motor.res
        geo  = motor.geo
        muro = motor.muro
        B    = res.B
        h    = res.h
        d    = geo.d
        r    = geo.recubrimiento
        t    = muro.espesor
        sep_t = res.separacion
        sep_l = res.sep_long
        var_t = res.varilla or "—"
        var_l = res.varilla_long or "—"
        db_t  = _parse_db(var_t)
        db_l  = _parse_db(var_l)

        # Se dibuja una franja de largo_ref = 1.0 m de muro
        LARGO = 1.0   # 1 metro de muro representativo

        # ── PLANTA ──────────────────────────────────────────────────────────
        ox, oy = 0.0, 0.0

        # Contorno zapata (vista superior, franja de 1 m)
        self._rect(msp, ox, oy, LARGO, B, "ZAPATA", 5)

        # Muro en planta
        mx = ox
        my = oy + (B - t) / 2
        self._rect(msp, mx, my, LARGO, t, "MURO", 8)

        # Barras transversales en planta (líneas paralelas al eje B)
        if sep_t > 0:
            x = ox + r
            while x <= ox + LARGO - r + 1e-6:
                self._line(msp, x, oy + r, x, oy + B - r, "ACERO_T")
                x += sep_t

        # Barras longitudinales en planta
        if sep_l > 0:
            y = oy + r
            while y <= oy + B - r + 1e-6:
                self._line(msp, ox + r, y, ox + LARGO - r, y, "ACERO_L")
                y += sep_l

        # Cotas planta
        self._cota_v(msp, oy, oy + B, ox - 0.35, ox, f"B={B:.2f}m")
        self._cota_h(msp, ox, ox + LARGO, oy - 0.35, oy, "1.00 m (repr.)")

        # Leyenda planta
        lx = ox + LARGO + 0.25
        self._text(msp, lx, oy + B,        f"Arm. Trans. (|): {var_t} @ {sep_t*100:.0f} cm", 0.10, "TEXTOS")
        self._text(msp, lx, oy + B - 0.18, f"Arm. Long.  (—): {var_l} @ {sep_l*100:.0f} cm", 0.10, "TEXTOS")

        # ── SECCIÓN TRANSVERSAL ─────────────────────────────────────────────
        # Corte perpendicular al muro (vista en dirección B)
        sx = ox
        sy = oy + B + 1.20

        y_acero = sy + r + db_t / 2.0   # acero en cara inferior

        # Contorno zapata en sección
        self._rect(msp, sx, sy, B, h, "ZAPATA", 5)

        # Stub del muro (arriba de la zapata)
        self._rect(msp, sx + (B - t) / 2, sy + h, t, 0.40, "MURO", 8)

        # Línea armadura transversal (corre perpendicular al plano de corte → se ve como línea)
        self._line(msp, sx + r, y_acero, sx + B - r, y_acero, "ACERO_T")

        # Círculos para barras longitudinales (paralelas al muro → perpendiculares al corte)
        if sep_l > 0 and db_l > 0:
            rad = db_l / 2.0
            x = sx + r
            while x <= sx + B - r + 1e-6:
                msp.add_circle((x, y_acero), rad,
                               dxfattribs={"layer": "ACERO_L", "color": 6})
                x += sep_l

        # Cotas sección
        self._cota_v(msp, sy, y_acero, sx - 0.30, sx, f"r={r*100:.0f}cm")
        self._cota_v(msp, sy, sy + h,  sx + B + 0.25, sx + B, f"h={h:.2f}m")
        self._cota_h(msp, sx, sx + B,  sy - 0.35, sy, f"B={B:.2f}m")
        self._cota_h(msp, sx + (B - t) / 2, sx + (B + t) / 2,
                     sy - 0.60, sy, f"t={t:.2f}m")

        # Etiqueta sección
        self._text(msp, sx, sy - 0.80, "SECCIÓN  (corte ⊥ al muro)", 0.12, "TEXTOS")
        self._text(msp, sx, sy - 0.98, f"Arm. Trans.: {var_t} @ {sep_t*100:.0f} cm  (línea roja)", 0.09, "TEXTOS")
        self._text(msp, sx, sy - 1.12, f"Arm. Long.:  {var_l} @ {sep_l*100:.0f} cm  (círculos magenta)", 0.09, "TEXTOS")

        # ── CUADRO DE ARMADURA ───────────────────────────────────────────────
        tx = ox
        ty = sy + h + 0.90

        encabezado = [
            ("FundaCalc — Zapata Corrida", 0.14),
            (f"Norma: {norma}    Fecha: {datetime.now():%d/%m/%Y %H:%M}", 0.10),
            (f"B = {B:.2f} m    h = {h:.2f} m    d = {geo.d:.3f} m    Recubrimiento = {r*100:.1f} cm", 0.10),
            (f"Muro espesor = {t:.2f} m    Voladizo a = {res.a:.3f} m", 0.10),
        ]
        for i, (txt, ht) in enumerate(encabezado):
            self._text(msp, tx, ty + i * 0.18, txt, ht, "TEXTOS")

        ty2 = ty + len(encabezado) * 0.18 + 0.20
        filas = [
            ("CUADRO DE ARMADURA  (por metro lineal de muro)", 0.12),
            (f"Arm. Transversal (⊥ muro):  {var_t} @ {sep_t*100:.0f} cm    As = {res.As_diseno:.2f} cm²/m", 0.10),
            (f"Arm. Longitudinal (‖ muro): {var_l} @ {sep_l*100:.0f} cm    As = {res.As_long:.2f} cm²/m", 0.10),
            (f"Momento último Mu = {res.Mu:.2f} kN·m/m    Cortante Vu = {res.Vu:.2f} kN/m", 0.09),
        ]
        for i, (txt, ht) in enumerate(filas):
            self._text(msp, tx, ty2 + i * 0.18, txt, ht, "TEXTOS")

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
        arr = abs(x2 - x1) * 0.03
        self._line(msp, x1, y_cota, x2, y_cota, "COTAS")
        self._line(msp, x1, y_ref,  x1, y_cota, "COTAS")
        self._line(msp, x2, y_ref,  x2, y_cota, "COTAS")
        self._line(msp, x1, y_cota, x1 + arr, y_cota + arr * 0.4, "COTAS")
        self._line(msp, x2, y_cota, x2 - arr, y_cota + arr * 0.4, "COTAS")
        mx = (x1 + x2) / 2
        self._text(msp, mx - len(label) * 0.035, y_cota - 0.18, label, 0.10, "COTAS")

    def _cota_v(self, msp, y1, y2, x_cota, x_ref, label):
        arr = abs(y2 - y1) * 0.04
        self._line(msp, x_cota, y1, x_cota, y2, "COTAS")
        self._line(msp, x_ref,  y1, x_cota, y1, "COTAS")
        self._line(msp, x_ref,  y2, x_cota, y2, "COTAS")
        self._line(msp, x_cota, y1, x_cota + arr * 0.4, y1 + arr, "COTAS")
        self._line(msp, x_cota, y2, x_cota + arr * 0.4, y2 - arr, "COTAS")
        my = (y1 + y2) / 2
        self._text(msp, x_cota - 0.35, my, label, 0.10, "COTAS")

    # ── fallback básico ───────────────────────────────────────────────────────

    def _generar_dxf_basico(self, ruta: str, motor, norma: str):
        res = motor.res
        B = res.B
        h = res.h
        t = motor.muro.espesor
        r = motor.geo.recubrimiento
        sep_t = res.separacion
        sep_l = res.sep_long
        var_t = res.varilla or "?"
        var_l = res.varilla_long or "?"
        LARGO = 1.0

        lines = [
            "0", "SECTION", "2", "HEADER",
            "9", "$ACADVER", "1", "AC1021",
            "0", "ENDSEC",
            "0", "SECTION", "2", "ENTITIES",
        ]

        def poly(vertices, layer="0", closed=True):
            lines.extend(["0", "LWPOLYLINE", "8", layer,
                           "90", str(len(vertices)), "70", "1" if closed else "0"])
            for x, y in vertices:
                lines.extend(["10", f"{x:.6f}", "20", f"{y:.6f}"])

        def txt(t_str, x, y, ht=0.12, layer="0"):
            lines.extend(["0", "TEXT", "8", layer,
                           "10", f"{x:.6f}", "20", f"{y:.6f}",
                           "40", f"{ht:.6f}", "1", t_str])

        # planta
        poly([(0, 0), (LARGO, 0), (LARGO, B), (0, B)], "ZAPATA")
        poly([(0, (B-t)/2), (LARGO, (B-t)/2),
              (LARGO, (B+t)/2), (0, (B+t)/2)], "MURO")

        if sep_t > 0:
            x = r
            while x <= LARGO - r + 1e-6:
                poly([(x, r), (x, B-r)], "ACERO_T", closed=False)
                x += sep_t

        if sep_l > 0:
            y = r
            while y <= B - r + 1e-6:
                poly([(r, y), (LARGO-r, y)], "ACERO_L", closed=False)
                y += sep_l

        # sección
        sx, sy = 0.0, B + 1.0
        poly([(sx, sy), (sx+B, sy), (sx+B, sy+h), (sx, sy+h)], "ZAPATA")
        poly([(sx+(B-t)/2, sy+h), (sx+(B+t)/2, sy+h),
              (sx+(B+t)/2, sy+h+0.4), (sx+(B-t)/2, sy+h+0.4)], "MURO")
        y_ac = sy + r
        poly([(sx+r, y_ac), (sx+B-r, y_ac)], "ACERO_T", closed=False)

        txt("FundaCalc — Zapata Corrida", 0, -0.4, 0.14, "TEXTOS")
        txt(f"B={B:.2f}m  h={h:.2f}m  t_muro={t:.2f}m", 0, -0.65, 0.10, "TEXTOS")
        txt(f"Trans: {var_t} @ {sep_t*100:.0f}cm", 0, -0.85, 0.10, "TEXTOS")
        txt(f"Long:  {var_l} @ {sep_l*100:.0f}cm", 0, -1.05, 0.10, "TEXTOS")
        txt(f"Fecha: {datetime.now():%d/%m/%Y %H:%M}", 0, -1.25, 0.10, "TEXTOS")

        lines.extend(["0", "ENDSEC", "0", "EOF"])
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
