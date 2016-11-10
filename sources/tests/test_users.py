import unittest

import zmq

from models.InternalMessage import InternalMessage
from models.User import User
from models.Room import Room
import Proxy
import Users


class TestUsers(unittest.TestCase):
    def setUp(self):
        context = zmq.Context()
        self.controller = Users.Controller(context)

    # Check the socket registration
    def test_internal_create(self):
        request = InternalMessage("a", "command")
        response = self.controller.internal_create(request)
        self.assertEqual(response.get_identity(), "a")
        self.assertEqual(response.get_arguments(), Users.WELCOME)

        request = InternalMessage("b", "command")
        response = self.controller.internal_create(request)
        self.assertEqual(response.get_identity(), "b")
        self.assertEqual(response.get_arguments(), Users.WELCOME)

    # Check the user configuration
    def test_internal_configure_succeed(self):
        users = {
            "a": User("user1"), "b": User("user2"),
            "c": User()
        }
        request = InternalMessage("c", "command", "user3")
        succeed, response = self.controller.internal_configure(request, users)
        self.assertTrue(succeed)
        self.assertEqual(response.get_identity(), "c")
        self.assertEqual(response.get_command(), Proxy.Commands.send.name)
        self.assertEqual(response.get_arguments(), Users.WELCOME_LOGGED.format("user3"))

    def test_internal_configure_failed(self):
        users = {
            "a": User("user1"), "b": User("user2"),
            "c": User()
        }
        request = InternalMessage("c", "command", "user1")
        succeed, response = self.controller.internal_configure(request, users)
        self.assertFalse(succeed)
        self.assertEqual(response.get_identity(), "c")
        self.assertEqual(response.get_command(), Proxy.Commands.send.name)
        self.assertEqual(response.get_arguments(), Users.LOGIN_ALREADY_USED)

    # Check /join
    def test_internal_join_succeed(self):
        users = {
            "a": User("user1", "room1"), "b": User("user2", "room1"),
            "c": User("user3")
        }
        rooms = [
            Room("room1"), Room("room2")
        ]
        request = InternalMessage("c", "command", "room1")
        succeed, messages = self.controller.internal_join(request, users, rooms)
        message = Users.ENTERING_ROOM.format("room1") + \
                  Users.USER.format("user1") + Users.USER.format("user2") + Users.Y_USER.format("user3") + \
                  Users.END_LIST

        expected_responses = [
            InternalMessage("a", Proxy.Commands.send.name, Users.JOINED.format("room1", "user3")),
            InternalMessage("b", Proxy.Commands.send.name, Users.JOINED.format("room1", "user3")),
            InternalMessage("c", Proxy.Commands.send.name, message)
        ]
        self.assertTrue(succeed)
        self.assertEqual(len(messages), len(expected_responses))
        for i in range(0, len(messages)):
            self.assertEqual(messages[i].get_identity(), expected_responses[i].get_identity())
            self.assertEqual(messages[i].get_command(), expected_responses[i].get_command())
            self.assertEqual(messages[i].get_arguments(), expected_responses[i].get_arguments())

    def test_internal_join_failed(self):
        users = {
            "a": User("user1", "room1"), "b": User("user2", "room1"),
            "c": User("user3")
        }
        rooms = [
            Room("room1"), Room("room2")
        ]
        request = InternalMessage("c", "command", "room3")
        succeed, messages = self.controller.internal_join(request, users, rooms)
        self.assertFalse(succeed)
        self.assertEqual(messages[0].get_identity(), "c")
        self.assertEqual(messages[0].get_command(), Proxy.Commands.send.name)
        self.assertEqual(messages[0].get_arguments(), Users.ROOM_NOT_FOUND.format("room3"))

    # Check /leave
    def test_internal_leave_succeed(self):
        users = {
            "a": User("user1", "room1"), "b": User("user2", "room1"),
            "c": User("user3")
        }
        request = InternalMessage("a", "command")
        succeed, messages = self.controller.internal_leave(request, users)
        expected_responses = [
            InternalMessage("b", Proxy.Commands.send.name, Users.LEAVING_ROOM.format("room1", "user1")),
            InternalMessage("a", Proxy.Commands.send.name, Users.Y_LEAVING_ROOM.format("room1", "user1"))
        ]
        self.assertTrue(succeed)
        self.assertEqual(len(messages), len(expected_responses))
        for i in range(0, len(messages)):
            self.assertEqual(messages[i].get_identity(), expected_responses[i].get_identity())
            self.assertEqual(messages[i].get_command(), expected_responses[i].get_command())
            self.assertEqual(messages[i].get_arguments(), expected_responses[i].get_arguments())

    def test_internal_leave_failed(self):
        users = {
            "a": User("user1", "room1"), "b": User("user2", "room1"),
            "c": User("user3")
        }
        request = InternalMessage("c", "command")
        succeed, messages = self.controller.internal_leave(request, users)
        self.assertFalse(succeed)
        self.assertEqual(messages[0].get_identity(), "c")
        self.assertEqual(messages[0].get_command(), Proxy.Commands.send.name)
        self.assertEqual(messages[0].get_arguments(), Users.ROOM_NOT_JOINED)

    # Check /quit
    def test_quit_without_room(self):
        users = {
            "a": User("user1", "room1"), "b": User("user2", "room1"),
            "c": User("user3")
        }
        request = InternalMessage("c", "command")
        responses = self.controller.internal_quit(request, users)
        expected_responses = [
            InternalMessage("c", Proxy.Commands.send.name, Users.QUIT),
            InternalMessage("c", Proxy.Commands.close.name)
        ]
        self.assertEqual(len(responses), len(expected_responses))
        for i in range(0, len(responses)):
            self.assertEqual(responses[i].get_identity(), expected_responses[i].get_identity())
            self.assertEqual(responses[i].get_command(), expected_responses[i].get_command())
            self.assertEqual(responses[i].get_arguments(), expected_responses[i].get_arguments())

    def test_quit_with_room(self):
        users = {
            "a": User("user1", "room1"), "b": User("user2", "room1"),
            "c": User("user3")
        }
        request = InternalMessage("a", "command")
        responses = self.controller.internal_quit(request, users)
        expected_responses = [
            InternalMessage("b", Proxy.Commands.send.name, Users.LEAVING_ROOM.format("room1", "user1")),
            InternalMessage("a", Proxy.Commands.send.name, Users.Y_LEAVING_ROOM.format("room1", "user1")),
            InternalMessage("a", Proxy.Commands.send.name, Users.QUIT),
            InternalMessage("a", Proxy.Commands.close.name)
        ]
        self.assertEqual(len(responses), len(expected_responses))
        for i in range(0, len(responses)):
            self.assertEqual(responses[i].get_identity(), expected_responses[i].get_identity())
            self.assertEqual(responses[i].get_command(), expected_responses[i].get_command())
            self.assertEqual(responses[i].get_arguments(), expected_responses[i].get_arguments())