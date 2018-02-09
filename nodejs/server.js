console.log('starting server.js');

var daemon_status = 0

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

  if (data_tab[0].toString() == "status") {
    if (data_tab[1].toString() == "running") {
      console.log("socket response: beer_machine daemon is in RUNNING state")
      daemon_status = 1
    }

    if (data_tab[1].toString() == "stopped") {
      console.log("socket response: beer_machine daemon is in STOPPED state")
      daemon_status = 0
    }
  }
});

/////////////////////////////
// routing for overview page
/////////////////////////////
app.get('/', function(request, response) {

  console.log("receiving GET on /")

  //first, let's fetch batch_list for batch history dropdown menu
  db.all("SELECT * FROM batch_list", function (err, rows) {
    batch_list = rows;
  });

  // check if there is an on-going brew (status = "running"), and select it for display.
  // otherwise, display nothing
  db.all("SELECT * FROM batch_list WHERE status='running'", function (err, rows) {
    rows.forEach( function(row) {
      selected_brew = row.name;
      console.log("selected batch:" + row.name )
      db.all("SELECT * FROM " + selected_brew, function (err, rows) {
        response.render('index', {point_list:rows, table_list:batch_list, beer_machine:daemon_status})
      });
    });
    response.render('index', {point_list:[], table_list:batch_list, beer_machine:daemon_status})
  });
});

////////////////////////////
// routing for overview POST
///////////////////////////
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
});

//////////////////////////////////////////////////
// routing for monitoring page with selected batch
//////////////////////////////////////////////////
app.get('/monitoring/:batch', function(request, response) {

  console.log("receiving GET on /monitoring/:batch !")

  var batch_name = request.params.batch;

  //first, let's fetch batch_list for batch history dropdown menu
  db.all("SELECT * FROM batch_list", function (err, rows) {
    batch_list = rows;
    rows.forEach(function(row) {
      if (row.name === batch_name) {
        batch_info = row;
      }
      // we need to get the associate batch information to render
    });
    db.all("SELECT * FROM " + batch_name, function (err, rows) {
      response.render('monitoring', {point_list:rows, table_list:batch_list, beer_machine:daemon_status})
    });
  });

});

//////////////////////////////////////////////////
// routing for monitoring page POST
//////////////////////////////////////////////////
app.post('/monitoring/:batch', function(request, response) {

  console.log("receiving POST on /monitoring/:batch !")

  var batch_name = request.params.batch;

  // stop button
  if (request.body && (request.body.button_value === "stop")) {
    console.log("stop pushed")
    client.write("stop")
    daemon_status = 0
  }

  // stop button
  if (request.body && (request.body.button_value === "start")) {
    console.log("start pushed")
    client.write("start " + batch_name)
    daemon_status = 1
  }

  response.redirect('/monitoring/' + batch_name);
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
    var name = req.body.batch_name;
    var temperature = req.body.temperature
    var duration = req.body.duration;
    console.log(name + " " + temperature + " " + duration);

    //send create msg through socket
    client.write("create" + " " + name + " " + temperature + " " + duration)

    res.redirect('/');

});


///////////////////////////
// routing for system GET
///////////////////////////
app.get('/system', function(req, res){
  console.log('redirecting to new_batch page');
  db.all("SELECT * FROM batch_list", function (err, rows) {
    res.render('system', {table_list:rows});
    });
});


app.listen(8080);
