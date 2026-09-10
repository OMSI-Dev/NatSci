# Setup Guide / Documentation for Venn Diagram Exhibit Installation

Computer : Beelink EQ
Operating System : Linux Mint Xcef
Godot Version : v4.6

# Installation 
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
    - NOTE: At this step, there may be errors for outdated mirrors. In the error panel: 'more details' reveals the problematic update. Deselect it in the update manager and continue to install updates. 
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
1. 
```
sudo adduser game   
```
2. Password stored in Drive 'Passwords'

3. **ENTER** for all default values 

# Disable admin privledges for 'game'
1. Find **'Users and Groups'** in Settings
2. Select **'game'**
3. Change User Account Type > Desktop User
4. Password > Not asked on login


# Build Godot project file for Linux 
1. In your (remote) Godot project file, find **'Manage Export Templates'** in the Editor tab
2. Download and Install 
3. Find **'Export'** in the Project tab
4. Click **'Add...'** and select Linux
5. Give your game file a name
6. Turn Embedding PCK **On** 
7. Click **Export Project**
8. Name your file `Venn_Diagram.x86_64`

# Import build onto computer and configure
1. Download the [Godot Executable folder]()from Github to the target computer
2. Store the folder in Documents > Scripts
3. Navigate to the build directory `Godot Executable` in terminal 
4. Run the **chmod** command:
```
chmod +x Venn_Diagram.x86_64
```

# Enable group policy 


3. (TODO) Build Godot project for Linux 

Compile in Godot, copy eveything to /USR/BIN?


w-i-p last edited 2026-09-10 by autumn
