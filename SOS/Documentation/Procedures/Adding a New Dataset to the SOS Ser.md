# **Adding a New Dataset to the SOS Server**

**Note:** This guide covers the specific case of adding custom movie datasets. Standard dataset procedures may vary.



**\* Overview**

This document explains how to add new content to the Science On a Sphere (SOS) system. The example shown here documents the addition of two movies: "Nature's Harmonious Relationships" and "We Are All Related" to OMSI's SOS server.



**\* Required Tasks**

\[] Update the noaa.csv file with new slide designations

\[] Create and upload necessary files to the /media/ folder on the SOS server

\[] Configure playlist.sos metadata for the specific media type



**\* File Structure**

Each dataset requires a folder containing:



playlist.sos (configuration file)

movie.mp4 (video file)

english\_subtitles.srt (English captions)

spanish\_subtitles.srt (Spanish captions)



Refer to existing datasets in the SOS server's /media/ for examples of proper folder structure.



**\* Step-by-Step Process**

1: Update noaa.csv

Add new slide designations for each movie in the noaa.csv file.



2: Configure "Nature's Harmonious Relationships"

Location: /shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships



2.1: Upload Caption Files

Upload both English and Spanish subtitle files to the playlist folder:



scp -r "C:\\OMSI\\App\\SOS\\Custom SOS Videos Test\\Harmonious\_Spanish.srt" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/



2.2 Download Existing playlist.sos



**scp -r sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/playlist.sos C:\\OMSI\\App\\SOS**



2.3 Edit playlist.sos Metadata



Add the following information to the playlist.sos file:

\- timer: Video duration in seconds

\- caption: Path to English subtitles

/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/Harmonious\_English.srt

\- caption2: Path to Spanish subtitles

/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/Harmonious\_Spanish.srt



2.4 Re-upload playlist.sos



scp -r "C:\\OMSI\\App\\SOS\\Custom SOS Videos Test\\playlist.sos" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/



3: Configure "We Are All Related"

Location: /shared/sos/media/site-custom/Movies/we\_are\_all\_related



3.1 Upload Caption Files



scp -r "C:\\OMSI\\App\\SOS\\Custom SOS Videos Test\\warmsprings\_English.srt" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/we\_are\_all\_related



3.2 Download Existing playlist.sos



scp -r sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/we\_are\_all\_related/playlist.sos C:\\OMSI\\App\\SOS\\



3.3 Edit playlist.sos Metadata



Add the following information to the playlist.sos file:

\- timer: 92 (duration in seconds)

\- caption: Path to English subtitles

/shared/sos/media/site-custom/Movies/we\_are\_all\_related/warmsprings\_English.srt

\- caption\_es: Path to Spanish subtitles

/shared/sos/media/site-custom/Movies/we\_are\_all\_related/warmsprings\_Spanish.srt



3.4 Re-upload playlist.sos



scp -r "C:\\OMSI\\App\\SOS\\Custom SOS Videos Test\\playlist.sos" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/we\_are\_all\_related/



Step 4: Add Custom Display Logic (If Required)

Some datasets may require custom programming for special features. In this case, both movies needed:



\- A credits screen at the end

\- Custom English/Spanish subtitle translation screens

\- Specific display conditions for these elements



Configure these custom sequences according to your dataset's requirements.



\* Notes:



Timer values must match the actual video duration in seconds

File paths must be absolute and match the server directory structure exactly

Datasets without a timer value default to 180s

