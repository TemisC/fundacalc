"""
Generador PDF — Módulo 9.5 · Muro de Sótano.
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

_AZUL    = "#1565C0"
_VERDE   = "#2E7D32"
_ROJO    = "#C62828"
_CABEC   = "#E3F2FD"
_GRIS    = "#CCCCCC"
_NARANJA = "#E65100"
_AZUL_W  = "#1565C0"


class GeneradorPDFMuroSotano:

    def generar(self, ruta: str, motor, norma: str = "ACI 318-19"):
        if not _REPORTLAB:
            self._generar_txt(ruta, motor, norma)
            return
        self._generar_pdf(ruta, motor, norma)

    def _generar_pdf(self, ruta, motor, norma):
        MARGEN = 2.0 * cm
        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            leftMargin=MARGEN, rightMargin=MARGEN,
            topMargin=MARGEN, bottomMargin=MARGEN,
        )

        sty = getSampleStyleSheet()
        sty.add(ParagraphStyle('T1', parent=sty['Heading1'], fontSize=16,
                               leading=20, spaceAfter=10,
                               textColor=colors.HexColor(_AZUL)))
        sty.add(ParagraphStyle('T2', parent=sty['Heading2'], fontSize=12,
                               leading=16, spaceBefore=14, spaceAfter=6,
                               textColor=colors.HexColor(_AZUL)))
        sty.add(ParagraphStyle('N',  parent=sty['Normal'], fontSize=9, leading=13))
        sty.add(ParagraphStyle('Nc', parent=sty['Normal'], fontSize=9, leading=13,
                               alignment=TA_CENTER))
        sty.add(ParagraphStyle('OK',  parent=sty['Normal'], fontSize=8, leading=12,
                               textColor=colors.HexColor(_VERDE)))
        sty.add(ParagraphStyle('ERR', parent=sty['Normal'], fontSize=8, leading=12,
                               textColor=colors.HexColor(_ROJO)))
        sty.add(ParagraphStyle('ADV', parent=sty['Normal'], fontSize=8, leading=12,
                               textColor=colors.HexColor(_NARANJA)))

        res = motor.res
        inp = motor._inp
        c   = res.cargas
        m   = res.momentos
        story = []

        # ── Portada ──────────────────────────────────────────────────────
        story.append(Paragraph("FundaCalc — Módulo 9.5", sty['T1']))
        story.append(Paragraph("Muro de Sótano", sty['T1']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            f"Norma: {norma} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Condición: {res.condicion.replace('_', ' ').title()} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Fecha: {datetime.now():%d/%m/%Y %H:%M}", sty['N']))
        story.append(Spacer(1, 0.5 * cm))

        # ── Datos de entrada ─────────────────────────────────────────────
        story.append(Paragraph("1. Datos de Entrada", sty['T2']))
        story += self._tbl2([
            ("Altura libre entre apoyos H",   f"{res.H:.2f} m"),
            ("Espesor del muro e",             f"{res.e_muro:.2f} m"),
            ("Nivel freático h_NF",            f"{res.h_NF:.2f} m" + (" (sin NF)" if not c.tiene_nf else "")),
            ("Condición de apoyo",             res.condicion.replace('_',' ').title()),
        ], "Geometría")
        story.append(Spacer(1, 0.2 * cm))
        story += self._tbl2([
            ("γ suelo retenido",  f"{inp['gamma_r']:.1f} kN/m³"),
            ("φ suelo retenido",  f"{inp['phi_r']:.1f} °"),
            ("c suelo retenido",  f"{inp['c_r']:.1f} kPa"),
            ("Sobrecarga q_s",    f"{inp['q_s']:.1f} kPa"),
            ("γ agua",            f"{inp['gamma_w']:.2f} kN/m³"),
            ("f'c",               f"{inp['fc']:.1f} MPa"),
            ("fy",                f"{inp['fy']:.1f} MPa"),
            ("Recubrimiento",     f"{inp['recub']*100:.0f} cm"),
        ], "Materiales y Suelo")

        # ── Cargas ───────────────────────────────────────────────────────
        story.append(Paragraph("2. Cargas Horizontales", sty['T2']))
        story += self._tbl2([
            ("Ka (Rankine)",              f"{c.Ka:.4f}"),
            ("Presión activa en corona",  f"{c.pa_corona:.2f} kPa"),
            ("Presión activa en base",    f"{c.pa_base:.2f} kPa"),
            ("Presión hidrostática base", f"{c.pw_base:.2f} kPa"),
            ("Presión TOTAL en la base",  f"{c.p_total_base:.2f} kPa"),
            ("Empuje activo Ea",          f"{c.Ea:.2f} kN/m"),
            ("Empuje hidrostático Ew",    f"{c.Ew:.2f} kN/m"),
            ("Fuerza horizontal total",   f"{c.E_total:.2f} kN/m"),
        ], "")

        # ── Momentos ─────────────────────────────────────────────────────
        story.append(Paragraph("3. Diagrama de Momentos", sty['T2']))
        story.append(Paragraph(
            f"Condición: {m.condicion.replace('_',' ').title()} &nbsp;|&nbsp; "
            f"R_top = {m.R_top:.2f} kN/m &nbsp;|&nbsp; R_bot = {m.R_bot:.2f} kN/m",
            sty['N']))
        story.append(Spacer(1, 0.2 * cm))
        story += self._tbl2([
            ("M_max positivo (vano)",     f"{m.M_max:.3f} kN·m/m"),
            ("z en M_max (desde corona)", f"{m.z_max:.3f} m"),
            ("M_base (empotramiento)",    f"{m.M_base:.3f} kN·m/m" if res.condicion == 'empotrado_base' else "— (articulado)"),
        ], "")

        # ── Diseño RC ────────────────────────────────────────────────────
        story.append(Paragraph("4. Diseño de Armadura (ACI 318-19)", sty['T2']))
        rc_data = [
            ["Elemento", "Mu [kN·m/m]", "d [m]", "As_req [cm²/m]", "As_mín [cm²/m]", "As_dis [cm²/m]", "Armadura"],
        ]
        for el in [res.vert_cara_suelo, res.vert_cara_int, res.horiz_temp]:
            rc_data.append([
                el.nombre,
                f"{el.Mu:.2f}" if el.Mu else "—",
                f"{el.d:.3f}",
                f"{el.As_req:.2f}" if el.As_req else "—",
                f"{el.As_min:.2f}",
                f"{el.As_dis:.2f}",
                el.barra,
            ])
        story.append(self._tabla(rc_data,
                                  col_widths=[4.5*cm, 2.5*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm]))
        story.append(Spacer(1, 0.15 * cm))
        for el in [res.vert_cara_suelo, res.vert_cara_int, res.horiz_temp]:
            story.append(Paragraph(f"↳ {el.nota}", sty['N']))

        # ── Mensajes ─────────────────────────────────────────────────────
        story.append(Paragraph("5. Mensajes del Verificador", sty['T2']))
        for msg in res.mensajes:
            stl = {'ok': 'OK', 'error': 'ERR', 'advertencia': 'ADV'}.get(msg['tipo'], 'N')
            story.append(Paragraph(f"▸ {msg['texto']}", sty[stl]))

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(
            "Generado por FundaCalc — Módulo 9.5 Muro de Sótano",
            sty['Nc']))

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
            ('BACKGROUND',    (0, 0), (-1,  0), colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0), (-1,  0), 'Helvetica-Bold'),
            ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor(_GRIS)),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return t

    def _generar_txt(self, ruta, motor, norma):
        res = motor.res
        m   = res.momentos
        lines = [
            "FundaCalc — Módulo 9.5: Muro de Sótano",
            f"Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            "",
            f"H={res.H:.2f}m  e={res.e_muro:.2f}m  h_NF={res.h_NF:.2f}m  cond={res.condicion}",
            f"Ka={res.Ka:.4f}  Ea={res.cargas.Ea:.2f}kN/m  Ew={res.cargas.Ew:.2f}kN/m",
            f"R_top={m.R_top:.2f}kN/m  R_bot={m.R_bot:.2f}kN/m",
            f"M_max={m.M_max:.2f}kN.m/m a z={m.z_max:.2f}m  M_base={m.M_base:.2f}kN.m/m",
            "",
            "Diseño RC:",
        ]
        for el in [res.vert_cara_suelo, res.vert_cara_int, res.horiz_temp]:
            lines.append(f"  {el.nombre}: Mu={el.Mu:.2f}  As_dis={el.As_dis:.2f}cm²/m  {el.barra}")
        lines.append("")
        for msg in res.mensajes:
            lines.append(f"[{msg['tipo'].upper()}] {msg['texto']}")
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
