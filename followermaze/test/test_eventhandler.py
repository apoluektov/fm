# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

import unittest
from collections import defaultdict

from followermaze.eventhandler import EventHandler
from followermaze.server import Server
from followermaze.usergraph import UserGraph
from followermaze.event import Event


class FakeServer(object):
    def __init__(self):
        self.messages = defaultdict(list)

    def send(self, conn, msg):
        self.messages[conn].append(msg + '\n')


class LoggingUser(UserGraph.User):
    @classmethod
    def start_logging_changes(cls):
        cls.constructed = False
        cls.added_follower = False
        cls.removed_follower = False

    @classmethod
    def graph_changed(cls):
        return cls.constructed or cls.added_follower or cls.removed_follower

    @classmethod
    def followers_changed(cls):
        return cls.added_follower or cls.removed_follower

    def __init__(self):
        UserGraph.User.__init__(self)
        LoggingUser.constructed = True

    def add_follower(self, f):
        UserGraph.User.add_follower(self, f)
        LoggingUser.added_follower = True

    def remove_follower(self, f):
        UserGraph.User.remove_follower(self, f)
        LoggingUser.removed_follower = True


class TestEventHandler(unittest.TestCase):
    def setUp(self):
        self.graph = UserGraph(LoggingUser)

        self.graph.register_user('me', connection=1)
        self.graph.register_user('you', connection=2)
        self.graph.register_user('they', connection=3)
        self.graph.register_user('nobody', connection=4)

        self.graph.user('me').add_follower('you')
        self.graph.user('me').add_follower('they')
        self.graph.user('you').add_follower('nobody')
        self.graph.user('nothere').add_follower('nobody')

        self.server = FakeServer()
        self.handler = EventHandler(self.graph, self.server, None)


    def test_follow_works(self):
        self.handler.follow(Event.from_string('1|F|misterx|me'))

        self.assertTrue(self.graph.user('misterx') in self.graph.followers_of('me'))
        self.assertEqual(self.server.messages, {1: ['1|F|misterx|me\n'] })


    def test_follow_not_connected_user_works(self):
        self.handler.follow(Event.from_string('1|F|misterx|xxx'))

        # misterx now follows xxx but no messages send to xxx because he is not connected
        self.assertTrue(self.graph.user('misterx') in self.graph.followers_of('xxx'))
        self.assertEqual(self.server.messages, {})


    def test_unfollow_works(self):
        self.assertTrue(self.graph.user('you') in self.graph.followers_of('me'))
        self.assertTrue(self.graph.user('nobody') in self.graph.followers_of('nothere'))

        self.handler.unfollow(Event.from_string('1|U|you|me'))
        self.handler.unfollow(Event.from_string('1|U|nobody|nothere'))

        self.assertTrue(self.graph.user('you') not in self.graph.followers_of('me'))
        self.assertTrue(self.graph.user('nobody') not in self.graph.followers_of('nothere'))
        self.assertEqual(self.server.messages, {})


    def test_broadcast_works(self):
        LoggingUser.changed = False
        self.handler.broadcast(Event.from_string('1|B'))

        msg = ['1|B\n']
        self.assertEqual(self.server.messages, {1: msg, 2: msg, 3: msg, 4: msg})
        # graph should not have changed
        self.assertFalse(LoggingUser.changed)


    def test_private_message_to_connected_user_works(self):
        LoggingUser.start_logging_changes()
        self.handler.private(Event.from_string('1|P|you|me'))
        self.assertEqual(self.server.messages, {1: ['1|P|you|me\n']} )
        # graph should not have changed
        self.assertFalse(LoggingUser.graph_changed())


    def test_private_message_to_not_connected_user_works(self):
        LoggingUser.start_logging_changes()
        self.handler.private(Event.from_string('1|P|you|him'))
        self.assertEqual(self.server.messages, {})
        # new user can be added here by UserGraph on demand but not followers
        self.assertFalse(LoggingUser.followers_changed())


    def test_status_update_works(self):
        LoggingUser.start_logging_changes()
        self.handler.status_update(Event.from_string('1|S|me'))
        self.assertEqual(self.server.messages, {2: ['1|S|me\n'], 3: ['1|S|me\n']} )
        # new user can be added here by UserGraph on demand but not followers
        self.assertFalse(LoggingUser.followers_changed())
