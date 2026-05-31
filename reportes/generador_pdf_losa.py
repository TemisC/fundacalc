"""
Generador PDF — Losa de Fundación (Mat Foundation).
Produce una memoria de cálculo con:
  - Portada
  - Datos de entrada
  - Geometría y presiones
  - Diagrama en planta / sección (imagen)
  - Momentos de diseño y armadura (4 capas)
  - Verificaciones de punzonado y cortante
  - Cómputo de materiales
  - Registro de verificaciones
"""

import os
import re
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

_BAR_KG_M = {8: 0.395, 10: 0.617, 12: 0.888, 16: 1.578,
             20: 2.466, 25: 3.854, 32: 6.313}

_AZUL  = "#1565C0"
_VERDE = "#2E7D32"
_ROJO  = "#C62828"
_CABEC = "#E3F2FD"
_GRIS  = "#CCCCCC"


def _db(varilla: str) -> int:
    m = re.search(r'(\d+)', varilla or '')
    return int(m.group(1)) if m else 16


def _ok(v): return colors.HexColor("#E8F5E9") if v else colors.HexColor("#FFEBEE")
def _txt(v): return "✔ CUMPLE" if v else "✘ NO CUMPLE"


class GeneradorPDFLosa:

    def generar(self, ruta: str, motor, datos_entrada: dict,
                imagen_seccion: str = None):
        if not _REPORTLAB:
            self._generar_txt(ruta, motor, datos_entrada)
            return
        self._generar_pdf(ruta, motor, datos_entrada, imagen_seccion)

    # ── Documento ───────────────────────────────────────────────────────────

    def _generar_pdf(self, ruta, motor, datos_entrada, imagen_seccion):
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
        h += self._geometria_presiones(est, motor, datos_entrada)
        if imagen_seccion:
            h.append(PageBreak())
            h += self._pagina_imagen(est, "Diagrama de la Losa (planta + sección)",
                                     imagen_seccion, ANCHO_UTIL, ANCHO_UTIL * 0.62)
        h.append(PageBreak())
        h += self._momentos_armadura(est, motor)
        h.append(PageBreak())
        h += self._verificaciones(est, motor)
        h.append(PageBreak())
        h += self._computo_materiales(est, motor)
        h.append(PageBreak())
        h += self._mensajes(est, res)

        doc.build(h)

    # ── Secciones ───────────────────────────────────────────────────────────

    def _portada(self, est, norma):
        azul  = colors.HexColor(_AZUL)
        gris  = colors.HexColor("#546E7A")
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Estilos de portada definidos como objetos completos (evita solapamiento)
        st_titulo = ParagraphStyle('pT',  fontSize=36, textColor=azul,
                                   alignment=TA_CENTER, leading=44,
                                   spaceBefore=0, spaceAfter=8)
        st_sub    = ParagraphStyle('pS',  fontSize=15, textColor=gris,
                                   alignment=TA_CENTER, leading=20,
                                   spaceBefore=0, spaceAfter=0)
        st_mem    = ParagraphStyle('pM',  fontSize=22, textColor=azul,
                                   alignment=TA_CENTER, leading=28,
                                   spaceBefore=0, spaceAfter=8)
        st_mod    = ParagraphStyle('pMd', fontSize=13, textColor=colors.HexColor("#37474F"),
                                   alignment=TA_CENTER, leading=18,
                                   spaceBefore=0, spaceAfter=0)

        p = [
            Spacer(1, 3*cm),
            Paragraph("FundaCalc", st_titulo),
            Spacer(1, 0.3*cm),
            Paragraph("Diseño de Cimentaciones", st_sub),
            Spacer(1, 2.5*cm),
            Paragraph("MEMORIA DE CÁLCULO", st_mem),
            Spacer(1, 0.4*cm),
            Paragraph("Módulo 4 — Losa de Fundación (Mat Foundation)", st_mod),
            Spacer(1, 2.5*cm),
        ]

        # Tabla de metadatos centrada
        tbl = Table(
            [["Norma de diseño:", norma],
             ["Fecha de emisión:", fecha],
             ["Versión:", "1.0"]],
            colWidths=[5.5*cm, 8*cm],
            hAlign='CENTER',
        )
        tbl.setStyle(TableStyle([
            ('FONTSIZE',     (0, 0), (-1, -1), 10),
            ('TEXTCOLOR',    (0, 0), (0, -1), azul),
            ('FONTNAME',     (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME',     (1, 0), (1, -1), 'Helvetica'),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 7),
            ('TOPPADDING',   (0, 0), (-1, -1), 7),
            ('LINEBELOW',    (0, 0), (-1, -2), 0.3, colors.HexColor("#BBDEFB")),
        ]))
        p.append(tbl)
        return p

    def _tbl(self, titulo, filas, col_w=None):
        col_w = col_w or [9*cm, 6*cm]
        azul  = colors.HexColor(_AZUL)
        tbl   = Table([[titulo, ""]] + filas, colWidths=col_w)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9.5),
            ('SPAN',       (0, 0), (-1, 0)),
            ('TEXTCOLOR',  (0, 0), (-1, 0), azul),
            ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ]))
        return KeepTogether([Spacer(1, 0.3*cm), tbl])

    def _datos_entrada(self, est, motor, datos_entrada):
        res  = motor.res
        geo  = motor.geo
        horm = motor.hormigon
        ace  = motor.acero
        sue  = motor.suelo
        u    = datos_entrada.get("unidades", {})
        fu   = u.get("cargas", "kN")
        pu   = u.get("presiones", "kN/m²")
        modo = datos_entrada.get("modo", "grilla")
        orig = datos_entrada.get("orig", {})

        p = [Paragraph("Datos de Entrada", est['T1'])]

        # Cargas según modo
        if modo == "grilla":
            filas_c = [
                ["Modo de carga", "Grilla de columnas"],
                ["Carga muerta total Pd", f"{orig.get('Pd_total', 0):.1f} {fu}"],
                ["Carga viva total Pl", f"{orig.get('Pl_total', 0):.1f} {fu}"],
                ["Columnas nx × ny", f"{datos_entrada.get('nx', 2)} × {datos_entrada.get('ny', 2)}"],
                ["Luz X sx", f"{datos_entrada.get('lx_span', 5.0):.2f} m"],
                ["Luz Y sy", f"{datos_entrada.get('ly_span', 5.0):.2f} m"],
            ]
        elif modo == "global":
            filas_c = [
                ["Modo de carga", "Carga global por columna"],
                ["Carga muerta Pd/columna", f"{orig.get('Pd', 0):.1f} {fu}"],
                ["Carga viva Pl/columna",   f"{orig.get('Pl', 0):.1f} {fu}"],
                ["Número de columnas", f"{datos_entrada.get('n_col', 4)}"],
            ]
        else:
            filas_c = [
                ["Modo de carga", "Presión uniforme equivalente"],
                ["q muerta qD", f"{orig.get('q_D', 0):.2f} kN/m²"],
                ["q viva qL",   f"{orig.get('q_L', 0):.2f} kN/m²"],
            ]
        p.append(self._tbl("Cargas de Diseño", filas_c))

        filas_geo = [
            ["Largo L (dirección X)", f"{res.L:.2f} m"],
            ["Ancho B (dirección Y)", f"{res.B:.2f} m"],
            ["Espesor h", f"{geo.h:.2f} m"],
            ["Recubrimiento r", f"{geo.recubrimiento*100:.1f} cm"],
            ["Canto útil d", f"{res.d:.3f} m"],
            ["Vuelo borde X", f"{geo.vuelo_x:.2f} m"],
            ["Vuelo borde Y", f"{geo.vuelo_y:.2f} m"],
            ["Dimensión columna cx", f"{geo.cx*100:.0f} cm"],
            ["Dimensión columna cy", f"{geo.cy*100:.0f} cm"],
        ]
        p.append(self._tbl("Geometría de la Losa", filas_geo))

        filas_sue = [
            ["Presión admisible qa", f"{sue.qa:.2f} {pu}"],
            ["Profundidad Df", f"{sue.Df:.2f} m"],
            ["Peso específico suelo γs", f"{sue.gamma_suelo:.1f} kN/m³"],
        ]
        p.append(self._tbl("Suelo", filas_sue))

        filas_mat = [
            ["Resistencia hormigón f'c / fck", f"{horm.fck:.1f} MPa"],
            ["Límite de fluencia acero fy", f"{ace.fy:.1f} MPa"],
        ]
        p.append(self._tbl("Materiales", filas_mat))
        return p

    def _geometria_presiones(self, est, motor, datos_entrada):
        res = motor.res
        sue = motor.suelo
        p   = [Paragraph("Geometría y Presiones del Suelo", est['T1'])]

        filas_geo = [
            ["Área A = L × B",         f"{res.A:.2f} m²"],
            ["Luz de diseño X",         f"{res.lx_diseno:.2f} m"],
            ["Luz de diseño Y",         f"{res.ly_diseno:.2f} m"],
            ["Carga factorizada Pu col",f"{res.Pu_col:.1f} kN"],
        ]
        p.append(self._tbl("Geometría Calculada", filas_geo))

        ok_nuc = getattr(res, 'en_nucleo', True)
        filas_pres = [
            ["Presión máx servicio q_max", f"{res.q_max:.2f} kN/m²"],
            ["Presión mín servicio q_min",  f"{res.q_min:.2f} kN/m²"],
            ["Presión promedio q_prom",     f"{res.q_prom:.2f} kN/m²"],
            ["Resultante en núcleo central",_txt(ok_nuc)],
            ["Presión admisible qa",        f"{sue.qa:.2f} kN/m²"],
            ["Verif. presión",              _txt(res.ok_presion)],
            ["qu neto promedio (diseño)",   f"{res.qu_net_avg:.2f} kN/m²"],
            ["qu neto máximo (diseño)",     f"{res.qu_net_max:.2f} kN/m²"],
        ]
        azul = colors.HexColor(_AZUL)
        tbl  = Table([["Presiones del Suelo", ""]] + filas_pres,
                     colWidths=[9*cm, 6*cm])
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9.5),
            ('SPAN',       (0, 0), (-1, 0)),
            ('TEXTCOLOR',  (0, 0), (-1, 0), azul),
            ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 6), (-1, 6), _ok(res.ok_presion)),
        ]
        tbl.setStyle(TableStyle(style))
        p.append(KeepTogether([Spacer(1, 0.3*cm), tbl]))
        return p

    def _pagina_imagen(self, est, titulo, ruta_img, ancho, alto):
        p = [Paragraph(titulo, est['T1'])]
        if ruta_img and os.path.exists(ruta_img):
            p.append(Spacer(1, 0.3*cm))
            p.append(RLImage(ruta_img, width=ancho, height=alto))
        return p

    def _momentos_armadura(self, est, motor):
        res = motor.res
        p   = [Paragraph("Momentos de Diseño y Armadura", est['T1'])]

        def sep_cm(v): return f"{v*100:.0f} cm" if v and v > 0 else "—"

        filas_mu = [
            ["Mu sup. apoyo X  (hogging)",   f"{res.Mu_sup_x:.1f} kN·m/m"],
            ["Mu inf. vano X   (sagging)",   f"{res.Mu_inf_x:.1f} kN·m/m"],
            ["Mu neg. voladizo X",            f"{res.Mu_cant_x:.1f} kN·m/m"],
            ["Mu sup. apoyo Y  (hogging)",   f"{res.Mu_sup_y:.1f} kN·m/m"],
            ["Mu inf. vano Y   (sagging)",   f"{res.Mu_inf_y:.1f} kN·m/m"],
            ["Mu neg. voladizo Y",            f"{res.Mu_cant_y:.1f} kN·m/m"],
        ]
        p.append(self._tbl("Momentos Críticos de Diseño [kN·m/m]", filas_mu))

        capas = [
            ("Sup-X (armadura superior paralela X)",
             res.As_req_sup_x, res.As_dis_sup_x, res.var_sup_x, res.sep_sup_x),
            ("Inf-X (armadura inferior paralela X)",
             res.As_req_inf_x, res.As_dis_inf_x, res.var_inf_x, res.sep_inf_x),
            ("Sup-Y (armadura superior paralela Y)",
             res.As_req_sup_y, res.As_dis_sup_y, res.var_sup_y, res.sep_sup_y),
            ("Inf-Y (armadura inferior paralela Y)",
             res.As_req_inf_y, res.As_dis_inf_y, res.var_inf_y, res.sep_inf_y),
        ]
        filas_arm = [["Capa", "As req.\n(cm²/m)", "As diseño\n(cm²/m)", "Varilla", "Sep."]]
        for nombre, as_req, as_dis, var, sep in capas:
            filas_arm.append([nombre, f"{as_req:.2f}", f"{as_dis:.2f}", var or "—", sep_cm(sep)])

        azul = colors.HexColor(_AZUL)
        tbl  = Table(filas_arm,
                     colWidths=[6.5*cm, 2.3*cm, 2.5*cm, 2.0*cm, 1.7*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ('TEXTCOLOR',  (0, 0), (-1, 0), azul),
            ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm),
                               Paragraph("Armadura — 4 Capas", est['T2']),
                               tbl]))

        p.append(Paragraph(
            f"As mínimo = {res.As_min:.2f} cm²/m  "
            "(controla cuando el momento requerido es muy pequeño).",
            ParagraphStyle('n', fontSize=8.5, textColor=colors.gray, spaceAfter=4)))
        return p

    def _verificaciones(self, est, motor):
        res = motor.res
        p   = [Paragraph("Verificaciones Estructurales", est['T1'])]

        filas_punz = [
            ["Carga factorizada columna Pu_col",    f"{res.Pu_col:.1f} kN"],
            ["Cortante punzonado Vu",               f"{res.Vu_punch:.1f} kN"],
            ["Resistencia φVc",                     f"{res.phi_Vc_punch:.1f} kN"],
            ["Verificación punzonado",              _txt(res.ok_punzonado)],
        ]
        azul = colors.HexColor(_AZUL)
        tbl_punz = Table([["Punzonado (Shear Two-Way)", ""]] + filas_punz,
                         colWidths=[9*cm, 6*cm])
        tbl_punz.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9.5),
            ('SPAN',       (0, 0), (-1, 0)),
            ('TEXTCOLOR',  (0, 0), (-1, 0), azul),
            ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 4), (-1, 4), _ok(res.ok_punzonado)),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm), tbl_punz]))

        filas_cort = [
            ["Cortante X: Vu_cx",       f"{res.Vu_cx:.1f} kN/m"],
            ["Resistencia X: φVc_cx",   f"{res.phi_Vc_cx:.1f} kN/m"],
            ["Verificación cortante X", _txt(res.ok_cx)],
            ["Cortante Y: Vu_cy",       f"{res.Vu_cy:.1f} kN/m"],
            ["Resistencia Y: φVc_cy",   f"{res.phi_Vc_cy:.1f} kN/m"],
            ["Verificación cortante Y", _txt(res.ok_cy)],
        ]
        tbl_cort = Table([["Cortante Unidireccional (One-Way Shear)", ""]] + filas_cort,
                         colWidths=[9*cm, 6*cm])
        tbl_cort.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9.5),
            ('SPAN',       (0, 0), (-1, 0)),
            ('TEXTCOLOR',  (0, 0), (-1, 0), azul),
            ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 3), (-1, 3), _ok(res.ok_cx)),
            ('BACKGROUND', (0, 6), (-1, 6), _ok(res.ok_cy)),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm), tbl_cort]))
        return p

    def _computo_materiales(self, est, motor):
        res  = motor.res
        L, B = res.L, res.B
        azul = colors.HexColor(_AZUL)
        p    = [Paragraph("Cómputo de Materiales", est['T1'])]

        capas = [
            ("Sup-X", res.var_sup_x, res.sep_sup_x, B, "sup. // X"),
            ("Inf-X", res.var_inf_x, res.sep_inf_x, B, "inf. // X"),
            ("Sup-Y", res.var_sup_y, res.sep_sup_y, L, "sup. // Y"),
            ("Inf-Y", res.var_inf_y, res.sep_inf_y, L, "inf. // Y"),
        ]

        hdrs   = ["Capa", "Descripción", "Ø (mm)", "Cant.", "Long. (m)", "kg/m", "Total (kg)"]
        filas  = [hdrs]
        total  = 0.0
        for marca, var, sep, long_barra, desc in capas:
            if not var or sep <= 0:
                continue
            db   = _db(var)
            kg_m = _BAR_KG_M.get(db, 1.578)
            n    = max(1, round(long_barra / sep) + 1)
            long_total = long_barra + 0.30   # gancho
            subtot = n * long_total * kg_m
            total += subtot
            filas.append([marca, f"Arm. {desc}", str(db), str(n),
                          f"{long_total:.2f}", f"{kg_m:.3f}", f"{subtot:.1f}"])

        filas.append(["", "TOTAL ACERO", "", "", "", "", f"{total:.1f}"])

        # Hormigón
        vol_h = L * B * res.h
        filas_horm = [
            ["", "Hormigón losa", "—", "—", "—", f"{vol_h:.2f} m³", "—"],
        ]

        tbl = Table(filas + filas_horm,
                    colWidths=[1.5*cm, 4.5*cm, 1.8*cm, 1.5*cm, 2.3*cm, 2.0*cm, 2.2*cm])
        n_data = len(filas) + len(filas_horm)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 8.5),
            ('TEXTCOLOR',  (0, 0), (-1, 0), azul),
            ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, len(filas)-1), (-1, len(filas)-1),
             colors.HexColor("#FFF3E0")),
            ('FONTNAME',   (0, len(filas)-1), (-1, len(filas)-1), 'Helvetica-Bold'),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm), tbl]))
        notas = [
            "• Cantidades son para la losa completa.",
            "• Acero: no incluye desperdicio (agregar 5–10 % en obra).",
            "• Long. incluye 30 cm de gancho estándar; sin longitudes de anclaje extremas.",
        ]
        for nota in notas:
            p.append(Paragraph(nota, ParagraphStyle('n', fontSize=8,
                                                     textColor=colors.gray, spaceAfter=2)))
        return p

    def _mensajes(self, est, res):
        azul  = colors.HexColor(_AZUL)
        verde = colors.HexColor(_VERDE)
        rojo  = colors.HexColor(_ROJO)
        p = [Paragraph("Registro de Verificaciones", est['T1'])]
        for msg in res.mensajes:
            c = verde if msg["tipo"] == "ok" else (rojo if msg["tipo"] == "error" else azul)
            p.append(Paragraph(msg["texto"],
                               ParagraphStyle('m', fontSize=9, textColor=c, spaceAfter=3)))
        return p

    # ── Fallback texto ──────────────────────────────────────────────────────

    def _generar_txt(self, ruta, motor, datos_entrada):
        res   = motor.res
        norma = datos_entrada.get("norma", "?")
        lines = [
            "FundaCalc — Losa de Fundación",
            f"Norma: {norma}   Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            "=" * 60,
            f"L={res.L:.2f} m  B={res.B:.2f} m  h={motor.geo.h:.2f} m  d={res.d:.3f} m",
            f"q_max={res.q_max:.1f} kN/m²  qa={motor.suelo.qa:.1f} kN/m²",
            f"qu_net_avg={res.qu_net_avg:.1f} kN/m²",
            f"Mu_sup_x={res.Mu_sup_x:.1f}  Mu_inf_x={res.Mu_inf_x:.1f} kN·m/m",
            f"Sup-X: {res.var_sup_x} @ {res.sep_sup_x*100:.0f} cm  As={res.As_dis_sup_x:.2f} cm²/m",
            f"Inf-X: {res.var_inf_x} @ {res.sep_inf_x*100:.0f} cm  As={res.As_dis_inf_x:.2f} cm²/m",
            f"Sup-Y: {res.var_sup_y} @ {res.sep_sup_y*100:.0f} cm  As={res.As_dis_sup_y:.2f} cm²/m",
            f"Inf-Y: {res.var_inf_y} @ {res.sep_inf_y*100:.0f} cm  As={res.As_dis_inf_y:.2f} cm²/m",
            f"Punzonado: Vu={res.Vu_punch:.1f} kN  φVc={res.phi_Vc_punch:.1f} kN  {'OK' if res.ok_punzonado else 'FALLA'}",
        ]
        with open(ruta.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
