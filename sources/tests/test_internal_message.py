import unittest

from app.models.InternalMessage import InternalMessage


class TestInternalMessage(unittest.TestCase):
    def test_is_valid_succeed(self):
        message = InternalMessage("identity", "command")
        self.assertTrue(message.is_valid())
        message = InternalMessage("identity", "command", "arguments")
        self.assertTrue(message.is_valid())

    def test_is_valid_failed(self):
        message = InternalMessage("identity", "")
        self.assertFalse(message.is_valid())
        message = InternalMessage("", "command")
        self.assertFalse(message.is_valid())
        message = InternalMessage("", "")
        self.assertFalse(message.is_valid())

    def test_from_valid_json(self):
        json = {"identity": "a", "command": "b", "arguments": "c"}
        message = InternalMessage.from_json(json)
        self.assertEqual(message.get_identity(), "a")
        self.assertEqual(message.get_command(), "b")
        self.assertEqual(message.get_arguments(), "c")

        json = {"identity": "a", "command": "b"}
        message = InternalMessage.from_json(json)
        self.assertEqual(message.get_identity(), "a")
        self.assertEqual(message.get_command(), "b")
        self.assertEqual(message.get_arguments(), "")

    def test_from_invalid_json(self):
        json = {"identity": "a"}
        message = InternalMessage.from_json(json)
        self.assertEqual(message.get_identity(), "a")
        self.assertEqual(message.get_command(), "")
        self.assertEqual(message.get_arguments(), "")

        json = {"command": "b"}
        message = InternalMessage.from_json(json)
        self.assertEqual(message.get_identity(), "")
        self.assertEqual(message.get_command(), "b")
        self.assertEqual(message.get_arguments(), "")

        json = {"arguments": "c"}
        message = InternalMessage.from_json(json)
        self.assertEqual(message.get_identity(), "")
        self.assertEqual(message.get_command(), "")
        self.assertEqual(message.get_arguments(), "c")

        json = {"random": "a", "key": "b", "value": "c"}
        message = InternalMessage.from_json(json)
        self.assertEqual(message.get_identity(), "")
        self.assertEqual(message.get_command(), "")
        self.assertEqual(message.get_arguments(), "")
