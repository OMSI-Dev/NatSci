# Setup Guide / Documentation for Venn Diagram Exhibit Installation

Computer : Beelink EQ
Operating System : Linux Mint Xcef
Godot Version : v4.6

## Installation 
[Linux Mint Installation Guide](https://linuxmint-installation-guide.readthedocs.io/en/latest/index.html)   

1. Install Linux Mint Xcef on USB drive
2. Create a bootable drive via utility tool (i.e. Fedora Media Writer)
3. Plug into target machine and restart
4. Press **'F7'** or system equivalent during reboot and follow BIOS prompts
5. Install Linux Mint once launched to Desktop
6. Restart

# Linux (Ubuntu) Setup & System Service Automations

## Welcome
  - System Snapshots: 
  - Driver Manager: Launch and follow prompts to install reccommended drivers. 
  - Update Manager: Launch and follow prompts to install available updates.
    - **NOTE:** At this step, there may be errors for outdated mirrors. In the error panel: 'more details' reveals the problematic update. Deselect it in the update manager and continue to install updates. 
  - System Settings: TODO configure as needed
  - Firewall: TODO configure as needed

## BIOS power settings: Boot on power

```
sudo systemctl reboot --frmware-setup
```
1. Advanced Tab > AMD CBS > FCH Common Options > AC Power Loss Options > AC Loss Control 
2. Set to > Always On 
3. Esc to main menu
4. F4 to Save and Exit

## User Configuration: Create 'game' Account
```
sudo adduser game   
```
1. Password stored in Drive 'Passwords'
2. **ENTER** for all default values 

# Build Godot project file for Linux 
1. In your (remote) Godot project file, find **'Manage Export Templates'** in the Editor tab
2. Download and Install 
3. Find **'Export'** in the Project tab
4. Click **'Add...'** and select Linux
5. Give your game file a name
6. Turn Embedding PCK **On** 
7. Click **Export Project**
8. Name your file `Venn_Diagram.x86_64`

## Import build onto computer and configure
1. Download the [Godot Executable folder](https://github.com/OMSI-Dev/NatSci/tree/main/Climate%20Action%20Venn%20Diagram/Components/Beelink%20-%20Gameplay%20Display/Software)from Github to the target computer
2. Store the folder in Documents > Scripts
3. Navigate to the build directory `Godot Executable` in terminal 
4. Run the **chmod** command:
```
chmod +x Venn_Diagram.x86_64
```
5. Ensure the file strucure is as follows: `Documents > Scripts > Godot_Executable`
  - **NOTE:** If any changes are made to the Godot executable, please be sure to chmod the file to re-enable its' ability to execute!

# Configure Auto-Login for 'game'
1. Find **'Users and Groups'** in Settings
2. Select **'game'**
3. Change User Account Type > Desktop User
4. Password > Not asked on login

## Create Auto-Login Automation 

1. In 'omsiadmin' account, edit (or create) 
`/etc/lightdm/lightdm.conf.d/70-autologin.conf`

```
sudo nano /etc/lightdm/lightdm.conf.d/70-autologin.conf
```

```
[Seat:*]
autologin-user=game
autologin-user-timeout=0
```

2. Then make sure your user is in the `autologin` group:
```
sudo groupadd -f autologin
sudo gpasswd -a yourusername autologin
```

3. Reboot to test

# Configure Auto-launch for game
1. Create autostart directory structure 
```
mkdir -p ~/.config/autostart
```

2. Create the auto-launch automation
```
sudo nano ~/.config/autostart/venn-diagram.desktop
```

```
[Desktop Entry]
Type=Application
Name=Venn Diagram
Exec=/home/game/Documents/Scripts/Godot_Executable/Venn_Diagram.x86_64
Path=/home/game/Documents/Scripts/Godot_Executable/
X-GNOME-Autostart-enabled=true
```

3. Reboot and test

# Disable administrative privledges for 'game'
1. In the `omsiadmin` account, go to `Groups and People` in `Settings` using the Start menu
2. Select `game`
3. Change `Account Type` from `Administrator` to `Desktop User`

# TODO (...?)
1. Disable GUI access of `game` user 
2. Install RustDesk on both machines
3. Create a reboot cron job after 12am 


created 2026-09-10 by autumn
