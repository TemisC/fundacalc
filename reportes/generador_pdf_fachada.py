"""
Generador PDF para Zapata de Fachada / Excéntrica por Geometría.
"""
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, Image, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    reportlab_ok = True
except ImportError:
    reportlab_ok = False


class GeneradorPDFFachada:

    def generar(self, ruta: str, motor, datos_entrada: dict, imagen_seccion=None):
        if reportlab_ok:
            self._generar_reportlab(ruta, motor, datos_entrada, imagen_seccion)
        else:
            self._generar_txt(ruta, motor)

    def _generar_reportlab(self, ruta, motor, datos_entrada, imagen_seccion):
        res  = motor.res
        col  = motor.columna
        geo  = motor.geo
        gf   = motor.geo_fachada

        doc = SimpleDocTemplate(ruta, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=14,
                             textColor=colors.HexColor('#0D47A1'), spaceAfter=4)
        h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=11,
                             textColor=colors.HexColor('#1565C0'), spaceAfter=3)
        normal = styles['Normal']
        small  = ParagraphStyle('small', parent=normal, fontSize=8, leading=11)
        center = ParagraphStyle('center', parent=normal, alignment=TA_CENTER)

        def tbl(data, col_widths=None, header_row=True):
            t = Table(data, colWidths=col_widths, repeatRows=1 if header_row else 0)
            cmd = [
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1565C0')),
                ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                ('FONTSIZE',   (0,0), (-1,-1), 8),
                ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#BDBDBD')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1),
                 [colors.white, colors.HexColor('#F5F5F5')]),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING',  (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ]
            t.setStyle(TableStyle(cmd))
            return t

        story = []
        norma = datos_entrada.get('norma', 'ACI318')
        fecha = datetime.now().strftime('%d/%m/%Y')

        # Portada
        story.append(Paragraph("FundaCalc", h1))
        story.append(Paragraph("Módulo 5b — Zapata de Fachada / Excéntrica por Geometría", h2))
        story.append(Paragraph(f"Norma: {norma}   |   Fecha: {fecha}", normal))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#1565C0')))
        story.append(Spacer(1, 10))

        # Geometría resultado
        story.append(Paragraph("Dimensiones de diseño", h2))
        story.append(tbl([
            ['Parámetro', 'Valor'],
            ['Ancho B', f"{res.B:.2f} m"],
            ['Largo L', f"{res.L:.2f} m"],
            ['Peralte h', f"{res.h:.2f} m"],
            ['Canto útil d', f"{res.d:.2f} m"],
            ['Área A', f"{res.A:.2f} m²"],
            ['ex geométrico', f"{gf.ex_geom:.4f} m"],
            ['ey geométrico', f"{gf.ey_geom:.4f} m"],
            ['Vuelo lado restringido', f"{res.L/2 - abs(gf.ex_geom) - col.cx/2:.3f} m"],
        ], [5*cm, 5*cm]))
        story.append(Spacer(1, 6))

        # Presiones de servicio
        story.append(Paragraph("Presiones de servicio — 4 esquinas", h2))
        story.append(tbl([
            ['Esquina', 'Posición', 'q (kN/m²)'],
            ['q1 (máx)', '+L/2, +B/2', f"{res.q1:.1f}"],
            ['q2',       '+L/2, −B/2', f"{res.q2:.1f}"],
            ['q3',       '−L/2, +B/2', f"{res.q3:.1f}"],
            ['q4 (mín)', '−L/2, −B/2', f"{res.q4:.1f}"],
        ], [4*cm, 4*cm, 4*cm]))
        story.append(Paragraph(
            f"Contacto: <b>{res.tipo_contacto}</b>   |   "
            f"q_max={res.q_max:.1f} kN/m²   q_min={res.q_min:.1f} kN/m²", small))
        story.append(Spacer(1, 6))

        # Presiones últimas
        story.append(Paragraph("Presiones últimas — 4 esquinas", h2))
        story.append(tbl([
            ['Esquina', 'q_u (kN/m²)'],
            ['q1u (máx)', f"{res.q1u:.1f}"],
            ['q2u',       f"{res.q2u:.1f}"],
            ['q3u',       f"{res.q3u:.1f}"],
            ['q4u (mín)', f"{res.q4u:.1f}"],
        ], [5*cm, 5*cm]))
        story.append(Spacer(1, 6))

        # Sección
        if imagen_seccion:
            try:
                story.append(Paragraph("Sección en Dirección L — Diagrama de Presiones", h2))
                story.append(Image(imagen_seccion, width=14*cm, height=6*cm))
                story.append(Spacer(1, 6))
            except Exception:
                pass

        # Verificaciones
        story.append(Paragraph("Verificaciones", h2))
        def tick(ok): return "✔" if ok else "✘"
        story.append(tbl([
            ['Verificación', 'Resultado', 'Estado'],
            ['Presión admisible', f"q_max={res.q_max:.1f} ≤ qa={motor.suelo.qa:.1f} kN/m²",
             tick(res.ok_presion)],
            ['Contacto positivo (q_min≥0)', f"q_min={res.q_min:.1f} kN/m²",
             tick(res.ok_tension)],
            ['Punzonado', f"Vu={res.Vpu:.1f} ≤ φVn={res.phi_Vpn:.1f} kN",
             tick(res.ok_punzonado)],
            ['Cortante dir. L', f"Vu={res.Vu_L:.1f} ≤ φVn={res.phi_Vn:.1f} kN/m",
             tick(res.ok_cortante_L)],
            ['Cortante dir. B', f"Vu={res.Vu_B:.1f} ≤ φVn={res.phi_Vn:.1f} kN/m",
             tick(res.ok_cortante_B)],
        ], [5*cm, 6*cm, 2*cm]))
        story.append(Spacer(1, 6))

        # Armadura
        story.append(Paragraph("Cuadro de Armadura", h2))
        story.append(tbl([
            ['Dir.', 'Varilla', 'Sep. (cm)', 'As_req (cm²/m)', 'As_dis (cm²/m)', 'n barras'],
            ['L (principal)', res.varilla_L, f"{res.sep_L*100:.0f}",
             f"{res.As_req_L:.2f}", f"{res.As_dis_L:.2f}", str(res.n_barras_L)],
            ['B (secundaria)', res.varilla_B, f"{res.sep_B*100:.0f}",
             f"{res.As_req_B:.2f}", f"{res.As_dis_B:.2f}", str(res.n_barras_B)],
        ], [2.5*cm, 2.5*cm, 2*cm, 3*cm, 3*cm, 2*cm]))
        story.append(Spacer(1, 6))

        # Viga de atado
        story.append(Paragraph("Viga de Atado (referencial)", h2))
        story.append(tbl([
            ['Parámetro', 'Valor'],
            ['Momento equiv. servicio Mx', f"{motor.carga.Mser_x:.1f} kN·m"],
            ['Momento equiv. último Mux', f"{motor.carga.Mux:.1f} kN·m"],
            ['Luz asumida L_atado', f"{motor.L_atado:.1f} m"],
            ['Fuerza de atado T ≈', f"{motor.T_atado:.1f} kN"],
        ], [7*cm, 5*cm]))
        story.append(Paragraph(
            "⚠ La viga de atado debe diseñarse para las cargas horizontales específicas "
            "del proyecto. El valor T es referencial (equilibrio de momento vertical).", small))
        story.append(Spacer(1, 6))

        # Mensajes
        story.append(Paragraph("Mensajes del motor", h2))
        for m in res.mensajes:
            story.append(Paragraph(m['texto'], small))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"Generado por FundaCalc v1.0  —  {fecha}", center))

        doc.build(story)

    def _generar_txt(self, ruta, motor):
        res = motor.res
        lines = [
            "FundaCalc — Zapata de Fachada",
            f"B={res.B:.2f}m  L={res.L:.2f}m  h={res.h:.2f}m",
            f"ex_geom={motor.ex_geom:.3f}m  ey_geom={motor.ey_geom:.3f}m",
            f"q_max={res.q_max:.1f}kN/m²  q_min={res.q_min:.1f}kN/m²",
            f"T_atado≈{motor.T_atado:.1f}kN  (L_atado={motor.L_atado:.1f}m)",
        ]
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
