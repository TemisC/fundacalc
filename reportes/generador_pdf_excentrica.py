"""
Generador PDF para Zapata Excéntrica.
Memoria de cálculo multi-página:
  Portada → Datos entrada → Geometría/Presiones → Imagen sección →
  Verificaciones → Armadura → Mensajes
"""
import re, os, io, tempfile
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


class GeneradorPDFExcentrica:

    def generar(self, ruta: str, motor, datos_entrada: dict, imagen_seccion: str = None):
        if not _REPORTLAB:
            self._generar_txt(ruta, motor, datos_entrada)
            return
        self._generar_pdf(ruta, motor, datos_entrada, imagen_seccion)

    # ── PDF completo ─────────────────────────────────────────────────────────

    def _generar_pdf(self, ruta: str, motor, datos_entrada: dict, imagen_seccion: str = None):
        ANCHO, ALTO = A4
        MARGEN = 2.0 * cm
        ANCHO_UTIL = ANCHO - 2 * MARGEN

        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            leftMargin=MARGEN, rightMargin=MARGEN,
            topMargin=MARGEN, bottomMargin=MARGEN,
        )

        estilos = getSampleStyleSheet()
        N = ParagraphStyle("N", parent=estilos["Normal"], fontSize=9, spaceAfter=2)
        T = ParagraphStyle("T", parent=estilos["Title"], fontSize=18, textColor=colors.HexColor("#1565C0"),
                           spaceAfter=6, alignment=TA_CENTER)
        H1 = ParagraphStyle("H1", parent=estilos["Heading1"], fontSize=13,
                             textColor=colors.HexColor("#0D47A1"), spaceBefore=10, spaceAfter=4)
        H2 = ParagraphStyle("H2", parent=estilos["Heading2"], fontSize=10.5,
                             textColor=colors.HexColor("#1565C0"), spaceBefore=6, spaceAfter=3)
        SUB = ParagraphStyle("SUB", parent=N, fontSize=8, textColor=colors.HexColor("#555555"))
        C = ParagraphStyle("C", parent=N, alignment=TA_CENTER, fontSize=9)

        AZUL = colors.HexColor("#1565C0")
        AZUL_C = colors.HexColor("#BBDEFB")
        GRIS = colors.HexColor("#F5F5F5")

        def tabla(data, col_widths=None, header=True):
            t = Table(data, colWidths=col_widths)
            cmds = [
                ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
                ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
                ("TOPPADDING",  (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING",(0,0), (-1,-1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING",(0, 0), (-1, -1), 5),
            ]
            if header:
                cmds += [
                    ("BACKGROUND",  (0, 0), (-1, 0), AZUL_C),
                    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("TEXTCOLOR",   (0, 0), (-1, 0), AZUL),
                ]
            t.setStyle(TableStyle(cmds))
            return t

        res  = motor.res
        carga = motor.carga
        col  = motor.columna
        suelo = motor.suelo
        geo  = motor.geo
        norma_str = datos_entrada.get("norma", "—")
        u    = datos_entrada.get("unidades", {})
        fu   = u.get("cargas", "kN")
        pu   = u.get("presiones", "kN/m²")
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        story = []

        # ── PORTADA ─────────────────────────────────────────────────────────
        story += [
            Spacer(1, 1.8 * cm),
            Paragraph("FundaCalc", T),
            Paragraph("Módulo 5 — Zapata Excéntrica", ParagraphStyle(
                "ST", parent=estilos["Normal"], fontSize=14,
                textColor=colors.HexColor("#1976D2"), alignment=TA_CENTER, spaceAfter=2)),
            Spacer(1, 0.3 * cm),
            Paragraph("Memoria de Cálculo — Diseño de Zapata bajo Carga Axial + Momento Biaxial",
                       ParagraphStyle("D", parent=N, alignment=TA_CENTER, fontSize=9,
                                      textColor=colors.HexColor("#555555"))),
            Spacer(1, 0.8 * cm),
        ]
        meta = [
            ["Norma de diseño", norma_str],
            ["Fecha", fecha],
            ["P de servicio", f"{carga.Pser:.1f} {fu}"],
            ["Momento Mx (servicio)", f"{carga.Mser_x:.1f} {fu}·m"],
            ["Momento My (servicio)", f"{carga.Mser_y:.1f} {fu}·m"],
            ["Excentricidad ex", f"{res.ex:.3f} m"],
            ["Excentricidad ey", f"{res.ey:.3f} m"],
            ["Tipo de contacto", res.tipo_contacto],
            ["Zapata B × L", f"{res.B:.2f} m × {res.L:.2f} m"],
            ["Peralte h", f"{res.h:.2f} m"],
        ]
        story.append(tabla(meta, col_widths=[ANCHO_UTIL * 0.45, ANCHO_UTIL * 0.55], header=False))
        story.append(PageBreak())

        # ── DATOS DE ENTRADA ─────────────────────────────────────────────────
        story.append(Paragraph("1. Datos de Entrada", H1))

        story.append(Paragraph("Cargas", H2))
        dc = [
            ["Parámetro", "Valor"],
            ["Carga muerta Pd", f"{carga.Pd:.1f} {fu}"],
            ["Carga viva Pl",   f"{carga.Pl:.1f} {fu}"],
            ["Pser = Pd + Pl",  f"{carga.Pser:.1f} {fu}"],
            ["Pu = 1.2Pd + 1.6Pl", f"{carga.Pu:.1f} {fu}"],
            ["Momento muerto Mdx (dir. L)", f"{carga.Mdx:.1f} {fu}·m"],
            ["Momento vivo Mlx (dir. L)",   f"{carga.Mlx:.1f} {fu}·m"],
            ["Mser_x = Mdx + Mlx",          f"{carga.Mser_x:.1f} {fu}·m"],
            ["Mux = 1.2Mdx + 1.6Mlx",      f"{carga.Mux:.1f} {fu}·m"],
            ["Momento muerto Mdy (dir. B)", f"{carga.Mdy:.1f} {fu}·m"],
            ["Momento vivo Mly (dir. B)",   f"{carga.Mly:.1f} {fu}·m"],
            ["Mser_y",                       f"{carga.Mser_y:.1f} {fu}·m"],
            ["Muy",                          f"{carga.Muy:.1f} {fu}·m"],
        ]
        story.append(KeepTogether([tabla(dc, col_widths=[ANCHO_UTIL * 0.55, ANCHO_UTIL * 0.45]), Spacer(1, 0.3 * cm)]))

        story.append(Paragraph("Columna / Suelo / Materiales", H2))
        dm = [
            ["Parámetro", "Valor"],
            ["cx (dimensión col. en L)",   f"{col.cx:.2f} m"],
            ["cy (dimensión col. en B)",   f"{col.cy:.2f} m"],
            ["qa — presión admisible",      f"{suelo.qa:.1f} {pu}"],
            ["Df — profundidad empotramiento", f"{suelo.Df:.2f} m"],
            ["γ_suelo",                    f"{suelo.gamma_suelo:.1f} kN/m³"],
            ["f'c / fck",                  f"{motor.hormigon.fck:.1f} MPa"],
            ["fy",                         f"{motor.acero.fy:.0f} MPa"],
        ]
        story.append(KeepTogether([tabla(dm, col_widths=[ANCHO_UTIL * 0.55, ANCHO_UTIL * 0.45]), Spacer(1, 0.3 * cm)]))
        story.append(PageBreak())

        # ── GEOMETRÍA Y PRESIONES ────────────────────────────────────────────
        story.append(Paragraph("2. Geometría y Distribución de Presiones", H1))

        story.append(Paragraph("Geometría final", H2))
        dg = [
            ["Parámetro", "Símbolo", "Valor"],
            ["Ancho",          "B",  f"{res.B:.2f} m"],
            ["Largo",          "L",  f"{res.L:.2f} m"],
            ["Área",           "A",  f"{res.A:.2f} m²"],
            ["Peralte total",  "h",  f"{res.h:.2f} m"],
            ["Peralte efectivo","d", f"{res.d:.2f} m"],
            ["q neto",         "q_neto", f"{res.q_neto:.1f} {pu}"],
            ["ex (servicio)",  "ex", f"{res.ex:.4f} m"],
            ["ey (servicio)",  "ey", f"{res.ey:.4f} m"],
            ["Núcleo central", "—",  "SÍ" if res.en_nucleo else "NO"],
            ["Tipo contacto",  "—",  res.tipo_contacto],
        ]
        story.append(KeepTogether([tabla(dg, col_widths=[ANCHO_UTIL*0.45, ANCHO_UTIL*0.15, ANCHO_UTIL*0.40]), Spacer(1, 0.3*cm)]))

        story.append(Paragraph("Presiones de servicio — 4 esquinas", H2))
        pres_data = [
            ["Esquina", "x", "y", f"Presión [{pu}]", "Estado"],
            ["q1 (+L/2, +B/2)", "+L/2", "+B/2", f"{res.q1:.1f}", "máx" if res.q1 == res.q_max else "—"],
            ["q2 (+L/2, -B/2)", "+L/2", "-B/2", f"{res.q2:.1f}", "—"],
            ["q3 (-L/2, +B/2)", "-L/2", "+B/2", f"{res.q3:.1f}", "—"],
            ["q4 (-L/2, -B/2)", "-L/2", "-B/2", f"{res.q4:.1f}", "mín" if res.q4 == res.q_min else "—"],
            ["q_max", "—", "—", f"{res.q_max:.1f}", "≤ qa" if res.ok_presion else "> qa ✘"],
            ["q_min", "—", "—", f"{res.q_min:.1f}", "≥ 0" if res.ok_tension else "< 0 ⚠"],
        ]
        story.append(KeepTogether([tabla(pres_data,
            col_widths=[ANCHO_UTIL*0.28, ANCHO_UTIL*0.12, ANCHO_UTIL*0.12, ANCHO_UTIL*0.28, ANCHO_UTIL*0.20]),
            Spacer(1, 0.3*cm)]))

        story.append(Paragraph("Presiones últimas (diseño)", H2))
        pu_data = [
            ["Esquina", f"q_u [{pu}]"],
            ["q1u (+L/2, +B/2)", f"{res.q1u:.1f}"],
            ["q2u (+L/2, -B/2)", f"{res.q2u:.1f}"],
            ["q3u (-L/2, +B/2)", f"{res.q3u:.1f}"],
            ["q4u (-L/2, -B/2)", f"{res.q4u:.1f}"],
            ["q_max_u",           f"{res.q_max_u:.1f}"],
            ["q_min_u",           f"{res.q_min_u:.1f}"],
        ]
        story.append(KeepTogether([tabla(pu_data, col_widths=[ANCHO_UTIL*0.55, ANCHO_UTIL*0.45]), Spacer(1, 0.3*cm)]))
        story.append(PageBreak())

        # ── IMAGEN DE SECCIÓN ────────────────────────────────────────────────
        story.append(Paragraph("3. Vista en Sección (dirección L)", H1))
        story.append(Spacer(1, 0.2 * cm))
        if imagen_seccion and os.path.exists(imagen_seccion):
            max_w = ANCHO_UTIL
            max_h = 9 * cm
            img = RLImage(imagen_seccion, width=max_w, height=max_h, kind='proportional')
            story.append(img)
        else:
            story.append(Paragraph("(imagen de sección no disponible)", SUB))
        story.append(PageBreak())

        # ── VERIFICACIONES ───────────────────────────────────────────────────
        story.append(Paragraph("4. Verificaciones Estructurales", H1))

        story.append(Paragraph("Punzonado (cortante bidireccional)", H2))
        dp = [
            ["Parámetro", "Valor"],
            ["Perímetro crítico bo", f"{res.bo:.3f} m"],
            ["Vu punzonado",         f"{res.Vpu:.1f} kN"],
            ["φVn punzonado",        f"{res.phi_Vpn:.1f} kN"],
            ["Ratio Vu/φVn",         f"{res.rel_punzonado*100:.0f}%"],
            ["Resultado",            "✔ OK" if res.ok_punzonado else "✘ FALLA"],
        ]
        story.append(KeepTogether([tabla(dp, col_widths=[ANCHO_UTIL*0.55, ANCHO_UTIL*0.45]), Spacer(1, 0.3*cm)]))

        story.append(Paragraph("Cortante unidireccional", H2))
        dc2 = [
            ["Dirección", "Vu [kN/m]", "φVn [kN/m]", "Resultado"],
            ["L (a lo largo de L)", f"{res.Vu_L:.1f}", f"{res.phi_Vn:.1f}",
             "✔ OK" if res.ok_cortante_L else "✘ FALLA"],
            ["B (a lo largo de B)", f"{res.Vu_B:.1f}", f"{res.phi_Vn:.1f}",
             "✔ OK" if res.ok_cortante_B else "✘ FALLA"],
        ]
        story.append(KeepTogether([tabla(dc2, col_widths=[ANCHO_UTIL*0.40, ANCHO_UTIL*0.20, ANCHO_UTIL*0.20, ANCHO_UTIL*0.20]), Spacer(1, 0.3*cm)]))
        story.append(PageBreak())

        # ── ARMADURA ─────────────────────────────────────────────────────────
        story.append(Paragraph("5. Diseño de Armadura", H1))

        for lbl, Mu, As_req, As_min, As_dis, var, sep, nb, dim in [
            ("Dir. L — paralela a L (resistiendo Mu_L)",
             res.Mu_L, res.As_req_L, res.As_min_L, res.As_dis_L,
             res.varilla_L, res.sep_L, res.n_barras_L, res.B),
            ("Dir. B — paralela a B (resistiendo Mu_B)",
             res.Mu_B, res.As_req_B, res.As_min_B, res.As_dis_B,
             res.varilla_B, res.sep_B, res.n_barras_B, res.L),
        ]:
            story.append(Paragraph(lbl, H2))
            db = _db_mm(var)
            kg_m = _BAR_KG_M.get(db, 0)
            barras_pm = round(1.0 / sep) if sep > 0 else 0
            da = [
                ["Parámetro", "Valor"],
                ["Momento último Mu",     f"{Mu:.2f} kN·m/m"],
                ["As requerido por flexión", f"{As_req:.2f} cm²/m"],
                ["As mínimo",             f"{As_min:.2f} cm²/m"],
                ["As diseño (máx)",       f"{As_dis:.2f} cm²/m"],
                ["Varilla seleccionada",  var],
                ["Separación",            f"{sep*100:.0f} cm"],
                ["Barras/metro",          f"{barras_pm}"],
                ["N° barras en ancho",    f"{nb}"],
                ["Peso aprox.",           f"{kg_m * As_dis / (db**2 * 3.14159 / 4 * 1e4) * barras_pm:.1f} kg/m"],
            ]
            story.append(KeepTogether([tabla(da, col_widths=[ANCHO_UTIL*0.55, ANCHO_UTIL*0.45]), Spacer(1, 0.3*cm)]))

        story.append(PageBreak())

        # ── MENSAJES ─────────────────────────────────────────────────────────
        story.append(Paragraph("6. Registro del Cálculo", H1))
        colores_tipo = {
            "ok":   colors.HexColor("#1B5E20"),
            "error":colors.HexColor("#B71C1C"),
            "warn": colors.HexColor("#E65100"),
            "info": colors.HexColor("#1A237E"),
        }
        for m in res.mensajes:
            c = colores_tipo.get(m["tipo"], colors.black)
            story.append(Paragraph(
                m["texto"],
                ParagraphStyle("MSG", parent=N, textColor=c, spaceAfter=1, fontSize=8.5)))

        doc.build(story)

    # ── Fallback TXT ─────────────────────────────────────────────────────────

    def _generar_txt(self, ruta: str, motor, datos_entrada: dict):
        res = motor.res
        lineas = [
            "FUNDACALC — MÓDULO 5: ZAPATA EXCÉNTRICA",
            f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "=" * 60,
            f"B = {res.B:.2f} m   L = {res.L:.2f} m   h = {res.h:.2f} m",
            f"ex = {res.ex:.4f} m   ey = {res.ey:.4f} m",
            f"q_max = {res.q_max:.1f} kN/m²   q_min = {res.q_min:.1f} kN/m²",
            f"Tipo contacto: {res.tipo_contacto}",
            f"Punzonado: {'OK' if res.ok_punzonado else 'FALLA'}",
            f"Cortante L: {'OK' if res.ok_cortante_L else 'FALLA'}",
            f"Cortante B: {'OK' if res.ok_cortante_B else 'FALLA'}",
            f"Arm. L: {res.varilla_L} @ {res.sep_L*100:.0f} cm  As={res.As_dis_L:.2f} cm²/m",
            f"Arm. B: {res.varilla_B} @ {res.sep_B*100:.0f} cm  As={res.As_dis_B:.2f} cm²/m",
        ]
        ruta_txt = ruta.replace('.pdf', '.txt')
        with open(ruta_txt, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lineas))
