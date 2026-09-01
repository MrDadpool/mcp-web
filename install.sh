#!/usr/bin/env bash
# Sets up mcp-web on a Mac and prints the LM Studio config to paste.
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing mcp-web in $(pwd)"

# uv handles everything including fetching a Python if none is new enough.
if command -v uv >/dev/null 2>&1; then
    uv venv --python 3.12
    VENV_PY=.venv/bin/python
    uv pip install --python "$VENV_PY" -e .
else
    PY=""
    for candidate in python3.13 python3.12 python3.11 python3; do
        if command -v "$candidate" >/dev/null 2>&1 &&
           "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'; then
            PY="$candidate"
            break
        fi
    done
    if [ -z "$PY" ]; then
        echo
        echo "No Python 3.11 or newer found. Install uv, which will fetch one for you:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "then run this script again."
        exit 1
    fi
    "$PY" -m venv .venv
    VENV_PY=.venv/bin/python
    "$VENV_PY" -m pip install --quiet --upgrade pip
    "$VENV_PY" -m pip install --quiet -e .
fi

BIN="$(pwd)/.venv/bin/mcp-web"
"$VENV_PY" -c 'import mcp_web.server' >/dev/null

cat <<CONFIG

Done. Now open LM Studio, go to the Program tab in the right sidebar,
choose Install > Edit mcp.json, and add this entry:

{
  "mcpServers": {
    "mcp-web": {
      "command": "$BIN"
    }
  }
}

If mcp.json already has other servers, add "mcp-web" alongside them
inside the existing "mcpServers" object.

Then load a model that supports tools and enable mcp-web in the chat.
CONFIG
