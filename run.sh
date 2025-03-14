#! /bin/bash

SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

source $SCRIPT_DIR/myenv/bin/activate
python3 $SCRIPT_DIR/heimdallr.py "$@"
deactivate
