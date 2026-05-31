"""
Generador PDF — Módulo 8 · Capacidad Portante del suelo.
Métodos: Terzaghi (1943), Meyerhof (1963), Hansen (1970).
"""
from datetime import datetime

try:
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, KeepTogether,
    )
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False

_AZUL  = "#1565C0"
_VERDE = "#2E7D32"
_ROJO  = "#C62828"
_CABEC = "#E3F2FD"
_GRIS  = "#CCCCCC"
_NARANJA = "#E65100"


class GeneradorPDFCapacidad:

    def generar(self, ruta: str, motor, datos_entrada: dict):
        if not _REPORTLAB:
            self._generar_txt(ruta, motor, datos_entrada)
            return
        self._generar_pdf(ruta, motor, datos_entrada)

    # ── Documento ────────────────────────────────────────────────────────────

    def _generar_pdf(self, ruta, motor, datos_entrada):
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
                               leading=16, spaceAfter=6,
                               textColor=colors.HexColor(_AZUL)))
        est.add(ParagraphStyle('Cuerpo', parent=est['Normal'],
                               fontSize=9.5, leading=13, spaceAfter=3))
        est.add(ParagraphStyle('Pie', parent=est['Normal'],
                               fontSize=8, leading=11,
                               textColor=colors.gray, spaceAfter=2))
        est.add(ParagraphStyle('Centro', parent=est['Normal'],
                               fontSize=9, leading=12,
                               alignment=TA_CENTER, spaceAfter=4))

        h = []
        h += self._portada(est, datos_entrada)
        h.append(PageBreak())
        h += self._datos_entrada(est, motor, datos_entrada)
        h.append(PageBreak())
        h += self._factores(est, motor)
        h += self._comparativa(est, motor)
        h += self._mensajes(est, motor.res)

        doc.build(h)

    # ── Portada ──────────────────────────────────────────────────────────────

    def _portada(self, est, datos_entrada):
        norma = datos_entrada.get("norma", "—")
        forma = datos_entrada.get("forma", "rectangular").capitalize()
        elems = []
        elems.append(Spacer(1, 2 * cm))
        elems.append(Paragraph("FundaCalc", est['T1']))
        elems.append(Paragraph(
            "Módulo 8 — Capacidad Portante del Suelo",
            ParagraphStyle('PORT', parent=est['T1'], fontSize=14, leading=18,
                           textColor=colors.HexColor(_AZUL)),
        ))
        elems.append(Spacer(1, 0.4 * cm))
        elems.append(Paragraph(
            f"Métodos: Terzaghi (1943) · Meyerhof (1963) · Hansen (1970)",
            ParagraphStyle('SUB', parent=est['Normal'], fontSize=11, leading=15,
                           textColor=colors.HexColor(_NARANJA)),
        ))
        elems.append(Spacer(1, 0.3 * cm))
        elems.append(Paragraph(
            f"Forma de fundación: {forma}  |  Norma referencia: {norma}",
            ParagraphStyle('INFO', parent=est['Normal'], fontSize=10, leading=14,
                           textColor=colors.HexColor("#555555")),
        ))
        elems.append(Spacer(1, 0.3 * cm))
        elems.append(Paragraph(
            f"Generado: {datetime.now():%d/%m/%Y %H:%M}",
            ParagraphStyle('FECHA', parent=est['Normal'], fontSize=9, leading=12,
                           textColor=colors.gray),
        ))
        return elems

    # ── Datos de entrada ─────────────────────────────────────────────────────

    def _datos_entrada(self, est, motor, datos_entrada):
        res = motor.res
        elems = [Paragraph("1. Datos de Entrada", est['T2'])]

        forma   = datos_entrada.get("forma", "rectangular")
        B       = datos_entrada.get("B", 0)
        L       = datos_entrada.get("L", 0)
        Df      = datos_entrada.get("Df", 0)
        phi     = datos_entrada.get("phi", 0)
        c       = datos_entrada.get("c", 0)
        gamma   = datos_entrada.get("gamma", 0)
        FS      = datos_entrada.get("FS", 3.0)
        nf_prof = datos_entrada.get("nf_prof", None)
        gsub    = datos_entrada.get("gamma_sub", None)

        geo_rows = [
            ["Parámetro", "Valor"],
            ["Forma de la fundación", forma.capitalize()],
            ["B — ancho [m]", f"{B:.2f}"],
        ]
        if forma not in ("corrida", "circular"):
            geo_rows.append(["L — largo [m]", f"{L:.2f}"])
        geo_rows += [
            ["Df — profundidad de desplante [m]", f"{Df:.2f}"],
            ["q = γ·Df — sobrecarga [kPa]", f"{res.q:.1f}"],
        ]
        elems += self._tbl("Geometría", geo_rows)

        suelo_rows = [
            ["Parámetro", "Valor"],
            ["φ — ángulo de fricción [°]", f"{phi:.1f}"],
            ["c — cohesión [kPa]", f"{c:.1f}"],
            ["γ — peso unitario [kN/m³]", f"{gamma:.1f}"],
            ["γ efectivo en la base [kN/m³]", f"{res.gamma_ef:.1f}"],
            ["FS — factor de seguridad", f"{FS:.1f}"],
        ]
        if nf_prof is not None:
            suelo_rows.append(["Nivel freático [m desde superficie]", f"{nf_prof:.2f}"])
        if gsub is not None:
            suelo_rows.append(["γ' — peso sumergido [kN/m³]", f"{gsub:.1f}"])
        elems += self._tbl("Suelo y materiales", suelo_rows)

        return elems

    # ── Factores de capacidad portante ───────────────────────────────────────

    def _factores(self, est, motor):
        res = motor.res
        elems = [Paragraph("2. Factores de Capacidad Portante", est['T2'])]

        tbl_rows = [["Método", "Nc", "Nq", "Nγ", "sc", "sq", "sγ", "dc", "dq", "dγ"]]
        for m in res.metodos:
            tbl_rows.append([
                m.nombre,
                f"{m.Nc:.2f}",   f"{m.Nq:.2f}",    f"{m.Ngamma:.2f}",
                f"{m.sc:.3f}",   f"{m.sq:.3f}",     f"{m.sgamma:.3f}",
                f"{m.dc:.3f}",   f"{m.dq:.3f}",     f"{m.dgamma:.3f}",
            ])

        col_w = [3.8*cm] + [1.3*cm]*9
        t = Table(tbl_rows, colWidths=col_w)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_AZUL)),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTSIZE',   (0, 0), (-1, -1), 8),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID',       (0, 0), (-1, -1), 0.4, colors.HexColor(_GRIS)),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor(_CABEC)]),
            ('ALIGN',      (1, 0), (-1, -1), 'CENTER'),
        ]))
        elems.append(t)
        elems.append(Spacer(1, 0.3*cm))
        return elems

    # ── Tabla comparativa qu / qa ─────────────────────────────────────────────

    def _comparativa(self, est, motor):
        res = motor.res
        elems = [Paragraph("3. Capacidad Portante — Tabla Comparativa", est['T2'])]

        rows = [["Método", "qu [kPa]", "qa [kPa]", "Observación"]]
        qa_vals = [m.q_adm for m in res.metodos]
        qa_min = min(qa_vals)

        for m in res.metodos:
            obs = "← conservador" if abs(m.q_adm - qa_min) < 0.1 else ""
            rows.append([m.nombre, f"{m.q_ult:.1f}", f"{m.q_adm:.1f}", obs])

        rows.append(["qa conservador (mín.)", "—", f"{res.qa_conserv:.1f}", "Recomendado para diseño"])
        rows.append(["qa promedio",            "—", f"{res.qa_medio:.1f}",   ""])

        col_w = [4.5*cm, 2.5*cm, 2.5*cm, 4.5*cm]
        t = Table(rows, colWidths=col_w)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_AZUL)),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID',       (0, 0), (-1, -1), 0.4, colors.HexColor(_GRIS)),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2),
             [colors.white, colors.HexColor(_CABEC)]),
            ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor("#E8F5E9")),
            ('FONTNAME',   (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN',      (1, 0), (2, -1), 'CENTER'),
        ]))
        elems.append(t)
        elems.append(Spacer(1, 0.3*cm))
        return elems

    # ── Mensajes ─────────────────────────────────────────────────────────────

    def _mensajes(self, est, res):
        elems = [Paragraph("4. Verificaciones y mensajes", est['T2'])]
        tipo_color = {
            "ok":          _VERDE,
            "advertencia": _NARANJA,
            "error":       _ROJO,
            "info":        "#555555",
        }
        for msg in (res.mensajes or []):
            color = tipo_color.get(msg.get("tipo", "info"), "#555555")
            p = Paragraph(
                f"<font color='{color}'>● {msg['texto']}</font>",
                ParagraphStyle('MSG', parent=est['Normal'],
                               fontSize=9, leading=12, spaceAfter=3),
            )
            elems.append(p)
        if not res.mensajes:
            elems.append(Paragraph("Sin mensajes.", est['Pie']))
        return elems

    # ── Helper tabla genérica ─────────────────────────────────────────────────

    def _tbl(self, titulo: str, filas: list, col_w=None):
        elems = []
        if titulo:
            elems.append(Paragraph(titulo, ParagraphStyle(
                'SEC', parent=ParagraphStyle('base'), fontSize=9.5,
                fontName='Helvetica-Bold', textColor=colors.HexColor(_AZUL),
                spaceBefore=6, spaceAfter=3, leading=12,
            )))
        if col_w is None:
            col_w = [8*cm, 6*cm]
        t = Table(filas, colWidths=col_w)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_AZUL)),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID',       (0, 0), (-1, -1), 0.4, colors.HexColor(_GRIS)),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor(_CABEC)]),
            ('ALIGN',      (1, 0), (-1, -1), 'RIGHT'),
        ]))
        elems.append(t)
        elems.append(Spacer(1, 0.25*cm))
        return elems

    # ── Fallback TXT ──────────────────────────────────────────────────────────

    def _generar_txt(self, ruta, motor, datos_entrada):
        res = motor.res
        lines = [
            "FundaCalc — Módulo 8: Capacidad Portante",
            f"Generado: {datetime.now():%d/%m/%Y %H:%M}",
            "-" * 60,
        ]
        for m in res.metodos:
            lines.append(f"{m.nombre}: qu={m.q_ult:.1f} kPa  qa={m.q_adm:.1f} kPa")
        lines.append(f"qa conservador: {res.qa_conserv:.1f} kPa")
        with open(ruta.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
