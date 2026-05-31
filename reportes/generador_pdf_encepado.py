"""
Generador PDF — Encepado de Pilotes (Pile Cap).
Produce una memoria de cálculo con:
  - Portada
  - Datos de entrada
  - Geometría y cargas por pilote
  - Diagrama / sección (imagen opcional)
  - Momentos de diseño y armadura
  - Verificaciones de cortante y punzonado
  - Cómputo de materiales
  - Registro de verificaciones
"""

import os
import re
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
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False

_BAR_KG_M = {8: 0.395, 10: 0.617, 12: 0.888, 16: 1.578,
             20: 2.466, 25: 3.854, 32: 6.313}

_AZUL  = "#1565C0"
_VERDE = "#2E7D32"
_ROJO  = "#C62828"
_CABEC = "#E3F2FD"
_GRIS  = "#CCCCCC"


def _db(varilla: str) -> int:
    m = re.search(r'(\d+)', varilla or '')
    return int(m.group(1)) if m else 16


def _ok(v): return colors.HexColor("#E8F5E9") if v else colors.HexColor("#FFEBEE")
def _txt(v): return "✔ CUMPLE" if v else "✘ NO CUMPLE"


class GeneradorPDFEncepado:

    def generar(self, ruta: str, motor, datos_entrada: dict,
                imagen_seccion: str = None):
        if not _REPORTLAB:
            self._generar_txt(ruta, motor, datos_entrada)
            return
        self._generar_pdf(ruta, motor, datos_entrada, imagen_seccion)

    # ── Documento ───────────────────────────────────────────────────────────

    def _generar_pdf(self, ruta, motor, datos_entrada, imagen_seccion):
        MARGEN = 2.0 * cm
        ANCHO, _ = A4
        ANCHO_UTIL = ANCHO - 2 * MARGEN

        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            leftMargin=MARGEN, rightMargin=MARGEN,
            topMargin=MARGEN, bottomMargin=MARGEN,
        )

        est = getSampleStyleSheet()
        est.add(ParagraphStyle('T1', parent=est['Heading1'], fontSize=16,
                               spaceAfter=10, textColor=colors.HexColor(_AZUL)))
        est.add(ParagraphStyle('T2', parent=est['Heading2'], fontSize=12,
                               spaceAfter=6,  textColor=colors.HexColor(_AZUL)))
        est.add(ParagraphStyle('Cuerpo', parent=est['Normal'], fontSize=9.5, spaceAfter=3))
        est.add(ParagraphStyle('Pie', parent=est['Normal'], fontSize=8,
                               textColor=colors.gray, spaceAfter=2))

        norma = datos_entrada.get("norma", "ACI318")
        res   = motor.res

        h = []
        h += self._portada(est, norma)
        h.append(PageBreak())
        h += self._datos_entrada(est, motor, datos_entrada)
        h.append(PageBreak())
        h += self._geometria_pilotes(est, motor)
        if imagen_seccion:
            h.append(PageBreak())
            h += self._pagina_imagen(est,
                                     "Diagrama del Encepado (planta + sección)",
                                     imagen_seccion, ANCHO_UTIL, ANCHO_UTIL * 0.62)
        h.append(PageBreak())
        h += self._momentos_armadura(est, motor)
        h.append(PageBreak())
        h += self._verificaciones(est, motor)
        h.append(PageBreak())
        h += self._computo_materiales(est, motor)
        h.append(PageBreak())
        h += self._mensajes(est, res)

        doc.build(h)

    # ── Secciones ───────────────────────────────────────────────────────────

    def _portada(self, est, norma):
        azul  = colors.HexColor(_AZUL)
        gris  = colors.HexColor("#546E7A")
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Estilos de portada definidos como objetos completos (evita solapamiento)
        st_titulo = ParagraphStyle('pT',  fontSize=36, textColor=azul,
                                   alignment=TA_CENTER, leading=44,
                                   spaceBefore=0, spaceAfter=8)
        st_sub    = ParagraphStyle('pS',  fontSize=15, textColor=gris,
                                   alignment=TA_CENTER, leading=20,
                                   spaceBefore=0, spaceAfter=0)
        st_mem    = ParagraphStyle('pM',  fontSize=22, textColor=azul,
                                   alignment=TA_CENTER, leading=28,
                                   spaceBefore=0, spaceAfter=8)
        st_mod    = ParagraphStyle('pMd', fontSize=13, textColor=colors.HexColor("#37474F"),
                                   alignment=TA_CENTER, leading=18,
                                   spaceBefore=0, spaceAfter=0)

        p = [
            Spacer(1, 3*cm),
            Paragraph("FundaCalc", st_titulo),
            Spacer(1, 0.3*cm),
            Paragraph("Diseño de Cimentaciones", st_sub),
            Spacer(1, 2.5*cm),
            Paragraph("MEMORIA DE CÁLCULO", st_mem),
            Spacer(1, 0.4*cm),
            Paragraph("Módulo 6 — Encepado de Pilotes", st_mod),
            Spacer(1, 2.5*cm),
        ]

        # Tabla de metadatos centrada
        tbl = Table(
            [["Norma de diseño:", norma],
             ["Fecha de emisión:", fecha],
             ["Versión:", "1.0"]],
            colWidths=[5.5*cm, 8*cm],
            hAlign='CENTER',
        )
        tbl.setStyle(TableStyle([
            ('FONTSIZE',     (0, 0), (-1, -1), 10),
            ('TEXTCOLOR',    (0, 0), (0, -1), azul),
            ('FONTNAME',     (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME',     (1, 0), (1, -1), 'Helvetica'),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 7),
            ('TOPPADDING',   (0, 0), (-1, -1), 7),
            ('LINEBELOW',    (0, 0), (-1, -2), 0.3, colors.HexColor("#BBDEFB")),
        ]))
        p.append(tbl)
        return p

    def _tbl(self, titulo, filas, col_w=None):
        col_w = col_w or [9*cm, 6*cm]
        azul  = colors.HexColor(_AZUL)
        tbl   = Table([[titulo, ""]] + filas, colWidths=col_w)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9.5),
            ('SPAN',       (0, 0), (-1, 0)),
            ('TEXTCOLOR',  (0, 0), (-1, 0), azul),
            ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ]))
        return KeepTogether([Spacer(1, 0.3*cm), tbl])

    def _datos_entrada(self, est, motor, datos_entrada):
        carga = motor.carga
        col   = motor.columna
        pil   = motor.pilote
        geo   = motor.geo
        horm  = motor.hormigon
        ace   = motor.acero
        norma = datos_entrada.get("norma", "ACI318")

        p = [Paragraph("Datos de Entrada", est['T1'])]

        filas_c = [
            ["Carga muerta axial Pd",          f"{carga.Pd:.1f} kN"],
            ["Carga viva axial Pl",            f"{carga.Pl:.1f} kN"],
            ["Momento muerto + vivo Mdx+Mlx",  f"{carga.Mdx + carga.Mlx:.1f} kN·m"],
            ["Momento muerto + vivo Mdy+Mly",  f"{carga.Mdy + carga.Mly:.1f} kN·m"],
            ["Carga de servicio Pser",         f"{carga.Pser:.1f} kN"],
            ["Carga última Pu",                f"{carga.Pu:.1f} kN"],
        ]
        p.append(self._tbl("Cargas de Diseño", filas_c))

        filas_col = [
            ["Dimensión columna cx", f"{col.cx*100:.0f} cm"],
            ["Dimensión columna cy", f"{col.cy*100:.0f} cm"],
        ]
        p.append(self._tbl("Columna", filas_col))

        modo_label = "Automático" if pil.modo == "auto" else "Manual"
        filas_pil = [
            ["Diámetro pilote D",        f"{pil.D*100:.0f} cm"],
            ["Carga admisible Qa",       f"{pil.Qa:.0f} kN"],
            ["Modo de configuración",    modo_label],
            ["Pilotes en X (config.)",   f"{pil.nx}"],
            ["Pilotes en Y (config.)",   f"{pil.ny}"],
            ["Separación X sx (config.)",f"{pil.spacing_x:.2f} m" if pil.spacing_x > 0 else "Automática"],
            ["Separación Y sy (config.)",f"{pil.spacing_y:.2f} m" if pil.spacing_y > 0 else "Automática"],
            ["Vuelo borde X vx",         f"{pil.vuelo_x:.2f} m" if pil.vuelo_x > 0 else "Automático"],
            ["Vuelo borde Y vy",         f"{pil.vuelo_y:.2f} m" if pil.vuelo_y > 0 else "Automático"],
        ]
        p.append(self._tbl("Configuración de Pilotes", filas_pil))

        filas_geo = [
            ["Altura total del encepado h", f"{geo.h:.2f} m"],
            ["Recubrimiento nominal r",     f"{geo.recubrimiento*100:.1f} cm"],
            ["Canto útil d",               f"{geo.d:.3f} m"],
        ]
        p.append(self._tbl("Geometría del Encepado", filas_geo))

        filas_mat = [
            ["Resistencia hormigón f'c / fck", f"{horm.fck:.1f} MPa"],
            ["Límite de fluencia acero fy",    f"{ace.fy:.1f} MPa"],
            ["Norma de diseño",                norma],
        ]
        p.append(self._tbl("Materiales", filas_mat))
        return p

    def _geometria_pilotes(self, est, motor):
        res = motor.res
        azul = colors.HexColor(_AZUL)
        p = [Paragraph("Geometría de Pilotes y Cargas", est['T1'])]

        filas_conf = [
            ["Pilotes en X (nx)",        f"{res.nx}"],
            ["Pilotes en Y (ny)",        f"{res.ny}"],
            ["Total pilotes (n)",         f"{res.n}"],
            ["Largo encepado L",         f"{res.L:.2f} m"],
            ["Ancho encepado B",         f"{res.B:.2f} m"],
            ["Área A = L × B",           f"{res.A:.2f} m²"],
            ["Separación X sx",          f"{res.spacing_x:.2f} m"],
            ["Separación Y sy",          f"{res.spacing_y:.2f} m"],
            ["Vuelo borde X vx",         f"{res.vuelo_x:.2f} m"],
            ["Vuelo borde Y vy",         f"{res.vuelo_y:.2f} m"],
            ["Altura encepado h",        f"{res.h:.2f} m"],
            ["Canto útil d",             f"{res.d:.3f} m"],
        ]
        p.append(self._tbl("Configuración Geométrica Calculada", filas_conf))

        # Tabla de cargas por pilote
        p.append(Spacer(1, 0.3*cm))
        p.append(Paragraph("Cargas por Pilote", est['T2']))

        hdrs = ["Pilote #", "x (m)", "y (m)", "P_ser (kN)", "P_ult (kN)"]
        filas_p = [hdrs]

        positions  = res.pile_positions
        loads_ser  = res.pile_loads_ser
        loads_ult  = res.pile_loads_ult
        n_pilotes  = len(positions)

        mostrar_todos = n_pilotes <= 20
        if mostrar_todos:
            for i, ((x, y), Ps, Pu) in enumerate(zip(positions, loads_ser, loads_ult), 1):
                filas_p.append([str(i), f"{x:.3f}", f"{y:.3f}",
                                f"{Ps:.1f}", f"{Pu:.1f}"])
        else:
            # Mostrar solo los 5 pilotes más cargados y los 5 menos cargados
            indices_sorted = sorted(range(n_pilotes), key=lambda i: loads_ser[i])
            mostrar_idx = set(indices_sorted[:5] + indices_sorted[-5:])
            prev_skip = False
            for i in range(n_pilotes):
                if i in mostrar_idx:
                    x, y = positions[i]
                    filas_p.append([str(i+1), f"{x:.3f}", f"{y:.3f}",
                                    f"{loads_ser[i]:.1f}", f"{loads_ult[i]:.1f}"])
                    prev_skip = False
                else:
                    if not prev_skip:
                        filas_p.append(["…", "…", "…", "…", "…"])
                        prev_skip = True

        # Fila de envolvente
        filas_p.append([
            "Envolvente",
            "P_max / P_min",
            f"{res.P_max:.1f} / {res.P_min:.1f}",
            "P_max_u / P_min_u",
            f"{res.P_max_u:.1f} / {res.P_min_u:.1f}",
        ])

        col_w_p = [1.5*cm, 2.5*cm, 2.5*cm, 3.0*cm, 3.0*cm]
        tbl_p = Table(filas_p, colWidths=col_w_p)
        n_env = len(filas_p) - 1  # índice fila envolvente (base 0)
        tbl_p.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0),  (-1, 0),     colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0),  (-1, 0),     'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0),  (-1, -1),    9),
            ('TEXTCOLOR',     (0, 0),  (-1, 0),     azul),
            ('GRID',          (0, 0),  (-1, -1),    0.3, colors.HexColor(_GRIS)),
            ('ALIGN',         (1, 0),  (-1, -1),    'CENTER'),
            ('BOTTOMPADDING', (0, 0),  (-1, -1),    4),
            ('TOPPADDING',    (0, 0),  (-1, -1),    4),
            ('BACKGROUND',    (0, n_env), (-1, n_env), colors.HexColor("#FFF3E0")),
            ('FONTNAME',      (0, n_env), (-1, n_env), 'Helvetica-Bold'),
            ('SPAN',          (1, n_env), (2, n_env)),
            ('SPAN',          (3, n_env), (4, n_env)),
        ]))
        p.append(tbl_p)

        if not mostrar_todos:
            p.append(Paragraph(
                f"Nota: se muestran los 5 pilotes más cargados y 5 menos cargados de un total de {n_pilotes}.",
                ParagraphStyle('n', fontSize=8, textColor=colors.gray, spaceAfter=4)))

        # Verificaciones geotécnicas
        p.append(Spacer(1, 0.3*cm))
        filas_geo_v = [
            ["Verificación capacidad (P_max ≤ Qa)", _txt(res.ok_capacidad)],
            ["Verificación tensión   (P_min ≥ 0)",  _txt(res.ok_tension)],
        ]
        tbl_v = Table([["Verificaciones Geotécnicas", ""]] + filas_geo_v,
                      colWidths=[9*cm, 6*cm])
        tbl_v.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0),  (-1, 0),  colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0),  (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0),  (-1, -1), 9.5),
            ('SPAN',          (0, 0),  (-1, 0)),
            ('TEXTCOLOR',     (0, 0),  (-1, 0),  azul),
            ('GRID',          (0, 0),  (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0),  (-1, -1), 4),
            ('TOPPADDING',    (0, 0),  (-1, -1), 4),
            ('BACKGROUND',    (0, 1),  (-1, 1),  _ok(res.ok_capacidad)),
            ('BACKGROUND',    (0, 2),  (-1, 2),  _ok(res.ok_tension)),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm), tbl_v]))
        return p

    def _pagina_imagen(self, est, titulo, ruta_img, ancho, alto):
        p = [Paragraph(titulo, est['T1'])]
        if ruta_img and os.path.exists(ruta_img):
            p.append(Spacer(1, 0.3*cm))
            p.append(RLImage(ruta_img, width=ancho, height=alto))
        return p

    def _momentos_armadura(self, est, motor):
        res = motor.res
        azul = colors.HexColor(_AZUL)
        p = [Paragraph("Momentos de Diseño y Armadura", est['T1'])]

        filas_mu = [
            ["Momento último Mu_x (sobre ancho B)", f"{res.Mu_x:.1f} kN·m"],
            ["Momento último Mu_y (sobre largo L)",  f"{res.Mu_y:.1f} kN·m"],
        ]
        p.append(self._tbl("Momentos Críticos de Diseño [kN·m]", filas_mu))

        def sep_cm(v): return f"{v*100:.0f} cm" if v and v > 0 else "—"

        filas_arm = [
            ["Dirección", "As req.\n(cm²/m)", "Varilla", "N° barras", "Sep.", "As dis.\n(cm²/m)"]
        ]
        filas_arm.append([
            "Dir. X (// X, sobre ancho B)",
            f"{res.As_req_x:.2f}",
            res.var_x or "—",
            str(res.n_barras_x),
            sep_cm(res.sep_x),
            f"{res.As_dis_x:.2f}",
        ])
        filas_arm.append([
            "Dir. Y (// Y, sobre largo L)",
            f"{res.As_req_y:.2f}",
            res.var_y or "—",
            str(res.n_barras_y),
            sep_cm(res.sep_y),
            f"{res.As_dis_y:.2f}",
        ])

        col_w_arm = [5.0*cm, 2.2*cm, 2.0*cm, 2.0*cm, 1.8*cm, 2.2*cm]
        tbl_arm = Table(filas_arm, colWidths=col_w_arm)
        tbl_arm.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('TEXTCOLOR',     (0, 0), (-1, 0), azul),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm),
                               Paragraph("Armadura de Flexión", est['T2']),
                               tbl_arm]))

        p.append(Paragraph(
            f"As mínimo = {res.As_min:.2f} cm²/m  "
            "(controla cuando el momento requerido es muy pequeño).",
            ParagraphStyle('n', fontSize=8.5, textColor=colors.gray, spaceAfter=4)))
        return p

    def _verificaciones(self, est, motor):
        res  = motor.res
        azul = colors.HexColor(_AZUL)
        p    = [Paragraph("Verificaciones Estructurales", est['T1'])]

        # Cortante unidireccional
        filas_cort = [
            ["Cortante dir. X: Vu_x",       f"{res.Vu_x:.1f} kN"],
            ["Resistencia dir. X: φVc_x",   f"{res.phi_Vc_x:.1f} kN"],
            ["Verificación cortante X",      _txt(res.ok_cx)],
            ["Cortante dir. Y: Vu_y",       f"{res.Vu_y:.1f} kN"],
            ["Resistencia dir. Y: φVc_y",   f"{res.phi_Vc_y:.1f} kN"],
            ["Verificación cortante Y",      _txt(res.ok_cy)],
        ]
        tbl_cort = Table([["Cortante Unidireccional (One-Way Shear)", ""]] + filas_cort,
                         colWidths=[9*cm, 6*cm])
        tbl_cort.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9.5),
            ('SPAN',          (0, 0), (-1, 0)),
            ('TEXTCOLOR',     (0, 0), (-1, 0), azul),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BACKGROUND',    (0, 3), (-1, 3),  _ok(res.ok_cx)),
            ('BACKGROUND',    (0, 6), (-1, 6),  _ok(res.ok_cy)),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm), tbl_cort]))

        # Punzonado columna
        filas_pcol = [
            ["Perímetro crítico columna b0_col",   f"{res.b0_col:.3f} m"],
            ["Cortante punzonado columna Vu",       f"{res.Vu_punch_col:.1f} kN"],
            ["Resistencia punzonado columna φVc",   f"{res.phi_Vc_col:.1f} kN"],
            ["Verificación punzonado columna",      _txt(res.ok_punch_col)],
        ]
        tbl_pcol = Table([["Punzonado por Columna (Two-Way Shear)", ""]] + filas_pcol,
                         colWidths=[9*cm, 6*cm])
        tbl_pcol.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9.5),
            ('SPAN',          (0, 0), (-1, 0)),
            ('TEXTCOLOR',     (0, 0), (-1, 0), azul),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BACKGROUND',    (0, 4), (-1, 4),  _ok(res.ok_punch_col)),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm), tbl_pcol]))

        # Punzonado pilote
        filas_ppil = [
            ["Perímetro crítico pilote b0_pil",    f"{res.b0_pil:.3f} m"],
            ["Cortante punzonado pilote Vu",        f"{res.Vu_punch_pil:.1f} kN"],
            ["Resistencia punzonado pilote φVc",    f"{res.phi_Vc_pil:.1f} kN"],
            ["Verificación punzonado pilote",       _txt(res.ok_punch_pil)],
        ]
        tbl_ppil = Table([["Punzonado por Pilote (Two-Way Shear)", ""]] + filas_ppil,
                         colWidths=[9*cm, 6*cm])
        tbl_ppil.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9.5),
            ('SPAN',          (0, 0), (-1, 0)),
            ('TEXTCOLOR',     (0, 0), (-1, 0), azul),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BACKGROUND',    (0, 4), (-1, 4),  _ok(res.ok_punch_pil)),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm), tbl_ppil]))
        return p

    def _computo_materiales(self, est, motor):
        res  = motor.res
        L, B = res.L, res.B
        h    = res.h
        azul = colors.HexColor(_AZUL)
        p    = [Paragraph("Cómputo de Materiales", est['T1'])]

        hdrs  = ["Material", "Descripción", "Ø (mm)", "Cant.", "Long. (m)", "kg/m", "Total (kg)"]
        filas = [hdrs]
        total_acero = 0.0

        # Dirección X: n_barras_x barras de longitud L
        if res.var_x and res.sep_x > 0:
            db_x   = _db(res.var_x)
            kg_m_x = _BAR_KG_M.get(db_x, 1.578)
            long_x = L + 0.30   # gancho
            sub_x  = res.n_barras_x * long_x * kg_m_x
            total_acero += sub_x
            filas.append(["Acero Dir. X",
                           f"Arm. // X  ({res.n_barras_x} barras)",
                           str(db_x), str(res.n_barras_x),
                           f"{long_x:.2f}", f"{kg_m_x:.3f}", f"{sub_x:.1f}"])

        # Dirección Y: n_barras_y barras de longitud B
        if res.var_y and res.sep_y > 0:
            db_y   = _db(res.var_y)
            kg_m_y = _BAR_KG_M.get(db_y, 1.578)
            long_y = B + 0.30   # gancho
            sub_y  = res.n_barras_y * long_y * kg_m_y
            total_acero += sub_y
            filas.append(["Acero Dir. Y",
                           f"Arm. // Y  ({res.n_barras_y} barras)",
                           str(db_y), str(res.n_barras_y),
                           f"{long_y:.2f}", f"{kg_m_y:.3f}", f"{sub_y:.1f}"])

        filas.append(["", "TOTAL ACERO", "", "", "", "", f"{total_acero:.1f}"])

        # Hormigón
        vol_h = L * B * h
        peso_h = vol_h * 2400.0
        filas.append(["Hormigón", "Encepado completo", "—", "—",
                       f"{vol_h:.3f} m³", f"2400 kg/m³", f"{peso_h:.0f}"])

        col_w = [2.5*cm, 4.0*cm, 1.8*cm, 1.5*cm, 2.3*cm, 2.0*cm, 2.2*cm]
        tbl   = Table(filas, colWidths=col_w)
        i_tot = len(filas) - 2   # fila "TOTAL ACERO"
        i_horm = len(filas) - 1  # fila hormigón
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0),      (-1, 0),      colors.HexColor(_CABEC)),
            ('FONTNAME',      (0, 0),      (-1, 0),      'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0),      (-1, -1),     8.5),
            ('TEXTCOLOR',     (0, 0),      (-1, 0),      azul),
            ('GRID',          (0, 0),      (-1, -1),     0.3, colors.HexColor(_GRIS)),
            ('BOTTOMPADDING', (0, 0),      (-1, -1),     4),
            ('TOPPADDING',    (0, 0),      (-1, -1),     4),
            ('BACKGROUND',    (0, i_tot),  (-1, i_tot),  colors.HexColor("#FFF3E0")),
            ('FONTNAME',      (0, i_tot),  (-1, i_tot),  'Helvetica-Bold'),
            ('BACKGROUND',    (0, i_horm), (-1, i_horm), colors.HexColor("#E3F2FD")),
        ]))
        p.append(KeepTogether([Spacer(1, 0.3*cm), tbl]))

        notas = [
            "• Cantidades son para el encepado completo.",
            "• Acero: no incluye desperdicio (agregar 5–10 % en obra).",
            "• Long. incluye 30 cm de gancho estándar; sin longitudes de anclaje extremas.",
            "• Hormigón: peso unitario asumido 2 400 kg/m³.",
        ]
        for nota in notas:
            p.append(Paragraph(nota, ParagraphStyle('n', fontSize=8,
                                                     textColor=colors.gray, spaceAfter=2)))
        return p

    def _mensajes(self, est, res):
        azul  = colors.HexColor(_AZUL)
        verde = colors.HexColor(_VERDE)
        rojo  = colors.HexColor(_ROJO)
        p = [Paragraph("Registro de Verificaciones", est['T1'])]
        for msg in res.mensajes:
            c = verde if msg["tipo"] == "ok" else (rojo if msg["tipo"] == "error" else azul)
            p.append(Paragraph(msg["texto"],
                               ParagraphStyle('m', fontSize=9, textColor=c, spaceAfter=3)))
        return p

    # ── Fallback texto ──────────────────────────────────────────────────────

    def _generar_txt(self, ruta, motor, datos_entrada):
        res   = motor.res
        norma = datos_entrada.get("norma", "?")
        lines = [
            "FundaCalc — Encepado de Pilotes",
            f"Norma: {norma}   Fecha: {datetime.now():%d/%m/%Y %H:%M}",
            "=" * 60,
            f"Pilotes: {res.n}  ({res.nx}×{res.ny})  Qa={motor.pilote.Qa:.0f} kN",
            f"L={res.L:.2f} m  B={res.B:.2f} m  h={res.h:.2f} m  d={res.d:.3f} m",
            f"sx={res.spacing_x:.2f} m  sy={res.spacing_y:.2f} m",
            f"P_max={res.P_max:.1f} kN  P_min={res.P_min:.1f} kN",
            f"Capacidad: {'OK' if res.ok_capacidad else 'FALLA'}  "
            f"Tensión: {'OK' if res.ok_tension else 'TRACCIÓN'}",
            f"Mu_x={res.Mu_x:.1f} kN·m  Mu_y={res.Mu_y:.1f} kN·m",
            f"Dir X: {res.var_x} @ {res.sep_x*100:.0f} cm  "
            f"As_req={res.As_req_x:.2f} cm²/m  As_dis={res.As_dis_x:.2f} cm²/m  "
            f"n={res.n_barras_x}",
            f"Dir Y: {res.var_y} @ {res.sep_y*100:.0f} cm  "
            f"As_req={res.As_req_y:.2f} cm²/m  As_dis={res.As_dis_y:.2f} cm²/m  "
            f"n={res.n_barras_y}",
            f"Cortante X: Vu={res.Vu_x:.1f} kN  φVc={res.phi_Vc_x:.1f} kN  "
            f"{'OK' if res.ok_cx else 'FALLA'}",
            f"Cortante Y: Vu={res.Vu_y:.1f} kN  φVc={res.phi_Vc_y:.1f} kN  "
            f"{'OK' if res.ok_cy else 'FALLA'}",
            f"Punzonado col: Vu={res.Vu_punch_col:.1f} kN  φVc={res.phi_Vc_col:.1f} kN  "
            f"{'OK' if res.ok_punch_col else 'FALLA'}",
            f"Punzonado pil: Vu={res.Vu_punch_pil:.1f} kN  φVc={res.phi_Vc_pil:.1f} kN  "
            f"{'OK' if res.ok_punch_pil else 'FALLA'}",
        ]
        with open(ruta.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
