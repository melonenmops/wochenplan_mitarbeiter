#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

source "$DIR/.venv/bin/activate"

python -m app.main

exit $?
