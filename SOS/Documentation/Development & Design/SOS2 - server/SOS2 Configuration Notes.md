**SOS2 Configuration Notes**

* ssh key active on B-link
* firewall enabled for Apache web server



**HTTP Server Config**

Documentation of troubleshooting setup specs

1. apache2's VirtualHost file - granting permissions to edit '.' file:

```
sudo chown sos /var/www/sos
```

1a) change directory of hosted files:

```
sudo nano /etc/apache2/sites-available/000-default.conf
```

2. Granting external access to the VirtualHost file - firewall granting incoming connections on SOS2 port 80:

```
sudo nano /etc/hosts
sudo ss -tlnp | grep :80
```






