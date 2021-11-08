#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/home/guige/Research/ADS/Oct20/openpilot-9.11/
export PASSIVE="0"
export NOBOARD="1"
export SIMULATION="1"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd ../../selfdrive/manager && ./manager.py
