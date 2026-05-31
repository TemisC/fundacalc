"""
Generador DXF — Viga de Fundacion (Winkler MEF).
Plano:
  - Alzado longitudinal (L x h): contorno, columnas, acero inf/sup, estribos, cotas
  - Seccion transversal (B x h): barras inferiores/superiores + estribo
  - Cuadro de armadura
"""
import re
from datetime import datetime

try:
    import ezdxf
except ImportError:
    ezdxf = None


def _parse_db(varilla: str) -> float:
    m = re.search(r'(\d+)', varilla or '')
    return int(m.group(1)) / 1000.0 if m else 0.012


class GeneradorDXFViga:

    # Colores de capas
    _LAYERS = {
        "VIGA":      4,   # cyan
        "COLUMNAS":  8,   # gris
        "ACERO_INF": 1,   # rojo
        "ACERO_SUP": 3,   # verde
        "ESTRIBOS":  5,   # azul
        "COTAS":     7,   # blanco
        "TEXTOS":    7,   # blanco
    }

    def generar(self, ruta: str, motor, norma: str = "ACI318"):
        if ezdxf:
            self._generar_con_ezdxf(ruta, motor, norma)
        else:
            self._generar_dxf_basico(ruta, motor, norma)

    # ── ezdxf ────────────────────────────────────────────────────────────────

    def _generar_con_ezdxf(self, ruta: str, motor, norma: str):
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        for name, color in self._LAYERS.items():
            if name not in doc.layers:
                doc.layers.new(name, dxfattribs={"color": color})

        res  = motor.res
        geo  = motor.geo
        cols = motor.columnas

        L     = res.L
        B     = res.B
        h     = res.h
        recub = geo.recubrimiento
        s_est = res.s_estribo   # separacion estribos [m]
        n_inf = res.n_inf
        n_sup = res.n_sup
        var_inf = res.var_inf
        var_sup = res.var_sup
        db_inf  = _parse_db(var_inf)
        db_sup  = _parse_db(var_sup)

        GAP = max(B * 1.2, 1.5)   # espacio horizontal entre alzado y seccion

        # ── 1. ALZADO LONGITUDINAL ────────────────────────────────────────────
        self._alzado(msp, cols, L, h, recub, db_inf, db_sup,
                     n_inf, n_sup, var_inf, var_sup, s_est)

        # ── 2. SECCION TRANSVERSAL ────────────────────────────────────────────
        ox = L + GAP
        self._seccion(msp, B, h, recub, db_inf, db_sup, n_inf, n_sup, ox)

        # ── 3. CUADRO DE ARMADURA ─────────────────────────────────────────────
        self._cuadro(msp, motor, cols, norma, L, B, h, recub, var_inf, var_sup)

        doc.saveas(ruta)

    # ── Alzado longitudinal ─────────────────────────────────────────────────

    def _alzado(self, msp, cols, L, h, recub, db_inf, db_sup,
                n_inf, n_sup, var_inf, var_sup, s_est):

        # Contorno de la viga
        self._rect(msp, 0, 0, L, h, "VIGA", 4)

        # Acero inferior — linea horizontal cerca de cara inferior
        y_inf = recub + db_inf / 2
        self._line(msp, recub, y_inf, L - recub, y_inf, "ACERO_INF")
        # Segunda capa si muchas barras
        if n_inf > 4:
            y_inf2 = y_inf + db_inf * 1.5
            self._line(msp, recub, y_inf2, L - recub, y_inf2, "ACERO_INF")

        # Acero superior — linea horizontal cerca de cara superior
        y_sup = h - recub - db_sup / 2
        self._line(msp, recub, y_sup, L - recub, y_sup, "ACERO_SUP")

        # Estribos — verticales interiores
        if s_est > 0:
            x_est = recub
            while x_est <= L - recub + 1e-6:
                self._line(msp, x_est, recub, x_est, h - recub, "ESTRIBOS")
                x_est += s_est

        # Columnas — stub por encima de la viga
        for col in cols:
            self._line(msp, col.x, 0, col.x, h + 0.30, "COLUMNAS")
            lbl = col.etiqueta or ""
            if lbl:
                self._text(msp, col.x, h + 0.35, lbl, 0.12, "TEXTOS")

        # Cota longitud total (debajo)
        self._cota_h(msp, 0, L, -0.45, 0.0, f"L = {L:.2f} m")

        # Cotas inter-columnas
        if len(cols) > 1:
            for i in range(len(cols) - 1):
                x1 = cols[i].x
                x2 = cols[i + 1].x
                self._cota_h(msp, x1, x2, -0.75, 0.0,
                             f"{x2 - x1:.2f} m")

        # Cota altura (a la derecha)
        self._cota_v(msp, 0, h, L + 0.25, L, f"h = {h:.2f} m")

        # Textos de armadura (sobre las lineas de acero)
        self._text(msp, L / 2, y_inf + 0.12, f"{n_inf} x {var_inf}", 0.10, "ACERO_INF")
        self._text(msp, L / 2, y_sup - 0.12 - 0.10, f"{n_sup} x {var_sup}", 0.10, "ACERO_SUP")

    # ── Seccion transversal ────────────────────────────────────────────────

    def _seccion(self, msp, B, h, recub, db_inf, db_sup, n_inf, n_sup, ox):

        oy = 0.0  # misma baseline que el alzado

        # Contorno
        self._rect(msp, ox, oy, B, h, "VIGA", 4)

        # Estribo interior
        est = recub * 0.9  # offset ligeramente menor que el recubrimiento
        self._rect(msp, ox + est, oy + est, B - 2*est, h - 2*est, "ESTRIBOS", 5)

        # Barras inferiores
        y_inf = oy + recub + db_inf / 2
        self._barras_seccion(msp, ox, B, recub, db_inf, n_inf, y_inf, "ACERO_INF", 1)

        # Barras superiores
        y_sup = oy + h - recub - db_sup / 2
        self._barras_seccion(msp, ox, B, recub, db_sup, n_sup, y_sup, "ACERO_SUP", 3)

        # Cotas seccion
        self._cota_h(msp, ox, ox + B, oy - 0.45, oy, f"B = {B:.2f} m")
        self._cota_v(msp, oy, oy + h, ox - 0.40, ox, f"h = {h:.2f} m")

        # Etiqueta seccion
        self._text(msp, ox, oy - 0.70, "SECCION TRANSVERSAL", 0.13, "TEXTOS")

    def _barras_seccion(self, msp, ox, B, recub, db, n, y_c, layer, color):
        r = db / 2
        if n <= 1:
            msp.add_circle(
                (ox + B / 2, y_c), r,
                dxfattribs={"layer": layer, "color": color},
            )
            return
        x_ini = ox + recub + r
        x_fin = ox + B - recub - r
        paso  = (x_fin - x_ini) / (n - 1)
        for i in range(n):
            xc = x_ini + i * paso
            msp.add_circle(
                (xc, y_c), r,
                dxfattribs={"layer": layer, "color": color},
            )

    # ── Cuadro de armadura ─────────────────────────────────────────────────

    def _cuadro(self, msp, motor, cols, norma, L, B, h, recub, var_inf, var_sup):
        """Cuadro de datos debajo del alzado (coordenadas negativas)."""
        res = motor.res
        geo = motor.geo
        sue = motor.suelo

        GAP_V   = 1.20   # espacio desde y=0 hacia abajo
        paso    = 0.22   # altura de fila
        texto_h = 0.10

        filas = [
            (f"FundaCalc -- Viga de Fundacion  |  Norma: {norma}  |  "
             f"{datetime.now():%d/%m/%Y %H:%M}",
             True),
            (f"L={L:.2f}m  B={B:.2f}m  h={h:.2f}m  d={geo.d:.3f}m  "
             f"r={recub*100:.0f}cm",
             False),
            (f"ks={sue.ks:.0f} kN/m3  qa={sue.qa:.0f} kN/m2  "
             f"n_columnas={len(cols)}",
             False),
            (f"Arm. Inf: {res.n_inf}x{var_inf}  As_req={res.As_req_inf:.2f}cm2  "
             f"As_dis={res.As_dis_inf:.2f}cm2",
             False),
            (f"Arm. Sup: {res.n_sup}x{var_sup}  As_req={res.As_req_sup:.2f}cm2  "
             f"As_dis={res.As_dis_sup:.2f}cm2",
             False),
            (f"Estribos: {res.var_estribo} @ {res.s_estribo*100:.0f}cm (2 ramas)  "
             f"Vu={res.Vu_max:.1f}kN  phiVc={res.phi_Vc:.1f}kN",
             False),
            (f"q_max={res.q_max:.1f}kN/m2  M+={res.M_max_pos:.1f}kN.m  "
             f"M-={res.M_max_neg:.1f}kN.m  V_max={res.V_max:.1f}kN",
             False),
        ]

        y = -GAP_V
        for txt, es_titulo in filas:
            ht = texto_h * 1.2 if es_titulo else texto_h
            self._text(msp, 0, y, txt, ht, "TEXTOS")
            y -= paso

    # ── Primitivos ─────────────────────────────────────────────────────────

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
        self._line(msp, x1, y_cota, x2, y_cota, "COTAS")
        self._line(msp, x1, y_ref,  x1, y_cota, "COTAS")
        self._line(msp, x2, y_ref,  x2, y_cota, "COTAS")
        mx = (x1 + x2) / 2
        self._text(msp, mx - len(label) * 0.035, y_cota - 0.18, label, 0.10, "COTAS")

    def _cota_v(self, msp, y1, y2, x_cota, x_ref, label):
        self._line(msp, x_cota, y1, x_cota, y2, "COTAS")
        self._line(msp, x_ref,  y1, x_cota, y1, "COTAS")
        self._line(msp, x_ref,  y2, x_cota, y2, "COTAS")
        my = (y1 + y2) / 2
        self._text(msp, x_cota + 0.05, my, label, 0.10, "COTAS")

    # ── Fallback sin ezdxf ─────────────────────────────────────────────────

    def _generar_dxf_basico(self, ruta: str, motor, norma: str):
        res  = motor.res
        geo  = motor.geo
        cols = motor.columnas
        L    = res.L
        B    = res.B
        h    = res.h

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

        # Contorno alzado
        for x1, y1, x2, y2 in [
            (0, 0, L, 0), (L, 0, L, h), (L, h, 0, h), (0, h, 0, 0)
        ]:
            ln(x1, y1, x2, y2, "VIGA")

        # Columnas
        for c in cols:
            ln(c.x, 0, c.x, h, "COLUMNAS")

        # Acero
        recub = geo.recubrimiento
        db_inf = _parse_db(res.var_inf)
        db_sup = _parse_db(res.var_sup)
        ln(recub, recub + db_inf/2, L - recub, recub + db_inf/2, "ACERO_INF")
        ln(recub, h - recub - db_sup/2, L - recub, h - recub - db_sup/2, "ACERO_SUP")

        # Textos
        txt(0, -0.6, f"FundaCalc - Viga Fundacion | {norma}", 0.15)
        txt(0, -0.9, f"L={L:.2f}m B={B:.2f}m h={h:.2f}m", 0.12)
        txt(0, -1.2, f"Inf: {res.n_inf}x{res.var_inf}  Sup: {res.n_sup}x{res.var_sup}", 0.12)
        txt(0, -1.5, f"Est: {res.var_estribo} @ {res.s_estribo*100:.0f}cm", 0.12)

        lines.append("  0\nENDSEC\n  0\nEOF\n")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("".join(lines))
