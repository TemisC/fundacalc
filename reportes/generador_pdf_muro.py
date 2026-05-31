"""
Generador PDF — Módulo 9.1 · Muro en Voladizo.
"""
from datetime import datetime

try:
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        KeepTogether,
    )
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False

_AZUL    = "#1565C0"
_VERDE   = "#2E7D32"
_ROJO    = "#C62828"
_CABEC   = "#E3F2FD"
_GRIS    = "#CCCCCC"
_NARANJA = "#E65100"
_AMARILLO = "#FFF9C4"


class GeneradorPDFMuro:

    def generar(self, ruta: str, motor, norma: str = "ACI 318-19"):
        if not _REPORTLAB:
            self._generar_txt(ruta, motor, norma)
            return
        self._generar_pdf(ruta, motor, norma)

    # ── Documento ────────────────────────────────────────────────────────────

    def _generar_pdf(self, ruta, motor, norma):
        MARGEN = 2.0 * cm
        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            leftMargin=MARGEN, rightMargin=MARGEN,
            topMargin=MARGEN, bottomMargin=MARGEN,
        )

        est = getSampleStyleSheet()
        est.add(ParagraphStyle('T1', parent=est['Heading1'], fontSize=16,
                               leading=20, spaceAfter=10,
                               textColor=colors.HexColor(_AZUL)))
        est.add(ParagraphStyle('T2', parent=est['Heading2'], fontSize=12,
                               leading=16, spaceBefore=14, spaceAfter=6,
                               textColor=colors.HexColor(_AZUL)))
        est.add(ParagraphStyle('N', parent=est['Normal'],
                               fontSize=9, leading=13))
        est.add(ParagraphStyle('Nc', parent=est['Normal'],
                               fontSize=9, leading=13, alignment=TA_CENTER))
        est.add(ParagraphStyle('OK', parent=est['Normal'],
                               fontSize=8, leading=12,
                               textColor=colors.HexColor(_VERDE)))
        est.add(ParagraphStyle('ERR', parent=est['Normal'],
                               fontSize=8, leading=12,
                               textColor=colors.HexColor(_ROJO)))
        est.add(ParagraphStyle('ADV', parent=est['Normal'],
                               fontSize=8, leading=12,
                               textColor=colors.HexColor(_NARANJA)))

        res = motor.res
        inp = motor._inp
        story = []

        # ── Portada ─────────────────────────────────────────────────────
        story.append(Paragraph("FundaCalc — Módulo 9.1", est['T1']))
        story.append(Paragraph("Muro en Voladizo (L invertida)", est['T1']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            f"Norma: {norma} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            est['N']))
        story.append(Spacer(1, 0.5 * cm))

        # ── Datos de entrada ─────────────────────────────────────────────
        story.append(Paragraph("1. Datos de Entrada", est['T2']))
        story += self._tbl2([
            ("Altura total H", f"{inp['H']:.2f} m"),
            ("Espesor zapata h_zap", f"{inp['h_zapata']:.2f} m"),
            ("Altura fuste h_fuste", f"{res.h_fuste:.2f} m"),
            ("Ancho fuste — base", f"{inp['b_base']:.2f} m"),
            ("Ancho fuste — corona", f"{inp['b_corona']:.2f} m"),
            ("Punta B_p", f"{inp['B_punta']:.2f} m"),
            ("Talón B_t", f"{inp['B_talon']:.2f} m"),
            ("Ancho total B", f"{res.B_total:.2f} m"),
        ], "Geometría")
        story.append(Spacer(1, 0.2 * cm))
        story += self._tbl2([
            ("γ suelo retenido", f"{inp['gamma_r']:.1f} kN/m³"),
            ("φ suelo retenido", f"{inp['phi_r']:.1f} °"),
            ("c suelo retenido", f"{inp['c_r']:.1f} kPa"),
            ("Sobrecarga q_s", f"{inp['q_s']:.1f} kPa"),
            ("γ suelo fundación", f"{inp['gamma_f']:.1f} kN/m³"),
            ("φ suelo fundación", f"{inp['phi_f']:.1f} °"),
            ("c suelo fundación", f"{inp['c_f']:.1f} kPa"),
            ("q_adm", f"{inp['qa']:.1f} kPa"),
        ], "Suelo")
        story.append(Spacer(1, 0.2 * cm))
        story += self._tbl2([
            ("f'c", f"{inp['fc']:.1f} MPa"),
            ("fy", f"{inp['fy']:.1f} MPa"),
            ("Recubrimiento", f"{inp['recub']*100:.0f} cm"),
            ("γ hormigón", f"{inp['gamma_c']:.1f} kN/m³"),
            ("δ/φ (desliz.)", f"{inp['delta_factor']:.3f}"),
        ], "Materiales")

        # ── Estabilidad ──────────────────────────────────────────────────
        est_r = res.estabilidad
        story.append(Paragraph("2. Verificación de Estabilidad", est['T2']))

        story.append(Paragraph(
            f"Ka (Rankine) = {est_r.Ka:.4f} &nbsp;&nbsp; "
            f"Ea = {est_r.Ea:.2f} kN/m &nbsp;&nbsp; "
            f"Mo = {est_r.Mo:.2f} kN·m/m",
            est['N']))
        story.append(Spacer(1, 0.2 * cm))

        # Tabla de fuerzas
        story.append(Paragraph("Fuerzas estabilizantes:", est['N']))
        fuerza_data = [
            ["Elemento", "Peso (kN/m)", "Brazo (m)", "Momento (kN·m/m)"],
        ]
        inp_v = motor._inp
        B_p = inp_v['B_punta']
        b_b = inp_v['b_base']
        b_c = inp_v['b_corona']
        b_avg = (b_b + b_c) / 2
        B_t = inp_v['B_talon']
        B_tot = res.B_total
        x_f = B_p + b_avg / 2
        x_z = B_tot / 2
        x_t = B_p + b_b + B_t / 2
        fuerza_data += [
            ["Fuste",         f"{est_r.W_fuste:.2f}",       f"{x_f:.3f}", f"{est_r.W_fuste*x_f:.2f}"],
            ["Zapata",        f"{est_r.W_zapata:.2f}",       f"{x_z:.3f}", f"{est_r.W_zapata*x_z:.2f}"],
            ["Suelo talón",   f"{est_r.W_talon_soil:.2f}",   f"{x_t:.3f}", f"{est_r.W_talon_soil*x_t:.2f}"],
            ["Sobrecarga",    f"{est_r.W_q_talon:.2f}",      f"{x_t:.3f}", f"{est_r.W_q_talon*x_t:.2f}"],
            ["TOTAL", f"{est_r.W_total:.2f}", "—", f"{est_r.Mr:.2f}"],
        ]
        story.append(self._tabla(fuerza_data, col_widths=[5.5*cm,3.5*cm,3*cm,4*cm]))

        story.append(Spacer(1, 0.3 * cm))

        # Tabla de FS
        ok_str  = lambda v: ("✓ OK" if v else "✗ FALLA")
        fs_data = [
            ["Verificación", "Valor", "Mínimo", "Estado"],
            ["Vuelco",         f"FS = {est_r.FS_vuelco:.2f}",  "2.00", ok_str(est_r.ok_vuelco)],
            ["Deslizamiento",  f"FS = {est_r.FS_desliz:.2f}",  "1.50", ok_str(est_r.ok_desliz)],
            ["Presión base",   f"q_max = {est_r.q_max:.1f} kPa", f"qa = {inp['qa']:.1f} kPa", ok_str(est_r.ok_presion)],
            ["Excentricidad",  f"|e| = {abs(est_r.e):.3f} m",  f"B/6 = {B_tot/6:.3f} m", ok_str(est_r.ok_excentricidad)],
        ]
        story.append(self._tabla(fs_data, col_widths=[5*cm,4.5*cm,4*cm,3*cm],
                                 ok_col=3,
                                 ok_rows={1:est_r.ok_vuelco, 2:est_r.ok_desliz,
                                          3:est_r.ok_presion, 4:est_r.ok_excentricidad}))

        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            f"Presión base: q_max = <b>{est_r.q_max:.1f} kPa</b> (punta) | "
            f"q_min = <b>{est_r.q_min:.1f} kPa</b> (talón) | "
            f"Empuje pasivo Ep = {est_r.Ep:.2f} kN/m",
            est['N']))
        story.append(Paragraph(
            f"Posición resultante: x_R = {est_r.x_R:.3f} m desde punta | "
            f"Excentricidad e = {est_r.e:.4f} m",
            est['N']))

        # ── Diseño RC ────────────────────────────────────────────────────
        story.append(Paragraph("3. Diseño de Armadura (ACI 318-19)", est['T2']))

        rc_data = [
            ["Elemento", "Mu (kN·m/m)", "d (m)", "As_req (cm²/m)", "As_min (cm²/m)", "As_dis (cm²/m)", "Armadura"],
        ]
        for elem in [res.fuste, res.punta, res.talon]:
            rc_data.append([
                elem.nombre,
                f"{elem.Mu:.2f}",
                f"{elem.d:.3f}",
                f"{elem.As_req:.2f}",
                f"{elem.As_min:.2f}",
                f"{elem.As_dis:.2f}",
                elem.barra,
            ])
        story.append(self._tabla(rc_data,
                                 col_widths=[2*cm,3*cm,2*cm,3*cm,3*cm,3*cm,3.5*cm]))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            f"Acero temp./retracción fuste (barras horiz., c/cara): "
            f"As = {res.As_temp:.2f} cm²/m  →  {res.barra_temp}",
            est['N']))

        # ── Mensajes ─────────────────────────────────────────────────────
        story.append(Paragraph("4. Mensajes del Verificador", est['T2']))
        for msg in res.mensajes:
            stl = {'ok': 'OK', 'error': 'ERR', 'advertencia': 'ADV'}.get(msg['tipo'], 'N')
            story.append(Paragraph(f"▸ {msg['texto']}", est[stl]))

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(
            "Generado por FundaCalc — Módulo 9.1 Muro en Voladizo",
            est['Nc']))

        doc.build(story)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _tbl2(self, filas, titulo=""):
        rows = []
        if titulo:
            rows.append([Paragraph(f"<b>{titulo}</b>", ParagraphStyle(
                '_th', fontSize=8, leading=11)), ""])
        for k, v in filas:
            rows.append([k, v])
        tbl = Table(rows, colWidths=[8*cm, 8*cm])
        tbl.setStyle(TableStyle([
            ('FONTSIZE',    (0, 0), (-1, -1), 8),
            ('LEADING',     (0, 0), (-1, -1), 11),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1),
             [colors.HexColor(_CABEC), colors.white]),
            ('GRID',        (0, 0), (-1, -1), 0.4,
             colors.HexColor(_GRIS)),
            ('TOPPADDING',  (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return [tbl, Spacer(1, 0.15 * cm)]

    def _tabla(self, data, col_widths=None, ok_col=None, ok_rows=None):
        tbl = Table(data, colWidths=col_widths)
        style = [
            ('BACKGROUND',  (0, 0), (-1, 0),  colors.HexColor(_CABEC)),
            ('FONTSIZE',    (0, 0), (-1, -1), 8),
            ('LEADING',     (0, 0), (-1, -1), 11),
            ('GRID',        (0, 0), (-1, -1), 0.4, colors.HexColor(_GRIS)),
            ('FONTNAME',    (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('TOPPADDING',  (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ]
        if ok_col is not None and ok_rows:
            for row_idx, ok in ok_rows.items():
                color = colors.HexColor(_VERDE) if ok else colors.HexColor(_ROJO)
                style.append(('TEXTCOLOR', (ok_col, row_idx), (ok_col, row_idx), color))
                style.append(('FONTNAME',  (ok_col, row_idx), (ok_col, row_idx), 'Helvetica-Bold'))
        tbl.setStyle(TableStyle(style))
        return tbl

    # ── Fallback texto ────────────────────────────────────────────────────────

    def _generar_txt(self, ruta: str, motor, norma: str):
        res = motor.res
        est = res.estabilidad
        lines = [
            f"FundaCalc — Módulo 9.1 Muro en Voladizo | {norma}",
            f"Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            "=" * 60,
            f"H={res.H:.2f}m  h_fuste={res.h_fuste:.2f}m  B={res.B_total:.2f}m",
            f"Ka={res.Ka:.4f}  Ea={est.Ea:.2f}kN/m  Mo={est.Mo:.2f}kN.m/m",
            f"FS_vuelco={est.FS_vuelco:.2f}  FS_desliz={est.FS_desliz:.2f}",
            f"q_max={est.q_max:.1f}kPa  q_min={est.q_min:.1f}kPa",
            "--- Armadura ---",
            f"Fuste: Mu={res.fuste.Mu:.2f}kN.m/m  As={res.fuste.As_dis:.2f}cm2/m  {res.fuste.barra}",
            f"Punta: Mu={res.punta.Mu:.2f}kN.m/m  As={res.punta.As_dis:.2f}cm2/m  {res.punta.barra}",
            f"Talon: Mu={res.talon.Mu:.2f}kN.m/m  As={res.talon.As_dis:.2f}cm2/m  {res.talon.barra}",
        ]
        ruta_txt = ruta.replace('.pdf', '.txt')
        with open(ruta_txt, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
