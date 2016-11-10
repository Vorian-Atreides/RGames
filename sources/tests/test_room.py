import unittest

from models.Room import Room


class TestUser(unittest.TestCase):
    def test_from_valid_json(self):
        json = {"name": "a", "connected_users": 10}
        message = Room.from_json(json)
        self.assertEqual(message.get_name(), "a")
        self.assertEqual(message.get_connected_users(), 10)

        json = {"name": "a"}
        message = Room.from_json(json)
        self.assertEqual(message.get_name(), "a")
        self.assertEqual(message.get_connected_users(), 0)

    def test_from_invalid_json(self):
        json = {"a": "a", "b": "b"}
        message = Room.from_json(json)
        self.assertEqual(message.get_name(), "")
        self.assertEqual(message.get_connected_users(), 0)

    def test_to_json(self):
        room = Room("name", 10)
        self.assertEqual({"name":"name", "connected_users":10}, room.to_json())

        room = Room("name")
        self.assertEqual({"name":"name", "connected_users":0}, room.to_json())

        room = Room("", 10)
        self.assertEqual({"name": "", "connected_users": 10}, room.to_json())

        room = Room()
        self.assertEqual({"name":"", "connected_users":0}, room.to_json())
