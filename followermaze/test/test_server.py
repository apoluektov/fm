# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

import unittest

import socket
import threading
import time

from followermaze.eventhandler import EventHandler
from followermaze.server import Server
from followermaze.usergraph import UserGraph
from followermaze.event import Event, EventQueue


def init_socket(port):
    HOST = 'localhost'
    PORT = port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(0.05)
    s.connect((HOST, PORT))
    return s


def receive(s, seconds):
    start_time = time.time()
    while time.time() - start_time < seconds:
        try:
            data = s.recv(1024)
        except: # ignore timeout
            data = None

    s.close()


def new_client(userid):
    def client():
        s = init_socket(9099)
        s.sendall('%s\r\n' % userid)
        receive(s, 0.05)

    t = threading.Thread(target=client)
    return t


def event_source(*messages):
    def source():
        s = init_socket(9090)
        for msg in messages:
            s.sendall('%s\r\n' % msg)
        receive(s, 0.05)

    t = threading.Thread(target=source)
    return t


class TestServer(unittest.TestCase):
    '''
    Not really a unit-test as it uses real sockets and threading but hopefully OK for the challenge purposes.
    '''

    class Listener(object):
        def __init__(self, server):
            self.clients_received = []
            self.events_received = []

        def on_client_id_received(self, s, msg):
            self.clients_received.append(msg)
            return False

        def on_event_received(self, msg):
            self.events_received.append(msg)
            return True

        def on_poll(self):
            pass

    def assertClientsReceived(self, messages):
        self.assertEqual(set(self.listener.clients_received), set(messages))

    def assertEventsReceived(self, messages):
        self.assertEqual(self.listener.events_received, messages)

    def setUp(self):
        self.server = Server(event_port=9090, client_port=9099)
        self.listener = self.Listener(self.server)
        self.server.set_listener(self.listener)

        self.server.start()

    def tearDown(self):
        self.server.stop()


    def test_receiving_messages(self):
        def start_and_join(t):
            t.start()
            t.join()

        self.assertClientsReceived([])
        self.assertEventsReceived([])

        start_and_join(new_client('me'))
        self.assertClientsReceived(['me'])
        self.assertEventsReceived([])

        start_and_join(new_client('me'))
        self.assertClientsReceived(['me', 'me'])
        self.assertEventsReceived([])

        start_and_join(new_client('you'))
        self.assertClientsReceived(['me', 'me', 'you'])
        self.assertEventsReceived([])

        start_and_join(event_source('one', 'two', 'three'))
        self.assertClientsReceived(['me', 'me', 'you'])
        self.assertEventsReceived(['one', 'two', 'three'])


    def test_concurrency(self):
        self.assertClientsReceived([])
        self.assertEventsReceived([])

        clients = [new_client(u) for u in 'me', 'me', 'you']
        clients.append(event_source('one', 'two', 'three'))

        for c in clients:
            c.start()

        for c in clients:
            c.join()

        self.assertClientsReceived(['me', 'me', 'you'])
        self.assertEventsReceived(['one', 'two', 'three'])
