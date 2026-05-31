"""
Generador PDF — Viga de Fundación (Winkler MEF).
Produce una memoria de cálculo con:
  - Portada
  - Datos de entrada (columnas, geometría, suelo, materiales)
  - Clasificación Winkler (lambda, rígida/flexible) + envolventes MEF
  - Imagen de diagramas (deformada, q, V, M)
  - Diseño de armadura longitudinal
  - Verificación de cortante y estribos
  - Registro de verificaciones
"""

import os
from datetime import datetime

try:
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, KeepTogether, Image as RLImage,
    )
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False

_AZUL  = "#1565C0"
_VERDE = "#2E7D32"
_ROJO  = "#C62828"
_CABEC = "#E3F2FD"
_GRIS  = "#CCCCCC"


def _ok(v):  return colors.HexColor("#E8F5E9") if v else colors.HexColor("#FFEBEE")
def _txt(v): return "CUMPLE" if v else "NO CUMPLE"


class GeneradorPDFViga:

    def generar(self, ruta: str, motor, datos_entrada: dict,
                imagen_diagramas: str = None):
        if not _REPORTLAB:
            self._generar_txt(ruta, motor, datos_entrada)
            return
        self._generar_pdf(ruta, motor, datos_entrada, imagen_diagramas)

    # ── Documento ───────────────────────────────────────────────────────────

    def _generar_pdf(self, ruta, motor, datos_entrada, imagen_diagramas):
        MARGEN = 2.0 * cm
        ANCHO, _ = A4
        ANCHO_UTIL = ANCHO - 2 * MARGEN

        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            leftMargin=MARGEN, rightMargin=MARGEN,
            topMargin=MARGEN, bottomMargin=MARGEN,
        )

        est = getSampleStyleSheet()
        est.add(ParagraphStyle('T1', parent=est['Heading1'], fontSize=16,
                               spaceAfter=10, textColor=colors.HexColor(_AZUL)))
        est.add(ParagraphStyle('T2', parent=est['Heading2'], fontSize=12,
                               spaceAfter=6,  textColor=colors.HexColor(_AZUL)))
        est.add(ParagraphStyle('Cuerpo', parent=est['Normal'], fontSize=9.5, spaceAfter=3))
        est.add(ParagraphStyle('Pie', parent=est['Normal'], fontSize=8,
                               textColor=colors.gray, spaceAfter=2))

        norma = datos_entrada.get("norma", "ACI318")
        res   = motor.res

        h = []
        h += self._portada(est, norma)
        h.append(PageBreak())
        h += self._datos_entrada(est, motor, datos_entrada)
        h.append(PageBreak())
        h += self._clasificacion(est, motor)
        if imagen_diagramas and os.path.isfile(imagen_diagramas):
            h.append(PageBreak())
            h += self._pagina_imagen(
                est,
                "Diagramas MEF — deformada, presion de contacto, cortante, momento",
                imagen_diagramas, ANCHO_UTIL, ANCHO_UTIL * 0.85,
            )
        h.append(PageBreak())
        h += self._armadura(est, motor)
        h.append(PageBreak())
        h += self._cortante(est, motor)
        h.append(PageBreak())
        h += self._mensajes(est, res)

        doc.build(h)

    # ── Portada ─────────────────────────────────────────────────────────────

    def _portada(self, est, norma):
        azul  = colors.HexColor(_AZUL)
        gris  = colors.HexColor("#546E7A")
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        st_titulo = ParagraphStyle('pT',  fontSize=36, textColor=azul,
                                   alignment=TA_CENTER, leading=44,
                                   spaceBefore=0, spaceAfter=8)
        st_sub    = ParagraphStyle('pS',  fontSize=15, textColor=gris,
                                   alignment=TA_CENTER, leading=20,
                                   spaceBefore=0, spaceAfter=0)
        st_mem    = ParagraphStyle('pM',  fontSize=22, textColor=azul,
                                   alignment=TA_CENTER, leading=28,
                                   spaceBefore=0, spaceAfter=8)
        st_mod    = ParagraphStyle('pMd', fontSize=13,
                                   textColor=colors.HexColor("#37474F"),
                                   alignment=TA_CENTER, leading=18,
                                   spaceBefore=0, spaceAfter=0)

        p = [
            Spacer(1, 3*cm),
            Paragraph("FundaCalc", st_titulo),
            Spacer(1, 0.3*cm),
            Paragraph("Diseno de Cimentaciones", st_sub),
            Spacer(1, 2.5*cm),
            Paragraph("MEMORIA DE CALCULO", st_mem),
            Spacer(1, 0.4*cm),
            Paragraph("Modulo 7 — Viga de Fundacion", st_mod),
            Spacer(1, 2.5*cm),
        ]

        tbl = Table(
            [["Norma de diseno:",     norma],
             ["Metodo de calculo:",   "MEF — Winkler (Hetenyi)"],
             ["Fecha de emision:",    fecha],
             ["Version:",             "1.0"]],
            colWidths=[5.5*cm, 8*cm],
            hAlign='CENTER',
        )
        tbl.setStyle(TableStyle([
            ('FONTSIZE',      (0, 0), (-1, -1), 10),
            ('TEXTCOLOR',     (0, 0), (0, -1), azul),
            ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME',      (1, 0), (1, -1), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING',    (0, 0), (-1, -1), 7),
            ('LINEBELOW',     (0, 0), (-1, -2), 0.3, colors.HexColor("#BBDEFB")),
        ]))
        p.append(tbl)
        return p

    # ── Datos de entrada ────────────────────────────────────────────────────

    def _datos_entrada(self, est, motor, datos_entrada):
        res  = motor.res
        geo  = motor.geo
        sue  = motor.suelo
        cols = motor.columnas

        h = [Paragraph("1. Datos de Entrada", est['T1'])]

        h.append(self._tbl("Geometria de la Viga", [
            ["Longitud total (L)",    f"{res.L:.2f} m"],
            ["Ancho (B)",             f"{res.B:.2f} m"],
            ["Altura (h)",            f"{res.h:.2f} m"],
            ["Peralte efectivo (d)",  f"{res.d:.3f} m"],
            ["Recubrimiento libre",   f"{geo.recubrimiento*100:.1f} cm"],
            ["Vuelo izquierdo",       f"{geo.vuelo_izq:.2f} m"],
            ["Vuelo derecho",         f"{geo.vuelo_der:.2f} m"],
        ]))

        h.append(self._tbl("Materiales", [
            ["Resistencia hormigon (f'c)", f"{motor.hormigon.fck:.0f} MPa"],
            ["Fluencia acero (fy)",        f"{motor.acero.fy:.0f} MPa"],
            ["Norma de diseno",            datos_entrada.get("norma", "ACI318")],
        ]))

        h.append(self._tbl("Parametros de Suelo", [
            ["Coef. de balasto (ks)",      f"{sue.ks:.0f} kN/m3"],
            ["Presion admisible (qa)",     f"{sue.qa:.1f} kN/m2"],
        ]))

        # Tabla de columnas
        azul = colors.HexColor(_AZUL)
        tbl_data = [["Columna", "x [m]", "Pd [kN]", "Pl [kN]", "Pu [kN]", "Pser [kN]"]]
        for c in cols:
            tbl_data.append([
                c.etiqueta or "—",
                f"{c.x:.2f}",
                f"{c.Pd:.1f}",
                f"{c.Pl:.1f}",
                f"{c.Pu:.1f}",
                f"{c.Pser:.1f}",
            ])
        tbl_col = Table(
            tbl_data,
            colWidths=[3.0*cm, 3.0*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm],
        )
        tbl_col.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('TEXTCOLOR',     (0, 0), (-1, 0), azul),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('ALIGN',         (1, 1), (-1, -1), 'CENTER'),
        ]))
        h += [Spacer(1, 0.3*cm), Paragraph("Columnas", est['T2']), tbl_col]

        return h

    # ── Clasificacion Winkler ────────────────────────────────────────────────

    def _clasificacion(self, est, motor):
        res = motor.res

        h = [Paragraph("2. Clasificacion — Modelo Winkler (Hetenyi)", est['T1'])]

        # Parámetros calculados (acceso a atributos internos del motor)
        E_MPa  = getattr(motor, '_E',  0.0) / 1000.0
        I_m4   = getattr(motor, '_I',  0.0)
        EI_kNm = getattr(motor, '_EI', 0.0)

        tipo = "FLEXIBLE" if res.flexible else "RIGIDA"

        h.append(self._tbl("Parametros de Clasificacion", [
            ["Modulo de elasticidad (E)",        f"{E_MPa:.0f} MPa"],
            ["Inercia de la seccion (I)",         f"{I_m4:.6f} m4"],
            ["Rigidez EI",                        f"{EI_kNm:.1f} kN.m2"],
            ["Parametro caracteristico (lambda)", f"{res.lambda_char:.5f} m-1"],
            ["lambda x L",                        f"{res.L_char:.3f}"],
            ["Criterio (pi = 3.1416)",            f"lambda*L {'>' if res.flexible else '<='} pi"],
            ["Tipo de viga",                      tipo],
        ]))

        nota = (
            "Viga RIGIDA: la deformacion es practicamente uniforme a lo largo de la viga."
            if not res.flexible else
            "Viga FLEXIBLE: la distribucion de presiones y momentos varia "
            "significativamente a lo largo de la viga."
        )
        bg = "#E8F5E9" if not res.flexible else "#FFF3E0"
        st_nota = ParagraphStyle('nota', parent=est['Normal'], fontSize=9.5,
                                 backColor=colors.HexColor(bg),
                                 borderPadding=8, spaceAfter=6)
        h += [Spacer(1, 0.2*cm), Paragraph(nota, st_nota)]

        # Envolventes MEF
        bg_q = _ok(res.ok_presion)
        h.append(self._tbl("Envolventes de Diseno (MEF — Pu = 1.2Pd + 1.6Pl)", [
            ["Presion de contacto maxima (q_max)", f"{res.q_max:.2f} kN/m2"],
            ["Presion admisible (qa)",              f"{motor.suelo.qa:.1f} kN/m2"],
            ["Verificacion presion",               _txt(res.ok_presion)],
            ["Momento maximo positivo (M+)",        f"{res.M_max_pos:.2f} kN.m"],
            ["Momento maximo negativo (M-)",        f"{res.M_max_neg:.2f} kN.m"],
            ["Cortante maximo absoluto (V_max)",    f"{res.V_max:.2f} kN"],
        ]))

        return h

    # ── Armadura longitudinal ────────────────────────────────────────────────

    def _armadura(self, est, motor):
        res = motor.res
        h = [Paragraph("3. Diseno de Armadura Longitudinal", est['T1'])]

        h.append(self._tbl("Acero Minimo (ACI 318-19 art. 9.6.1.2)", [
            ["As_min", f"{res.As_min:.2f} cm2"],
        ]))

        h.append(Paragraph("Armadura Inferior — zona de momento positivo (M+)", est['T2']))
        h.append(self._tbl("Armadura Inferior", [
            ["Momento de diseno (M+)",        f"{res.M_max_pos:.2f} kN.m"],
            ["As requerido por calculo",      f"{res.As_req_inf:.2f} cm2"],
            ["As minimo aplicado",            f"{res.As_min:.2f} cm2"],
            ["Varilla seleccionada",          res.var_inf],
            ["Numero de barras",              str(res.n_inf)],
            ["As dispuesto",                  f"{res.As_dis_inf:.2f} cm2"],
            ["Separacion entre barras",       f"{res.sep_inf*100:.1f} cm"],
        ]))

        h.append(Paragraph("Armadura Superior — zona de momento negativo (M-)", est['T2']))
        h.append(self._tbl("Armadura Superior", [
            ["Momento de diseno (M-)",        f"{res.M_max_neg:.2f} kN.m"],
            ["As requerido por calculo",      f"{res.As_req_sup:.2f} cm2"],
            ["As minimo aplicado",            f"{res.As_min:.2f} cm2"],
            ["Varilla seleccionada",          res.var_sup],
            ["Numero de barras",              str(res.n_sup)],
            ["As dispuesto",                  f"{res.As_dis_sup:.2f} cm2"],
            ["Separacion entre barras",       f"{res.sep_sup*100:.1f} cm"],
        ]))

        return h

    # ── Cortante y estribos ─────────────────────────────────────────────────

    def _cortante(self, est, motor):
        res = motor.res
        h = [Paragraph("4. Verificacion de Cortante y Estribos", est['T1'])]

        h.append(self._tbl("Cortante en Seccion Critica (ACI 318 art. 22.5.5)", [
            ["Cortante de diseno (Vu)",     f"{res.Vu_max:.2f} kN"],
            ["fi*Vc (resistencia hormigon)", f"{res.phi_Vc:.2f} kN"],
            ["Verificacion cortante",        _txt(res.ok_cortante)],
            ["Av/s requerido",              f"{res.Av_s:.3f} cm2/m"],
        ]))

        h.append(self._tbl("Estribos Seleccionados (2 ramas)", [
            ["Diametro del estribo",        res.var_estribo],
            ["Separacion (s)",              f"{res.s_estribo*100:.0f} cm"],
            ["Numero de ramas",             "2"],
            ["s_max ACI (min(d/2, 600mm))", f"{min(motor.geo.d/2, 0.60)*100:.0f} cm"],
        ]))

        return h

    # ── Imagen de diagramas ─────────────────────────────────────────────────

    def _pagina_imagen(self, est, titulo, ruta_img, ancho, alto):
        h = [Paragraph(titulo, est['T1'])]
        try:
            img = RLImage(ruta_img, width=ancho, height=alto)
            h.append(img)
        except Exception as exc:
            h.append(Paragraph(f"[Imagen no disponible: {exc}]", est['Cuerpo']))
        return h

    # ── Mensajes ────────────────────────────────────────────────────────────

    def _mensajes(self, est, res):
        h = [Paragraph("5. Registro de Verificaciones", est['T1'])]
        color_map = {
            "ok": _VERDE, "error": _ROJO,
            "advertencia": "#E65100", "info": _AZUL,
        }
        prefijo_map = {"ok": "OK ", "error": "FALLA ", "advertencia": "AVISO ", "info": "INFO "}
        for m in res.mensajes:
            tipo = m.get("tipo", "info")
            col  = color_map.get(tipo, "#000000")
            pre  = prefijo_map.get(tipo, "• ")
            st = ParagraphStyle('msg', parent=est['Normal'], fontSize=8.5,
                                textColor=colors.HexColor(col),
                                spaceAfter=2, leftIndent=10)
            h.append(Paragraph(f"{pre}  {m.get('texto', '')}", st))
        return h

    # ── Helper tabla clave-valor ─────────────────────────────────────────────

    def _tbl(self, titulo, filas, col_w=None):
        col_w = col_w or [9*cm, 6*cm]
        azul  = colors.HexColor(_AZUL)
        data  = [[titulo, ""]] + filas
        tbl   = Table(data, colWidths=col_w)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9.5),
            ('SPAN',          (0, 0), (-1, 0)),
            ('TEXTCOLOR',     (0, 0), (-1, 0), azul),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ]))
        return KeepTogether([Spacer(1, 0.3*cm), tbl])

    # ── Fallback texto plano ─────────────────────────────────────────────────

    def _generar_txt(self, ruta, motor, datos_entrada):
        res = motor.res
        lineas = [
            "MEMORIA DE CALCULO — Viga de Fundacion (FundaCalc)",
            "=" * 60,
            f"Norma: {datos_entrada.get('norma', 'ACI318')}",
            f"Metodo: MEF Winkler (Hetenyi)",
            "",
            "GEOMETRIA",
            f"  L={res.L:.2f}m  B={res.B:.2f}m  h={res.h:.2f}m  d={res.d:.3f}m",
            "",
            "CLASIFICACION",
            f"  lambda={res.lambda_char:.5f} 1/m  lambda*L={res.L_char:.3f}",
            f"  Tipo: {'FLEXIBLE' if res.flexible else 'RIGIDA'}",
            "",
            "ENVOLVENTES MEF",
            f"  q_max={res.q_max:.2f} kN/m2  qa={motor.suelo.qa:.1f} kN/m2",
            f"  M+={res.M_max_pos:.2f} kN.m  M-={res.M_max_neg:.2f} kN.m  V_max={res.V_max:.2f} kN",
            "",
            "ARMADURA LONGITUDINAL",
            f"  Inferior: {res.n_inf}{res.var_inf}  As_dis={res.As_dis_inf:.2f} cm2",
            f"  Superior: {res.n_sup}{res.var_sup}  As_dis={res.As_dis_sup:.2f} cm2",
            "",
            "CORTANTE Y ESTRIBOS",
            f"  Vu={res.Vu_max:.2f} kN  phiVc={res.phi_Vc:.2f} kN  "
            f"{'OK' if res.ok_cortante else 'FALLA'}",
            f"  Estribos: {res.var_estribo} @ {res.s_estribo*100:.0f} cm (2 ramas)",
        ]
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))
