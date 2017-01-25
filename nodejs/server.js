console.log('starting server.js');

// include and initialize libraries
let express = require('express');
app = express();

let path = require('path');

let sqlite3 = require('sqlite3').verbose();
var db = new sqlite3.Database('beer_machine.db');

//template engine
app.set('view engine', 'ejs')

// set public/ as static path
app.use(express.static('public'));

//routing default response
app.get('/', function(request, response) {

  db.serialize(function() {
    db.all("SELECT * FROM fermentation_temp", function (err, rows) {
      current_batch_temp = rows;
    });
    db.all("SELECT name FROM sqlite_master WHERE type='table'", function (err, rows) {
      response.render('index', {point_list:current_batch_temp, table_list:rows})
    });
  });
});

app.listen(8080);
