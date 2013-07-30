# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

import heapq
import time


class Event(object):
    '''Event is a convenient interface for working with data that comes from event source.'''

    command_lengths = { 'F': 4, 'U': 4, 'B': 2, 'P': 4, 'S': 3 }

    def __init__(self, message, sequence_num, command, from_user=None, to_user=None):
        self.message = message
        self.sequence_num = int(sequence_num)
        self.code = command
        self.from_user = from_user
        self.to_user = to_user

    def __lt__(self, other):
        return self.sequence_num < other.sequence_num

    @classmethod
    def from_string(cls, message):
        '''Constructs Event from the message, or raises ValueError if the message is of incorrect format.'''

        def validate(tokens):
            # there should be at least 2 tokens
            if len(tokens) < 2:
                raise ValueError("invalid command; event: '%s'" % message)

            # 0th token should be a number
            int(tokens[0])

            # 1st token should be a valid command code: one of 'FUBPS'
            # number of tokens in command should be correct for the given command code
            length = Event.command_lengths.get(tokens[1])
            if not length:
                raise ValueError("invalid command code; event: '%s'" % message)
            if len(tokens) != length:
                raise ValueError("invalid command length; event: '%s'" % message)

            # 2nd and 3rd tokens should not be empty if they are present
            for token in [tokens[i] for i in range(2, length)]:
                if not token:
                    raise ValueError("empty value for user id; event: '%s'" % message)

        tokens = message.split('|')
        validate(tokens)
        
        return Event(message, *tokens)


class EventQueue(object):
    '''
    Receives events out-of-order and dispatches them in the correct order.
    Handles timeouts and maximum capacity of buffer of out-of-order events.
    Events order determined by their sequence numbers.
    '''

    def __init__(self, max_capacity=None, timeout_s=None):
        self.queue = []
        self.waiting_for = 1
        self.max_capacity = max_capacity
        self.timeout_s = timeout_s
        self.last_sent_timestamp_s = None

    def set_handler(self, handler):
        '''
        Sets handler that is notified when next (in the correct order) event is ready.
        handler should implement on_event() method that accepts Event object as its only argument.
        '''
        self.handler = handler


    def add(self, event):
        '''Adds event for processing.'''
        heapq.heappush(self.queue, event)


    def poll(self):
        '''
        Checks if an event that has been waited for arrived and if so, sends it and repeats.
        Also handles buffer capacity and timeouts.
        '''
        while self.queue:
            event = self.queue[0]
            # is it an event that has been waited for?
            if event.sequence_num == self.waiting_for:
                # yes: process it, notify handler and increase sequence number of next waited-for event
                heapq.heappop(self.queue)
                self.handler.on_event(event)
                self.waiting_for += 1
            # no, but cannot wait for it any longer
            elif self._capacity_exceeded() or self._timeout_occured():
                self.waiting_for = self.queue[0].sequence_num
            # no, update timestamp and exit
            else:
                self.last_sent_timestamp_s = time.time()
                break

    def _capacity_exceeded(self):
        return self.max_capacity and len(self.queue) > self.max_capacity

    def _timeout_occured(self):
        return self.timeout_s and self.last_sent_timestamp_s \
            and time.time() - self.last_sent_timestamp_s > self.timeout_s
