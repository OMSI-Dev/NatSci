sudo nano /Documents/SOS/service.sh
#!/bin/bash
set -e

VENV_PATH="/home/omsiadmin/Documents/SOS/myenv/bin/activate"
PYTHON_SCRIPT="/home/omsiadmin/Documents/SOS/nowPlaying.py"

source "$VENV_PATH"

python "$PYTHON_SCRIPT" "$@"

journalctl -u nowplaying.service
Sep 02 11:28:26 raspberrypi systemd[1]: Started nowplaying.service.
Sep 02 11:28:29 raspberrypi service.sh[1077]: XDG_RUNTIME_DIR (/run/user/1000) is not owned by us (uid 0), but by uid 1000!
