import unittest

from app.models.User import User


class TestUser(unittest.TestCase):
    def test_from_valid_json(self):
        json = {"login": "a", "room": "b"}
        message = User.from_json(json)
        self.assertEqual(message.get_login(), "a")
        self.assertEqual(message.get_room(), "b")

        json = {"login": "a"}
        message = User.from_json(json)
        self.assertEqual(message.get_login(), "a")
        self.assertEqual(message.get_room(), "")

    def test_from_invalid_json(self):
        json = {"a": "a", "b": "b"}
        message = User.from_json(json)
        self.assertEqual(message.get_login(), "")
        self.assertEqual(message.get_room(), "")

    def test_to_json(self):
        user = User("login", "room")
        self.assertEqual({"login":"login", "room":"room"}, user.to_json())

        user = User("login", "")
        self.assertEqual({"login":"login", "room":""}, user.to_json())

        user = User("", "room")
        self.assertEqual({"login": "", "room": "room"}, user.to_json())

        user = User()
        self.assertEqual({"login":"", "room":""}, user.to_json())
