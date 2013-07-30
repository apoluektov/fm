# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

import logging

from followermaze.event import Event


class EventHandler(object):
    '''
    Serves as a controller between the system components.
    Listens to events from the server, dispatches them for reordering and then processes them,
    possibly sending notifications back using the server.
    '''

    def __init__(self, graph, server, queue):
        self.graph = graph
        self.server = server
        self.queue = queue

    def on_client_id_received(self, connection, msg):
        '''
        Called by server when new client id is received.
        Return value False interpreted by server as a reject to accept more messages from this connection.
        '''
        logging.info("EventHandler: new client id received from server: '%s'" % msg)
        self.graph.register_user(msg, connection=connection)
        return False

    def on_event_received(self, msg):
        '''
        Called by server when new message from event source is received.
        Return value False interpreted by server as a reject to accept more events from this connection.
        '''
        logging.info("EventHandler: new event string received from server: '%s'" % msg)
        try:
            event = Event.from_string(msg)
            self.queue.add(event)
            return True
        except ValueError, v:
            logging.warning("EventHandler: Bad event string; error text: '%s'" % v)
            return False

    def on_poll(self):
        '''Called by server after some data are received over network.'''
        self.queue.poll()

    def on_event(self, event):
        '''Called by event queue when new event can be processed.'''
        logging.info("EventHandler: processing event '%s'" % event.message)
        if event.code == 'F':
            self.follow(event)
        elif event.code == 'U':
            self.unfollow(event)
        elif event.code == 'B':
            self.broadcast(event)
        elif event.code == 'P':
            self.private(event)
        elif event.code == 'S':
            self.status_update(event)

    def follow(self, event):
        user = self.graph.user(event.to_user)
        user.add_follower(event.from_user)
        self.notify(user, event.message)

    def unfollow(self, event):
        self.graph.user(event.to_user).remove_follower(event.from_user)

    def broadcast(self, event):
        for u in self.graph.all_users():
            self.notify(u, event.message)

    def private(self, event):
        self.notify(self.graph.user(event.to_user), event.message)

    def status_update(self, event):
        for u in self.graph.followers_of(event.from_user):
            self.notify(u, event.message)

    def notify(self, user, msg):
        connection = getattr(user, 'connection', None)
        if connection:
            self.server.send(connection, msg)
