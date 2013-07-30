#!/usr/bin/python
# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

import logging
import time

from followermaze.event import EventQueue
from followermaze.server import Server
from followermaze.usergraph import UserGraph
from followermaze.eventhandler import EventHandler

import followermaze_config as config


def run():

    # set up everything
    graph = UserGraph()
    queue = EventQueue()
    server = Server(event_port=config.event_port, client_port=config.client_port)
    handler = EventHandler(graph, server, queue)
    queue.set_handler(handler)
    server.set_listener(handler)
    logging.Logger.root.setLevel(config.log_level)

    # start polling thread
    server.start()

    # run until Ctrl-C pressed
    while True:
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            logging.warning('User-requested exit.')
            server.stop()
            break
        except:
            server.stop()
            raise

def main():
    try:
        run()
        return 0
    except:
        logging.error('Error occured; exit.')
        logging.exception('stack trace: ')
        return 1

# TODO: command-line for verbose and ports
if __name__ == '__main__':
    main()
