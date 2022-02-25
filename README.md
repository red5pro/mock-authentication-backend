# mock-authenticaion-backend

This NodeJS Mock Authentication Service is for use in testing Red5 Pro [Round Trip Authentication](https://www.red5pro.com/docs/special/round-trip-auth/overview/).

You can set up your validation server in any technology as long as you keep the endpoints and `response JSON` format the same. You can use the provided code as a starting point for your own auth server as a NodeJS service.

The steps below explain the various components of the NodeJS mock server and how to set it up to work with the `RoundTripAuthenticator`.

This NodeJS service simulates the business application server's API. It has some exposed endpoints to validate and invalidate the username and password supplied. The mock service does not do any actual validation on the inputs that it receives, just that it is receiving something. This means, for example, that usernames/passwords validity are not checked.



# Requirements

* NodeJS v10+
* NPM 6+

```sh
curl -sL https://deb.nodesource.com/setup_12.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh
sudo apt-get install -y nodejs
sudo apt-get install build-essential
sudo npm install forever -g
```

> This project was developed with the latest NodeJS & NPM as of the time of this writing (April 15th, 2021).


# Configuration

In the `nodejs-mock-service directory`, edit the `index.js` file. In the top rows of the file, locate the comment `BEGINNING OF CONFIGURATION`. After that, there will be two variables that need to be updated with your custom values:

* `host`: The host where the NodeJS service is deployed. Replace "localhost" with the private IP address of the NodeJS server.
* `port`: The port that you opened for the service. Default example: 3000 (make sure this port is opened on your inbound firewall rules).

There is also an optional value, `optionalURLResource`, which can be used to pass a URL to a connecting client.

# Installation

```sh
npm install
```

# How to run

You can start the server with the command:

`node index.js`

or better yet,

```sh
forever start index.js
```

to view the log location and status of the running process, run `forever list`

> Running the above will start the server on the default port which is defined in index.js

If you open in a browser `http://<host>:<port>` you will get a few forms to test the API. The server's console will output the values received. The browser will show you the responses from the node server.

## Forever Commands

* `forever start`: starts a script as a daemon.
* `forever stop`: stops the daemon script by `Id|Uid|Pid|Index|Script`.
* `forever stopall`: stops all running scripts.
* `forever restart`: restarts the daemon script.
* `forever restartall`: restarts all running forever scripts.
