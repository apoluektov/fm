# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

import unittest

from followermaze.event import Event, EventQueue

class FakeHandler(object):
    def __init__(self):
        self.messages = []

    def on_event(self, event):
        self.messages.append(event.message)


class TestEventQueue(unittest.TestCase):
    def shouldReceive(self, msgs):
        self.assertEqual(self.handler.messages, msgs)

    def setUp(self):
        self.handler = FakeHandler()
        self.timeout_s = 0.05
        self.queue = EventQueue(max_capacity=3, timeout_s=self.timeout_s)
        self.queue.set_handler(self.handler)


    def test_inorder(self):
        self.queue.poll()
        self.shouldReceive([])

        self.queue.add(Event.from_string('1|B'))
        self.queue.poll()
        self.shouldReceive(['1|B'])

        self.queue.add(Event.from_string('2|S|3'))
        self.queue.poll()
        self.shouldReceive(['1|B', '2|S|3'])

        self.queue.add(Event.from_string('3|U|1|2'))
        self.queue.poll()
        self.shouldReceive(['1|B', '2|S|3', '3|U|1|2'])


    def test_outoforder1(self):
        self.queue.add(Event.from_string('2|S|3'))
        self.queue.poll()
        self.shouldReceive([])

        self.queue.add(Event.from_string('3|U|1|2'))
        self.queue.poll()
        self.shouldReceive([])

        self.queue.add(Event.from_string('1|B'))
        self.queue.poll()
        self.shouldReceive(['1|B', '2|S|3', '3|U|1|2'])


    def test_outoforder2(self):
        self.queue.add(Event.from_string('2|S|3'))
        self.queue.poll()
        self.shouldReceive([])

        self.queue.add(Event.from_string('1|B'))
        self.queue.poll()
        self.shouldReceive(['1|B', '2|S|3'])

        self.queue.add(Event.from_string('4|P|42|123'))
        self.queue.poll()
        self.shouldReceive(['1|B', '2|S|3'])

        self.queue.add(Event.from_string('3|U|1|2'))
        self.queue.poll()
        self.shouldReceive(['1|B', '2|S|3', '3|U|1|2', '4|P|42|123'])


    def test_calling_process_doesnt_change_order(self):
        self.queue.add(Event.from_string('2|S|3'))
        self.queue.add(Event.from_string('1|B'))
        self.queue.add(Event.from_string('4|P|42|123'))
        self.queue.add(Event.from_string('3|U|1|2'))
        self.queue.poll()
        self.shouldReceive(['1|B', '2|S|3', '3|U|1|2', '4|P|42|123'])


    def test_capacity_exceeded(self):
        self.queue.add(Event.from_string('2|S|3'))
        self.queue.add(Event.from_string('4|P|42|123'))
        self.queue.add(Event.from_string('3|U|1|2'))
        self.queue.add(Event.from_string('5|B'))
        self.queue.poll()
        self.shouldReceive(['2|S|3', '3|U|1|2', '4|P|42|123', '5|B'])


    def test_timeout_occured(self):
        import time
        self.queue.add(Event.from_string('2|S|3'))
        self.queue.add(Event.from_string('4|P|42|123'))
        self.queue.add(Event.from_string('3|U|1|2'))
        self.queue.poll()
        self.shouldReceive([])

        time.sleep(self.timeout_s)
        self.queue.poll()
        self.shouldReceive(['2|S|3', '3|U|1|2', '4|P|42|123'])
