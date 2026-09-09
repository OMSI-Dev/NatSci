# OMSI SOS RPi5 Startup Guide

last updated 2026-09-01 by autumn 

*If re-installing a RPi from scratch for the SOS system, follow the steps below:*

# Operating System 

**Flash RPi with latest (Linux) distribution** 

    1) user: omsiadmin
    
# Remote Access
    
**Configure ConnectPi**

    ```
    sudo apt update && sudo apt upgrade -y
    sudo apt install rpi-connect
    ```
    
    ```
    sudo systemctl enable rpi-connect
    sudo systemctl start rpi-connect
    sudo reboot   
    ```

# Python Configuration
    
**Configure python and venv environment**

1)
    ```
    sudo apt install python3 python3-pip -y
    ```
2)
    ```
    cd Documents
    mkdir SOS
    ```
    
3) 
    ```
    python3 -m venv --system-site-packages myenv
    ```
    
# Scripts
**Create nowPlaying.py script** 

1)
    ```
    cd Documents
    mkdir SOS
    cd SOS
    ```
    
2) 
    ```
    Refer to Github NatSci/SOS/Devices/RPi5 - Now Playing/Scripts/nowPlaying.py
    ```
    
3) 
    ```
    Import assets from Github NatSci/SOS/Devices/RPi5 - Now playing/Assets/ into local /SOS/ directory
    ```
    

# System Service Automation
**Create OS startup script service** 

1) Create bash script
    ```
    cd Documents/SOS/
    sudo nano service.sh
    ```
    
    ```Refer to NatSci/SOS/Devices/RPi5 - Now Playing/Scripts/service.sh
    ```
    
2) Create systemd service 
    ```
    sudo nano /etc/systemd/system/nowplaying.service
    ```
    
    ```
    Refer to /SOS/Devices/RPi5 - Now Playing/Script/nowplaying.service
    ```
    
3) Start service
    ```
    sudo systemctl daemon-reload
    sudo systemctl enable nowplaying.service
    sudo systemctl start nowplaying.service
    ```
    
4) Reboot and monitor for errors
    ```
    sudo reboot
    ```
    
    ```
    journalctl -u nowplaying.service
    systemd-analyze verify nowplaying.service
    systemctl status nowplaying.service
    ```
    
**Create a crontab to automate overnight reboot process** 

1)
    ``sudo crontab -e``
    
2) select nano 
    
3) add the following entry at the bottom. this schedules a reboot every night at 12am.
    ``0 0 * * * /sbin/shutdown -r now``


