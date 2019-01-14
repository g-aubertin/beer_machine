import sqlite3
import sys
import time
import json

JSON_EXPORT="./beer.json"

class batch_status:
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ENDED = "ended"

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
                 (date TEXT, name TEXT, temperature float, duration INT, status TEXT)''')
        conn.commit()
        conn.close()

    def new_batch(self, name, temperature, duration):

        conn = sqlite3.connect(self.file)
        c = conn.cursor()
        # create new table for temperature data
        c.execute("CREATE TABLE IF NOT EXISTS %s (date TEXT, temperature float)" % command[1])
        # add entry in table_list : creation date - name - temperature - duration -status
        c.execute("INSERT INTO batch_list VALUES (?, ?, ?, ?, ?)",
            (time.ctime(), str(name), int(temperature), int(duration), batch_status.READY))
        conn.commit()
        conn.close()

    def get_status(self):

        conn = sqlite3.connect(self.file)
        c = conn.cursor()
        c.execute("SELECT name FROM batch_list WHERE status=?", (batch_status.RUNNING,))
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
        # add latest measurement
        c.execute("INSERT INTO %s VALUES (?, ?)"% batch_name, (time.ctime(), temp))
        # generate new json file to charting
        c.execute("SELECT * FROM %s" % batch_name)
        conn.commit()
        temp = c.fetchall()
        print "creating new json file"
        fd_json = open("nodejs/public/%s.json" % batch_name, "w");
        json.dump(temp, fd_json, separators=(',', ': '), indent=4)
        conn.close()
