"""
Generador PDF — Módulo 8B · Asentamientos (Schmertmann + Terzaghi).
"""
from datetime import datetime

try:
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    )
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False

_AZUL   = "#1565C0"
_VERDE  = "#2E7D32"
_CABEC  = "#E3F2FD"
_GRIS   = "#CCCCCC"
_NARANJA = "#E65100"


class GeneradorPDFAsentamientos:

    def generar(self, ruta: str, motor_s=None, motor_t=None):
        """
        motor_s: instancia de AsentamientoSchmertmann (o None)
        motor_t: instancia de AsentamientoTerzaghi   (o None)
        """
        if not _REPORTLAB:
            self._generar_txt(ruta, motor_s, motor_t)
            return
        self._generar_pdf(ruta, motor_s, motor_t)

    def _generar_pdf(self, ruta, ms, mt):
        MARGEN = 2.0 * cm
        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            leftMargin=MARGEN, rightMargin=MARGEN,
            topMargin=MARGEN, bottomMargin=MARGEN,
        )
        sty = getSampleStyleSheet()
        sty.add(ParagraphStyle('T1', parent=sty['Heading1'], fontSize=15,
                               leading=19, spaceAfter=8,
                               textColor=colors.HexColor(_AZUL)))
        sty.add(ParagraphStyle('T2', parent=sty['Heading2'], fontSize=11,
                               leading=15, spaceBefore=12, spaceAfter=5,
                               textColor=colors.HexColor(_AZUL)))
        sty.add(ParagraphStyle('N',  parent=sty['Normal'], fontSize=9, leading=13))
        sty.add(ParagraphStyle('Nc', parent=sty['Normal'], fontSize=9, leading=13,
                               alignment=TA_CENTER))

        story = []
        story.append(Paragraph("FundaCalc — Módulo 8B", sty['T1']))
        story.append(Paragraph("Asentamientos de Fundaciones", sty['T1']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"Fecha: {datetime.now():%d/%m/%Y %H:%M}", sty['N']))
        story.append(Spacer(1, 0.5 * cm))

        # ── SCHMERTMANN ──────────────────────────────────────────────────
        if ms:
            res = ms.res
            inp = ms._inp
            story.append(Paragraph("1. Asentamiento Inmediato — Schmertmann (1978)", sty['T2']))
            story += self._tbl2([
                ("Zapata B × L",       f"{inp['B']:.2f} m × {inp['L']:.2f} m"),
                ("Desplante Df",        f"{inp['Df']:.2f} m"),
                ("Presión total q",     f"{inp['q_total']:.1f} kPa"),
                ("Presión neta q_net",  f"{res.q_net:.1f} kPa"),
                ("γ suelo",             f"{inp['gamma']:.1f} kN/m³"),
                ("Tiempo t (creep)",    f"{inp['t']:.0f} años"),
            ], "Datos de entrada")
            story.append(Spacer(1, 0.2 * cm))
            story += self._tbl2([
                ("C₁ (empotramiento)",  f"{res.C1:.4f}"),
                ("C₂ (fluencia)",       f"{res.C2:.4f}"),
                ("Iz_peak",             f"{res.Iz_peak:.4f} a z = {res.z_peak:.2f} m"),
                ("z_max influencia",    f"{res.z_max:.2f} m"),
                ("Σ (Iz·Δz/Es)",        f"{res.suma_Iz_Es:.6f} m/kPa"),
                ("δᵢ (inmediato)",      f"<b>{res.delta_i:.1f} mm</b>"),
            ], "Resultados")
            story.append(Spacer(1, 0.2 * cm))

            # Tabla de capas
            story.append(Paragraph("Capas de suelo:", sty['N']))
            capa_data = [["Capa", "z_mid [m]", "Espesor [m]", "N60", "Es [kPa]", "Iz [-]", "Contrib [m/kPa]"]]
            for i, c in enumerate(res.capas, 1):
                capa_data.append([
                    str(i), f"{c.z_mid:.2f}", f"{c.espesor:.2f}",
                    f"{c.N60:.0f}", f"{c.Es:.0f}",
                    f"{c.Iz_mid:.3f}", f"{c.contrib:.2e}",
                ])
            story.append(self._tabla(capa_data,
                                      col_widths=[1*cm,2*cm,2.5*cm,1.5*cm,2.5*cm,2*cm,3*cm]))
            story.append(Spacer(1, 0.4 * cm))

        # ── TERZAGHI ─────────────────────────────────────────────────────
        if mt:
            res = mt.res
            inp = mt._inp
            story.append(Paragraph("2. Asentamiento por Consolidación — Terzaghi (1943)", sty['T2']))
            story += self._tbl2([
                ("Zapata B × L",            f"{inp['B']:.2f} m × {inp['L']:.2f} m"),
                ("Presión neta q_net",       f"{inp['q_net']:.1f} kPa"),
                ("Prof. centroide arcilla z_mid", f"{inp['z_mid']:.2f} m"),
                ("Espesor arcilla H_c",      f"{inp['H_c']:.2f} m"),
                ("Cc / Cs / e₀",            f"{inp['Cc']:.3f} / {inp['Cs']:.3f} / {inp['e0']:.3f}"),
                ("OCR",                      f"{inp['OCR']:.2f}"),
                ("σ'₀",                      f"{res.sigma0:.1f} kPa"),
                ("σ'p",                      f"{res.sigma_p:.1f} kPa"),
                ("Cv",                       f"{inp['Cv']:.4f} m²/año"),
                ("Drenaje",                  "Doble" if inp['doble_dren'] else "Simple"),
            ], "Datos de entrada")
            story.append(Spacer(1, 0.2 * cm))
            tipo = "Normalmente consolidada" if res.es_NC else "Sobreconsolidada"
            story += self._tbl2([
                ("Δσ (método 2:1)",      f"{res.delta_sig:.2f} kPa"),
                ("σ'f = σ'₀ + Δσ",      f"{res.sigma_f:.2f} kPa"),
                ("Tipo de consolidación", tipo),
                ("δ_c total",            f"<b>{res.delta_c:.1f} mm</b>"),
                ("  Componente OC",       f"{res.delta_c1:.1f} mm" if not res.es_NC else "—"),
                ("  Componente NC",       f"{res.delta_c2:.1f} mm" if not res.es_NC else f"{res.delta_c:.1f} mm"),
                ("H_dr",                 f"{res.H_dr:.2f} m"),
                ("t₅₀ (U=50%)",          f"{res.t50:.2f} años"),
                ("t₉₀ (U=90%)",          f"{res.t90:.2f} años"),
            ], "Resultados")

            # Tabla curva (cada 10% de U)
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph("Curva δ(t) seleccionada:", sty['N']))
            curva_data = [["t [años]", "Tv [-]", "U [%]", "δ [mm]"]]
            targets = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
            added = set()
            for pt in res.curva:
                for tgt in targets:
                    if abs(pt.U - tgt) < 2 and tgt not in added:
                        curva_data.append([f"{pt.t:.2f}", f"{pt.Tv:.4f}",
                                           f"{pt.U:.1f}", f"{pt.delta:.1f}"])
                        added.add(tgt)
            story.append(self._tabla(curva_data, col_widths=[3*cm,3*cm,3*cm,3*cm]))

        # ── Resumen total ─────────────────────────────────────────────────
        if ms and mt:
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph("3. Resumen", sty['T2']))
            d_total = ms.res.delta_i + mt.res.delta_c
            story += self._tbl2([
                ("δᵢ  (Schmertmann, inmediato)", f"{ms.res.delta_i:.1f} mm"),
                ("δ_c (Terzaghi, consolidación)", f"{mt.res.delta_c:.1f} mm"),
                ("δ_TOTAL estimado",              f"<b>{d_total:.1f} mm</b>"),
            ], "")

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Generado por FundaCalc — Módulo 8B Asentamientos", sty['Nc']))
        doc.build(story)

    def _tbl2(self, filas, titulo=""):
        rows = []
        if titulo:
            rows.append([Paragraph(f"<b>{titulo}</b>", getSampleStyleSheet()['Normal']), ""])
        for k, v in filas:
            rows.append([k, v])
        t = Table(rows, colWidths=[9 * cm, 7 * cm])
        t.setStyle(TableStyle([
            ('FONTSIZE',       (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor("#F5F9FF")]),
            ('GRID',           (0, 0), (-1, -1), 0.3, colors.HexColor("#CCDDEE")),
            ('TOPPADDING',     (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 3),
        ]))
        return [t, Spacer(1, 0.15 * cm)]

    def _tabla(self, data, col_widths=None):
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor(_GRIS)),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return t

    def _generar_txt(self, ruta, ms, mt):
        lines = ["FundaCalc — Módulo 8B: Asentamientos",
                 f"Fecha: {datetime.now():%d/%m/%Y %H:%M}", ""]
        if ms:
            lines += [f"SCHMERTMANN: δᵢ = {ms.res.delta_i:.1f} mm",
                      f"  C1={ms.res.C1:.3f}  C2={ms.res.C2:.3f}  q_net={ms.res.q_net:.1f}kPa", ""]
        if mt:
            lines += [f"TERZAGHI: δ_c = {mt.res.delta_c:.1f} mm",
                      f"  Δσ={mt.res.delta_sig:.2f}kPa  t50={mt.res.t50:.2f}a  t90={mt.res.t90:.2f}a", ""]
        if ms and mt:
            lines.append(f"δ_TOTAL = {ms.res.delta_i + mt.res.delta_c:.1f} mm")
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
