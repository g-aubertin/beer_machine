import sqlite3
import sys
import time
import json
from datetime import datetime
from time import mktime


class batch_status:
    STARTED = "started"
    STOPPED = "stopped"


class beer_db:
    """ sqlite3 database wrapper to store fermentation data

    Attributes:
        file: path to database
    """

    def __init__(self, filename):

        self.file = filename
        # todo : what happens if file does not exist ?
        try:
            conn = sqlite3.connect(self.file)
            c = conn.cursor()
        except sqlite3.Error as e:
                print ("error connecting to database, exiting...")
                sys.exit()
        # if this is an empty DB, create the batch list
        c.execute('''CREATE TABLE IF NOT EXISTS batch_list
                 (date INT, name TEXT, temperature float, duration INT, status TEXT)''')
        conn.commit()
        conn.close()

    def new_batch(self, name, temperature, duration):

        conn = sqlite3.connect(self.file)
        c = conn.cursor()
        # clear db and set all other batches to "stopped"
        c.execute("UPDATE batch_list SET status='stopped'")
        # create new table for temperature data
        c.execute("CREATE TABLE IF NOT EXISTS %s (date INT, temperature float)" % name)
        # add entry in table_list : creation date - name - temperature - duration -status
        c.execute("INSERT INTO batch_list VALUES (?, ?, ?, ?, ?)",
            (time.ctime(), str(name), int(temperature), int(duration), batch_status.STARTED))
        # create empty json file for charting
        fd_json = open("nodejs/public/%s.json" % name, "w");
        fd_json.close()
        conn.commit()
        conn.close()

    def get_status(self):

        conn = sqlite3.connect(self.file)
        c = conn.cursor()
        c.execute("SELECT name FROM batch_list WHERE status='started'")
        # return a list of running batches (but there shouldn't be more than one)
        batch_list = c.fetchall()
        conn.close()
        return batch_list

    def change_status(self, batch_name, status):

        conn = sqlite3.connect(self.file)
        c = conn.cursor()
        c.execute("UPDATE batch_list SET status = ? WHERE name = ?"(status, batch_name))
        conn.commit()
        conn.close()

    def add_temperature(self, batch_name, temp):

        conn = sqlite3.connect(self.file)
        c = conn.cursor()
        # calculate time in millisecond since epoch
        dt = datetime.now()
        sec_since_epoch = mktime(dt.timetuple()) + dt.microsecond/1000000.0
        timestamp = sec_since_epoch * 1000
        print "timestamp: %d ", timestamp
        # add latest measurement
        c.execute("INSERT INTO %s VALUES (?, ?)"% batch_name, (int(timestamp), temp))
        # generate new json file to charting
        c.execute("SELECT * FROM %s" % batch_name)
        conn.commit()
        temp = c.fetchall()
        print "creating new json file"
        fd_json = open("nodejs/public/%s.json" % batch_name, "w");
        json.dump(temp, fd_json, separators=(',', ': '), indent=4)
        conn.close()
