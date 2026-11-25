#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "$(id -u)" != 0 ]]; then echo 'Run as root: sudo ./install-install.sh'; exit 1; fi
install -m 755 NvidiaFanController.py /usr/local/sbin/NvidiaFanController.py
install -m 644 NvidiaFanController.service /etc/systemd/system/NvidiaFanController.service
systemctl daemon-reload
printf '\nTesting NVML fan control (80%% temporarily, restores auto)...\n'
if ! /usr/bin/python3 /usr/local/sbin/NvidiaFanController.py --test; then
  echo 'TEST FAILED: Service NOT enabled; inspect output above.'
  exit 1
fi
printf '\nTest completed. Enabling the service...\n'
systemctl enable --now NvidiaFanController.service
systemctl --no-pager status NvidiaFanController.service
