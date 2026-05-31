"""
Generador de Memoria de Cálculo PDF — Zapata Combinada.

Estructura de páginas:
  1. Portada
  2. Datos de entrada
  3. Geometría + presiones + momentos longitudinales
  4. Vista en planta (página completa — nunca se parte)
  5. Diagramas V(x) y M(x) (página completa — nunca se parte)
  6. Verificaciones + armadura
  7. Cómputo de materiales (tabla + leyenda de criterios)
  8. Mensajes de cálculo
"""

from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER

from core.zapata_combinada import ZapataCombinadaRectangular, ResultadosZapataCombi

import re

_BAR_KG_M = {
    8: 0.395, 10: 0.617, 12: 0.888, 16: 1.578,
    20: 2.466, 25: 3.854, 32: 6.313,
}

def _db_mm(varilla: str) -> int:
    m = re.search(r'(\d+)', varilla or '')
    return int(m.group(1)) if m else 16

AZUL       = colors.HexColor("#1565C0")
VERDE      = colors.HexColor("#2e7d32")
ROJO       = colors.HexColor("#c62828")
GRIS_CLARO = colors.HexColor("#ECEFF1")
ANCHO_UTIL = 17 * cm    # A4 − 2 cm márgenes c/lado


class GeneradorPDFCombinada:

    def generar(self, ruta: str, motor: ZapataCombinadaRectangular,
                norma_nombre: str, datos_entrada: dict,
                imagen_planta: str = None, imagen_diagramas: str = None):

        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm,   bottomMargin=2*cm,
        )
        estilos = getSampleStyleSheet()
        h = []

        h += self._portada(estilos, norma_nombre)
        h.append(PageBreak())

        h += self._datos_entrada(estilos, motor, datos_entrada)
        h.append(PageBreak())

        h += self._geometria_presiones(estilos, motor.res, datos_entrada)
        h.append(PageBreak())

        # ── imagen planta — página completa ──────────────────────────────
        if imagen_planta:
            h += self._pagina_imagen(estilos, "Vista en Planta", imagen_planta,
                                     ANCHO_UTIL, ANCHO_UTIL * 0.68)
        h.append(PageBreak())

        # ── diagramas V/M — página completa ──────────────────────────────
        if imagen_diagramas:
            h += self._pagina_imagen(estilos, "Diagramas V(x) y M(x)", imagen_diagramas,
                                     ANCHO_UTIL, ANCHO_UTIL * 0.72)
        h.append(PageBreak())

        h += self._verificaciones_armadura(estilos, motor.res, datos_entrada)
        h.append(PageBreak())

        h += self._computo_materiales(estilos, motor)
        h.append(PageBreak())

        h += self._mensajes(estilos, motor.res)

        doc.build(h)

    # ── estilos ───────────────────────────────────────────────────────────────

    def _h1(self, estilos):
        return ParagraphStyle('H1', parent=estilos['Normal'],
                              fontSize=15, textColor=AZUL,
                              fontName='Helvetica-Bold',
                              spaceBefore=0, spaceAfter=6)

    def _h2(self, estilos, color=None):
        return ParagraphStyle('H2', parent=estilos['Normal'],
                              fontSize=11, textColor=color or AZUL,
                              fontName='Helvetica-Bold',
                              spaceBefore=8, spaceAfter=4)

    def _tabla_style(self):
        return TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('GRID',          (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ])

    # ── secciones ─────────────────────────────────────────────────────────────

    def _portada(self, estilos, norma_nombre):
        logo = ParagraphStyle('Logo', fontSize=38, textColor=AZUL,
                              alignment=TA_CENTER, leading=46)
        sub  = ParagraphStyle('Sub',  fontSize=14, textColor=colors.grey,
                              alignment=TA_CENTER, leading=20)
        info = ParagraphStyle('Info', fontSize=11, spaceAfter=4, leading=16)
        return [
            Spacer(1, 3*cm),
            Paragraph("FundaCalc", logo),
            Spacer(1, 0.5*cm),
            Paragraph("Memoria de Cálculo — Zapata Combinada", sub),
            Spacer(1, 1.0*cm),
            HRFlowable(width="100%", thickness=2, color=AZUL),
            Spacer(1, 1.0*cm),
            Paragraph(f"Norma de diseño: <b>{norma_nombre}</b>", info),
            Paragraph(f"Fecha: <b>{datetime.now().strftime('%d/%m/%Y %H:%M')}</b>", info),
        ]

    def _datos_entrada(self, estilos, motor: ZapataCombinadaRectangular, datos_entrada: dict):
        col1, col2 = motor.col1, motor.col2
        suelo = motor.suelo
        horm  = motor.hormigon
        acero = motor.acero
        geo   = motor.geo

        ue  = datos_entrada.get("unidades", {})
        uf  = ue.get("cargas", "kN")
        up  = ue.get("presiones", "kN/m²")
        orig = datos_entrada.get("orig", {})

        tit = Paragraph("1. Datos de Entrada", self._h1(estilos))

        # columnas
        tit_col = Paragraph("Columnas", self._h2(estilos))
        t_col = Table(
            [["", f"Col 1", "Col 2"],
             [f"Pd [{uf}]",    f"{orig.get('Pd1', col1.Pd):.1f}", f"{orig.get('Pd2', col2.Pd):.1f}"],
             [f"Pl [{uf}]",    f"{orig.get('Pl1', col1.Pl):.1f}", f"{orig.get('Pl2', col2.Pl):.1f}"],
             ["Pu [kN]",       f"{col1.Pu:.1f}",                   f"{col2.Pu:.1f}"],
             ["Ancho bx (m)",  f"{col1.ancho:.2f}",                f"{col2.ancho:.2f}"],
             ["Largo by (m)",  f"{col1.largo:.2f}",                f"{col2.largo:.2f}"]],
            colWidths=[6*cm, 5.5*cm, 5.5*cm],
        )
        t_col.setStyle(self._tabla_style())

        # suelo + materiales
        tit_sm = Paragraph("Suelo y Materiales", self._h2(estilos))
        qa_orig = orig.get('qa', suelo.qa)
        t_sm = Table(
            [["Parámetro", "Valor", "Parámetro", "Valor"],
             [f"qa [{up}]",       f"{qa_orig:.1f}",           "fck (MPa)",       f"{horm.fck:.1f}"],
             ["Df (m)",           f"{suelo.Df:.2f}",           "fy (MPa)",        f"{acero.fy:.1f}"],
             ["γ suelo (kN/m³)", f"{suelo.gamma_suelo:.1f}",  "Recub. (m)",      f"{geo.recubrimiento:.3f}"]],
            colWidths=[4.5*cm, 3.5*cm, 4.5*cm, 4.5*cm],
        )
        t_sm.setStyle(self._tabla_style())

        # geometría
        tit_geo = Paragraph("Geometría", self._h2(estilos))
        t_geo = Table(
            [["Parámetro", "Valor"],
             ["L entre ejes (m)",              f"{geo.L_entre:.2f}"],
             ["h zapata (m)",                  f"{geo.h:.2f}"],
             ["Ancho fijo B (m)",              f"{geo.B_fijo:.2f}" if geo.B_fijo > 0 else "Automático"],
             ["Col1 en borde de propiedad",    "Sí" if geo.col1_en_borde else "No"]],
            colWidths=[8*cm, 9*cm],
        )
        t_geo.setStyle(self._tabla_style())

        return [tit,
                KeepTogether([tit_col, t_col]), Spacer(1, 0.4*cm),
                KeepTogether([tit_sm,  t_sm]),  Spacer(1, 0.4*cm),
                KeepTogether([tit_geo, t_geo])]

    def _geometria_presiones(self, estilos, res: ResultadosZapataCombi, datos_entrada: dict):
        up = datos_entrada.get("unidades", {}).get("presiones", "kN/m²")

        tit = Paragraph("2. Geometría de la Zapata y Presiones", self._h1(estilos))

        tit_dim = Paragraph("Dimensiones calculadas", self._h2(estilos))
        t_dim = Table(
            [["Parámetro", "Valor", "Parámetro", "Valor"],
             ["B — ancho (m)",    f"{res.B:.2f}", "h — canto (m)",    f"{res.h:.2f}"],
             ["L — largo (m)",    f"{res.L:.2f}", "Área (m²)",        f"{res.area:.2f}"],
             ["d1 — eje col1 (m)",f"{res.d1:.2f}","d2 — eje col2 (m)",f"{res.d2:.2f}"]],
            colWidths=[4.5*cm, 4*cm, 4.5*cm, 4*cm],
        )
        t_dim.setStyle(self._tabla_style())

        tit_pre = Paragraph("Presiones", self._h2(estilos))
        st_pre = self._tabla_style()
        ok_txt = "✔ CUMPLE" if res.ok_presion else "✘ FALLA"
        st_pre.add('TEXTCOLOR', (2, 2), (2, 2), VERDE if res.ok_presion else ROJO)
        st_pre.add('FONTNAME',  (2, 2), (2, 2), 'Helvetica-Bold')
        t_pre = Table(
            [[f"Parámetro",          f"Valor [{up}]",       "Estado"],
             ["q neto admisible",    f"{res.q_neto:.2f}",   ""],
             ["q máx. servicio",     f"{res.q_max:.2f}",    ok_txt],
             ["q última (diseño)",   f"{res.q_ultima:.2f}", ""]],
            colWidths=[6*cm, 6*cm, 5*cm],
        )
        t_pre.setStyle(st_pre)

        tit_mom = Paragraph("Momentos longitudinales críticos", self._h2(estilos))
        t_mom = Table(
            [["Momento",                       "Valor [kN·m]",         "Descripción"],
             ["Mu neg col1 (cara interna)",    f"{res.Mu_neg1:.1f}",  "Superior, extremo izquierdo"],
             ["Mu neg col2 (cara interna)",    f"{res.Mu_neg2:.1f}",  "Superior, extremo derecho"],
             [f"Mu pos (x={res.x_Mu_pos:.2f} m)", f"{res.Mu_pos:.1f}", "Inferior, entre columnas"]],
            colWidths=[6*cm, 4.5*cm, 6.5*cm],
        )
        t_mom.setStyle(self._tabla_style())

        return [tit,
                KeepTogether([tit_dim, t_dim]), Spacer(1, 0.4*cm),
                KeepTogether([tit_pre, t_pre]), Spacer(1, 0.4*cm),
                KeepTogether([tit_mom, t_mom])]

    def _pagina_imagen(self, estilos, titulo, ruta_img, ancho, alto):
        tit = Paragraph(titulo, self._h1(estilos))
        try:
            img = Image(ruta_img, width=ancho, height=alto)
        except Exception:
            return [tit, Paragraph("(imagen no disponible)", estilos['Normal'])]
        return [tit, Spacer(1, 0.4*cm), img]

    def _verificaciones_armadura(self, estilos, res: ResultadosZapataCombi, datos_entrada: dict):
        uf = datos_entrada.get("unidades", {}).get("cargas", "kN")

        tit = Paragraph("3. Verificaciones y Armadura", self._h1(estilos))

        # verificaciones
        tit_ver = Paragraph("Verificaciones de punzonado y cortante", self._h2(estilos))
        checks = [
            ("Punzonado Col1", res.Vu_punz1,  res.phi_Vn_punz1, res.rel_punz1,    res.ok_punz1),
            ("Punzonado Col2", res.Vu_punz2,  res.phi_Vn_punz2, res.rel_punz2,    res.ok_punz2),
            ("Cortante 1-vía", res.Vu_cort,   res.phi_Vn_cort,  res.rel_cortante, res.ok_cortante),
        ]
        st_ver = self._tabla_style()
        for i, (*_, ok) in enumerate(checks, start=1):
            st_ver.add('TEXTCOLOR', (4, i), (4, i), VERDE if ok else ROJO)
            st_ver.add('FONTNAME',  (4, i), (4, i), 'Helvetica-Bold')
        t_ver = Table(
            [[f"Verificación", f"Vu [{uf}]", f"φVn [{uf}]", "Vu / φVn", "Estado"]] +
            [[lbl, f"{vu:.1f}", f"{pvn:.1f}", f"{ratio:.3f}",
              "✔ CUMPLE" if ok else "✘ FALLA"]
             for lbl, vu, pvn, ratio, ok in checks],
            colWidths=[4.5*cm, 3*cm, 3*cm, 3*cm, 3.5*cm],
        )
        t_ver.setStyle(st_ver)

        # armadura longitudinal
        tit_long = Paragraph("Armadura longitudinal", self._h2(estilos))
        t_long = Table(
            [["Capa", "Varilla", "Sep. (cm)", "As req. (cm²/m)", "N° barras"],
             ["Superior (neg)",  res.varilla_long_top or "—",
              f"{res.sep_long_top*100:.0f}",  f"{res.As_long_top_pm:.2f}", str(res.n_long_top)],
             ["Inferior (pos)",  res.varilla_long_bot or "—",
              f"{res.sep_long_bot*100:.0f}",  f"{res.As_long_bot_pm:.2f}", str(res.n_long_bot)]],
            colWidths=[4*cm, 3.5*cm, 3*cm, 4*cm, 2.5*cm],
        )
        t_long.setStyle(self._tabla_style())

        # armadura transversal
        tit_trans = Paragraph("Armadura transversal", self._h2(estilos))
        t_trans = Table(
            [["Franja", "Voladizo (m)", "Mu (kN·m)", "Varilla", "Sep. (cm)", "As req. (cm²/m)"],
             ["Col1", f"{res.vol_trans1:.2f}", f"{res.Mu_trans1:.1f}",
              res.varilla_trans1 or "—", f"{res.sep_trans1*100:.0f}", f"{res.As_trans1:.2f}"],
             ["Col2", f"{res.vol_trans2:.2f}", f"{res.Mu_trans2:.1f}",
              res.varilla_trans2 or "—", f"{res.sep_trans2*100:.0f}", f"{res.As_trans2:.2f}"]],
            colWidths=[2.5*cm, 3*cm, 3*cm, 2.5*cm, 3*cm, 3*cm],
        )
        t_trans.setStyle(self._tabla_style())

        return [tit,
                KeepTogether([tit_ver,   t_ver]),   Spacer(1, 0.5*cm),
                KeepTogether([tit_long,  t_long]),  Spacer(1, 0.5*cm),
                KeepTogether([tit_trans, t_trans])]

    def _computo_materiales(self, estilos, motor: ZapataCombinadaRectangular):
        res  = motor.res
        col1, col2 = motor.col1, motor.col2
        B, L = res.B, res.L

        tit = Paragraph("4. Cómputo de Materiales — Acero de Refuerzo", self._h1(estilos))

        # ── calcular filas ────────────────────────────────────────────────
        db_A = _db_mm(res.varilla_long_top);  wA = _BAR_KG_M.get(db_A, 1.578)
        db_B = _db_mm(res.varilla_long_bot);  wB = _BAR_KG_M.get(db_B, 1.578)
        db_C = _db_mm(res.varilla_trans1);    wC = _BAR_KG_M.get(db_C, 1.578)
        db_D = _db_mm(res.varilla_trans2);    wD = _BAR_KG_M.get(db_D, 1.578)

        len_long = round(L + 2 * 0.10, 2)           # longitud barras longitudinales
        len_C    = round(B + 2 * 0.10, 2)           # longitud barras transversales
        len_D    = len_C

        strip1 = col1.ancho + 2 * min(float(res.vol_trans1), 0.40)
        strip2 = col2.ancho + 2 * min(float(res.vol_trans2), 0.40)
        n_C = max(2, int(strip1 / res.sep_trans1) + 1)
        n_D = max(2, int(strip2 / res.sep_trans2) + 1)

        def row_kg(n, length, w): return float(n) * length * w

        kg_A = row_kg(res.n_long_top, len_long, wA)
        kg_B = row_kg(res.n_long_bot, len_long, wB)
        kg_C = row_kg(n_C,            len_C,    wC)
        kg_D = row_kg(n_D,            len_D,    wD)
        total_kg = kg_A + kg_B + kg_C + kg_D

        # ── tabla ─────────────────────────────────────────────────────────
        NARANJA_CLARO = colors.HexColor("#FFF3E0")
        NARANJA_OSC   = colors.HexColor("#E65100")

        cab = [["Marca", "Descripción", "Ø (mm)", "sep (cm)", "Long. (m)", "Ud.", "kg/m", "Total (kg)"]]
        filas = [
            ["A", "Long. Superior",
             db_A, f"{res.sep_long_top*100:.0f}", f"{len_long:.2f}", res.n_long_top, f"{wA:.3f}", f"{kg_A:.1f}"],
            ["B", "Long. Inferior",
             db_B, f"{res.sep_long_bot*100:.0f}", f"{len_long:.2f}", res.n_long_bot, f"{wB:.3f}", f"{kg_B:.1f}"],
            ["C", "Trans. Col1",
             db_C, f"{res.sep_trans1*100:.0f}", f"{len_C:.2f}", n_C, f"{wC:.3f}", f"{kg_C:.1f}"],
            ["D", "Trans. Col2",
             db_D, f"{res.sep_trans2*100:.0f}", f"{len_D:.2f}", n_D, f"{wD:.3f}", f"{kg_D:.1f}"],
            ["", "TOTAL ACERO", "", "", "", "", "", f"{total_kg:.1f} kg"],
        ]

        col_w = [1.2*cm, 4.0*cm, 1.8*cm, 2.0*cm, 2.2*cm, 1.5*cm, 2.0*cm, 2.3*cm]
        t = Table(cab + filas, colWidths=col_w)

        st = self._tabla_style()
        # fila total: fondo naranja suave, texto bold
        fila_total = len(filas)  # índice 1-based en la tabla completa
        st.add('BACKGROUND', (0, fila_total), (-1, fila_total), NARANJA_CLARO)
        st.add('FONTNAME',   (0, fila_total), (-1, fila_total), 'Helvetica-Bold')
        st.add('TEXTCOLOR',  (7, fila_total), (7, fila_total), NARANJA_OSC)
        # marcas en bold
        for i in range(1, len(filas)):
            st.add('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')
        t.setStyle(st)

        # ── leyenda de criterios ──────────────────────────────────────────
        est_leyenda = ParagraphStyle(
            'Leyenda', parent=estilos['Normal'],
            fontSize=8.5, textColor=colors.HexColor("#555555"),
            leading=13, spaceBefore=4,
            leftIndent=6, borderPad=4,
        )
        est_titulo_ley = ParagraphStyle(
            'LeyTit', parent=estilos['Normal'],
            fontSize=9, textColor=NARANJA_OSC,
            fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=2,
        )
        leyenda = [
            Spacer(1, 0.5*cm),
            Paragraph("Criterios y limitaciones del cómputo:", est_titulo_ley),
            Paragraph(
                "• No incluye el desperdicio por corte y empalme "
                "(normalmente se agrega un 5–10 % en obra).",
                est_leyenda),
            Paragraph(
                "• No incluye las longitudes de anclaje en los extremos "
                "(la longitud usada es L + 2 × 0.10 m como estimado mínimo).",
                est_leyenda),
            Paragraph(
                "• Los pesos lineales (kg/m) corresponden a barras corrugadas de acero "
                "con ρ = 7 850 kg/m³ y sección circular nominal.",
                est_leyenda),
            Paragraph(
                "• El número de barras transversales se estima sobre la franja "
                "tributaria de cada columna (ancho columna + 2 × voladizo transversal).",
                est_leyenda),
        ]

        return [tit, Spacer(1, 0.3*cm),
                KeepTogether([t]),
                *leyenda]

    def _mensajes(self, estilos, res: ResultadosZapataCombi):
        COLOR_MAP = {
            "ok": "#2e7d32", "error": "#c62828",
            "advertencia": "#e65100", "info": "#1565c0",
        }
        tit = Paragraph("4. Mensajes de Cálculo", self._h1(estilos))
        elementos = [tit, Spacer(1, 0.3*cm)]
        for msg in res.mensajes:
            color = COLOR_MAP.get(msg["tipo"], "#000000")
            icono = "✔" if msg["tipo"] == "ok" else ("✘" if msg["tipo"] == "error" else "•")
            elementos.append(Paragraph(
                f'<font color="{color}">{icono} {msg["texto"]}</font>',
                estilos['Normal'],
            ))
            elementos.append(Spacer(1, 0.1*cm))
        if not res.mensajes:
            elementos.append(Paragraph("Sin mensajes.", estilos['Normal']))
        return elementos
