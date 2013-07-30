# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

import socket
import select
import sys
import logging
import threading
import time
import tempfile
import os, os.path
import shutil
from collections import defaultdict

from event import Event


class Server(object):
    '''
    Manages connections of user clients and event source, and receiving/sending data from/to them.
    Notofies registered listener when some data is ready for processing by the application.
    '''
    def __init__(self, event_port, client_port):
        self.event_control_socket = self._init_control_socket(event_port)
        self.client_control_socket = self._init_control_socket(client_port)
        self.service_socket = self._init_service_socket()
        self.event_socket = None

        self.inputs = [self.event_control_socket, self.client_control_socket, self.service_socket]
        self.outputs = set()

        self.event_data = ''
        self.client_data = defaultdict(str)

        self.should_stop = False


    def set_listener(self, listener):
        '''
        Sets listener that is notified when some data is ready for processing by the application.
        The listener must not be null and must provide the following methods:
        class Listener(object):
            def on_client_id_received(self, connection, message):
                # return True if wants to listen to this connection further

            def on_event_received(self, message):
                # return True if wants to listen to this connection further

            def on_poll(self):
                # return nothing
        '''
        self.listener = listener

    def send(self, connection, data):
        '''Sends given data over given connection.'''
        self.outputs.add(connection)
        self.client_data[connection] += data + '\r\n'

    def client_id_received(self, connection, msg):
        '''Notifies the listener of the client id just received.'''
        more = self.listener.on_client_id_received(connection, msg)
        if not more:
            connection.shutdown(socket.SHUT_RD)
            self.inputs.remove(connection)

    def event_received(self, msg):
        '''
        Notifies the listener of the event just received.
        If the event was malformed, disconnect the client.
        '''
        more = self.listener.on_event_received(msg)
        if not more:
            logging.warning('event source will be disconnected.')
            self._reset_event_socket()

    def start(self):
        '''
        Starts polling thread.
        set_listener() must be called before this method.
        '''
        self.server_thread = threading.Thread(target=self.run)
        self.server_thread.start()

    def run(self):
        while not self.should_stop:
            self._poll()
        self._cleanup()

    def stop(self):
        '''
        Requests server thread stop and waits for it to complete.

        Here is the trick: server thread is listening for the service socket, and it interprets connections
        as a stop request. The beauty is that communication is done without any synchronization, and using
        the same select() call that listens for the clients.
        '''
        logging.info('Server: requesting polling thread to stop ...')
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self.service_socket_filename)
        self.inputs.append(s)

        self.server_thread.join()

    def _poll(self):
        r, w, e = select.select(self.inputs, self.outputs, self.inputs)
        for s in r:
            if s == self.event_control_socket:
                self._handle_event_source_connection()
            elif s == self.client_control_socket:
                self._handle_client_connection()
            elif s == self.event_socket:
                self._handle_event_data()
            elif s == self.service_socket:
                self.should_stop = True
                return
            else:
                self._handle_client_data(s)
        for s in w:
            self._write_data(s)
        for s in e:
            self.inputs.remove(s)
            s.close()

        self.listener.on_poll()


    def _init_control_socket(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setblocking(0)
        s.bind(('', port))
        s.listen(5)
        return s

    def _init_service_socket(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.service_socket_filename = os.path.join(
            tempfile.mkdtemp(dir='/tmp', prefix='followermaze-'),
            'internal')
            
        s.bind(self.service_socket_filename)
        s.listen(1)
        return s

    def _reset_event_socket(self):
        self.inputs.remove(self.event_socket)
        self.event_socket.close()
        self.event_socket = None

    def _handle_event_source_connection(self):
        if not self.event_socket:
            self.event_socket, addr = self.event_control_socket.accept()
            self.event_socket.setblocking(0)
            self.inputs.append(self.event_socket)

    def _handle_client_connection(self):
        conn, addr = self.client_control_socket.accept()
        conn.setblocking(0)
        self.inputs.append(conn)

    def _handle_event_data(self):
        data = self.event_socket.recv(1024)
        if data:
            data = self.event_data + data
            ds = data.split('\n')
            for msg in ds[:-1]:
                if msg:
                    msg = msg.strip('\r')
                    self.event_received(msg)
            self.event_data = ds[-1]
        else:
            self._reset_event_socket()


    def _handle_client_data(self, s):
        data = s.recv(1024)
        if data:
            client_data = self.client_data[s]
            data = client_data + data
            if data.endswith('\n'):
                data = data.rstrip('\n').rstrip('\r')
                self.client_id_received(s, data)
                client_data = ''
            else:
                client_data = data
        else:
            self.inputs.remove(s)
            s.close()


    def _write_data(self, s):
        client_data = self.client_data[s]
        try:
            bytes_send = s.send(client_data)
            client_data = client_data[bytes_send:]
            if not client_data:
                self.outputs.remove(s)
                del self.client_data[s]
        except socket.error, v:
            logging.warning('Problem with writing socket; disconnecting client.')
            logging.warning('error text: %s' % v)
            # remove the troublemaker's socket and clean up its residual data
            self.outputs.remove(s)
            del self.client_data[s]


    def _cleanup(self):
        for s in self.inputs:
            s.close()
        for s in self.outputs:
            s.close()
        self.service_socket.close()
        shutil.rmtree(os.path.dirname(self.service_socket_filename))
