#!/bin/bash
# ============================================================
# FundaCalc — Configuración inicial de autenticación
# Ejecutar UNA VEZ en el servidor después del despliegue.
# ============================================================

set -e

APP_DIR="/home/fundacalc/fundacalc"
ENV_FILE="$APP_DIR/.env"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   FundaCalc — Configuración de acceso        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Usuario de acceso
read -p "Nombre de usuario [admin]: " FC_USER
FC_USER="${FC_USER:-admin}"

# Contraseña (con confirmación)
while true; do
    read -s -p "Contraseña: " FC_PASS
    echo ""
    read -s -p "Confirmar contraseña: " FC_PASS2
    echo ""
    if [ "$FC_PASS" = "$FC_PASS2" ]; then
        break
    fi
    echo "❌ Las contraseñas no coinciden. Intenta de nuevo."
done

# Generar hash SHA-256 de la contraseña
FC_HASH=$(echo -n "$FC_PASS" | sha256sum | awk '{print $1}')

# Generar clave secreta aleatoria
FC_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Crear archivo .env
cat > "$ENV_FILE" <<EOF
# FundaCalc — Variables de entorno (NO compartir ni subir a git)
FUNDACALC_SECRET_KEY=$FC_SECRET
FUNDACALC_USER=$FC_USER
FUNDACALC_PASS_HASH=$FC_HASH
EOF

chmod 600 "$ENV_FILE"
chown fundacalc:fundacalc "$ENV_FILE"

echo ""
echo "✅ Archivo .env creado en $ENV_FILE"
echo "   Usuario: $FC_USER"
echo "   Hash:    $FC_HASH"
echo ""
echo "Reiniciando el servicio..."
systemctl restart fundacalc
echo "✅ FundaCalc reiniciado con autenticación activa."
echo ""
echo "Accede en: https://fundacalc.miwebsiteonline.com"
echo ""
