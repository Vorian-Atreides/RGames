import unittest

import zmq

from models.InternalMessage import InternalMessage
from models.User import User
import Chat
import Proxy


class TestChat(unittest.TestCase):
    def setUp(self):
        context = zmq.Context()
        self.controller = Chat.Controller(context)

    def test_internal_broadcast_with_valid_user(self):
        users = {
            "a": User("user1", "room1"),
            "b": User("user2", "room1"),
            "c": User("user3")
        }
        request = InternalMessage("a", "command", "Hello")
        responses = self.controller.internal_broadcast(request, users)
        expected_responses = [
            InternalMessage("a", Proxy.Commands.send.name, Chat.Text.TO_SEND.format("user1", "Hello")),
            InternalMessage("b", Proxy.Commands.send.name, Chat.Text.TO_SEND.format("user1", "Hello"))
        ]
        self.assertEqual(len(responses), len(expected_responses))
        for i in range(0, len(responses)):
            self.assertEqual(responses[i].get_identity(), expected_responses[i].get_identity())
            self.assertEqual(responses[i].get_command(), expected_responses[i].get_command())
            self.assertEqual(responses[i].get_arguments(), expected_responses[i].get_arguments())

    def test_internal_broadcast_with_invalid_user(self):
        users = {
            "a": User("user1", "room1"),
            "b": User("user2", "room1"),
            "c": User("user3")
        }
        request = InternalMessage("c", "command", "Hello")
        responses = self.controller.internal_broadcast(request, users)
        expected_responses = [
        ]
        self.assertEqual(len(responses), len(expected_responses))