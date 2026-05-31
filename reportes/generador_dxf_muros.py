"""
Generadores DXF — Módulos 9.2 a 9.5: Muros de Contención.

Cada clase produce un archivo DXF con:
  · Sección transversal acotada (metros, escala 1:1)
  · Diagrama de presión activa + hidrostática (si aplica)
  · Cuadro de datos y resultados de estabilidad

Reglas de espaciado aplicadas:
  - Offset cotas desde geometría: 0.50 m
  - Segunda línea de cotas: 0.90 m
  - Espacio entre sección y tabla de datos: 2.00 m
  - Altura de texto normal: 0.10 m  (inter-línea 0.22 m)
  - Altura de texto título: 0.14 m  (inter-línea 0.28 m)
  - Zona de presiones: empieza a 0.60 m a la derecha del talón
"""
from datetime import datetime

try:
    import ezdxf
    _HAS_EZDXF = True
except ImportError:
    _HAS_EZDXF = False


# ─── Clase base con primitivos compartidos ────────────────────────────────────

class _DXFBase:
    """Primitivos DXF reutilizables."""

    _LAYERS = {
        "MURO":    (5,  "Cuerpo del muro"),
        "ZAPATA":  (5,  "Zapata / losas"),
        "SUELO":   (3,  "Zona de suelo retenido"),
        "AGUA":    (4,  "Zona saturada / hidrostática"),
        "PRESION": (1,  "Diagrama de presión activa"),
        "HIDRO":   (4,  "Presión hidrostática"),
        "COTAS":   (7,  "Líneas de cota"),
        "TEXTOS":  (7,  "Textos y etiquetas"),
        "ACERO":   (6,  "Indicaciones de armadura"),
        "EJES":    (8,  "Ejes y líneas auxiliares"),
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
        """Relleno de suelo con líneas a 45°."""
        # Líneas diagonales dentro del rectángulo [x0,x1] × [y0,y1]
        ancho, alto = x1 - x0, y1 - y0
        n = int((ancho + alto) / paso) + 2
        for i in range(n):
            d = i * paso
            # línea desde borde superior izq → borde derecho/inferior
            xa, ya = x0 + d, y1
            xb, yb = x0, y1 - d
            # clip al rectángulo
            xa = min(xa, x1)
            xb = max(xb, x0)
            ya = y1 - (d - (xa - x0))
            ya = max(min(ya, y1), y0)
            yb = y1 - d
            yb = max(min(yb, y1), y0)
            if xa >= x0 and xb <= x1 and ya <= y1 and yb >= y0:
                self._line(msp, xa, ya, xb, yb, "SUELO")

    # ── Cotas ─────────────────────────────────────────────────────────────────

    def _cota_h(self, msp, x1, x2, y_cota, y_ref, label):
        """Cota horizontal con testigos."""
        arr = max(abs(x2 - x1) * 0.04, 0.08)
        self._line(msp, x1, y_cota, x2, y_cota, "COTAS")
        self._line(msp, x1, y_ref, x1, y_cota - 0.05, "COTAS")
        self._line(msp, x2, y_ref, x2, y_cota - 0.05, "COTAS")
        # Flechas
        self._line(msp, x1, y_cota, x1 + arr, y_cota + arr * 0.35, "COTAS")
        self._line(msp, x2, y_cota, x2 - arr, y_cota + arr * 0.35, "COTAS")
        mx = (x1 + x2) / 2
        lbl_w = len(label) * 0.06
        self._text(msp, mx - lbl_w / 2, y_cota - 0.20, label, 0.10, "COTAS")

    def _cota_v(self, msp, y1, y2, x_cota, x_ref, label):
        """Cota vertical con testigos."""
        arr = max(abs(y2 - y1) * 0.04, 0.08)
        self._line(msp, x_cota, y1, x_cota, y2, "COTAS")
        self._line(msp, x_ref, y1, x_cota + 0.05, y1, "COTAS")
        self._line(msp, x_ref, y2, x_cota + 0.05, y2, "COTAS")
        # Flechas
        self._line(msp, x_cota, y1, x_cota + arr * 0.35, y1 + arr, "COTAS")
        self._line(msp, x_cota, y2, x_cota + arr * 0.35, y2 - arr, "COTAS")
        my = (y1 + y2) / 2
        self._text(msp, x_cota - 0.38, my, label, 0.10, "COTAS")

    # ── Flecha de presión ──────────────────────────────────────────────────────

    def _flecha_pres(self, msp, x_base, y, longitud, layer="PRESION"):
        """Flecha horizontal apuntando a la izquierda."""
        if longitud < 0.02:
            return
        x_punta = x_base
        x_cola  = x_base + longitud
        self._line(msp, x_cola, y, x_punta, y, layer)
        arr = min(longitud * 0.15, 0.12)
        self._line(msp, x_punta, y, x_punta + arr, y + arr * 0.5, layer)
        self._line(msp, x_punta, y, x_punta + arr, y - arr * 0.5, layer)

    # ── Tabla de datos ─────────────────────────────────────────────────────────

    def _tabla(self, msp, x0, y0, filas, titulo="", ancho_col=(4.0, 3.0)):
        """Dibuja tabla de datos con dos columnas."""
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

        # Marco exterior
        tabla_h = y0 - y + 0.10
        self._poly(msp,
                   [(x0, y0 + 0.22), (x2, y0 + 0.22),
                    (x2, y0 + 0.22 - tabla_h), (x0, y0 + 0.22 - tabla_h)],
                   "COTAS", closed=True)
        # Separador vertical
        self._line(msp, x1, y0 + 0.22, x1, y0 + 0.22 - tabla_h, "COTAS")
        return y   # retorna la y final

    def _titulo_plano(self, msp, x0, y0, titulo, subtitulo=""):
        """Encabezado del plano con título y fecha."""
        self._text(msp, x0, y0, titulo, 0.16, "TEXTOS")
        self._text(msp, x0, y0 - 0.28, subtitulo, 0.11, "TEXTOS")
        self._text(msp, x0, y0 - 0.52, f"FundaCalc   |   {datetime.now():%d/%m/%Y}", 0.09, "TEXTOS")
        self._line(msp, x0, y0 - 0.60, x0 + 8.0, y0 - 0.60, "COTAS")


# ─── M9.2 — Muro de Gravedad ─────────────────────────────────────────────────

class GeneradorDXFMuroGravedad(_DXFBase):

    def generar(self, ruta: str, motor):
        if not _HAS_EZDXF:
            self._fallback_txt(ruta, motor)
            return
        doc, msp = self._setup_doc()
        self._dibujar(msp, motor)
        doc.saveas(ruta)

    def _dibujar(self, msp, motor):
        res  = motor.res
        inp  = motor._inp
        est  = res.estabilidad
        H    = res.H
        bb   = res.b_base
        bc   = res.b_corona
        h_emb = inp['h_emb']

        # Escala de presiones: max flecha = 1.5 m
        p_max = est.Ka * (inp['gamma_r'] * H + inp['q_s']) + est.Ka * inp['q_s']
        p_scl = min(1.5 / max(p_max, 0.1), 0.10)

        # ── Sección transversal ─────────────────────────────────────────────
        # Origen (0,0) = toe en nivel de cimentación (top de h_emb)
        # Cuerpo del muro (trapecio): frente vertical, trasdós inclinado
        cuerpo = [(0, 0), (bb, 0), (bc, H), (0, H)]
        self._poly(msp, cuerpo, "MURO")

        # Empotramiento (zona enterrada del pie)
        if h_emb > 0:
            self._poly(msp, [(0, -h_emb), (bb, -h_emb), (bb, 0), (0, 0)], "SUELO")
            # hatch diagonal en el enterramiento
            self._suelo_hatch(msp, 0, -h_emb, bb, 0, paso=0.25)

        # Suelo retenido (derecha del trasdós)
        suelo_ancho = max(bb, 1.0)
        self._poly(msp, [(bc, H), (bc + suelo_ancho, H),
                         (bc + suelo_ancho, 0), (bb, 0)], "SUELO")
        self._suelo_hatch(msp, bb, 0, bb + suelo_ancho, H, paso=0.25)

        # Línea de terreno
        self._line(msp, bc, H, bc + suelo_ancho + 0.3, H, "EJES")

        # ── Presión activa (flechas) ─────────────────────────────────────────
        n_flechas = 8
        x_pres = bb + suelo_ancho + 0.60   # base de las flechas
        for i in range(n_flechas + 1):
            z = H * i / n_flechas
            p = est.Ka * (inp['gamma_r'] * z + inp['q_s'])
            self._flecha_pres(msp, bb + (bb - bc) * (H - z) / H, H - z,
                               p * p_scl)

        # Triángulo de presión (outline)
        p_top = est.Ka * inp['q_s'] * p_scl
        p_bot = est.Ka * (inp['gamma_r'] * H + inp['q_s']) * p_scl
        self._poly(msp, [
            (bb, 0),
            (bb + p_bot, 0),
            (bc + p_top, H),
            (bc, H),
        ], "PRESION", closed=True)
        self._text(msp, bb + p_bot + 0.10, H * 0.1,
                   f"{est.Ka*(inp['gamma_r']*H+inp['q_s']):.1f} kPa", 0.10, "PRESION")

        # ── Cotas ─────────────────────────────────────────────────────────────
        DIM_L = -0.55    # offset cotas izquierda
        DIM_L2 = -0.95   # segunda cota

        # H total
        self._cota_v(msp, 0, H, DIM_L, 0, f"H={H:.2f}m")
        # h_emb
        if h_emb > 0:
            self._cota_v(msp, -h_emb, 0, DIM_L2, 0, f"h_emb={h_emb:.2f}m")

        DIM_B = -0.55   # offset cotas abajo
        self._cota_h(msp, 0, bb, DIM_B, 0, f"b_base={bb:.2f}m")

        DIM_T = H + 0.50
        self._cota_h(msp, 0, bc, DIM_T, H, f"b_corona={bc:.2f}m")

        # ── Tabla de datos ─────────────────────────────────────────────────────
        tx = DIM_L - 0.5
        ty = -h_emb - 2.0   # 2 m debajo de la zona enterrada

        self._titulo_plano(msp, tx, ty,
                           "MURO DE GRAVEDAD — SECCIÓN TRANSVERSAL",
                           f"H={H:.2f}m  b_base={bb:.2f}m  b_corona={bc:.2f}m")
        ty -= 0.80

        filas_inp = [
            ("Altura total H",       f"{H:.2f} m"),
            ("Ancho en base",        f"{bb:.2f} m"),
            ("Ancho en corona",      f"{bc:.2f} m"),
            ("Enterramiento pie",    f"{h_emb:.2f} m"),
            ("γ material muro",      f"{inp['gamma_muro']:.1f} kN/m³"),
            ("γ suelo retenido",     f"{inp['gamma_r']:.1f} kN/m³"),
            ("φ suelo retenido",     f"{inp['phi_r']:.1f} °"),
            ("Sobrecarga q_s",       f"{inp['q_s']:.1f} kPa"),
            ("Ka (Rankine)",         f"{est.Ka:.4f}"),
            ("q_adm",                f"{inp['qa']:.1f} kPa"),
        ]
        filas_res = [
            ("FS vuelco",           f"{est.FS_vuelco:.2f}  {'✓' if est.ok_vuelco else '✗'}"),
            ("FS deslizamiento",    f"{est.FS_desliz:.2f}  {'✓' if est.ok_desliz else '✗'}"),
            ("q_max (base)",        f"{est.q_max:.1f} kPa  {'✓' if est.ok_presion else '✗'}"),
            ("Excentricidad e",     f"{abs(est.e):.3f} m  {'✓' if est.ok_excentricidad else '✗'}"),
            ("x_R desde toe",       f"{est.x_R:.3f} m"),
            ("Empuje activo Ea",    f"{est.Ea:.2f} kN/m"),
            ("Momento volcador Mo", f"{est.Mo:.2f} kN·m/m"),
        ]
        ty = self._tabla(msp, tx, ty, filas_inp, "DATOS DE ENTRADA") - 0.40
        ty = self._tabla(msp, tx, ty, filas_res, "RESULTADOS DE ESTABILIDAD")

    def _fallback_txt(self, ruta, motor):
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("DXF no disponible: instalar ezdxf\n")


# ─── M9.3 — Muro de Gaviones ─────────────────────────────────────────────────

class GeneradorDXFMuroGaviones(_DXFBase):

    def generar(self, ruta: str, motor):
        if not _HAS_EZDXF:
            self._fallback_txt(ruta, motor)
            return
        doc, msp = self._setup_doc()
        self._dibujar(msp, motor)
        doc.saveas(ruta)

    def _dibujar(self, msp, motor):
        res  = motor.res
        inp  = motor._inp
        est  = res.estabilidad
        N    = res.N
        h    = res.h_capa
        H    = res.H
        bb   = res.b_base
        h_emb = inp['h_emb']

        # Escala de presiones
        p_max = est.Ka * inp['gamma_r'] * H + est.Ka * inp['q_s']
        p_scl = min(1.5 / max(p_max, 0.1), 0.10)

        # ── Cursos de gaviones ──────────────────────────────────────────────
        for i, ancho in enumerate(res.anchos):
            y0 = i * h
            y1 = y0 + h

            # Rectángulo del curso
            self._poly(msp, [(0, y0), (ancho, y0), (ancho, y1), (0, y1)], "MURO")

            # Grilla interna del gavión
            n_cols = max(2, min(4, round(ancho / 0.5)))
            for c in range(1, n_cols):
                xc = ancho * c / n_cols
                self._line(msp, xc, y0, xc, y1, "EJES")
            ym = (y0 + y1) / 2
            self._line(msp, 0, ym, ancho, ym, "EJES")

            # Etiqueta del curso (dentro del rectángulo, con espacio)
            self._text(msp, 0.10, ym - 0.05,
                       f"C{i+1}  {ancho:.2f}m", 0.09, "TEXTOS")

        # Enterramiento
        if h_emb > 0:
            self._poly(msp, [(0, -h_emb), (bb, -h_emb), (bb, 0), (0, 0)], "SUELO")
            self._suelo_hatch(msp, 0, -h_emb, bb, 0, paso=0.22)

        # Suelo retenido (derecha del escalonado)
        # La zona de suelo sigue el perfil escalonado del trasdós
        suelo_ancho = max(bb * 0.6, 1.0)
        self._poly(msp,
                   [(res.anchos[-1], H), (res.anchos[-1] + suelo_ancho, H),
                    (bb + suelo_ancho, 0), (bb, 0)],
                   "SUELO")
        self._suelo_hatch(msp, bb, 0, bb + suelo_ancho, H, paso=0.25)

        # Línea de terreno
        self._line(msp, res.anchos[-1], H, res.anchos[-1] + suelo_ancho + 0.3, H, "EJES")

        # Juntas horizontales (líneas de separación entre cursos)
        for i in range(1, N):
            yi = i * h
            bi = res.anchos[i]
            self._line(msp, 0, yi, bi, yi, "PRESION")

        # Presión activa
        for i in range(9):
            z = H * i / 8
            p = est.Ka * (inp['gamma_r'] * z + inp['q_s'])
            # La posición x del trasdós a esta profundidad
            ratio = z / H
            b_en_z = res.anchos[0] - (res.anchos[0] - res.anchos[-1]) * (1 - ratio)
            self._flecha_pres(msp, b_en_z, H - z, p * p_scl)

        # ── Cotas ─────────────────────────────────────────────────────────────
        DIM_L = -0.55
        self._cota_v(msp, 0, H, DIM_L, 0, f"H={H:.2f}m")
        if h_emb > 0:
            self._cota_v(msp, -h_emb, 0, -0.95, 0, f"h_emb={h_emb:.2f}m")
        self._cota_h(msp, 0, bb, -0.55, 0, f"b_base={bb:.2f}m")
        self._cota_h(msp, 0, res.anchos[-1], H + 0.50, H,
                     f"b_corona={res.b_corona:.2f}m")
        self._cota_v(msp, 0, h, bb + 0.55, bb, f"h_capa={h:.2f}m")

        # ── Tabla de datos ─────────────────────────────────────────────────────
        tx = DIM_L - 0.5
        ty = -h_emb - 2.0

        self._titulo_plano(msp, tx, ty,
                           "MURO DE GAVIONES — SECCIÓN TRANSVERSAL",
                           f"N={N} cursos  H={H:.2f}m  h_capa={h:.2f}m")
        ty -= 0.80
        anchos_str = " / ".join(f"{b:.2f}" for b in res.anchos)
        filas_inp = [
            ("N cursos",             str(N)),
            ("Altura por curso",     f"{h:.2f} m"),
            ("Altura total H",       f"{H:.2f} m"),
            ("b_base / b_corona",    f"{bb:.2f} / {res.b_corona:.2f} m"),
            ("Anchos (base→corona)", anchos_str + " m"),
            ("γ gavión",             f"{inp['gamma_g']:.1f} kN/m³"),
            ("φ suelo retenido",     f"{inp['phi_r']:.1f} °"),
            ("Ka (Rankine)",         f"{est.Ka:.4f}"),
            ("q_adm",                f"{inp['qa']:.1f} kPa"),
        ]
        filas_res = [
            ("FS vuelco",        f"{est.FS_vuelco:.2f}  {'✓' if est.ok_vuelco else '✗'}"),
            ("FS deslizamiento", f"{est.FS_desliz:.2f}  {'✓' if est.ok_desliz else '✗'}"),
            ("q_max base",       f"{est.q_max:.1f} kPa  {'✓' if est.ok_presion else '✗'}"),
            ("Excentricidad e",  f"{abs(est.e):.3f} m  {'✓' if est.ok_excentricidad else '✗'}"),
            ("Juntas internas",  f"{'Todas OK ✓' if res.ok_interna else 'Ver detalle ✗'}"),
            ("Ea total",         f"{est.Ea:.2f} kN/m"),
        ]
        ty = self._tabla(msp, tx, ty, filas_inp, "DATOS DE ENTRADA") - 0.40
        # Tabla de juntas internas
        filas_juntas = [
            (f"Junta {vi.junta} (H_sobre={vi.H_sobre:.2f}m)",
             f"FS={vi.FS_desliz:.2f} {'✓' if vi.ok_desliz else '✗'}")
            for vi in res.internas
        ]
        ty = self._tabla(msp, tx, ty, filas_res, "RESULTADOS GLOBALES") - 0.40
        self._tabla(msp, tx, ty, filas_juntas, "VERIFICACIÓN INTERNA DE JUNTAS")

    def _fallback_txt(self, ruta, motor):
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("DXF no disponible: instalar ezdxf\n")


# ─── M9.4 — Muro con Contrafuertes ───────────────────────────────────────────

class GeneradorDXFMuroContrafuertes(_DXFBase):

    def generar(self, ruta: str, motor):
        if not _HAS_EZDXF:
            self._fallback_txt(ruta, motor)
            return
        doc, msp = self._setup_doc()
        self._dibujar(msp, motor)
        doc.saveas(ruta)

    def _dibujar(self, msp, motor):
        res  = motor.res
        inp  = motor._inp
        est  = res.estabilidad
        H    = res.H
        hz   = inp['h_zapata']
        ep   = inp['e_pantalla']
        ec   = inp['e_contrafuerte']
        Bp   = inp['B_punta']
        Bt   = inp['B_talon']
        s    = inp['s']
        BT   = res.B_total
        hf   = res.h_fuste

        p_max = est.Ka * inp['gamma_r'] * hf + est.Ka * inp['q_s']
        p_scl = min(1.5 / max(p_max, 0.1), 0.10)

        # ── SECCIÓN TRANSVERSAL (a través de un contrafuerte) ───────────────
        # Origen (0,0) = toe en nivel superior de cimentación
        # Zapata
        self._poly(msp, [(0, -hz), (BT, -hz), (BT, 0), (0, 0)], "ZAPATA")
        # Pantalla (stem)
        self._poly(msp, [(Bp, 0), (Bp + ep, 0),
                         (Bp + ep, hf), (Bp, hf)], "MURO")
        # Contrafuerte (triángulo)
        self._poly(msp, [(Bp, 0), (Bp, hf),
                         (Bp + ep + Bt, 0)], "MURO")
        # Suelo retenido sobre el talón
        self._poly(msp, [(Bp + ep, 0), (BT, 0), (BT, hf), (Bp + ep, hf)], "SUELO")
        self._suelo_hatch(msp, Bp + ep, 0, BT, hf, paso=0.30)
        # Línea de terreno
        self._line(msp, Bp + ep, hf, BT + 0.5, hf, "EJES")

        # Presión activa sobre la pantalla
        x_pant = Bp  # cara de la pantalla hacia el suelo = Bp + ep
        for i in range(9):
            z = hf * i / 8
            p = est.Ka * (inp['gamma_r'] * z + inp['q_s'])
            self._flecha_pres(msp, Bp + ep, hf - z, p * p_scl)

        # Triángulo de presión
        p_top_px = est.Ka * inp['q_s'] * p_scl
        p_bot_px = est.Ka * (inp['gamma_r'] * hf + inp['q_s']) * p_scl
        self._poly(msp, [
            (Bp + ep, hf), (Bp + ep + p_top_px, hf),
            (Bp + ep + p_bot_px, 0), (Bp + ep, 0),
        ], "PRESION")
        self._text(msp, Bp + ep + p_bot_px + 0.12, hf * 0.1,
                   f"{est.Ka*(inp['gamma_r']*hf+inp['q_s']):.1f} kPa", 0.09, "PRESION")

        # ── Indicaciones de armadura ─────────────────────────────────────────
        # Pantalla neg (cara suelo)
        self._text(msp, Bp + ep + 0.10, hf * 0.7,
                   f"Pan.neg: {res.pantalla_neg.barra}", 0.09, "ACERO")
        # Punta
        self._text(msp, 0.05, -hz * 0.5,
                   f"Punta: {res.punta.barra}", 0.09, "ACERO")
        # Talón
        self._text(msp, Bp + ep + 0.10, -hz * 0.5,
                   f"Talón: {res.talon.barra}", 0.09, "ACERO")
        # Contrafuerte
        self._text(msp, Bp + 0.10, hf * 0.3,
                   f"CF: {res.contrafuerte.barra}", 0.09, "ACERO")

        # ── Cotas sección ────────────────────────────────────────────────────
        DIM_L = -0.55
        self._cota_v(msp, -hz, hf, DIM_L, 0, f"H={H:.2f}m")
        self._cota_v(msp, -hz, 0, -0.95, 0, f"h_zap={hz:.2f}m")
        self._cota_h(msp, 0, BT, -hz - 0.55, -hz, f"B={BT:.2f}m")
        self._cota_h(msp, 0, Bp, -hz - 0.95, -hz, f"Bp={Bp:.2f}m")
        self._cota_h(msp, Bp + ep, BT, -hz - 0.95, -hz, f"Bt={Bt:.2f}m")
        self._cota_h(msp, Bp, Bp + ep, hf + 0.50, hf, f"e_pan={ep:.2f}m")

        # ── ELEVACIÓN FRONTAL (a la derecha, separación de 3.0m) ─────────────
        ox2 = BT + 3.0

        # Losa de base
        self._poly(msp, [(ox2, -hz), (ox2 + s * 3, -hz),
                         (ox2 + s * 3, 0), (ox2, 0)], "ZAPATA")
        # Pantalla frontal
        self._poly(msp, [(ox2, 0), (ox2 + s * 3, 0),
                         (ox2 + s * 3, hf), (ox2, hf)], "MURO")
        # Contrafuertes en elevación (3 triangles)
        for k in range(1, 4):
            xk = ox2 + k * s - ec / 2
            self._poly(msp, [(xk, 0), (xk + ec, 0), (xk + ec, hf),
                             (xk, hf), (xk, 0)], "EJES")

        # Cotas elevación
        self._cota_h(msp, ox2, ox2 + s, -hz - 0.55, -hz, f"s={s:.2f}m")
        self._cota_h(msp, ox2, ox2 + s * 3, -hz - 0.95, -hz, "3×s (repr.)")
        self._cota_v(msp, -hz, hf, ox2 - 0.55, ox2, f"H={H:.2f}m")

        self._text(msp, ox2, hf + 0.40, "ELEVACIÓN FRONTAL (vista intradós)", 0.12, "TEXTOS")
        self._text(msp, ox2, hf + 0.22, "Pantalla + Contrafuertes (representativo 3 vanos)", 0.09, "TEXTOS")

        # ── Tabla de datos ────────────────────────────────────────────────────
        tx = DIM_L - 0.5
        ty = -hz - 2.0

        self._titulo_plano(msp, tx, ty,
                           "MURO CON CONTRAFUERTES — SECCIÓN Y ELEVACIÓN",
                           f"H={H:.2f}m  s={s:.2f}m  B={BT:.2f}m")
        ty -= 0.80
        filas_inp = [
            ("Altura total H",       f"{H:.2f} m"),
            ("Espesor zapata",       f"{hz:.2f} m"),
            ("Espesor pantalla",     f"{ep:.2f} m"),
            ("Espesor CF",           f"{ec:.2f} m"),
            ("Espaciado s",          f"{s:.2f} m"),
            ("Luz libre L = s-e",    f"{res.L_libre:.2f} m"),
            ("Punta Bp / Talón Bt",  f"{Bp:.2f} / {Bt:.2f} m"),
            ("φ suelo / Ka",         f"{inp['phi_r']:.0f}°  /  {est.Ka:.4f}"),
        ]
        filas_res = [
            ("FS vuelco",        f"{est.FS_vuelco:.2f}  {'✓' if est.ok_vuelco else '✗'}"),
            ("FS deslizamiento", f"{est.FS_desliz:.2f}  {'✓' if est.ok_desliz else '✗'}"),
            ("q_max base",       f"{est.q_max:.1f} kPa  {'✓' if est.ok_presion else '✗'}"),
            ("Excentricidad e",  f"{abs(est.e):.3f} m  {'✓' if est.ok_excentricidad else '✗'}"),
        ]
        filas_arm = [
            ("Pantalla neg (apoyo)", res.pantalla_neg.barra),
            ("Pantalla pos (vano)",  res.pantalla_pos.barra),
            ("Punta",                res.punta.barra),
            ("Talón",                res.talon.barra),
            (f"Contrafuerte/CF (s={s:.2f}m)", res.contrafuerte.barra),
        ]
        ty = self._tabla(msp, tx, ty, filas_inp, "DATOS DE ENTRADA") - 0.40
        ty = self._tabla(msp, tx, ty, filas_res, "RESULTADOS ESTABILIDAD") - 0.40
        self._tabla(msp, tx, ty, filas_arm, "ARMADURA PRINCIPAL")

    def _fallback_txt(self, ruta, motor):
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("DXF no disponible: instalar ezdxf\n")


# ─── M9.5 — Muro de Sótano ───────────────────────────────────────────────────

class GeneradorDXFMuroSotano(_DXFBase):

    def generar(self, ruta: str, motor):
        if not _HAS_EZDXF:
            self._fallback_txt(ruta, motor)
            return
        doc, msp = self._setup_doc()
        self._dibujar(msp, motor)
        doc.saveas(ruta)

    def _dibujar(self, msp, motor):
        res  = motor.res
        inp  = motor._inp
        c    = res.cargas
        m    = res.momentos
        H    = res.H
        e    = res.e_muro
        h_NF = res.h_NF

        p_max = c.p_total_base
        p_scl = min(1.5 / max(p_max, 0.1), 0.08)

        # ── Sección transversal ──────────────────────────────────────────────
        # Origen (0,0) = cara interior del muro, a nivel de la losa de techo
        # Muro va de y=0 (corona) hacia abajo a y=-H (base)
        self._poly(msp, [(0, 0), (e, 0), (e, -H), (0, -H)], "MURO")

        # Losa de techo
        self._poly(msp, [(-0.4, 0.10), (e + 1.5, 0.10),
                         (e + 1.5, 0), (-0.4, 0)], "ZAPATA")
        # Losa de piso
        self._poly(msp, [(-0.4, -H), (e + 1.5, -H),
                         (e + 1.5, -H - 0.20), (-0.4, -H - 0.20)], "ZAPATA")

        # Suelo retenido (derecha del muro)
        suelo_w = 1.2
        self._poly(msp, [(e, 0), (e + suelo_w, 0),
                         (e + suelo_w, -H), (e, -H)], "SUELO")
        self._suelo_hatch(msp, e, -H, e + suelo_w, 0, paso=0.22)

        # Nivel freático
        if c.tiene_nf and h_NF < H:
            y_nf = -h_NF
            self._line(msp, e - 0.2, y_nf, e + suelo_w + 0.3, y_nf, "AGUA")
            self._text(msp, e + suelo_w + 0.35, y_nf + 0.05, f"NF={h_NF:.2f}m", 0.09, "AGUA")
            # Zona saturada (líneas horizontales)
            y = y_nf - 0.20
            while y >= -H + 0.05:
                self._line(msp, e, y, e + suelo_w, y, "AGUA")
                y -= 0.20

        # ── Símbolos de apoyo ────────────────────────────────────────────────
        sym = 0.12
        # Corona (articulado)
        self._poly(msp, [(0, 0), (-sym, -sym), (sym, -sym)], "COTAS")
        self._line(msp, -sym, -sym, sym, -sym, "COTAS")
        # Base
        if res.condicion == 'empotrado_base':
            # Hash marks (empotramiento)
            for k in range(5):
                xk = -0.20 + k * 0.10
                self._line(msp, xk, -H - 0.20, xk - 0.10, -H - 0.32, "COTAS")
            self._line(msp, -0.22, -H - 0.20, 0.22, -H - 0.20, "COTAS")
        else:
            # Articulado base
            self._poly(msp, [(0, -H), (-sym, -H - sym), (sym, -H - sym)], "COTAS")
            self._line(msp, -sym, -H - sym, sym, -H - sym, "COTAS")

        # ── Presión activa ────────────────────────────────────────────────────
        x_pres = e + suelo_w + 0.50
        for i in range(9):
            z = H * i / 8
            p_a = c.Ka * (inp['gamma_r'] * z + inp['q_s'])
            self._flecha_pres(msp, e, -z, p_a * p_scl, "PRESION")

        if c.tiene_nf and h_NF < H:
            for i in range(7):
                z_w = (H - h_NF) * i / 6
                p_w = inp['gamma_w'] * z_w
                self._flecha_pres(msp, e, -(h_NF + z_w), p_w * p_scl, "HIDRO")

        # ── Diagrama de momentos (esquemático, a la izquierda) ───────────────
        M_ref = max(abs(m.M_max), abs(m.M_base), 0.1)
        M_scl = min(0.6 / M_ref, 0.15)
        # Puntos del diagrama: bilineal aprox
        z_max = m.z_max
        M_nod = [
            (0,      0),
            (z_max,  m.M_max),
            (H,     -abs(m.M_base) if res.condicion == 'empotrado_base' else 0),
        ]
        pts_diag = []
        for z, Mval in M_nod:
            pts_diag.append((-0.30 - Mval * M_scl, -z))
        pts_diag_closed = [(-0.30, 0)] + pts_diag + [(-0.30, -H)]
        self._poly(msp, pts_diag_closed, "ACERO", closed=True)
        self._text(msp, -0.30 - m.M_max * M_scl - 0.30, -z_max,
                   f"M_max={m.M_max:.2f}", 0.09, "ACERO")
        if res.condicion == 'empotrado_base' and abs(m.M_base) > 0.1:
            self._text(msp, -0.30 - abs(m.M_base) * M_scl - 0.30, -H + 0.10,
                       f"M_base={m.M_base:.2f}", 0.09, "ACERO")
        self._text(msp, -1.80, -H / 2, "M [kN·m/m]", 0.09, "ACERO")

        # ── Cotas ────────────────────────────────────────────────────────────
        self._cota_v(msp, -H, 0, -0.80, 0, f"H={H:.2f}m")
        self._cota_h(msp, 0, e, 0.20, 0, f"e={e:.2f}m")
        if c.tiene_nf and h_NF < H:
            self._cota_v(msp, -h_NF, 0, e + suelo_w + 0.80, e + suelo_w,
                         f"h_NF={h_NF:.2f}m")

        # ── Tabla de datos ───────────────────────────────────────────────────
        tx = -2.50
        ty = -H - 0.40 - 2.00

        cond_lbl = ("Empotrado en base" if res.condicion == 'empotrado_base'
                    else "Biapoyado")
        self._titulo_plano(msp, tx, ty,
                           "MURO DE SÓTANO — SECCIÓN TRANSVERSAL",
                           f"H={H:.2f}m  e={e:.2f}m  {cond_lbl}")
        ty -= 0.80
        filas_inp = [
            ("Altura libre H",        f"{H:.2f} m"),
            ("Espesor muro e",        f"{e:.2f} m"),
            ("Nivel freático h_NF",   f"{h_NF:.2f} m" + ("" if c.tiene_nf else " (sin NF)")),
            ("Condición de apoyo",    cond_lbl),
            ("Ka (Rankine)",          f"{c.Ka:.4f}"),
            ("γ suelo / φ",           f"{inp['gamma_r']:.1f} kN/m³  /  {inp['phi_r']:.0f}°"),
            ("q_s (sobrecarga)",      f"{inp['q_s']:.1f} kPa"),
        ]
        filas_res = [
            ("R_top (losa techo)",    f"{m.R_top:.2f} kN/m"),
            ("R_bot (losa piso)",     f"{m.R_bot:.2f} kN/m"),
            ("M_max positivo (vano)", f"{m.M_max:.3f} kN·m/m  @  z={m.z_max:.2f}m"),
            ("M_base (empotr.)",      f"{m.M_base:.3f} kN·m/m"),
            ("Ea total",              f"{c.Ea:.2f} kN/m"),
            ("Ew (hidrostático)",     f"{c.Ew:.2f} kN/m"),
            ("p_total en base",       f"{c.p_total_base:.1f} kPa"),
        ]
        filas_arm = [
            ("Vert. cara suelo (M+)",  res.vert_cara_suelo.barra),
            ("Vert. cara int.  (M-)",  res.vert_cara_int.barra),
            ("Horiz. temp./c/cara",    res.horiz_temp.barra),
        ]
        ty = self._tabla(msp, tx, ty, filas_inp, "DATOS DE ENTRADA") - 0.40
        ty = self._tabla(msp, tx, ty, filas_res, "RESULTADOS") - 0.40
        self._tabla(msp, tx, ty, filas_arm, "ARMADURA PRINCIPAL")

    def _fallback_txt(self, ruta, motor):
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("DXF no disponible: instalar ezdxf\n")
