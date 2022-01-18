#!/bin/bash

chown -R kubemon:kubemon /home/kubemon/kubemon-data

python -m kubemon "$@"
