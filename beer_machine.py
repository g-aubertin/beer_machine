#!/usr/bin/env python

import sys, os, time, signal, socket
import sqlite3, datetime
import webui, threading

W1_PATH = ""

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

def worker_temp(target_temp):

   t = threading.currentThread()
   while (t.stop_signal == False):

        # get temperature
        temp = read_temperature()

        time.sleep(10)


if __name__ == '__main__':

    if (len(sys.argv) < 2):
        print "configuration file needed"
        sys.exit(0)

    # database init
    conn = sqlite3.connect('beer_machine.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS batch_list
             (date TEXT, temperature float, name TEXT, status INT)''')
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
            data = connection.recv(256)
            if not data:
                break
            print 'data received : ', data
            command = data.split(" ")

            if command[0] == "start" :
                print "receiving start"
                t = threading.Thread(target=worker_temp, args=(21,))
                t.stop_signal = False
                t.start()

            if command[0] == "stop" :
                print "receiving start"
                t.stop_signal = True

        connection.close()
        print 'connection close'
