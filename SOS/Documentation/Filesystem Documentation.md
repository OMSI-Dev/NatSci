###### **auxShare/**

this folder is network-shared across the B-link, SOS2 server, and Raspberry Pi 5



**auxShare/audio/**

this folder contains all related files to automated audio handling



**auxShare/audio/audio-config.JSON**

this file contains audio file names organized by category, modified only by facilitator commands found in engine.py



**auxShare/audio/audio-list.CSV**

this file contains a list of audio file names and their associated category in key:value format



**auxShare/audio/mp3**

this folder contains all the .mp3 files for playing ambient and narrated audio



###### **auxShare/cache**



**auxShare/cache/subtitles**

this folder contains all related files to subtitle caching 



**auxShare/cache/clip\_metadata\_cache.JSON**

this file contains generated content by cache\_manager.py from the SOS server. The data is used by the engine for querying data to display



**auxShare/cache/playlist\_cache.JSON**

this file contains generated content by cache\_manager.py from the SOS server. The data is used by the engine for querying data to display



###### **auxShare/data**

This folder contains SOS data for powerpoint slide navigation initialized by sdc.py, pp\_init.py, and pp\_access.py



###### **auxShare/documents**

This folder contains a powerpoint document to display on the ring monitors, managed by pp\_access.py







