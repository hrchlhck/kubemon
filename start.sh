#!/bin/bash

BASE_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST=$1

cd $BASE_DIR

# Activate venv
source venv/bin/activate

# Start monitors
nohup python -m kubemon -t all -H $HOST > /dev/null 2>&1 &

cd -