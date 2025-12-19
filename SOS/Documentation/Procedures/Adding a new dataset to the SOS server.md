# Adding a new “dataset” to the SOS server

*\*This specific case may not cover all the bases with creating standard datasets.*



**Context**: Two movies “Nature’s Harmonious Relationships” and “We Are All Related” were added to the server’s /media/site-custom/ folder, with the same structure as existing datasets.



**Summary of tasks:** 

\- edit noaa.csv with new slide designations

\- upload/create necessary files in dataset folder (playlist.sos, movie.mp4, english\_subtitles.srt, spanish\_subtitles.srt) 

\- configure playlist.sos metadata for a "movieset"



--------------------------------------------------



###### **1) edit noaa.csv** 

\- \[x]  add new slide designations for both movies





###### **2) playlist.sos file metadata for “Nature’s Harmonious Relationships”** 



*/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships* 



\- \[x]  upload caption(s) to playlist folder

&nbsp;   

**scp -r "C:\\OMSI\\App\\SOS\\Custom SOS Videos Test\\Harmonious\_Spanish.srt" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/**

&nbsp;   

\- \[x]  Download playlist.sos of Harmonious

&nbsp;   

**scp -r sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/playlist.sos C:\\OMSI\\App\\SOS**

&nbsp;   

\- \[x]  add timer: duration in seconds to playlist.sos

\- \[x]  add caption: metadata to path to playlist.sos

&nbsp;   

**/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/Harmonious\_English.srt**

&nbsp;   

\- \[x]  add caption2: espanol path

&nbsp;   

**/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships /Harmonious\_Spanish.srt**

&nbsp;   

\- \[x]  Re-upload Harmonious playlist.sos to the SOS server

&nbsp;   

**scp -r "C:\\OMSI\\App\\SOS\\Custom SOS Videos Test\\playlist.sos" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/**

&nbsp;   



###### **3) edit playlist.sos file metadata for We Are All Related**



*/shared/sos/media/site-custom/Movies/we\_are\_all\_related* 



\- \[x]  upload caption(s) to playlist folder

&nbsp;   

**scp -r "C:\\OMSI\\App\\SOS\\Custom SOS Videos Test\\warmsprings\_English.srt" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/we\_are\_all\_related** 

&nbsp;   

\- \[x]  Download playlist.sos of warmsprings

&nbsp;   

**scp -r sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/we\_are\_all\_related/playlist.sos C:\\OMSI\\App\\SOS\\**

&nbsp;   

\- \[x]  add timer: duration in seconds to playlist.sos 92

\- \[x]  add caption: metadata to path to playlist.sos

&nbsp;   

**/shared/sos/media/site-custom/Movies/we\_are\_all\_related/warmsprings\_English.srt**

&nbsp;   

\- \[x]  add caption\_es: espanol path

&nbsp;   

**/shared/sos/media/site-custom/Movies/we\_are\_all\_related/warmsprings\_Spanish.srt**

&nbsp;   

\- \[x]  Re-upload warmsprings playlist.sos

&nbsp;   

**scp -r "C:\\OMSI\\App\\SOS\\Custom SOS Videos Test\\playlist.sos" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/we\_are\_all\_related/**

&nbsp;   

###### **4) add any necessary logic for custom slideshow display** 



*\* these moviesets needed a custom sequence programmed to show a credits screen and custom english/spanish subtitle translation screen. Conditions for these*  

