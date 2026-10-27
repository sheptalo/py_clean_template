#!/usr/bin/env bash
# Render every flag combination from this working tree and run its gates on each one.
# Usage: checks/check_matrix.sh   (exit code 0 when every combination passes)
set -uo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
src="$work/template"
rsync -a --exclude .git --exclude .archify --exclude .venv --exclude __pycache__ \
  --exclude .ruff_cache --exclude .pytest_cache --exclude .mypy_cache "$repo/" "$src/"

failed=0

check() {  # dir label command...
  local dir=$1 label=$2
  shift 2
  local log
  if ! log=$(cd "$dir" && "$@" 2>&1); then
    echo "  FAIL $label"
    echo "$log" | tail -n 8 | sed 's/^/       /'
    failed=1
  fi
}

combo() {  # name, then copier answers as key=value
  local name=$1
  shift
  local data=()
  local answer
  for answer in "$@"; do data+=(--data "$answer"); done
  local dest="$work/$name"
  if ! uvx copier copy --trust --defaults --data project_name="$name" "${data[@]}" "$src" "$dest" \
      >"$work/$name.copier.log" 2>&1; then
    echo "FAIL $name: copier"
    tail -n 5 "$work/$name.copier.log"
    failed=1
    return
  fi
  echo "$name"
  check "$dest" "checks folder not rendered" test ! -e checks
  check "$dest" "ruff check" uv run ruff check .
  check "$dest" "ruff format" uv run ruff format --check .
  check "$dest" "mypy" uv run mypy .
  check "$dest" "lint-imports" uv run lint-imports
  check "$dest" "pytest" uv run pytest -q
  if [ -d "$dest/tools" ]; then
    check "$dest" "codegen --check" uv run python -m tools.codegen --check
  fi
  local generated="$dest/$name/presentation/fastapi/generated"
  if [ -d "$generated" ]; then
    printf 'def probe() -> int:\n    return 1\n' > "$generated/probe_user.py"
    check "$dest" "codegen keeps a user file in generated/" \
      sh -c 'uv run python -m tools.codegen >/dev/null && test -f "$1"' sh "$generated/probe_user.py"
  fi
}

combo bare include_fastapi=false include_dishka=false
combo dsh include_fastapi=false include_dishka=true
combo api include_fastapi=true include_dishka=true
combo full include_fastapi=true include_dishka=true include_codegen=true
combo cga include_fastapi=true include_dishka=true include_codegen=true codegen_fastapi=false
combo cgb include_fastapi=false include_dishka=false include_codegen=true
combo nowire include_fastapi=true include_dishka=true auto_wire_ports=false auto_wire_use_cases=false
combo fnd include_fastapi=true include_dishka=false include_codegen=true

if [ "$failed" -eq 0 ]; then
  echo "all combinations passed"
else
  echo "some combinations failed"
fi
exit "$failed"
