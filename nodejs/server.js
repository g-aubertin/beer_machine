console.log('starting server.js');

var daemon_status = 0;
var current_batch = undefined;

/////////////////////////////
// init and includes
/////////////////////////////

var express = require('express');
app = express();

var path = require('path');

var sqlite3 = require('sqlite3').verbose();
var db = new sqlite3.Database('../beer_machine.db');

var net = require('net');

var bodyParser = require('body-parser');
app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({ extended: true })); // support encoded bodies
//template engine
app.set('view engine', 'ejs')

// set public/ as static path
app.use(express.static('public'));

// socket init
var client = net.createConnection("../beer_socket");

client.on("connect", function() {
    console.log("connected to socket !");
    client.write("get_status")

});

/////////////////////////////
// socket handler
/////////////////////////////
client.on("data", function(data) {

    console.log(data.toString())
    data_tab = data.toString().split(" ")

    // daemon status
    if (data_tab[0].toString() == "status") {
	if (data_tab[1].toString() == "daemon_running") {
	    console.log("socket response: beer_machine daemon is in RUNNING state")
	    daemon_status = 1
	}

	if (data_tab[1].toString() == "daemon_stopped") {
	    console.log("socket response: beer_machine daemon is in STOPPED state")
	    daemon_status = 0
	}
    }

    // batch status
    if (data_tab[0].toString() == "batch") {
	current_batch = data_tab[1].toString()
    }
});

/////////////////////////////
// routing for overview page
/////////////////////////////
app.get('/', function(request, response) {

    console.log("receiving GET on /")

    // we need to get the data from test_table
    db.all("SELECT * FROM test_table", function (err, rows) {
	response.render('index', {daemon_status:daemon_status, current_batch:current_batch});
    });
});

////////////////////////////
// routing for overview POST
///////////////////////////
app.post('/', function(req, res) {

    // debug
    console.log('POST request to the homepage');

    // stop button
    if (req.body && (req.body.button_value === "stop")) {
	console.log("stop pushed")
	client.write("stop")
	daemon_status = 0
	res.redirect('/');
    }

    // stop button
    if (req.body && (req.body.button_value === "start")) {
	console.log("start pushed")
	client.write("start")
	daemon_status = 1
	res.redirect('/');

    }
});

//////////////////////////////
// routing for new batch GET
//////////////////////////////
app.get('/new_batch', function(req, res){
    console.log('redirecting to new_batch page');
    db.all("SELECT * FROM batch_list", function (err, rows) {
	res.render('new_batch', {table_list:rows});
    });

});

//////////////////////////////
// routing for new batch POST
//////////////////////////////
app.post('/new_batch', function (req, res) {
    console.log('POST request to create a new batch');
    console.log(req.body);
    var name = req.body.batch_name;
    var temperature = req.body.temperature
    var duration = req.body.duration;
    console.log(name + " " + temperature + " " + duration);

    //send create msg through socket
    client.write("create" + " " + name + " " + temperature + " " + duration)

    res.redirect('/');

});

app.listen(8080);
