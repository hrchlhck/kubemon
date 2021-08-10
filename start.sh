#!/bin/bash

HOST=$1

# Activate venv
source venv/bin/activate

# Start monitors
sudo nohup $(pwd)/venv/bin/python -m kubemon -t all -H $HOST 2>&1 &