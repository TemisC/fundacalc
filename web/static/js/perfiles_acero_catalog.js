/**
 * perfiles_acero_catalog.js
 * Catálogo de perfiles estructurales W (Wide Flange) — AISC 16th Edition
 * Dimensiones en mm. Peso en kg/m.
 */
const PERFILES_W = (() => {

  // ── Datos (d, bf, tf, tw en mm — peso en kg/m) ──────────────────────────
  const VIGAS = [
    // W8
    { id:'W8x18',   label:'W8×18',   d:207, bf:133, tf:11.0, tw:5.8,  peso:18  },
    { id:'W8x24',   label:'W8×24',   d:210, bf:134, tf:14.9, tw:6.9,  peso:24  },
    // W10
    { id:'W10x22',  label:'W10×22',  d:259, bf:146, tf:11.0, tw:5.8,  peso:22  },
    { id:'W10x33',  label:'W10×33',  d:262, bf:148, tf:17.0, tw:7.4,  peso:33  },
    { id:'W10x39',  label:'W10×39',  d:269, bf:203, tf:14.6, tw:8.0,  peso:39  },
    // W12
    { id:'W12x26',  label:'W12×26',  d:311, bf:165, tf:9.7,  tw:5.8,  peso:26  },
    { id:'W12x35',  label:'W12×35',  d:318, bf:167, tf:14.6, tw:7.6,  peso:35  },
    { id:'W12x40',  label:'W12×40',  d:312, bf:203, tf:13.2, tw:7.6,  peso:40  },
    { id:'W12x50',  label:'W12×50',  d:318, bf:205, tf:16.3, tw:9.0,  peso:50  },
    // W14
    { id:'W14x22',  label:'W14×22',  d:349, bf:127, tf:8.5,  tw:5.8,  peso:22  },
    { id:'W14x30',  label:'W14×30',  d:352, bf:171, tf:9.8,  tw:6.9,  peso:30  },
    { id:'W14x38',  label:'W14×38',  d:360, bf:171, tf:13.1, tw:7.9,  peso:38  },
    { id:'W14x48',  label:'W14×48',  d:363, bf:203, tf:14.4, tw:9.1,  peso:48  },
    // W16
    { id:'W16x26',  label:'W16×26',  d:399, bf:140, tf:8.8,  tw:6.4,  peso:26  },
    { id:'W16x36',  label:'W16×36',  d:403, bf:178, tf:11.0, tw:7.5,  peso:36  },
    { id:'W16x45',  label:'W16×45',  d:409, bf:178, tf:14.0, tw:8.6,  peso:45  },
    { id:'W16x57',  label:'W16×57',  d:417, bf:181, tf:18.0, tw:10.9, peso:57  },
    // W18
    { id:'W18x35',  label:'W18×35',  d:450, bf:152, tf:10.8, tw:7.6,  peso:35  },
    { id:'W18x46',  label:'W18×46',  d:455, bf:153, tf:14.5, tw:9.1,  peso:46  },
    { id:'W18x55',  label:'W18×55',  d:460, bf:191, tf:12.8, tw:7.9,  peso:55  },
    { id:'W18x65',  label:'W18×65',  d:466, bf:191, tf:15.2, tw:9.1,  peso:65  },
    { id:'W18x76',  label:'W18×76',  d:472, bf:194, tf:17.6, tw:11.2, peso:76  },
    { id:'W18x97',  label:'W18×97',  d:480, bf:214, tf:19.1, tw:11.2, peso:97  },
    // W21
    { id:'W21x44',  label:'W21×44',  d:525, bf:165, tf:11.4, tw:8.9,  peso:44  },
    { id:'W21x57',  label:'W21×57',  d:535, bf:166, tf:16.5, tw:9.9,  peso:57  },
    { id:'W21x68',  label:'W21×68',  d:537, bf:210, tf:14.0, tw:8.9,  peso:68  },
    { id:'W21x83',  label:'W21×83',  d:546, bf:214, tf:17.0, tw:10.9, peso:83  },
    // W24
    { id:'W24x55',  label:'W24×55',  d:599, bf:178, tf:12.8, tw:9.7,  peso:55  },
    { id:'W24x68',  label:'W24×68',  d:608, bf:228, tf:14.0, tw:10.5, peso:68  },
    { id:'W24x84',  label:'W24×84',  d:612, bf:229, tf:15.9, tw:9.8,  peso:84  },
    { id:'W24x104', label:'W24×104', d:620, bf:324, tf:16.3, tw:12.7, peso:104 },
    // W27
    { id:'W27x84',  label:'W27×84',  d:678, bf:254, tf:15.2, tw:9.9,  peso:84  },
    { id:'W27x94',  label:'W27×94',  d:688, bf:254, tf:15.2, tw:9.9,  peso:94  },
    { id:'W27x114', label:'W27×114', d:699, bf:259, tf:19.8, tw:13.1, peso:114 },
    // W30
    { id:'W30x90',  label:'W30×90',  d:756, bf:267, tf:14.5, tw:9.5,  peso:90  },
    { id:'W30x108', label:'W30×108', d:762, bf:267, tf:17.3, tw:10.9, peso:108 },
    { id:'W30x124', label:'W30×124', d:771, bf:267, tf:20.1, tw:12.7, peso:124 },
  ]

  const COLUMNAS = [
    // W6
    { id:'W6x15',   label:'W6×15',   d:152, bf:152, tf:9.7,  tw:5.8,  peso:15  },
    { id:'W6x20',   label:'W6×20',   d:157, bf:152, tf:13.2, tw:6.6,  peso:20  },
    { id:'W6x25',   label:'W6×25',   d:162, bf:162, tf:14.0, tw:8.1,  peso:25  },
    // W8
    { id:'W8x24',   label:'W8×24',   d:210, bf:207, tf:14.9, tw:6.9,  peso:24  },
    { id:'W8x31',   label:'W8×31',   d:210, bf:203, tf:11.0, tw:7.2,  peso:31  },
    { id:'W8x40',   label:'W8×40',   d:213, bf:205, tf:20.0, tw:9.0,  peso:40  },
    { id:'W8x48',   label:'W8×48',   d:216, bf:206, tf:23.6, tw:10.2, peso:48  },
    // W10
    { id:'W10x33',  label:'W10×33',  d:262, bf:201, tf:14.4, tw:7.9,  peso:33  },
    { id:'W10x49',  label:'W10×49',  d:254, bf:254, tf:14.0, tw:9.0,  peso:49  },
    { id:'W10x60',  label:'W10×60',  d:260, bf:256, tf:17.3, tw:10.7, peso:60  },
    { id:'W10x77',  label:'W10×77',  d:266, bf:258, tf:22.3, tw:13.3, peso:77  },
    // W12
    { id:'W12x40',  label:'W12×40',  d:303, bf:203, tf:13.1, tw:7.6,  peso:40  },
    { id:'W12x53',  label:'W12×53',  d:311, bf:254, tf:15.2, tw:9.0,  peso:53  },
    { id:'W12x65',  label:'W12×65',  d:318, bf:305, tf:15.4, tw:9.9,  peso:65  },
    { id:'W12x87',  label:'W12×87',  d:327, bf:307, tf:20.6, tw:13.1, peso:87  },
    // W14
    { id:'W14x48',  label:'W14×48',  d:355, bf:205, tf:14.2, tw:8.9,  peso:48  },
    { id:'W14x61',  label:'W14×61',  d:360, bf:254, tf:17.3, tw:9.5,  peso:61  },
    { id:'W14x82',  label:'W14×82',  d:363, bf:257, tf:21.7, tw:12.9, peso:82  },
    { id:'W14x99',  label:'W14×99',  d:368, bf:259, tf:25.7, tw:14.5, peso:99  },
    { id:'W14x109', label:'W14×109', d:371, bf:259, tf:28.4, tw:14.8, peso:109 },
    { id:'W14x132', label:'W14×132', d:378, bf:374, tf:36.1, tw:21.1, peso:132 },
    { id:'W14x145', label:'W14×145', d:381, bf:394, tf:38.7, tw:22.2, peso:145 },
    { id:'W14x176', label:'W14×176', d:389, bf:395, tf:47.7, tw:26.2, peso:176 },
  ]

  // ── Helpers ──────────────────────────────────────────────────────────────

  /** Devuelve todos los perfiles de viga como array */
  function getVigas() { return VIGAS }

  /** Devuelve todos los perfiles de columna como array */
  function getColumnas() { return COLUMNAS }

  /** Busca un perfil por id en la lista combinada */
  function buscar(id) {
    return [...VIGAS, ...COLUMNAS].find(p => p.id === id) || null
  }

  /**
   * Genera las <option> HTML para un <select>.
   * grupo: 'vigas' | 'columnas'
   * selectedId: id preseleccionado (opcional)
   */
  function renderOptions(grupo, selectedId = '') {
    const lista = grupo === 'vigas' ? VIGAS : COLUMNAS
    return lista.map(p =>
      `<option value="${p.id}" ${p.id === selectedId ? 'selected' : ''}>${p.label}</option>`
    ).join('')
  }

  /** Texto de resumen de un perfil para mostrar en la UI */
  function resumen(perfil) {
    if (!perfil) return '—'
    return `d=${perfil.d}mm  bf=${perfil.bf}mm  tf=${perfil.tf}mm  tw=${perfil.tw}mm`
  }

  return { getVigas, getColumnas, buscar, renderOptions, resumen }
})()
