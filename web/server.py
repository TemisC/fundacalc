"""
FastAPI backend for FundaCalc web front-end.
Provides:
 - POST /api/calcular  -> runs calculation and returns JSON results
 - GET /api/plot/planta -> returns PNG of planta
 - GET /api/plot/seccion -> returns PNG of section
 - Serves static files from web/static
"""
import io
import sys
import hashlib
import os
import secrets
from typing import Optional
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, Response, FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tempfile

# ensure project root in path
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Cargar .env si existe ──────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    _env_path = ROOT / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv no instalado → usar variables de entorno del sistema

# ── Configuración de autenticación ────────────────────────────────────────────
_SECRET_KEY   = os.getenv("FUNDACALC_SECRET_KEY", "")
_ADMIN_USER   = os.getenv("FUNDACALC_USER", "admin")
_ADMIN_HASH   = os.getenv("FUNDACALC_PASS_HASH", "")
_AUTH_ENABLED = bool(_ADMIN_HASH)   # Si no hay hash, auth desactivada (dev)

if not _SECRET_KEY:
    _SECRET_KEY = secrets.token_hex(32)   # clave temporal por sesión

def _check_password(plain: str) -> bool:
    h = hashlib.sha256(plain.encode()).hexdigest()
    return h == _ADMIN_HASH

def _is_authenticated(request: Request) -> bool:
    if not _AUTH_ENABLED:
        return True
    from itsdangerous import TimestampSigner, BadSignature
    token = request.cookies.get("fc_session")
    if not token:
        return False
    try:
        signer = TimestampSigner(_SECRET_KEY)
        signer.unsign(token, max_age=28800)  # 8 horas
        return True
    except Exception:
        return False

def _make_session_token() -> str:
    from itsdangerous import TimestampSigner
    signer = TimestampSigner(_SECRET_KEY)
    return signer.sign(b"ok").decode()

# Rutas que NO requieren autenticación
_PUBLIC_PATHS = {"/login", "/api/login", "/favicon.ico"}

from core.zapata_aislada import (
    CargasColumna, Columna, Suelo,
    MaterialHormigon, MaterialAcero, GeometriaZapata, GeometriaPedestal,
    ZapataAislada, ResultadosZapata
)
from core.zapata_combinada import (
    ZapataCombinadaRectangular, ColCombinada, SueloCombinada, GeometriaCombi
)
from core.normas.aci318 import ACI318

# Unit conversion helper
class UnitConverter:
    # Conversion factors TO base units (kN for force, kN/m² for pressure)
    FORCE_TO_KN = {
        'kN': 1.0,
        'kip': 4.44822,
        'tf': 9.81,
        'lbf': 0.00444822,
        'ton': 9.81,  # tonelada métrica
        'kg': 0.00981,  # kilogramo
    }
    
    PRESSURE_TO_KN_M2 = {
        'kN/m²': 1.0,
        'kip/ft²': 47.88,
        'tf/m²': 9.81,
        'psf': 0.04788,
        'ton/m²': 9.81,  # tonelada métrica por m²
        'kg/m²': 0.00981,  # kilogramo por m²
    }
    
    @staticmethod
    def parse_units(unidades_str: str):
        """Parse 'kN_kN/m2' into (force_unit, pressure_unit)"""
        if '_' in unidades_str:
            force, pressure = unidades_str.split('_')
            force = force.replace('ft2', 'ft²').replace('m2', 'm²')
            pressure = pressure.replace('ft2', 'ft²').replace('m2', 'm²')
            return force, pressure
        return 'kN', 'kN/m²'
    
    @staticmethod
    def to_base(value: float, unit: str, unit_type: str) -> float:
        """Convert to base units (kN or kN/m²)"""
        if unit_type == 'force':
            return value * UnitConverter.FORCE_TO_KN.get(unit, 1.0)
        else:  # pressure
            return value * UnitConverter.PRESSURE_TO_KN_M2.get(unit, 1.0)
    
    @staticmethod
    def from_base(value: float, unit: str, unit_type: str) -> float:
        """Convert from base units to target unit"""
        if unit_type == 'force':
            conv = UnitConverter.FORCE_TO_KN.get(unit, 1.0)
        else:  # pressure
            conv = UnitConverter.PRESSURE_TO_KN_M2.get(unit, 1.0)
        return value / conv if conv != 0 else value
from core.normas.cirsoc201 import CIRSOC201
from core.normas.nch170 import NCh170
from core.normas.nsr10 import NSR10
from core.normas.nte_e060 import NTE_E060
from core.normas.ntc_cdmx import NTC_CDMX
from core.normas.ehe08 import EHE08
from core.normas.covenin1753 import COVENIN1753

from reportes.generador_pdf import GeneradorPDF
from reportes.generador_dxf import GeneradorDXF
from reportes.generador_dxf_combinada import GeneradorDXFCombinada
from reportes.generador_pdf_combinada import GeneradorPDFCombinada
from core.zapata_corrida import (
    ZapataCorridaRectangular, CargaMuro, MuroCorrida, SueloCorrida, GeometriaCorrida
)
from reportes.generador_pdf_corrida import GeneradorPDFCorrida
from reportes.generador_dxf_corrida import GeneradorDXFCorrida
from core.zapata_excentrica import (
    ZapataExcentricaRectangular, CargaExcentrica, ColumnaExcentrica,
    SueloExcentrica, GeometriaExcentrica,
)
from reportes.generador_pdf_excentrica import GeneradorPDFExcentrica
from reportes.generador_dxf_excentrica import GeneradorDXFExcentrica
from core.zapata_fachada import (
    ZapataFachadaRectangular, GeometriaFachada,
)
from reportes.generador_pdf_fachada import GeneradorPDFFachada
from reportes.generador_dxf_fachada import GeneradorDXFFachada
from reportes.generador_pdf_losa import GeneradorPDFLosa
from reportes.generador_dxf_losa import GeneradorDXFLosa
from reportes.generador_pdf_encepado import GeneradorPDFEncepado
from reportes.generador_dxf_encepado import GeneradorDXFEncepado
from reportes.generador_pdf_viga import GeneradorPDFViga
from reportes.generador_dxf_viga import GeneradorDXFViga
from core.capacidad_portante import CapacidadPortante, phi_desde_spt
from reportes.generador_pdf_capacidad import GeneradorPDFCapacidad
from core.muro_voladizo import MuroVoladizo
from reportes.generador_pdf_muro import GeneradorPDFMuro
from core.muro_gravedad import MuroGravedad
from reportes.generador_pdf_muro_gravedad import GeneradorPDFMuroGravedad
from core.muro_gaviones import MuroGaviones
from reportes.generador_pdf_muro_gaviones import GeneradorPDFMuroGaviones
from core.muro_contrafuertes import MuroContrafuertes
from reportes.generador_pdf_muro_contrafuertes import GeneradorPDFMuroContrafuertes
from core.muro_sotano import MuroSotano
from reportes.generador_pdf_muro_sotano import GeneradorPDFMuroSotano
from core.asentamientos import AsentamientoSchmertmann, AsentamientoTerzaghi
from reportes.generador_pdf_asentamientos import GeneradorPDFAsentamientos
from core.pilote_individual import PiloteIndividual
from reportes.generador_pdf_pilote import GeneradorPDFPilote
from reportes.generador_dxf_muros import (
    GeneradorDXFMuroGravedad, GeneradorDXFMuroGaviones,
    GeneradorDXFMuroContrafuertes, GeneradorDXFMuroSotano,
    GeneradorDXFMuroVoladizo,
)
from reportes.generador_dxf_pilote import GeneradorDXFPilote
from core.losa_fundacion import (
    LosaFundacion, SueloLosa, GeometriaLosa,
    CargaGlobal, CargaGrilla, CargaUniforme,
)
from core.encepado import (
    Encepado, CargaEncepado, ColumnaEncepado,
    PiloteConfig, GeometriaEncepado,
)
from core.viga_fundacion import (
    VigaFundacion, CargaColumna as CargaColumnaViga, SueloViga, GeometriaViga,
)

NORMAS_MAP = {
    "ACI318": ACI318,
    "CIRSOC201": CIRSOC201,
    "NCH170": NCh170,
    "NSR10": NSR10,
    "NTE_E060": NTE_E060,
    "NTC_CDMX": NTC_CDMX,
    "EHE08": EHE08,
    "COVENIN1753": COVENIN1753,
}

def _build_geometria(datos: "DatosEntrada") -> GeometriaZapata:
    geo = GeometriaZapata(h=datos.h, recubrimiento=datos.recubrimiento, cuadrada=datos.cuadrada)
    if datos.B_fijo and datos.L_fijo and datos.B_fijo > 0 and datos.L_fijo > 0:
        geo.B = datos.B_fijo
        geo.L = datos.L_fijo
        geo.dimensiones_fijas = True
        geo.cuadrada = False
    return geo

def _build_geo_pedestal(datos: "DatosEntrada") -> GeometriaPedestal:
    ped = GeometriaPedestal(hp=datos.hp)
    if datos.Bp_fijo and datos.Lp_fijo and datos.Bp_fijo > 0 and datos.Lp_fijo > 0:
        ped.Bp = datos.Bp_fijo
        ped.Lp = datos.Lp_fijo
    return ped

app = FastAPI(title="FundaCalc API")
app.mount("/static", StaticFiles(directory=str(ROOT / "web" / "static")), name="static")


# ── Middleware de autenticación ────────────────────────────────────────────────

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Protege todas las rutas excepto /login y /api/login."""
    path = request.url.path

    # Rutas públicas: login + assets estáticos
    if path in _PUBLIC_PATHS or path.startswith("/static/"):
        return await call_next(request)

    # Verificar sesión
    if not _is_authenticated(request):
        # Si es llamada AJAX/API → 401 JSON
        if path.startswith("/api/"):
            return JSONResponse({"error": "No autenticado"}, status_code=401)
        # Si es página HTML → redirigir al login
        return RedirectResponse(url="/login", status_code=302)

    response = await call_next(request)

    # Inyectar botón de logout en todas las páginas HTML
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type:
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        logout_btn = (
            b'<a href="/logout" style="'
            b'position:fixed;bottom:16px;right:16px;z-index:9999;'
            b'background:#21262d;border:1px solid #30363d;color:#8b949e;'
            b'font-size:11px;padding:5px 10px;border-radius:4px;'
            b'text-decoration:none;font-family:sans-serif;'
            b'opacity:0.7;transition:opacity 0.2s;" '
            b'onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7">'
            b'Cerrar sesi\xc3\xb3n</a>'
        )
        body = body.replace(b"</body>", logout_btn + b"</body>")
        return Response(
            content=body,
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items()
                     if k.lower() != "content-length"},
            media_type="text/html",
        )

    return response


# ── Rutas de autenticación ─────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return (ROOT / "web" / "static" / "login.html").read_text(encoding="utf-8")


@app.post("/api/login")
async def api_login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    if not _AUTH_ENABLED:
        return JSONResponse({"ok": True, "redirect": "/"})

    if username == _ADMIN_USER and _check_password(password):
        token = _make_session_token()
        resp = JSONResponse({"ok": True, "redirect": "/"})
        resp.set_cookie(
            key="fc_session",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=28800,   # 8 horas
            secure=False,    # cambiar a True si tienes HTTPS terminado en app (no Nginx)
        )
        return resp

    return JSONResponse({"ok": False, "error": "Credenciales incorrectas"}, status_code=401)


@app.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("fc_session")
    return resp

class DatosEntrada(BaseModel):
    Pd: float = 500.0
    Pl: float = 300.0
    Mxd: float = 0.0
    Mxl: float = 0.0
    Myd: float = 0.0
    Myl: float = 0.0
    col_ancho: float = 0.30
    col_largo: float = 0.30
    qa: float = 150.0
    Df: float = 1.2
    gamma_s: float = 18.0
    fck: float = 25.0
    fy: float = 420.0
    recubrimiento: float = 0.075
    h: float = 0.50
    cuadrada: bool = True
    norma: str = "ACI318"
    unidades: str = "kN_kN/m2"
    B_fijo: Optional[float] = None
    L_fijo: Optional[float] = None
    hp: float = 0.40
    Bp_fijo: Optional[float] = None
    Lp_fijo: Optional[float] = None
    varilla_pref: Optional[str] = ""


@app.get("/", response_class=HTMLResponse)
async def home():
    return (Path(ROOT / "web" / "static" / "home.html")).read_text(encoding="utf-8")

@app.get("/zapata", response_class=HTMLResponse)
async def zapata():
    return (Path(ROOT / "web" / "static" / "index.html")).read_text(encoding="utf-8")


@app.get("/verificacion", response_class=HTMLResponse)
async def verificacion():
    return (Path(ROOT / "web" / "static" / "verificacion.html")).read_text(encoding="utf-8")


@app.get("/verificacion-publicada", response_class=HTMLResponse)
async def verificacion_publicada():
    return (Path(ROOT / "web" / "static" / "verificacion_publicada.html")).read_text(encoding="utf-8")

@app.post("/api/calcular")
async def api_calcular(datos: DatosEntrada):
    # Parse units and convert input to base units
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    
    # Convert loads to kN (base)
    Pd_kN = UnitConverter.to_base(datos.Pd, force_unit, 'force')
    Pl_kN = UnitConverter.to_base(datos.Pl, force_unit, 'force')
    Mxd_kN = UnitConverter.to_base(datos.Mxd, force_unit, 'force')
    Mxl_kN = UnitConverter.to_base(datos.Mxl, force_unit, 'force')
    Myd_kN = UnitConverter.to_base(datos.Myd, force_unit, 'force')
    Myl_kN = UnitConverter.to_base(datos.Myl, force_unit, 'force')
    
    # Convert pressure to kN/m² (base)
    qa_kN_m2 = UnitConverter.to_base(datos.qa, pressure_unit, 'pressure')
    
    cargas = CargasColumna(Pd=Pd_kN, Pl=Pl_kN, Mxd=Mxd_kN, Mxl=Mxl_kN, Myd=Myd_kN, Myl=Myl_kN)
    columna = Columna(ancho=datos.col_ancho, largo=datos.col_largo)
    suelo = Suelo(qa=qa_kN_m2, Df=datos.Df, gamma_suelo=datos.gamma_s)
    hormigon = MaterialHormigon(fck=datos.fck)
    acero = MaterialAcero(fy=datos.fy)
    geometria = _build_geometria(datos)
    geo_ped = _build_geo_pedestal(datos)

    norma_cls = NORMAS_MAP.get(datos.norma, ACI318)
    norma = norma_cls()

    motor = ZapataAislada(cargas, columna, suelo, hormigon, acero, norma, geometria, geo_ped)
    resultado = motor.calcular()

    if resultado.q_neto <= 0:
        error_msgs = [m["texto"] for m in resultado.mensajes if m["tipo"] == "error"]
        msg = error_msgs[0] if error_msgs else "Presión neta del suelo ≤ 0. Verifique qa, Df y γ suelo."
        return JSONResponse({"error": msg}, status_code=422)

    # Convert results back to selected units
    def res_to_dict(res: ResultadosZapata):
        d = res.__dict__.copy()
        # Convert force-related results
        d['Vu_punz'] = UnitConverter.from_base(d['Vu_punz'], force_unit, 'force')
        d['phi_Vn_punz'] = UnitConverter.from_base(d['phi_Vn_punz'], force_unit, 'force')
        d['Vu_cort'] = UnitConverter.from_base(d['Vu_cort'], force_unit, 'force')
        d['phi_Vn_cort'] = UnitConverter.from_base(d['phi_Vn_cort'], force_unit, 'force')
        d['Mu_x'] = UnitConverter.from_base(d['Mu_x'], force_unit, 'force')
        d['Mu_y'] = UnitConverter.from_base(d['Mu_y'], force_unit, 'force')
        # Convert pressure-related results
        d['q_neto'] = UnitConverter.from_base(d['q_neto'], pressure_unit, 'pressure')
        d['q_max'] = UnitConverter.from_base(d['q_max'], pressure_unit, 'pressure')
        d['q_min'] = UnitConverter.from_base(d['q_min'], pressure_unit, 'pressure')
        d['q_ultima'] = UnitConverter.from_base(d['q_ultima'], pressure_unit, 'pressure')
        return d

    ped_res = motor.resultados_pedestal
    return JSONResponse({
        "resultado": res_to_dict(resultado),
        "geometria": vars(motor.geo),
        "columna": vars(columna),
        "unidades": {"cargas": force_unit, "presiones": pressure_unit},
        "pedestal": vars(ped_res) if ped_res else None,
        "geo_pedestal": vars(motor.geo_pedestal) if ped_res else None,
    })


def _dibujar_planta_bytes(geo, col, res):
    import numpy as np
    import matplotlib.colors as mcolors

    B, L   = geo.B, geo.L
    c1, c2 = col.ancho, col.largo
    q_max  = getattr(res, 'q_max', None) or 100.0
    q_min  = max(getattr(res, 'q_min', 0.0) or 0.0, 0.0)
    d      = getattr(geo, 'd', 0.0) or 0.0

    fig, ax = plt.subplots(figsize=(7, 7), facecolor='#0a1929')
    ax.set_facecolor('#0a1929')

    eccentric = (q_max - q_min) / max(q_max, 1.0) > 0.05

    if eccentric:
        # ── Heatmap de presión (carga excéntrica) ─────────────────────────────
        _nx = _ny = 80
        x_arr = np.linspace(-B/2, B/2, _nx)
        y_arr = np.linspace(-L/2, L/2, _ny)
        XX, YY = np.meshgrid(x_arr, y_arr)
        q_med = (q_max + q_min) / 2
        ZZ = q_med + (q_max - q_med) * (XX / (B / 2) + YY / (L / 2)) / 2
        ZZ = np.clip(ZZ, 0.0, None)
        cmap = plt.colormaps['YlOrRd']
        pcm  = ax.pcolormesh(XX, YY, ZZ, cmap=cmap, zorder=2,
                             vmin=0.0, vmax=max(q_max, 1.0))
        ax.add_patch(plt.Rectangle((-B/2, -L/2), B, L,
                     facecolor='none', edgecolor='#378ADD', lw=2.0, zorder=4))
        # Colorbar
        cbar = fig.colorbar(pcm, ax=ax, fraction=0.04, pad=0.02, aspect=25)
        cbar.set_label('Presión del suelo [kN/m²]', color='#85B7EB', fontsize=9)
        cbar.ax.yaxis.set_tick_params(color='#85B7EB')
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#85B7EB', fontsize=8)
        cbar.outline.set_edgecolor('#378ADD')
        # Etiquetas de esquina
        ax.text(-B/2 + B*0.03, -L/2 + L*0.03, f"{q_min:.0f} kN/m²",
                ha='left', va='bottom', fontsize=8.5, color='white', fontweight='bold', zorder=8)
        ax.text(B/2 - B*0.03, L/2 - L*0.03, f"{q_max:.0f} kN/m²",
                ha='right', va='top', fontsize=8.5, color='white', fontweight='bold', zorder=8)
    else:
        # ── Carga uniforme: color sólido en planta (top-down view) ────────────
        # La presión uniforme se muestra como un relleno de color cálido sobre
        # toda la huella de la zapata. Las flechas de reacción van en la sección.
        _nx = _ny = 60
        x_arr = np.linspace(-B/2, B/2, _nx)
        y_arr = np.linspace(-L/2, L/2, _ny)
        XX, YY = np.meshgrid(x_arr, y_arr)
        ZZ = np.full_like(XX, q_max)
        cmap = plt.colormaps['YlOrRd']
        pcm  = ax.pcolormesh(XX, YY, ZZ, cmap=cmap, zorder=2,
                             vmin=0.0, vmax=max(q_max * 1.5, 1.0))
        ax.add_patch(plt.Rectangle((-B/2, -L/2), B, L,
                     facecolor='none', edgecolor='#378ADD', lw=2.0, zorder=4))
        cbar = fig.colorbar(pcm, ax=ax, fraction=0.04, pad=0.02, aspect=25)
        cbar.set_label('Presión del suelo [kN/m²]', color='#85B7EB', fontsize=9)
        cbar.ax.yaxis.set_tick_params(color='#85B7EB')
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#85B7EB', fontsize=8)
        cbar.outline.set_edgecolor('#378ADD')
        ax.text(0, 0, f"q = {q_max:.0f} kN/m²\n(uniforme)",
                ha='center', va='center', fontsize=11, color='white',
                fontweight='bold', zorder=8,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0a1929',
                          alpha=0.65, edgecolor='none'))

    # ── Punching perimeter (d/2 from column face) ─────────────────────────────
    if d > 0:
        ax.add_patch(plt.Rectangle(
            (-(c1 + d) / 2, -(c2 + d) / 2), c1 + d, c2 + d,
            facecolor='none', edgecolor='#EF5350', lw=1.0, ls='--', zorder=5))
        # Etiqueta fuera de la zapata (arriba a la derecha del perímetro)
        ax.text((c1 + d) / 2 + B*0.03, (c2 + d) / 2 + L*0.03,
                "perim. punz.", ha='left', va='bottom',
                fontsize=7.5, color='#EF5350', zorder=8)

    # ── Column ────────────────────────────────────────────────────────────────
    ax.add_patch(plt.Rectangle((-c1/2, -c2/2), c1, c2,
                 facecolor='#546E7A', edgecolor='#90A4AE', lw=1.2, zorder=6))

    # ── Dimension lines ───────────────────────────────────────────────────────
    dim_offset = 0.15 * max(B, L)
    y_dim = -L/2 - dim_offset * 0.60
    ax.annotate('', xy=(B/2, y_dim), xytext=(-B/2, y_dim),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ax.text(0, y_dim - dim_offset * 0.12, f"B = {B:.2f} m",
            ha='center', va='top', fontsize=11, color='#85B7EB', fontweight='bold')

    x_dim = B/2 + dim_offset * 0.60
    ax.annotate('', xy=(x_dim, L/2), xytext=(x_dim, -L/2),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ax.text(x_dim + dim_offset * 0.12, 0, f"L = {L:.2f} m",
            ha='left', va='center', fontsize=11, color='#85B7EB',
            fontweight='bold', rotation=90)

    ax.set_xlim(-B/2 - dim_offset, B/2 + dim_offset * 2.2)
    ax.set_ylim(-L/2 - dim_offset * 0.7, L/2 + dim_offset * 0.4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Vista en Planta — Presión del Suelo", color='#85B7EB', fontsize=11, pad=8)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=130,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _build_motor(datos: "DatosEntrada"):
    """Build a fully calculated ZapataAislada motor with proper unit conversion."""
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    Pd_kN = UnitConverter.to_base(datos.Pd, force_unit, 'force')
    Pl_kN = UnitConverter.to_base(datos.Pl, force_unit, 'force')
    Mxd_kN = UnitConverter.to_base(datos.Mxd, force_unit, 'force')
    Mxl_kN = UnitConverter.to_base(datos.Mxl, force_unit, 'force')
    Myd_kN = UnitConverter.to_base(datos.Myd, force_unit, 'force')
    Myl_kN = UnitConverter.to_base(datos.Myl, force_unit, 'force')
    qa_kN_m2 = UnitConverter.to_base(datos.qa, pressure_unit, 'pressure')
    cargas = CargasColumna(Pd=Pd_kN, Pl=Pl_kN, Mxd=Mxd_kN, Mxl=Mxl_kN, Myd=Myd_kN, Myl=Myl_kN)
    columna = Columna(ancho=datos.col_ancho, largo=datos.col_largo)
    suelo = Suelo(qa=qa_kN_m2, Df=datos.Df, gamma_suelo=datos.gamma_s)
    hormigon = MaterialHormigon(fck=datos.fck)
    acero = MaterialAcero(fy=datos.fy)
    geometria = _build_geometria(datos)
    geo_ped = _build_geo_pedestal(datos)
    norma_cls = NORMAS_MAP.get(datos.norma, ACI318)
    norma = norma_cls()
    motor = ZapataAislada(cargas, columna, suelo, hormigon, acero, norma, geometria, geo_ped,
                          varilla_pref=datos.varilla_pref or "")
    motor.calcular()
    return motor


@app.post("/api/plot/planta")
async def api_plot_planta(datos: DatosEntrada):
    motor = _build_motor(datos)
    buf = _dibujar_planta_bytes(motor.geo, motor.columna, motor.resultados)
    return Response(content=buf.getvalue(), media_type='image/png')

def _dibujar_seccion_bytes(motor) -> io.BytesIO:
    """Render two-panel section drawing and return PNG bytes."""
    import numpy as np
    B    = motor.geo.B or 1.0
    h    = motor.geo.h
    ped  = motor.geo_pedestal
    Bp   = ped.Bp if ped.Bp > 0 else motor.columna.ancho + 0.20
    hp   = ped.hp
    c1   = motor.columna.ancho
    recub = motor.geo.recubrimiento
    res  = motor.resultados
    ped_res = motor.resultados_pedestal

    col_stub_h = hp * 0.5
    total_h    = h + hp + col_stub_h
    ref = max(B, total_h * 2.2)
    dim_offset = 0.13 * ref
    tick       = 0.032 * ref
    FONT       = 10

    fig = plt.figure(figsize=(16, 7), facecolor='#0a1929')
    ax   = fig.add_axes([0.01, 0.04, 0.46, 0.92])
    ax_t = fig.add_axes([0.50, 0.04, 0.48, 0.92])
    ax.set_facecolor('#0a1929')
    ax_t.set_facecolor('#0a1929')
    ax_t.axis('off')

    ax.add_patch(plt.Rectangle((-B/2, 0),      B,  h,          facecolor='#142233', edgecolor='#378ADD', lw=1.5))
    ax.add_patch(plt.Rectangle((-Bp/2, h),     Bp, hp,         facecolor='#1a3a5c', edgecolor='#378ADD', lw=1.2))
    ax.add_patch(plt.Rectangle((-c1/2, h+hp),  c1, col_stub_h, facecolor='#546E7A', edgecolor='#90A4AE', lw=1.2))

    sep_x = res.separacion_x or 0.15
    db_m  = 0.016
    y_X   = recub + db_m / 2
    y_Y   = recub + db_m * 1.5
    n_b   = min(14, max(6, round((B - 2*recub) / sep_x) + 1))
    xs    = [-B/2 + recub + i*(B - 2*recub)/(n_b-1) for i in range(n_b)]

    ax.plot([-B/2+recub, B/2-recub], [y_X, y_X], color='#EF5350', lw=2.0, zorder=5)
    for xb in xs:
        ax.add_patch(plt.Circle((xb, y_X), db_m*0.85, color='#EF5350', zorder=6))
    ax.plot([-B/2+recub, B/2-recub], [y_Y, y_Y], color='#AB47BC', lw=2.0, ls='--', zorder=5)
    for xb in xs:
        ax.add_patch(plt.Circle((xb, y_Y), db_m*0.85, color='#AB47BC', zorder=6))

    ax.annotate('', xy=(-B/2+recub*0.05, 0), xytext=(-B/2+recub*0.05, recub),
                arrowprops=dict(arrowstyle='<->', color='#8899AA', lw=0.8))
    ax.text(-B/2+recub*0.1, recub/2, f"r={recub*100:.0f}cm",
            ha='left', va='center', fontsize=8.5, color='#8899AA')

    # ── Reacción del suelo: flechas hacia arriba bajo la zapata ──────────────
    q_max_s = getattr(res, 'q_max', None) or 100.0
    q_min_s = max(getattr(res, 'q_min', 0.0) or 0.0, 0.0)
    qa_s    = getattr(motor.suelo, 'qa', None) or q_max_s
    arrow_h = h * 0.38
    y_base  = -arrow_h
    n_arr   = max(5, min(12, int(B / 0.35)))
    eccentric_s = (q_max_s - q_min_s) / max(q_max_s, 1.0) > 0.05
    xs_arr  = np.linspace(-B/2 + B*0.05, B/2 - B*0.05, n_arr)
    arr_col = '#EF9F27'
    if eccentric_s:
        # altura proporcional a la presión en cada punto (trapecio)
        qs_arr = np.linspace(q_min_s, q_max_s, n_arr)
        y_tails = y_base * (qs_arr / max(q_max_s, 1.0))
    else:
        y_tails = [y_base] * n_arr
    for xa, yt in zip(xs_arr, y_tails):
        ax.annotate('', xy=(xa, 0), xytext=(xa, yt),
                    arrowprops=dict(arrowstyle='->', color=arr_col,
                                    lw=1.3, mutation_scale=11))
    ax.plot([-B/2, B/2], [y_base, y_base if not eccentric_s else y_tails[0]],
            color=arr_col, lw=1.2)
    if eccentric_s:
        ax.plot([-B/2, B/2], [y_tails[0], y_tails[-1]], color=arr_col, lw=1.2)
    # Etiqueta con valor y verificación vs qa
    ok_color = '#66BB6A' if q_max_s <= qa_s else '#EF5350'
    ok_sym   = '✔' if q_max_s <= qa_s else '✘'
    label_q  = (f"q = {q_max_s:.0f} kN/m²  {ok_sym}  qa = {qa_s:.0f} kN/m²"
                if not eccentric_s else
                f"q_max = {q_max_s:.0f} | q_min = {q_min_s:.0f} kN/m²  {ok_sym}  qa = {qa_s:.0f}")
    ax.text(0, y_base - h*0.06, label_q,
            ha='center', va='top', fontsize=9, color=ok_color, fontweight='bold')

    x_dim  = B/2 + dim_offset
    x_dim2 = x_dim + 0.36*ref
    for xd, y0, y1, lbl in [
        (x_dim,  0, h,    f"h={h:.2f} m"),
        (x_dim2, h, h+hp, f"hp={hp:.2f} m"),
    ]:
        ax.plot([xd, xd], [y0, y1], color='#85B7EB', lw=1.0)
        ax.plot([xd-tick, xd], [y0, y0], color='#85B7EB', lw=1.0)
        ax.plot([xd-tick, xd], [y1, y1], color='#85B7EB', lw=1.0)
        ax.annotate(lbl, xy=(xd+0.01*ref, (y0+y1)/2),
                    ha='left', va='center', fontsize=FONT+1, fontweight='bold',
                    color='white')

    ax.set_xlim(-B/2 - 0.08*ref, x_dim2 + 0.45*ref)
    ax.set_ylim(-h * 0.52, total_h + 0.12)
    ax.set_aspect('equal')
    ax.axis('off')

    _AZUL = '#42A5F5'
    _ROJO = '#EF5350'
    _PURP = '#AB47BC'
    _GR   = '#66BB6A'
    _FONT_MONO = 'DejaVu Sans Mono'
    _FONT_SANS = 'DejaVu Sans'
    TS = 13.5; HS = 12.0; VS = 11.5
    DT = 0.048; DH = 0.055; DV = 0.050; DG = 0.065

    def oline(y, txt, color='white', size=VS, bold=False, mono=False):
        ax_t.text(0.03, y, txt, transform=ax_t.transAxes,
                  fontsize=size, color=color,
                  fontweight='bold' if bold else 'normal',
                  va='top', fontfamily=_FONT_MONO if mono else _FONT_SANS)

    def hline(y, color=_AZUL):
        ax_t.axhline(y + 0.018, xmin=0.01, xmax=0.99, color=color, lw=1.0)

    def _phi(s):
        return (s or '').replace('Ø', '(Diam.) ')

    sep_x_cm = (res.separacion_x or 0)*100
    sep_y_cm = (res.separacion_y or 0)*100
    var_x = _phi(res.varilla_x)
    var_y = _phi(res.varilla_y)

    y = 0.97
    oline(y, 'ARMADURA INFERIOR — ZAPATA', _AZUL, TS, bold=True); y -= DT
    hline(y); y -= 0.022

    oline(y, 'Eje X  (paralelo a B):', _ROJO, HS, bold=True); y -= DH
    oline(y, f'  Varilla :  {var_x}',                      mono=True); y -= DV
    oline(y, f'  Separac.:  @ {sep_x_cm:.0f} cm',          mono=True); y -= DV
    oline(y, f'  As      :  {res.As_x_diseno:.2f} cm2/m',  mono=True); y -= DG

    oline(y, 'Eje Y  (paralelo a L):', _PURP, HS, bold=True); y -= DH
    oline(y, f'  Varilla :  {var_y}',                      mono=True); y -= DV
    oline(y, f'  Separac.:  @ {sep_y_cm:.0f} cm',          mono=True); y -= DV
    oline(y, f'  As      :  {res.As_y_diseno:.2f} cm2/m',  mono=True); y -= DG

    if ped_res:
        hline(y); y -= 0.022
        oline(y, 'PEDESTAL', _AZUL, TS, bold=True); y -= DT
        vl  = _phi(ped_res.varilla_long)
        ve  = _phi(ped_res.varilla_estribo)
        vep = _phi(ped_res.varilla_espera)
        oline(y, 'Long.:',    _GR, HS, bold=True); y -= DH
        oline(y, f'  {ped_res.n_barras} x {vl}  (As = {ped_res.As_diseno:.2f} cm2)', mono=True); y -= DG
        oline(y, 'Estribos:', _GR, HS, bold=True); y -= DH
        oline(y, f'  {ve} @ {ped_res.separacion_estribo*100:.0f} cm', mono=True); y -= DG
        oline(y, 'Esperas:',  _GR, HS, bold=True); y -= DH
        oline(y, f'  {ped_res.n_esperas} x {vep}', mono=True); y -= DV
        oline(y, f'  ld_comp = {ped_res.ld_espera_comp*100:.0f} cm', mono=True)

    fig.add_artist(plt.Line2D([0.495, 0.495], [0.04, 0.96],
                              transform=fig.transFigure, color='#2a4060', lw=1.2))

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=130,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _dibujar_seccion_solo_bytes(motor) -> io.BytesIO:
    """Render only the structural cross-section drawing (no text panel) — for PDF."""
    B     = motor.geo.B or 1.0
    h     = motor.geo.h
    ped   = motor.geo_pedestal
    Bp    = ped.Bp if ped.Bp > 0 else motor.columna.ancho + 0.20
    hp    = ped.hp
    c1    = motor.columna.ancho
    recub = motor.geo.recubrimiento
    res   = motor.resultados

    col_stub_h = hp * 0.5
    total_h    = h + hp + col_stub_h
    ref        = max(B, total_h * 2.2)
    dim_offset = 0.12 * ref
    tick       = 0.030 * ref

    fig, ax = plt.subplots(figsize=(12, 5), facecolor='#0a1929')
    ax.set_facecolor('#0a1929')
    ax.set_aspect('equal')
    ax.axis('off')

    ax.add_patch(plt.Rectangle((-B/2, 0),      B,  h,           facecolor='#142233', edgecolor='#378ADD', lw=1.5))
    ax.add_patch(plt.Rectangle((-Bp/2, h),    Bp,  hp,          facecolor='#1a3a5c', edgecolor='#378ADD', lw=1.2))
    ax.add_patch(plt.Rectangle((-c1/2, h+hp), c1,  col_stub_h,  facecolor='#546E7A', edgecolor='#90A4AE', lw=1.2))

    sep_x = res.separacion_x or 0.15
    db_m  = 0.016
    y_X   = recub + db_m / 2
    y_Y   = recub + db_m * 1.5
    n_b   = min(14, max(6, round((B - 2*recub) / sep_x) + 1))
    xs    = [-B/2 + recub + i*(B - 2*recub)/(n_b-1) for i in range(n_b)]

    ax.plot([-B/2+recub, B/2-recub], [y_X, y_X], color='#EF5350', lw=2.0, zorder=5)
    for xb in xs:
        ax.add_patch(plt.Circle((xb, y_X), db_m*0.85, color='#EF5350', zorder=6))
    ax.plot([-B/2+recub, B/2-recub], [y_Y, y_Y], color='#AB47BC', lw=2.0, ls='--', zorder=5)
    for xb in xs:
        ax.add_patch(plt.Circle((xb, y_Y), db_m*0.85, color='#AB47BC', zorder=6))

    ax.annotate('', xy=(-B/2+recub*0.05, 0), xytext=(-B/2+recub*0.05, recub),
                arrowprops=dict(arrowstyle='<->', color='#8899AA', lw=0.8))
    ax.text(-B/2+recub*0.1, recub/2, f"r={recub*100:.0f}cm",
            ha='left', va='center', fontsize=8, color='#8899AA')

    x_dim  = B/2 + dim_offset
    x_dim2 = x_dim + 0.32*ref
    for xd, y0, y1, lbl in [
        (x_dim,  0, h,    f"h={h:.2f} m"),
        (x_dim2, h, h+hp, f"hp={hp:.2f} m"),
    ]:
        ax.plot([xd, xd],      [y0, y1], color='#85B7EB', lw=1.0)
        ax.plot([xd-tick, xd], [y0, y0], color='#85B7EB', lw=1.0)
        ax.plot([xd-tick, xd], [y1, y1], color='#85B7EB', lw=1.0)
        ax.annotate(lbl, xy=(xd+0.01*ref, (y0+y1)/2),
                    ha='left', va='center', fontsize=11, fontweight='bold', color='white')

    ax.set_xlim(-B/2 - 0.06*ref, x_dim2 + 0.42*ref)
    ax.set_ylim(-0.08, total_h + 0.10)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


@app.post("/api/plot/seccion")
async def api_plot_seccion(datos: DatosEntrada):
    motor = _build_motor(datos)
    buf = _dibujar_seccion_bytes(motor)
    return Response(content=buf.getvalue(), media_type='image/png')


@app.post("/api/report/pdf")
async def api_report_pdf(datos: DatosEntrada):
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    motor = _build_motor(datos)
    resultado = motor.resultados

    gen = GeneradorPDF()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp.close()
    img_planta_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img_planta_tmp.close()
    img_seccion_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img_seccion_tmp.close()

    buf_planta = _dibujar_planta_bytes(motor.geo, motor.columna, resultado)
    with open(img_planta_tmp.name, 'wb') as f:
        f.write(buf_planta.getvalue())
    buf_seccion = _dibujar_seccion_solo_bytes(motor)
    with open(img_seccion_tmp.name, 'wb') as f:
        f.write(buf_seccion.getvalue())

    from types import SimpleNamespace
    cargas_pdf = SimpleNamespace(
        Pd=datos.Pd, Pl=datos.Pl,
        Pu=motor.cargas.Pu,
    )
    suelo_pdf = SimpleNamespace(
        qa=datos.qa, Df=datos.Df, gamma_suelo=datos.gamma_s,
    )
    datos_para_pdf = {
        "cargas": cargas_pdf,
        "columna": motor.columna,
        "suelo": suelo_pdf,
        "hormigon": motor.hormigon,
        "acero": motor.acero,
        "geometria": motor.geo,
        "norma": datos.norma,
        "unidades": {"cargas": force_unit, "presiones": pressure_unit},
        "ped_res": motor.resultados_pedestal,
    }
    try:
        gen.generar(tmp.name, resultado, datos_para_pdf,
                    imagen_planta=img_planta_tmp.name,
                    imagen_seccion=img_seccion_tmp.name)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="memoria_zapata.pdf"'},
        )
    finally:
        for p in (tmp.name, img_planta_tmp.name, img_seccion_tmp.name):
            try:
                os.unlink(p)
            except Exception:
                pass


@app.post("/api/report/dxf")
async def api_report_dxf(datos: DatosEntrada):
    motor = _build_motor(datos)

    gen = GeneradorDXF()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
    tmp.close()
    try:
        gen.generar(tmp.name, motor.geo, motor.columna, motor.resultados, datos.norma)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes,
            media_type='application/dxf',
            headers={'Content-Disposition': 'attachment; filename="dibujo_zapata.dxf"'},
        )
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


# ─── Module 2: Zapata Combinada ──────────────────────────────────────────────

class DatosCombinadaEntrada(BaseModel):
    Pd1: float = 500.0;  Pl1: float = 300.0
    col1_ancho: float = 0.35;  col1_largo: float = 0.35
    Pd2: float = 400.0;  Pl2: float = 250.0
    col2_ancho: float = 0.35;  col2_largo: float = 0.35
    qa: float = 150.0;  Df: float = 1.20;  gamma_s: float = 18.0
    fck: float = 25.0;  fy: float = 420.0
    L_entre: float = 4.0
    B_fijo: float = 0.0
    h: float = 0.60
    recubrimiento: float = 0.075
    col1_en_borde: bool = True
    norma: str = "ACI318"
    unidades: str = "kN_kN/m2"
    varilla_pref: Optional[str] = ""


def _build_motor_combinada(datos: DatosCombinadaEntrada) -> ZapataCombinadaRectangular:
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    col1 = ColCombinada(
        Pd=UnitConverter.to_base(datos.Pd1, force_unit, 'force'),
        Pl=UnitConverter.to_base(datos.Pl1, force_unit, 'force'),
        ancho=datos.col1_ancho, largo=datos.col1_largo,
    )
    col2 = ColCombinada(
        Pd=UnitConverter.to_base(datos.Pd2, force_unit, 'force'),
        Pl=UnitConverter.to_base(datos.Pl2, force_unit, 'force'),
        ancho=datos.col2_ancho, largo=datos.col2_largo,
    )
    suelo = SueloCombinada(
        qa=UnitConverter.to_base(datos.qa, pressure_unit, 'pressure'),
        Df=datos.Df, gamma_suelo=datos.gamma_s,
    )
    hormigon = MaterialHormigon(fck=datos.fck)
    acero = MaterialAcero(fy=datos.fy)
    geo = GeometriaCombi(
        L_entre=datos.L_entre, B_fijo=datos.B_fijo,
        h=datos.h, recubrimiento=datos.recubrimiento,
        col1_en_borde=datos.col1_en_borde,
    )
    norma_cls = NORMAS_MAP.get(datos.norma, ACI318)
    norma = norma_cls()
    motor = ZapataCombinadaRectangular(col1, col2, suelo, hormigon, acero, norma, geo,
                                       varilla_pref=datos.varilla_pref or "")
    motor.calcular()
    return motor


def _dibujar_planta_combinada_bytes(motor: ZapataCombinadaRectangular) -> io.BytesIO:
    import matplotlib.patches as mpatches
    res = motor.res
    col1, col2 = motor.col1, motor.col2
    d = motor.geo.d
    B, L, d1, d2 = res.B, res.L, res.d1, res.d2

    pad = max(B, L) * 0.20          # uniform padding
    lbl_gap = pad * 0.55            # gap above footing for column labels

    # axis limits
    x_lo = -(pad * 1.3)            # extra room on left for B dimension
    x_hi = L + pad * 0.55
    y_lo = -(pad * 1.0)            # room below for L dimension
    y_hi = B + lbl_gap + pad * 0.3  # room above for labels

    # figure size proportional to data extent (equal-aspect aware)
    data_w = x_hi - x_lo
    data_h = y_hi - y_lo
    fig_w = 9.0
    fig_h = max(4.0, fig_w * data_h / data_w)
    import numpy as np
    import matplotlib.colors as mcolors

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor='#0a1929')
    ax.set_facecolor('#0a1929')

    # ── Pressure heatmap on footing ──
    q_max_v = getattr(res, 'q_max', None) or 100.0
    _nx = _ny = 80
    x_arr = np.linspace(0, L, _nx)
    y_arr = np.linspace(0, B, _ny)
    XX, YY = np.meshgrid(x_arr, y_arr)
    ZZ = np.full_like(XX, q_max_v)   # combinada: uniform pressure
    cmap_f = plt.colormaps['YlOrRd']
    pcm = ax.pcolormesh(XX, YY, ZZ, cmap=cmap_f, zorder=1,
                        vmin=0.0, vmax=max(q_max_v, 1.0), alpha=0.75)
    ax.add_patch(plt.Rectangle((0, 0), L, B,
                                facecolor='none', edgecolor='#378ADD', lw=1.8, zorder=2))

    # ── Columns & punching perimeters ──
    col_colors = ['#546E7A', '#37474F']
    for (xc, col, fc) in [(d1, col1, col_colors[0]), (d2, col2, col_colors[1])]:
        ax.add_patch(plt.Rectangle(
            (xc - col.ancho / 2, B / 2 - col.largo / 2), col.ancho, col.largo,
            facecolor=fc, edgecolor='#90A4AE', lw=1.2, zorder=5))
        ax.add_patch(plt.Rectangle(
            (xc - (col.ancho + d) / 2, B / 2 - (col.largo + d) / 2),
            col.ancho + d, col.largo + d,
            fill=False, edgecolor='#EF5350', lw=0.9, ls='--', zorder=6))

    # ── Column labels ──
    for xc, name, col in [(d1, "Col1", col1), (d2, "Col2", col2)]:
        if xc < L * 0.25:
            ha, txt_x = 'left', max(xc, 0.0)
        elif xc > L * 0.75:
            ha, txt_x = 'right', min(xc, L)
        else:
            ha, txt_x = 'center', xc
        ax.text(txt_x, B + lbl_gap * 0.15,
                f"{name}  {col.ancho*100:.0f}×{col.largo*100:.0f} cm",
                ha=ha, va='bottom', fontsize=9.5, fontweight='bold', color='#85B7EB')
        ax.plot([xc, xc], [B, B + lbl_gap * 0.12],
                color='#85B7EB', lw=0.7, ls='-', alpha=0.5)

    # ── Dimension L (below footing) ──
    y_dim = -pad * 0.55
    ax.annotate('', xy=(L, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ax.plot([0, 0], [y_dim, 0], color='#378ADD', lw=0.5, ls=':')
    ax.plot([L, L], [y_dim, 0], color='#378ADD', lw=0.5, ls=':')
    ax.text(L / 2, y_dim - pad * 0.14, f"L = {L:.2f} m",
            ha='center', va='top', fontsize=11, fontweight='bold', color='#85B7EB')

    # ── Dimension B (left of footing) ──
    x_dim = -pad * 0.75
    ax.annotate('', xy=(x_dim, B), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ax.plot([x_dim, 0], [0, 0], color='#378ADD', lw=0.5, ls=':')
    ax.plot([x_dim, 0], [B, B], color='#378ADD', lw=0.5, ls=':')
    ax.text(x_dim - pad * 0.10, B / 2, f"B = {B:.2f} m",
            ha='right', va='center', fontsize=11, fontweight='bold', color='#85B7EB', rotation=90)

    # ── Colorbar ──
    cbar = fig.colorbar(pcm, ax=ax, fraction=0.035, pad=0.03, aspect=22)
    cbar.set_label('Presión [kN/m²]', color='#85B7EB', fontsize=8)
    cbar.ax.yaxis.set_tick_params(color='#85B7EB')
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#85B7EB', fontsize=7.5)
    cbar.outline.set_edgecolor('#378ADD')

    # ── Column centerlines ──
    for xc in [d1, d2]:
        ax.plot([xc, xc], [0, B], color='#378ADD', lw=0.6, ls=':', alpha=0.45, zorder=3)

    # ── Legend ──
    handles = [
        mpatches.Patch(facecolor='#546E7A', edgecolor='#90A4AE', label="Columnas"),
        mpatches.Patch(fill=False, edgecolor='#EF5350', ls='--',
                       label=f"Perim. punzonado (d/2 = {d/2:.2f} m)"),
    ]
    legend = ax.legend(handles=handles, loc='lower right', fontsize=8.5)
    legend.get_frame().set_facecolor('#0a1929')
    legend.get_frame().set_edgecolor('#378ADD')
    for text in legend.get_texts():
        text.set_color('white')

    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)
    ax.set_aspect('equal')
    ax.axis('off')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _dibujar_seccion_long_combinada_bytes(motor: ZapataCombinadaRectangular) -> io.BytesIO:
    """Longitudinal section (along L axis) of combined footing with soil pressure arrows."""
    import numpy as np
    res  = motor.res
    col1, col2 = motor.col1, motor.col2
    B, L, h = res.B, res.L, res.h
    d1, d2  = res.d1, res.d2
    q_max   = getattr(res, 'q_max', None) or 100.0
    qa      = getattr(motor.suelo, 'qa', None) or q_max

    # Column heights for visual stub
    col_h = h * 0.55

    pad        = max(L, h * 4) * 0.12
    dim_offset = pad * 0.55
    arrow_h    = h * 0.55
    y_base     = -arrow_h

    fig, ax = plt.subplots(figsize=(13, 5), facecolor='#0a1929')
    ax.set_facecolor('#0a1929')

    # ── Footing body ──────────────────────────────────────────────────────────
    ax.add_patch(plt.Rectangle((0, 0), L, h,
                 facecolor='#142233', edgecolor='#378ADD', lw=1.8, zorder=3))

    # ── Column stubs ──────────────────────────────────────────────────────────
    for xc, col in [(d1, col1), (d2, col2)]:
        ax.add_patch(plt.Rectangle(
            (xc - col.ancho/2, h), col.ancho, col_h,
            facecolor='#546E7A', edgecolor='#90A4AE', lw=1.2, zorder=4))
        ax.text(xc, h + col_h + pad*0.08,
                f"{col.ancho*100:.0f}×{col.largo*100:.0f} cm",
                ha='center', va='bottom', fontsize=9, color='#85B7EB')

    # ── Rebar indication at bottom ─────────────────────────────────────────────
    recub = getattr(motor.geo, 'recubrimiento', 0.07)
    ax.plot([recub, L - recub], [recub, recub],
            color='#EF5350', lw=2.2, zorder=5)
    ax.plot([recub, L - recub], [recub + 0.016, recub + 0.016],
            color='#AB47BC', lw=2.0, ls='--', zorder=5)

    # ── Soil pressure diagram ────────────────────────────────────────────────
    q_min    = getattr(res, 'q_min', 0.0)
    a_efect  = getattr(res, 'a_efectiva', L) or L
    uniforme = getattr(res, 'presion_uniforme', True)
    arr_col  = '#EF9F27'

    n_arr = max(7, min(20, int(L / 0.28)))

    if a_efect >= L - 0.01:
        # Trapezoidal o uniforme: flechas proporcionales a la presión en cada x
        xs_arr = np.linspace(L*0.025, L*0.975, n_arr)
        for xa in xs_arr:
            # Interpolar presión en xa: q_left en x=0, q_right en x=L
            # Si e>0 (heavy left): q_max en x=0, q_min en x=L
            # Determinamos dirección por comparación de q en d1 vs d2
            if q_max >= q_min:  # alta a la izquierda
                q_xa = q_max + (q_min - q_max) * xa / L
            else:                # alta a la derecha
                q_xa = q_min + (q_max - q_min) * xa / L
            h_arrow = arrow_h * (q_xa / max(q_max, 1.0))
            h_arrow = max(h_arrow, arrow_h * 0.05)
            ax.annotate('', xy=(xa, 0), xytext=(xa, -h_arrow),
                        arrowprops=dict(arrowstyle='->', color=arr_col,
                                        lw=1.2, mutation_scale=10))
        # Baseline trapezoidal
        if uniforme:
            ax.plot([0, L], [-arrow_h, -arrow_h], color=arr_col, lw=1.3)
        else:
            # línea inclinada conectando las puntas de las flechas extremas
            h_left  = arrow_h * (q_max / max(q_max, 1.0)) if q_max >= q_min else arrow_h * (q_min / max(q_max, 1.0))
            h_right = arrow_h * (q_min / max(q_max, 1.0)) if q_max >= q_min else arrow_h * (q_max / max(q_max, 1.0))
            ax.plot([0, L], [-h_left, -h_right], color=arr_col, lw=1.3)
    else:
        # Triangular con despegue: flechas solo en la zona activa [0, a_efect]
        xs_arr = np.linspace(L*0.015, a_efect*0.98, max(6, int(a_efect/0.28)))
        for xa in xs_arr:
            q_xa   = q_max * (1 - xa / a_efect)
            h_arrow = arrow_h * (q_xa / max(q_max, 1.0))
            h_arrow = max(h_arrow, arrow_h * 0.02)
            ax.annotate('', xy=(xa, 0), xytext=(xa, -h_arrow),
                        arrowprops=dict(arrowstyle='->', color=arr_col,
                                        lw=1.2, mutation_scale=10))
        # Baseline triangular
        ax.plot([0, a_efect], [-arrow_h, 0], color=arr_col, lw=1.3)
        ax.plot([0, 0], [0, -arrow_h], color=arr_col, lw=0.8, ls=':')
        # Zona sin contacto
        ax.fill_between([a_efect, L], [0, 0], [-arrow_h*0.06, -arrow_h*0.06],
                        color='#EF5350', alpha=0.15, zorder=1)
        ax.text((a_efect + L)/2, -arrow_h*0.25, "sin contacto",
                ha='center', va='center', fontsize=8, color='#EF5350', style='italic')
        ax.axvline(a_efect, color='#EF5350', lw=1.0, ls='--', alpha=0.7, zorder=2)

    # Etiqueta de presión + verificación vs qa
    ok_color = '#66BB6A' if q_max <= qa else '#EF5350'
    ok_sym   = '✔' if q_max <= qa else '✘'
    if uniforme:
        lbl = f"q = {q_max:.0f} kN/m²  (uniforme)   {ok_sym}  qa = {qa:.0f} kN/m²"
    elif a_efect >= L - 0.01:
        lbl = f"q_max={q_max:.0f} | q_min={q_min:.0f} kN/m²   {ok_sym}  qa={qa:.0f} kN/m²"
    else:
        lbl = f"q_max={q_max:.0f} kN/m²  (triangular, a={a_efect:.2f} m)   {ok_sym}  qa={qa:.0f} kN/m²"
    ax.text(min(a_efect, L)/2, -arrow_h - h*0.10, lbl,
            ha='center', va='top', fontsize=9, color=ok_color, fontweight='bold')

    # ── Dimension lines ───────────────────────────────────────────────────────
    # Total L (below arrows)
    y_ldim = y_base - arrow_h * 0.55
    ax.annotate('', xy=(L, y_ldim), xytext=(0, y_ldim),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.1))
    ax.text(L/2, y_ldim - dim_offset*0.18, f"L = {L:.2f} m",
            ha='center', va='top', fontsize=11, color='#85B7EB', fontweight='bold')

    # h (right side)
    xr = L + dim_offset*0.55
    ax.plot([xr, xr], [0, h], color='#85B7EB', lw=0.9)
    tick = dim_offset*0.18
    ax.plot([xr-tick, xr], [0, 0], color='#85B7EB', lw=0.9)
    ax.plot([xr-tick, xr], [h, h], color='#85B7EB', lw=0.9)
    ax.text(xr + dim_offset*0.12, h/2, f"h = {h:.2f} m",
            ha='left', va='center', fontsize=10, color='white', fontweight='bold')

    # d1 and d2 positions (column centerlines)
    for xc, lbl_d, i in [(d1, f"d₁={d1:.2f} m", 0), (d2, f"d₂={d2:.2f} m", 1)]:
        ax.plot([xc, xc], [0, h + col_h], color='#378ADD', lw=0.7, ls=':', alpha=0.5, zorder=2)
        ax.text(xc, -dim_offset*0.12,
                lbl_d, ha='center', va='top', fontsize=8.5, color='#85B7EB')

    ax.set_xlim(-pad*1.1, L + pad*1.8)
    ax.set_ylim(y_ldim - dim_offset*0.45, h + col_h + pad*0.7)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Sección Longitudinal — Perfil de la Zapata", color='#85B7EB', fontsize=11, pad=8)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _dibujar_diagramas_combinada_bytes(motor: ZapataCombinadaRectangular) -> io.BytesIO:
    res = motor.res
    xs = res.x_diag
    Vs = res.V_diag
    Ms = res.M_diag
    d1, d2 = res.d1, res.d2

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, facecolor='#0a1929')
    fig.patch.set_facecolor('#0a1929')

    ax1.fill_between(xs, Vs, 0, where=[v >= 0 for v in Vs], alpha=0.35, color='#42A5F5')
    ax1.fill_between(xs, Vs, 0, where=[v < 0 for v in Vs], alpha=0.35, color='#EF5350')
    ax1.plot(xs, Vs, color='#90CAF9', lw=2.0)
    ax1.axhline(0, color='#85B7EB', lw=0.8)
    ax1.axvline(d1, color='#90A4AE', lw=1.0, ls='--', alpha=0.8, label=f'Col1  x={d1:.2f} m')
    ax1.axvline(d2, color='#90A4AE', lw=1.0, ls=':',  alpha=0.8, label=f'Col2  x={d2:.2f} m')
    ax1.set_ylabel("V (kN)", fontsize=11, color='white')
    ax1.set_title("Diagrama de Cortante V(x)", fontsize=12, fontweight='bold', color='#85B7EB')
    ax1.grid(True, alpha=0.15, ls=':', color='#378ADD')
    ax1.legend(fontsize=9, facecolor='#0a1929', edgecolor='#378ADD', labelcolor='white')
    ax1.set_facecolor('#0d2137')
    ax1.tick_params(colors='#85B7EB')
    ax1.spines[:].set_color('#2a4060')

    ax2.fill_between(xs, Ms, 0, where=[m >= 0 for m in Ms], alpha=0.35, color='#66BB6A')
    ax2.fill_between(xs, Ms, 0, where=[m < 0 for m in Ms], alpha=0.35, color='#EF5350')
    ax2.plot(xs, Ms, color='#A5D6A7', lw=2.0)
    ax2.axhline(0, color='#85B7EB', lw=0.8)
    ax2.axvline(d1, color='#90A4AE', lw=1.0, ls='--', alpha=0.8, label=f'Col1  x={d1:.2f} m')
    ax2.axvline(d2, color='#90A4AE', lw=1.0, ls=':',  alpha=0.8, label=f'Col2  x={d2:.2f} m')
    if res.x_Mu_pos > 0 and res.Mu_pos > 0:
        peak_y = res.Mu_pos
        offset = abs(peak_y) * 0.35 + 30
        ax2.annotate(f"+{peak_y:.1f} kN·m",
                     xy=(res.x_Mu_pos, peak_y),
                     xytext=(res.x_Mu_pos, peak_y + offset),
                     ha='center', fontsize=9, color='#A5D6A7',
                     arrowprops=dict(arrowstyle='->', color='#66BB6A', lw=1.2))
    ax2.set_xlabel("x (m)", fontsize=11, color='white')
    ax2.set_ylabel("M (kN·m)", fontsize=11, color='white')
    ax2.set_title("Diagrama de Momento M(x)", fontsize=12, fontweight='bold', color='#85B7EB')
    ax2.grid(True, alpha=0.15, ls=':', color='#378ADD')
    ax2.legend(fontsize=9, facecolor='#0a1929', edgecolor='#378ADD', labelcolor='white')
    ax2.set_facecolor('#0d2137')
    ax2.tick_params(colors='#85B7EB')
    ax2.spines[:].set_color('#2a4060')

    plt.tight_layout(pad=1.2)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


@app.get("/zapata-combinada", response_class=HTMLResponse)
async def zapata_combinada_page():
    return (Path(ROOT / "web" / "static" / "combinada.html")).read_text(encoding="utf-8")


@app.post("/api/combinada/calcular")
async def api_combinada_calcular(datos: DatosCombinadaEntrada):
    try:
        force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
        motor = _build_motor_combinada(datos)
        res = motor.res

        if res.B == 0 or res.L == 0:
            error_msgs = [m["texto"] for m in res.mensajes if m["tipo"] == "error"]
            msg = error_msgs[0] if error_msgs else "Presión neta ≤ 0. Verifique qa, Df y γ suelo."
            return JSONResponse({"error": msg}, status_code=422)

        def fc(v): return float(UnitConverter.from_base(float(v), force_unit, 'force'))
        def pc(v): return float(UnitConverter.from_base(float(v), pressure_unit, 'pressure'))

        return JSONResponse({
            "B": float(res.B), "L": float(res.L), "h": float(res.h),
            "d1": float(res.d1), "d2": float(res.d2), "area": float(res.area),
            "q_neto": pc(res.q_neto), "q_max": pc(res.q_max),
            "q_ultima": pc(res.q_ultima), "ok_presion": bool(res.ok_presion),
            "Mu_neg1": float(res.Mu_neg1), "Mu_neg2": float(res.Mu_neg2),
            "Mu_pos": float(res.Mu_pos), "x_Mu_pos": float(res.x_Mu_pos),
            "ok_punz1": bool(res.ok_punz1), "rel_punz1": float(res.rel_punz1),
            "Vu_punz1": fc(res.Vu_punz1), "phi_Vn_punz1": fc(res.phi_Vn_punz1),
            "ok_punz2": bool(res.ok_punz2), "rel_punz2": float(res.rel_punz2),
            "Vu_punz2": fc(res.Vu_punz2), "phi_Vn_punz2": fc(res.phi_Vn_punz2),
            "ok_cortante": bool(res.ok_cortante), "rel_cortante": float(res.rel_cortante),
            "Vu_cort": fc(res.Vu_cort), "phi_Vn_cort": fc(res.phi_Vn_cort),
            "Mu_long_top": float(res.Mu_long_top), "Mu_long_bot": float(res.Mu_long_bot),
            "As_long_top_pm": float(res.As_long_top_pm), "As_long_bot_pm": float(res.As_long_bot_pm),
            "varilla_long_top": res.varilla_long_top, "sep_long_top": float(res.sep_long_top),
            "n_long_top": int(res.n_long_top),
            "varilla_long_bot": res.varilla_long_bot, "sep_long_bot": float(res.sep_long_bot),
            "n_long_bot": int(res.n_long_bot),
            "vol_trans1": float(res.vol_trans1), "Mu_trans1": float(res.Mu_trans1),
            "As_trans1": float(res.As_trans1), "varilla_trans1": res.varilla_trans1,
            "sep_trans1": float(res.sep_trans1),
            "vol_trans2": float(res.vol_trans2), "Mu_trans2": float(res.Mu_trans2),
            "As_trans2": float(res.As_trans2), "varilla_trans2": res.varilla_trans2,
            "sep_trans2": float(res.sep_trans2),
            "mensajes": res.mensajes,
            "unidades": {"cargas": force_unit, "presiones": pressure_unit},
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/combinada/plot/planta")
async def api_combinada_plot_planta(datos: DatosCombinadaEntrada):
    motor = _build_motor_combinada(datos)
    buf = _dibujar_planta_combinada_bytes(motor)
    return Response(content=buf.getvalue(), media_type='image/png')


@app.post("/api/combinada/plot/diagramas")
async def api_combinada_plot_diagramas(datos: DatosCombinadaEntrada):
    motor = _build_motor_combinada(datos)
    buf = _dibujar_diagramas_combinada_bytes(motor)
    return Response(content=buf.getvalue(), media_type='image/png')


@app.post("/api/combinada/plot/seccion_long")
async def api_combinada_plot_seccion_long(datos: DatosCombinadaEntrada):
    motor = _build_motor_combinada(datos)
    buf = _dibujar_seccion_long_combinada_bytes(motor)
    return Response(content=buf.getvalue(), media_type='image/png')


@app.post("/api/combinada/report/pdf")
async def api_combinada_report_pdf(datos: DatosCombinadaEntrada):
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    motor = _build_motor_combinada(datos)

    datos_entrada = {
        "unidades": {"cargas": force_unit, "presiones": pressure_unit},
        "orig": {
            "Pd1": datos.Pd1, "Pl1": datos.Pl1,
            "Pd2": datos.Pd2, "Pl2": datos.Pl2,
            "qa":  datos.qa,
        },
    }

    buf_planta = _dibujar_planta_combinada_bytes(motor)
    buf_diag   = _dibujar_diagramas_combinada_bytes(motor)

    tmp_pdf    = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp_planta = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    tmp_diag   = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    for t in (tmp_pdf, tmp_planta, tmp_diag):
        t.close()

    with open(tmp_planta.name, 'wb') as f:
        f.write(buf_planta.getvalue())
    with open(tmp_diag.name, 'wb') as f:
        f.write(buf_diag.getvalue())

    gen = GeneradorPDFCombinada()
    try:
        gen.generar(tmp_pdf.name, motor, datos.norma, datos_entrada,
                    imagen_planta=tmp_planta.name, imagen_diagramas=tmp_diag.name)
        with open(tmp_pdf.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="memoria_zapata_combinada.pdf"'},
        )
    finally:
        for p in (tmp_pdf.name, tmp_planta.name, tmp_diag.name):
            try:
                os.unlink(p)
            except Exception:
                pass


@app.post("/api/combinada/report/dxf")
async def api_combinada_report_dxf(datos: DatosCombinadaEntrada):
    motor = _build_motor_combinada(datos)
    gen = GeneradorDXFCombinada()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
    tmp.close()
    try:
        gen.generar(tmp.name, motor, datos.norma)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes,
            media_type='application/dxf',
            headers={'Content-Disposition': 'attachment; filename="despiece_zapata_combinada.dxf"'},
        )
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


# ─── Module 3: Zapata Corrida ────────────────────────────────────────────────

class DatosCorridaEntrada(BaseModel):
    Pd: float = 100.0
    Pl: float = 60.0
    t_muro: float = 0.20
    qa: float = 100.0
    Df: float = 0.80
    gamma_s: float = 18.0
    fck: float = 25.0
    fy: float = 420.0
    B_fijo: float = 0.0
    h: float = 0.40
    recubrimiento: float = 0.075
    norma: str = "ACI318"
    unidades: str = "kN_kN/m2"
    varilla_pref: Optional[str] = ""


def _build_motor_corrida(datos: DatosCorridaEntrada) -> ZapataCorridaRectangular:
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    carga = CargaMuro(
        Pd=UnitConverter.to_base(datos.Pd, force_unit, 'force'),
        Pl=UnitConverter.to_base(datos.Pl, force_unit, 'force'),
    )
    muro  = MuroCorrida(espesor=datos.t_muro)
    suelo = SueloCorrida(
        qa=UnitConverter.to_base(datos.qa, pressure_unit, 'pressure'),
        Df=datos.Df, gamma_suelo=datos.gamma_s,
    )
    hormigon = MaterialHormigon(fck=datos.fck)
    acero    = MaterialAcero(fy=datos.fy)
    geo = GeometriaCorrida(
        B_fijo=datos.B_fijo, h=datos.h, recubrimiento=datos.recubrimiento,
    )
    norma_cls = NORMAS_MAP.get(datos.norma, ACI318)
    motor = ZapataCorridaRectangular(carga, muro, suelo, hormigon, acero, norma_cls(), geo,
                                     varilla_pref=datos.varilla_pref or "")
    motor.calcular()
    return motor


def _dibujar_seccion_corrida_bytes(motor: ZapataCorridaRectangular) -> io.BytesIO:
    res  = motor.res
    geo  = motor.geo
    muro = motor.muro
    B    = res.B or 1.0
    h    = res.h
    t    = muro.espesor
    d    = geo.d
    r    = geo.recubrimiento

    ref        = max(B, h * 3.5)
    dim_offset = 0.14 * ref
    tick       = 0.032 * ref

    fig, ax = plt.subplots(figsize=(12, 4.5), facecolor='#0a1929')
    ax.set_facecolor('#0a1929')
    ax.set_aspect('equal')
    ax.axis('off')

    # Footing body
    ax.add_patch(plt.Rectangle((-B/2, 0), B, h,
                                facecolor='#142233', edgecolor='#378ADD', lw=1.5))
    # Wall stub (0.5 m height)
    ax.add_patch(plt.Rectangle((-t/2, h), t, 0.50,
                                facecolor='#546E7A', edgecolor='#90A4AE', lw=1.2))

    # Transverse reinforcement bar (runs ⊥ to wall — shown as line in this view)
    db_m  = 0.016
    y_bar = r + db_m / 2
    ax.plot([-B/2 + r, B/2 - r], [y_bar, y_bar], color='#EF5350', lw=2.2, zorder=5)

    # Longitudinal bars (‖ wall — circles in this section)
    sep_l = res.sep_long or 0.20
    n_show = min(12, max(4, round((B - 2*r) / sep_l) + 1))
    xs_l  = [-B/2 + r + i*(B - 2*r)/(n_show - 1) for i in range(n_show)]
    for xb in xs_l:
        ax.add_patch(plt.Circle((xb, y_bar), db_m * 0.8, color='#AB47BC', zorder=6))

    # Cover annotation
    ax.annotate('', xy=(-B/2 + r*0.08, 0), xytext=(-B/2 + r*0.08, r),
                arrowprops=dict(arrowstyle='<->', color='#8899AA', lw=0.8))
    ax.text(-B/2 + r*0.15, r/2, f"r={r*100:.0f}cm",
            ha='left', va='center', fontsize=8.5, color='#8899AA')

    # Dim h
    x_dh = B/2 + dim_offset
    ax.plot([x_dh, x_dh], [0, h], color='#85B7EB', lw=1.0)
    ax.plot([x_dh - tick, x_dh], [0, 0], color='#85B7EB', lw=1.0)
    ax.plot([x_dh - tick, x_dh], [h, h], color='#85B7EB', lw=1.0)
    ax.annotate(f"h={h:.2f} m", xy=(x_dh + 0.01*ref, h/2),
                ha='left', va='center', fontsize=11, fontweight='bold', color='white')

    # Dim B (below)
    y_db = -dim_offset * 0.28
    ax.annotate('', xy=(B/2, y_db), xytext=(-B/2, y_db),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ax.plot([-B/2, -B/2], [y_db, 0], color='#378ADD', lw=0.5, ls=':')
    ax.plot([ B/2,  B/2], [y_db, 0], color='#378ADD', lw=0.5, ls=':')
    ax.text(0, y_db - 0.015*ref, f"B = {B:.2f} m",
            ha='center', va='top', fontsize=11, fontweight='bold', color='#85B7EB')

    # Dim t (wall)
    y_dt = h + 0.55 + dim_offset * 0.3
    ax.annotate('', xy=(t/2, y_dt), xytext=(-t/2, y_dt),
                arrowprops=dict(arrowstyle='<->', color='#90A4AE', lw=1.0))
    ax.text(0, y_dt + 0.01*ref, f"t={t:.2f} m",
            ha='center', va='bottom', fontsize=9.5, color='#90A4AE')

    # Legend text
    ax.text(-B/2 + r, -dim_offset * 1.00,
            f"Arm. Trans. (⊥ muro): {res.varilla} @ {(res.separacion or 0)*100:.0f} cm   As={res.As_diseno:.2f} cm²/m",
            fontsize=9, color='#EF5350')
    ax.text(-B/2 + r, -dim_offset * 1.32,
            f"Arm. Long.  (‖ muro): {res.varilla_long} @ {(res.sep_long or 0)*100:.0f} cm   As={res.As_long:.2f} cm²/m",
            fontsize=9, color='#AB47BC')

    ax.set_xlim(-B/2 - 0.08*ref, B/2 + dim_offset + 0.52*ref)
    ax.set_ylim(-dim_offset * 1.60, h + 0.65)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


@app.get("/zapata-corrida", response_class=HTMLResponse)
async def zapata_corrida_page():
    return (Path(ROOT / "web" / "static" / "corrida.html")).read_text(encoding="utf-8")


@app.post("/api/corrida/calcular")
async def api_corrida_calcular(datos: DatosCorridaEntrada):
    try:
        force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
        motor = _build_motor_corrida(datos)
        res = motor.res

        if res.B == 0:
            error_msgs = [m["texto"] for m in res.mensajes if m["tipo"] == "error"]
            msg = error_msgs[0] if error_msgs else "Presión neta ≤ 0. Verifique qa, Df y γ suelo."
            return JSONResponse({"error": msg}, status_code=422)

        def pc(v): return float(UnitConverter.from_base(float(v), pressure_unit, 'pressure'))

        return JSONResponse({
            "B": float(res.B), "h": float(res.h), "d": float(res.d), "a": float(res.a),
            "q_neto": pc(res.q_neto), "q_max": pc(res.q_max),
            "q_ultima": pc(res.q_ultima), "ok_presion": bool(res.ok_presion),
            "Mu": float(res.Mu), "Vu": float(res.Vu), "phi_Vn": float(res.phi_Vn),
            "ok_cortante": bool(res.ok_cortante), "rel_cortante": float(res.rel_cortante),
            "As_req": float(res.As_req), "As_min": float(res.As_min),
            "As_diseno": float(res.As_diseno),
            "varilla": res.varilla, "separacion": float(res.separacion),
            "n_barras_por_metro": int(res.n_barras_por_metro),
            "As_long": float(res.As_long),
            "varilla_long": res.varilla_long, "sep_long": float(res.sep_long),
            "mensajes": res.mensajes,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/corrida/plot/seccion")
async def api_corrida_plot_seccion(datos: DatosCorridaEntrada):
    motor = _build_motor_corrida(datos)
    buf = _dibujar_seccion_corrida_bytes(motor)
    return Response(content=buf.getvalue(), media_type='image/png')


@app.post("/api/corrida/report/pdf")
async def api_corrida_report_pdf(datos: DatosCorridaEntrada):
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    motor = _build_motor_corrida(datos)

    datos_entrada = {
        "norma": datos.norma,
        "unidades": {"cargas": force_unit, "presiones": pressure_unit},
        "orig": {"Pd": datos.Pd, "Pl": datos.Pl, "qa": datos.qa},
    }

    buf_sec = _dibujar_seccion_corrida_bytes(motor)
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp_sec = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    tmp_pdf.close(); tmp_sec.close()
    with open(tmp_sec.name, 'wb') as f:
        f.write(buf_sec.getvalue())

    gen = GeneradorPDFCorrida()
    try:
        gen.generar(tmp_pdf.name, motor, datos_entrada, imagen_seccion=tmp_sec.name)
        with open(tmp_pdf.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="memoria_zapata_corrida.pdf"'},
        )
    finally:
        for p in (tmp_pdf.name, tmp_sec.name):
            try:
                os.unlink(p)
            except Exception:
                pass


@app.post("/api/corrida/report/dxf")
async def api_corrida_report_dxf(datos: DatosCorridaEntrada):
    motor = _build_motor_corrida(datos)
    gen = GeneradorDXFCorrida()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
    tmp.close()
    try:
        gen.generar(tmp.name, motor, datos.norma)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes,
            media_type='application/dxf',
            headers={'Content-Disposition': 'attachment; filename="zapata_corrida.dxf"'},
        )
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


# ─── Module 5: Zapata Excéntrica ─────────────────────────────────────────────

class DatosExcentricaEntrada(BaseModel):
    Pd:  float = 200.0
    Pl:  float = 100.0
    Mdx: float = 40.0
    Mlx: float = 20.0
    Mdy: float = 0.0
    Mly: float = 0.0
    cx:  float = 0.35
    cy:  float = 0.35
    qa:  float = 120.0
    Df:  float = 1.20
    gamma_s: float = 18.0
    fck: float = 25.0
    fy:  float = 420.0
    B_fijo: float = 0.0
    L_fijo: float = 0.0
    h:   float = 0.50
    recubrimiento: float = 0.075
    norma:    str = "ACI318"
    unidades: str = "kN_kN/m2"
    varilla_pref: Optional[str] = ""


def _build_motor_excentrica(datos: DatosExcentricaEntrada) -> ZapataExcentricaRectangular:
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    carga = CargaExcentrica(
        Pd=UnitConverter.to_base(datos.Pd,  force_unit, 'force'),
        Pl=UnitConverter.to_base(datos.Pl,  force_unit, 'force'),
        Mdx=UnitConverter.to_base(datos.Mdx, force_unit, 'force'),
        Mlx=UnitConverter.to_base(datos.Mlx, force_unit, 'force'),
        Mdy=UnitConverter.to_base(datos.Mdy, force_unit, 'force'),
        Mly=UnitConverter.to_base(datos.Mly, force_unit, 'force'),
    )
    columna = ColumnaExcentrica(cx=datos.cx, cy=datos.cy)
    suelo   = SueloExcentrica(
        qa=UnitConverter.to_base(datos.qa, pressure_unit, 'pressure'),
        Df=datos.Df, gamma_suelo=datos.gamma_s,
    )
    hormigon = MaterialHormigon(fck=datos.fck)
    acero    = MaterialAcero(fy=datos.fy)
    geo      = GeometriaExcentrica(
        B_fijo=datos.B_fijo, L_fijo=datos.L_fijo,
        h=datos.h, recubrimiento=datos.recubrimiento,
    )
    norma_cls = NORMAS_MAP.get(datos.norma, ACI318)
    motor = ZapataExcentricaRectangular(
        carga, columna, suelo, hormigon, acero, norma_cls(), geo,
        varilla_pref=datos.varilla_pref or "",
    )
    motor.calcular()
    return motor


def _dibujar_seccion_excentrica_bytes(motor: ZapataExcentricaRectangular) -> io.BytesIO:
    """Sección en dirección L con diagrama de presiones trapezoidal."""
    res   = motor.res
    geo   = motor.geo
    col   = motor.columna
    L     = res.L or 1.5
    h     = res.h
    cx    = col.cx
    r     = geo.recubrimiento

    q_max_u = res.q_max_u
    q_min_u = max(res.q_min_u, 0.0)

    ref        = max(L, h * 3.5)
    dim_offset = 0.14 * ref
    tick       = 0.030 * ref

    fig, ax = plt.subplots(figsize=(12, 5), facecolor='#0a1929')
    ax.set_facecolor('#0a1929')
    ax.set_aspect('equal')
    ax.axis('off')

    # Cuerpo de la zapata
    ax.add_patch(plt.Rectangle((-L/2, 0), L, h,
                                facecolor='#142233', edgecolor='#378ADD', lw=1.5))

    # Columna stub
    col_h = 0.40
    ax.add_patch(plt.Rectangle((-cx/2, h), cx, col_h,
                                facecolor='#546E7A', edgecolor='#90A4AE', lw=1.2))

    # Diagrama de presiones trapezoidal (escala relativa a h)
    pmax = max(q_max_u, q_min_u, 1.0)
    p_scale = (h * 0.55) / pmax
    py_max  = -(q_max_u * p_scale)
    py_min  = -(q_min_u * p_scale)

    trap_x = [-L/2, -L/2, L/2, L/2, -L/2]
    trap_y = [0,   py_min, py_max, 0,  0]
    ax.fill(trap_x, trap_y, facecolor='#EF9F27', edgecolor='#EF9F27', lw=1.2, alpha=0.30, zorder=2)
    ax.plot([-L/2, L/2], [py_min, py_max], color='#EF9F27', lw=1.5, zorder=3)

    # Flechas de presión
    for frac in [0.15, 0.40, 0.65, 0.90]:
        xi    = -L/2 + frac * L
        py_xi = py_min + (py_max - py_min) * frac
        ax.annotate('', xy=(xi, 0), xytext=(xi, py_xi),
                    arrowprops=dict(arrowstyle='->', color='#EF9F27', lw=1.0))

    # Labels presiones
    ax.text(L/2 + 0.02*ref, py_max/2,
            f"qu,max\n{q_max_u:.1f} kN/m²",
            ha='left', va='center', fontsize=8.5, color='#FFB74D', fontweight='bold')
    ax.text(-L/2 - 0.02*ref, py_min/2,
            f"qu,min\n{q_min_u:.1f} kN/m²",
            ha='right', va='center', fontsize=8.5, color='#90CAF9', fontweight='bold')

    # Barras As_L
    db_m   = 0.018
    y_barL = r + db_m / 2
    ax.plot([-L/2 + r, L/2 - r], [y_barL, y_barL], color='#EF5350', lw=2.2, zorder=5,
            label=f"As-L: {res.varilla_L} @ {res.sep_L*100:.0f}cm")

    # Barras As_B (círculos en sección L)
    sep_b  = res.sep_B or 0.20
    n_show = min(12, max(3, round((L - 2*r) / sep_b)))
    y_barB = r + db_m * 1.6
    for i in range(n_show + 1):
        xb = -L/2 + r + i * (L - 2*r) / max(n_show, 1)
        ax.add_patch(plt.Circle((xb, y_barB), db_m * 0.75, color='#AB47BC', zorder=6))

    # Recubrimiento
    ax.annotate('', xy=(-L/2 + r*0.08, 0), xytext=(-L/2 + r*0.08, r),
                arrowprops=dict(arrowstyle='<->', color='#8899AA', lw=0.8))
    ax.text(-L/2 + r*0.15, r/2, f"r={r*100:.0f}cm",
            ha='left', va='center', fontsize=8, color='#8899AA')

    # Cota h
    x_dh = L/2 + dim_offset
    ax.plot([x_dh, x_dh], [0, h], color='#85B7EB', lw=1.0)
    ax.plot([x_dh - tick, x_dh], [0, 0], color='#85B7EB', lw=1.0)
    ax.plot([x_dh - tick, x_dh], [h, h], color='#85B7EB', lw=1.0)
    ax.annotate(f"h={h:.2f} m", xy=(x_dh + 0.01*ref, h/2),
                ha='left', va='center', fontsize=11, fontweight='bold', color='white')

    # Cota L
    y_dL = py_min - dim_offset * 0.35
    ax.annotate('', xy=(L/2, y_dL), xytext=(-L/2, y_dL),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ax.plot([-L/2, -L/2], [y_dL, 0], color='#378ADD', lw=0.5, ls=':')
    ax.plot([ L/2,  L/2], [y_dL, 0], color='#378ADD', lw=0.5, ls=':')
    ax.text(0, y_dL - 0.015*ref, f"L = {L:.2f} m",
            ha='center', va='top', fontsize=11, fontweight='bold', color='#85B7EB')

    # Leyenda
    y_leg1 = py_min - dim_offset * 1.00
    y_leg2 = py_min - dim_offset * 1.35
    ax.text(-L/2 + r, y_leg1,
            f"Arm. dir.L (─ en sección): {res.varilla_L} @ {res.sep_L*100:.0f} cm   As={res.As_dis_L:.2f} cm²/m",
            fontsize=9, color='#EF5350')
    ax.text(-L/2 + r, y_leg2,
            f"Arm. dir.B (● en sección): {res.varilla_B} @ {res.sep_B*100:.0f} cm   As={res.As_dis_B:.2f} cm²/m",
            fontsize=9, color='#AB47BC')

    ax.set_xlim(-L/2 - 0.08*ref, L/2 + dim_offset + 0.48*ref)
    ax.set_ylim(y_leg2 - 0.06*ref, h + col_h + 0.12)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


@app.get("/modulo5", response_class=HTMLResponse)
async def modulo5_hub_page():
    return (Path(ROOT / "web" / "static" / "excentrica_hub.html")).read_text(encoding="utf-8")


@app.get("/zapata-excentrica", response_class=HTMLResponse)
async def zapata_excentrica_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/modulo5")


@app.get("/zapata-excentrica/por-carga", response_class=HTMLResponse)
async def zapata_excentrica_page():
    return (Path(ROOT / "web" / "static" / "excentrica.html")).read_text(encoding="utf-8")


@app.post("/api/excentrica/calcular")
async def api_excentrica_calcular(datos: DatosExcentricaEntrada):
    try:
        force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
        motor = _build_motor_excentrica(datos)
        res   = motor.res

        if res.B == 0:
            error_msgs = [m["texto"] for m in res.mensajes if m["tipo"] == "error"]
            msg = error_msgs[0] if error_msgs else "Presión neta ≤ 0. Verifique qa, Df y γ suelo."
            return JSONResponse({"error": msg}, status_code=422)

        def pc(v): return float(UnitConverter.from_base(float(v), pressure_unit, 'pressure'))
        def fc(v): return float(UnitConverter.from_base(float(v), force_unit, 'force'))

        return JSONResponse({
            "B": float(res.B), "L": float(res.L), "h": float(res.h),
            "d": float(res.d), "A": float(res.A),
            "ex": float(res.ex), "ey": float(res.ey),
            "ex_u": float(res.ex_u), "ey_u": float(res.ey_u),
            "tipo_contacto": res.tipo_contacto,
            "en_nucleo": bool(res.en_nucleo),
            "L_ef": float(res.L_ef),
            "q_neto": pc(res.q_neto),
            "q1": pc(res.q1), "q2": pc(res.q2),
            "q3": pc(res.q3), "q4": pc(res.q4),
            "q_max": pc(res.q_max), "q_min": pc(res.q_min),
            "ok_presion": bool(res.ok_presion),
            "ok_tension": bool(res.ok_tension),
            "q1u": pc(res.q1u), "q2u": pc(res.q2u),
            "q3u": pc(res.q3u), "q4u": pc(res.q4u),
            "q_max_u": pc(res.q_max_u), "q_min_u": pc(res.q_min_u),
            "bo": float(res.bo),
            "Vpu": fc(res.Vpu), "phi_Vpn": fc(res.phi_Vpn),
            "ok_punzonado": bool(res.ok_punzonado),
            "rel_punzonado": float(res.rel_punzonado),
            "Vu_L": float(res.Vu_L), "Vu_B": float(res.Vu_B),
            "phi_Vn": float(res.phi_Vn),
            "ok_cortante_L": bool(res.ok_cortante_L),
            "ok_cortante_B": bool(res.ok_cortante_B),
            "Mu_L": float(res.Mu_L),
            "As_req_L": float(res.As_req_L), "As_min_L": float(res.As_min_L),
            "As_dis_L": float(res.As_dis_L),
            "varilla_L": res.varilla_L, "sep_L": float(res.sep_L),
            "n_barras_L": int(res.n_barras_L),
            "Mu_B": float(res.Mu_B),
            "As_req_B": float(res.As_req_B), "As_min_B": float(res.As_min_B),
            "As_dis_B": float(res.As_dis_B),
            "varilla_B": res.varilla_B, "sep_B": float(res.sep_B),
            "n_barras_B": int(res.n_barras_B),
            "mensajes": res.mensajes,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/excentrica/plot/seccion")
async def api_excentrica_plot_seccion(datos: DatosExcentricaEntrada):
    motor = _build_motor_excentrica(datos)
    buf   = _dibujar_seccion_excentrica_bytes(motor)
    return Response(content=buf.getvalue(), media_type='image/png')


@app.post("/api/excentrica/report/pdf")
async def api_excentrica_report_pdf(datos: DatosExcentricaEntrada):
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    motor = _build_motor_excentrica(datos)

    datos_entrada = {
        "norma":    datos.norma,
        "unidades": {"cargas": force_unit, "presiones": pressure_unit},
    }

    buf_sec = _dibujar_seccion_excentrica_bytes(motor)
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp_sec = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    tmp_pdf.close(); tmp_sec.close()
    with open(tmp_sec.name, 'wb') as f:
        f.write(buf_sec.getvalue())

    gen = GeneradorPDFExcentrica()
    try:
        gen.generar(tmp_pdf.name, motor, datos_entrada, imagen_seccion=tmp_sec.name)
        with open(tmp_pdf.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="memoria_zapata_excentrica.pdf"'},
        )
    finally:
        for p in (tmp_pdf.name, tmp_sec.name):
            try: os.unlink(p)
            except Exception: pass


@app.post("/api/excentrica/report/dxf")
async def api_excentrica_report_dxf(datos: DatosExcentricaEntrada):
    motor = _build_motor_excentrica(datos)
    gen   = GeneradorDXFExcentrica()
    tmp   = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
    tmp.close()
    try:
        gen.generar(tmp.name, motor, datos.norma)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes,
            media_type='application/dxf',
            headers={'Content-Disposition': 'attachment; filename="zapata_excentrica.dxf"'},
        )
    finally:
        try: os.unlink(tmp.name)
        except Exception: pass


# ─── Module 5b: Zapata de Fachada / Excéntrica por Geometría ─────────────────

class DatosFachadaEntrada(BaseModel):
    Pd:      float = 200.0
    Pl:      float = 100.0
    ex_geom: float = 0.50
    ey_geom: float = 0.0
    a_borde: float = 0.10
    L_atado: float = 5.0
    cx:      float = 0.35
    cy:      float = 0.35
    qa:      float = 120.0
    Df:      float = 1.20
    gamma_s: float = 18.0
    fck:     float = 25.0
    fy:      float = 420.0
    B_fijo:  float = 0.0
    L_fijo:  float = 0.0
    h:       float = 0.50
    recubrimiento: float = 0.075
    norma:    str = "ACI318"
    unidades: str = "kN_kN/m2"
    varilla_pref: Optional[str] = ""
    modo_ras: bool = False


def _build_motor_fachada(datos: DatosFachadaEntrada) -> ZapataFachadaRectangular:
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    Pd = UnitConverter.to_base(datos.Pd, force_unit, 'force')
    Pl = UnitConverter.to_base(datos.Pl, force_unit, 'force')
    columna = ColumnaExcentrica(cx=datos.cx, cy=datos.cy)
    suelo   = SueloExcentrica(
        qa=UnitConverter.to_base(datos.qa, pressure_unit, 'pressure'),
        Df=datos.Df, gamma_suelo=datos.gamma_s,
    )
    hormigon = MaterialHormigon(fck=datos.fck)
    acero    = MaterialAcero(fy=datos.fy)
    geo_f    = GeometriaFachada(
        ex_geom=datos.ex_geom, ey_geom=datos.ey_geom,
        a_borde=datos.a_borde, L_atado=datos.L_atado,
        B_fijo=datos.B_fijo, L_fijo=datos.L_fijo,
        h=datos.h, recubrimiento=datos.recubrimiento,
        modo_ras=datos.modo_ras,
    )
    norma_cls = NORMAS_MAP.get(datos.norma, ACI318)
    motor = ZapataFachadaRectangular(
        Pd, Pl, columna, suelo, hormigon, acero, norma_cls(), geo_f,
        varilla_pref=datos.varilla_pref or "",
    )
    motor.calcular()
    return motor


def _dibujar_seccion_fachada_bytes(motor: ZapataFachadaRectangular) -> io.BytesIO:
    """Vista en planta + sección en dir. L con columna excéntrica y diagrama de presiones."""
    import matplotlib.patches as mpatches

    res   = motor.res
    geo   = motor.geo
    col   = motor.columna
    L     = res.L or 1.5
    B     = res.B or 1.0
    h     = res.h
    cx    = col.cx
    cy    = col.cy
    ex    = motor.ex_geom
    ey    = motor.ey_geom
    r     = geo.recubrimiento
    db_L  = 0.012
    db_B  = 0.012

    q_max_u = res.q_max_u or 1.0
    q_min_u = max(res.q_min_u, 0.0)

    fig, (ax_plan, ax_sec) = plt.subplots(
        1, 2, figsize=(13, 6),
        gridspec_kw={'width_ratios': [1, 1], 'wspace': 0.35},
        constrained_layout=False, facecolor='#0a1929',
    )
    fig.patch.set_facecolor('#0a1929')

    # ══════════════════════════════════════════════════════════════════════════
    # PANEL IZQUIERDO — VISTA EN PLANTA
    # ══════════════════════════════════════════════════════════════════════════
    ap = ax_plan
    ap.set_facecolor('#0a1929')
    ap.set_aspect('equal')
    ap.axis('off')
    ap.set_title('Vista en Planta', fontsize=10, fontweight='bold', pad=6, color='#85B7EB')

    # Zapata
    foot_plan = mpatches.Rectangle((-B/2, -L/2), B, L, linewidth=1.5,
                                    edgecolor='#378ADD', facecolor='#142233',
                                    alpha=0.85, zorder=2)
    ap.add_patch(foot_plan)

    # Columna
    col_plan = mpatches.Rectangle((ey - cy/2, ex - cx/2), cy, cx,
                                   linewidth=1.5, edgecolor='#90A4AE',
                                   facecolor='#546E7A', alpha=0.85, zorder=4)
    ap.add_patch(col_plan)

    # Cruz centroide zapata
    ap.plot(0, 0, '+', color='#378ADD', ms=8, mew=1.5, zorder=5)

    # Cruz centroide columna
    ap.plot(ey, ex, '+', color='#90A4AE', ms=8, mew=1.5, zorder=5)

    # LINDERO
    x_lind_ext = B/2 + 0.30
    ap.plot([-x_lind_ext, x_lind_ext], [L/2, L/2],
            color='#26C6DA', linewidth=2, linestyle='--', zorder=5)
    ap.text(x_lind_ext + 0.04, L/2, 'LINDERO',
            fontsize=7, color='#26C6DA', va='center', ha='left')

    # Flecha de excentricidad ex (vertical: de centroide zapata a centroide columna)
    if abs(ex) > 0.005:
        ap.annotate('', xy=(0, ex), xytext=(0, 0),
                    arrowprops=dict(arrowstyle='<->', color='#00838F', lw=1.3),
                    zorder=6)
        ap.text(cy/2 + 0.06, ex / 2, f'ex = {ex:.3f} m',
                ha='left', va='center', fontsize=7.5, color='#00838F', fontweight='bold')
    else:
        ap.text(0, ex + 0.04, f'ex ≈ 0',
                ha='center', va='bottom', fontsize=7, color='#555')

    # Flecha de excentricidad ey (horizontal)
    if abs(ey) > 0.005:
        ap.annotate('', xy=(ey, -cx/2 - 0.08), xytext=(0, -cx/2 - 0.08),
                    arrowprops=dict(arrowstyle='<->', color='#AB47BC', lw=1.2),
                    zorder=6)
        ap.text(ey / 2, -cx/2 - 0.16, f'ey = {ey:.3f} m',
                ha='center', va='top', fontsize=7.5, color='#AB47BC', fontweight='bold')

    # Cota B (abajo de la zapata)
    y_cotaB = -L/2 - 0.22
    ap.annotate('', xy=(B/2, y_cotaB), xytext=(-B/2, y_cotaB),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1))
    ap.text(0, y_cotaB - 0.05, f'B = {B:.2f} m',
            ha='center', va='top', fontsize=9, fontweight='bold', color='#85B7EB')

    # Cota L (derecha de la zapata)
    x_cotaL = B/2 + 0.55
    ap.annotate('', xy=(x_cotaL, L/2), xytext=(x_cotaL, -L/2),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1))
    ap.text(x_cotaL + 0.05, 0, f'L = {L:.2f} m',
            ha='left', va='center', fontsize=9, fontweight='bold', color='#85B7EB')

    # Vuelo del lado restringido
    vuelo = L/2 - ex - cx/2
    ap.annotate('', xy=(cy/2 + 0.05, L/2), xytext=(cy/2 + 0.05, ex + cx/2),
                arrowprops=dict(arrowstyle='<->', color='#E65100', lw=1.0))
    ap.text(cy/2 + 0.12, (L/2 + ex + cx/2) / 2,
            f'{vuelo:.3f} m', ha='left', va='center', fontsize=7, color='#E65100')

    # Make data range square so equal-aspect fills the panel for any B/L ratio
    x_lo, x_hi = -B/2 - 0.50, B/2 + 0.80   # room for right-side label
    y_lo, y_hi = -L/2 - 0.55, L/2 + 0.40
    x_range, y_range = x_hi - x_lo, y_hi - y_lo
    max_range = max(x_range, y_range)
    x_center  = (x_lo + x_hi) / 2
    y_center  = (y_lo + y_hi) / 2
    ap.set_xlim(x_center - max_range / 2, x_center + max_range / 2)
    ap.set_ylim(y_center - max_range / 2, y_center + max_range / 2)

    # ══════════════════════════════════════════════════════════════════════════
    # PANEL DERECHO — SECCIÓN EN DIRECCIÓN L
    # ══════════════════════════════════════════════════════════════════════════
    ax = ax_sec
    ax.set_facecolor('#0a1929')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Sección en Dirección L — Diagrama de Presiones', fontsize=10, pad=6, color='#85B7EB')

    pscale = 0.003
    if ex >= 0:
        p_right = q_max_u * pscale
        p_left  = q_min_u * pscale
    else:
        p_right = q_min_u * pscale
        p_left  = q_max_u * pscale

    xs_trap = [-L/2, -L/2, L/2, L/2, -L/2]
    ys_trap = [0, -p_left, -p_right, 0, 0]
    ax.fill(xs_trap, ys_trap, color='#EF9F27', alpha=0.25, zorder=1)
    ax.plot([-L/2, -L/2, L/2, L/2], [0, -p_left, -p_right, 0],
            color='#EF9F27', linewidth=1.5, zorder=2)

    p_max = max(p_left, p_right)
    n_arr = 5
    for i in range(n_arr):
        xp   = -L/2 + L * i / (n_arr - 1)
        frac = (xp + L/2) / L
        py   = p_left + (p_right - p_left) * frac
        if py > 0.005:
            ax.annotate('', xy=(xp, 0), xytext=(xp, -py),
                        arrowprops=dict(arrowstyle='->', color='#EF9F27', lw=1.1))

    ax.text(L/2 + 0.10, -p_right / 2,
            f'qu,max\n{q_max_u:.1f} kN/m²',
            va='center', ha='left', fontsize=7.5, color='#FFB74D', fontweight='bold')
    if q_min_u > 1.0:
        ax.text(-L/2 - 0.10, -p_left / 2,
                f'qu,min\n{q_min_u:.1f} kN/m²',
                va='center', ha='right', fontsize=7.5, color='#90CAF9', fontweight='bold')

    foot = mpatches.Rectangle((-L/2, 0), L, h, linewidth=1.5,
                               edgecolor='#378ADD', facecolor='#142233', alpha=0.90, zorder=3)
    ax.add_patch(foot)

    col_h = 0.40
    col_rect = mpatches.Rectangle((ex - cx/2, h), cx, col_h, linewidth=1.2,
                                   edgecolor='#90A4AE', facecolor='#546E7A', alpha=0.85, zorder=4)
    ax.add_patch(col_rect)

    ax.axvline(x=L/2, color='#26C6DA', linewidth=1.5, linestyle='--', zorder=5)
    ax.text(L/2 + 0.05, h + col_h * 0.6, 'LINDERO',
            fontsize=7, color='#26C6DA', va='center', rotation=90)

    y_barL = r + db_L / 2
    ax.plot([-L/2 + r, L/2 - r], [y_barL, y_barL],
            color='#EF5350', linewidth=3.5, solid_capstyle='round', zorder=5)

    y_barB = r + db_L + db_B / 2
    n_circles = min(16, max(4, int((L - 2*r) / res.sep_B))) if res.sep_B else 8
    for i in range(n_circles):
        xc = -L/2 + r + i * (L - 2*r) / max(n_circles - 1, 1)
        circ = mpatches.Circle((xc, y_barB), db_B / 2, color='#AB47BC', zorder=6)
        ax.add_patch(circ)

    if abs(ex) > 0.01:
        y_ex_lbl = h * 0.55
        ax.annotate('', xy=(ex, y_ex_lbl), xytext=(0, y_ex_lbl),
                    arrowprops=dict(arrowstyle='<->', color='#26C6DA', lw=1.2))
        ax.text(ex / 2, y_ex_lbl + 0.04, f'ex={ex:.3f} m',
                ha='center', va='bottom', fontsize=7.5, color='#26C6DA', fontweight='bold')

    x_dim_h = L/2 + 0.20
    ax.annotate('', xy=(x_dim_h, h), xytext=(x_dim_h, 0),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1))
    ax.text(x_dim_h + 0.05, h / 2, f'h={h:.2f} m',
            va='center', ha='left', fontsize=8, color='white')

    y_dim_L = -(p_max + 0.22)
    ax.annotate('', xy=(L/2, y_dim_L), xytext=(-L/2, y_dim_L),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1))
    ax.text(0, y_dim_L - 0.06, f'L = {L:.2f} m',
            ha='center', va='top', fontsize=9, fontweight='bold', color='#85B7EB')

    y_leg = y_dim_L - 0.22
    ax.text(-L/2, y_leg,
            f'Arm. dir.L (— en sección):  '
            f'{res.varilla_L or "—"} @ {(res.sep_L or 0)*100:.0f} cm   '
            f'As = {res.As_dis_L or 0:.2f} cm²/m',
            ha='left', va='top', fontsize=7.5, color='#EF5350')
    ax.text(-L/2, y_leg - 0.14,
            f'Arm. dir.B (● en sección):  '
            f'{res.varilla_B or "—"} @ {(res.sep_B or 0)*100:.0f} cm   '
            f'As = {res.As_dis_B or 0:.2f} cm²/m',
            ha='left', va='top', fontsize=7.5, color='#AB47BC')

    x_margin = max(p_left, p_right) * 0.4 + 0.55
    ax.set_xlim(-L/2 - x_margin, L/2 + x_margin)
    ax.set_ylim(y_leg - 0.20, h + col_h + 0.30)

    fig.subplots_adjust(left=0.03, right=0.97, top=0.93, bottom=0.05, wspace=0.30)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


@app.get("/zapata-excentrica/fachada", response_class=HTMLResponse)
async def zapata_fachada_page():
    return (Path(ROOT / "web" / "static" / "fachada.html")).read_text(encoding="utf-8")


@app.post("/api/fachada/calcular")
async def api_fachada_calcular(datos: DatosFachadaEntrada):
    try:
        force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
        motor = _build_motor_fachada(datos)
        res   = motor.res
        col   = motor.columna

        if res.B == 0:
            error_msgs = [m["texto"] for m in res.mensajes if m["tipo"] == "error"]
            msg = error_msgs[0] if error_msgs else "Presión neta ≤ 0. Verifique qa, Df y γ suelo."
            return JSONResponse({"error": msg}, status_code=422)

        def pc(v): return float(UnitConverter.from_base(float(v), pressure_unit, 'pressure'))
        def fc(v): return float(UnitConverter.from_base(float(v), force_unit, 'force'))

        return JSONResponse({
            "B": float(res.B), "L": float(res.L), "h": float(res.h),
            "d": float(res.d), "A": float(res.A),
            "ex_geom": float(motor.ex_geom), "ey_geom": float(motor.ey_geom),
            "vuelo_borde": float(res.L / 2 - abs(motor.ex_geom) - col.cx / 2),
            "Mequiv_x":  float(motor.carga.Mser_x),
            "Mequiv_xu": float(motor.carga.Mux),
            "T_atado":   float(motor.T_atado),
            "L_atado":   float(motor.L_atado),
            "tipo_contacto": str(res.tipo_contacto),
            "q1": pc(res.q1), "q2": pc(res.q2),
            "q3": pc(res.q3), "q4": pc(res.q4),
            "q_max": pc(res.q_max), "q_min": pc(res.q_min),
            "ok_presion": bool(res.ok_presion), "ok_tension": bool(res.ok_tension),
            "q1u": pc(res.q1u), "q2u": pc(res.q2u),
            "q3u": pc(res.q3u), "q4u": pc(res.q4u),
            "q_max_u": pc(res.q_max_u), "q_min_u": pc(res.q_min_u),
            "ok_punzonado":  bool(res.ok_punzonado),
            "ok_cortante_L": bool(res.ok_cortante_L),
            "ok_cortante_B": bool(res.ok_cortante_B),
            "Vpu": fc(res.Vpu), "phi_Vpn": fc(res.phi_Vpn),
            "Vu_L": float(res.Vu_L), "Vu_B": float(res.Vu_B),
            "phi_Vn": float(res.phi_Vn),
            "Mu_L": float(res.Mu_L), "Mu_B": float(res.Mu_B),
            "As_req_L": float(res.As_req_L), "As_min_L": float(res.As_min_L),
            "As_dis_L": float(res.As_dis_L),
            "varilla_L": str(res.varilla_L), "sep_L": float(res.sep_L),
            "n_barras_L": int(res.n_barras_L),
            "As_req_B": float(res.As_req_B), "As_min_B": float(res.As_min_B),
            "As_dis_B": float(res.As_dis_B),
            "varilla_B": str(res.varilla_B), "sep_B": float(res.sep_B),
            "n_barras_B": int(res.n_barras_B),
            "mensajes": res.mensajes,
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/fachada/plot/seccion")
async def api_fachada_plot_seccion(datos: DatosFachadaEntrada):
    motor = _build_motor_fachada(datos)
    buf   = _dibujar_seccion_fachada_bytes(motor)
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/fachada/report/pdf")
async def api_fachada_report_pdf(datos: DatosFachadaEntrada):
    motor = _build_motor_fachada(datos)
    datos_entrada = {"norma": datos.norma, "unidades": datos.unidades}
    buf_sec = _dibujar_seccion_fachada_bytes(motor)
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp_sec = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    tmp_pdf.close(); tmp_sec.close()
    with open(tmp_sec.name, 'wb') as f:
        f.write(buf_sec.getvalue())
    gen = GeneradorPDFFachada()
    try:
        gen.generar(tmp_pdf.name, motor, datos_entrada, imagen_seccion=tmp_sec.name)
        with open(tmp_pdf.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes, media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="memoria_zapata_fachada.pdf"'},
        )
    finally:
        for p in (tmp_pdf.name, tmp_sec.name):
            try: os.unlink(p)
            except Exception: pass


@app.post("/api/fachada/report/dxf")
async def api_fachada_report_dxf(datos: DatosFachadaEntrada):
    motor = _build_motor_fachada(datos)
    gen   = GeneradorDXFFachada()
    tmp   = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
    tmp.close()
    try:
        gen.generar(tmp.name, motor, datos.norma)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes, media_type='application/dxf',
            headers={'Content-Disposition': 'attachment; filename="zapata_fachada.dxf"'},
        )
    finally:
        try: os.unlink(tmp.name)
        except Exception: pass


# ─── Module 4: Losa de Fundación ──────────────────────────────────────────────

class DatosLosaEntrada(BaseModel):
    modo:       str   = "grilla"    # 'global' | 'grilla' | 'uniforme'
    # Cargas — modo global
    Pd:         float = 0.0
    Pl:         float = 0.0
    Mdx:        float = 0.0
    Mlx:        float = 0.0
    Mdy:        float = 0.0
    Mly:        float = 0.0
    n_col:      int   = 4
    # Cargas — modo grilla
    Pd_total:   float = 0.0
    Pl_total:   float = 0.0
    nx:         int   = 2
    ny:         int   = 2
    spacing_x:  float = 5.0
    spacing_y:  float = 5.0
    # Cargas — modo uniforme
    q_D:        float = 0.0
    q_L:        float = 0.0
    # Geometría
    L:          float = 0.0
    B:          float = 0.0
    h:          float = 0.40
    recubrimiento: float = 0.075
    cx:         float = 0.35
    cy:         float = 0.35
    lx_span:    float = 5.0
    ly_span:    float = 5.0
    vuelo_x:    float = 0.50
    vuelo_y:    float = 0.50
    # Suelo
    qa:         float = 100.0
    Df:         float = 0.50
    gamma_s:    float = 18.0
    # Materiales
    fck:        float = 25.0
    fy:         float = 420.0
    norma:      str   = "ACI318"
    unidades:   str   = "kN_kN/m2"
    varilla_pref: Optional[str] = ""


def _build_motor_losa(datos: DatosLosaEntrada) -> LosaFundacion:
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    f  = lambda v: UnitConverter.to_base(v, force_unit, 'force')
    p  = lambda v: UnitConverter.to_base(v, pressure_unit, 'pressure')

    suelo    = SueloLosa(qa=p(datos.qa), Df=datos.Df, gamma_suelo=datos.gamma_s)
    hormigon = MaterialHormigon(fck=datos.fck)
    acero    = MaterialAcero(fy=datos.fy)
    norma    = NORMAS_MAP.get(datos.norma, ACI318)()

    modo = datos.modo
    if modo == LosaFundacion.MODO_GRILLA:
        carga = CargaGrilla(
            Pd_total=f(datos.Pd_total), Pl_total=f(datos.Pl_total),
            nx=datos.nx, ny=datos.ny,
            spacing_x=datos.spacing_x, spacing_y=datos.spacing_y,
            vuelo_x=datos.vuelo_x, vuelo_y=datos.vuelo_y,
        )
        geo = GeometriaLosa(
            h=datos.h, recubrimiento=datos.recubrimiento,
            cx=datos.cx, cy=datos.cy,
        )
    elif modo == LosaFundacion.MODO_UNIFORME:
        carga = CargaUniforme(q_D=p(datos.q_D), q_L=p(datos.q_L))
        geo = GeometriaLosa(
            L=datos.L, B=datos.B,
            h=datos.h, recubrimiento=datos.recubrimiento,
            cx=datos.cx, cy=datos.cy,
            lx_span=datos.lx_span, ly_span=datos.ly_span,
            vuelo_x=datos.vuelo_x, vuelo_y=datos.vuelo_y,
        )
    else:  # global
        carga = CargaGlobal(
            Pd=f(datos.Pd), Pl=f(datos.Pl),
            Mdx=f(datos.Mdx), Mlx=f(datos.Mlx),
            Mdy=f(datos.Mdy), Mly=f(datos.Mly),
            n_col=datos.n_col,
        )
        geo = GeometriaLosa(
            L=datos.L, B=datos.B,
            h=datos.h, recubrimiento=datos.recubrimiento,
            cx=datos.cx, cy=datos.cy,
            lx_span=datos.lx_span, ly_span=datos.ly_span,
            vuelo_x=datos.vuelo_x, vuelo_y=datos.vuelo_y,
        )

    motor = LosaFundacion(modo, carga, suelo, hormigon, acero, norma, geo,
                          varilla_pref=datos.varilla_pref or "")
    motor.calcular()
    return motor


def _dibujar_seccion_losa_bytes(motor: LosaFundacion) -> io.BytesIO:
    """Vista en planta (izq) + sección transversal (der arriba) + leyenda armadura (der abajo)."""
    import matplotlib.patches as mpatches
    from matplotlib.gridspec import GridSpec

    res = motor.res
    geo = motor.geo
    L   = res.L or 5.0
    B   = res.B or 5.0
    h   = res.h
    cx  = geo.cx
    cy  = geo.cy
    r   = geo.recubrimiento

    # GridSpec: plan a la izquierda (col 0, ambas filas),
    #           sección arriba-derecha, leyenda abajo-derecha
    fig = plt.figure(figsize=(15, 8), facecolor='#0a1929')
    gs  = GridSpec(2, 2, figure=fig,
                   width_ratios=[1, 1.5],
                   height_ratios=[3.5, 1.2],
                   hspace=0.10, wspace=0.28)

    ap     = fig.add_subplot(gs[:, 0])   # planta — columna izquierda completa
    ax     = fig.add_subplot(gs[0, 1])   # sección — arriba derecha
    ax_leg = fig.add_subplot(gs[1, 1])   # leyenda — abajo derecha

    for a in (ap, ax, ax_leg):
        a.set_facecolor('#0a1929')

    # ── PLANTA ────────────────────────────────────────────────────────────────
    ap.set_aspect('equal')
    ap.axis('off')

    ap.add_patch(plt.Rectangle((-B/2, -L/2), B, L,
                 facecolor='#142233', edgecolor='#378ADD', lw=1.5))

    # ── Franjas de momento (ACI strip method) ─────────────────────────────────
    modo = motor.modo
    lx_s = geo.lx_span
    ly_s = geo.ly_span
    cs_hw = min(lx_s, ly_s) / 4   # franja de columna half-width (ACI: min(lx,ly)/4)

    if modo == LosaFundacion.MODO_GRILLA and hasattr(motor.carga, 'nx'):
        c = motor.carga
        col_xs = [-(c.nx-1)*c.spacing_x/2 + i*c.spacing_x for i in range(c.nx)]
        col_ys = [-(c.ny-1)*c.spacing_y/2 + j*c.spacing_y for j in range(c.ny)]
    else:
        col_xs = [0.0]
        col_ys = [0.0]

    # Franja media base (momento positivo — azul claro)
    ap.add_patch(plt.Rectangle((-B/2, -L/2), B, L,
                 facecolor='#1565C0', alpha=0.12, zorder=1))

    # Franjas de columna en X (bandas verticales, momento negativo — naranja/rojo)
    for xc in col_xs:
        x0 = max(xc - cs_hw, -B/2);  x1 = min(xc + cs_hw, B/2)
        if x1 > x0:
            ap.add_patch(plt.Rectangle((x0, -L/2), x1-x0, L,
                         facecolor='#E53935', alpha=0.20, zorder=2))

    # Franjas de columna en Y (bandas horizontales)
    for yc in col_ys:
        y0 = max(yc - cs_hw, -L/2);  y1 = min(yc + cs_hw, L/2)
        if y1 > y0:
            ap.add_patch(plt.Rectangle((-B/2, y0), B, y1-y0,
                         facecolor='#E53935', alpha=0.20, zorder=2))

    # Intersección franja-X ∩ franja-Y (zona de máximo momento negativo)
    for xc in col_xs:
        for yc in col_ys:
            x0 = max(xc - cs_hw, -B/2);  x1 = min(xc + cs_hw, B/2)
            y0 = max(yc - cs_hw, -L/2);  y1 = min(yc + cs_hw, L/2)
            if x1 > x0 and y1 > y0:
                ap.add_patch(plt.Rectangle((x0, y0), x1-x0, y1-y0,
                             facecolor='#B71C1C', alpha=0.28, zorder=3))

    # Etiquetas de momento (solo modo columna simple para no saturar)
    if len(col_xs) == 1 and len(col_ys) == 1:
        ap.text(0, 0, f"M⁻={res.Mu_sup_x:.0f}\nkN·m/m",
                ha='center', va='center', fontsize=7.5, color='#FF8A80',
                zorder=9, linespacing=1.4)
        mid_x = (B/2 + cs_hw) / 2
        if mid_x > cs_hw * 1.3:
            for sx in [mid_x, -mid_x]:
                ap.text(sx, 0, f"M⁺={res.Mu_inf_x:.0f}",
                        ha='center', va='center', fontsize=7, color='#90CAF9', zorder=9)

    # Mini-leyenda de franjas
    dim = max(B, L) * 0.12
    ap.scatter([-B/2 + dim*0.18], [L/2 - dim*0.20], s=60,
               color='#EF9A9A', marker='s', zorder=10)
    ap.text(-B/2 + dim*0.35, L/2 - dim*0.20, "Fr. columna (M⁻)",
            ha='left', va='center', fontsize=7, color='#EF9A9A')
    ap.scatter([-B/2 + dim*0.18], [L/2 - dim*0.40], s=60,
               color='#90CAF9', marker='s', zorder=10)
    ap.text(-B/2 + dim*0.35, L/2 - dim*0.40, "Fr. media (M⁺)",
            ha='left', va='center', fontsize=7, color='#90CAF9')

    if modo == LosaFundacion.MODO_GRILLA and hasattr(motor.carga, 'nx'):
        c = motor.carga
        for i in range(c.nx):
            for j in range(c.ny):
                xc = -(c.nx-1)*c.spacing_x/2 + i*c.spacing_x
                yc = -(c.ny-1)*c.spacing_y/2 + j*c.spacing_y
                ap.add_patch(plt.Rectangle(
                    (xc - cx/2, yc - cy/2), cx, cy,
                    facecolor='#546E7A', edgecolor='#90A4AE', lw=0.8, zorder=8))
    else:
        ap.add_patch(plt.Rectangle((-cx/2, -cy/2), cx, cy,
                     facecolor='#546E7A', edgecolor='#90A4AE', lw=1.0, zorder=8))

    dim = max(B, L) * 0.12
    ap.annotate('', xy=(B/2, -L/2-dim*0.75), xytext=(-B/2, -L/2-dim*0.75),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ap.text(0, -L/2-dim*0.98, f"B = {B:.2f} m", ha='center', va='top',
            fontsize=9, color='#85B7EB', fontweight='bold')
    ap.annotate('', xy=(B/2+dim*0.75, L/2), xytext=(B/2+dim*0.75, -L/2),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ap.text(B/2+dim*0.90, 0, f"L = {L:.2f} m", ha='left', va='center',
            fontsize=9, color='#85B7EB', fontweight='bold', rotation=90)
    ap.text(0, L/2+dim*0.28, f"lx = {geo.lx_span:.1f} m  |  ly = {geo.ly_span:.1f} m",
            ha='center', va='bottom', fontsize=8.5, color='#EF9F27')
    ap.set_title("Vista en Planta", color='#85B7EB', fontsize=12, pad=10)

    pad = max(B, L) * 0.28
    ap.set_xlim(-B/2 - pad, B/2 + pad * 1.9)
    ap.set_ylim(-L/2 - pad * 1.4, L/2 + pad * 0.8)

    # ── SECCIÓN TRANSVERSAL (sin aspect='equal' → se estira para llenar el panel) ──
    ax.axis('off')
    col_stub = max(h * 0.65, 0.30)

    # Losa y columna
    ax.add_patch(plt.Rectangle((-B/2, 0), B, h,
                 facecolor='#142233', edgecolor='#378ADD', lw=1.8, zorder=3))
    ax.add_patch(plt.Rectangle((-cx/2, h), cx, col_stub,
                 facecolor='#546E7A', edgecolor='#90A4AE', lw=1.3, zorder=3))

    # 4 capas de armadura — posiciones equiespaciadas dentro del área de acero
    inner_h = max(h - 2*r, h * 0.3)
    y_positions = [
        r + inner_h * 0.88,   # Sup-X (capa exterior superior)
        r + inner_h * 0.62,   # Sup-Y (segunda capa)
        r + inner_h * 0.38,   # Inf-Y (tercera capa)
        r + inner_h * 0.12,   # Inf-X (capa exterior inferior)
    ]
    bar_colors  = ['#EF5350', '#AB47BC', '#26C6DA', '#42A5F5']
    bar_labels  = ['Sup-X', 'Sup-Y', 'Inf-Y', 'Inf-X']

    n_b    = min(14, max(6, round(B / 0.75)))
    xb_all = [-B/2 + r + i*(B-2*r)/(n_b-1) for i in range(n_b)]

    for yb, col_b in zip(y_positions, bar_colors):
        ax.plot([-B/2+r, B/2-r], [yb, yb], color=col_b, lw=2.5, zorder=5)
        ax.scatter(xb_all, [yb]*n_b, s=35, color=col_b, zorder=6)

    # Recubrimiento (flecha izquierda)
    ax.annotate('', xy=(-B/2 + r*0.12, 0), xytext=(-B/2 + r*0.12, r),
                arrowprops=dict(arrowstyle='<->', color='#667', lw=1.0))
    ax.text(-B/2 + r*0.20, r/2, f"r = {r*100:.0f} cm",
            ha='left', va='center', fontsize=8.5, color='#8899AA')

    # Cota h (flecha derecha)
    tick_x = B/2 + B * 0.05
    ax.annotate('', xy=(tick_x, h), xytext=(tick_x, 0),
                arrowprops=dict(arrowstyle='<->', color='white', lw=1.1))
    ax.text(tick_x + B*0.015, h/2, f"h = {h:.2f} m",
            ha='left', va='center', fontsize=10.5, color='white', fontweight='bold')

    # Cota d (flecha gris, desde inf a cara superior)
    d = geo.d
    tick_x2 = tick_x + B*0.13
    ax.annotate('', xy=(tick_x2, h - r), xytext=(tick_x2, r),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=0.9))
    ax.text(tick_x2 + B*0.015, h/2, f"d = {d:.3f} m",
            ha='left', va='center', fontsize=9, color='#85B7EB')

    # Zona de presión bajo la losa
    p_zone = h * 0.70  # altura visual de la presión
    q_max_v = max(res.q_max, 1.0)
    q_min_v = max(res.q_min, 0.0)
    p_left  = q_min_v / q_max_v * p_zone
    p_right = p_zone

    ax.fill_between([-B/2, B/2], [-p_left, -p_right], [0, 0],
                    color='#1565C0', alpha=0.45, zorder=2)
    ax.plot([-B/2, B/2], [-p_left, -p_right], color='#378ADD', lw=1.3)

    # Etiquetas de presión — bien separadas de la losa
    ax.text(-B/2 - B*0.025, -p_left * 0.5,
            f"{res.q_min:.0f}", ha='right', va='center', fontsize=9, color='#85B7EB')
    ax.text(B/2 + B*0.025, -p_right * 0.5,
            f"{res.q_max:.0f}", ha='left', va='center', fontsize=9, color='#85B7EB')
    ax.text(0, -p_right - h*0.08,
            f"q (kN/m²)", ha='center', va='top', fontsize=8, color='#85B7EB')

    # Límites — el ylim amplio es lo que hace que la sección se vea bien separada
    ylim_range = h / 0.22   # la losa ocupa ~22 % de la altura del panel
    y_mid = h / 2
    ax.set_xlim(-B/2 - B*0.08, B/2 + B*0.28)
    ax.set_ylim(y_mid - ylim_range * 0.55, y_mid + ylim_range * 0.45)
    # SIN set_aspect('equal') → matplotlib estira Y para llenar el panel
    ax.set_title("Sección Transversal", color='#85B7EB', fontsize=12, pad=10)

    # ── LEYENDA DE ARMADURA (panel inferior) ─────────────────────────────────
    ax_leg.axis('off')

    legend_data = [
        ('#EF5350', 'Sup-X', res.var_sup_x, res.sep_sup_x, res.As_req_sup_x, res.As_dis_sup_x),
        ('#AB47BC', 'Sup-Y', res.var_sup_y, res.sep_sup_y, res.As_req_sup_y, res.As_dis_sup_y),
        ('#26C6DA', 'Inf-Y', res.var_inf_y, res.sep_inf_y, res.As_req_inf_y, res.As_dis_inf_y),
        ('#42A5F5', 'Inf-X', res.var_inf_x, res.sep_inf_x, res.As_req_inf_x, res.As_dis_inf_x),
    ]

    # Título de la leyenda
    ax_leg.text(0.50, 0.96, "Armadura de diseño — 4 capas",
                ha='center', va='top', fontsize=9.5, color='#85B7EB',
                transform=ax_leg.transAxes, fontweight='bold')

    # Cabecera de columnas
    for cx_h, lbl in [(0.06, 'Capa'), (0.24, 'Varilla'), (0.44, 'Separ.'),
                       (0.60, 'As req.'), (0.78, 'As dis.')]:
        ax_leg.text(cx_h, 0.80, lbl, ha='left', va='top', fontsize=8.5,
                    color='#85B7EB', transform=ax_leg.transAxes)
    ax_leg.axhline(0.76, xmin=0.02, xmax=0.98, color='#378ADD', lw=0.8)

    # Filas de datos
    for idx, (col, lyr, var, sep, as_req, as_dis) in enumerate(legend_data):
        y = 0.65 - idx * 0.175
        # Patch de color
        rect = plt.Rectangle((0.01, y-0.06), 0.035, 0.12,
                              facecolor=col, edgecolor='none',
                              transform=ax_leg.transAxes, clip_on=False)
        ax_leg.add_patch(rect)
        # Datos en columnas
        row = [lyr, var, f"c/{sep*100:.0f} cm",
               f"{as_req:.2f} cm²/m", f"{as_dis:.2f} cm²/m"]
        for cx_h, txt in zip([0.06, 0.24, 0.44, 0.60, 0.78], row):
            bold = (cx_h == 0.78)
            ax_leg.text(cx_h, y, txt, ha='left', va='center', fontsize=9,
                        color='white', transform=ax_leg.transAxes,
                        fontweight='bold' if bold else 'normal')

    fig.subplots_adjust(left=0.02, right=0.97, top=0.94, bottom=0.03,
                        hspace=0.10, wspace=0.28)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


@app.get("/losa-fundacion", response_class=HTMLResponse)
async def losa_page():
    return (ROOT / "web" / "static" / "losa.html").read_text(encoding="utf-8")


@app.post("/api/losa/calcular")
async def api_losa_calcular(datos: DatosLosaEntrada):
    try:
        motor = _build_motor_losa(datos)
        res   = motor.res
        return JSONResponse({
            "L": float(res.L), "B": float(res.B),
            "h": float(res.h), "d": float(res.d), "A": float(res.A),
            "q_max": float(res.q_max), "q_min": float(res.q_min),
            "q_prom": float(res.q_prom),
            "ok_presion": bool(res.ok_presion),
            "en_nucleo":  bool(res.en_nucleo),
            "qu_net_avg": float(res.qu_net_avg),
            "qu_net_max": float(res.qu_net_max),
            "lx_diseno": float(res.lx_diseno),
            "ly_diseno": float(res.ly_diseno),
            "Mu_sup_x":  float(res.Mu_sup_x),  "Mu_inf_x": float(res.Mu_inf_x),
            "Mu_sup_y":  float(res.Mu_sup_y),  "Mu_inf_y": float(res.Mu_inf_y),
            "Mu_neg_x":  float(res.Mu_neg_x),  "Mu_neg_y": float(res.Mu_neg_y),
            "Mu_cant_x": float(res.Mu_cant_x), "Mu_cant_y": float(res.Mu_cant_y),
            "As_min":        float(res.As_min),
            "As_req_sup_x":  float(res.As_req_sup_x),
            "As_req_inf_x":  float(res.As_req_inf_x),
            "As_req_sup_y":  float(res.As_req_sup_y),
            "As_req_inf_y":  float(res.As_req_inf_y),
            "As_dis_sup_x":  float(res.As_dis_sup_x),
            "As_dis_inf_x":  float(res.As_dis_inf_x),
            "As_dis_sup_y":  float(res.As_dis_sup_y),
            "As_dis_inf_y":  float(res.As_dis_inf_y),
            "var_sup_x": str(res.var_sup_x), "sep_sup_x": float(res.sep_sup_x),
            "var_inf_x": str(res.var_inf_x), "sep_inf_x": float(res.sep_inf_x),
            "var_sup_y": str(res.var_sup_y), "sep_sup_y": float(res.sep_sup_y),
            "var_inf_y": str(res.var_inf_y), "sep_inf_y": float(res.sep_inf_y),
            "Pu_col":       float(res.Pu_col),
            "Vu_punch":     float(res.Vu_punch),
            "phi_Vc_punch": float(res.phi_Vc_punch),
            "ok_punzonado": bool(res.ok_punzonado),
            "Vu_cx":    float(res.Vu_cx),   "phi_Vc_cx": float(res.phi_Vc_cx),
            "ok_cx":    bool(res.ok_cx),
            "Vu_cy":    float(res.Vu_cy),   "phi_Vc_cy": float(res.phi_Vc_cy),
            "ok_cy":    bool(res.ok_cy),
            "mensajes": res.mensajes,
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/losa/plot/seccion")
async def api_losa_plot_seccion(datos: DatosLosaEntrada):
    motor = _build_motor_losa(datos)
    buf   = _dibujar_seccion_losa_bytes(motor)
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/losa/report/pdf")
async def api_losa_report_pdf(datos: DatosLosaEntrada):
    try:
        motor = _build_motor_losa(datos)
        force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)

        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp_pdf.close()
        tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        tmp_img.close()

        buf_img = _dibujar_seccion_losa_bytes(motor)
        with open(tmp_img.name, 'wb') as f:
            f.write(buf_img.getvalue())

        datos_entrada = {
            "norma": datos.norma,
            "unidades": {"cargas": force_unit, "presiones": pressure_unit},
            "modo": datos.modo,
            "nx": datos.nx, "ny": datos.ny,
            "lx_span": datos.lx_span, "ly_span": datos.ly_span,
            "n_col": datos.n_col,
            "orig": {
                "Pd_total": datos.Pd_total, "Pl_total": datos.Pl_total,
                "Pd": datos.Pd, "Pl": datos.Pl,
                "q_D": datos.q_D, "q_L": datos.q_L,
                "qa": datos.qa,
            },
        }

        gen = GeneradorPDFLosa()
        gen.generar(tmp_pdf.name, motor, datos_entrada, imagen_seccion=tmp_img.name)

        with open(tmp_pdf.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="memoria_losa_fundacion.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        for p in (tmp_pdf.name, tmp_img.name):
            try: os.unlink(p)
            except Exception: pass


@app.post("/api/losa/report/dxf")
async def api_losa_report_dxf(datos: DatosLosaEntrada):
    try:
        motor = _build_motor_losa(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp.close()
        gen = GeneradorDXFLosa()
        gen.generar(tmp.name, motor, datos.norma)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes,
            media_type='application/octet-stream',
            headers={'Content-Disposition': 'attachment; filename="losa_fundacion.dxf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        try: os.unlink(tmp.name)
        except Exception: pass


# ─── Module 6: Encepado de Pilotes ───────────────────────────────────────────

class DatosEncepado(BaseModel):
    # Cargas
    Pd:  float = 800.0
    Pl:  float = 400.0
    Mdx: float = 0.0
    Mlx: float = 0.0
    Mdy: float = 0.0
    Mly: float = 0.0
    # Columna
    cx: float = 0.40
    cy: float = 0.40
    # Pilote
    D_pil:     float = 0.40
    Qa_pil:    float = 400.0
    modo_pil:  str   = "auto"    # 'auto' | 'manual'
    nx:        int   = 2
    ny:        int   = 2
    spacing_x: float = 0.0       # 0 = auto
    spacing_y: float = 0.0
    vuelo_x:   float = 0.0       # 0 = auto
    vuelo_y:   float = 0.0
    # Encepado
    h:             float = 0.60
    recubrimiento: float = 0.075
    # Materiales
    fck:  float = 25.0
    fy:   float = 420.0
    norma: str  = "ACI318"
    unidades: str = "kN_kN/m2"
    varilla_pref: Optional[str] = ""


def _build_motor_encepado(datos: DatosEncepado) -> Encepado:
    force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)
    f = lambda v: UnitConverter.to_base(v, force_unit, 'force')
    p = lambda v: UnitConverter.to_base(v, pressure_unit, 'pressure')

    carga  = CargaEncepado(
        Pd=f(datos.Pd), Pl=f(datos.Pl),
        Mdx=f(datos.Mdx), Mlx=f(datos.Mlx),
        Mdy=f(datos.Mdy), Mly=f(datos.Mly),
    )
    columna = ColumnaEncepado(cx=datos.cx, cy=datos.cy)
    pilote  = PiloteConfig(
        D=datos.D_pil, Qa=p(datos.Qa_pil),
        modo=datos.modo_pil,
        nx=datos.nx, ny=datos.ny,
        spacing_x=datos.spacing_x, spacing_y=datos.spacing_y,
        vuelo_x=datos.vuelo_x,   vuelo_y=datos.vuelo_y,
    )
    geo      = GeometriaEncepado(h=datos.h, recubrimiento=datos.recubrimiento)
    hormigon = MaterialHormigon(fck=datos.fck)
    acero    = MaterialAcero(fy=datos.fy)
    norma    = NORMAS_MAP.get(datos.norma, ACI318)()

    motor = Encepado(carga, columna, pilote, geo, hormigon, acero, norma,
                     varilla_pref=datos.varilla_pref or "")
    motor.calcular()
    return motor


def _dibujar_encepado_bytes(motor: Encepado) -> io.BytesIO:
    """Vista en planta + sección de encepado de pilotes."""
    import matplotlib.patches as mpatches
    from matplotlib.gridspec import GridSpec
    import matplotlib.colors as mcolors
    import numpy as np

    res  = motor.res
    geo  = motor.geo
    col  = motor.columna
    pil  = motor.pilote
    D    = pil.D
    Qa   = pil.Qa
    L    = res.L or 2.0
    B    = res.B or 2.0
    h    = res.h
    cx   = col.cx
    cy   = col.cy
    r    = geo.recubrimiento
    pos  = res.pile_positions
    load_ser = res.pile_loads_ser
    load_ult = res.pile_loads_ult

    fig = plt.figure(figsize=(14, 7), facecolor='#0a1929')
    gs  = GridSpec(1, 2, figure=fig, width_ratios=[1.1, 1.0], wspace=0.30)
    ap  = fig.add_subplot(gs[0, 0])   # planta
    ax  = fig.add_subplot(gs[0, 1])   # sección

    for a in (ap, ax):
        a.set_facecolor('#0a1929')

    # ── PLANTA ────────────────────────────────────────────────────────────────
    ap.set_aspect('equal')
    ap.axis('off')

    # Encepado
    ap.add_patch(plt.Rectangle((-B/2, -L/2), B, L,
                 facecolor='#142233', edgecolor='#378ADD', lw=1.8, zorder=2))

    # Pilotes coloreados por carga
    cmap_vals = [P / Qa for P in load_ser]
    cmap      = plt.colormaps['RdYlGn_r']

    for (x, y), P, cv in zip(pos, load_ser, cmap_vals):
        color = cmap(min(max(cv, 0.0), 1.2))
        circ  = plt.Circle((x, y), D/2, color=color, zorder=4, lw=1.2,
                            edgecolor='white', linewidth=0.8)
        ap.add_patch(circ)
        if len(pos) <= 12:
            ap.text(x, y, f"{P:.0f}", ha='center', va='center',
                    fontsize=6.5, color='white', fontweight='bold', zorder=5)

    # Columna
    ap.add_patch(plt.Rectangle((-cx/2, -cy/2), cx, cy,
                 facecolor='#546E7A', edgecolor='#90A4AE', lw=1.2, zorder=6))

    # Cotas B y L
    sx  = res.spacing_x
    sy  = res.spacing_y
    dim = max(B, L) * 0.14
    ap.annotate('', xy=(B/2, -L/2-dim*0.7), xytext=(-B/2, -L/2-dim*0.7),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ap.text(0, -L/2-dim*0.95, f"B = {B:.2f} m", ha='center', va='top',
            fontsize=9, color='#85B7EB', fontweight='bold')
    ap.annotate('', xy=(B/2+dim*0.75, L/2), xytext=(B/2+dim*0.75, -L/2),
                arrowprops=dict(arrowstyle='<->', color='#85B7EB', lw=1.2))
    ap.text(B/2+dim*0.90, 0, f"L = {L:.2f} m", ha='left', va='center',
            fontsize=9, color='#85B7EB', fontweight='bold', rotation=90)

    # Pilote info label
    ap.text(0, L/2+dim*0.30,
            f"{res.nx}×{res.ny} pilotes  Ø{D*100:.0f}cm  s={sx:.2f}m  Qa={Qa:.0f}kN",
            ha='center', va='bottom', fontsize=8, color='#EF9F27')
    ap.set_title("Vista en Planta", color='#85B7EB', fontsize=11, pad=8)

    pad = max(B, L) * 0.28
    ap.set_xlim(-B/2-pad, B/2+pad*1.9)
    ap.set_ylim(-L/2-pad*1.3, L/2+pad*0.8)

    # Colorbar (carga relativa)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=mcolors.Normalize(0, Qa))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ap, fraction=0.035, pad=0.03, aspect=20)
    cbar.set_label('Carga por pilote [kN]', color='#85B7EB', fontsize=8)
    cbar.ax.yaxis.set_tick_params(color='#85B7EB')
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#85B7EB', fontsize=7.5)
    cbar.outline.set_edgecolor('#378ADD')

    # ── SECCIÓN (corte en Y=0, vista X) ──────────────────────────────────────
    ax.axis('off')
    col_stub = max(h * 0.6, 0.35)
    pile_vis = max(h * 0.7, 0.50)   # longitud visible del pilote

    # Encepado
    ax.add_patch(plt.Rectangle((-B/2, 0), B, h,
                 facecolor='#142233', edgecolor='#378ADD', lw=1.8, zorder=3))
    # Columna
    ax.add_patch(plt.Rectangle((-cx/2, h), cx, col_stub,
                 facecolor='#546E7A', edgecolor='#90A4AE', lw=1.3, zorder=4))

    # Pilotes en sección (solo la fila central — los de y más cercano a 0)
    y_vals = sorted(set(round(y, 6) for _, y in pos))
    y_row  = min(y_vals, key=lambda yv: abs(yv))
    row_xs = sorted(x for x, y in pos if abs(y - y_row) < 0.001)

    for px in row_xs:
        # Pilote (semicírculo + rectángulo)
        ax.add_patch(mpatches.Wedge((px, 0), D/2, 180, 360,
                     facecolor='#1E3A5F', edgecolor='#378ADD', lw=1.2, zorder=5))
        ax.add_patch(plt.Rectangle((px-D/2, -pile_vis), D, pile_vis,
                     facecolor='#1E3A5F', edgecolor='#378ADD', lw=0.8, zorder=4))

    # Armadura (2 capas: X inferior, Y sobre ella)
    db = 0.014
    y_infx = r + db/2
    y_infy = r + db*1.8
    n_b    = min(14, max(5, round((B - 2*r) / 0.25)))
    xb_all = [-B/2+r + i*(B-2*r)/(n_b-1) for i in range(n_b)]

    for yb, col_b in [(y_infx, '#42A5F5'), (y_infy, '#26C6DA')]:
        ax.plot([-B/2+r, B/2-r], [yb, yb], color=col_b, lw=2.5, zorder=6)
        ax.scatter(xb_all, [yb]*n_b, s=30, color=col_b, zorder=7)

    # Recubrimiento
    ax.annotate('', xy=(-B/2+r*0.12, 0), xytext=(-B/2+r*0.12, r),
                arrowprops=dict(arrowstyle='<->', color='#667', lw=0.9))
    ax.text(-B/2+r*0.18, r/2, f"r={r*100:.0f}cm",
            ha='left', va='center', fontsize=8, color='#8899AA')

    # Cota h
    tick_x = B/2 + B*0.06
    ax.annotate('', xy=(tick_x, h), xytext=(tick_x, 0),
                arrowprops=dict(arrowstyle='<->', color='white', lw=1.1))
    ax.text(tick_x + B*0.02, h/2, f"h = {h:.2f} m",
            ha='left', va='center', fontsize=10, color='white', fontweight='bold')

    # Pilote label
    ax.text(0, -pile_vis - h*0.08,
            f"Ø{D*100:.0f} cm — s = {res.spacing_x:.2f} m",
            ha='center', va='top', fontsize=8.5, color='#85B7EB')

    # Armadura leyenda (transAxes)
    for frac, col_b, lbl in [
        (0.10, '#42A5F5', f"Inf-X: {res.var_x}  c/{res.sep_x*100:.0f}cm  [{res.As_dis_x:.2f} cm²/m]"),
        (0.04, '#26C6DA', f"Inf-Y: {res.var_y}  c/{res.sep_y*100:.0f}cm  [{res.As_dis_y:.2f} cm²/m]"),
    ]:
        rect = plt.Rectangle((0.02, frac-0.025), 0.04, 0.05,
                              facecolor=col_b, transform=ax.transAxes, clip_on=False)
        ax.add_patch(rect)
        ax.text(0.08, frac, lbl, ha='left', va='center', fontsize=8.5,
                color='white', transform=ax.transAxes)

    # Carga máx/mín
    ax.text(1.0, 0.98,
            f"P_max = {res.P_max:.0f} kN\nP_min = {res.P_min:.0f} kN\nQa = {Qa:.0f} kN",
            ha='right', va='top', fontsize=8.5, color='#85B7EB',
            transform=ax.transAxes, linespacing=1.6)

    # Y limits (sin equal aspect)
    ylim_range = h / 0.25
    y_mid = h / 2
    ax.set_xlim(-B/2 - B*0.10, B/2 + B*0.32)
    ax.set_ylim(y_mid - ylim_range*0.55, y_mid + ylim_range*0.45)
    ax.set_title("Sección Transversal", color='#85B7EB', fontsize=11, pad=8)

    fig.subplots_adjust(left=0.03, right=0.96, top=0.92, bottom=0.06, wspace=0.30)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


@app.get("/encepado", response_class=HTMLResponse)
async def encepado_page():
    return (ROOT / "web" / "static" / "encepado.html").read_text(encoding="utf-8")


@app.post("/api/encepado/calcular")
async def api_encepado_calcular(datos: DatosEncepado):
    try:
        motor = _build_motor_encepado(datos)
        res   = motor.res
        return JSONResponse({
            "n": res.n, "nx": res.nx, "ny": res.ny,
            "spacing_x": float(res.spacing_x), "spacing_y": float(res.spacing_y),
            "vuelo_x":   float(res.vuelo_x),   "vuelo_y":   float(res.vuelo_y),
            "L": float(res.L), "B": float(res.B),
            "h": float(res.h), "d": float(res.d), "A": float(res.A),
            "pile_positions": res.pile_positions,
            "pile_loads_ser": [float(p) for p in res.pile_loads_ser],
            "pile_loads_ult": [float(p) for p in res.pile_loads_ult],
            "P_max":   float(res.P_max),   "P_min":   float(res.P_min),
            "P_max_u": float(res.P_max_u), "P_min_u": float(res.P_min_u),
            "ok_capacidad": bool(res.ok_capacidad),
            "ok_tension":   bool(res.ok_tension),
            "Mu_x": float(res.Mu_x), "Mu_y": float(res.Mu_y),
            "As_min":    float(res.As_min),
            "As_req_x":  float(res.As_req_x), "As_dis_x": float(res.As_dis_x),
            "var_x":     str(res.var_x),       "sep_x":    float(res.sep_x),
            "n_barras_x": int(res.n_barras_x),
            "As_req_y":  float(res.As_req_y), "As_dis_y": float(res.As_dis_y),
            "var_y":     str(res.var_y),       "sep_y":    float(res.sep_y),
            "n_barras_y": int(res.n_barras_y),
            "Vu_x":     float(res.Vu_x),     "phi_Vc_x": float(res.phi_Vc_x),
            "ok_cx":    bool(res.ok_cx),
            "Vu_y":     float(res.Vu_y),     "phi_Vc_y": float(res.phi_Vc_y),
            "ok_cy":    bool(res.ok_cy),
            "b0_col":       float(res.b0_col),
            "Vu_punch_col": float(res.Vu_punch_col),
            "phi_Vc_col":   float(res.phi_Vc_col),
            "ok_punch_col": bool(res.ok_punch_col),
            "b0_pil":       float(res.b0_pil),
            "Vu_punch_pil": float(res.Vu_punch_pil),
            "phi_Vc_pil":   float(res.phi_Vc_pil),
            "ok_punch_pil": bool(res.ok_punch_pil),
            "mensajes": res.mensajes,
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/encepado/plot/seccion")
async def api_encepado_plot(datos: DatosEncepado):
    motor = _build_motor_encepado(datos)
    buf   = _dibujar_encepado_bytes(motor)
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/encepado/report/pdf")
async def api_encepado_report_pdf(datos: DatosEncepado):
    try:
        motor = _build_motor_encepado(datos)
        force_unit, pressure_unit = UnitConverter.parse_units(datos.unidades)

        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp_pdf.close()
        tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        tmp_img.close()

        buf_img = _dibujar_encepado_bytes(motor)
        with open(tmp_img.name, 'wb') as f:
            f.write(buf_img.getvalue())

        datos_entrada = {
            "norma": datos.norma,
            "unidades": {"cargas": force_unit, "presiones": pressure_unit},
            "Pd": datos.Pd, "Pl": datos.Pl,
            "Mdx": datos.Mdx, "Mlx": datos.Mlx,
            "Mdy": datos.Mdy, "Mly": datos.Mly,
            "cx": datos.cx, "cy": datos.cy,
            "D_pil": datos.D_pil, "Qa_pil": datos.Qa_pil,
            "modo_pil": datos.modo_pil,
            "nx": datos.nx, "ny": datos.ny,
            "spacing_x": datos.spacing_x, "spacing_y": datos.spacing_y,
            "vuelo_x": datos.vuelo_x, "vuelo_y": datos.vuelo_y,
            "h": datos.h, "recubrimiento": datos.recubrimiento,
            "fck": datos.fck, "fy": datos.fy,
        }

        gen = GeneradorPDFEncepado()
        gen.generar(tmp_pdf.name, motor, datos_entrada, imagen_seccion=tmp_img.name)

        with open(tmp_pdf.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="memoria_encepado_pilotes.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        for p in (tmp_pdf.name, tmp_img.name):
            try: os.unlink(p)
            except Exception: pass


@app.post("/api/encepado/report/dxf")
async def api_encepado_report_dxf(datos: DatosEncepado):
    try:
        motor = _build_motor_encepado(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp.close()
        gen = GeneradorDXFEncepado()
        gen.generar(tmp.name, motor, datos.norma)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes,
            media_type='application/octet-stream',
            headers={'Content-Disposition': 'attachment; filename="encepado_pilotes.dxf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        try: os.unlink(tmp.name)
        except Exception: pass


# ─── Module 7: Viga de Fundación ─────────────────────────────────────────────

class DatosViga(BaseModel):
    columnas: list  # [{"x": float, "Pd": float, "Pl": float, "etiqueta": str}, ...]
    B: float = 0.60
    h: float = 0.80
    recubrimiento: float = 0.075
    vuelo_izq: float = 0.50
    vuelo_der: float = 0.50
    ks: float = 20000.0
    qa: float = 150.0
    fck: float = 25.0
    fy: float = 420.0
    norma: str = "ACI318"
    varilla_pref: Optional[str] = ""
    unidades: str = "kN_kN/m2"


def _build_motor_viga(datos: DatosViga) -> VigaFundacion:
    fu, pu = UnitConverter.parse_units(datos.unidades)
    cols = [
        CargaColumnaViga(
            x=float(c["x"]),
            Pd=UnitConverter.to_base(float(c["Pd"]), fu, 'force'),
            Pl=UnitConverter.to_base(float(c["Pl"]), fu, 'force'),
            etiqueta=str(c.get("etiqueta", "")),
        )
        for c in datos.columnas
    ]
    # Calcular L automáticamente a partir de posiciones de columnas
    x_vals = [c.x for c in cols]
    x_min = min(x_vals)
    x_max = max(x_vals)
    L = x_max - x_min + datos.vuelo_izq + datos.vuelo_der
    # Ajustar posiciones al sistema local (0 a L)
    for c in cols:
        c.x = c.x - x_min + datos.vuelo_izq
    geo = GeometriaViga(
        L=L,
        B=datos.B,
        h=datos.h,
        recubrimiento=datos.recubrimiento,
        vuelo_izq=datos.vuelo_izq,
        vuelo_der=datos.vuelo_der,
    )
    suelo = SueloViga(ks=datos.ks, qa=UnitConverter.to_base(datos.qa, pu, 'pressure'))
    hormigon = MaterialHormigon(fck=datos.fck)
    acero = MaterialAcero(fy=datos.fy)
    norma = NORMAS_MAP.get(datos.norma, ACI318)()
    motor = VigaFundacion(
        cols, suelo, geo, hormigon, acero, norma,
        varilla_pref=datos.varilla_pref or "",
    )
    motor.calcular()
    return motor


def _dibujar_viga_bytes(motor: VigaFundacion) -> io.BytesIO:
    """Genera 4 subplots: deformada, presión de contacto, cortante, momento."""
    import numpy as np

    res = motor.res
    x = res.x_grid
    y = res.y_grid
    q = res.q_grid
    V = res.V_grid
    M = res.M_grid
    qa = motor.suelo.qa
    cols = motor.columnas

    fig, axes = plt.subplots(4, 1, figsize=(12, 11), facecolor='#0a1929')
    fig.subplots_adjust(hspace=0.45, left=0.09, right=0.97, top=0.93, bottom=0.06)

    titles = [
        'Deformada y(x) [mm]',
        'Presión de contacto q(x) [kN/m²]',
        'Cortante V(x) [kN]',
        'Momento M(x) [kN·m]',
    ]
    colors_fill = ['#378ADD', '#EF9F27', '#42A5F5', '#66BB6A']
    datasets = [
        [yi * 1000.0 for yi in y],   # m → mm
        q,
        V,
        M,
    ]

    for i, (ax, title, data, cfill) in enumerate(zip(axes, titles, datasets, colors_fill)):
        ax.set_facecolor('#0D1B2A')
        for sp in ax.spines.values():
            sp.set_edgecolor('#1E3A5F')
        ax.tick_params(colors='#85B7EB', labelsize=8)
        ax.set_title(title, color='#85B7EB', fontsize=9, pad=4)
        ax.set_xlim(min(x), max(x))
        ax.set_xlabel('x [m]', color='#85B7EB', fontsize=8)

        if len(x) == len(data):
            zeros = [0.0] * len(x)
            ax.plot(x, data, color=cfill, lw=1.4, zorder=3)
            ax.fill_between(x, zeros, data, color=cfill, alpha=0.25, zorder=2)

        # Línea de referencia qa en gráfico de presión
        if i == 1:
            ax.axhline(qa, color='#EF5350', lw=1.2, linestyle='--', label=f'qa={qa:.0f}')
            ax.legend(fontsize=7.5, facecolor='#0D1B2A', edgecolor='#1E3A5F',
                      labelcolor='#85B7EB', loc='upper right')

        # Línea cero
        ax.axhline(0, color='#445566', lw=0.8, zorder=1)

        # Marcar posiciones de columnas
        for col in cols:
            ax.axvline(col.x, color='#F9A825', lw=0.8, linestyle=':', alpha=0.8, zorder=4)
            if i == 0:
                ax.text(col.x, ax.get_ylim()[1] if ax.get_ylim()[1] != 1.0 else 0,
                        col.etiqueta or '', ha='center', va='bottom',
                        fontsize=7, color='#F9A825')

    fig.suptitle('Viga de Fundación — Winkler MEF', color='#85B7EB', fontsize=11, y=0.98)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


@app.get("/viga", response_class=HTMLResponse)
async def viga_page():
    return (ROOT / "web" / "static" / "viga.html").read_text(encoding="utf-8")


@app.post("/api/viga/calcular")
async def api_viga_calcular(datos: DatosViga):
    try:
        motor = _build_motor_viga(datos)
        res = motor.res
        return JSONResponse({
            "L":           float(res.L),
            "B":           float(res.B),
            "h":           float(res.h),
            "d":           float(res.d),
            "lambda_char": float(res.lambda_char),
            "L_char":      float(res.L_char),
            "flexible":    bool(res.flexible),
            "q_max":       float(res.q_max),
            "qa":          float(motor.suelo.qa),
            "ok_presion":  bool(res.ok_presion),
            "M_max_pos":   float(res.M_max_pos),
            "M_max_neg":   float(res.M_max_neg),
            "V_max":       float(res.V_max),
            "As_min":      float(res.As_min),
            "As_req_inf":  float(res.As_req_inf),
            "As_dis_inf":  float(res.As_dis_inf),
            "var_inf":     str(res.var_inf),
            "sep_inf":     float(res.sep_inf),
            "n_barras_inf": int(res.n_inf),
            "As_req_sup":  float(res.As_req_sup),
            "As_dis_sup":  float(res.As_dis_sup),
            "var_sup":     str(res.var_sup),
            "sep_sup":     float(res.sep_sup),
            "n_barras_sup": int(res.n_sup),
            "Vu_max":      float(res.Vu_max),
            "phi_Vc":      float(res.phi_Vc),
            "ok_cortante": bool(res.ok_cortante),
            "Av_s":        float(res.Av_s),
            "var_estribo": str(res.var_estribo),
            "s_estribo":   float(res.s_estribo),
            "mensajes":    res.mensajes,
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/viga/plot/diagramas")
async def api_viga_plot(datos: DatosViga):
    try:
        motor = _build_motor_viga(datos)
        buf = _dibujar_viga_bytes(motor)
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/viga/report/pdf")
async def api_viga_report_pdf(datos: DatosViga):
    tmp_pdf = None
    tmp_img = None
    try:
        motor = _build_motor_viga(datos)

        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp_pdf.close()
        tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        tmp_img.close()

        buf_img = _dibujar_viga_bytes(motor)
        with open(tmp_img.name, 'wb') as f:
            f.write(buf_img.getvalue())

        datos_entrada = {
            "norma":         datos.norma,
            "B":             datos.B,
            "h":             datos.h,
            "recubrimiento": datos.recubrimiento,
            "vuelo_izq":     datos.vuelo_izq,
            "vuelo_der":     datos.vuelo_der,
            "ks":            datos.ks,
            "qa":            datos.qa,
            "fck":           datos.fck,
            "fy":            datos.fy,
        }

        gen = GeneradorPDFViga()
        gen.generar(tmp_pdf.name, motor, datos_entrada, imagen_diagramas=tmp_img.name)

        with open(tmp_pdf.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="memoria_viga_fundacion.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        for p in [tmp_pdf, tmp_img]:
            if p:
                try: os.unlink(p.name)
                except Exception: pass


@app.post("/api/viga/report/dxf")
async def api_viga_report_dxf(datos: DatosViga):
    tmp = None
    try:
        motor = _build_motor_viga(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp.close()
        gen = GeneradorDXFViga()
        gen.generar(tmp.name, motor, norma=datos.norma)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes,
            media_type='application/octet-stream',
            headers={'Content-Disposition': 'attachment; filename="viga_fundacion.dxf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


# ── Módulo 8 — Capacidad Portante ────────────────────────────────────────────

class DatosCapacidad(BaseModel):
    phi: float = 30.0
    c: float = 0.0
    gamma: float = 18.0
    Df: float = 1.5
    B: float = 1.5
    L: float = 0.0
    forma: str = "rectangular"
    FS: float = 3.0
    nf_prof: Optional[float] = None
    gamma_sub: Optional[float] = None


def _build_motor_cap(datos: DatosCapacidad) -> CapacidadPortante:
    return CapacidadPortante().calcular(
        phi_deg=datos.phi,
        c=datos.c,
        gamma=datos.gamma,
        Df=datos.Df,
        B=datos.B,
        L=datos.L,
        forma=datos.forma,
        FS=datos.FS,
        nf_prof=datos.nf_prof,
        gamma_sub=datos.gamma_sub,
    )


@app.get("/muros", response_class=HTMLResponse)
async def pagina_muros():
    return (ROOT / "web" / "static" / "muros.html").read_text(encoding="utf-8")


@app.get("/capacidad", response_class=HTMLResponse)
async def pagina_capacidad():
    return (ROOT / "web" / "static" / "capacidad.html").read_text(encoding="utf-8")


@app.post("/api/capacidad/calcular")
async def api_capacidad_calcular(datos: DatosCapacidad):
    try:
        motor = _build_motor_cap(datos)
        res = motor.res
        return JSONResponse({
            "phi":          float(res.phi),
            "c":            float(res.c),
            "gamma_ef":     float(res.gamma_ef),
            "q":            float(res.q),
            "FS":           float(res.FS),
            "qa_conserv":   float(res.qa_conserv),
            "qa_medio":     float(res.qa_medio),
            "ok":           bool(res.ok),
            "metodos": [
                {
                    "nombre":   m.nombre,
                    "Nc":       float(m.Nc),
                    "Nq":       float(m.Nq),
                    "Ngamma":   float(m.Ngamma),
                    "sc":       float(m.sc),
                    "sq":       float(m.sq),
                    "sgamma":   float(m.sgamma),
                    "dc":       float(m.dc),
                    "dq":       float(m.dq),
                    "dgamma":   float(m.dgamma),
                    "q_ult":    float(m.q_ult),
                    "q_adm":    float(m.q_adm),
                }
                for m in res.metodos
            ],
            "mensajes": res.mensajes,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/capacidad/spt")
async def api_capacidad_spt(body: dict):
    try:
        N60     = float(body.get("N60", 20))
        sigma_v = float(body.get("sigma_v", 100))
        Cn      = min(2.0, (100.0 / max(sigma_v, 10.0)) ** 0.5)
        N1_60   = min(N60 * Cn, 100.0)
        phi     = phi_desde_spt(N60, sigma_v)
        return JSONResponse({"phi": phi, "N1_60": round(N1_60, 1), "Cn": round(Cn, 3)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/capacidad/report/pdf")
async def api_capacidad_report_pdf(datos: DatosCapacidad):
    tmp = None
    try:
        motor = _build_motor_cap(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.close()
        datos_entrada = {
            "phi":       datos.phi,
            "c":         datos.c,
            "gamma":     datos.gamma,
            "Df":        datos.Df,
            "B":         datos.B,
            "L":         datos.L,
            "forma":     datos.forma,
            "FS":        datos.FS,
            "nf_prof":   datos.nf_prof,
            "gamma_sub": datos.gamma_sub,
            "norma":     "General",
        }
        gen = GeneradorPDFCapacidad()
        gen.generar(tmp.name, motor, datos_entrada)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="capacidad_portante.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


# ── Módulo 9.1 — Muro en Voladizo ────────────────────────────────────────────

class DatosMuro(BaseModel):
    H:            float = 3.50
    h_zapata:     float = 0.40
    b_base:       float = 0.35
    b_corona:     float = 0.25
    B_punta:      float = 0.60
    B_talon:      float = 2.00
    phi_r:        float = 30.0
    c_r:          float = 0.0
    gamma_r:      float = 18.0
    q_s:          float = 0.0
    phi_f:        float = 30.0
    c_f:          float = 0.0
    gamma_f:      float = 18.0
    qa:           float = 150.0
    gamma_c:      float = 24.0
    fc:           float = 25.0
    fy:           float = 420.0
    recub:        float = 0.07
    delta_factor: float = 0.667
    unidades:     str   = "kN_kN/m2"


def _build_motor_muro(datos: DatosMuro) -> MuroVoladizo:
    fu, pu = UnitConverter.parse_units(datos.unidades)
    return MuroVoladizo().calcular(
        H=datos.H, h_zapata=datos.h_zapata,
        b_base=datos.b_base, b_corona=datos.b_corona,
        B_punta=datos.B_punta, B_talon=datos.B_talon,
        gamma_r=datos.gamma_r, phi_r=datos.phi_r,
        c_r=UnitConverter.to_base(datos.c_r, pu, 'pressure'),
        q_s=UnitConverter.to_base(datos.q_s, pu, 'pressure'),
        gamma_f=datos.gamma_f, phi_f=datos.phi_f,
        c_f=UnitConverter.to_base(datos.c_f, pu, 'pressure'),
        qa=UnitConverter.to_base(datos.qa, pu, 'pressure'),
        gamma_c=datos.gamma_c, fc=datos.fc, fy=datos.fy,
        recub=datos.recub, delta_factor=datos.delta_factor,
    )


@app.get("/muro-voladizo", response_class=HTMLResponse)
async def pagina_muro_voladizo():
    return (ROOT / "web" / "static" / "muro_voladizo.html").read_text(encoding="utf-8")


@app.post("/api/muro/calcular")
async def api_muro_calcular(datos: DatosMuro):
    try:
        motor = _build_motor_muro(datos)
        res = motor.res
        est = res.estabilidad

        def elem(e):
            return {
                "nombre": e.nombre,
                "Mu":     round(float(e.Mu), 4),
                "d":      round(float(e.d), 4),
                "As_req": round(float(e.As_req), 4),
                "As_min": round(float(e.As_min), 4),
                "As_dis": round(float(e.As_dis), 4),
                "barra":  e.barra,
            }

        return JSONResponse({
            "H":       float(res.H),
            "h_fuste": float(res.h_fuste),
            "B_total": float(res.B_total),
            "Ka":      float(res.Ka),
            "estabilidad": {
                "Ka":            float(est.Ka),
                "Ea_gamma":      float(est.Ea_gamma),
                "Ea_q":          float(est.Ea_q),
                "Ea":            float(est.Ea),
                "Mo":            float(est.Mo),
                "W_fuste":       float(est.W_fuste),
                "W_zapata":      float(est.W_zapata),
                "W_talon_soil":  float(est.W_talon_soil),
                "W_q_talon":     float(est.W_q_talon),
                "W_total":       float(est.W_total),
                "Mr":            float(est.Mr),
                "x_R":           float(est.x_R),
                "e":             float(est.e),
                "q_max":         float(est.q_max),
                "q_min":         float(est.q_min),
                "Ep":            float(est.Ep),
                "FS_vuelco":     float(est.FS_vuelco),
                "FS_desliz":     float(est.FS_desliz),
                "ok_vuelco":      bool(est.ok_vuelco),
                "ok_desliz":      bool(est.ok_desliz),
                "ok_presion":     bool(est.ok_presion),
                "ok_excentricidad": bool(est.ok_excentricidad),
                "ok_global":      bool(est.ok_global),
            },
            "fuste":      elem(res.fuste),
            "punta":      elem(res.punta),
            "talon":      elem(res.talon),
            "As_temp":    float(res.As_temp),
            "barra_temp": res.barra_temp,
            "mensajes":   res.mensajes,
            # Flat fields for SVG diagram
            "q_max":      float(est.q_max),
            "q_min":      float(est.q_min),
            "FS_vuelco":  float(est.FS_vuelco),
            "FS_desliz":  float(est.FS_desliz),
            "ok_vuelco":  bool(est.ok_vuelco),
            "ok_desliz":  bool(est.ok_desliz),
            "ok_presion": bool(est.ok_presion),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/muro/report/pdf")
async def api_muro_report_pdf(datos: DatosMuro):
    tmp = None
    try:
        motor = _build_motor_muro(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.close()
        GeneradorPDFMuro().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="muro_voladizo.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


@app.post("/api/muro-voladizo/report/dxf")
async def api_muro_voladizo_dxf(datos: DatosMuro):
    tmp = None
    try:
        motor = _build_motor_muro(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp.close()
        GeneradorDXFMuroVoladizo().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes,
            media_type='application/dxf',
            headers={'Content-Disposition': 'attachment; filename="muro_voladizo.dxf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


# ── Módulo 9.2 — Muro de Gravedad ────────────────────────────────────────────

class DatosMuroGravedad(BaseModel):
    H:            float = 3.00
    b_base:       float = 2.40
    b_corona:     float = 0.80
    h_emb:        float = 0.60
    gamma_muro:   float = 23.0
    phi_r:        float = 30.0
    c_r:          float = 0.0
    gamma_r:      float = 18.0
    q_s:          float = 0.0
    phi_f:        float = 30.0
    c_f:          float = 0.0
    gamma_f:      float = 18.0
    qa:           float = 150.0
    delta_factor: float = 0.667
    unidades:     str   = "kN_kN/m2"


def _build_motor_gravedad(datos: DatosMuroGravedad) -> MuroGravedad:
    fu, pu = UnitConverter.parse_units(datos.unidades)
    return MuroGravedad().calcular(
        H=datos.H, b_base=datos.b_base, b_corona=datos.b_corona,
        h_emb=datos.h_emb, gamma_muro=datos.gamma_muro,
        gamma_r=datos.gamma_r, phi_r=datos.phi_r,
        c_r=UnitConverter.to_base(datos.c_r, pu, 'pressure'),
        q_s=UnitConverter.to_base(datos.q_s, pu, 'pressure'),
        gamma_f=datos.gamma_f, phi_f=datos.phi_f,
        c_f=UnitConverter.to_base(datos.c_f, pu, 'pressure'),
        qa=UnitConverter.to_base(datos.qa, pu, 'pressure'),
        delta_factor=datos.delta_factor,
    )


@app.get("/muro-gravedad", response_class=HTMLResponse)
async def pagina_muro_gravedad():
    return (ROOT / "web" / "static" / "muro_gravedad.html").read_text(encoding="utf-8")


@app.post("/api/muro-gravedad/calcular")
async def api_muro_gravedad_calcular(datos: DatosMuroGravedad):
    try:
        motor = _build_motor_gravedad(datos)
        res   = motor.res
        est   = res.estabilidad

        return JSONResponse({
            "H":          float(res.H),
            "b_base":     float(res.b_base),
            "b_corona":   float(res.b_corona),
            "A_seccion":  float(res.A_seccion),
            "Ka":         float(res.Ka),
            "estabilidad": {
                "Ka":               float(est.Ka),
                "Ea_gamma":         float(est.Ea_gamma),
                "Ea_q":             float(est.Ea_q),
                "Ea":               float(est.Ea),
                "Mo":               float(est.Mo),
                "W_muro":           float(est.W_muro),
                "x_CG":             float(est.x_CG),
                "Mr":               float(est.Mr),
                "x_R":              float(est.x_R),
                "e":                float(est.e),
                "q_max":            float(est.q_max),
                "q_min":            float(est.q_min),
                "Ep":               float(est.Ep),
                "FS_vuelco":        float(est.FS_vuelco),
                "FS_desliz":        float(est.FS_desliz),
                "ok_vuelco":        bool(est.ok_vuelco),
                "ok_desliz":        bool(est.ok_desliz),
                "ok_presion":       bool(est.ok_presion),
                "ok_excentricidad": bool(est.ok_excentricidad),
                "ok_global":        bool(est.ok_global),
            },
            "mensajes": res.mensajes,
            # Campos planos para el diagrama SVG
            "q_max":      float(est.q_max),
            "q_min":      float(est.q_min),
            "FS_vuelco":  float(est.FS_vuelco),
            "FS_desliz":  float(est.FS_desliz),
            "ok_vuelco":  bool(est.ok_vuelco),
            "ok_desliz":  bool(est.ok_desliz),
            "ok_presion": bool(est.ok_presion),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/muro-gravedad/report/pdf")
async def api_muro_gravedad_report_pdf(datos: DatosMuroGravedad):
    tmp = None
    try:
        motor = _build_motor_gravedad(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.close()
        GeneradorPDFMuroGravedad().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="muro_gravedad.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


# ── Módulo 9.3 — Muro de Gaviones ────────────────────────────────────────────

class DatosMuroGaviones(BaseModel):
    N:            int   = 4
    h_capa:       float = 0.50
    b_base:       float = 2.50
    b_corona:     float = 1.00
    h_emb:        float = 0.40
    gamma_g:      float = 18.0
    phi_r:        float = 30.0
    c_r:          float = 0.0
    gamma_r:      float = 18.0
    q_s:          float = 0.0
    phi_f:        float = 30.0
    c_f:          float = 0.0
    gamma_f:      float = 18.0
    qa:           float = 150.0
    phi_gavion:   float = 35.0
    delta_factor: float = 0.667
    unidades:     str   = "kN_kN/m2"


def _build_motor_gaviones(datos: DatosMuroGaviones) -> MuroGaviones:
    fu, pu = UnitConverter.parse_units(datos.unidades)
    return MuroGaviones().calcular(
        N=datos.N, h_capa=datos.h_capa,
        b_base=datos.b_base, b_corona=datos.b_corona,
        h_emb=datos.h_emb, gamma_g=datos.gamma_g,
        phi_r=datos.phi_r,
        c_r=UnitConverter.to_base(datos.c_r, pu, 'pressure'),
        gamma_r=datos.gamma_r,
        q_s=UnitConverter.to_base(datos.q_s, pu, 'pressure'),
        phi_f=datos.phi_f,
        c_f=UnitConverter.to_base(datos.c_f, pu, 'pressure'),
        gamma_f=datos.gamma_f,
        qa=UnitConverter.to_base(datos.qa, pu, 'pressure'),
        phi_gavion=datos.phi_gavion,
        delta_factor=datos.delta_factor,
    )


@app.get("/muro-gaviones", response_class=HTMLResponse)
async def pagina_muro_gaviones():
    return (ROOT / "web" / "static" / "muro_gaviones.html").read_text(encoding="utf-8")


@app.post("/api/muro-gaviones/calcular")
async def api_muro_gaviones_calcular(datos: DatosMuroGaviones):
    try:
        motor = _build_motor_gaviones(datos)
        res   = motor.res
        est   = res.estabilidad

        def vi_dict(vi):
            return {
                "junta":     vi.junta,
                "H_sobre":   round(float(vi.H_sobre), 4),
                "W_sobre":   round(float(vi.W_sobre), 4),
                "Ea_sobre":  round(float(vi.Ea_sobre), 4),
                "FS_desliz": round(float(vi.FS_desliz), 4),
                "ok_desliz": bool(vi.ok_desliz),
            }

        return JSONResponse({
            "H":          float(res.H),
            "N":          int(res.N),
            "h_capa":     float(res.h_capa),
            "b_base":     float(res.b_base),
            "b_corona":   float(res.b_corona),
            "anchos":     [round(float(b), 4) for b in res.anchos],
            "A_seccion":  float(res.A_seccion),
            "Ka":         float(res.Ka),
            "estabilidad": {
                "Ka":               float(est.Ka),
                "Ea_gamma":         float(est.Ea_gamma),
                "Ea_q":             float(est.Ea_q),
                "Ea":               float(est.Ea),
                "Mo":               float(est.Mo),
                "W_total":          float(est.W_total),
                "x_CG":             float(est.x_CG),
                "Mr":               float(est.Mr),
                "x_R":              float(est.x_R),
                "e":                float(est.e),
                "q_max":            float(est.q_max),
                "q_min":            float(est.q_min),
                "Ep":               float(est.Ep),
                "FS_vuelco":        float(est.FS_vuelco),
                "FS_desliz":        float(est.FS_desliz),
                "ok_vuelco":        bool(est.ok_vuelco),
                "ok_desliz":        bool(est.ok_desliz),
                "ok_presion":       bool(est.ok_presion),
                "ok_excentricidad": bool(est.ok_excentricidad),
                "ok_global":        bool(est.ok_global),
            },
            "internas":   [vi_dict(vi) for vi in res.internas],
            "ok_interna": bool(res.ok_interna),
            "mensajes":   res.mensajes,
            # Campos planos para el diagrama SVG
            "q_max":      float(est.q_max),
            "q_min":      float(est.q_min),
            "FS_vuelco":  float(est.FS_vuelco),
            "FS_desliz":  float(est.FS_desliz),
            "ok_vuelco":  bool(est.ok_vuelco),
            "ok_desliz":  bool(est.ok_desliz),
            "ok_presion": bool(est.ok_presion),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/muro-gaviones/report/pdf")
async def api_muro_gaviones_report_pdf(datos: DatosMuroGaviones):
    tmp = None
    try:
        motor = _build_motor_gaviones(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.close()
        GeneradorPDFMuroGaviones().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="muro_gaviones.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


# ── Módulo 9.4 — Muro con Contrafuertes ──────────────────────────────────────

class DatosMuroContrafuertes(BaseModel):
    H:              float = 8.00
    h_zapata:       float = 0.60
    e_pantalla:     float = 0.30
    e_contrafuerte: float = 0.30
    B_punta:        float = 1.20
    B_talon:        float = 5.00
    s:              float = 4.00
    phi_r:          float = 30.0
    c_r:            float = 0.0
    gamma_r:        float = 18.0
    q_s:            float = 0.0
    phi_f:          float = 30.0
    c_f:            float = 0.0
    gamma_f:        float = 18.0
    qa:             float = 150.0
    gamma_c:        float = 24.0
    fc:             float = 25.0
    fy:             float = 420.0
    recub:          float = 0.07
    delta_factor:   float = 0.667
    unidades:       str   = "kN_kN/m2"


def _build_motor_contrafuertes(datos: DatosMuroContrafuertes) -> MuroContrafuertes:
    fu, pu = UnitConverter.parse_units(datos.unidades)
    return MuroContrafuertes().calcular(
        H=datos.H, h_zapata=datos.h_zapata,
        e_pantalla=datos.e_pantalla, e_contrafuerte=datos.e_contrafuerte,
        B_punta=datos.B_punta, B_talon=datos.B_talon, s=datos.s,
        gamma_r=datos.gamma_r, phi_r=datos.phi_r,
        c_r=UnitConverter.to_base(datos.c_r, pu, 'pressure'),
        q_s=UnitConverter.to_base(datos.q_s, pu, 'pressure'),
        gamma_f=datos.gamma_f, phi_f=datos.phi_f,
        c_f=UnitConverter.to_base(datos.c_f, pu, 'pressure'),
        qa=UnitConverter.to_base(datos.qa, pu, 'pressure'),
        gamma_c=datos.gamma_c, fc=datos.fc, fy=datos.fy,
        recub=datos.recub, delta_factor=datos.delta_factor,
    )


@app.get("/muro-contrafuertes", response_class=HTMLResponse)
async def pagina_muro_contrafuertes():
    return (ROOT / "web" / "static" / "muro_contrafuertes.html").read_text(encoding="utf-8")


@app.post("/api/muro-contrafuertes/calcular")
async def api_muro_contrafuertes_calcular(datos: DatosMuroContrafuertes):
    try:
        motor = _build_motor_contrafuertes(datos)
        res   = motor.res
        est   = res.estabilidad

        def elem(e):
            return {
                "nombre":  e.nombre,
                "Mu":      round(float(e.Mu), 4),
                "d":       round(float(e.d), 4),
                "As_req":  round(float(e.As_req), 4),
                "As_min":  round(float(e.As_min), 4),
                "As_dis":  round(float(e.As_dis), 4),
                "barra":   e.barra,
                "nota":    e.nota,
            }

        return JSONResponse({
            "H":       float(res.H),
            "h_fuste": float(res.h_fuste),
            "B_total": float(res.B_total),
            "Ka":      float(res.Ka),
            "s":       float(res.s),
            "L_libre": float(res.L_libre),
            "estabilidad": {
                "Ka":               float(est.Ka),
                "Ea_gamma":         float(est.Ea_gamma),
                "Ea_q":             float(est.Ea_q),
                "Ea":               float(est.Ea),
                "Mo":               float(est.Mo),
                "W_pantalla":       float(est.W_pantalla),
                "W_zapata":         float(est.W_zapata),
                "W_talon_soil":     float(est.W_talon_soil),
                "W_q_talon":        float(est.W_q_talon),
                "W_cont_m":         float(est.W_cont_m),
                "W_total":          float(est.W_total),
                "Mr":               float(est.Mr),
                "x_R":              float(est.x_R),
                "e":                float(est.e),
                "q_max":            float(est.q_max),
                "q_min":            float(est.q_min),
                "Ep":               float(est.Ep),
                "FS_vuelco":        float(est.FS_vuelco),
                "FS_desliz":        float(est.FS_desliz),
                "ok_vuelco":        bool(est.ok_vuelco),
                "ok_desliz":        bool(est.ok_desliz),
                "ok_presion":       bool(est.ok_presion),
                "ok_excentricidad": bool(est.ok_excentricidad),
                "ok_global":        bool(est.ok_global),
            },
            "pantalla_neg":  elem(res.pantalla_neg),
            "pantalla_pos":  elem(res.pantalla_pos),
            "punta":         elem(res.punta),
            "talon":         elem(res.talon),
            "contrafuerte":  elem(res.contrafuerte),
            "mensajes":      res.mensajes,
            # planos para diagrama
            "q_max":      float(est.q_max),
            "q_min":      float(est.q_min),
            "FS_vuelco":  float(est.FS_vuelco),
            "FS_desliz":  float(est.FS_desliz),
            "ok_vuelco":  bool(est.ok_vuelco),
            "ok_desliz":  bool(est.ok_desliz),
            "ok_presion": bool(est.ok_presion),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/muro-contrafuertes/report/pdf")
async def api_muro_contrafuertes_report_pdf(datos: DatosMuroContrafuertes):
    tmp = None
    try:
        motor = _build_motor_contrafuertes(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.close()
        GeneradorPDFMuroContrafuertes().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="muro_contrafuertes.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


# ── Módulo 9.5 — Muro de Sótano ──────────────────────────────────────────────

class DatosMuroSotano(BaseModel):
    H:         float = 3.00
    e_muro:    float = 0.25
    h_NF:      float = 1.50
    condicion: str   = "empotrado_base"
    phi_r:     float = 30.0
    c_r:       float = 0.0
    gamma_r:   float = 18.0
    q_s:       float = 5.0
    gamma_w:   float = 10.0
    fc:        float = 25.0
    fy:        float = 420.0
    recub:     float = 0.04
    gamma_c:   float = 24.0
    unidades:  str   = "kN_kN/m2"


def _build_motor_sotano(datos: DatosMuroSotano) -> MuroSotano:
    fu, pu = UnitConverter.parse_units(datos.unidades)
    return MuroSotano().calcular(
        H=datos.H, e_muro=datos.e_muro, h_NF=datos.h_NF,
        condicion=datos.condicion,
        phi_r=datos.phi_r,
        c_r=UnitConverter.to_base(datos.c_r, pu, 'pressure'),
        gamma_r=datos.gamma_r,
        q_s=UnitConverter.to_base(datos.q_s, pu, 'pressure'),
        gamma_w=datos.gamma_w,
        fc=datos.fc, fy=datos.fy, recub=datos.recub,
        gamma_c=datos.gamma_c,
    )


@app.get("/muro-sotano", response_class=HTMLResponse)
async def pagina_muro_sotano():
    return (ROOT / "web" / "static" / "muro_sotano.html").read_text(encoding="utf-8")


@app.post("/api/muro-sotano/calcular")
async def api_muro_sotano_calcular(datos: DatosMuroSotano):
    try:
        motor = _build_motor_sotano(datos)
        res   = motor.res
        c     = res.cargas
        m     = res.momentos

        def elem(e):
            return {
                "nombre":  e.nombre,
                "Mu":      round(float(e.Mu), 4),
                "d":       round(float(e.d), 4),
                "As_req":  round(float(e.As_req), 4),
                "As_min":  round(float(e.As_min), 4),
                "As_dis":  round(float(e.As_dis), 4),
                "barra":   e.barra,
                "nota":    e.nota,
            }

        return JSONResponse({
            "H":          float(res.H),
            "e_muro":     float(res.e_muro),
            "h_NF":       float(res.h_NF),
            "condicion":  res.condicion,
            "Ka":         float(res.Ka),
            "cargas": {
                "Ka":            float(c.Ka),
                "pa_corona":     float(c.pa_corona),
                "pa_base":       float(c.pa_base),
                "pw_base":       float(c.pw_base),
                "p_total_base":  float(c.p_total_base),
                "Ea":            float(c.Ea),
                "Ew":            float(c.Ew),
                "E_total":       float(c.E_total),
                "tiene_nf":      bool(c.tiene_nf),
            },
            "momentos": {
                "condicion": m.condicion,
                "R_top":     round(float(m.R_top), 4),
                "R_bot":     round(float(m.R_bot), 4),
                "M_base":    round(float(m.M_base), 4),
                "M_max":     round(float(m.M_max), 4),
                "z_max":     round(float(m.z_max), 4),
                "M_corona":  round(float(m.M_corona), 4),
            },
            "vert_cara_suelo": elem(res.vert_cara_suelo),
            "vert_cara_int":   elem(res.vert_cara_int),
            "horiz_temp":      elem(res.horiz_temp),
            "mensajes":        res.mensajes,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/muro-sotano/report/pdf")
async def api_muro_sotano_report_pdf(datos: DatosMuroSotano):
    tmp = None
    try:
        motor = _build_motor_sotano(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.close()
        GeneradorPDFMuroSotano().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="muro_sotano.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


# ── Módulo 6B — Pilote Individual ────────────────────────────────────────────

class DatosPilote(BaseModel):
    D:         float = 0.50
    L:         float = 12.0
    tipo:      str   = "vaciado_in_situ"
    capas:     list  = []
    Qa_dis:    float = 800.0
    FS_min:    float = 2.5
    H_lat:     float = 80.0
    e_lat:     float = 0.0
    tipo_lat:  str   = "granular"
    cu_lat:    float = 50.0
    phi_lat:   float = 32.0
    gamma_lat: float = 18.0
    fc:        float = 25.0
    fy:        float = 420.0
    recub:     float = 0.075
    unidades:  str   = "kN_kN/m2"


def _build_motor_pilote(datos: DatosPilote) -> PiloteIndividual:
    fu, pu = UnitConverter.parse_units(datos.unidades)
    capas_raw = datos.capas or [
        {"tipo": "arcilla", "espesor": 5.0, "gamma": 18.0, "cu": 50, "phi": 0},
        {"tipo": "arena",   "espesor": 8.0, "gamma": 19.0, "cu": 0,  "phi": 32},
    ]
    capas_inp = [
        {**c, "cu": UnitConverter.to_base(float(c.get("cu", 0)), pu, 'pressure')}
        for c in capas_raw
    ]
    return PiloteIndividual().calcular(
        D=datos.D, L=datos.L, tipo=datos.tipo,
        capas_inp=capas_inp,
        Qa_dis=UnitConverter.to_base(datos.Qa_dis, fu, 'force'),
        FS_min=datos.FS_min,
        H_lat=UnitConverter.to_base(datos.H_lat, fu, 'force'),
        e_lat=datos.e_lat,
        tipo_lat=datos.tipo_lat,
        cu_lat=UnitConverter.to_base(datos.cu_lat, pu, 'pressure'),
        phi_lat=datos.phi_lat, gamma_lat=datos.gamma_lat,
        fc=datos.fc, fy=datos.fy, recub=datos.recub,
    )


@app.get("/pilotes", response_class=HTMLResponse)
async def pagina_pilotes_hub():
    return (ROOT / "web" / "static" / "pilotes_hub.html").read_text(encoding="utf-8")


@app.get("/pilote", response_class=HTMLResponse)
async def pagina_pilote():
    return (ROOT / "web" / "static" / "pilote.html").read_text(encoding="utf-8")


@app.post("/api/pilote/calcular")
async def api_pilote_calcular(datos: DatosPilote):
    try:
        motor = _build_motor_pilote(datos)
        res   = motor.res
        ax    = res.axial
        lat   = res.lateral
        rc    = res.rc

        def capa_dict(c):
            return {
                "numero": c.numero, "tipo": c.tipo,
                "espesor": round(c.espesor,3), "gamma": round(c.gamma,2),
                "cu": round(c.cu,2), "phi": round(c.phi,2),
                "z_top": round(c.z_top,3), "z_mid": round(c.z_mid,3),
                "sigma_v": round(c.sigma_v,3),
                "alpha": round(c.alpha,4), "beta": round(c.beta,4),
                "fs": round(c.fs,3), "Qs": round(c.Qs,3),
            }

        return JSONResponse({
            "D": res.D, "L": res.L, "tipo": res.tipo,
            "H_lat": datos.H_lat,
            "axial": {
                "Ag":         round(ax.Ag, 6),
                "capas":      [capa_dict(c) for c in ax.capas],
                "Qs_total":   round(ax.Qs_total, 2),
                "Qp":         round(ax.Qp, 2),
                "Qu":         round(ax.Qu, 2),
                "Qa":         round(ax.Qa, 2),
                "FS_axial":   round(ax.FS_axial, 3),
                "tipo_punta": ax.tipo_punta,
                "Nq_o_Nc":   round(ax.Nq_o_Nc, 2),
            },
            "lateral": {
                "metodo":      lat.metodo,
                "condicion":   lat.condicion,
                "tipo_pilote": lat.tipo_pilote,
                "My":          round(lat.My, 2),
                "Hu":          round(lat.Hu, 2),
                "FS_lateral":  round(lat.FS_lateral, 3),
                "H_dis":       round(lat.H_dis, 2),
                "ok_lateral":  lat.ok_lateral,
                "z_max":       round(lat.z_max, 3),
            },
            "rc": {
                "D":        res.D,
                "Ag":       round(rc.Ag, 6),
                "Ast_req":  round(rc.Ast_req, 3),
                "Ast_min":  round(rc.Ast_min, 3),
                "Ast_max":  round(rc.Ast_max, 3),
                "Ast_dis":  round(rc.Ast_dis, 3),
                "rho_l":    round(rc.rho_l, 5),
                "desc_long": rc.desc_long,
                "rho_s_min": round(rc.rho_s_min, 5),
                "db_esp":    rc.db_esp,
                "paso_esp":  round(rc.paso_esp, 1),
            },
            "mensajes": res.mensajes,
            # planos para diagrama
            "Qu":       round(ax.Qu, 1),
            "Qs_total": round(ax.Qs_total, 1),
            "Qp":       round(ax.Qp, 1),
            "FS_axial": round(ax.FS_axial, 3),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/pilote/report/pdf")
async def api_pilote_report_pdf(datos: DatosPilote):
    tmp = None
    try:
        motor = _build_motor_pilote(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.close()
        GeneradorPDFPilote().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(content=pdf_bytes, media_type='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename="pilote_individual.pdf"'})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


@app.post("/api/pilote/report/dxf")
async def api_pilote_dxf(datos: DatosPilote):
    tmp = None
    try:
        motor = _build_motor_pilote(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp.close()
        GeneradorDXFPilote().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            dxf_bytes = f.read()
        return Response(
            content=dxf_bytes,
            media_type='application/dxf',
            headers={'Content-Disposition': 'attachment; filename="pilote_individual.dxf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


# ── DXF Módulos 9.2 a 9.5 — Muros de Contención ─────────────────────────────

@app.post("/api/muro-gravedad/report/dxf")
async def api_muro_gravedad_dxf(datos: DatosMuroGravedad):
    tmp = None
    try:
        motor = _build_motor_gravedad(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp.close()
        GeneradorDXFMuroGravedad().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            content = f.read()
        return Response(content=content, media_type='application/dxf',
                        headers={'Content-Disposition': 'attachment; filename="muro_gravedad.dxf"'})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


@app.post("/api/muro-gaviones/report/dxf")
async def api_muro_gaviones_dxf(datos: DatosMuroGaviones):
    tmp = None
    try:
        motor = _build_motor_gaviones(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp.close()
        GeneradorDXFMuroGaviones().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            content = f.read()
        return Response(content=content, media_type='application/dxf',
                        headers={'Content-Disposition': 'attachment; filename="muro_gaviones.dxf"'})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


@app.post("/api/muro-contrafuertes/report/dxf")
async def api_muro_contrafuertes_dxf(datos: DatosMuroContrafuertes):
    tmp = None
    try:
        motor = _build_motor_contrafuertes(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp.close()
        GeneradorDXFMuroContrafuertes().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            content = f.read()
        return Response(content=content, media_type='application/dxf',
                        headers={'Content-Disposition': 'attachment; filename="muro_contrafuertes.dxf"'})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


@app.post("/api/muro-sotano/report/dxf")
async def api_muro_sotano_dxf(datos: DatosMuroSotano):
    tmp = None
    try:
        motor = _build_motor_sotano(datos)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp.close()
        GeneradorDXFMuroSotano().generar(tmp.name, motor)
        with open(tmp.name, 'rb') as f:
            content = f.read()
        return Response(content=content, media_type='application/dxf',
                        headers={'Content-Disposition': 'attachment; filename="muro_sotano.dxf"'})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


# ── Módulo 8B — Asentamientos ────────────────────────────────────────────────

@app.get("/asentamientos", response_class=HTMLResponse)
async def pagina_asentamientos():
    return (ROOT / "web" / "static" / "asentamientos.html").read_text(encoding="utf-8")


class DatosSchmertmann(BaseModel):
    B:       float = 2.0
    L:       float = 2.0
    Df:      float = 1.0
    q_total: float = 150.0
    gamma:   float = 18.0
    t:       float = 10.0
    capas:   list  = []


class DatosTerzaghi(BaseModel):
    B:          float = 2.0
    L:          float = 2.0
    q_net:      float = 100.0
    z_mid:      float = 3.0
    H_c:        float = 4.0
    Cc:         float = 0.35
    Cs:         float = 0.07
    e0:         float = 0.85
    sigma0:     float = 80.0
    OCR:        float = 1.0
    Cv:         float = 2.0
    doble_dren: bool  = True


@app.post("/api/asentamientos/schmertmann")
async def api_schmertmann(datos: DatosSchmertmann):
    try:
        motor = AsentamientoSchmertmann().calcular(
            B=datos.B, L=datos.L, Df=datos.Df,
            q_total=datos.q_total, gamma=datos.gamma,
            t=datos.t, capas_inp=datos.capas,
        )
        res = motor.res
        return JSONResponse({
            "delta_i":   round(float(res.delta_i), 3),
            "C1":        round(float(res.C1), 4),
            "C2":        round(float(res.C2), 4),
            "q_net":     round(float(res.q_net), 3),
            "Iz_peak":   round(float(res.Iz_peak), 4),
            "z_peak":    round(float(res.z_peak), 3),
            "z_max":     round(float(res.z_max), 3),
            "suma_Iz_Es": round(float(res.suma_Iz_Es), 8),
            "capas": [
                {
                    "espesor": round(float(c.espesor), 3),
                    "N60":     round(float(c.N60), 1),
                    "tipo":    c.tipo,
                    "Es":      round(float(c.Es), 1),
                    "z_mid":   round(float(c.z_mid), 3),
                    "Iz_mid":  round(float(c.Iz_mid), 4),
                    "contrib": round(float(c.contrib), 8),
                }
                for c in res.capas
            ],
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/asentamientos/terzaghi")
async def api_terzaghi(datos: DatosTerzaghi):
    try:
        motor = AsentamientoTerzaghi().calcular(
            B=datos.B, L=datos.L, q_net=datos.q_net,
            z_mid=datos.z_mid, H_c=datos.H_c,
            Cc=datos.Cc, e0=datos.e0, OCR=datos.OCR,
            sigma0=datos.sigma0, Cs=datos.Cs,
            Cv=datos.Cv, doble_dren=datos.doble_dren,
        )
        res = motor.res
        return JSONResponse({
            "delta_c":   round(float(res.delta_c), 3),
            "delta_c1":  round(float(res.delta_c1), 3),
            "delta_c2":  round(float(res.delta_c2), 3),
            "sigma0":    round(float(res.sigma0), 3),
            "delta_sig": round(float(res.delta_sig), 3),
            "sigma_f":   round(float(res.sigma_f), 3),
            "sigma_p":   round(float(res.sigma_p), 3),
            "es_NC":     bool(res.es_NC),
            "H_dr":      round(float(res.H_dr), 3),
            "t50":       round(float(res.t50), 4),
            "t90":       round(float(res.t90), 4),
            "curva": [
                {"t": p.t, "Tv": p.Tv, "U": p.U, "delta": p.delta}
                for p in res.curva
            ],
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class DatosPDFAsentamientos(BaseModel):
    schmertmann: DatosSchmertmann = None
    terzaghi:    DatosTerzaghi   = None


@app.post("/api/asentamientos/report/pdf")
async def api_asentamientos_pdf(datos: DatosPDFAsentamientos):
    tmp = None
    try:
        ms = mt = None
        if datos.schmertmann:
            ms = AsentamientoSchmertmann().calcular(
                B=datos.schmertmann.B, L=datos.schmertmann.L,
                Df=datos.schmertmann.Df, q_total=datos.schmertmann.q_total,
                gamma=datos.schmertmann.gamma, t=datos.schmertmann.t,
                capas_inp=datos.schmertmann.capas,
            )
        if datos.terzaghi:
            td = datos.terzaghi
            mt = AsentamientoTerzaghi().calcular(
                B=td.B, L=td.L, q_net=td.q_net, z_mid=td.z_mid, H_c=td.H_c,
                Cc=td.Cc, e0=td.e0, OCR=td.OCR, sigma0=td.sigma0, Cs=td.Cs,
                Cv=td.Cv, doble_dren=td.doble_dren,
            )
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.close()
        GeneradorPDFAsentamientos().generar(tmp.name, ms, mt)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="asentamientos.pdf"'},
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.server:app", host="127.0.0.1", port=8000, reload=True)
