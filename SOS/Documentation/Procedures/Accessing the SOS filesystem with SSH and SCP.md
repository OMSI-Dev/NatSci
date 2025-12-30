# Accessing the SOS filesystem with SSH and SCP



\* *these commands are...*

*-* only executable *from the external SOS B-link (using a remote environment via RustDesk)*

*- for accessing the SOS file system hosted on the SOS server* 



RUSTDESK CREDENTIALS

Control Remote Desktop - 252 708 030

OMSIismo1234



BEE-LINK

ismoomsi



*----*

**ssh sosdemo@10.10.51.87**

‘cd /’ : go to root

‘pwd’ : filepath of current location

‘dir’ : files in current location

---



**Downloading a playlist.sos file associated with a dataset on the SOS server**

scp -r sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/playlist.sos C:\\OMSI\\App\\SOS



**Uploading file from a localpath to a path destination on the SOS server**

scp -r "C:\\OMSI\\App\\SOS\\playlist.sos" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/

