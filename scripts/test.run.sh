#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
set -a
source $SCRIPT_DIR/.env
set +a
cd $SCRIPT_DIR/..
poetry run pytest -p no:warnings -o log_cli=true $1