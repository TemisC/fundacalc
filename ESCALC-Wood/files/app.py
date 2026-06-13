# app.py — ESCALC Suite
# Servidor Flask principal — registra todos los módulos
# Levantar: python app.py  →  http://localhost:5050
# F5 en VS Code con launch.json configurado

from flask import Flask, render_template, redirect

app = Flask(__name__)
app.secret_key = "escalc-dev-2024"

# ── Registrar módulos ──────────────────────────────────────────────────────
# Descomentar a medida que se van creando los módulos

from wood.routes.wood import wood_bp
app.register_blueprint(wood_bp, url_prefix="/wood")

from draw.routes.draw import draw_bp
app.register_blueprint(draw_bp, url_prefix="/draw")

# from foundation.routes.foundation import foundation_bp
# app.register_blueprint(foundation_bp, url_prefix="/foundation")

# from steel.routes.steel import steel_bp
# app.register_blueprint(steel_bp, url_prefix="/steel")

# from elements.routes.elements import elements_bp
# app.register_blueprint(elements_bp, url_prefix="/elements")


# ── Home — portal de módulos ───────────────────────────────────────────────
@app.route("/")
def index():
    modules = [
        {
            "name":    "Wood",
            "sub":     "Roof Rafter — NDS 2024",
            "url":     "/wood/rafter",
            "status":  "active",
            "icon":    "timber",
        },
        {
            "name":    "Draw",
            "sub":     "Visualizador de elementos",
            "url":     "/draw/",
            "status":  "active",
            "icon":    "blueprint",
        },
        {
            "name":    "Foundation",
            "sub":     "Zapatas y pilotes",
            "url":     "/foundation",
            "status":  "wip",
            "icon":    "foundation",
        },
        {
            "name":    "Steel",
            "sub":     "Conexiones AISC",
            "url":     "/steel",
            "status":  "wip",
            "icon":    "steel",
        },
        {
            "name":    "Elements",
            "sub":     "Vigas y columnas",
            "url":     "/elements",
            "status":  "wip",
            "icon":    "beam",
        },
    ]
    return render_template("home.html", modules=modules)


# ── Dev server ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5050, host="0.0.0.0")
