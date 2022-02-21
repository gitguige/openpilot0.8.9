#!/bin/bash
source ~/venvOPnew/bin/activate
export PYTHONPATH="$PWD":$PYTHONPATH

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd ./tools/sim/ && ./bridge.py --cruise_lead $1 --init_dist $2 --cruise_lead2 $3
cd $DIR