# SteelConn — Documento Maestro de Desarrollo
> App **Web** para el Cálculo de Conexiones en Estructuras de Acero  
> Uniones apernadas · Uniones soldadas · Placas base · Nodos de armadura  
> Stack: HTML5 · CSS3 · JavaScript ES6+ · SVG · jsPDF  
> IDE: Visual Studio Code  
> Versión del documento: 1.0

---

## Índice

1. [Visión y Alcance](#1-visión-y-alcance)
2. [Normas y Referencias Técnicas](#2-normas-y-referencias-técnicas)
3. [Fundamentos Técnicos — Teoría de Conexiones](#3-fundamentos-técnicos--teoría-de-conexiones)
4. [Estructura de Carpetas](#4-estructura-de-carpetas)
5. [Módulo 1 — Unión Apernada a Corte (Shear Tab)](#5-módulo-1--unión-apernada-a-corte-shear-tab)
6. [Módulo 2 — Unión con Plancha de Extremo (End Plate)](#6-módulo-2--unión-con-plancha-de-extremo-end-plate)
7. [Módulo 3 — Placa Base de Columna](#7-módulo-3--placa-base-de-columna)
8. [Módulo 4 — Soldadura en Filete](#8-módulo-4--soldadura-en-filete)
9. [Módulo 5 — Soldadura en Ranura CJP y PJP](#9-módulo-5--soldadura-en-ranura-cjp-y-pjp)
10. [Módulo 6 — Unión Viga-Columna Momento Resistente](#10-módulo-6--unión-viga-columna-momento-resistente)
11. [Módulo 7 — Nodo de Armadura (Gusset Plate)](#11-módulo-7--nodo-de-armadura-gusset-plate)
12. [Base de Datos de Perfiles y Materiales](#12-base-de-datos-de-perfiles-y-materiales)
13. [Motor de Normas — Factores por País](#13-motor-de-normas--factores-por-país)
14. [Pantalla Principal — UI Home](#14-pantalla-principal--ui-home)
15. [Sistema de Verificaciones — Semáforo](#15-sistema-de-verificaciones--semáforo)
16. [Exportación PDF y DXF](#16-exportación-pdf-y-dxf)
17. [Casos de Prueba con Valores Reales](#17-casos-de-prueba-con-valores-reales)
18. [Roadmap — Módulos Futuros](#18-roadmap--módulos-futuros)

---

## 1. Visión y Alcance

### Objetivo
Aplicación web para el diseño y verificación de conexiones en estructuras de acero, siguiendo normas internacionales vigentes (AISC, CIRSOC, EC3, NSR-10, NCh). Produce memoria de cálculo en PDF y plano en DXF.

### Filosofía de diseño
- Cada verificación muestra claramente: **Demanda / Capacidad ≤ 1.0**
- Si la relación supera 1.0 → la verificación falla y se indica qué cambiar
- El usuario ingresa las fuerzas de diseño y la geometría; la app hace todas las verificaciones
- Compatible con el método LRFD (factores de carga y resistencia) y ASD (tensiones admisibles)

### Módulos planificados

| # | Módulo | Tipo | Estado |
|---|---|---|---|
| 1 | Unión apernada a corte — shear tab | Apernada | ✅ Módulo 1 |
| 2 | Unión con plancha de extremo — end plate | Apernada | ✅ Módulo 2 |
| 3 | Placa base de columna | Apernada + soldada | ✅ Módulo 3 |
| 4 | Soldadura en filete | Soldada | ✅ Módulo 4 |
| 5 | Soldadura en ranura CJP y PJP | Soldada | ✅ Módulo 5 |
| 6 | Unión viga-columna momento resistente | Soldada | 🔲 Módulo 6 |
| 7 | Nodo de armadura — gusset plate | Mixta | 🔲 Módulo 7 |
| 8 | Unión con cartela — haunch | Soldada | 🔲 Módulo 8 |
| 9 | Unión columna-columna empalme | Apernada/sold. | 🔲 Módulo 9 |
| 10 | Ángulo de asiento — seat angle | Apernada | 🔲 Módulo 10 |

---

## 2. Normas y Referencias Técnicas

Esta sección es el núcleo del documento. Toda verificación está referenciada a un artículo específico de la norma correspondiente.

---

### 2.1 AISC 360-22 — Specification for Structural Steel Buildings (USA / Internacional)

La norma base más completa. Usada directamente en USA y como referencia en toda Latinoamérica.

**Capítulos relevantes para conexiones:**

| Capítulo | Tema | Artículos clave |
|---|---|---|
| B | Diseño general | B3 (LRFD vs ASD), B4 (secciones compactas) |
| D | Miembros en tracción | D1, D2, D3 |
| E | Miembros en compresión | E1, E2, E3, E7 |
| F | Miembros en flexión | F1, F2, F13 |
| G | Cortante en vigas | G1, G2 |
| J | Diseño de conexiones | **J1 a J7 — SECCIÓN PRINCIPAL** |
| L | Serviceability | L3 |

**Capítulo J — Diseño de conexiones (detalle completo):**

```
J1  — Disposiciones generales
  J1.1  Diseño de la conexión completa
  J1.2  Cargas y fuerzas de diseño
  J1.3  Diseño para fuerzas de tracción y compresión
  J1.4  Limitaciones en conexiones de alta resistencia
  J1.5  Soldaduras y pernos combinados
  J1.6  Conexiones de empalme de alas
  J1.7  Conexiones en ángulos
  J1.8  Distancias al borde y espaciado
  J1.9  Longitud máxima de conexión

J2  — Soldaduras
  J2.1  Tipos de soldadura
  J2.2  Tamaño y longitud de soldaduras en filete
        J2.2a Tamaño mínimo
        J2.2b Tamaño máximo
        J2.2c Longitud mínima
        J2.2d Longitud de retorno
        J2.2e Soldaduras en ranura
  J2.3  Áreas efectivas
        J2.3a Soldadura en filete — garganta efectiva = 0.707 × tamaño
        J2.3b Soldadura CJP — garganta = espesor completo
        J2.3c Soldadura PJP — garganta efectiva según preparación
  J2.4  Resistencia de diseño de soldaduras en filete
        φRn = φ × 0.60 × FEXX × Aw × (1.0 + 0.50 sin^1.5 θ)
        φ = 0.75 (LRFD)
        FEXX = resistencia nominal del electrodo [MPa o ksi]
        Aw = área efectiva de la garganta [mm² o in²]
        θ = ángulo de la carga con respecto al eje longitudinal
  J2.5  Resistencia de soldaduras en ranura
        CJP: igual al metal base
        PJP en tracción perpendicular: φ = 0.80, Rn = 0.60 FEXX × Aw
        PJP en compresión: φ = 0.90
        PJP en corte: φ = 0.75, Rn = 0.60 FEXX × Aw

J3  — Pernos y partes roscadas
  J3.1  Pernos de alta resistencia
  J3.2  Instalación
  J3.3  Tamaño de agujeros
        Estándar: dh = db + 1/16" (1.6mm)
        Sobredimensionado: dh = db + 5/16" (8mm) máx
        Ranura corta: db + 5/16" × db + 5/8"
  J3.4  Distancias mínimas al borde
        Tabla J3.4: según diámetro del perno
  J3.5  Distancias máximas al borde y espaciado
        Espaciado mínimo: 2.67 db (preferible 3 db)
        Borde máximo: 12t ≤ 150mm
  J3.6  Resistencia de diseño al corte de pernos
        φRn = φ × Fnv × Ab
        φ = 0.75 (LRFD)
        Fnv: Tabla J3.2
          A307: Fnv = 165 MPa (24 ksi) — un plano de corte
          A325 (ASTM F3125 Gr.A325): Fnv = 372 MPa (54 ksi) sin hilos, 310 MPa con hilos
          A490 (ASTM F3125 Gr.A490): Fnv = 457 MPa (66 ksi) sin hilos, 372 MPa con hilos
        Ab = área nominal del perno = π × db² / 4
  J3.7  Resistencia combinada corte + tracción
        (frv/φFnv)² + (frt/φFnt)² ≤ 1.0
  J3.8  Pernos pretensados — conexiones de deslizamiento crítico
        φRn = φ × μ × Du × hf × Tb × ns
        φ = 1.00 (superficies clase A) o 0.85 (clase B)
        μ: coeficiente de deslizamiento (0.35 clase A, 0.50 clase B)
        Du = 1.13 (factor de pretensado)
        Tb: pretensado mínimo (Tabla J3.1)
  J3.9  Resistencia de diseño al aplastamiento (bearing)
        φRn = φ × 1.2 × Lc × t × Fu ≤ φ × 2.4 × db × t × Fu
        φ = 0.75
        Lc = distancia libre al borde o al perno adyacente [mm]
        t = espesor de la plancha [mm]
        Fu = resistencia a la ruptura del material [MPa]
  J3.10 Resistencia de diseño al desgarro (tearout)
        φRn = φ × 1.2 × Lc × t × Fu
  J3.11 Distribución de la fuerza en conexiones largas

J4  — Elementos afectados en las conexiones
  J4.1  Tracción en la sección bruta
        φRn = φ × Fy × Ag
        φ = 0.90
  J4.2  Tracción en la sección neta
        φRn = φ × Fu × An × U (factor de reducción de corte)
        φ = 0.75
  J4.3  Desgarro en bloque (Block Shear)
        φRn = φ × (0.60 Fu Anv + Ubs Fu Ant)
        ≤    φ × (0.60 Fy Agv + Ubs Fu Ant)
        φ = 0.75
        Ubs = 1.0 (tracción uniforme) o 0.50 (no uniforme)
        Anv = área neta en cizalladura
        Ant = área neta en tracción
        Agv = área bruta en cizalladura
  J4.4  Corte en sección bruta y neta
        Bruta: φRn = φ × 0.60 Fy Agv, φ = 1.00
        Neta:  φRn = φ × 0.60 Fu Anv, φ = 0.75
  J4.5  Compresión
  J4.6  Flexión

J5  — Conexiones de empalme de alas
J6  — Conexiones de alas y almas
J7  — Rellenado de espacios (fill plates)
```

**Propiedades de materiales — AISC (aceros ASTM):**

| Acero | Fy (MPa) | Fu (MPa) | Uso típico |
|---|---|---|---|
| ASTM A36 | 250 | 400 | Perfiles, planchas generales |
| ASTM A572 Gr.50 | 345 | 450 | Perfiles estructurales |
| ASTM A572 Gr.60 | 415 | 520 | Perfiles de alta resistencia |
| ASTM A992 | 345 | 450 | Perfiles W (vigas y columnas) |
| ASTM A500 Gr.B | 317 | 400 | Tubos estructurales HSS |
| ASTM A500 Gr.C | 345 | 427 | Tubos HSS alta resistencia |
| ASTM A53 Gr.B | 240 | 415 | Tubos circulares (pipe) |

**Propiedades de pernos — AISC:**

| Perno | Fnt (MPa) | Fnv (MPa) | Tb mín (kN) |
|---|---|---|---|
| A307 | 310 | 165 | No pretensado |
| A325 (F3125 A325) — M16 | 620 | 372 | 71 |
| A325 (F3125 A325) — M20 | 620 | 372 | 110 |
| A325 (F3125 A325) — M22 | 620 | 372 | 134 |
| A325 (F3125 A325) — M24 | 620 | 372 | 157 |
| A490 (F3125 A490) — M20 | 780 | 457 | 138 |
| A490 (F3125 A490) — M22 | 780 | 457 | 168 |
| A490 (F3125 A490) — M24 | 780 | 457 | 196 |

**Electrodos de soldadura — AWS:**

| Electrodo | FEXX (MPa) | FEXX (ksi) | Proceso |
|---|---|---|---|
| E6010 / E6013 | 414 | 60 | SMAW |
| E7010 / E7018 | 482 | 70 | SMAW — más común |
| E71T-1 | 482 | 70 | FCAW |
| E80XX | 552 | 80 | SMAW alta resistencia |
| ER70S-X | 482 | 70 | GMAW/GTAW |

---

### 2.2 AISC 341-22 — Seismic Provisions for Structural Steel Buildings

Para conexiones en zonas sísmicas. Complementa el AISC 360.

**Requisitos adicionales clave:**

```
E2  — Sistemas de marcos especiales a momento (SMF)
  E2.4  Conexiones viga-columna precalificadas
        → referencia a AISC 358-22

E3  — Marcos intermedios a momento (IMF)

E6  — Marcos arriostrados excéntricos (EBF)

F1  — Marcos arriostrados concéntricos especiales (SCBF)
  F1.6  Conexiones en las barras de arriostre
        → Pu ≥ 1.1 Ry Fy Ag (tracción esperada)
        → Pu ≥ 0.3 × φcPn (compresión mínima)

F2  — Marcos arriostrados concéntricos ordinarios (OCBF)
```

**AISC 358-22 — Conexiones precalificadas para SMF:**

```
Conexiones precalificadas disponibles:
  WUF-W    — Unreinforced Flange-Welded Web
  BFP      — Bolted Flange Plate
  CFP      — Cover-Flated Flange Plate
  DST      — Double Split Tee
  BSEP     — Bolted Stiffened End Plate (4 y 8 pernos)
  BUEP     — Bolted Unstiffened End Plate
  RBS      — Reduced Beam Section (dog-bone)
  Kaiser BHP — Kaiser Bolted Bracket
```

---

### 2.3 AISC Design Guides — Guías de diseño específicas

| Guía | Título | Módulo de la app |
|---|---|---|
| DG 1 (3ª ed.) | Column Base Plates | Módulo 3 — Placa base |
| DG 2 | Steel and Composite Beams with Web Openings | — |
| DG 3 | Serviceability Design | — |
| DG 4 | Extended End-Plate Moment Connections | Módulo 2 — End plate |
| DG 9 | Torsional Analysis of Structural Steel Members | Módulo 4 |
| DG 10 | Erection Bracing of Low-Rise Structural Steel | — |
| DG 16 | Flush and Extended Multiple-Row Moment End-Plate | Módulo 2 |
| DG 21 | Welded Connections | Módulos 4, 5, 6 |
| DG 24 | Hollow Structural Section Connections | Módulo 7 futuro |
| DG 29 | Vertical Bracing Connections | Módulo 7 |
| DG 30 | Design Guide for Wide-Flange Column Stiffening | Módulo 6 |

---

### 2.4 CIRSOC 301-2005 — Argentina

Reglamento Argentino de Estructuras de Acero para Edificios.
Basado en AISC LRFD 1994 con adaptaciones locales.

**Materiales en Argentina:**

| Acero | Denominación | Fy (MPa) | Fu (MPa) |
|---|---|---|---|
| F-24 (IRAM IAS U-500-2503) | Equivalente A36 | 235 | 370 |
| F-36 | Alta resistencia | 355 | 510 |
| Tubos sin costura (IRAM 2502) | — | 250 | 390 |

**Pernos en Argentina:**

| Perno | Norma | Equivalencia |
|---|---|---|
| Grado 5.6 | ISO 898-1 | Similar A307 |
| Grado 8.8 | ISO 898-1 | Similar A325 |
| Grado 10.9 | ISO 898-1 | Similar A490 |

**Diferencias clave CIRSOC vs AISC:**
- CIRSOC usa el sistema métrico (mm, kN, MPa) en forma nativa
- Los factores φ son equivalentes al AISC 360
- Las tablas de pernos usan diámetros métricos (M16, M20, M22, M24, M27, M30)
- El espaciado mínimo entre pernos: 3 db (vs 2.67 db en AISC)

**Artículos CIRSOC relevantes:**

```
Cap. 9  — Conexiones
  9.1   Diseño de conexiones (principios generales)
  9.2   Pernos y partes roscadas
    9.2.1  Tipos de pernos
    9.2.2  Resistencia al corte
    9.2.3  Resistencia al aplastamiento
    9.2.4  Resistencia combinada corte+tracción
    9.2.5  Pernos de alta resistencia pretensados
  9.3   Soldaduras
    9.3.1  Generalidades
    9.3.2  Soldadura en filete
    9.3.3  Soldadura en ranura
    9.3.4  Precauciones ante la rotura laminar
  9.4   Elementos en las conexiones
    9.4.1  Tracción
    9.4.2  Corte
    9.4.3  Bloque de corte (block shear)
  9.5   Placas base
  9.6   Conexiones a momento
```

---

### 2.5 NCh 427 Of.2000 — Chile

Norma Chilena de Acero. Chile usa AISC como referencia principal con adaptaciones.

**Materiales en Chile:**

| Acero | Denominación | Fy (MPa) | Fu (MPa) |
|---|---|---|---|
| A37-24ES | Planchas laminadas | 235 | 370 |
| A42-27ES | Laminados en caliente | 260 | 420 |
| A52-36ES | Alta resistencia | 355 | 510 |

**Pernos en Chile:**
- Se usan clasificaciones métricas (ISO): 4.6, 5.6, 8.8, 10.9
- Equivalencias: 8.8 ≈ A325, 10.9 ≈ A490

**NCh 430 Of.2008** — Hormigón armado (para conexiones mixtas acero-hormigón)

**NCh 2369.Of2003** — Diseño sísmico de estructuras industriales

---

### 2.6 NSR-10 Título F — Colombia

Norma Sismo-Resistente de Colombia. Título F: Estructuras metálicas.

**Materiales en Colombia:**

| Acero | Fy (MPa) | Fu (MPa) | Referencia |
|---|---|---|---|
| ASTM A36 | 250 | 400 | Más usado |
| ASTM A572 Gr.50 | 345 | 450 | Estructural |
| ASTM A500 Gr.B | 317 | 400 | Tubulares |

**Artículos NSR-10 Título F relevantes:**

```
F.1   — Disposiciones generales
F.2   — Materiales
F.3   — Diseño de elementos
F.4   — Conexiones (basado en AISC 360)
  F.4.1  Pernos
  F.4.2  Soldaduras
  F.4.3  Placas base
F.5   — Diseño sísmico (referencia a AISC 341)
```

---

### 2.7 Eurocódigo 3 (EC3) — EN 1993-1-8:2005

Norma Europea. Usada en España y países europeos. Sistema de factores parciales γ.

**Sistema de factores EC3:**

```
γM0 = 1.00  — Resistencia de secciones transversales
γM1 = 1.00  — Resistencia de miembros (inestabilidad)
γM2 = 1.25  — Resistencia de secciones netas (tracción)
γM3 = 1.25  — Pernos en conexiones de deslizamiento (ELS)
γM3,ser = 1.10 — Conexiones de deslizamiento en ELS
γMw = 1.25  — Soldaduras
```

**Materiales en EC3 — Aceros laminados EN 10025:**

| Denominación | Fy (MPa) para t≤16mm | Fu (MPa) |
|---|---|---|
| S235 | 235 | 360 |
| S275 | 275 | 430 |
| S355 | 355 | 510 |
| S420 | 420 | 520 |
| S460 | 460 | 540 |

**Clases de pernos EC3 (ISO 898-1):**

| Clase | fyb (MPa) | fub (MPa) |
|---|---|---|
| 4.6 | 240 | 400 |
| 5.6 | 300 | 500 |
| 6.8 | 480 | 600 |
| 8.8 | 640 | 800 |
| 10.9 | 900 | 1000 |

**Resistencias de diseño pernos EC3 — EN 1993-1-8 §3.6:**

```
Corte por plano:
  Fv,Rd = αv × fub × A / γM2
  αv = 0.6 para clases 4.6, 5.6, 6.8 (hilos en el plano)
  αv = 0.5 para clases 8.8, 10.9 (hilos en el plano)
  αv = 0.6 para vástago en el plano de corte (todas las clases)

Aplastamiento:
  Fb,Rd = k1 × αb × fub × d × t / γM2
  αb = min(αd, fub/fu, 1.0)
  αd = e1/(3d0) para perno extremo en dirección de carga
  αd = p1/(3d0) - 1/4 para pernos interiores
  k1 = min(2.8 e2/d0 - 1.7, 1.4 p2/d0 - 1.7, 2.5) perpendicular a la carga

Tracción:
  Ft,Rd = 0.9 × fub × As / γM2

Corte + tracción combinado:
  Fv,Ed/Fv,Rd + Ft,Ed/(1.4 Ft,Rd) ≤ 1.0
```

**Resistencia de soldaduras — EC3 §4.5.3:**

```
Soldadura en filete — método simplificado:
  Fw,Rd = fvw,d × Aw
  fvw,d = fu / (√3 × βw × γMw)
  βw: coeficiente de correlación
    S235: βw = 0.80
    S275: βw = 0.85
    S355: βw = 0.90
    S420/S460: βw = 1.00
  fu = resistencia a ruptura del metal base más débil
  Aw = garganta efectiva × longitud efectiva
```

---

### 2.8 NTE E.090-2006 — Perú

Norma Técnica de Estructuras Metálicas. Perú adopta AISC LRFD como referencia base.

**Materiales en Perú:**

| Acero | Fy (kg/cm²) | Fu (kg/cm²) | Equiv. ASTM |
|---|---|---|---|
| A36 | 2530 | 4080 | A36 |
| A572 Gr.50 | 3515 | 4590 | A572 |

Nota: el motor convierte internamente a MPa.

---

### 2.9 Tabla resumen — Equivalencias entre normas

| Concepto | AISC (USA) | CIRSOC (ARG) | EC3 (EUR) | NSR-10 (COL) | NCh (CHI) |
|---|---|---|---|---|---|
| Acero estructural base | A36 / A572 | F-24 / F-36 | S235 / S355 | A36 / A572 | A37 / A52 |
| Perno estándar | A307 | Gr. 5.6 | Cl. 4.6 | A307 | Cl. 4.6 |
| Perno alta resistencia | A325 | Gr. 8.8 | Cl. 8.8 | A325 | Cl. 8.8 |
| Perno muy alta resist. | A490 | Gr. 10.9 | Cl. 10.9 | A490 | Cl. 10.9 |
| Electrodo base | E70XX | E70XX | E35 (ISO) | E70XX | E70XX |
| Factor resistencia corte | φ=0.75 | φ=0.75 | γM2=1.25 | φ=0.75 | φ=0.75 |
| Factor resist. fluencia | φ=0.90 | φ=0.90 | γM0=1.00 | φ=0.90 | φ=0.90 |
| Espaciado mín. pernos | 2.67 db | 3.0 db | 3.0 d0 | 2.67 db | 3.0 db |

---

## 3. Fundamentos Técnicos — Teoría de Conexiones

### 3.1 Filosofía LRFD vs ASD

```
LRFD (Load and Resistance Factor Design):
  ΣγᵢQᵢ ≤ φRn
  Factores de carga γ: 1.2D + 1.6L + ...
  Factor de resistencia φ < 1.0 (reduce la capacidad)
  Más preciso, permite optimizar material

ASD (Allowable Stress Design):
  Q ≤ Rn / Ω
  Sin factores de carga (cargas de servicio)
  Ω = factor de seguridad (Ω = 1/φ × 1.5 aprox.)
  Más conservador, más intuitivo
```

La app trabaja en LRFD por defecto. El usuario puede cambiar a ASD.

### 3.2 Clasificación de conexiones por rigidez

```
Simple (articulada):
  → Solo transmite corte (y pequeño momento secundario)
  → La viga puede rotar libremente en el extremo
  → Ejemplos: shear tab, doble ángulo, ángulo de asiento

Rígida (momento resistente):
  → Transmite momento, corte y axial
  → La rotación relativa viga-columna es despreciable
  → Ejemplos: end plate extendida, WUF-W, brida atornillada

Semi-rígida:
  → Transmite momento parcial
  → La rigidez depende de la geometría
  → Menos usada en diseño estándar
```

### 3.3 Jerarquía de verificaciones en una conexión apernada

Siempre verificar en este orden (de la más común a la más rara):

```
1. Corte en el perno (shear in bolt)
2. Aplastamiento en la plancha (bearing on plate)
3. Aplastamiento en el alma de la viga (bearing on web)
4. Desgarro en bloque en la plancha (block shear in plate)
5. Desgarro en bloque en el alma de la viga (block shear in web)
6. Corte en la sección neta de la plancha (shear yielding/rupture)
7. Corte en la sección neta del alma de la viga
8. Longitud de soldadura plancha-columna (si hay soldadura)
```

### 3.4 Grupo de pernos con carga excéntrica

Cuando la fuerza no pasa por el centroide del grupo → hay momento secundario.

**Método elástico (conservador):**
```
Ic = Σ(xi² + yi²)   [momento de inercia polar del grupo]
e = excentricidad de la carga respecto al centroide
M = V × e            [momento excéntrico]

Fuerza directa en cada perno:
  fx_dir = Vx / n
  fy_dir = Vy / n

Fuerza por momento en cada perno:
  fx_mom = -M × yi / Ic
  fy_mom =  M × xi / Ic

Fuerza resultante en el perno más cargado:
  Fr = √[(fx_dir + fx_mom)² + (fy_dir + fy_mom)²]
```

**Método de resistencia última (IC method — más preciso, AISC Manual Tabla 8-4 a 8-11):**
```
- Usa el coeficiente C del Manual AISC
- Rn = C × φrn (resistencia del perno individual)
- C depende de: geometría del grupo, ángulo de carga, excentricidad
- Implementación: interpolación en tablas o solución iterativa
```

### 3.5 Grupo de soldaduras con carga excéntrica

**Método elástico:**
```
Aw = área efectiva total de garganta de la soldadura
x̄, ȳ = centroide del grupo de soldaduras

Ju = momento polar de inercia unitario (por unidad de garganta)
Para línea horizontal: Ju = L³/12
Para línea vertical:   Ju = L³/12
Para L-shape:          combinar con teorema de ejes paralelos

Carga directa por mm:
  f_dir_x = Fx / Aw
  f_dir_y = Fy / Aw

Carga por torsión:
  f_tors_x = -M × c_y / Ju
  f_tors_y =  M × c_x / Ju
  (c_x, c_y = distancia del perno al centroide)

Resultante máxima:
  f_max = √[(f_dir_x + f_tors_x)² + (f_dir_y + f_tors_y)²]
```

---

## 4. Estructura de Carpetas

```
SteelConn-Web/
│
├── index.html                      ← Pantalla principal
├── css/
│   ├── main.css                    ← Variables globales
│   ├── home.css                    ← Estilos home
│   └── modulo.css                  ← Estilos módulos de cálculo
│
├── modulos/
│   ├── shear-tab.html              ← Módulo 1
│   ├── end-plate.html              ← Módulo 2
│   ├── placa-base.html             ← Módulo 3
│   ├── soldadura-filete.html       ← Módulo 4
│   ├── soldadura-ranura.html       ← Módulo 5
│   ├── viga-columna-momento.html   ← Módulo 6
│   └── gusset-plate.html           ← Módulo 7
│
├── js/
│   ├── core/
│   │   ├── normas.js               ← Factores φ, Fy, Fu por norma
│   │   ├── materiales.js           ← Tabla de aceros, pernos, electrodos
│   │   ├── perfiles.js             ← Base de datos perfiles W, C, HSS
│   │   ├── pernos.js               ← Motor de cálculo de pernos
│   │   ├── soldaduras.js           ← Motor de cálculo de soldaduras
│   │   ├── block-shear.js          ← Desgarro en bloque
│   │   ├── shear-tab.js            ← Motor módulo 1
│   │   ├── end-plate.js            ← Motor módulo 2
│   │   ├── placa-base.js           ← Motor módulo 3
│   │   └── gusset-plate.js         ← Motor módulo 7
│   ├── ui/
│   │   ├── home.js                 ← Interactividad home
│   │   ├── semaforo.js             ← Sistema de verificaciones
│   │   ├── graficos-svg.js         ← Dibujo SVG de la conexión
│   │   └── resultados.js           ← Renderizado de tablas
│   └── utils/
│       ├── exportar-pdf.js         ← jsPDF — memoria de cálculo
│       ├── exportar-dxf.js         ← Exportación DXF
│       └── helpers.js              ← Redondeos, unidades, conversiones
│
├── assets/
│   ├── img/
│   │   ├── shear-tab-iso.png       ← Isometría genérica (imagen IA)
│   │   ├── end-plate-iso.png
│   │   ├── placa-base-iso.png
│   │   └── gusset-iso.png
│   └── icons/
│
└── tests/
    ├── test-shear-tab.js
    ├── test-end-plate.js
    └── test-soldaduras.js
```

---

## 5. Módulo 1 — Unión Apernada a Corte (Shear Tab)

### 5.1 Descripción

La shear tab (plancha de alma) es la conexión simple más usada en acero. Transmite solo corte. Una plancha rectangular se suelda a la columna (o viga principal) y se aperna al alma de la viga secundaria.

### 5.2 Geometría y datos de entrada

```
Fuerza de diseño:
  Vu = cortante último [kN]  (LRFD) o V = cortante de servicio [kN] (ASD)

Pernos:
  n      = número de pernos (1 a 12)
  db     = diámetro del perno [mm]  (12, 16, 19, 22, 24, 27, 30)
  tipo   = A307 / A325 / A490 / Gr.8.8 / Gr.10.9
  n_corte = planos de corte (1 o 2)
  e1     = distancia del perno al borde superior [mm]
  e2     = distancia del perno al borde lateral [mm]
  p      = separación entre pernos [mm]
  a      = excentricidad (distancia eje perno a cara de columna) [mm]

Plancha:
  tp     = espesor de la plancha [mm]
  Lp     = longitud de la plancha [mm]  (= (n-1)×p + 2×e1)
  bp     = ancho de la plancha [mm]
  Fyp    = fluencia de la plancha [MPa]
  Fup    = ruptura de la plancha [MPa]

Viga secundaria (beam):
  tw     = espesor del alma [mm]
  Fyw    = fluencia del alma [MPa]
  Fuw    = ruptura del alma [MPa]

Soldadura plancha-columna:
  w      = tamaño del filete [mm]
  FEXX   = resistencia del electrodo [MPa]  (482 para E70)
```

### 5.3 Proceso de verificación completo

```javascript
// js/core/shear-tab.js

/**
 * Motor de cálculo — Shear Tab (Plancha de alma)
 * Referencia: AISC 360-22 Capítulo J + AISC Manual Parte 10
 */

function calcularShearTab(input) {
  const { Vu, pernos, plancha, viga, soldadura, norma } = input;
  const phi_v = norma.phi_cortante;     // 0.75
  const phi_y = norma.phi_fluencia;     // 0.90
  const phi_t = norma.phi_traccion;     // 0.75

  const resultados = [];

  // ── 1. Corte en los pernos ──────────────────────────────────────────
  const Ab = Math.PI * (pernos.db / 2) ** 2;           // mm²
  const Fnv = norma.Fnv(pernos.tipo);                   // MPa
  const phi_Rn_perno = phi_v * Fnv * Ab * pernos.n_corte * pernos.n;  // N
  
  resultados.push({
    verificacion: "Corte en pernos",
    referencia: "AISC J3.6",
    demanda: Vu * 1000,                   // N
    capacidad: phi_Rn_perno,             // N
    relacion: (Vu * 1000) / phi_Rn_perno,
    formula: `φRn = φ × Fnv × Ab × n_corte × n = 0.75 × ${Fnv} × ${Ab.toFixed(0)} × ${pernos.n_corte} × ${pernos.n}`,
  });

  // ── 2. Aplastamiento en la plancha ──────────────────────────────────
  // Perno más cargado (extremo): Lc = e2 - d_agujero/2
  const d_agujero = pernos.db + 1.6;    // agujero estándar +1/16"
  const Lc_borde = plancha.e2 - d_agujero / 2;
  const Lc_inter = plancha.p - d_agujero;

  const Rn_borde = Math.min(1.2 * Lc_borde * plancha.tp * plancha.Fup,
                             2.4 * pernos.db * plancha.tp * plancha.Fup);
  const Rn_inter = Math.min(1.2 * Lc_inter * plancha.tp * plancha.Fup,
                             2.4 * pernos.db * plancha.tp * plancha.Fup);

  // Total aplastamiento plancha (1 borde + (n-1) interiores)
  const phi_Rn_aplast_p = phi_v * (Rn_borde + (pernos.n - 1) * Rn_inter);

  resultados.push({
    verificacion: "Aplastamiento en plancha",
    referencia: "AISC J3.10",
    demanda: Vu * 1000,
    capacidad: phi_Rn_aplast_p,
    relacion: (Vu * 1000) / phi_Rn_aplast_p,
    formula: `φRn = φ × [1.2×Lc×t×Fu ≤ 2.4×db×t×Fu] por perno`,
  });

  // ── 3. Aplastamiento en el alma de la viga ──────────────────────────
  const Lc_borde_v = plancha.e2 - d_agujero / 2;  // mismo e2 en la viga
  const Rn_borde_v = Math.min(1.2 * Lc_borde_v * viga.tw * viga.Fuw,
                               2.4 * pernos.db * viga.tw * viga.Fuw);
  const Rn_inter_v = Math.min(1.2 * Lc_inter * viga.tw * viga.Fuw,
                               2.4 * pernos.db * viga.tw * viga.Fuw);
  const phi_Rn_aplast_v = phi_v * (Rn_borde_v + (pernos.n - 1) * Rn_inter_v);

  resultados.push({
    verificacion: "Aplastamiento en alma de viga",
    referencia: "AISC J3.10",
    demanda: Vu * 1000,
    capacidad: phi_Rn_aplast_v,
    relacion: (Vu * 1000) / phi_Rn_aplast_v,
    formula: `Igual que plancha pero con tw=${viga.tw}mm y Fu=${viga.Fuw}MPa`,
  });

  // ── 4. Desgarro en bloque — plancha ────────────────────────────────
  const Anv_p = plancha.tp * (plancha.Lp - pernos.n * d_agujero);
  const Ant_p = plancha.tp * (plancha.e2 - d_agujero / 2);
  const Agv_p = plancha.tp * plancha.Lp;
  const Ubs = 1.0;  // tracción uniforme

  const phi_Rn_bs_p = phi_v * Math.min(
    0.60 * plancha.Fup * Anv_p + Ubs * plancha.Fup * Ant_p,
    0.60 * plancha.Fyp * Agv_p + Ubs * plancha.Fup * Ant_p
  );

  resultados.push({
    verificacion: "Desgarro en bloque — plancha",
    referencia: "AISC J4.3",
    demanda: Vu * 1000,
    capacidad: phi_Rn_bs_p,
    relacion: (Vu * 1000) / phi_Rn_bs_p,
    formula: `φRn = φ[0.60Fu×Anv + Ubs×Fu×Ant] ≤ φ[0.60Fy×Agv + Ubs×Fu×Ant]`,
  });

  // ── 5. Corte — sección bruta y neta de la plancha ──────────────────
  const Agv_plan = plancha.tp * plancha.Lp;
  const Anv_plan = plancha.tp * (plancha.Lp - pernos.n * d_agujero);

  const phi_Vn_bruta = 1.00 * 0.60 * plancha.Fyp * Agv_plan;
  const phi_Vn_neta  = phi_v * 0.60 * plancha.Fup * Anv_plan;
  const phi_Vn_plan  = Math.min(phi_Vn_bruta, phi_Vn_neta);

  resultados.push({
    verificacion: "Corte en plancha",
    referencia: "AISC J4.4",
    demanda: Vu * 1000,
    capacidad: phi_Vn_plan,
    relacion: (Vu * 1000) / phi_Vn_plan,
    formula: `min(φ×0.60Fy×Agv; φ×0.60Fu×Anv)`,
  });

  // ── 6. Soldadura plancha-columna ────────────────────────────────────
  const a_sold = 0.707 * soldadura.w;     // garganta efectiva [mm]
  const L_sold = 2 * plancha.Lp;          // soldadura a ambos lados
  const theta = 90;                        // carga perpendicular al eje de soldadura

  // Factor de dirección: 1.0 + 0.5 × sin^1.5(θ)
  const f_dir = 1.0 + 0.50 * Math.pow(Math.sin(theta * Math.PI / 180), 1.5);
  const Fw = 0.60 * soldadura.FEXX * f_dir;
  const phi_Rn_sold = phi_v * Fw * a_sold * L_sold;

  resultados.push({
    verificacion: "Soldadura plancha-columna",
    referencia: "AISC J2.4",
    demanda: Vu * 1000,
    capacidad: phi_Rn_sold,
    relacion: (Vu * 1000) / phi_Rn_sold,
    formula: `φRn = φ × 0.60×FEXX×(1+0.5sin^1.5θ) × a × L`,
  });

  // ── Verificación de excentricidad (momento secundario) ──────────────
  // Carga excéntrica en el grupo de pernos
  const e = soldadura ? plancha.bp / 2 : plancha.e2;  // excentricidad
  const M_exc = Vu * e;   // kN·m

  // Fuerza adicional por torsión en el perno más alejado
  const yi_max = (pernos.n - 1) / 2 * pernos.p;
  const Ic = pernos.n > 1
    ? pernos.n * Math.pow(pernos.p, 2) * (pernos.n ** 2 - 1) / 12
    : 0;
  const F_tors = Ic > 0 ? M_exc * 1000 * yi_max / Ic : 0;  // N

  // ── Resumen ─────────────────────────────────────────────────────────
  const ok = resultados.every(r => r.relacion <= 1.0);
  const relacion_max = Math.max(...resultados.map(r => r.relacion));
  const verificacion_critica = resultados.find(r => r.relacion === relacion_max);

  return {
    ok,
    relacion_max,
    verificacion_critica: verificacion_critica.verificacion,
    verificaciones: resultados,
    advertencias: relacion_max > 0.90 ? ["Relación Vu/φVn > 90% — conexión al límite"] : [],
  };
}
```

---

## 6. Módulo 2 — Unión con Plancha de Extremo (End Plate)

### 6.1 Descripción

La unión con plancha de extremo es la conexión momento resistente apernada más usada. La plancha se suelda a los extremos de la viga y se aperna a la columna.

### 6.2 Tipos de plancha de extremo

```
BUEP — Unstiffened End Plate (sin rigidizadores)
  → 2 filas de pernos, una sobre y una bajo el ala
  → Momento limitado, conexión sencilla

4ES — 4-Bolt Extended Stiffened
  → 4 pernos fuera del ala superior, 2 bajo el ala inferior
  → Rigidizadores en los extremos

8ES — 8-Bolt Extended Stiffened
  → 4 pernos sobre y 4 pernos bajo cada ala
  → Mayor capacidad de momento
  → Más usada en SMF (AISC 358)
```

### 6.3 Proceso de cálculo — Método AISC DG4/DG16

```javascript
// js/core/end-plate.js
// Referencia: AISC Design Guide 4 (3ª edición) y Design Guide 16

function calcularEndPlate(input) {
  const { Mu, Vu, viga, columna, plancha, pernos, norma } = input;
  const phi_b = norma.phi_flexion;   // 0.90
  const phi_v = norma.phi_cortante;  // 0.75

  const resultados = [];

  // ── 1. Momento plástico de la viga ──────────────────────────────────
  // El momento de diseño de la conexión debe ser ≥ Mu
  const Zx = viga.Zx;   // módulo plástico de la viga [mm³]
  const Mp_viga = viga.Fy * Zx;  // N·mm

  // ── 2. Fuerza en los pernos de tracción ────────────────────────────
  // Pernos sobre el ala en tracción (los más solicitados)
  // Para conexión de 4 pernos por ala (8ES):
  const d_brazo = viga.d - viga.tf;   // distancia entre ejes de alas [mm]
  const T_ala = Mu * 1e6 / d_brazo;   // N — fuerza total en el ala traccionada

  // Fuerza por perno (grupo de pernos por encima del ala)
  const n_t = pernos.n_traccion;      // pernos en la zona de tracción (2 o 4)
  const Pt_perno = T_ala / n_t;       // N por perno

  // Resistencia del perno a tracción
  const Ab = Math.PI * (pernos.db / 2) ** 2;
  const Fnt = norma.Fnt(pernos.tipo);  // MPa
  const phi_Rn_t = norma.phi_traccion * Fnt * Ab;  // N

  resultados.push({
    verificacion: "Tracción en pernos",
    referencia: "AISC J3.6 + DG4",
    demanda: Pt_perno,
    capacidad: phi_Rn_t,
    relacion: Pt_perno / phi_Rn_t,
    formula: `φRn = φ × Fnt × Ab = 0.75 × ${Fnt} × ${Ab.toFixed(0)}`,
  });

  // ── 3. Espesor de la plancha — método yield line ────────────────────
  // AISC DG4 Ec. 3.3 para plancha extendida sin rigidizadores
  // tp_req = √(4 Mu / (φb × bp × Fy × Yp))
  // Yp = parámetro geométrico (yield line parameter)
  // Simplificado:
  const bp = plancha.bp;          // ancho de la plancha [mm]
  const pf = pernos.pf;           // distancia ala a perno interior [mm]
  const pb = pernos.pb;           // separación entre pernos [mm]

  // Yield line parameter (para 4-bolt unstiffened, AISC DG4 Fig. 3.1)
  const Yp = bp / 2 * (1 / pf + 1 / (d_brazo - pf)) + 2 / pb;

  const tp_req = Math.sqrt(
    (4 * Mu * 1e6) / (phi_b * bp * plancha.Fyp * Yp)
  );

  resultados.push({
    verificacion: "Espesor de plancha de extremo",
    referencia: "AISC DG4 Ec.3.3",
    demanda: plancha.tp,        // espesor provisto
    capacidad: tp_req,          // espesor mínimo requerido
    relacion: tp_req / plancha.tp,
    formula: `tp_req = √(4Mu / (φ×bp×Fyp×Yp)) = ${tp_req.toFixed(1)} mm`,
    nota: "Relación: tp_req / tp_prov ≤ 1.0",
  });

  // ── 4. Ala de columna a flexión (T-stub) ───────────────────────────
  // La fuerza de los pernos introduce flexión en el ala de la columna
  const tcf = columna.tf;   // espesor del ala de columna
  const bcf = columna.bf;   // ancho del ala de columna

  // Resistencia del ala de columna (simplificado)
  const phi_Mn_ala_col = phi_b * 0.90 * columna.Fy * bcf * tcf ** 2 / 4;
  const M_ala_col_demand = Pt_perno * pernos.pf;

  resultados.push({
    verificacion: "Ala de columna a flexión",
    referencia: "AISC DG4 §3.2",
    demanda: M_ala_col_demand,
    capacidad: phi_Mn_ala_col,
    relacion: M_ala_col_demand / phi_Mn_ala_col,
    formula: `φMn = φ × 0.90 × Fy × bcf × tcf² / 4`,
    nota: "Si falla → agregar rigidizadores de columna",
  });

  // ── 5. Panel de cortante de la columna (panel zone) ────────────────
  // AISC 360-22 J10.6
  const Vn_pz = 0.60 * columna.Fy * columna.d * columna.tw;
  const phi_Vn_pz = 0.90 * Vn_pz;
  const V_pz = T_ala - Vu;  // Cortante en el panel (aprox.)

  resultados.push({
    verificacion: "Panel de cortante — columna",
    referencia: "AISC J10.6",
    demanda: Math.abs(V_pz),
    capacidad: phi_Vn_pz,
    relacion: Math.abs(V_pz) / phi_Vn_pz,
    formula: `φVn = 0.90 × 0.60 × Fy × d_col × tw_col`,
    nota: "Si falla → agregar plancha de doblaje (doubler plate)",
  });

  // ── 6. Soldaduras ala de viga a plancha ────────────────────────────
  // Las alas se sueldan con CJP → resistencia = metal base
  // Verif: el ala de la viga es suficiente
  const phi_Rn_ala = phi_b * viga.Fy * viga.bf * viga.tf;
  resultados.push({
    verificacion: "Ala de viga (soldadura CJP al ala)",
    referencia: "AISC J2.5a",
    demanda: T_ala,
    capacidad: phi_Rn_ala,
    relacion: T_ala / phi_Rn_ala,
    formula: `φRn = φ × Fy × bf × tf (metal base — CJP)`,
  });

  // ── 7. Alma de viga a plancha (soldadura filete) ────────────────────
  const w_alma = soldadura_alma_requerida(Vu, viga.d, viga.FEXX);
  resultados.push({
    verificacion: "Alma de viga — soldadura filete",
    referencia: "AISC J2.4",
    demanda: soldadura.w_alma,
    capacidad: w_alma.w_max,
    relacion: soldadura.w_alma >= w_alma.w_req ? 0 : w_alma.w_req / soldadura.w_alma,
    formula: `w_req = Vu / (φ × 0.60×FEXX × 0.707 × 2×Ld)`,
  });

  // ── Rigidizadores de columna requeridos ────────────────────────────
  const rigidizadores_requeridos = resultados
    .filter(r => r.nota && r.nota.includes("rigidizadores") && r.relacion > 1.0)
    .map(r => r.nota);

  const ok = resultados.every(r => r.relacion <= 1.0);
  return {
    ok,
    relacion_max: Math.max(...resultados.map(r => r.relacion)),
    verificaciones: resultados,
    rigidizadores_requeridos,
    tp_requerido: tp_req,
    T_ala_traccion: T_ala,
  };
}

function soldadura_alma_requerida(Vu, d_viga, FEXX) {
  const phi = 0.75;
  const Fw = 0.60 * FEXX * 1.0;  // carga paralela al eje → sin factor dirección
  const Ld = d_viga - 2 * 25;    // longitud soldadura (descuenta esquinas)
  const w_req = (Vu * 1000) / (phi * Fw * 0.707 * 2 * Ld);
  return { w_req, w_max: 0.75 * Math.min(d_viga / 2, 50) };
}
```

---

## 7. Módulo 3 — Placa Base de Columna

### 7.1 Descripción

Conecta la columna metálica con la cimentación de hormigón. Transmite carga axial (compresión o tracción), corte y momento.

### 7.2 Proceso de cálculo — AISC Design Guide 1

```javascript
// js/core/placa-base.js
// Referencia: AISC Design Guide 1 (3ª edición, 2014)

function calcularPlacaBase(input) {
  const { Pu, Vu, Mu, columna, placa, hormigon, pernos, norma } = input;
  const resultados = [];

  // ── Caso A: Solo compresión (sin momento o momento pequeño) ─────────
  // Presión máxima bajo la placa
  const A1 = placa.B * placa.N;       // área de la placa [mm²]
  // Área de apoyo (hormigón) — puede ser mayor si hay empotramiento
  const A2 = Math.min(placa.B * 4, hormigon.B_ped) *
              Math.min(placa.N * 4, hormigon.N_ped);

  // Resistencia del hormigón bajo la placa (AISC DG1 Ec.3.1.1)
  const phi_pp = 0.65;
  const Pp = phi_pp * 0.85 * hormigon.fc * A1 * Math.sqrt(A2 / A1);
  // (limitado a 2 × 0.85 fc A1 según ACI 318)
  const phi_Pp = Math.min(Pp, phi_pp * 2 * 0.85 * hormigon.fc * A1);

  resultados.push({
    verificacion: "Resistencia hormigón bajo placa",
    referencia: "AISC DG1 §3.1 / ACI 318 §22.8",
    demanda: Pu * 1000,
    capacidad: phi_Pp,
    relacion: (Pu * 1000) / phi_Pp,
    formula: `φPp = φ × 0.85×f'c×A1×√(A2/A1) = ${(phi_Pp/1000).toFixed(1)} kN`,
  });

  // ── Presión de diseño fp ─────────────────────────────────────────────
  const fp = (Pu * 1000) / A1;   // MPa

  // ── Espesor de la placa base ─────────────────────────────────────────
  // Voladizos de la placa (AISC DG1 §3.1.2)
  const m = (placa.N - 0.8 * columna.d) / 2;    // voladizo en dirección d
  const n = (placa.B - 0.8 * columna.bf) / 2;   // voladizo en dirección bf
  const lambda = Math.min(1.0, Math.sqrt(
    (2 * Math.sqrt(columna.bf * columna.d)) / (4 * Math.sqrt(A1 / 4))
  ));
  const n_prima = lambda / 4 * Math.sqrt(columna.d * columna.bf);
  const l_max = Math.max(m, n, n_prima);   // voladizo dominante

  const tp_req = l_max * Math.sqrt(2 * fp / (phi_pp * placa.Fyp));

  resultados.push({
    verificacion: "Espesor de placa base — compresión",
    referencia: "AISC DG1 Ec.3.3.4",
    demanda: placa.tp,
    capacidad: tp_req,
    relacion: tp_req / placa.tp,
    formula: `tp_req = l × √(2fp / (φ×Fyp)) = ${tp_req.toFixed(1)} mm`,
    nota: "Si ratio > 1.0 → aumentar tp",
  });

  // ── Caso B: Con momento (excentricidad grande) ───────────────────────
  if (Math.abs(Mu) > 0) {
    const e = (Mu * 1e6) / (Pu * 1000);   // excentricidad [mm]
    const e_crit = placa.N / 2 - phi_Pp / (2 * Pu * 1000) * placa.N;

    if (e > e_crit) {
      // Zona en tensión → pernos de anclaje trabajan a tracción
      const f = placa.N / 2 - pernos.distancia_borde;  // brazo de los pernos

      // Presión de contacto (distribución triangular)
      // q = presión máxima [N/mm]
      const Y = (placa.N / 2 + f - e) * 2;   // longitud de contacto [mm]
      const q = (Pu * 1000 + /* T */ 0) / Y;  // iteración

      // Tracción total en los pernos
      const T = q * Y / 2 - Pu * 1000;

      // Fuerza por perno
      const Tp_perno = T / pernos.n;
      const phi_Rn_anclaje = phi_pp * pernos.Futa * pernos.Ase;

      resultados.push({
        verificacion: "Tracción en pernos de anclaje",
        referencia: "AISC DG1 §3.2 + ACI 318 §17",
        demanda: Tp_perno,
        capacidad: phi_Rn_anclaje,
        relacion: Tp_perno / phi_Rn_anclaje,
        formula: `Tp = T_total / n_pernos = ${(Tp_perno/1000).toFixed(1)} kN/perno`,
      });
    }
  }

  // ── Cortante — transferencia al hormigón ─────────────────────────────
  // Por fricción: φVn = φ × μ × Pu (si hay compresión)
  const mu_friccion = 0.55;   // hormigón acabado sin mortero
  const phi_Vn_fric = 0.75 * mu_friccion * Pu * 1000;

  // Por pernos de anclaje: φVn = φ × 0.60 × Futa × Ase_v × n
  const phi_Vn_pernos = 0.75 * 0.60 * pernos.Futa * pernos.Ase * pernos.n;

  resultados.push({
    verificacion: "Cortante — fricción placa-hormigón",
    referencia: "AISC DG1 §3.3",
    demanda: Vu * 1000,
    capacidad: phi_Vn_fric,
    relacion: (Vu * 1000) / phi_Vn_fric,
    formula: `φVn = φ × μ × Pu = 0.75 × 0.55 × ${Pu.toFixed(0)}kN`,
  });

  const ok = resultados.every(r => r.relacion <= 1.0);
  return { ok, verificaciones: resultados, tp_requerido: tp_req, fp };
}
```

---

## 8. Módulo 4 — Soldadura en Filete

### 8.1 Proceso de cálculo

```javascript
// js/core/soldaduras.js

/**
 * Soldadura en filete — verificación completa
 * Referencia: AISC 360-22 J2.2 y J2.4
 */
function calcularSoldaduraFilete(input) {
  const { Pu, Vu, Mu, soldadura, norma } = input;
  const phi = 0.75;
  const resultados = [];

  // ── Garganta efectiva ───────────────────────────────────────────────
  const a = 0.707 * soldadura.w;   // garganta [mm]

  // ── Verificaciones de tamaño ────────────────────────────────────────
  // Tamaño mínimo según espesor de la parte más gruesa (AISC Tabla J2.4)
  const t_grueso = Math.max(soldadura.t1, soldadura.t2);
  const w_min = tamanioMinimoFilete(t_grueso);

  // Tamaño máximo: para t ≥ 6mm → w_max = t - 2mm; para t < 6mm → w_max = t
  const t_delgado = Math.min(soldadura.t1, soldadura.t2);
  const w_max = t_delgado >= 6 ? t_delgado - 2 : t_delgado;

  resultados.push({
    verificacion: "Tamaño de filete — mínimo",
    referencia: "AISC Tabla J2.4",
    demanda: w_min,
    capacidad: soldadura.w,
    relacion: w_min / soldadura.w,
    formula: `w_min = ${w_min}mm para t_max = ${t_grueso}mm`,
  });

  // ── Carga directa (sin excentricidad) ───────────────────────────────
  if (Vu > 0 && Mu === 0) {
    // Carga paralela al eje de la soldadura (corte puro)
    const theta = 0;
    const f_dir = 1.0 + 0.50 * Math.pow(Math.sin(theta * Math.PI / 180), 1.5);
    const Fw = 0.60 * soldadura.FEXX * f_dir;
    const Rn_sold = phi * Fw * a * soldadura.L_total;

    resultados.push({
      verificacion: "Capacidad soldadura a corte",
      referencia: "AISC J2.4",
      demanda: Vu * 1000,
      capacidad: Rn_sold,
      relacion: (Vu * 1000) / Rn_sold,
      formula: `φRn = φ × 0.60×FEXX×(1+0.5sin^1.5θ) × a × L = ${(Rn_sold/1000).toFixed(1)} kN`,
    });
  }

  if (Pu > 0 && Mu === 0) {
    // Carga perpendicular al eje (tracción/compresión)
    const theta = 90;
    const f_dir = 1.0 + 0.50 * Math.pow(Math.sin(theta * Math.PI / 180), 1.5);
    // f_dir = 1.50 para carga perpendicular
    const Fw = 0.60 * soldadura.FEXX * f_dir;
    const Rn_sold = phi * Fw * a * soldadura.L_total;

    resultados.push({
      verificacion: "Capacidad soldadura a tracción",
      referencia: "AISC J2.4",
      demanda: Pu * 1000,
      capacidad: Rn_sold,
      relacion: (Pu * 1000) / Rn_sold,
      formula: `φRn = φ × 0.60×FEXX×1.50 × a × L (θ=90°)`,
    });
  }

  // ── Verificación del metal base adyacente ───────────────────────────
  // φRn_metal_base = φ × 0.60 × Fy × t (para corte)
  const phi_Rn_mb1 = 0.90 * 0.60 * soldadura.Fy1 * soldadura.t1 * soldadura.L_total;
  const phi_Rn_mb2 = 0.90 * 0.60 * soldadura.Fy2 * soldadura.t2 * soldadura.L_total;

  resultados.push({
    verificacion: "Metal base — plancha 1",
    referencia: "AISC J4.4",
    demanda: Vu * 1000,
    capacidad: phi_Rn_mb1,
    relacion: (Vu * 1000) / phi_Rn_mb1,
    formula: `φRn = 0.90 × 0.60 × Fy × t × L`,
  });

  return { ok: resultados.every(r => r.relacion <= 1.0), verificaciones: resultados };
}

function tamanioMinimoFilete(t_max_mm) {
  // AISC Tabla J2.4
  if (t_max_mm <= 6)   return 3;
  if (t_max_mm <= 13)  return 5;
  if (t_max_mm <= 19)  return 6;
  return 8;
}
```

---

## 9. Módulo 5 — Soldadura en Ranura CJP y PJP

```javascript
// Parte de js/core/soldaduras.js

function calcularSoldaduraRanura(input) {
  const { tipo, Pu, Vu, Mu, soldadura, norma } = input;
  // tipo: "CJP" o "PJP"
  const resultados = [];

  if (tipo === "CJP") {
    // CJP = Resistencia igual al metal base (AISC J2.5a)
    // Solo verificar el metal base
    const phi_Rn_traccion = 0.90 * soldadura.Fy * soldadura.A_neta;
    const phi_Rn_corte    = 0.75 * 0.60 * soldadura.Fu * soldadura.A_neta;

    resultados.push({
      verificacion: "CJP — tracción (metal base)",
      referencia: "AISC J2.5a",
      demanda: Pu * 1000,
      capacidad: phi_Rn_traccion,
      relacion: (Pu * 1000) / phi_Rn_traccion,
      formula: `φRn = 0.90 × Fy × A_neta`,
    });

    resultados.push({
      verificacion: "CJP — corte (metal base)",
      referencia: "AISC J2.5a",
      demanda: Vu * 1000,
      capacidad: phi_Rn_corte,
      relacion: (Vu * 1000) / phi_Rn_corte,
      formula: `φRn = 0.75 × 0.60 × Fu × A_neta`,
    });

  } else if (tipo === "PJP") {
    // PJP — garganta efectiva depende del ángulo de preparación
    // AISC J2.3b y Tabla J2.2
    const te = garganteEfectivaPJP(soldadura.tipo_prep, soldadura.angulo, soldadura.t);

    // Tracción perpendicular (AISC J2.5b — φ = 0.80)
    const phi_Rn_t_perp = 0.80 * 0.60 * soldadura.FEXX * te * soldadura.L;

    // Compresión (φ = 0.90)
    const phi_Rn_comp = 0.90 * 0.60 * soldadura.FEXX * te * soldadura.L;

    // Corte (φ = 0.75)
    const phi_Rn_corte = 0.75 * 0.60 * soldadura.FEXX * te * soldadura.L;

    resultados.push({
      verificacion: "PJP — tracción perpendicular",
      referencia: "AISC J2.5b",
      demanda: Pu * 1000,
      capacidad: phi_Rn_t_perp,
      relacion: (Pu * 1000) / phi_Rn_t_perp,
      formula: `φRn = 0.80 × 0.60 × FEXX × te × L (te=${te.toFixed(1)}mm)`,
    });

    resultados.push({
      verificacion: "PJP — corte paralelo",
      referencia: "AISC J2.5b",
      demanda: Vu * 1000,
      capacidad: phi_Rn_corte,
      relacion: (Vu * 1000) / phi_Rn_corte,
      formula: `φRn = 0.75 × 0.60 × FEXX × te × L`,
    });
  }

  return { ok: resultados.every(r => r.relacion <= 1.0), verificaciones: resultados };
}

function garganteEfectivaPJP(tipo_prep, angulo_deg, t) {
  // AISC Tabla J2.2 — garganta efectiva para PJP
  // tipo_prep: "V", "doble-V", "U", "J", "bisel"
  const angulo = angulo_deg;
  if (tipo_prep === "V") {
    if (angulo >= 60) return t;           // V completa ≥ 60°
    if (angulo >= 45) return t - 3;       // V parcial 45°-60°
  }
  if (tipo_prep === "bisel") {
    if (angulo >= 45) return t - 3;
    return t * Math.tan(angulo * Math.PI / 180);
  }
  if (tipo_prep === "U") return t - 3;
  if (tipo_prep === "J") return t - 3;
  return t * 0.70;   // conservador por defecto
}
```

---

## 10. Módulo 6 — Unión Viga-Columna Momento Resistente

### 10.1 Descripción

Conexión rígida que transmite momento, corte y axial. Es la conexión crítica en marcos a momento. Se verifica contra AISC 358 para zonas sísmicas.

### 10.2 Verificaciones principales

```
1. Soldadura CJP de alas: resistencia = metal base
2. Plancha de continuidad (rigidizador de columna):
   - Requiere si: tcf < tf_viga o Pbf > φRn_ala_col
3. Plancha de doblaje (doubler plate) alma de columna:
   - Verifica panel zone: AISC J10.6
   - φVn = 0.90 × 0.60 × Fy × dc × tw_col × (1 + 3bcf×tcf² / (db×dc×tw_col))
4. Relación columna fuerte / viga débil (AISC 341 E3.4a):
   - ΣMpc* / ΣMpb* ≥ 1.0
   - Mpc* = Mp_col - Pu×Ag/Fy / (Fy×Z_col)
   - Mpb* = Mp_viga esperado
5. Si es SMF: verificar conexión precalificada (AISC 358)
   - WUF-W, BFP, RBS según aplique
```

```javascript
// js/core/shear-tab.js — panel zone
function verificarPanelZone(columna, Vu_col, Vu_vigas) {
  // AISC 360-22 J10.6 — Resistencia del panel de cortante
  const dc = columna.d;
  const tw = columna.tw;
  const bcf = columna.bf;
  const tcf = columna.tf;

  // Resistencia nominal (sin dobladoras)
  const Vn = 0.60 * columna.Fy * dc * tw *
    (1 + 3 * bcf * tcf ** 2 / (columna.d * dc * tw));

  const phi = 0.90;
  const phi_Vn = phi * Vn;

  // Cortante en el panel = ΣM_vigas / d_brazo - V_columna
  const V_panel = Vu_vigas / (columna.d - columna.tf) - Vu_col;

  return {
    verificacion: "Panel de cortante (panel zone)",
    referencia: "AISC J10.6",
    demanda: Math.abs(V_panel),
    capacidad: phi_Vn,
    relacion: Math.abs(V_panel) / phi_Vn,
    formula: `φVn = 0.90×0.60×Fy×dc×tw×(1 + 3bcf×tcf²/(db×dc×tw))`,
    nota: V_panel > phi_Vn ? "Requiere plancha de doblaje" : "OK",
  };
}
```

---

## 11. Módulo 7 — Nodo de Armadura (Gusset Plate)

### 11.1 Descripción

La plancha nodal (gusset plate) conecta barras de arriostre o celosía al nodo viga-columna. Es crítica en marcos arriostrados.

### 11.2 Verificaciones (AISC DG 29)

```
1. Tracción en la barra de arriostre (AISC D1, D2)
   - Sección bruta: φPn = 0.90 × Fy × Ag
   - Sección neta: φPn = 0.75 × Fu × Ae = 0.75 × Fu × An × U

2. Compresión en la barra (AISC E3)
   - φPn = 0.90 × Fcr × Ag
   - Fcr depende de la esbeltez KL/r

3. Whitmore section — plancha nodal en compresión
   - Lw = longitud de Whitmore = L_sold × tan(30°) × 2 + w_barra
   - φRn = φ × Fy × Lw × t_gusset

4. Block shear en la plancha nodal (AISC J4.3)

5. Soldaduras barra-gusset

6. Soldaduras gusset-viga y gusset-columna
   - Método de la interfaz (AISC Manual Parte 13)
   - Distribución de fuerzas en cada soldadura (Hv, Hh, H_diag)

7. Pandeo de la plancha en zona sin soporte
   - L_libre / t_gusset ≤ 0.65 × √(E/Fy) × 2
```

---

## 12. Base de Datos de Perfiles y Materiales

### 12.1 `js/core/materiales.js`

```javascript
/**
 * Base de datos de materiales y pernos
 * Todas las unidades en MPa, mm, N
 */

const ACEROS = {
  "A36":       { Fy: 250, Fu: 400, E: 200000, nombre: "ASTM A36" },
  "A572-50":   { Fy: 345, Fu: 450, E: 200000, nombre: "ASTM A572 Gr.50" },
  "A572-60":   { Fy: 415, Fu: 520, E: 200000, nombre: "ASTM A572 Gr.60" },
  "A992":      { Fy: 345, Fu: 450, E: 200000, nombre: "ASTM A992 (vigas W)" },
  "A500-B":    { Fy: 317, Fu: 400, E: 200000, nombre: "ASTM A500 Gr.B (HSS)" },
  "A500-C":    { Fy: 345, Fu: 427, E: 200000, nombre: "ASTM A500 Gr.C (HSS)" },
  "S235":      { Fy: 235, Fu: 360, E: 210000, nombre: "EN S235 (EC3)" },
  "S275":      { Fy: 275, Fu: 430, E: 210000, nombre: "EN S275 (EC3)" },
  "S355":      { Fy: 355, Fu: 510, E: 210000, nombre: "EN S355 (EC3)" },
  "F-24":      { Fy: 235, Fu: 370, E: 200000, nombre: "IRAM F-24 (CIRSOC)" },
  "F-36":      { Fy: 355, Fu: 510, E: 200000, nombre: "IRAM F-36 (CIRSOC)" },
};

const PERNOS = {
  "A307":      { Fnt: 310, Fnv: 165, Futa: 414, tipo: "sin_pretension",
                 nombre: "ASTM A307 (perno ordinario)" },
  "A325-X":    { Fnt: 620, Fnv: 372, Futa: 724, tipo: "alta_resistencia",
                 nombre: "A325 / F3125-A325 (sin hilos)" },
  "A325-N":    { Fnt: 620, Fnv: 310, Futa: 724, tipo: "alta_resistencia",
                 nombre: "A325 / F3125-A325 (con hilos)" },
  "A490-X":    { Fnt: 780, Fnv: 457, Futa: 1000, tipo: "alta_resistencia",
                 nombre: "A490 / F3125-A490 (sin hilos)" },
  "A490-N":    { Fnt: 780, Fnv: 372, Futa: 1000, tipo: "alta_resistencia",
                 nombre: "A490 / F3125-A490 (con hilos)" },
  "ISO-8.8":   { Fnt: 560, Fnv: 336, Futa: 800, tipo: "alta_resistencia",
                 nombre: "ISO 898-1 Clase 8.8" },
  "ISO-10.9":  { Fnt: 700, Fnv: 420, Futa: 1000, tipo: "alta_resistencia",
                 nombre: "ISO 898-1 Clase 10.9" },
  "ISO-4.6":   { Fnt: 240, Fnv: 144, Futa: 400, tipo: "sin_pretension",
                 nombre: "ISO 898-1 Clase 4.6" },
};

// Pretensado mínimo de pernos de alta resistencia [kN] — AISC Tabla J3.1
const PRETENSADO = {
  "A325": { 16: 71, 19: 91, 22: 110, 24: 125, 27: 146, 30: 176 },
  "A490": { 16: 89, 19: 114, 22: 138, 24: 157, 27: 184, 30: 220 },
};

const ELECTRODOS = {
  "E60":   { FEXX: 414, nombre: "E6010 / E6013 (SMAW)" },
  "E70":   { FEXX: 482, nombre: "E7018 / E71T-1 — más común" },
  "E80":   { FEXX: 552, nombre: "E8010 / E80XX (alta resistencia)" },
  "ER70S": { FEXX: 482, nombre: "ER70S-X (GMAW/GTAW)" },
};

// Diámetros de pernos comerciales [mm]
const DIAMETROS_PERNOS = [12, 14, 16, 19, 20, 22, 24, 27, 30, 33, 36];

// Áreas nominales de pernos [mm²]
function areaPernoNominal(db_mm) {
  return Math.PI * Math.pow(db_mm / 2, 2);
}

// Área de la raíz de la rosca (resistencia) — aprox 0.75 × Ab
function areaRaizRosca(db_mm) {
  return 0.75 * areaPernoNominal(db_mm);
}
```

### 12.2 `js/core/perfiles.js` — Extracto perfiles W (AISC)

```javascript
/**
 * Base de datos de perfiles W — propiedades geométricas
 * Fuente: AISC Steel Construction Manual 16th Ed., Tabla 1-1
 * Unidades: mm, mm², mm³, mm⁴
 */

const PERFILES_W = {
  "W200x100": { d:210, bf:206, tf:23.7, tw:12.6, A:12700, Ix:6.21e7, Sx:5.91e5, Zx:6.61e5, Iy:2.23e7, ry:42.0 },
  "W250x89":  { d:260, bf:256, tf:17.3, tw:10.7, A:11400, Ix:1.42e8, Sx:1.09e6, Zx:1.23e6, Iy:4.79e7, ry:64.8 },
  "W310x97":  { d:308, bf:305, tf:15.4, tw:9.9,  A:12300, Ix:2.22e8, Sx:1.44e6, Zx:1.64e6, Iy:7.27e7, ry:76.9 },
  "W360x91":  { d:353, bf:254, tf:16.4, tw:9.8,  A:11600, Ix:3.35e8, Sx:1.90e6, Zx:2.14e6, Iy:4.41e7, ry:61.7 },
  "W360x110": { d:360, bf:256, tf:19.9, tw:11.4, A:14100, Ix:4.16e8, Sx:2.31e6, Zx:2.61e6, Iy:5.50e7, ry:62.5 },
  "W410x60":  { d:407, bf:178, tf:12.8, tw:7.7,  A:7590,  Ix:2.16e8, Sx:1.06e6, Zx:1.20e6, Iy:1.18e7, ry:39.5 },
  "W410x85":  { d:417, bf:181, tf:18.2, tw:10.9, A:10800, Ix:3.16e8, Sx:1.52e6, Zx:1.74e6, Iy:1.78e7, ry:40.6 },
  "W460x82":  { d:460, bf:191, tf:16.0, tw:9.9,  A:10400, Ix:3.70e8, Sx:1.61e6, Zx:1.83e6, Iy:2.36e7, ry:47.6 },
  "W530x92":  { d:533, bf:209, tf:15.6, tw:10.2, A:11800, Ix:5.54e8, Sx:2.08e6, Zx:2.37e6, Iy:2.39e7, ry:44.9 },
  "W610x101": { d:603, bf:228, tf:14.9, tw:10.5, A:12900, Ix:7.61e8, Sx:2.52e6, Zx:2.88e6, Iy:3.44e7, ry:51.6 },
};

/**
 * Busca el perfil más liviano que cumple con Zx_requerido
 */
function seleccionarPerfilW(Zx_req_mm3) {
  return Object.entries(PERFILES_W)
    .filter(([_, p]) => p.Zx >= Zx_req_mm3)
    .sort((a, b) => a[1].A - b[1].A)[0];
}
```

---

## 13. Motor de Normas — Factores por País

### 13.1 `js/core/normas.js`

```javascript
/**
 * Factores de diseño por norma.
 * El motor de cálculo llama siempre a norma.phi_cortante, etc.
 * Cambiar la norma = cambiar el objeto. Nada más.
 */

const NORMAS = {

  "AISC360": {
    nombre: "AISC 360-22",
    pais: "USA / Internacional",
    sistema: "LRFD",
    phi_flexion: 0.90,
    phi_cortante: 0.75,
    phi_fluencia: 0.90,
    phi_traccion: 0.75,
    phi_compresion: 0.90,
    phi_aplastamiento: 0.75,
    espaciado_min_pernos: (db) => 2.67 * db,
    Fnv: (tipo) => PERNOS[tipo].Fnv,
    Fnt: (tipo) => PERNOS[tipo].Fnt,
    combinaciones: { D: 1.2, L: 1.6, S: 1.6, W: 1.0, E: 1.0 },
    referencia: "AISC 360-22 Capítulo J",
  },

  "CIRSOC301": {
    nombre: "CIRSOC 301-2005",
    pais: "Argentina",
    sistema: "LRFD",
    phi_flexion: 0.90,
    phi_cortante: 0.75,
    phi_fluencia: 0.90,
    phi_traccion: 0.75,
    phi_compresion: 0.90,
    phi_aplastamiento: 0.75,
    espaciado_min_pernos: (db) => 3.0 * db,     // CIRSOC: 3db
    Fnv: (tipo) => PERNOS[tipo].Fnv,
    Fnt: (tipo) => PERNOS[tipo].Fnt,
    combinaciones: { D: 1.2, L: 1.6, S: 1.6, W: 1.0, E: 1.0 },
    referencia: "CIRSOC 301-2005 Cap.9",
  },

  "EC3": {
    nombre: "Eurocódigo 3 — EN 1993-1-8",
    pais: "España / Europa",
    sistema: "LRFD (factores γ)",
    phi_flexion: 1.0 / 1.00,   // γM0 = 1.00
    phi_cortante: 1.0 / 1.25,  // γM2 = 1.25 → φ = 0.80
    phi_fluencia: 1.0 / 1.00,
    phi_traccion: 1.0 / 1.25,
    phi_compresion: 1.0 / 1.00,
    phi_aplastamiento: 1.0 / 1.25,
    phi_soldadura: 1.0 / 1.25,
    espaciado_min_pernos: (db) => 3.0 * db,
    Fnv: (tipo) => {
      // EC3 Tabla 3.4: corte αv × fub / γM2
      const perno = PERNOS[tipo];
      const alpha_v = (tipo.includes("8.8") || tipo.includes("10.9")) ? 0.5 : 0.6;
      return alpha_v * perno.Futa / 1.25;
    },
    Fnt: (tipo) => 0.9 * PERNOS[tipo].Futa / 1.25,
    combinaciones: { G: 1.35, Q: 1.50, E: 1.0 },
    // Coeficientes de correlación βw para soldaduras
    beta_w: (acero) => ({ "S235":0.80, "S275":0.85, "S355":0.90, "S420":1.00, "S460":1.00 }[acero] || 1.00),
    referencia: "EN 1993-1-8:2005 §3 y §4",
  },

  "NSR10": {
    nombre: "NSR-10 Título F",
    pais: "Colombia",
    sistema: "LRFD",
    phi_flexion: 0.90,
    phi_cortante: 0.75,
    phi_fluencia: 0.90,
    phi_traccion: 0.75,
    phi_compresion: 0.90,
    phi_aplastamiento: 0.75,
    espaciado_min_pernos: (db) => 2.67 * db,
    Fnv: (tipo) => PERNOS[tipo].Fnv,
    Fnt: (tipo) => PERNOS[tipo].Fnt,
    combinaciones: { D: 1.2, L: 1.6, S: 1.6, E: 1.0 },
    referencia: "NSR-10 F.4",
  },

  "NCH427": {
    nombre: "NCh 427 Of.2000",
    pais: "Chile",
    sistema: "LRFD",
    phi_flexion: 0.90,
    phi_cortante: 0.75,
    phi_fluencia: 0.90,
    phi_traccion: 0.75,
    phi_compresion: 0.90,
    phi_aplastamiento: 0.75,
    espaciado_min_pernos: (db) => 3.0 * db,
    Fnv: (tipo) => PERNOS[tipo].Fnv,
    Fnt: (tipo) => PERNOS[tipo].Fnt,
    combinaciones: { D: 1.2, L: 1.6, S: 1.6, E: 1.0 },
    referencia: "NCh 427 Of.2000 + NCh 2369",
  },
};

function getNorma(codigo) {
  return NORMAS[codigo] || NORMAS["AISC360"];
}
```

---

## 14. Pantalla Principal — UI Home

### 14.1 Estructura visual

La home de SteelConn sigue el mismo diseño que FundaCalc pero con identidad visual de acero: fondo oscuro con sección de perfil W, grid técnico, 10 tarjetas de módulos.

### 14.2 Selector de norma global

```html
<!-- Barra superior — selector de norma persistente en toda la app -->
<div class="sc-norma-bar">
  <label>Norma de diseño:</label>
  <select id="sel-norma" onchange="setNormaGlobal(this.value)">
    <option value="AISC360">AISC 360-22 (USA / Internacional)</option>
    <option value="CIRSOC301">CIRSOC 301-2005 (Argentina)</option>
    <option value="EC3">Eurocódigo 3 — EN 1993-1-8 (España)</option>
    <option value="NSR10">NSR-10 Título F (Colombia)</option>
    <option value="NCH427">NCh 427 (Chile)</option>
  </select>
  <label>Sistema:</label>
  <select id="sel-sistema">
    <option value="LRFD">LRFD (cargas últimas)</option>
    <option value="ASD">ASD (cargas de servicio)</option>
  </select>
</div>
```

---

## 15. Sistema de Verificaciones — Semáforo

### 15.1 `js/ui/semaforo.js`

```javascript
/**
 * Renderiza la tabla de verificaciones con semáforo de colores.
 * Cada verificación muestra: Demanda / Capacidad y ratio.
 */

function renderizarSemaforo(verificaciones, contenedor_id) {
  const cont = document.getElementById(contenedor_id);
  cont.innerHTML = "";

  const tabla = document.createElement("table");
  tabla.className = "sc-semaforo-tabla";

  // Header
  tabla.innerHTML = `
    <thead>
      <tr>
        <th>Verificación</th>
        <th>Referencia</th>
        <th>Demanda</th>
        <th>Capacidad</th>
        <th>D/C</th>
        <th>Estado</th>
      </tr>
    </thead>
    <tbody></tbody>
  `;

  const tbody = tabla.querySelector("tbody");

  verificaciones.forEach(v => {
    const ratio = v.relacion;
    const color = ratio <= 0.80 ? "verde"
                : ratio <= 1.00 ? "amarillo"
                : "rojo";
    const icono = ratio <= 1.00 ? "✔" : "✘";

    const tr = document.createElement("tr");
    tr.className = `sc-row-${color}`;
    tr.innerHTML = `
      <td>${v.verificacion}</td>
      <td class="sc-ref">${v.referencia}</td>
      <td>${formatearFuerza(v.demanda)}</td>
      <td>${formatearFuerza(v.capacidad)}</td>
      <td class="sc-ratio sc-${color}">${ratio.toFixed(3)}</td>
      <td class="sc-icono sc-${color}">${icono}</td>
    `;

    // Expandir fórmula al hacer clic
    tr.addEventListener("click", () => {
      const detalle = document.getElementById(`det-${v.verificacion}`);
      if (detalle) detalle.classList.toggle("open");
    });

    tbody.appendChild(tr);

    // Fila de detalle (oculta)
    const tr_det = document.createElement("tr");
    tr_det.id = `det-${v.verificacion}`;
    tr_det.className = "sc-row-detalle";
    tr_det.innerHTML = `
      <td colspan="6">
        <code>${v.formula}</code>
        ${v.nota ? `<p class="sc-nota">${v.nota}</p>` : ""}
      </td>
    `;
    tbody.appendChild(tr_det);
  });

  cont.appendChild(tabla);

  // Resumen global
  const ok_total = verificaciones.every(v => v.relacion <= 1.0);
  const ratio_max = Math.max(...verificaciones.map(v => v.relacion));
  const resumen = document.createElement("div");
  resumen.className = `sc-resumen ${ok_total ? "ok" : "falla"}`;
  resumen.innerHTML = `
    <strong>${ok_total ? "✔ Conexión CONFORME" : "✘ Conexión NO CONFORME"}</strong>
    <span>Ratio máximo: ${ratio_max.toFixed(3)}</span>
  `;
  cont.appendChild(resumen);
}

function formatearFuerza(valor_N) {
  if (Math.abs(valor_N) >= 1e6) return `${(valor_N/1e6).toFixed(2)} MN`;
  if (Math.abs(valor_N) >= 1e3) return `${(valor_N/1e3).toFixed(1)} kN`;
  return `${valor_N.toFixed(0)} N`;
}
```

---

## 16. Exportación PDF y DXF

### 16.1 Estructura del PDF (memoria de cálculo)

```
Página 1 — Portada
  Logo SteelConn
  Tipo de conexión
  Norma seleccionada
  Fecha y proyecto

Página 2 — Datos de entrada
  Fuerzas de diseño (Vu, Pu, Mu)
  Geometría de pernos / soldadura
  Materiales (acero, pernos, electrodo)
  Perfiles involucrados

Página 3 — Isometría de la conexión
  Imagen genérica + cotas dinámicas del cálculo específico

Página 4 — Tabla de verificaciones
  Semáforo completo con ratios D/C
  Fórmulas utilizadas

Página 5 — Conclusiones
  Conexión conforme / no conforme
  Verificación crítica
  Recomendaciones si falla
```

### 16.2 Estructura del DXF (plano)

```
Capas DXF:
  PERFIL_VIGA       — Sección de la viga
  PERFIL_COLUMNA    — Sección de la columna
  PLANCHA           — Plancha de conexión
  PERNOS            — Círculos de pernos + cruces
  SOLDADURAS        — Símbolo de soldadura (AWS)
  COTAS             — Dimensiones y distancias
  TEXTOS            — Rótulos y especificaciones
  SIMBOLOS          — Símbolo de soldadura completo
```

---

## 17. Casos de Prueba con Valores Reales

### Caso 1 — Shear Tab: viga W410x85 en columna W310x97

```
Fuerza de diseño:
  Vu = 180 kN (LRFD)

Pernos:
  n = 3 pernos A325 M22 (db = 22mm)
  Planos de corte: 1
  e1 = 38mm (borde superior)
  e2 = 38mm (borde lateral)
  p  = 76mm (separación)

Plancha:
  tp = 10mm
  Lp = 190mm  (= 2×38 + 2×76)
  bp = 100mm
  A36: Fyp=250MPa, Fup=400MPa

Soldadura plancha-columna:
  Filete w=8mm, E70 (FEXX=482MPa)
  L_total = 2×190 = 380mm

Resultados esperados:
  1. Corte en pernos:     φRn = 3×0.75×310×380 = 264.5kN ✔ (ratio=0.68)
  2. Aplastamiento plancha: φRn = 0.75×[1.2×27×10×400 +
                                        2×(1.2×54×10×400)] = 356kN ✔
  3. Soldadura filete:    φRn = 0.75×0.60×482×1.0×0.707×8×380 = 493kN ✔
  4. Block shear plancha: verificar con las dimensiones dadas
  5. Corte plancha:       φRn = 0.90×0.60×250×190×10 = 256.5kN ✔
```

### Caso 2 — Placa Base: columna W250x89, Pu=1200kN

```
Fuerza axial:
  Pu = 1200 kN (solo compresión, sin momento)

Placa base:
  B = 350mm, N = 350mm
  tp = 25mm
  A36: Fyp = 250MPa

Pedestal de hormigón:
  B_ped = 600mm, N_ped = 600mm
  f'c = 25 MPa (H25)

Resultados esperados:
  A1 = 350×350 = 122500 mm²
  A2 = 600×600 = 360000 mm²
  √(A2/A1) = 1.71 → limitado a 2.0
  φPp = 0.65 × 0.85 × 25 × 122500 × 2.0 = 3381 kN ✔

  fp = 1200×1000 / 122500 = 9.80 MPa
  Voladizo m = (350 - 0.8×260)/2 = 71mm
  Voladizo n = (350 - 0.8×256)/2 = 73mm (dominante)
  tp_req = 73 × √(2×9.80 / (0.65×250)) = 73×0.346 = 25.3mm ≈ 25mm ✔
```

### Caso 3 — Soldadura en Filete: ángulo de asiento

```
Fuerza:
  Vu = 120 kN (perpendicular al eje de soldadura)

Soldadura:
  Filete w = 10mm, E70 (FEXX = 482MPa)
  L_total = 2 × 150mm = 300mm (filete en dos lados)
  θ = 90° (carga perpendicular)

Cálculo:
  a = 0.707 × 10 = 7.07mm
  f_dir = 1.0 + 0.5 × sin^1.5(90°) = 1.5
  Fw = 0.60 × 482 × 1.5 = 433.8 MPa
  φRn = 0.75 × 433.8 × 7.07 × 300 = 690 kN ✔ (ratio = 0.17)

Conclusión: Soldadura muy holgada — optimizar a w=6mm
  φRn_6mm = 0.75 × 433.8 × 4.24 × 300 = 414 kN ✔ (ratio = 0.29)
```

---

## 18. Roadmap — Módulos Futuros

| Módulo | Descripción | Prioridad |
|---|---|---|
| Ángulo de asiento (seat angle) | Conexión simple — ángulo apernado | Alta |
| Doble ángulo (double angle) | Conexión simple de alma | Alta |
| Empalme de columna | CJP o plancha de empalme | Media |
| Empalme de viga | Plancha de brida + alma | Media |
| Conexión con cartela (haunch) | Naves industriales | Media |
| Conexión HSS-HSS (T, Y, K) | Perfiles tubulares — AISC DG24 | Media |
| Conexión con plano inclinado | Para armaduras con pendiente | Baja |
| Verificación sísmica completa | AISC 341 + 358 — SMF/IMF/SCBF | Alta |
| Análisis de fatiga | AISC DG27 | Baja |
| Optimizador automático | Sugiere geometría óptima | Media |

---

## Setup de VS Code

### Extensiones necesarias

```
ritwickdey.LiveServer       ← Preview en vivo
esbenp.prettier-vscode      ← Formateo
dbaeumer.vscode-eslint      ← Linting JS
```

### Abrir el proyecto

```bash
mkdir SteelConn-Web && cd SteelConn-Web
code .
# Click derecho en index.html → Open with Live Server
# → http://127.0.0.1:5500
```

### Librerías JS (CDN)

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
```

---

*SteelConn — Documento Maestro v1.0 | Conexiones en acero · 7 módulos activos · 5 normas · HTML+CSS+JS*
