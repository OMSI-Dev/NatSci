#!/bin/bash
set -e

VENV_PATH="/home/omsiadmin/Documents/SOS/myenv/bin/activate"
PYTHON_SCRIPT="/home/omsiadmin/Documents/SOS/nowPlaying.py"

DISPLAY=:0 unclutter -idle 0 -root &

sleep 1
DISPLAY=:0 xdotool mousemove_relative -- 1 0
DISPLAY=:0 xdotool mousemove_relative -- -1 0

source "$VENV_PATH"
python "$PYTHON_SCRIPT" "$@" 
#& #PY_PID=$!

