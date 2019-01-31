#!/usr/bin/python2
import sys, os, time, signal, socket
import datetime
import threading
from random import randint
import beer_db

W1_PATH = ""
test_mode = 0

# overall state machine of the daemon
class daemon_status:
    STOPPED = "daemon_stopped"
    RUNNING = "daemon_running"
    SHUTDOWN = "daemon_shutdown"

daemon_state = daemon_status.STOPPED

# initialize UDS socket
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

# read configuration file
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

# read file from 1-wire sysfs and parse result
def read_temperature():

    fd = open(W1_PATH, "r")
    temp_str = fd.read()
    fd.close()
    temp_str = temp_str.split()
    temp_str = temp_str[-1].translate(None, " t=")
    temp_flt = float(temp_str) / 1000
    print "current temperature :", temp_flt
    return temp_flt

# infinite loop getting temp from thermometer and storing it in the DB
def worker_thread(batch_name):

    print "worker thread started"
    t = threading.currentThread()

    while (True):
        # get temperature
        if test_mode == 0:
            temp = read_temperature()
        else:
            temp = randint(20,25)
        # save temp in db
        db.add_temperature(batch_name, temp)
        print str(temp) + " added to " + batch_name

        # checking for stop signal during 10s sleep
        i = 0
        while(i < 10):
            if (t.stop_signal == True):
                sys.exit()
            time.sleep(1)
            i = i + 1

if __name__ == '__main__':

    if (len(sys.argv) < 2):
        print "configuration file needed"
        sys.exit(0)

    get_config(sys.argv[1]);

    if (len(sys.argv) > 2 and sys.argv[2] == '-t'):
        print "test mode enabled"
        test_mode = 1

    # initialize db
    db = beer_db.beer_db('beer_machine.db')

    # create and bind socket
    uds_sock = socket_init()

    ############################################################################
    # available RPC calls:
    # create(name, fermentation temperature, fermentation time) : new batch
    # start(name): start batch
    # stop(name): stop batch
    # delete(name) : remove batch from db
    ############################################################################

    while True:
        # Wait for a socket connection
        print 'waiting for a connection'
        connection, client_address = uds_sock.accept()
        print "inbound connection successful"

        while True:
            try:
                # wait for inputs on the socket
                data = connection.recv(256)
            except KeyboardInterrupt:
                print "SIGINT received while waiting for data !"
                t.stop_signal = True
                t.join()
                print "worker thread has been stopped. exiting...."
                sys.exit(0)
            if not data:
                break

            # separate command and arguments
            command = data.split(" ")

            # new batch
            if command[0] == "create" :
                print "from socket: CREATE requested : ", command
                db.new_batch(command[1], command[2], command[3])
                batch_status = db.get_status()
                connection.sendall("batch" + " " + " ".join(batch_status[0]))

            # status request
            if command[0] == "get_status" :
                print "from socket: daemon STATUS requested"
                batch_status = db.get_status()
                connection.sendall("status" + " " +  daemon_state)
                if batch_status:
                    connection.sendall("batch" + " " + " ".join(batch_status[0]))

            # start aquisition
            if command[0] == "start" :
                print "from socket: START requested"
                t = threading.Thread(target=worker_thread, args=[" ".join(batch_status[0])])
                t.stop_signal = False
                t.start()
                daemon_state = daemon_status.RUNNING

            # stop aquisition
            if command[0] == "stop" :
                print "from socket: STOP requested"
                t.stop_signal = True
                t.join()
                daemon_state = daemon_status.STOPPED
                print "worker thread stopped"
