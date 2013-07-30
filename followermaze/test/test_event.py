# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

import unittest

from followermaze.event import Event

class TestEvent(unittest.TestCase):
    def shouldFail(self, msg):
        with self.assertRaises(ValueError):
            Event.from_string(msg)

    def shouldBeEqual(self, e1, e2):
        for k,v in vars(e1).items():
            self.assertEqual(v, vars(e2)[k])

    def test_invalid_inputs_fail(self):
        self.shouldFail('')
        self.shouldFail(' \n')
        self.shouldFail('abrakadabra')
        self.shouldFail('1|abrakadabra')
        self.shouldFail('1|B ')
        self.shouldFail('2|B|')
        self.shouldFail('|3|B')
        self.shouldFail('4||B')
        self.shouldFail('5|B|1')
        self.shouldFail('S|B')
        self.shouldFail('7|b')
        self.shouldFail('8|Be')
        self.shouldFail('9|F||')
        self.shouldFail('10|F|1|2|3')
        self.shouldFail('11|S|9|10')

    def test_correct_inputs(self):
        self.shouldBeEqual(Event.from_string('1|F|12|21'), Event('1|F|12|21', 1, 'F', '12', '21',))
        self.shouldBeEqual(Event.from_string('23|U|1|10'), Event('23|U|1|10', 23, 'U', '1', '10'))
        self.shouldBeEqual(Event.from_string('2|B'), Event('2|B', 2, 'B'))
        self.shouldBeEqual(Event.from_string('34|P|0|1'), Event('34|P|0|1', 34, 'P', '0', '1'))
        self.shouldBeEqual(Event.from_string('5|S|9'), Event('5|S|9', 5, 'S', '9'))
        
    def test_some_event_properties(self):
        # sequence number could be int or str
        self.shouldBeEqual(Event('dummy', '1', 'B'), Event('dummy', 1, 'B'))

        # from- and to- defaults to None
        self.shouldBeEqual(Event('dummy', 1, 'F'), Event('dummy', 1, 'F', None, None))
