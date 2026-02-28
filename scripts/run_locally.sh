#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/run_locally.sh [repo_url] [clone_dir] [python_cmd]
# Defaults:
#   repo_url: https://github.com/szaboweb/Raid-simulator.git
#   clone_dir: Raid-simulator
#   python_cmd: python3

REPO_URL=${REPO_URL:-https://github.com/szaboweb/Raid-simulator.git}
CLONE_DIR=${CLONE_DIR:-Raid-simulator}
PYTHON_CMD=${PYTHON_CMD:-python3}
NO_VENV=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-venv)
      NO_VENV=1
      shift
      ;;
    --repo)
      REPO_URL="$2"; shift 2
      ;;
    --dir)
      CLONE_DIR="$2"; shift 2
      ;;
    --python)
      PYTHON_CMD="$2"; shift 2
      ;;
    --help)
      echo "Usage: $0 [--no-venv] [--repo URL] [--dir DIR] [--python PYTHON]"; exit 0
      ;;
    *) break ;;
  esac
done

echo "Cloning $REPO_URL into $CLONE_DIR"
if [ -d "$CLONE_DIR" ]; then
  echo "Directory $CLONE_DIR already exists. Skipping clone."
else
  git clone "$REPO_URL" "$CLONE_DIR"
fi

cd "$CLONE_DIR"

# Load .env into environment (if present) for users who prefer dotenv files
if [ -f .env ]; then
  echo "Loading environment from .env"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [ "$NO_VENV" -eq 0 ]; then
  if [ -d ".venv" ]; then
    echo "Using existing .venv"
  else
    echo "Creating virtualenv .venv with $PYTHON_CMD"
    $PYTHON_CMD -m venv .venv
  fi

  # shellcheck source=/dev/null
  source .venv/bin/activate

  echo "Upgrading pip and installing requirements into virtualenv"
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "Skipping virtualenv creation (--no-venv). Installing requirements to user site-packages"
  # Install to user site to avoid requiring sudo
  $PYTHON_CMD -m pip install --upgrade pip --user
  $PYTHON_CMD -m pip install --user -r requirements.txt
fi

echo "Running example simulation (50 rounds)"
${PYTHON_CMD} -m src.simulator --boss examples/boss.yaml --team examples/team.yaml --abilities boss_abilities.yaml --out battle_log.json --rounds 50

echo "Done. Output: $(pwd)/battle_log.json (or other formats if configured)"

if [ "$NO_VENV" -eq 0 ]; then
  echo "To run again without cloning, enter the project dir and run:"
  echo "  source .venv/bin/activate && python -m src.simulator --boss examples/boss.yaml --team examples/team.yaml --abilities boss_abilities.yaml --out battle_log.json --rounds 50"
else
  echo "To run again, enter the project dir and run:"
  echo "  ${PYTHON_CMD} -m src.simulator --boss examples/boss.yaml --team examples/team.yaml --abilities boss_abilities.yaml --out battle_log.json --rounds 50"
fi
