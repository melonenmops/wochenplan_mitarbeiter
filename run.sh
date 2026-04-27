#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

source "$DIR/.venv/bin/activate"

exec python3 -m app.main
