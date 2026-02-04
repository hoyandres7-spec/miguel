#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
python -m value_alert_bot.cli run --dry-run
