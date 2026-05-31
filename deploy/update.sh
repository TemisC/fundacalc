#!/bin/bash
set -e

echo "==> Actualizando FundaCalc..."
sudo -u fundacalc bash -c "cd /home/fundacalc/fundacalc && git pull"

echo "==> Reiniciando servicio..."
sudo systemctl restart fundacalc

echo "==> Listo. Estado actual:"
sudo systemctl status fundacalc --no-pager -l
