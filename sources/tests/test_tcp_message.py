import unittest

from app.models.TcpMessage import TcpMessage


class TestTcpMessage(unittest.TestCase):
    def test_is_valid_succeed(self):
        message = TcpMessage("identity", "body")
        self.assertTrue(message.is_valid())
        message = TcpMessage("identity", "")
        self.assertTrue(message.is_valid())

    def test_is_valid_failed(self):
        message = TcpMessage("", "")
        self.assertFalse(message.is_valid())

    def test_from_valid_json(self):
        json = {"identity": "a", "body": "b"}
        message = TcpMessage.from_json(json)
        self.assertEqual(message.get_identity(), "a")
        self.assertEqual(message.get_body(), "b")

        json = {"identity": "a"}
        message = TcpMessage.from_json(json)
        self.assertEqual(message.get_identity(), "a")
        self.assertEqual(message.get_body(), "")

    def test_from_invalid_json(self):
        json = {"random": "a"}
        message = TcpMessage.from_json(json)
        self.assertEqual(message.get_identity(), "")
        self.assertEqual(message.get_body(), "")