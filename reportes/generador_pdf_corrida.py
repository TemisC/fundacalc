"""
Generador PDF para Zapata Corrida.
Produce una memoria de cálculo multi-página con:
  - Portada
  - Datos de entrada
  - Geometría y presiones
  - Vista en sección (imagen)
  - Verificaciones y armadura
  - Cómputo de materiales
  - Mensajes del cálculo
"""

import re
import os
import tempfile
import io
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
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False


_BAR_KG_M = {8: 0.395, 10: 0.617, 12: 0.888, 16: 1.578, 20: 2.466, 25: 3.854, 32: 6.313}


def _db_mm(varilla: str) -> int:
    m = re.search(r'(\d+)', varilla or '')
    return int(m.group(1)) if m else 16


class GeneradorPDFCorrida:

    def generar(self, ruta: str, motor, datos_entrada: dict,
                imagen_seccion: str = None):
        if not _REPORTLAB:
            self._generar_txt(ruta, motor, datos_entrada)
            return
        self._generar_pdf(ruta, motor, datos_entrada, imagen_seccion)

    # ── PDF completo ────────────────────────────────────────────────────────

    def _generar_pdf(self, ruta: str, motor, datos_entrada: dict,
                     imagen_seccion: str = None):
        ANCHO, ALTO = A4
        MARGEN = 2.0 * cm
        ANCHO_UTIL = ANCHO - 2 * MARGEN

        doc = SimpleDocTemplate(
            ruta,
            pagesize=A4,
            leftMargin=MARGEN, rightMargin=MARGEN,
            topMargin=MARGEN, bottomMargin=MARGEN,
        )

        estilos = getSampleStyleSheet()
        estilos.add(ParagraphStyle('Titulo1', parent=estilos['Heading1'],
                                   fontSize=16, spaceAfter=10, textColor=colors.HexColor("#1565C0")))
        estilos.add(ParagraphStyle('Titulo2', parent=estilos['Heading2'],
                                   fontSize=12, spaceAfter=6, textColor=colors.HexColor("#1565C0")))
        estilos.add(ParagraphStyle('Cuerpo', parent=estilos['Normal'],
                                   fontSize=9.5, spaceAfter=3))
        estilos.add(ParagraphStyle('CuerpoC', parent=estilos['Normal'],
                                   fontSize=9.5, alignment=TA_CENTER))
        estilos.add(ParagraphStyle('Pie', parent=estilos['Normal'],
                                   fontSize=8, textColor=colors.gray, spaceAfter=2))

        norma_nombre = datos_entrada.get("norma", "ACI318")
        res = motor.res

        h = []
        h += self._portada(estilos, norma_nombre)
        h.append(PageBreak())
        h += self._datos_entrada(estilos, motor, datos_entrada)
        h.append(PageBreak())
        h += self._geometria_presiones(estilos, motor, datos_entrada)
        h.append(PageBreak())
        if imagen_seccion:
            h += self._pagina_imagen(estilos, "Vista en Sección Transversal",
                                     imagen_seccion, ANCHO_UTIL, ANCHO_UTIL * 0.55)
            h.append(PageBreak())
        h += self._verificaciones_armadura(estilos, motor, datos_entrada)
        h.append(PageBreak())
        h += self._computo_materiales(estilos, motor)
        h.append(PageBreak())
        h += self._mensajes(estilos, res)

        doc.build(h)

    # ── Páginas ─────────────────────────────────────────────────────────────

    def _portada(self, estilos, norma_nombre: str) -> list:
        azul = colors.HexColor("#1565C0")
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        parrafos = [
            Spacer(1, 2 * cm),
            Paragraph("FundaCalc", ParagraphStyle('T', fontSize=32, textColor=azul,
                                                   alignment=TA_CENTER, spaceAfter=4)),
            Paragraph("Diseño de Cimentaciones", ParagraphStyle('S', fontSize=16,
                                                                  textColor=colors.gray,
                                                                  alignment=TA_CENTER, spaceAfter=30)),
            Spacer(1, 1.5 * cm),
            Paragraph("MEMORIA DE CÁLCULO",
                       ParagraphStyle('MC', fontSize=20, textColor=azul,
                                      alignment=TA_CENTER, spaceAfter=6)),
            Paragraph("Módulo 3 — Zapata Corrida (Strip Footing)",
                       ParagraphStyle('MT', fontSize=14, alignment=TA_CENTER, spaceAfter=40)),
            Spacer(1, 1.5 * cm),
        ]
        datos_portada = [
            ["Norma de diseño:", norma_nombre],
            ["Fecha:", fecha],
            ["Versión:", "1.0"],
        ]
        tbl = Table(datos_portada, colWidths=[5 * cm, 9 * cm])
        tbl.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), azul),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        parrafos.append(tbl)
        parrafos.append(Spacer(1, 2 * cm))
        parrafos.append(Paragraph(
            "Documento generado automáticamente. Verifique los resultados con un ingeniero calificado.",
            ParagraphStyle('D', fontSize=8, textColor=colors.gray, alignment=TA_CENTER)))
        return parrafos

    def _datos_entrada(self, estilos, motor, datos_entrada: dict) -> list:
        carga = motor.carga
        muro = motor.muro
        suelo = motor.suelo
        hormigon = motor.hormigon
        acero = motor.acero
        geo = motor.geo
        u = datos_entrada.get("unidades", {})
        fu = u.get("cargas", "kN/m")
        pu = u.get("presiones", "kN/m²")
        orig = datos_entrada.get("orig", {})

        parrafos = [Paragraph("Datos de Entrada", estilos['Titulo1'])]
        secciones = [
            ("Cargas (por metro lineal de muro)", [
                ["Carga muerta Pd", f"{orig.get('Pd', carga.Pd):.2f} {fu}"],
                ["Carga viva Pl",   f"{orig.get('Pl', carga.Pl):.2f} {fu}"],
                ["Carga total servicio Pser", f"{carga.Pser:.2f} kN/m"],
                ["Carga última Pu (1.2D+1.6L)", f"{carga.Pu:.2f} kN/m"],
            ]),
            ("Muro", [
                ["Espesor del muro t_muro", f"{muro.espesor:.2f} m"],
            ]),
            ("Suelo", [
                ["Presión admisible qa", f"{orig.get('qa', suelo.qa):.2f} {pu}"],
                ["Profundidad de empotramiento Df", f"{suelo.Df:.2f} m"],
                ["Peso específico del suelo γs", f"{suelo.gamma_suelo:.1f} kN/m³"],
            ]),
            ("Materiales", [
                ["Resistencia del hormigón f'c / fck", f"{hormigon.fck:.1f} MPa"],
                ["Límite de fluencia del acero fy",    f"{acero.fy:.1f} MPa"],
            ]),
            ("Geometría inicial", [
                ["Peralte total h",       f"{geo.h:.2f} m"],
                ["Recubrimiento r",       f"{geo.recubrimiento*100:.1f} cm"],
                ["Peralte efectivo d",    f"{geo.d:.3f} m"],
                ["Ancho fijo B (0=auto)", f"{geo.B_fijo:.2f} m"],
            ]),
        ]
        azul = colors.HexColor("#1565C0")
        for titulo, filas in secciones:
            tbl = Table([[titulo, ""]] + filas,
                        colWidths=[8 * cm, 7 * cm])
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E3F2FD")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9.5),
                ('SPAN', (0, 0), (-1, 0)),
                ('TEXTCOLOR', (0, 0), (-1, 0), azul),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            parrafos.append(KeepTogether([Spacer(1, 0.3 * cm), tbl]))
        return parrafos

    def _geometria_presiones(self, estilos, motor, datos_entrada: dict) -> list:
        res = motor.res
        u = datos_entrada.get("unidades", {})
        pu = u.get("presiones", "kN/m²")
        azul = colors.HexColor("#1565C0")

        parrafos = [Paragraph("Geometría y Presiones", estilos['Titulo1'])]

        filas_geo = [
            ["Ancho calculado B",      f"{res.B:.2f} m"],
            ["Peralte total h",        f"{res.h:.2f} m"],
            ["Peralte efectivo d",     f"{res.d:.3f} m"],
            ["Voladizo a = (B−t)/2",   f"{res.a:.3f} m"],
        ]
        filas_pres = [
            ["Presión neta admisible q_neto", f"{res.q_neto:.2f} kN/m²"],
            ["Presión servicio q_max",        f"{res.q_max:.2f} kN/m²  (≤ {motor.suelo.qa:.1f})"],
            ["Presión última qu",             f"{res.q_ultima:.2f} kN/m²"],
            ["OK presión",                    "✔ CUMPLE" if res.ok_presion else "✘ NO CUMPLE"],
        ]

        for titulo, filas in [("Geometría de la Zapata Corrida", filas_geo),
                               ("Presiones de Suelo", filas_pres)]:
            tbl = Table([[titulo, ""]] + filas, colWidths=[8 * cm, 7 * cm])
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E3F2FD")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9.5),
                ('SPAN', (0, 0), (-1, 0)),
                ('TEXTCOLOR', (0, 0), (-1, 0), azul),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            parrafos.append(KeepTogether([Spacer(1, 0.3 * cm), tbl]))
        return parrafos

    def _pagina_imagen(self, estilos, titulo: str, ruta_img: str,
                       ancho: float, alto: float) -> list:
        parrafos = [Paragraph(titulo, estilos['Titulo1'])]
        if ruta_img and os.path.exists(ruta_img):
            parrafos.append(Spacer(1, 0.3 * cm))
            parrafos.append(RLImage(ruta_img, width=ancho, height=alto))
        return parrafos

    def _verificaciones_armadura(self, estilos, motor, datos_entrada: dict) -> list:
        res = motor.res
        azul = colors.HexColor("#1565C0")
        verde = colors.HexColor("#2E7D32")
        rojo  = colors.HexColor("#C62828")

        def ok(v): return colors.HexColor("#E8F5E9") if v else colors.HexColor("#FFEBEE")
        def txt(v): return ("✔ CUMPLE" if v else "✘ NO CUMPLE")

        parrafos = [Paragraph("Verificaciones Estructurales y Armadura", estilos['Titulo1'])]

        # Verificación cortante
        filas_cort = [
            ["Cortante último Vu",         f"{res.Vu:.2f} kN/m"],
            ["Capacidad φVn",              f"{res.phi_Vn:.2f} kN/m"],
            ["Relación Vu/φVn",            f"{res.rel_cortante*100:.0f}%"],
            ["Verificación cortante",      txt(res.ok_cortante)],
        ]
        tbl_c = Table([["Verificación de Cortante Unidireccional (a dist. d de muro)", ""]] + filas_cort,
                      colWidths=[9 * cm, 6 * cm])
        tbl_c.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E3F2FD")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('SPAN', (0, 0), (-1, 0)),
            ('TEXTCOLOR', (0, 0), (-1, 0), azul),
            ('BACKGROUND', (0, 4), (-1, 4), ok(res.ok_cortante)),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        parrafos.append(KeepTogether([Spacer(1, 0.3 * cm), tbl_c]))

        # Armadura transversal
        filas_arm = [
            ["Momento último Mu",             f"{res.Mu:.2f} kN·m/m"],
            ["As requerido por flexión",       f"{res.As_req:.2f} cm²/m"],
            ["As mínimo",                      f"{res.As_min:.2f} cm²/m"],
            ["As de diseño (max)",             f"{res.As_diseno:.2f} cm²/m"],
            ["Varilla seleccionada",           res.varilla],
            ["Separación transversal",         f"{res.separacion*100:.0f} cm"],
            ["Barras por metro",               str(res.n_barras_por_metro)],
        ]
        tbl_a = Table([["Armadura Transversal (⊥ al muro — armadura principal)", ""]] + filas_arm,
                      colWidths=[9 * cm, 6 * cm])
        tbl_a.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E3F2FD")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('SPAN', (0, 0), (-1, 0)),
            ('TEXTCOLOR', (0, 0), (-1, 0), azul),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        parrafos.append(KeepTogether([Spacer(1, 0.3 * cm), tbl_a]))

        # Armadura longitudinal
        filas_long = [
            ["As longitudinal (mínimo)",       f"{res.As_long:.2f} cm²/m"],
            ["Varilla longitudinal",           res.varilla_long],
            ["Separación longitudinal",        f"{res.sep_long*100:.0f} cm"],
        ]
        tbl_l = Table([["Armadura Longitudinal (‖ al muro — mínima de temperatura)", ""]] + filas_long,
                      colWidths=[9 * cm, 6 * cm])
        tbl_l.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E3F2FD")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('SPAN', (0, 0), (-1, 0)),
            ('TEXTCOLOR', (0, 0), (-1, 0), azul),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        parrafos.append(KeepTogether([Spacer(1, 0.3 * cm), tbl_l]))
        return parrafos

    def _computo_materiales(self, estilos, motor) -> list:
        res = motor.res
        B = res.B
        h = res.h
        t = motor.muro.espesor
        azul = colors.HexColor("#1565C0")

        parrafos = [Paragraph("Cómputo de Materiales (por metro lineal de muro)", estilos['Titulo1'])]

        # Varillas transversales (1 m de muro, largo = B + 0.20 m ganchos)
        db_t  = _db_mm(res.varilla)
        kg_t  = _BAR_KG_M.get(db_t, 1.578)
        n_t   = res.n_barras_por_metro or (round(1.0 / res.separacion) if res.separacion > 0 else 0)
        L_t   = B + 0.20
        tot_t = n_t * L_t * kg_t

        # Varillas longitudinales (por metro de ancho B, largo = 1 m de referencia)
        db_l  = _db_mm(res.varilla_long)
        kg_l  = _BAR_KG_M.get(db_l, 0.888)
        # numero de barras longitudinales en altura (usualmente 2 capas: inferior y superior)
        n_l   = max(2, round(B / res.sep_long) + 1) if res.sep_long > 0 else 4
        L_l   = 1.0      # por metro lineal de muro
        tot_l = n_l * L_l * kg_l

        total_acero = tot_t + tot_l

        hdrs = ["Marca", "Descripción", "Ø (mm)", "Cant.", "Long. (m)", "kg/m", "Total (kg)"]
        filas = [
            ["A", "Arm. transversal (⊥ muro)", str(db_t), str(n_t), f"{L_t:.2f}", f"{kg_t:.3f}", f"{tot_t:.2f}"],
            ["B", "Arm. longitudinal (‖ muro)", str(db_l), str(n_l), f"{L_l:.2f}", f"{kg_l:.3f}", f"{tot_l:.2f}"],
            ["", "TOTAL ACERO", "", "", "", "", f"{total_acero:.2f}"],
        ]

        tbl = Table([hdrs] + filas,
                    colWidths=[1.5*cm, 5.5*cm, 1.8*cm, 1.5*cm, 2.2*cm, 1.8*cm, 2.2*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E3F2FD")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('TEXTCOLOR', (0, 0), (-1, 0), azul),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, len(filas)), (-1, len(filas)),
             colors.HexColor("#FFF3E0")),
            ('FONTNAME', (0, len(filas)), (-1, len(filas)), 'Helvetica-Bold'),
        ]))
        parrafos.append(KeepTogether([Spacer(1, 0.3 * cm), tbl]))

        leyenda_items = [
            "• Las cantidades son por metro lineal de muro.",
            "• No incluye desperdicio por corte y empalme (agregar 5–10 % en obra).",
            "• No incluye longitudes de anclaje en los extremos de la zapata.",
            "• Densidad del acero: ρ = 7 850 kg/m³.",
        ]
        for item in leyenda_items:
            parrafos.append(Paragraph(item, ParagraphStyle('ley', fontSize=8,
                                                            textColor=colors.gray, spaceAfter=2)))
        return parrafos

    def _mensajes(self, estilos, res) -> list:
        azul  = colors.HexColor("#1565C0")
        verde = colors.HexColor("#2E7D32")
        rojo  = colors.HexColor("#C62828")

        parrafos = [Paragraph("Registro de Verificaciones", estilos['Titulo1'])]
        for msg in res.mensajes:
            color = verde if msg["tipo"] == "ok" else (rojo if msg["tipo"] == "error" else azul)
            parrafos.append(Paragraph(
                msg["texto"],
                ParagraphStyle('msg', fontSize=9, textColor=color, spaceAfter=3)))
        return parrafos

    # ── Fallback texto plano ─────────────────────────────────────────────────

    def _generar_txt(self, ruta: str, motor, datos_entrada: dict):
        res = motor.res
        norma = datos_entrada.get("norma", "?")
        lines = [
            "FundaCalc — Zapata Corrida",
            f"Norma: {norma}   Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            "=" * 60,
            f"Carga Pser = {motor.carga.Pser:.2f} kN/m   Pu = {motor.carga.Pu:.2f} kN/m",
            f"Muro espesor = {motor.muro.espesor:.2f} m",
            f"qa = {motor.suelo.qa:.1f} kN/m²   Df = {motor.suelo.Df:.2f} m",
            "─" * 40,
            f"B = {res.B:.2f} m   h = {res.h:.2f} m   d = {res.d:.3f} m",
            f"Voladizo a = {res.a:.3f} m",
            f"q_max = {res.q_max:.1f} kN/m²   qu = {res.q_ultima:.1f} kN/m²",
            f"Mu = {res.Mu:.2f} kN·m/m   Vu = {res.Vu:.2f} kN/m",
            f"Arm. Trans.: {res.varilla} @ {res.separacion*100:.0f} cm  (As={res.As_diseno:.2f} cm²/m)",
            f"Arm. Long.:  {res.varilla_long} @ {res.sep_long*100:.0f} cm",
        ]
        ruta_txt = ruta.replace(".pdf", ".txt")
        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
