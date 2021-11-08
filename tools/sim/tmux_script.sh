#!/bin/bash
tmux new -d -s htop
tmux send-keys "./launch_openpilot.sh" ENTER
tmux neww

tmux send-keys ". ~/venvOP3.8.10/bin/activate" ENTER
tmux send-keys "export PYTHONPATH=$PYTHONPATH:/home/guige/Research/ADS/Oct20/openpilot0.8.9/" ENTER

tmux send-keys "./bridge.py $*" ENTER
tmux a
