@echo off
uv run ruff format .
if %errorlevel% neq 0 exit /b %errorlevel%

uv run ruff check .
if %errorlevel% neq 0 exit /b %errorlevel%

uv run mypy
if %errorlevel% neq 0 exit /b %errorlevel%

uv run pytest
