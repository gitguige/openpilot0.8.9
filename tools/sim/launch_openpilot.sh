#!/bin/bash

source ~/venvOP3.8.10/bin/activate

export PYTHONPATH=$PYTHONPATH:$PWD/../../
export PASSIVE="0"
export NOBOARD="1"
export SIMULATION="1"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd ../../selfdrive/manager && ./manager.py
