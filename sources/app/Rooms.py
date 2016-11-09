from enum import Enum

import zmq

from app import Constants
from app import Proxy
from app.AWorker import AWorker
from app.models.InternalMessage import InternalMessage
from app.models.Room import Room
from app.models.User import User
from app.utils import Serializer

ACTIVE_ROOMS = "<= Active rooms are:\n"
END_LIST = "<= end of list.\n"
ROOM = "<= * {0} ({1})\n"
CREATED = "<= Room: {0} created\n"
ERROR_ROOM_EXIST = "<= Room: {0} already exist\n"


class Commands(Enum):
    create = 1
    list = 2


##
## The Rooms is a Worker handling every request related to the rooms.
##
class Controller(AWorker):
    PUSHER = "rooms_pusher"
    USERS = "users"

    def __init__(self, context):
        super(Controller, self).__init__(context)

        self.commands = {
            Commands.create.name: Controller.create_room,
            Commands.list.name: Controller.get_rooms
        }

        self.users = {}
        self.rooms = []

        self.sub.setsockopt_string(zmq.SUBSCRIBE, Constants.InternalTopics.users.name)


    #########################
    # Private
    #########################

    def share_rooms(self):
        string = Serializer.array_to_string(self.rooms)
        self.pub.send_multipart([Constants.InternalTopics.rooms.name.encode(), string.encode()])

    def update_connected_users(self):
        # Clean the connected users
        for room in self.rooms:
            room.set_connected_users(0)
        # Update the connected users
        for key in self.users.keys():
            user = self.users[key]
            rooms = [item for item in self.rooms if item.get_name() == user.get_room()]
            if len(rooms) == 1:
                rooms[0].set_connected_users(rooms[0].get_connected_users() + 1)

    @staticmethod
    def build_list_rooms(rooms):
        room_messages = [ROOM.format(room.get_name(), room.get_connected_users()) for room in rooms]
        messages = [
            ACTIVE_ROOMS,
            ''.join(sorted(room_messages)),
            END_LIST
        ]

        return ''.join(messages)

    @staticmethod
    def internal_get_rooms(internal_message, rooms):
        message = Controller.build_list_rooms(rooms)
        return InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, message)

    @staticmethod
    def internal_create_room(internal_message, rooms):
        name = internal_message.get_arguments()
        others = [room for room in rooms if room.get_name() == name]
        if len(others) > 0:
            return False, InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name,
                                   ERROR_ROOM_EXIST.format(name))
        return True, InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, CREATED.format(name))

    #########################
    # Commands
    #########################

    def get_rooms(self, internal_message):
        internal = self.internal_get_rooms(internal_message, self.rooms)
        self.pusher.send_json(internal.to_json())

    def create_room(self, internal_message):
        succeed, message = self.internal_create_room(internal_message, self.rooms)
        self.pusher.send_json(message.to_json())
        if not succeed:
            return
        self.rooms.append(Room(internal_message.get_arguments()))
        # Broadcast the change
        self.share_rooms()

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
        # Execute the command
        if internal_message.get_command() in self.commands:
            self.commands[internal_message.get_command()](self, internal_message)

    def from_broadcast(self, topic, message):
        if topic == Constants.InternalTopics.users.name:
            self.users = Serializer.string_to_dict(User, message)
            self.update_connected_users()

#########################
# Standalone option
#########################


def main():
    context = zmq.Context()
    controller = Controller(context)
    controller.run()

if __name__ == "__main__":
    main()