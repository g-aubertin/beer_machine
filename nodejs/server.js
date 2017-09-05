console.log('starting server.js');

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
  console.log("connected !");

  client.write("create IPA 21 21 toto")

});

client.on("data", function(data) {
    console.log("receiving data over socket");
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

    // use it for default display
    db.all("SELECT * FROM " + selected_brew, function (err, rows) {
      response.render('index', {point_list:rows, table_list:batch_list})
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
          res.render('index', {point_list:batch_switch, table_list:rows})
          });
      });
    }

    // new batch button
    if (req.body && (req.body.new_batch === '')) {
      res.redirect('/new_batch');
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
    db.serialize(function() {
      db.run("CREATE TABLE IF NOT EXISTS "+ name +" (date TEXT, temperature NUMERIC, switch NUMERIC)", function(err){
        if (err)
          console.log(err);
        res.redirect('/');
      });
    });
});

app.listen(8080);
