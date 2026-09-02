sudo nano /etc/systemd/system/nowplaying.service
[Unit]
After=network.target

[Service]
Type=simple
User=root
Environment="XDG_RUNTIME_DIR=/run/user/1000"
ExecStart=/home/omsiadmin/Documents/SOS/service.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target

journalctl -u nowplaying.service
Sep 02 10:59:32 raspberrypi systemd[1]: Started nowplaying.service.
Sep 02 10:59:32 raspberrypi (rvice.sh)[1121]: nowplaying.service: Failed to execute /home/omsiadmin/Documents/SOS/service.sh: Exec format error
Sep 02 10:59:32 raspberrypi (rvice.sh)[1121]: nowplaying.service: Failed at step EXEC spawning /home/omsiadmin/Documents/SOS/service.sh: Exec format e>
Sep 02 10:59:32 raspberrypi systemd[1]: nowplaying.service: Main process exited, code=exited, status=203/EXEC
Sep 02 10:59:32 raspberrypi systemd[1]: nowplaying.service: Failed with result 'exit-code'.

sudo nano ./service.sh
#~/bin/bash
echo "Hello world!"

#enabled chmod privledges for the service

