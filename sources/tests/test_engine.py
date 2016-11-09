import re
import unittest

import zmq

from app.Engine import Controller


class TestEngine(unittest.TestCase):
    def setUp(self):
        context = zmq.Context()
        self.controller = Controller(context)

    #########################
    # Private
    #########################

    def routing_succeed(self, commands, expected_function, groups=[]):
        for i in range(0, len(commands)):
            enter = False
            for (regex, function) in self.controller.commands.items():
                result = re.search(regex, commands[i])
                if result:
                    enter = True
                    if len(groups) > 0:
                        self.assertEqual(result.group(1), groups[i])
                    self.assertEqual(function, expected_function)
            self.assertTrue(enter, "Didn't match any case")

    def routing_failed(self, commands, unexpected_function):
        for command in commands:
            for (regex, function) in self.controller.commands.items():
                result = re.search(regex, command)
                if result:
                    self.assertNotEqual(function, unexpected_function, "Failed with: |{0}|".format(command))

    #########################
    # Tests
    #########################

    # Check /join
    def test_routing_join_succeed(self):
        rooms = ["room1", "test", "bugfix", "python"]
        commands = ["=> /join {0}\n".format(room) for room in rooms]
        self.routing_succeed(commands, Controller.join_room, rooms)

    def test_routing_join_failed(self):
        commands = [
            "=>  /join room\n", "=> join  room\n", "=>/join room\n",
            "=> join room\n", "=> /join\n", "/join room\n", "join room\n",
            "random string\n", "=> /create room\n"
        ]
        self.routing_failed(commands, Controller.join_room)

    # Check /leave
    def test_routing_leave_succeed(self):
        self.routing_succeed(["=> /leave\n"], Controller.leave_room)

    def test_routing_leave_failed(self):
        commands = [
            "=>  /leave\n", "=> leave\n", "=>/leave\n",
            "/leave\n", "leave\n", "=>\n", "=> leave test\n",
            "=> /leave"
        ]
        self.routing_failed(commands, Controller.leave_room)

    # Check /quit
    def test_routing_quit_succeed(self):
        self.routing_succeed(["=> /quit\n"], Controller.quit)

    def test_routing_quit_failed(self):
        commands = [
            "=>  /quit\n", "=> quit\n", "=>/quit\n",
            "/quit\n", "quit\n", "=>\n", "=> quit test\n",
            "=> /quit"
        ]
        self.routing_failed(commands, Controller.quit)

    # Check brutaly_quit
    def test_routing_brutaly_quit_succeed(self):
        self.routing_succeed([""], Controller.brutaly_quit)

    def test_routing_brutaly_quit_failed(self):
        commands = [
            # "\n",
            "random\n", " \n", "=>\n"
        ]
        self.routing_failed(commands, Controller.brutaly_quit)

    # Check /create room
    def test_routing_create_room_succeed(self):
        rooms = ["room1", "test", "bugfix", "python"]
        commands = ["=> /create {0}\n".format(room) for room in rooms]
        self.routing_succeed(commands, Controller.create_room, rooms)

    def test_routing_create_room_failed(self):
        commands = [
            "=>  /create room\n", "=> create  room\n", "=>/create room\n",
            "=> create room\n", "=> /create\n", "/create room\n", "create room\n",
            "random string\n", "=> /join room\n"
        ]
        self.routing_failed(commands, Controller.create_room)

    # Check /rooms
    def test_routing_rooms_succeed(self):
        self.routing_succeed(["=> /rooms\n"], Controller.list_rooms)

    def test_routing_rooms_failed(self):
        commands = [
            "=>  /rooms\n", "=> rooms\n", "=>/rooms\n",
            "/rooms\n", "rooms\n", "=>\n", "=> rooms test\n",
            "=> /rooms"
        ]
        self.routing_failed(commands, Controller.list_rooms)

    # Check broadcast
    def test_routing_broadcast_succeed(self):
        commands = [
            "=> Hello\n", "=> Hello world\n"
        ]
        for command in commands:
            result = re.search(self.controller.broadcast[0],command)
            self.assertIsNotNone(result)

    def test_routing_broadcast_failed(self):
        commands = [
            "\n", "=> \n", "=>\n"
        ]
        self.routing_failed(commands, Controller.chat_broadcast)

    # Check configure
    def test_routing_configure_succeed(self):
        commands = [
            "=> login\n", "=> randomLogin\n"
        ]
        for command in commands:
            result = re.search(self.controller.configure[0], command)
            self.assertIsNotNone(result)

    def test_routing_configure_failed(self):
        commands = [
            "\n", "=> \n", "=>\n",
            "=> ___\n", "=>  a\n", "=> a \n"
        ]
        self.routing_failed(commands, Controller.configure_user)