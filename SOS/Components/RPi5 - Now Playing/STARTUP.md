# OMSI SOS RPi5 Startup Guide

last updated 2026-09-01 by autumn 

# Update modified script

1) 

    `scp /path/to/local/file <username>@<pi_ip_address>:/path/to/destination/`
    
    for example:
    
    `scp /NatSci/SOS/Components/RPi5 - Now Playing/Scripts/nowplaying.py <omsiadmin>@<pi_ip_address>:/Documents/SOS/` 

2) 

3) 

# Re-installing a RPi for NowPlaying

**Operating System:** Flash RPi with the latest Linux Debian distribution
**User:** omsiadmin
    
## Remote Access
    
**Configuring ConnectPi**

    ```
    sudo apt update && sudo apt upgrade -y
    sudo apt install rpi-connect
    ```
    
    ```
    sudo systemctl enable rpi-connect
    sudo systemctl start rpi-connect
    sudo reboot   
    ```

## Python 
    
**Configuring python and venv**

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
    
## Scripts

**Configuring nowPlaying.py** 

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
    

## System Service Automation
**Configuring OS startup script service** 

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
    
**Configuring crontab to automate overnight reboot process** 

1)
    ``sudo crontab -e``
    
2) select nano 
    
3) add the following entry at the bottom. this schedules a reboot every night at 12am.
    ``0 0 * * * /sbin/shutdown -r now``


