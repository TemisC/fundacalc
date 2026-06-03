/**
 * steelconn_svg.js
 * Primitivas SVG para diagramas de conexiones de acero.
 * Coordenadas en mm (world). Usar SteelSVG.View para convertir a px.
 */
const SteelSVG = (() => {

  // ── Paleta de colores ─────────────────────────────────────────────────────
  const C = {
    col:        { fill: '#1c2e4a', stroke: '#4a90d9', sw: 1.5 },
    colDark:    { fill: '#243752', stroke: '#4a90d9', sw: 1.2 },
    beam:       { fill: '#1e3a5f', stroke: '#60a5fa', sw: 1.0 },
    plate:      { fill: '#1e4080', stroke: '#3b82f6', sw: 1.8 },
    bolt:       { fill: '#0f2744', stroke: '#60a5fa', sw: 1.5 },
    boltHide:   { fill: 'none',    stroke: '#60a5fa', sw: 1.2, dash: '4,2' },
    boltSec:    { fill: '#0f2744', stroke: '#facc15', sw: 1.5 },
    weld:       { fill: '#d97706' },
    dim:        { stroke: '#4b5563', text: '#9ca3af' },
    vu:         { stroke: '#ef4444', fill: '#ef4444' },
    lbl:        { fill: '#6b7280' },
    lblBlue:    { fill: '#60a5fa' },
    lblCol:     { fill: '#4a90d9' },
  }

  // Dimensiones esquemáticas de perfiles (mm) — columna y viga genéricas
  const SCHEMATIC = {
    col_bf: 200, col_tf: 28, col_tw: 10, col_d: 230,
    beam_bf: 150, beam_tf: 12,
    beam_extent: 180,   // cuánto de viga se muestra en alzado
    sec_extent: 100,    // cuánto de viga se muestra en sección
  }

  // ── Transformada world (mm) → screen (px) ────────────────────────────────
  class View {
    constructor(ox, oy, sc) {
      this.ox = ox   // origen px X
      this.oy = oy   // origen px Y (Y world=0)
      this.sc = sc   // px / mm
    }
    x(mm) { return this.ox + mm * this.sc }
    y(mm) { return this.oy - mm * this.sc }  // Y invertida (screen Y↓, world Y↑)
    s(mm) { return Math.abs(mm * this.sc) }
  }

  // ── Primitivas ────────────────────────────────────────────────────────────

  /**
   * Perfil I vertical en alzado (columna).
   * cx, cy = centro world (mm). d=profundidad, bf=ala, tf=esp.ala, tw=esp.alma.
   */
  function iProfileV(v, cx, cy, d, bf, tf, tw, opts = {}) {
    const { fill = C.col.fill, stroke = C.col.stroke, sw = C.col.sw } = opts
    const px = v.x(cx), py = v.y(cy)
    const pd = v.s(d), pbf = v.s(bf), ptf = v.s(tf), ptw = v.s(tw)
    return `
    <rect x="${px - pbf/2}" y="${py - pd/2}" width="${pbf}" height="${ptf}"
          fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>
    <rect x="${px - ptw/2}" y="${py - pd/2 + ptf}" width="${ptw}" height="${pd - 2*ptf}"
          fill="${fill}" stroke="${stroke}" stroke-width="${sw * 0.6}"/>
    <rect x="${px - pbf/2}" y="${py + pd/2 - ptf}" width="${pbf}" height="${ptf}"
          fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`
  }

  /**
   * Perfil I horizontal en alzado (viga). x0→xf = extensión X world.
   * cy = centro Y world. d=peralte, bf=ala, tf=esp.ala, tw=esp.alma.
   */
  function iProfileH(v, x0, xf, cy, d, bf, tf, tw, opts = {}) {
    const { fill = C.beam.fill, stroke = C.beam.stroke, sw = C.beam.sw } = opts
    const px0 = v.x(x0), pxf = v.x(xf), pcy = v.y(cy)
    const pw = pxf - px0
    const pd = v.s(d), ptf = v.s(tf), ptw = v.s(tw)
    return `
    <rect x="${px0}" y="${pcy - pd/2}" width="${pw}" height="${ptf}"
          fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>
    <rect x="${px0}" y="${pcy - pd/2 + ptf}" width="${ptw}" height="${pd - 2*ptf}"
          fill="${fill}" stroke="${stroke}" stroke-width="${sw * 0.8}"/>
    <rect x="${px0}" y="${pcy + pd/2 - ptf}" width="${pw}" height="${ptf}"
          fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`
  }

  /**
   * Perfil I en sección (vista extremo del perfil).
   * cx, cy = centro world. d=peralte (eje Y), bf=ala, tf=esp.ala, tw=esp.alma.
   * Extensión horizontal arbitraria no aplica — es la sección transversal.
   * Para la vista de sección se dibuja como rectángulos en el plano.
   */
  function iProfileSection(v, cx, cy, d, bf, tf, tw, opts = {}) {
    const { fill = C.beam.fill, stroke = C.beam.stroke, sw = C.beam.sw } = opts
    const px = v.x(cx), py = v.y(cy)
    const pd = v.s(d), pbf = v.s(bf), ptf = v.s(tf), ptw = v.s(tw)
    return `
    <rect x="${px - pbf/2}" y="${py - pd/2}" width="${pbf}" height="${ptf}"
          fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>
    <rect x="${px - ptw/2}" y="${py - pd/2 + ptf}" width="${ptw}" height="${pd - 2*ptf}"
          fill="${fill}" stroke="${stroke}" stroke-width="${sw * 0.7}"/>
    <rect x="${px - pbf/2}" y="${py + pd/2 - ptf}" width="${pbf}" height="${ptf}"
          fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`
  }

  /**
   * Rectángulo de plancha.
   * x_izq = borde izquierdo world X. y_bot = borde inferior world Y. w, h en mm.
   */
  function plateRect(v, x_izq, y_bot, w, h, opts = {}) {
    const { fill = C.plate.fill, stroke = C.plate.stroke, sw = C.plate.sw, dash = '' } = opts
    const px = v.x(x_izq), py = v.y(y_bot + h)
    const pw = v.s(w), ph = v.s(h)
    const da = dash ? `stroke-dasharray="${dash}"` : ''
    return `<rect x="${px}" y="${py}" width="${pw}" height="${ph}"
                  fill="${fill}" stroke="${stroke}" stroke-width="${sw}" rx="1" ${da}/>`
  }

  /**
   * Perno en alzado (círculo + cruceta). cx, cy world. db = diámetro mm.
   * opts.hidden = true → líneas de trazo (perno oculto)
   */
  function bolt(v, cx, cy, db, opts = {}) {
    const hidden = opts.hidden || false
    const section = opts.section || false
    let st, fill, sw, da
    if (section)     { fill = C.boltSec.fill; st = C.boltSec.stroke; sw = C.boltSec.sw; da = '' }
    else if (hidden) { fill = C.boltHide.fill; st = C.boltHide.stroke; sw = C.boltHide.sw; da = `stroke-dasharray="${C.boltHide.dash}"` }
    else             { fill = C.bolt.fill; st = C.bolt.stroke; sw = C.bolt.sw; da = '' }
    const px = v.x(cx), py = v.y(cy), r = v.s(db / 2)
    return `
    <circle cx="${px}" cy="${py}" r="${r}" fill="${fill}"
            stroke="${st}" stroke-width="${sw}" ${da}/>
    <line x1="${px - r + 1}" y1="${py}" x2="${px + r - 1}" y2="${py}"
          stroke="${st}" stroke-width="${sw * 0.55}" ${da}/>
    <line x1="${px}" y1="${py - r + 1}" x2="${px}" y2="${py + r - 1}"
          stroke="${st}" stroke-width="${sw * 0.55}" ${da}/>`
  }

  /**
   * Triángulo de soldadura filete.
   * x, y = punto de referencia world (cara donde se suelda). size = cateto en mm.
   * dir: 'left'|'right' (hacia qué lado apunta el triángulo).
   */
  function weldTriangle(v, x, y, size, dir = 'right', opts = {}) {
    const { fill = C.weld.fill, opacity = 0.9 } = opts
    const px = v.x(x), py = v.y(y), ps = v.s(size)
    const pts = dir === 'left'
      ? `${px},${py - ps/2} ${px},${py + ps/2} ${px - ps},${py}`
      : `${px},${py - ps/2} ${px},${py + ps/2} ${px + ps},${py}`
    return `<polygon points="${pts}" fill="${fill}" opacity="${opacity}"/>`
  }

  /**
   * Cota vertical.
   * x_ref = X world de referencia. y1, y2 = extremos Y world.
   * side: 'left'|'right'. off_mm = distancia del elemento a la línea de cota.
   */
  function dimV(v, x_ref, y1, y2, label, side = 'left', off_mm = 10) {
    const px = v.x(x_ref)
    const py1 = v.y(y1), py2 = v.y(y2)
    const off = side === 'left' ? -v.s(off_mm) : v.s(off_mm)
    const lx = px + off
    const midy = (py1 + py2) / 2
    const anchor = side === 'left' ? 'end' : 'start'
    const tx = lx + (side === 'left' ? -3 : 3)
    const { stroke, text } = C.dim
    return `
    <line x1="${px}" y1="${py1}" x2="${lx - 2}" y2="${py1}" stroke="${stroke}" stroke-width="0.7"/>
    <line x1="${px}" y1="${py2}" x2="${lx - 2}" y2="${py2}" stroke="${stroke}" stroke-width="0.7"/>
    <line x1="${lx}" y1="${py1}" x2="${lx}" y2="${py2}" stroke="${stroke}" stroke-width="0.7"/>
    <text x="${tx}" y="${midy + 4}" fill="${text}" font-size="9" text-anchor="${anchor}"
          transform="rotate(-90,${tx},${midy + 4})">${label}</text>`
  }

  /**
   * Cota horizontal.
   * x1, x2 = extremos X world. y_ref = Y world de referencia.
   * side: 'bottom'|'top'. off_mm = offset desde el elemento.
   */
  function dimH(v, x1, x2, y_ref, label, side = 'bottom', off_mm = 10) {
    const px1 = v.x(x1), px2 = v.x(x2), py = v.y(y_ref)
    const off = side === 'bottom' ? v.s(off_mm) : -v.s(off_mm)
    const ly = py + off
    const midx = (px1 + px2) / 2
    const ty = side === 'bottom' ? ly + 12 : ly - 4
    const { stroke, text } = C.dim
    return `
    <line x1="${px1}" y1="${py}" x2="${px1}" y2="${ly + 2}" stroke="${stroke}" stroke-width="0.7"/>
    <line x1="${px2}" y1="${py}" x2="${px2}" y2="${ly + 2}" stroke="${stroke}" stroke-width="0.7"/>
    <line x1="${px1}" y1="${ly}" x2="${px2}" y2="${ly}" stroke="${stroke}" stroke-width="0.7"/>
    <text x="${midx}" y="${ty}" fill="${text}" font-size="9" text-anchor="middle">${label}</text>`
  }

  /**
   * Flecha de carga cortante Vu (vertical, apunta hacia abajo).
   * x = posición X world. y_tip = punta (world). y_tail = cola (world, más arriba).
   */
  function vuArrow(v, x, y_tip, y_tail, label) {
    const { stroke, fill } = C.vu
    const px = v.x(x), pty = v.y(y_tip), ptail = v.y(y_tail)
    return `
    <defs>
      <marker id="arr-vu" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
        <path d="M0,0 L6,3 L0,6 Z" fill="${fill}"/>
      </marker>
    </defs>
    <line x1="${px}" y1="${ptail}" x2="${px}" y2="${pty + 2}"
          stroke="${stroke}" stroke-width="2.5" marker-end="url(#arr-vu)"/>
    <text x="${px}" y="${ptail - 4}" fill="${fill}" font-size="10"
          text-anchor="middle" font-weight="bold">${label}</text>`
  }

  /** Texto de etiqueta. x, y world. opts: fill, fs, anchor, bold. */
  function textLabel(v, x, y, text, opts = {}) {
    const { fill = C.lbl.fill, fs = 9, anchor = 'middle', bold = false } = opts
    const fw = bold ? 'font-weight="bold"' : ''
    return `<text x="${v.x(x)}" y="${v.y(y)}" fill="${fill}" font-size="${fs}"
                  text-anchor="${anchor}" ${fw}>${text}</text>`
  }

  /** Título de vista (coordenadas px directas). */
  function viewTitle(cx_px, y_px, title, sub = '') {
    return `
    <text x="${cx_px}" y="${y_px}" fill="#6b7280" font-size="10"
          text-anchor="middle" letter-spacing="1">${title}</text>
    ${sub ? `<text x="${cx_px}" y="${y_px + 12}" fill="#4b5563" font-size="8" text-anchor="middle">${sub}</text>` : ''}`
  }

  /** Línea divisora vertical entre vistas (px directas). */
  function divider(x_px, y1_px, y2_px) {
    return `<line x1="${x_px}" y1="${y1_px}" x2="${x_px}" y2="${y2_px}"
                  stroke="#21262d" stroke-width="1" stroke-dasharray="4,4"/>`
  }

  /**
   * Leyenda de resultado (px directas).
   * info: { ok, Lp, n, db, tp, bp, relacion_max, critica, boltType, steel }
   */
  function resultLegend(x_px, y_px, w_px, h_px, info) {
    const mid = x_px + w_px / 2
    if (info.ok === null) {
      return `
      <rect x="${x_px}" y="${y_px}" width="${w_px}" height="${h_px}" rx="6" fill="#161b22" stroke="#374151"/>
      <text x="${mid}" y="${y_px + 17}" fill="#6b7280" font-size="11"
            text-anchor="middle" font-style="italic">MODO ESQUEMA — geometría solamente</text>
      <text x="${mid}" y="${y_px + 31}" fill="#484f58" font-size="10" text-anchor="middle">
        Lp = ${info.Lp.toFixed(0)}mm  ·  n = ${info.n} pernos Ø${info.db}mm  ·  tp = ${info.tp}×${info.bp}mm
      </text>
      <text x="${mid}" y="${y_px + 45}" fill="#374151" font-size="9" text-anchor="middle">
        ▶ Presiona Calcular para verificar la resistencia
      </text>`
    }
    const rc = info.ok ? '#22c55e' : '#ef4444'
    return `
    <rect x="${x_px}" y="${y_px}" width="${w_px}" height="${h_px}" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="${mid}" y="${y_px + 18}" fill="#e6edf3" font-size="11"
          text-anchor="middle" font-weight="bold">
      ${info.ok ? '✔ CONEXIÓN CONFORME' : '✘ CONEXIÓN NO CONFORME'}
    </text>
    <text x="${mid}" y="${y_px + 32}" fill="${rc}" font-size="10" text-anchor="middle">
      D/C máx = ${info.relacion_max}  |  Crítica: ${info.critica}
    </text>
    <text x="${mid}" y="${y_px + 46}" fill="#484f58" font-size="9" text-anchor="middle">
      ${info.n} pernos Ø${info.db}mm ${info.boltType} — Plancha ${info.tp}×${info.bp}mm ${info.steel}
    </text>`
  }

  /**
   * Calcula escala para que la geometría del alzado quepa en el viewport.
   * worldW, worldH en mm. availW, availH en px.
   */
  function autoScale(worldW, worldH, availW, availH) {
    return Math.min(availW / worldW, availH / worldH)
  }

  /**
   * Contorno de elemento OCULTO (detrás de otro elemento).
   * Dibuja los bordes del rectángulo que quedan tapados con línea de trazo.
   * Regla de dibujo técnico: todo elemento que se extiende detrás de otro
   * debe mostrarse con trazos hasta su punto de finalización real.
   *
   * x_ini, x_fin = rango X world del tramo oculto.
   * y_bot, y_top = extremos Y world del elemento.
   * Se dibujan: borde superior, borde inferior y borde derecho (x_fin).
   */
  function hiddenOutline(v, x_ini, x_fin, y_bot, y_top, opts = {}) {
    const { stroke = '#60a5fa', sw = 1.2, dash = '5,3' } = opts
    const da = `stroke="${stroke}" stroke-width="${sw}" stroke-dasharray="${dash}"`
    return `
    <line x1="${v.x(x_ini)}" y1="${v.y(y_top)}" x2="${v.x(x_fin)}" y2="${v.y(y_top)}" ${da}/>
    <line x1="${v.x(x_ini)}" y1="${v.y(y_bot)}" x2="${v.x(x_fin)}" y2="${v.y(y_bot)}" ${da}/>
    <line x1="${v.x(x_fin)}" y1="${v.y(y_bot)}" x2="${v.x(x_fin)}" y2="${v.y(y_top)}" ${da}/>`
  }

  return {
    View, C, SCHEMATIC, autoScale,
    iProfileV, iProfileH, iProfileSection,
    plateRect, bolt, weldTriangle,
    dimV, dimH, vuArrow,
    textLabel, viewTitle, divider, resultLegend,
    hiddenOutline,
  }
})()
