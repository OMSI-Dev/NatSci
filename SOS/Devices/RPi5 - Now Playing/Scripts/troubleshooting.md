# Wait for the window to exist, then force focus onto it
for i in $(seq 1 30); do
    if DISPLAY=:0 wmctrl -l | grep -q "Now Playing"; then
        DISPLAY=:0 wmctrl -a "Now Playing"
        break
    fi
    sleep 0.5
done

wait $PY_PID
