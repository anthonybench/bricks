#!/bin/zsh

# Run the sleepybricks test suite.
#
# Usage:
#     ./tools/test.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "${ROOT_DIR}"
uv run pytest tests "$@"
