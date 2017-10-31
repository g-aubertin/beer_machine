#!/usr/bin/env python

import sys, os, time, signal, socket
import sqlite3, datetime
import webui, threading
from random import randint

W1_PATH = ""
test_mode = 0

class state_machine:
    STOPPED = "stopped"
    RUNNING = "running"
    SHUTDOWN = "shutdown"

class batch_status:
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ENDED = "ended"

state = state_machine.STOPPED

def socket_init():

    server_address = './beer_socket'

    # Make sure the socket does not already exist
    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # Bind the socket to the port
    print 'UDS socket binding up on %s' % server_address
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)
    return sock


def get_config(path):

    global W1_PATH, PLUG_CODE_ON, PLUG_CODE_OFF, STANDALONE_TEMP
    fd_config = open(path, 'r')
    for line in fd_config.readlines():
        line = " ".join(line.split())
        line = line.split(" ")
        if (line[0] == "W1_PATH"):
            print "W1_PATH :", line[1]
            W1_PATH = line[1]
    fd_config.close()

def read_temperature():

    # read file from 1-wire sysfs and parse result
    fd = open(W1_PATH, "r")
    temp_str = fd.read()
    fd.close()
    temp_str = temp_str.split()
    temp_str = temp_str[-1].translate(None, " t=")
    temp_flt = float(temp_str) / 1000
    print "current temperature :", temp_flt
    return temp_flt

def worker_temp():

    conn = sqlite3.connect('beer_machine.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS test_table (date TEXT, temperature float)''')
    conn.close()

    t = threading.currentThread()

    print "worker thread started"

    while (True):

        if (t.stop_signal == True):
            break
        else:
            # get temperature
            if test_mode == 0:
                temp = read_temperature()
            else:
                temp = randint(20,25)

            # save temp in db
            conn = sqlite3.connect('beer_machine.db')
            c = conn.cursor()
            print "adding value", temp, "to db"
            c.execute("INSERT INTO test_table VALUES (?, ?)", (time.ctime(), temp))
            conn.commit()
            conn.close()

        time.sleep(10)

if __name__ == '__main__':

    if (len(sys.argv) < 2):
        print "configuration file needed"
        sys.exit(0)

    if sys.argv[2] == '-t':
        print "test mode enabled"
        test_mode = 1

    # database init
    conn = sqlite3.connect('beer_machine.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS batch_list
             (date TEXT, name TEXT, temperature float, duration INT, status TEXT)''')
    conn.close()

    # UDS socket init
    uds_sock = socket_init()

    # command list :
    # create(name, fermentation temperature, fermentation time) : create new batch
    # start(name): start batch
    # stop(name): stop batch
    # delete(name) : remove batch from db

    while True:

        # Wait for a connection
        print 'waiting for a connection'
        connection, client_address = uds_sock.accept()

        print "inbound connection successful"

        while True:

            try:
                data = connection.recv(256)
            except KeyboardInterrupt:
                print "SIGINT received while waiting for data !"
                t.stop_signal = True
                t.join()
                print "worker thread has been stopped. exiting...."
                sys.exit(0)

            if not data:
                break
            command = data.split(" ")

            if command[0] == "create" :
                print "from socket: CREATE requested : ", command
                conn = sqlite3.connect('beer_machine.db')
                c = conn.cursor()

                # create new table
                c.execute("CREATE TABLE IF NOT EXISTS %s (date TEXT, temperature float)" % command[1])
                # add entry in table_list : creation date - name - temperature - duration -status
                c.execute("INSERT INTO batch_list VALUES (?, ?, ?, ?, ?)",
                    (time.ctime(), command[1], float(command[2]), int(command[3]), batch_status.READY))
                conn.commit()

                # if there is an on-going batch, change it to "ENDED"
                # c.execute("SELECT * FROM batch_list WHERE status = 'on-going'")
                # rows = c.fetchall()
                # if rows:
                    # todo : pop-up to explain that the on-going batch will be moved to ENDED
                    # and move it to ENDED

                conn.close()

            if command[0] == "get_status" :
                print "from socket: STATUS requested"
                connection.sendall("status "+ state)

            if command[0] == "start" :
                print "from socket: START requested"
                t = threading.Thread(target=worker_temp)
                t.stop_signal = False
                t.start()
                state = state_machine.RUNNING
                print "worker thread started"

            if command[0] == "stop" :
                print "from socket: STOP requested"
                t.stop_signal = True
                t.join()
                state = state_machine.STOPPED
                print "worker thread stopped"
