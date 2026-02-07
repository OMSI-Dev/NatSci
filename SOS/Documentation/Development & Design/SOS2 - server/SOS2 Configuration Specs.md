# **SOS2 Configuration Specs**



**Notes**

* ssh key active on B-link
* firewall enabled for Apache web server





###### **HTTP Server Config** (executed on SOS2 server)

Following the guide to \[Install and Configure Apache](https://ubuntu.com/tutorials/install-and-configure-apache#1-overview), supplemented with the steps below:



1. **apache2's VirtualHost file - grant permissions to edit '.' file**



&nbsp;	sudo chown sos /var/www/sos



**1a. Change directory of hosted files**



&nbsp;	sudo nano /etc/apache2/sites-available/000-default.conf



2. **External access to the VirtualHost file - allow firewall incoming connections on port 80**



&nbsp;	sudo nano /etc/hosts
	sudo ss -tlnp | grep :80



###### **Issues with Firefox** 

fsck repair caused issues with firefox's snap service. Steps to repair outlined below:



1\. **Remove the corrupted state file and let snapd recreate it**

&nbsp;	sudo rm /var/lib/snapd/state.json 


2\. **Use snap's built-in repair**

&nbsp;	sudo systemctl stop snapd.service snapd.socket

&nbsp;	sudo rm /var/lib/snapd/state.json

&nbsp;	sudo systemctl start snapd.service

&nbsp;	systemctl status snapd.service

&nbsp;	snap list



3\. **Verify successful logs on boot (no failures)** 





###### **Display issue** 

snapd, core22, and firefox mount issues 



