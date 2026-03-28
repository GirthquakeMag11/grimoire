#!/bin/bash
set -e

uv run ruff format .
uv run ruff check .
uv run mypy
uv run pytest

# to make it executable, run
# `chmod +x check.sh`
