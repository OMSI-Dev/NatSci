### **SSH and SCP commands for SOS2**

\*executable only from an external computer (ie. SOS B-link)



**ssh sosdemo@10.10.51.87**

‘cd /’ : go to root

‘pwd’ : filepath of current location

‘dir’ : files in current location



**Downloading a playlist.sos file on the SOS server to a localpath**

scp -r sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\\\_harmonious\\\_relationships/playlist.sos C:\\\\OMSI\\\\App\\\\SOS



**Uploading file from a localpath to a path destination on the SOS server**

scp -r "C:\\\\OMSI\\\\App\\\\SOS\\\\playlist.sos" sosdemo@10.10.51.87:/shared/sos/media/site-custom/Movies/natures\\\_harmonious\\\_relationships/

