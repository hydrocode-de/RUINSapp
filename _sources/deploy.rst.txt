================
Deployment guide
================

The RUINSapp consists of many different sub-applications. For this guide we assume that the full application
should be deployed on a single server instance.

Webserver
=========

Install
-------

We need at least one instance serving the main website. In this guide, nginx is used.
Install:

.. code-block:: bash

    apt update && apt install -y nginx


Next, we need certbot to automatically install and auto-renew SSL certificates.
Recommended way to install certbot is using snap, which needs to be installed in most cases first.

.. code-block:: bash

    apt install snapd
    snap install core
    snap install certbot --classic


Then configure certbot:

.. code-block:: bash
    ln -s /snap/bin/certbot /usr/bin/certbot


Then request and install certificates for nginx

.. code-block:: bash
    certbot --nginx

Configure website
-----------------

Streamlit is running on port 8501 by default. As we are using a docker container, we can bind this to any host port.
To serve the Streamlit app to public you need to either open these ports or use a webserver to proxy them using a 
path or subdomain. 
As the apps should be served using SSL encryption, you need to setup and configure nginx anyway.
There are many ways to do so, the recommended way is to create a new site configuration in `/etc/nginx/sites-available`
and then activate that site.


I.e: `/etc/nginx/sites-available/ruins.conf`

.. code-block:: nginx
    # main server for the main page
    server {
        listen 80;
        listen [::]:80;
        server_name ruins.hydrocode.de;
        
        root /var/www/html;
        index index.html index.htm index.nginx-debian.html;

        location / {
            # as we are serving a single page application -> fall back to index
            try_files $uri $uri/ $uri.html /index.html;
        }
    }

    # add server for each streamlit app
    # generally it is possible to serve them as /uncertainty /weather etc
    # but these routes are already taken by the SPA to build the frame.
    server {
        listen 80;
        listen [::]:80;
        server_name uncertainty.ruins.hydrocode.de

        location / {
            proxy_pass http://127.0.0.1:8501/;
        }
        location ^~ /static {
            proxy_pass http://127.0.0.1:8501/static/;
        }
        location ^~ /healthz {
            proxy_pass http://127.0.0.1:8501/healthz;
        }
        location ^~ /vendor {
            proxy_pass http://127.0.0.1:8501/vendor;
        }
        location /stream { 
            proxy_pass http://127.0.0.1:8501/stream;
            proxy_http_version 1.1; 
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }
    
    }


Docker
======

Install docker on the host machine:

.. code-block:: bash
    
    apt install -y ca-certificates curl gnupg lsb-release

Add dockers GPG key and add package repository to sources

.. code-block:: bash

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

Install docker

.. code-bock:: bash

    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin


aaaand finally:

```bash
docker run -d -i  -p 42001:8501  --name weather  --restart always  ghcr.io/hydrocode-de/ruins:v0.6.0 weather.py
```

