#!/bin/zsh

# Format shell, Python, and Markdown files for this repository.
#
# Usage:
#     ./tools/format.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SHELL_FILES=("${ROOT_DIR}"/tools/*.sh)

shfmt -w "${SHELL_FILES[@]}"
black "${ROOT_DIR}/sleepybricks" "${ROOT_DIR}/tests"
prettier --write "${ROOT_DIR}/README.md" "${ROOT_DIR}/docs"/*.md
