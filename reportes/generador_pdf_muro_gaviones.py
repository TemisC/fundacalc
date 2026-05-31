"""
Generador PDF — Módulo 9.3 · Muro de Gaviones.
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


class GeneradorPDFMuroGaviones:

    def generar(self, ruta: str, motor, norma: str = "—"):
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
        story = []

        # ── Portada ──────────────────────────────────────────────────────
        story.append(Paragraph("FundaCalc — Módulo 9.3", sty['T1']))
        story.append(Paragraph("Muro de Gaviones (Escalonado)", sty['T1']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"Fecha: {datetime.now():%d/%m/%Y %H:%M}", sty['N']))
        story.append(Spacer(1, 0.5 * cm))

        # ── Datos de entrada ─────────────────────────────────────────────
        story.append(Paragraph("1. Datos de Entrada", sty['T2']))
        anchos_str = " / ".join(f"{b:.2f}" for b in res.anchos)
        story += self._tbl2([
            ("Número de cursos N",      f"{res.N}"),
            ("Altura por curso h_capa", f"{res.h_capa:.2f} m"),
            ("Altura total H",          f"{res.H:.2f} m"),
            ("Ancho base (curso 1)",    f"{res.b_base:.2f} m"),
            ("Ancho corona (curso N)",  f"{res.b_corona:.2f} m"),
            ("Anchos por curso",        anchos_str + " m"),
            ("Área sección total",      f"{res.A_seccion:.3f} m²"),
            ("Enterramiento del pie",   f"{inp['h_emb']:.2f} m"),
        ], "Geometría")
        story.append(Spacer(1, 0.2 * cm))
        story += self._tbl2([
            ("γ gavión (relleno)",      f"{inp['gamma_g']:.1f} kN/m³"),
            ("φ fricción interna juntas", f"{inp['phi_gavion']:.1f} °"),
            ("γ suelo retenido",        f"{inp['gamma_r']:.1f} kN/m³"),
            ("φ suelo retenido",        f"{inp['phi_r']:.1f} °"),
            ("c suelo retenido",        f"{inp['c_r']:.1f} kPa"),
            ("Sobrecarga q_s",          f"{inp['q_s']:.1f} kPa"),
            ("γ suelo fundación",       f"{inp['gamma_f']:.1f} kN/m³"),
            ("φ suelo fundación",       f"{inp['phi_f']:.1f} °"),
            ("c suelo fundación",       f"{inp['c_f']:.1f} kPa"),
            ("q_adm",                   f"{inp['qa']:.1f} kPa"),
            ("δ/φ (desliz. global)",    f"{inp['delta_factor']:.3f}"),
        ], "Materiales y Suelo")

        # ── Estabilidad global ───────────────────────────────────────────
        e_r = res.estabilidad
        story.append(Paragraph("2. Verificación de Estabilidad Global", sty['T2']))
        story.append(Paragraph(
            f"Ka = {e_r.Ka:.4f} &nbsp;&nbsp; "
            f"Ea = {e_r.Ea:.2f} kN/m &nbsp;&nbsp; "
            f"Mo = {e_r.Mo:.2f} kN·m/m &nbsp;&nbsp; "
            f"W = {e_r.W_total:.2f} kN/m &nbsp;&nbsp; "
            f"x_CG = {e_r.x_CG:.3f} m",
            sty['N']))
        story.append(Spacer(1, 0.2 * cm))

        ok_str = lambda v: ("✓ OK" if v else "✗ FALLA")
        fs_data = [
            ["Verificación", "Valor", "Mínimo", "Estado"],
            ["Vuelco",        f"FS = {e_r.FS_vuelco:.2f}",         "2.00",              ok_str(e_r.ok_vuelco)],
            ["Deslizamiento", f"FS = {e_r.FS_desliz:.2f}",         "1.50",              ok_str(e_r.ok_desliz)],
            ["Presión base",  f"q_max = {e_r.q_max:.1f} kPa",      f"qa = {inp['qa']:.0f} kPa", ok_str(e_r.ok_presion)],
            ["Excentricidad", f"|e| = {abs(e_r.e):.3f} m",         f"B/6 = {res.b_base/6:.3f} m", ok_str(e_r.ok_excentricidad)],
        ]
        story.append(self._tabla(
            fs_data, col_widths=[5*cm, 4.5*cm, 4*cm, 3*cm],
            ok_col=3,
            ok_rows={1: e_r.ok_vuelco, 2: e_r.ok_desliz,
                     3: e_r.ok_presion, 4: e_r.ok_excentricidad}))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            f"q_max = {e_r.q_max:.1f} kPa (toe) | q_min = {e_r.q_min:.1f} kPa (heel) | "
            f"x_R = {e_r.x_R:.3f} m | e = {e_r.e:.4f} m | Ep = {e_r.Ep:.2f} kN/m",
            sty['N']))

        # ── Verificación interna ─────────────────────────────────────────
        story.append(Paragraph("3. Verificación Interna entre Cursos", sty['T2']))
        int_data = [["Junta", "H sobre [m]", "W sobre [kN/m]", "Ea sobre [kN/m]", "FS_d", "Estado"]]
        ok_rows_int = {}
        for i, vi in enumerate(res.internas, start=1):
            int_data.append([
                f"J{vi.junta}",
                f"{vi.H_sobre:.2f}",
                f"{vi.W_sobre:.2f}",
                f"{vi.Ea_sobre:.2f}",
                f"{vi.FS_desliz:.2f}",
                ok_str(vi.ok_desliz),
            ])
            ok_rows_int[i] = vi.ok_desliz
        story.append(self._tabla(
            int_data, col_widths=[2*cm, 3*cm, 3.5*cm, 3.5*cm, 2.5*cm, 3*cm],
            ok_col=5, ok_rows=ok_rows_int))
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(
            f"Criterio junta: FS_d ≥ 1.3 usando φ_gavión = {inp['phi_gavion']:.1f}°",
            sty['N']))

        # ── Mensajes ─────────────────────────────────────────────────────
        story.append(Paragraph("4. Mensajes del Verificador", sty['T2']))
        for msg in res.mensajes:
            stl = {'ok': 'OK', 'error': 'ERR', 'advertencia': 'ADV'}.get(msg['tipo'], 'N')
            story.append(Paragraph(f"▸ {msg['texto']}", sty[stl]))

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(
            "Generado por FundaCalc — Módulo 9.3 Muro de Gaviones",
            sty['Nc']))

        doc.build(story)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _tbl2(self, filas, titulo=""):
        rows = []
        if titulo:
            rows.append([Paragraph(f"<b>{titulo}</b>", getSampleStyleSheet()['Normal']), ""])
        for k, v in filas:
            rows.append([k, v])
        t = Table(rows, colWidths=[9 * cm, 7 * cm])
        t.setStyle(TableStyle([
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS',(0, 0), (-1, -1), [colors.white, colors.HexColor("#F5F9FF")]),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor("#CCDDEE")),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return [t, Spacer(1, 0.15 * cm)]

    def _tabla(self, data, col_widths=None, ok_col=None, ok_rows=None):
        t = Table(data, colWidths=col_widths)
        style = [
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('BACKGROUND',    (0, 0), (-1,  0), colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0), (-1,  0), 'Helvetica-Bold'),
            ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor(_GRIS)),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        if ok_col is not None and ok_rows:
            for row_idx, passed in ok_rows.items():
                bg = colors.HexColor("#E8F5E9") if passed else colors.HexColor("#FFEBEE")
                style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg))
        t.setStyle(TableStyle(style))
        return t

    def _generar_txt(self, ruta, motor, norma):
        res = motor.res
        e   = res.estabilidad
        lines = [
            "FundaCalc — Módulo 9.3: Muro de Gaviones",
            f"Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            "",
            f"N={res.N} cursos  h_capa={res.h_capa:.2f}m  H={res.H:.2f}m",
            f"b_base={res.b_base:.2f}m  b_corona={res.b_corona:.2f}m",
            f"Ka={res.Ka:.4f}  Ea={e.Ea:.2f}kN/m  Mo={e.Mo:.2f}kN.m/m",
            f"FS_v={e.FS_vuelco:.2f}  FS_d={e.FS_desliz:.2f}",
            f"q_max={e.q_max:.1f}kPa  e={e.e:.4f}m",
            "",
            "Juntas internas:",
        ]
        for vi in res.internas:
            lines.append(f"  J{vi.junta}: FS_d={vi.FS_desliz:.2f}  {'OK' if vi.ok_desliz else 'FALLA'}")
        lines.append("")
        for msg in res.mensajes:
            lines.append(f"[{msg['tipo'].upper()}] {msg['texto']}")
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
