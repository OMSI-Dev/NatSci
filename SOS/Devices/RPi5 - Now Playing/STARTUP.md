If re-installing a RPi from scratch for the SOS system, follow the steps below:

1. Flash RPi with latest (Linux) distribution 
    a) user: omsiadmin
    
2. Configure Rust Desk 
    a) Install (Ubuntu, AArch64)
    https://github.com/rustdesk/rustdesk/releases
    
    b) 
    ```
    sudo apt install ./rustdesk-*.deb
    ```
    c) 
    ```
    sudo systemctl enable rustdesk.service
    sudo systemctl start rustdesk.service
    ```
    d) Optional start 
    rustdesk 
    
3. Configure python and venv environment
    a)
    ```
    sudo apt install python3 python3-pip -y
    ```
    b)
    ```
    cd Documents
    mkdir SOS
    ```
    
    c) 
    ```
    python3 -m venv --system-site-packages myenv
    ```
    
4. Create nowPlaying.py script 
    a)
    ```
    cd Documents
    mkdir SOS
    cd SOS
    ```
    
    b) 
    ```
    Refer to Github NatSci/SOS/Devices/RPi5 - Now Playing/Scripts/nowPlaying.py
    ```
    
    c) 
    ```
    Import assets from Github NatSci/SOS/Devices/RPi5 - Now playing/Assets/ into local /SOS/ directory
    ```
    

5. Create OS startup script service 
    a) Create bash script
    ```
    cd Documents/SOS/
    sudo nano service.sh
    ```
    
    ```Refer to NatSci/SOS/Devices/RPi5 - Now Playing/Scripts/service.sh
    ```
    
    b) Create systemd service 
    ```
    sudo nano /etc/systemd/system/nowplaying.service
    ```
    
    ```
    Refer to /SOS/Devices/RPi5 - Now Playing/Script/nowplaying.service
    ```
    
    c) Start service
    ```
    sudo systemctl daemon-reload
    sudo systemctl enable nowplaying.service
    sudo systemctl start nowplaying.service
    ```
    
    d) Reboot and monitor for errors
    ```
    sudo reboot
    ```
    
    ```
    journalctl -u nowplaying.service
    systemd-analyze verify nowplaying.service
    systemctl status nowplaying.service
    ```
    

Created 2026-09-01 by autumn 
