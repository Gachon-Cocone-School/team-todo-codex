#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if ! command -v uv >/dev/null 2>&1; then
    printf '%s\n' "Error: uv is required. Install it before applying fixes." >&2
    exit 1
fi

uv run --locked ruff check . --fix
uv run --locked ruff format .
