
// un and pw
const validun = 'user'
const validpw = 'pass'

var express = require('express');
var bodyParser = require('body-parser');
var fs = require('fs');
var net = require('net');
var app = express();
//const http = require('http').Server(app);

/*
*   BEGINNING OF CONFIGURATION
*
*/
/*
*   HOST
*
*/
var host = "104.236.193.72";
/*
*   PORT
*
*/
var port  = 3000;
/*
*   Optional url resource for authenticated client
*
*/
var optionalURLResource = ""; // optional
/*
*   END OF CONFIGURATION
*
*/

app.use(bodyParser.urlencoded({
    extended: true
}));
app.use(bodyParser.json());

app.get('/', (req, res) => res.sendFile(__dirname + '/index.html'));

// get POST to log In
app.post('/logIn', function(request, response) {

    console.log(request.body.username);
    console.log(request.body.password);
    response.send(JSON.stringify({"username":"streamUsername","password":"streamPassword","streamID":"streamID"}));

});


// get POST to validate the credentials for a stream
app.post('/validateCredentials', function(request, response){

    console.log('\n\nvalidate credentials called');
    console.log('type: '+request.body.type);
    console.log('username: '+request.body.username);
    console.log('password: '+request.body.password);
    console.log('streamID: '+request.body.streamID);
    console.log('token: '+request.body.token);

    var type = request.body.type;
    var result = false;

    if ((request.body.username == validun) && (request.body.password == validpw)) {
        result = true;
        console.log('valid un/pw');
    } else {
        console.log('invalid un/pw');
    }

    if (type == "publisher") {
        response.send(JSON.stringify({"result":result,"url":optionalURLResource}));
    } else if (type == "subscriber") {
        response.send(JSON.stringify({"result":result}));
    } else {
        console.log('invalid type supplied');
        response.send(JSON.stringify({"result":false}));
    }

});

// get POST to invalidate the credentials for a stream
app.post('/invalidateCredentials', function(request, response) {

    console.log('\n\ninvalidate credentials called');
    console.log('username: '+request.body.username);
    console.log('password: '+request.body.password);
    console.log('streamID: '+request.body.streamID);
    console.log('token: '+request.body.token);
    response.send(JSON.stringify({"result":true}));

});

app.listen(port,host);

console.log(`${host} running on ${port}.`)
