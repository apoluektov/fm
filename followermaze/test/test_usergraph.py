# Copyright 2013 Alexander Poluektov
# This file is a part of my solution for 'follower-maze' challenge by SoundCloud

import unittest

from followermaze.usergraph import UserGraph


class TestUserGraph(unittest.TestCase):
    def assertListOfUsersEqual(self, users1, users2):
        self.assertEqual(set(users1), set(users2))

    def users(self, *args):
        return [self.graph.user(a) for a in args]

    def register_some_users(self):
        user_ids = ['me', 'you', 'they', 'nobody']
        for i,u in enumerate(user_ids):
            self.graph.register_user(u, key=i)
        return user_ids

    def setUp(self):
        self.graph = UserGraph()


    def test_register_user_works(self):
        self.assertListOfUsersEqual(self.graph.all_users(), [])
        some_users = self.register_some_users()
        self.assertListOfUsersEqual(self.graph.all_users(), self.users(*some_users))


    def test_twice_register_user_preserves_followers(self):
        self.graph.register_user('me')
        self.graph.register_user('you')
        self.graph.user('me').add_follower('you')
        self.graph.register_user('me')

        self.assertEqual(self.graph.followers_of('me'), self.users('you'))


    def test_twice_registering_doesnt_add_new_users(self):
        self.graph.register_user('me')
        self.graph.register_user('you')
        self.graph.user('me').add_follower('you')
        self.graph.register_user('me')

        self.assertListOfUsersEqual(self.graph.all_users(), self.users('me', 'you'))


    def test_follow_works(self):
        self.register_some_users()

        self.assertListOfUsersEqual(self.graph.followers_of('me'), [])
        self.assertListOfUsersEqual(self.graph.followers_of('you'), [])
        self.assertListOfUsersEqual(self.graph.followers_of('they'), [])

        self.graph.user('me').add_follower('you')
        self.graph.user('me').add_follower('they')
        self.graph.user('you').add_follower('nobody')

        self.assertListOfUsersEqual(self.graph.followers_of('me'), self.users('you', 'they'))
        self.assertListOfUsersEqual(self.graph.followers_of('you'), self.users('nobody'))
        self.assertListOfUsersEqual(self.graph.followers_of('they'), [])


    def test_unfollow_works(self):
        some_users = self.register_some_users()
        self.graph.user('me').add_follower('you')
        self.graph.user('me').add_follower('they')
        self.graph.user('you').add_follower('nobody')
        self.graph.user('me').remove_follower('they')

        self.assertListOfUsersEqual(self.graph.followers_of('me'), self.users('you'))
        self.assertListOfUsersEqual(self.graph.followers_of('you'), self.users('nobody'))
        self.assertListOfUsersEqual(self.graph.all_users(), self.users(*some_users))


    def test_unfollow_of_nonfollower_does_nothing(self):
        some_users = self.register_some_users()
        self.graph.user('me').remove_follower('you')

        self.assertListOfUsersEqual(self.graph.followers_of('me'), [])
        self.assertListOfUsersEqual(self.graph.all_users(), self.users(*some_users))


    def test_follow_same_user_twice_does_nothing(self):
        some_users = self.register_some_users()
        self.graph.user('me').add_follower('you')
        self.graph.user('me').add_follower('you')

        self.assertListOfUsersEqual(self.graph.followers_of('me'), self.users('you'))
        self.assertListOfUsersEqual(self.graph.all_users(), self.users(*some_users))
