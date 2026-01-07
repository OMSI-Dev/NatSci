# SOS (Science on a Sphere) 

## Theory of Operation

Science On a Sphere (SOS) is a globe-based data visualization system. These scripts synchronize dataset visualizations with surrounding monitors containing supporting powerpoint slides and closed captioning. 

A central server coordinates two computers: one displays the daily dataset ‘playlist’ while the other drives the perimeter displays. 

## Updating software

This software is built using Python 3.14. 

The following Python libraries must be installed before running :

- pillow
- pywin32
- pyuno
- PyQt5

The following software must be installed before running :

- LibreOffice

```
set PYTHONPATH=C:\Program Files\LibreOffice\program;%PYTHONPATH%
```

A virtual Python environment is configured on the Raspberry Pi to accommodate nowPlaying library custom dependencies. The pi is configured to boot via the following commands:

```
cd home/omsiadmin/Documents/SOS/nowPlaying.py
source venv/bin/activate
python nowPlaying.py
```

##Project File Organization

### >> Hardware

B-link : handles the main engine for powerpoint and subtitle control 

Raspberry Pi 5 : handles nowPlaying functions

SOS Server : 

## Audio

[If any audio, describe where they are located in the file organization and how to replace if needed. Include the naming scheme of the files and what part of the exhibit/component they affect.]

## Images/video

[If any images or videos, describe where they are located in the file organization and how to replace them if needed. Include the naming scheme and what part of the exhibit/component they affect.]

EXAMPLE:
The images are saved as PNG and the video is MP4, both are stored /data/images.  by following the naming scheme and replacing old files. It is recommended making a backup before replacing any files. Capitalization matters.

### Naming scheme:

```
Arrow Failure: redArrow.gif
Arrow Average: yellowArrow.gif
Arrow Success: greenArrow.gif
Head Failure: 3_en.png
Head Average:  2_en.png
Head Success:  1_en.png

```
