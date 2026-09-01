If re-installing a RPi from scratch for the SOS system, follow the steps below:

1. Flash RPi with latest (Linux) distribution 
    a) user= omsiadmin
    
2. Configure Pi Connect
    sudo apt update
    sudo apt upgrade -y
    sudo apt install rpi-connect
    
3. Configure python 
    sudo apt install python3 python3-pip -y
    
4. Create/place NowPlaying script in '/home/omsiadmin/Documents/SOS/' with associated assets

5. Create venv environment 
    cd Documents
    python3 -m venv --system-site-packages myenv

6. Create OS startup script service
    sudo nano /etc/systemd/system/nowplaying.service
    
    a) 
    [Unit]
    Description = Startup script for NowPlaying
    After = network.target
    
    [Service]
    User=omsiadmin
    WorkingDirectory=/home/omsiadmin/Documents/SOS/
    ExecStart=/home/omsiadmin/Documents/SOS/myenv/bin/python3 /home/omsiadmin/Documents/SOS/nowPlaying.py 
    Restart=always
    RestartSec=10
    
    [Install]
    WantedBy=multi-user.target
    
7. Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable nowplaying.service
    sudo systemctl start myscript.service
    
    a) For errors, use the following commands to troubleshoot:
        systemd-analyze verify nowplaying.service
        systemctl status nowplaying.service

    b) Re-execute the enable/start service commands
    
Created 2026-09-01 by autumn 
