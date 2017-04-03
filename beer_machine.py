#!/usr/bin/env python

import sys, os, time, signal, socket
import sqlite3, datetime
import webui

SOCKET_CODE_ON = 0
SOCKET_CODE_OFF = 0
W1_PATH = ""

def sock_init():

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

    global W1_PATH, SOCKET_CODE_ON, SOCKET_CODE_OFF
    fd_config = open(path, 'r')
    for line in fd_config.readlines():
        line = " ".join(line.split())
        line = line.split(" ")
        if (line[0] == "W1_PATH"):
            print "W1_PATH :", line[1]
            W1_PATH = line[1]
        if (line[0] == "SOCKET_CODE_ON"):
            print "SOCKET_CODE_ON :", line[1]
            SOCKET_CODE_ON = int(line[1])
        if (line[0] == "SOCKET_CODE_OFF"):
            print "SOCKET_CODE_OFF :", line[1]
            SOCKET_CODE_OFF = int(line[1])
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

def socket_command(value):

    cmd = "/opt/beer_machine/433_send %d %d" % (value, 24)
    os.system(cmd)
    if value == SOCKET_CODE_ON:
        return 1
    else:
        return 0

def dump_db():

    conn = sqlite3.connect('/opt/beer_machine/beer_machine.db')
    c = conn.cursor()
    c.execute("SELECT * FROM fermentation_temp")
    for data in c.fetchall():
        print data

def control_temp(target_temp):

    while True:

        # get temperature
        temp = read_temperature()

        # adjust temperature with socket
        if temp > target_temp + 0.5:
             socket_command(SOCKET_CODE_ON);
        if temp < target_temp - 0.5:
            socket_command(SOCKET_CODE_OFF);


if __name__ == '__main__':

    if (len(sys.argv) < 2):
        print "configuration file needed"
        sys.exit(0)

    # check if 433Mhz tools are compiled
    if os.path.exists("/opt/beer_machine/433_send") == False:
    print "433_send tool is not compiled. exiting.."
    sys.exit(0)

    # read configuration file and set variables
    get_config(sys.argv[1])

    # before getting started, we switch off the plug to be in a known state
    socket_status = socket_command(SOCKET_CODE_OFF);

    # if standalone mode, call control loop directly (simple mode)
    if (sys.argv[len(sys.argv)-1]) == '-s':
        while True:
            control_temp()
            time.sleep(30)

    # UDS socket init
    uds_sock = sock_init()

    # Wait for a connection
    print 'waiting for a connection'
    connection, client_address = sock.accept()

    print "connection successful to ", client_address

        while True:
            data = connection.recv(16)
            print 'data received', data

    # once connect, wait for commands

    # database init
    #conn = sqlite3.connect('/opt/beer_machine/beer_machine.db')
    #c = conn.cursor()
    #c.execute('''CREATE TABLE IF NOT EXISTS fermentation_temp
#             (date text, temperature float, switch int)''')
#    conn.close()
