"""
Generador PDF — Módulo 9.4 · Muro con Contrafuertes.
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


class GeneradorPDFMuroContrafuertes:

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
        story = []

        # ── Portada ──────────────────────────────────────────────────────
        story.append(Paragraph("FundaCalc — Módulo 9.4", sty['T1']))
        story.append(Paragraph("Muro con Contrafuertes", sty['T1']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            f"Norma: {norma} &nbsp;&nbsp;|&nbsp;&nbsp; Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            sty['N']))
        story.append(Spacer(1, 0.5 * cm))

        # ── Datos de entrada ─────────────────────────────────────────────
        story.append(Paragraph("1. Datos de Entrada", sty['T2']))
        story += self._tbl2([
            ("Altura total H",              f"{inp['H']:.2f} m"),
            ("Espesor zapata h_zap",        f"{inp['h_zapata']:.2f} m"),
            ("Altura pantalla h_fuste",     f"{res.h_fuste:.2f} m"),
            ("Espesor pantalla e_pan",      f"{inp['e_pantalla']:.2f} m"),
            ("Espesor contrafuerte e_cont", f"{inp['e_contrafuerte']:.2f} m"),
            ("Espaciado contrafuertes s",   f"{inp['s']:.2f} m"),
            ("Luz libre L = s−e_cont",      f"{res.L_libre:.2f} m"),
            ("Punta B_p",                   f"{inp['B_punta']:.2f} m"),
            ("Talón B_t",                   f"{inp['B_talon']:.2f} m"),
            ("Ancho total B",               f"{res.B_total:.2f} m"),
        ], "Geometría")
        story.append(Spacer(1, 0.2 * cm))
        story += self._tbl2([
            ("γ suelo retenido", f"{inp['gamma_r']:.1f} kN/m³"),
            ("φ suelo retenido", f"{inp['phi_r']:.1f} °"),
            ("c suelo retenido", f"{inp['c_r']:.1f} kPa"),
            ("Sobrecarga q_s",   f"{inp['q_s']:.1f} kPa"),
            ("γ fundación",      f"{inp['gamma_f']:.1f} kN/m³"),
            ("φ fundación",      f"{inp['phi_f']:.1f} °"),
            ("c fundación",      f"{inp['c_f']:.1f} kPa"),
            ("q_adm",            f"{inp['qa']:.1f} kPa"),
        ], "Suelo")
        story.append(Spacer(1, 0.2 * cm))
        story += self._tbl2([
            ("f'c",          f"{inp['fc']:.1f} MPa"),
            ("fy",           f"{inp['fy']:.1f} MPa"),
            ("Recubrimiento", f"{inp['recub']*100:.0f} cm"),
            ("γ hormigón",   f"{inp['gamma_c']:.1f} kN/m³"),
            ("δ/φ",          f"{inp['delta_factor']:.3f}"),
        ], "Materiales")

        # ── Estabilidad global ───────────────────────────────────────────
        e_r = res.estabilidad
        story.append(Paragraph("2. Verificación de Estabilidad Global", sty['T2']))
        story.append(Paragraph(
            f"Ka = {e_r.Ka:.4f} &nbsp;|&nbsp; Ea = {e_r.Ea:.2f} kN/m &nbsp;|&nbsp; Mo = {e_r.Mo:.2f} kN·m/m",
            sty['N']))
        story.append(Spacer(1, 0.2 * cm))

        fuerza_data = [
            ["Elemento", "Peso (kN/m)", "Mr (kN·m/m)"],
            ["Pantalla",         f"{e_r.W_pantalla:.2f}",   "—"],
            ["Zapata",           f"{e_r.W_zapata:.2f}",     "—"],
            ["Suelo talón",      f"{e_r.W_talon_soil:.2f}", "—"],
            ["Sobrecarga talón", f"{e_r.W_q_talon:.2f}",    "—"],
            ["Contrafuertes /m", f"{e_r.W_cont_m:.2f}",     "—"],
            ["TOTAL",            f"{e_r.W_total:.2f}",      f"{e_r.Mr:.2f}"],
        ]
        story.append(self._tabla(fuerza_data, col_widths=[6*cm, 4*cm, 4*cm]))
        story.append(Spacer(1, 0.3 * cm))

        ok_str = lambda v: ("✓ OK" if v else "✗ FALLA")
        fs_data = [
            ["Verificación", "Valor", "Mínimo", "Estado"],
            ["Vuelco",        f"FS = {e_r.FS_vuelco:.2f}",       "2.00",                     ok_str(e_r.ok_vuelco)],
            ["Deslizamiento", f"FS = {e_r.FS_desliz:.2f}",       "1.50",                     ok_str(e_r.ok_desliz)],
            ["Presión base",  f"q_max = {e_r.q_max:.1f} kPa",    f"qa = {inp['qa']:.0f} kPa",ok_str(e_r.ok_presion)],
            ["Excentricidad", f"|e| = {abs(e_r.e):.3f} m",       f"B/6 = {res.B_total/6:.3f} m", ok_str(e_r.ok_excentricidad)],
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

        # ── Diseño RC ────────────────────────────────────────────────────
        story.append(Paragraph("3. Diseño de Armadura (ACI 318-19)", sty['T2']))
        p_base_str = e_r.Ka * (inp['gamma_r'] * res.h_fuste + inp['q_s'])
        story.append(Paragraph(
            f"Pantalla: luz libre L = {res.L_libre:.2f} m, p_base (talón) = {p_base_str:.1f} kPa",
            sty['N']))
        story.append(Spacer(1, 0.15 * cm))

        rc_data = [
            ["Elemento", "Mu", "d [m]", "As_req", "As_mín", "As_dis", "Armadura"],
        ]

        def fmt_mu(el):
            if "Contrafuerte" in el.nombre:
                return f"{el.Mu:.1f} kN·m/CF"
            return f"{el.Mu:.2f} kN·m/m"

        def fmt_as(el):
            if "Contrafuerte" in el.nombre:
                return (f"{el.As_req:.2f} cm²/CF",
                        f"{el.As_min:.2f} cm²/CF",
                        f"{el.As_dis:.2f} cm²/CF")
            return (f"{el.As_req:.2f}", f"{el.As_min:.2f}", f"{el.As_dis:.2f}")

        for el in [res.pantalla_neg, res.pantalla_pos, res.punta, res.talon, res.contrafuerte]:
            ar, am, ad = fmt_as(el)
            rc_data.append([
                el.nombre, fmt_mu(el), f"{el.d:.3f}", ar, am, ad, el.barra,
            ])
        story.append(self._tabla(rc_data,
                                  col_widths=[4*cm, 3*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm]))
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(
            f"Nota contrafuerte: {res.contrafuerte.nota}",
            sty['N']))

        # ── Mensajes ─────────────────────────────────────────────────────
        story.append(Paragraph("4. Mensajes del Verificador", sty['T2']))
        for msg in res.mensajes:
            stl = {'ok': 'OK', 'error': 'ERR', 'advertencia': 'ADV'}.get(msg['tipo'], 'N')
            story.append(Paragraph(f"▸ {msg['texto']}", sty[stl]))

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(
            "Generado por FundaCalc — Módulo 9.4 Muro con Contrafuertes",
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
            "FundaCalc — Módulo 9.4: Muro con Contrafuertes",
            f"Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            "",
            f"H={res.H:.2f}m  h_fuste={res.h_fuste:.2f}m  B={res.B_total:.2f}m  s={res.s:.2f}m",
            f"Ka={res.Ka:.4f}  Ea={e.Ea:.2f}kN/m  Mo={e.Mo:.2f}kN.m/m",
            f"FS_v={e.FS_vuelco:.2f}  FS_d={e.FS_desliz:.2f}  q_max={e.q_max:.1f}kPa  e={e.e:.4f}m",
            "",
            "Diseño RC:",
        ]
        for el in [res.pantalla_neg, res.pantalla_pos, res.punta, res.talon, res.contrafuerte]:
            lines.append(f"  {el.nombre}: Mu={el.Mu:.2f}  As_dis={el.As_dis:.2f}  {el.barra}")
        lines.append("")
        for msg in res.mensajes:
            lines.append(f"[{msg['tipo'].upper()}] {msg['texto']}")
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
