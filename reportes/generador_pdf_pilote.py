"""
Generador PDF — Módulo 6B · Pilote Individual.
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
_ROJO   = "#C62828"
_CABEC  = "#E3F2FD"
_GRIS   = "#CCCCCC"
_NARANJA = "#E65100"


class GeneradorPDFPilote:

    def generar(self, ruta: str, motor, norma: str = "ACI 318-19"):
        if not _REPORTLAB:
            self._txt(ruta, motor)
            return
        self._pdf(ruta, motor, norma)

    def _pdf(self, ruta, motor, norma):
        MARGEN = 2.0 * cm
        doc = SimpleDocTemplate(ruta, pagesize=A4,
                                leftMargin=MARGEN, rightMargin=MARGEN,
                                topMargin=MARGEN, bottomMargin=MARGEN)
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
        sty.add(ParagraphStyle('OK',  parent=sty['Normal'], fontSize=8, leading=12,
                               textColor=colors.HexColor(_VERDE)))
        sty.add(ParagraphStyle('ERR', parent=sty['Normal'], fontSize=8, leading=12,
                               textColor=colors.HexColor(_ROJO)))
        sty.add(ParagraphStyle('ADV', parent=sty['Normal'], fontSize=8, leading=12,
                               textColor=colors.HexColor(_NARANJA)))

        res = motor.res
        inp = motor._inp
        ax  = res.axial
        lat = res.lateral
        rc  = res.rc
        story = []

        # ── Portada ──────────────────────────────────────────────────────
        story.append(Paragraph("FundaCalc — Módulo 6B", sty['T1']))
        tipo_lbl = "Vaciado in situ" if res.tipo == 'vaciado_in_situ' else "Hincado"
        story.append(Paragraph(f"Pilote Individual — {tipo_lbl}", sty['T1']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            f"Norma: {norma} &nbsp;|&nbsp; Fecha: {datetime.now():%d/%m/%Y %H:%M}", sty['N']))
        story.append(Spacer(1, 0.5 * cm))

        # ── Datos ────────────────────────────────────────────────────────
        story.append(Paragraph("1. Datos de Entrada", sty['T2']))
        story += self._t2([
            ("Diámetro D",           f"{res.D:.2f} m"),
            ("Longitud L",           f"{res.L:.2f} m"),
            ("Tipo de pilote",       tipo_lbl),
            ("Carga axial diseño",   f"{inp['Qa_dis']:.1f} kN"),
            ("FS mínimo axial",      f"{inp['FS_min']:.1f}"),
            ("Carga lateral H",      f"{inp['H_lat']:.1f} kN"),
            ("Excentricidad e",      f"{inp['e_lat']:.2f} m"),
            ("Suelo lateral",        inp['tipo_lat'].capitalize()),
            ("f'c / fy",            f"{inp['fc']:.0f} MPa / {inp['fy']:.0f} MPa"),
            ("Recubrimiento",        f"{inp['recub']*100:.1f} cm"),
        ], "Geometría, Cargas y Materiales")

        # ── Capacidad axial ───────────────────────────────────────────────
        story.append(Paragraph("2. Capacidad Axial por Capas", sty['T2']))
        cap_data = [["Capa", "Tipo", "Δz [m]", "cu/φ", "α o β", "fs [kPa]", "Qs [kN]"]]
        for c in ax.capas:
            if c.tipo == 'arcilla':
                prop = f"cu={c.cu:.0f} kPa"
                coef = f"α={c.alpha:.2f}"
            else:
                prop = f"φ={c.phi:.0f}°"
                coef = f"β={c.beta:.3f}"
            cap_data.append([
                str(c.numero), c.tipo.capitalize(), f"{c.espesor:.2f}",
                prop, coef, f"{c.fs:.1f}", f"{c.Qs:.1f}",
            ])
        story.append(self._tabla(cap_data, col_widths=[1*cm,2*cm,1.5*cm,3*cm,2*cm,2.5*cm,2.5*cm]))
        story.append(Spacer(1, 0.2 * cm))
        story += self._t2([
            ("Qs  (fricción lateral total)", f"{ax.Qs_total:.2f} kN"),
            ("Qp  (resistencia en punta)",   f"{ax.Qp:.2f} kN  (Nc={ax.Nq_o_Nc:.1f})"),
            ("Qu  (capacidad última)",        f"<b>{ax.Qu:.2f} kN</b>"),
            ("Qa  (capacidad admisible)",     f"<b>{ax.Qa:.2f} kN</b>"),
            ("FS  axial",                    f"{ax.FS_axial:.2f}"),
        ], "Resumen Axial")

        # ── Capacidad lateral ─────────────────────────────────────────────
        story.append(Paragraph("3. Capacidad Lateral — Broms (1964)", sty['T2']))
        story += self._t2([
            ("Método",                inp['tipo_lat'].capitalize()),
            ("Condición de cabeza",   lat.condicion.capitalize()),
            ("Tipo de pilote",        lat.tipo_pilote.capitalize()),
            ("My estimado",           f"{lat.My:.1f} kN·m"),
            ("Hu (capacidad ult.)",   f"<b>{lat.Hu:.2f} kN</b>"),
            ("H diseño",              f"{lat.H_dis:.1f} kN"),
            ("FS lateral",            f"{lat.FS_lateral:.2f}  {'✓' if lat.ok_lateral else '✗'}"),
            ("Prof. M_max (z_max)",   f"{lat.z_max:.2f} m" if lat.z_max > 0 else "N/A"),
        ], "Resultados Lateral")

        # ── Diseño RC ─────────────────────────────────────────────────────
        story.append(Paragraph("4. Diseño de Armadura (ACI 318-19)", sty['T2']))
        story += self._t2([
            ("Área bruta Ag",              f"{rc.Ag*1e4:.1f} cm²"),
            ("As_req  (carga axial)",       f"{rc.Ast_req:.2f} cm²"),
            ("As_mín  (ρ_min=0.8% ACI)",   f"{rc.Ast_min:.2f} cm²"),
            ("As_máx  (ρ_max=4.0% ACI)",   f"{rc.Ast_max:.2f} cm²"),
            ("As_dis  diseñada",            f"<b>{rc.Ast_dis:.2f} cm²</b>"),
            ("Barras longitudinales",       rc.desc_long),
            ("Cuantía ρ_l",                f"{rc.rho_l*100:.2f}%"),
            ("ρ_s mín espiral",            f"{rc.rho_s_min:.4f}"),
            ("Espiral",                    f"∅{rc.db_esp:.0f}mm @ {rc.paso_esp:.0f}mm"),
        ], "Armadura Sección Circular")

        # ── Mensajes ─────────────────────────────────────────────────────
        story.append(Paragraph("5. Mensajes del Verificador", sty['T2']))
        for msg in res.mensajes:
            stl = {'ok':'OK','error':'ERR','advertencia':'ADV'}.get(msg['tipo'],'N')
            story.append(Paragraph(f"▸ {msg['texto']}", sty[stl]))

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Generado por FundaCalc — Módulo 6B Pilote Individual", sty['Nc']))
        doc.build(story)

    def _t2(self, filas, titulo=""):
        rows = []
        if titulo:
            rows.append([Paragraph(f"<b>{titulo}</b>", getSampleStyleSheet()['Normal']), ""])
        for k, v in filas:
            rows.append([k, v])
        t = Table(rows, colWidths=[9*cm, 7*cm])
        t.setStyle(TableStyle([
            ('FONTSIZE',      (0,0),(-1,-1), 8),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white, colors.HexColor("#F5F9FF")]),
            ('GRID',          (0,0),(-1,-1), 0.3, colors.HexColor("#CCDDEE")),
            ('TOPPADDING',    (0,0),(-1,-1), 3),
            ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ]))
        return [t, Spacer(1, 0.15*cm)]

    def _tabla(self, data, col_widths=None):
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('FONTSIZE',      (0,0),(-1,-1), 8),
            ('BACKGROUND',    (0,0),(-1,0),  colors.HexColor(_CABEC)),
            ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
            ('GRID',          (0,0),(-1,-1), 0.4, colors.HexColor(_GRIS)),
            ('TOPPADDING',    (0,0),(-1,-1), 3),
            ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ]))
        return t

    def _txt(self, ruta, motor):
        res = motor.res
        ax = res.axial
        lat = res.lateral
        lines = [
            "FundaCalc — Módulo 6B: Pilote Individual",
            f"Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            f"D={res.D:.2f}m  L={res.L:.2f}m  Tipo={res.tipo}",
            f"Qs={ax.Qs_total:.1f}kN  Qp={ax.Qp:.1f}kN  Qu={ax.Qu:.1f}kN  FS={ax.FS_axial:.2f}",
            f"Hu={lat.Hu:.1f}kN  FS_lat={lat.FS_lateral:.2f}  tipo={lat.tipo_pilote}",
            f"RC: {res.rc.desc_long}  ρ={res.rc.rho_l*100:.2f}%",
        ]
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
