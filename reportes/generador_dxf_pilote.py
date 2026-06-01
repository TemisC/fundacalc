"""
Generador DXF — Módulo 6B: Pilote Individual.
Produce perfil longitudinal con capas de suelo, flechas de fricción y tabla de resultados.
"""
from datetime import datetime

try:
    import ezdxf
    _HAS_EZDXF = True
except ImportError:
    _HAS_EZDXF = False


class _DXFBase:
    _LAYERS = {
        "PILOTE":  (5, "Cuerpo del pilote"),
        "SUELO":   (3, "Capas de suelo"),
        "PRESION": (1, "Flechas de friccion y punta"),
        "COTAS":   (7, "Lineas de cota"),
        "TEXTOS":  (7, "Textos y etiquetas"),
        "EJES":    (8, "Ejes y lineas auxiliares"),
    }

    def _setup_doc(self):
        doc = ezdxf.new(dxfversion="R2010")
        for name, (color, _) in self._LAYERS.items():
            if name not in doc.layers:
                doc.layers.new(name, dxfattribs={"color": color})
        return doc, doc.modelspace()

    def _poly(self, msp, pts, layer, closed=True):
        if len(pts) < 2:
            return
        msp.add_lwpolyline(
            pts + ([pts[0]] if closed else []),
            dxfattribs={"layer": layer},
        )

    def _line(self, msp, x1, y1, x2, y2, layer="EJES"):
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})

    def _text(self, msp, x, y, txt, h=0.10, layer="TEXTOS"):
        msp.add_text(
            str(txt),
            dxfattribs={"height": h, "layer": layer},
        ).set_placement((x, y))

    def _suelo_hatch(self, msp, x0, y0, x1, y1, paso=0.20):
        ancho, alto = x1 - x0, y1 - y0
        n = int((ancho + alto) / paso) + 2
        for i in range(n):
            d = i * paso
            xa, ya = x0 + d, y1
            xb, yb = x0, y1 - d
            xa = min(xa, x1)
            xb = max(xb, x0)
            ya = y1 - (d - (xa - x0))
            ya = max(min(ya, y1), y0)
            yb = y1 - d
            yb = max(min(yb, y1), y0)
            if xa >= x0 and xb <= x1 and ya <= y1 and yb >= y0:
                self._line(msp, xa, ya, xb, yb, "SUELO")

    def _cota_v(self, msp, y1, y2, x_cota, x_ref, label):
        arr = max(abs(y2 - y1) * 0.04, 0.08)
        self._line(msp, x_cota, y1, x_cota, y2, "COTAS")
        self._line(msp, x_ref, y1, x_cota + 0.05, y1, "COTAS")
        self._line(msp, x_ref, y2, x_cota + 0.05, y2, "COTAS")
        self._line(msp, x_cota, y1, x_cota + arr * 0.35, y1 + arr, "COTAS")
        self._line(msp, x_cota, y2, x_cota + arr * 0.35, y2 - arr, "COTAS")
        my = (y1 + y2) / 2
        self._text(msp, x_cota - 0.38, my, label, 0.10, "COTAS")

    def _cota_h(self, msp, x1, x2, y_cota, y_ref, label):
        arr = max(abs(x2 - x1) * 0.04, 0.08)
        self._line(msp, x1, y_cota, x2, y_cota, "COTAS")
        self._line(msp, x1, y_ref, x1, y_cota - 0.05, "COTAS")
        self._line(msp, x2, y_ref, x2, y_cota - 0.05, "COTAS")
        self._line(msp, x1, y_cota, x1 + arr, y_cota + arr * 0.35, "COTAS")
        self._line(msp, x2, y_cota, x2 - arr, y_cota + arr * 0.35, "COTAS")
        mx = (x1 + x2) / 2
        lbl_w = len(label) * 0.06
        self._text(msp, mx - lbl_w / 2, y_cota - 0.20, label, 0.10, "COTAS")

    def _tabla(self, msp, x0, y0, filas, titulo="", ancho_col=(4.0, 3.0)):
        LINE_H = 0.22
        TITLE_H = 0.28
        x1 = x0 + ancho_col[0]
        x2 = x1 + ancho_col[1]
        y = y0
        if titulo:
            self._text(msp, x0, y, titulo, 0.13, "TEXTOS")
            y -= TITLE_H
            self._line(msp, x0, y + 0.05, x2, y + 0.05, "COTAS")
            y -= 0.08
        for k, v in filas:
            self._text(msp, x0 + 0.05, y, k, 0.10, "TEXTOS")
            self._text(msp, x1 + 0.05, y, v, 0.10, "TEXTOS")
            y -= LINE_H
        tabla_h = y0 - y + 0.10
        self._poly(msp,
                   [(x0, y0 + 0.22), (x2, y0 + 0.22),
                    (x2, y0 + 0.22 - tabla_h), (x0, y0 + 0.22 - tabla_h)],
                   "COTAS", closed=True)
        self._line(msp, x1, y0 + 0.22, x1, y0 + 0.22 - tabla_h, "COTAS")
        return y

    def _titulo_plano(self, msp, x0, y0, titulo, subtitulo=""):
        self._text(msp, x0, y0, titulo, 0.16, "TEXTOS")
        self._text(msp, x0, y0 - 0.28, subtitulo, 0.11, "TEXTOS")
        self._text(msp, x0, y0 - 0.52,
                   f"FundaCalc   |   {datetime.now():%d/%m/%Y}", 0.09, "TEXTOS")
        self._line(msp, x0, y0 - 0.60, x0 + 8.0, y0 - 0.60, "COTAS")


class GeneradorDXFPilote(_DXFBase):

    def generar(self, ruta: str, motor):
        if not _HAS_EZDXF:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write("DXF no disponible: instalar ezdxf\n")
            return
        doc, msp = self._setup_doc()
        self._dibujar(msp, motor)
        doc.saveas(ruta)

    def _dibujar(self, msp, motor):
        res = motor.res
        ax  = res.axial
        lat = res.lateral
        rc  = res.rc
        D   = res.D
        L   = res.L

        # Origen: tope del pilote en (0, 0), Y crece hacia abajo negativo
        # Pilote: rectángulo (0,0) → (D, -L)
        suelo_ancho = max(D * 2.5, 1.5)

        # ── Capas de suelo ─────────────────────────────────────────────────────
        for capa in ax.capas:
            y_top = -capa.z_top
            y_bot = -(capa.z_top + capa.espesor)
            y_top = min(y_top, 0)
            y_bot = max(y_bot, -L)
            if y_top <= y_bot:
                continue
            # suelo izquierdo
            self._poly(msp, [
                (-suelo_ancho, y_top), (0, y_top),
                (0, y_bot), (-suelo_ancho, y_bot),
            ], "SUELO")
            self._suelo_hatch(msp, -suelo_ancho, y_bot, 0, y_top, paso=0.22)
            # suelo derecho
            self._poly(msp, [
                (D, y_top), (D + suelo_ancho, y_top),
                (D + suelo_ancho, y_bot), (D, y_bot),
            ], "SUELO")
            self._suelo_hatch(msp, D, y_bot, D + suelo_ancho, y_top, paso=0.22)
            # separador de capa
            self._line(msp, -suelo_ancho - 0.15, y_bot,
                       D + suelo_ancho + 0.15, y_bot, "EJES")
            # etiqueta de capa
            mid_y = (y_top + y_bot) / 2
            self._text(msp, D + suelo_ancho + 0.25, mid_y,
                       f"Cap.{capa.numero}: {capa.tipo}  e={capa.espesor:.1f}m"
                       f"  fs={capa.fs:.1f}kPa  Qs={capa.Qs:.1f}kN",
                       0.10, "TEXTOS")

        # ── Cuerpo del pilote ──────────────────────────────────────────────────
        self._poly(msp, [(0, 0), (D, 0), (D, -L), (0, -L)], "PILOTE")

        # Línea de terreno
        self._line(msp, -suelo_ancho - 0.15, 0,
                   D + suelo_ancho + 0.15, 0, "EJES")
        self._text(msp, D + suelo_ancho + 0.25, 0.12, "N.T.N.", 0.10, "TEXTOS")

        # ── Flechas de fricción lateral ────────────────────────────────────────
        max_fs = max((c.fs for c in ax.capas), default=1.0)
        arr_scl = min(suelo_ancho * 0.5 / max(max_fs, 1.0), 0.25)
        for capa in ax.capas:
            if capa.fs < 0.5:
                continue
            y_mid = -(capa.z_top + capa.espesor / 2)
            if y_mid < -L or y_mid > 0:
                continue
            flen = capa.fs * arr_scl
            flen = max(min(flen, suelo_ancho * 0.7), 0.15)
            # flecha izquierda → pilote
            self._line(msp, -flen, y_mid, 0, y_mid, "PRESION")
            a = flen * 0.15
            self._line(msp, 0, y_mid, a, y_mid + a * 0.5, "PRESION")
            self._line(msp, 0, y_mid, a, y_mid - a * 0.5, "PRESION")
            # flecha derecha → pilote
            self._line(msp, D + flen, y_mid, D, y_mid, "PRESION")
            self._line(msp, D, y_mid, D - a, y_mid + a * 0.5, "PRESION")
            self._line(msp, D, y_mid, D - a, y_mid - a * 0.5, "PRESION")

        # ── Flecha de punta (apunta hacia arriba, sale de la base) ────────────
        tip_len = min(D * 1.2, 0.80)
        self._line(msp, D / 2, -L - tip_len, D / 2, -L, "PRESION")
        a = tip_len * 0.18
        self._line(msp, D / 2, -L, D / 2 - a, -L - a, "PRESION")
        self._line(msp, D / 2, -L, D / 2 + a, -L - a, "PRESION")
        self._text(msp, D / 2 + 0.12, -L - tip_len / 2,
                   f"Qp={ax.Qp:.1f}kN", 0.10, "PRESION")

        # ── Cotas ──────────────────────────────────────────────────────────────
        DIM_L = -suelo_ancho - 0.55
        self._cota_v(msp, -L, 0, DIM_L, 0, f"L={L:.2f}m")
        self._cota_h(msp, 0, D, 0.50, 0, f"D={D:.3f}m")

        # ── Tabla de datos ──────────────────────────────────────────────────────
        tx = DIM_L - 0.5
        ty = -L - 2.0
        self._titulo_plano(msp, tx, ty,
                           "PILOTE INDIVIDUAL — PERFIL LONGITUDINAL",
                           f"D={D:.2f}m  L={L:.2f}m  tipo={res.tipo}")
        ty -= 0.80

        filas_ax = [
            ("Diametro D",        f"{D:.3f} m"),
            ("Longitud L",        f"{L:.2f} m"),
            ("Tipo pilote",       res.tipo),
            ("Qs fuste",          f"{ax.Qs_total:.1f} kN"),
            ("Qp punta",          f"{ax.Qp:.1f} kN"),
            ("Qu ultima",         f"{ax.Qu:.1f} kN"),
            ("Qa admisible",      f"{ax.Qa:.1f} kN"),
            ("FS axial",          f"{ax.FS_axial:.2f}  {'OK' if ax.FS_axial >= 2.5 else 'NO'}"),
        ]
        filas_lat = [
            ("Metodo lateral",    lat.metodo),
            ("Tipo pilote lat.",  lat.tipo_pilote),
            ("My resistente",     f"{lat.My:.1f} kN.m"),
            ("Hu capacidad",      f"{lat.Hu:.1f} kN"),
            ("H diseno",          f"{lat.H_dis:.1f} kN"),
            ("FS lateral",        f"{lat.FS_lateral:.2f}  {'OK' if lat.ok_lateral else 'NO'}"),
        ]
        filas_rc = [
            ("Ag seccion",        f"{res.D**2 * 3.14159/4 * 1e4:.1f} cm2"),
            ("Ast diseno",        f"{rc.Ast_dis:.2f} cm2"),
            ("Armadura long.",    rc.desc_long),
            ("Espiral db",        f"{rc.db_esp:.0f} mm"),
            ("Paso espiral",      f"{rc.paso_esp:.0f} mm"),
        ]
        ty = self._tabla(msp, tx, ty, filas_ax, "CAPACIDAD AXIAL") - 0.40
        ty = self._tabla(msp, tx, ty, filas_lat, "CAPACIDAD LATERAL") - 0.40
        self._tabla(msp, tx, ty, filas_rc, "ARMADURA RC")
