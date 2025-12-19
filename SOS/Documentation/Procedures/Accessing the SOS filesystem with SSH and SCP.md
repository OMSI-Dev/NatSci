# Accessing the SOS filesystem with SSH and SCP



\**these commands may be helpful for debugging and investigating the SOS file system hosted on the SOS server*



*\* from its' associated B-link computer, a remote environment is accessible via rustdesk.* 



RUST DESK CREDENTIALS

Control Remote Desktop - 252 708 030

OMSIismo1234



BEE-LINK

ismoomsi 



*----*

<b>ssh sosdemo@10.10.51.87</b>

‘cd /’ : go to root

‘pwd’ : filepath of current location

‘dir’ : files in current location

----



**Downloading a playlist.sos file for a dataset from the SOS server**

scp -r sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/playlist.sos C:\\OMSI\\App\\SOS



**Uploading file from local to SOS server path destination**

scp -r "C:\\OMSI\\App\\SOS\\playlist.sos" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\_harmonious\_relationships/

