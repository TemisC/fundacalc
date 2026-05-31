"""
Generador de memoria de cálculo en PDF usando ReportLab.
Produce un informe profesional con:
  - Portada con datos del proyecto
  - Resumen ejecutivo (semáforo de verificaciones)
  - Tablas de resultados
  - Esquemas de la zapata
"""

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER

from core.zapata_aislada import ResultadosZapata

AZUL = colors.HexColor("#1565C0")
VERDE = colors.HexColor("#2e7d32")
ROJO = colors.HexColor("#c62828")
GRIS_CLARO = colors.HexColor("#ECEFF1")


class GeneradorPDF:

    def generar(self, ruta: str, resultado: ResultadosZapata, datos: dict,
                imagen_planta: str = None, imagen_seccion: str = None):
        doc = SimpleDocTemplate(
            ruta,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        estilos = getSampleStyleSheet()
        historia = []

        historia += self._portada(estilos, datos)
        historia.append(PageBreak())
        historia += self._datos_entrada(estilos, datos)
        historia.append(Spacer(1, 0.5*cm))
        if imagen_planta:
            try:
                titulo_planta = Paragraph("2. Vista en Planta", self._estilo_titulo(estilos))
                historia.append(titulo_planta)
                historia.append(Spacer(1, 0.2*cm))
                img = Image(imagen_planta, width=10*cm, height=10*cm)
                historia.append(img)
                historia.append(Spacer(1, 0.4*cm))
            except Exception:
                pass
        if imagen_seccion:
            try:
                historia.append(PageBreak())
                titulo_sec = Paragraph("3. Sección Transversal", self._estilo_titulo(estilos))
                historia.append(titulo_sec)
                historia.append(Spacer(1, 0.2*cm))
                # aspect ratio of the drawing-only figure is 12:5
                img_w = 17*cm
                img_h = img_w / (12 / 5)
                img = Image(imagen_seccion, width=img_w, height=img_h)
                historia.append(img)
                historia.append(Spacer(1, 0.4*cm))
                historia += self._detalles_armadura(estilos, resultado, datos)
            except Exception:
                pass
        historia += self._tabla_resultados(estilos, resultado)
        historia.append(Spacer(1, 0.5*cm))
        historia.append(PageBreak())
        historia += self._verificaciones(estilos, resultado)

        doc.build(historia)

    def _estilo_titulo(self, estilos):
        return ParagraphStyle(
            'Titulo', parent=estilos['Title'],
            fontSize=18, textColor=AZUL, spaceAfter=6,
        )

    def _portada(self, estilos, datos):
        norma = datos.get("norma")
        estilo_logo = ParagraphStyle(
            'Logo', fontSize=36, textColor=AZUL,
            alignment=TA_CENTER, spaceAfter=0, spaceBefore=0, leading=44,
        )
        estilo_sub = ParagraphStyle(
            'Sub', fontSize=13, textColor=colors.grey,
            alignment=TA_CENTER, spaceAfter=0, spaceBefore=10, leading=18,
        )
        estilo_info = ParagraphStyle(
            'Info', fontSize=11, textColor=colors.black,
            spaceAfter=4, spaceBefore=4, leading=16,
        )
        elementos = [
            Spacer(1, 3*cm),
            Paragraph("FundaCalc", estilo_logo),
            Spacer(1, 0.4*cm),
            Paragraph("Memoria de Cálculo — Zapata Aislada", estilo_sub),
            Spacer(1, 0.8*cm),
            HRFlowable(width="100%", thickness=2, color=AZUL),
            Spacer(1, 1.2*cm),
            Paragraph(f"Norma de diseño: <b>{norma}</b>", estilo_info),
            Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_info),
        ]
        return elementos

    def _datos_entrada(self, estilos, datos):
        cargas = datos["cargas"]
        col = datos["columna"]
        suelo = datos["suelo"]
        horm = datos["hormigon"]
        acero = datos["acero"]
        geo = datos["geometria"]
        norma = datos["norma"]
        unidades = datos.get("unidades", {"cargas": "kN", "presiones": "kN/m²"})
        unit_cargas = unidades.get("cargas", "kN")
        unit_presiones = unidades.get("presiones", "kN/m²")

        titulo = Paragraph("1. Datos de Entrada", self._estilo_titulo(estilos))

        tabla_data = [
            ["CARGAS", "", "SUELO", ""],
            [f"Pd (muerta) [{unit_cargas}]", f"{cargas.Pd:.1f}", f"qa [{unit_presiones}]", f"{suelo.qa:.1f}"],
            [f"Pl (viva) [{unit_cargas}]", f"{cargas.Pl:.1f}", "Df (m)", f"{suelo.Df:.2f}"],
            ["Pu (última) [kN]", f"{cargas.Pu:.1f}", "γ suelo (kN/m³)", f"{suelo.gamma_suelo:.1f}"],
            ["COLUMNA", "", "MATERIALES", ""],
            ["Ancho (bx) (m)", f"{col.ancho:.2f}", "fck (MPa)", f"{horm.fck:.1f}"],
            ["Largo (by) (m)", f"{col.largo:.2f}", "fy (MPa)", f"{acero.fy:.1f}"],
            ["Norma", str(norma), "Recubrimiento (cm)", f"{geo.recubrimiento*100:.1f}"],
        ]

        tabla = Table(tabla_data, colWidths=[4*cm, 3.5*cm, 4*cm, 3.5*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 4), (-1, 4), AZUL),
            ('TEXTCOLOR', (0, 4), (-1, 4), colors.white),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, 3), GRIS_CLARO),
            ('BACKGROUND', (0, 5), (-1, -1), GRIS_CLARO),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))

        return [titulo, Spacer(1, 0.3*cm), tabla]

    def _tabla_resultados(self, estilos, res: ResultadosZapata):
        titulo = Paragraph("4. Resultados del Diseño", self._estilo_titulo(estilos))

        data = [
            ["Parámetro", "Valor", "Unidad", "Estado"],
            ["Dimensiones", "", "", ""],
            ["B (largo)", f"{res.B_requerido:.2f}", "m", ""],
            ["L (ancho)", f"{res.L_requerido:.2f}", "m", ""],
            ["h (altura)", f"{res.h_requerido:.2f}", "m", ""],
            ["Verificaciones", "", "", ""],
            ["Presión máx.", f"{res.q_max:.1f}", "kN/m²", "✔ OK" if res.ok_presion else "✘ FALLA"],
            ["Punzonado Vu/φVn", f"{res.relacion_punzonado:.3f}", "—", "✔ OK" if res.ok_punzonado else "✘ FALLA"],
            ["Cortante Vu/φVn", f"{res.relacion_cortante:.3f}", "—", "✔ OK" if res.ok_cortante else "✘ FALLA"],
            ["Armadura", "", "", ""],
            ["As inf. eje X (cara -)", f"{res.As_x_diseno:.2f}", "cm²/m", f"{res.varilla_x} @ {res.separacion_x*100:.0f}cm"],
            ["As inf. eje Y (cara -)", f"{res.As_y_diseno:.2f}", "cm²/m", f"{res.varilla_y} @ {res.separacion_y*100:.0f}cm"],
        ]

        tabla = Table(data, colWidths=[5*cm, 3.5*cm, 3*cm, 4*cm])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ])
        for i, fila in enumerate(data):
            if "FALLA" in str(fila[-1]):
                style.add('TEXTCOLOR', (3, i), (3, i), ROJO)
                style.add('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')
            elif "OK" in str(fila[-1]):
                style.add('TEXTCOLOR', (3, i), (3, i), VERDE)
        tabla.setStyle(style)

        return [titulo, Spacer(1, 0.3*cm), tabla]

    def _detalles_armadura(self, estilos, res: ResultadosZapata, datos: dict):
        PURP = colors.HexColor("#6A1B9A")
        VERDE_OSC = colors.HexColor("#2E7D32")

        # ── Armadura zapata ──────────────────────────────────────────────
        tit = Paragraph("Armadura Inferior — Zapata", ParagraphStyle(
            'ArmTit', parent=estilos['Normal'],
            fontSize=11, textColor=AZUL, fontName='Helvetica-Bold',
            spaceBefore=0, spaceAfter=4,
        ))
        cab = [
            Paragraph('<b>Dirección</b>', estilos['Normal']),
            Paragraph('<b>Varilla</b>',   estilos['Normal']),
            Paragraph('<b>Separación</b>',estilos['Normal']),
            Paragraph('<b>As (cm²/m)</b>',estilos['Normal']),
        ]
        fila_x = [
            Paragraph('<font color="#C62828">Eje X  (paralelo a B)</font>', estilos['Normal']),
            res.varilla_x or '—',
            f'@ {res.separacion_x*100:.0f} cm',
            f'{res.As_x_diseno:.2f}',
        ]
        fila_y = [
            Paragraph('<font color="#6A1B9A">Eje Y  (paralelo a L)</font>', estilos['Normal']),
            res.varilla_y or '—',
            f'@ {res.separacion_y*100:.0f} cm',
            f'{res.As_y_diseno:.2f}',
        ]
        t_zap = Table([cab, fila_x, fila_y], colWidths=[5.5*cm, 3*cm, 3.5*cm, 3*cm])
        t_zap.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), GRIS_CLARO),
            ('GRID',       (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ('ALIGN',      (1, 0), (-1, -1), 'CENTER'),
        ]))

        elementos = [tit, t_zap]

        # ── Pedestal ─────────────────────────────────────────────────────
        ped_res = datos.get('ped_res')
        if ped_res:
            tit_ped = Paragraph("Pedestal", ParagraphStyle(
                'PedTit', parent=estilos['Normal'],
                fontSize=11, textColor=VERDE_OSC, fontName='Helvetica-Bold',
                spaceBefore=8, spaceAfter=4,
            ))
            cab_p = [
                Paragraph('<b>Elemento</b>',  estilos['Normal']),
                Paragraph('<b>Detalle</b>',   estilos['Normal']),
                Paragraph('<b>Cuantía / ld</b>', estilos['Normal']),
            ]
            filas_p = [
                ['Long.', f'{ped_res.n_barras} x {ped_res.varilla_long}',
                 f'As = {ped_res.As_diseno:.2f} cm²'],
                ['Estribos', f'{ped_res.varilla_estribo} @ {ped_res.separacion_estribo*100:.0f} cm', ''],
                ['Esperas', f'{ped_res.n_esperas} x {ped_res.varilla_espera}',
                 f'ld_comp = {ped_res.ld_espera_comp*100:.0f} cm'],
            ]
            t_ped = Table([cab_p] + filas_p, colWidths=[3*cm, 6*cm, 6*cm])
            t_ped.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), VERDE_OSC),
                ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), GRIS_CLARO),
                ('GRID',       (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ]))
            elementos += [Spacer(1, 0.2*cm), tit_ped, t_ped]

        return elementos

    def _verificaciones(self, estilos, res: ResultadosZapata):
        titulo = Paragraph("5. Mensajes de Verificación", self._estilo_titulo(estilos))
        elementos = [titulo, Spacer(1, 0.2*cm)]

        for msg in res.mensajes:
            color = {
                "ok": "#2e7d32", "error": "#c62828",
                "advertencia": "#e65100", "info": "#1565c0"
            }.get(msg["tipo"], "#000000")
            p = Paragraph(
                f'<font color="{color}">{msg["texto"]}</font>',
                estilos['Normal']
            )
            elementos.append(p)
            elementos.append(Spacer(1, 0.1*cm))

        return elementos
