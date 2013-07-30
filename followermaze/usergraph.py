# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

from collections import defaultdict

class UserGraph(object):
    '''Manages user graph where directed edges are follower-to-followee relationsheep.'''

    class User(object):
        def __init__(self):
            self.followers = set()

        def add_follower(self, follower):
            self.followers.add(follower)

        def remove_follower(self, follower):
            self.followers.discard(follower)

    def __init__(self, user_factory=None):
        if not user_factory:
            user_factory = self.User
        self.users = defaultdict(user_factory)

    def register_user(self, user_id, **kwargs):
        '''
        Register user in the graph.
        kwargs is arbitrary arguments that be convenient to store in user object (i.e. connection info).
        Re-registering user with same userid does not affect their followers but overwrite kwargs.
        '''
        user = self.users[user_id]
        for k,v in kwargs.items():
            setattr(user, k, v)
        return user

    def user(self, user_id):
        return self.users[user_id]

    def followers_of(self, user_id):
        return [self.user(user_id) for user_id in self.users[user_id].followers]

    def all_users(self):
        return self.users.values()
