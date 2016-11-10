import unittest

import zmq

from models.InternalMessage import InternalMessage
from models.Room import Room
import Rooms
import Proxy


class TestRooms(unittest.TestCase):
    def setUp(self):
        context = zmq.Context()
        self.controller = Rooms.Controller(context)

    def test_build_list_rooms(self):
        rooms = [Room("a", 10), Room("b", 2), Room("c", 1)]
        list = self.controller.build_list_rooms(rooms)
        expected_text = Rooms.ACTIVE_ROOMS + \
                        Rooms.ROOM.format("a", 10) + Rooms.ROOM.format("b", 2) + Rooms.ROOM.format("c", 1) + \
                        Rooms.END_LIST
        self.assertEqual(list, expected_text)

        rooms = []
        list = self.controller.build_list_rooms(rooms)
        expected_text = Rooms.ACTIVE_ROOMS + \
                        Rooms.END_LIST
        self.assertEqual(list, expected_text)

    def test_internal_get_rooms(self):
        request = InternalMessage("a", "command")
        rooms = [Room("a", 10), Room("b", 2), Room("c", 1)]
        expected_text = Rooms.ACTIVE_ROOMS + \
                        Rooms.ROOM.format("a", 10) + Rooms.ROOM.format("b", 2) + Rooms.ROOM.format("c", 1) + \
                        Rooms.END_LIST
        response = self.controller.internal_get_rooms(request, rooms)
        self.assertEqual(response.get_identity(), "a")
        self.assertEqual(response.get_command(), Proxy.Commands.send.name)
        self.assertEqual(response.get_arguments(), expected_text)

        request = InternalMessage("b", "command")
        rooms = []
        expected_text = Rooms.ACTIVE_ROOMS + \
                        Rooms.END_LIST
        response = self.controller.internal_get_rooms(request, rooms)
        self.assertEqual(response.get_identity(), "b")
        self.assertEqual(response.get_command(), Proxy.Commands.send.name)
        self.assertEqual(response.get_arguments(), expected_text)

    def test_internal_create_room_succeed(self):
        request = InternalMessage("a", "command", "d")
        rooms = [Room("a", 10), Room("b", 2), Room("c", 1)]
        succeed, response = self.controller.internal_create_room(request, rooms)
        self.assertEqual(succeed, True)
        self.assertEqual(response.get_identity(), "a")
        self.assertEqual(response.get_command(), Proxy.Commands.send.name)
        self.assertEqual(response.get_arguments(), Rooms.CREATED.format("d"))

    def test_internal_created_room_failed(self):
        request = InternalMessage("b", "command", "a")
        rooms = [Room("a", 10), Room("b", 2), Room("c", 1)]
        succeed, response = self.controller.internal_create_room(request, rooms)
        self.assertEqual(succeed, False)
        self.assertEqual(response.get_identity(), "b")
        self.assertEqual(response.get_command(), Proxy.Commands.send.name)
        self.assertEqual(response.get_arguments(), Rooms.ERROR_ROOM_EXIST.format("a"))
