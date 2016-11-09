from enum import Enum

import zmq

from app import Constants
from app import Proxy
from app.AWorker import AWorker
from app.models.InternalMessage import InternalMessage
from app.models.User import User
from app.utils import Serializer

TO_SEND = "<= {0}: {1}\n"


class Commands(Enum):
    broadcast = 1


##
## Chat is a Worker handling every request related to the communication
## inside of a room.
##
class Controller(AWorker):
    PUSHER = "chat_pusher"
    USERS = "users"

    def __init__(self, context):
        super(Controller, self).__init__(context)

        self.commands = {
            Commands.broadcast.name: Controller.broadcast
        }

        self.users = {}
        self.rooms = []

        self.sub.setsockopt_string(zmq.SUBSCRIBE, Constants.InternalTopics.users.name)


    #########################
    # Private
    #########################

    @staticmethod
    def internal_broadcast(internal_message, users):
        messages = []
        user = users[internal_message.get_identity()]
        if user.get_room() == "":
            return messages
        # Get the users in the same room
        room_users = sorted([key for (key, value) in users.items() if value.get_room() == user.get_room()])
        # Send the messages
        to_send = TO_SEND.format(user.get_login(), internal_message.get_arguments())
        for identity in room_users:
            message = InternalMessage(identity, Proxy.Commands.send.name, to_send)
            messages.append(message)
        return messages


    #########################
    # Command
    #########################

    def broadcast(self, internal_message):
        messages = self.internal_broadcast(internal_message, self.users)
        for message in messages:
            self.pusher.send_json(message.to_json())


    #########################
    # AWorker
    #########################

    def get_pusher(self):
        return self.PUSHER

    def get_topics(self):
        return [self.USERS]

    def from_client(self, internal_message):
        if not internal_message.is_valid():
            return
        if internal_message.get_command() in self.commands.keys():
            self.commands[internal_message.get_command()](self, internal_message)

    def from_broadcast(self, topic, message):
        if topic == Constants.InternalTopics.users.name:
            self.users = Serializer.string_to_dict(User, message)

#########################
# Standalone option
#########################


def main():
    context = zmq.Context()
    controller = Controller(context)
    controller.run()

if __name__ == "__main__":
    main()