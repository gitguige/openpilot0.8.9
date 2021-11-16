#!/bin/bash
source ~/venvOP3.8.10/bin/activate
export PYTHONPATH="$PWD":$PYTHONPATH

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd ./tools/sim/ && ./bridge.py --cruise_lead $1
cd $DIR