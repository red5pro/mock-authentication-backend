# mock-authentication-backend

This NodeJS Mock Authentication Service is for use in testing Red5 Pro [Round Trip Authentication](https://www.red5pro.com/docs/special/round-trip-auth/overview/).

You can set up your validation server in any technology as long as you keep the endpoints and `response JSON` format the same. You can use the provided code as a starting point for your own auth server as a NodeJS service.

The steps below explain the various components of the NodeJS mock server and how to set it up to work with the `RoundTripAuthenticator`.

This NodeJS service simulates the business application server's API. It has some exposed endpoints to validate and invalidate the username and password supplied. The mock service does not do any actual validation on the inputs that it receives, just that it is receiving something. This means, for example, that usernames/passwords validity are not checked.

The server also includes a webhook endpoint that accepts POST requests. The endpoint can be used to test the webhooks reported by the `live` server side application and `cloudstorage` plugin when configured to do so. The endpoint is available at `http(s)://<hostname>/webhook`

# Requirements

* NodeJS v19+
* NPM 6+

```sh
curl -sL https://deb.nodesource.com/setup_19.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh
sudo apt-get install -y nodejs
sudo apt-get install -y build-essential
```

> This project was updated with the latest NodeJS & NPM as of the time of this writing (January, 2023).


# Configuration

In the `nodejs-mock-service directory`, edit the `index.js` file. In the top rows of the file, locate the comment `BEGINNING OF CONFIGURATION`. After that, there will be two variables that need to be updated with your custom values:

* `host`: The host where the NodeJS service is deployed. Replace "localhost" with the private IP address of the NodeJS server *(note: if you are running on Digital Ocean, you need to use the public IP address)*.
* `port`: The port that you opened for the service. Default example: 3000 (make sure this port is opened on your inbound firewall rules).

There is also an optional value, `optionalURLResource`, which can be used to pass a URL to a connecting client.

# Installation

```sh
npm install
```

# SSL

For most NodeJS implementations, it is necessary to generate SSL certificate files, which are converted into .crt and .key files to be stored in the `<service>/cert` folder.

## Using Let's Encrypt

The following can be run to install Let's Encrypt Certbot on Ubuntu (`snap` is included with most Ubuntu distributions by default)

1.	sudo snap install core; sudo snap refresh core
2.	sudo snap install --classic certbot
3.	sudo ln -s /snap/bin/certbot /usr/bin/certbot

To generate the cert, run `sudo certbot certonly --standalone --email <your-email> --agree-tos -d <server-fqdn>`  (for example: `sudo certbot certonly --standalone --email jessica@infrared5.com --agree-tos -d test01.red5.net`)

You will then need to copy the fullchain and privatekey to the cert directory of your application

```sh
sudo cp /etc/letsencrypt/live/<server-fqdn>/fullchain.pem ~/<nodejs-server>/cert/certificate.crt
sudo cp /etc/letsencrypt/live/<server-fqdn>/privkey.pem ~/<nodejs-server>/cert/privateKey.key
sudo chmod +r ~/<nodejs-server>/cert/*
```

Your index.js file then needs to be modified with the full path to the certificate and privateKey files (replace with the appropriate paths):

```js
if (useSSL) {
  cert = fs.readFileSync('/home/ubuntu/serverapp/cert/certificate.crt')
  key = fs.readFileSync('/home/ubuntu/serverapp/cert/privateKey.key')
  port = 443
```

# How to run

You can start the server with the command:

`sudo node index.js &`

> Running the above will start the server on the default port which is defined in index.js

If you open in a browser `http://<host>:<port>` you will get a few forms to test the API. The server's console will output the values received. The browser will show you the responses from the node server.

##  Running as a Service

Copy the `mockauth.service` file (in this repository) to `/etc/systemd/system/`

```sh
sudo cp mockauth.service /etc/systemd/system/
```

The service file looks like the following: 

```shell
[Unit]
Description=mockauth-service
# Documentation=https://
# Author: Red5 Pro

[Service]
# Start Service and Examples
ExecStart=/usr/bin/node /home/ubuntu/mock-authentication-backend/index.js

# Options Stop and Restart
# ExecStop=
# ExecReload=

# Required on some systems
WorkingDirectory=/home/ubuntu/mock-authentication-backend/


# Restart service after 10 seconds if node service crashes
RestartSec=10
Restart=always
# Restart=on-failure

# Output to syslog
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nodejs-mock-authentication

# Variables
Environment=PATH=/usr/bin:/usr/local/bin

[Install]
WantedBy=multi-user.target
```

**NOTE:** The `mockauth.service` file assumes that you are running this back-end from `/home/ubuntu/mock-authentication-backend`. If you are running from a different filepath, then you will need to modify the service file accordingly.

Enable the service:

`sudo systemctl enable mockauth.service`

should return: `Created symlink /etc/systemd/system/multi-user.target.wants/mockauth.service → /etc/systemd/system/mockauth.service.`

## Start/Stop the Mock Authentication Service

To start the service, run:

`sudo systemctl start mockauth`

To stop the service, run:

`sudo systemctl stop mockauth`

To check the state of the mockauth service:

`sudo systemctl status mockauth`

Also, if you make any modifications to the service file after adding it, you will need to run:

`sudo systemctl daemon-reload`

# Logging

Using the above service file, the logging will be included in the `/var/log/syslog` file, and will look like:

```log
 nodejs-mock-authentication[393833]: validate credentials called
nodejs-mock-authentication[393833]: type: publisher
nodejs-mock-authentication[393833]: username: user
nodejs-mock-authentication[393833]: password: pass
nodejs-mock-authentication[393833]: streamID: stream2
nodejs-mock-authentication[393833]: token: undefined
nodejs-mock-authentication[393833]: valid un/pw
nodejs-mock-authentication[393833]: validate credentials called
nodejs-mock-authentication[393833]: type: subscriber
nodejs-mock-authentication[393833]: username: test
nodejs-mock-authentication[393833]: password: test
nodejs-mock-authentication[393833]: streamID: stream2
nodejs-mock-authentication[393833]: token: undefined
nodejs-mock-authentication[393833]: invalid un/pw
```

