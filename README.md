# mock-authentication-backend

This NodeJS Mock Authentication Service is for use in testing Red5 Pro [Round Trip Authentication](https://www.red5pro.com/docs/special/round-trip-auth/overview/).

You can set up your validation server in any technology as long as you keep the endpoints and `response JSON` format the same. You can use the provided code as a starting point for your own auth server as a NodeJS service.

The steps below explain the various components of the NodeJS mock server and how to set it up to work with the `RoundTripAuthenticator`.

This NodeJS service simulates the business application server's API. It has some exposed endpoints to validate and invalidate the username and password supplied. The mock service does not do any actual validation on the inputs that it receives, just that it is receiving something. This means, for example, that the usernames'/passwords' validity is not checked.

# Requirements

* NodeJS v10+
* NPM 6+

```sh
curl -sL https://deb.nodesource.com/setup_12.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh
sudo apt-get install -y nodejs
sudo apt-get install -y build-essential
sudo apt-get install -y forever -g
```

> This project was developed with the latest NodeJS & NPM as of the time of this writing (April 15th, 2021).


# Configuration

In the `nodejs-mock-service directory`, edit the `index.js` file. In the top rows of the file, locate the comment `BEGINNING OF CONFIGURATION`. After that, there will be two variables that need to be updated with your custom values:

* `host`: The host where the NodeJS service is deployed. Replace "localhost" with the public IP address of the NodeJS server.
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

or better yet,

`sudo forever start index.js &`

to view the log location and status of the running process, run `forever list`

> Running the above will start the server on the default port which is defined in index.js

If you open in a browser `http://<host>:<port>` you will get a few forms to test the API. The server's console will output the values received. The browser will show you the responses from the node server.

## Forever Commands

* `forever start`: starts a script as a daemon.
* `forever stop`: stops the daemon script by `Id|Uid|Pid|Index|Script`.
* `forever stopall`: stops all running scripts.
* `forever restart`: restarts the daemon script.
* `forever restartall`: restarts all running forever scripts.
