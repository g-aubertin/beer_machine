console.log('starting server.js');

var daemon_status = 0

// include and initialize libraries
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
  client.write("socket request: status")

});

client.on("data", function(data) {

  console.log(data.toString())

  if (data.toString() == "running") {
    console.log("socket response: beer_machine daemon is in RUNNING state")
    daemon_status = 1
  }

  if (data.toString() == "socket response: beer_machine daemon is in STOPPED state") {
    daemon_status = 0
  }
});

//  routing for root page (dashboard)
app.get('/', function(request, response) {

  console.log("receiving GET on /")
  // first, we need to get the batch list to load the on-going brew (status = 1).
  // if not,then we load the first in table
  db.all("SELECT * FROM batch_list", function (err, rows) {
    batch_list = rows
    selected_brew = rows[0]
    rows.forEach( function(row) {
      if (row.status == 1) {
        selected_brew = row.name;
      }
    });

    selected_brew = "test_table"
    // use it for default display
    db.all("SELECT * FROM " + selected_brew, function (err, rows) {
      response.render('index', {point_list:rows, table_list:batch_list, beer_machine:daemon_status})
    });
  });
});

// routing for buttons
app.post('/', function(req, res) {

    // debug
    console.log('POST request to the homepage');
    console.log(req.body);

    // batch switch
    if (req.body && req.body.tables) {
      db.serialize(function() {
        db.all("SELECT * FROM " +req.body.tables, function (err, rows) {
          batch_switch = rows;
          });
        db.all("SELECT name FROM sqlite_master WHERE type='table'", function (err, rows) {
          res.render('index', {point_list:batch_switch, table_list:rows, beer_machine:daemon_status})
          });
      });
    }

    // new batch button
    if (req.body && (req.body.new_batch === '')) {
      res.redirect('/new_batch');
    }

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

// routing for new batch page
app.get('/new_batch', function(req, res){
  console.log('redirecting to new_batch page');
  db.all("SELECT name FROM sqlite_master WHERE type='table'", function (err, rows) {
    res.render('new_batch', {table_list:rows});
    });
});

// routing for new batch page
app.get('/system', function(req, res){
  console.log('redirecting to new_batch page');
  db.all("SELECT name FROM sqlite_master WHERE type='table'", function (err, rows) {
    res.render('system', {table_list:rows});
    });
});

//routing for new_batch post
app.post('/new_batch', function (req, res) {
    console.log('POST request to create a new batch');
    var name = req.body.batch_name;
    var temperature = req.body.temperature
    var duration = req.body.duration;
    console.log(name + " " + temperature + " " + duration);

    //send create msg through socket
    client.write("create" + " " + name + " " + temperature + " " + duration)
    res.redirect('/');

});

app.listen(8080);
