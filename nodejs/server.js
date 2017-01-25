console.log('starting server.js');

// include and initialize libraries
var express = require('express');
app = express();

var path = require('path');

var sqlite3 = require('sqlite3').verbose();
var db = new sqlite3.Database('beer_machine.db');

var bodyParser = require('body-parser');
app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({ extended: true })); // support encoded bodies
//template engine
app.set('view engine', 'ejs')

// set public/ as static path
app.use(express.static('public'));

//  routing for root page (data display)
app.get('/', function(request, response) {

  db.serialize(function() {
    if (request.body && request.body.tables) {
      db.all("SELECT * FROM " +request.body.tables, function (err, rows) {
        current_batch_temp = rows;
      });
    }
    else {
      db.all("SELECT * FROM fermentation_temp", function (err, rows) {
        current_batch_temp = rows
      });
    }

  db.all("SELECT name FROM sqlite_master WHERE type='table'", function (err, rows) {
    response.render('index', {point_list:current_batch_temp, table_list:rows})
    });
  });
});

//routing for buttons
app.post('/', function(req, res) {
    console.log('POST request to the homepage');
    console.log(req.body);
    // table change
    if (req.body && req.body.tables) {
      db.serialize(function() {
        if (req.body && req.body.tables) {
          db.all("SELECT * FROM " +req.body.tables, function (err, rows) {
            batch_switch = rows;
          });
        }
      });
    }
    db.all("SELECT name FROM sqlite_master WHERE type='table'", function (err, rows) {
      res.render('index', {point_list:batch_switch, table_list:rows})
    });
});

// routing for new batch page
app.get('/new_batch', function(req, res){
  console.log('redirecting to new_batch page');
  res.render('new_batch');
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
