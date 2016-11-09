from enum import Enum

import zmq

from app import Constants
from app import Proxy
from app.AWorker import AWorker
from app.models.InternalMessage import InternalMessage
from app.models.Room import Room
from app.models.User import User
from app.utils import Serializer

WELCOME = "<= Welcome to the XYZ chat server\n" \
          "<= Login Name ?\n"
LOGIN_ALREADY_USED = "<= Sorry, name taken.\n"
WELCOME_LOGGED = "<= Welcome {0}!\n"
ENTERING_ROOM = "<= entering room: {0}\n"
JOINED = "<= * new user joined {0}: {1}\n"
LEAVING_ROOM = "<= * user has left {0}: {1}\n"
Y_LEAVING_ROOM = "<= * user has left {0}: {1} (** this is you)\n"
END_LIST = "<= end of list.\n"
USER = "<= * {0}\n"
Y_USER = "<= * {0} (** this is you)\n"
QUIT = "<= BYE\n"


class Commands(Enum):
    create = 1
    configure = 2
    join = 3
    leave = 4
    quit = 5
    hard_quit = 6


##
## The Users is a Worker handling every requests related to the users
## it store the official list of users, modify it, broadcast it.
##
## The command: /leave is considered in Users' scope
##
class Controller(AWorker):
    PUSHER = "users_pusher"
    ROOMS = "rooms"

    def __init__(self, context):
        super(Controller, self).__init__(context)

        self.commands = {
            Commands.create.name: Controller.create,
            Commands.configure.name: Controller.configure,
            Commands.join.name: Controller.join,
            Commands.leave.name: Controller.leave,
            Commands.quit.name: Controller.quit,
            Commands.hard_quit.name: Controller.hard_quit
        }

        self.users = {}
        self.rooms = []
        self.sub.setsockopt_string(zmq.SUBSCRIBE, Constants.InternalTopics.rooms.name)

    #########################
    # Private
    #########################

    def share_users(self):
        string = Serializer.dict_to_string(self.users)
        self.pub.send_multipart([Constants.InternalTopics.users.name.encode(), string.encode()])

    @staticmethod
    def build_entering_message(room, others, user):
        user_messages = [USER.format(value.get_login()) for (key, value) in others]
        user_messages.append(Y_USER.format(user.get_login()))

        messages = [
            ENTERING_ROOM.format(room),
            ''.join(sorted(user_messages)),
            END_LIST
        ]
        return ''.join(messages)

    #########################
    # Commands
    #########################

    def create(self, internal_message):
        self.users[internal_message.get_identity()] = User()
        internal = InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, WELCOME)
        self.pusher.send_json(internal.to_json())

    def configure(self, internal_message):
        name = internal_message.get_arguments()
        user = self.users[internal_message.get_identity()]
        if name == "":
            print("Invalid name")
            return
        # Compare if the name is taken
        others = [key for (key, value) in self.users.items() if value.get_login() == name]
        message = LOGIN_ALREADY_USED
        if len(others) == 0:
            message = WELCOME_LOGGED.format(name)
            user.set_login(name)
        internal = InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, message)
        self.pusher.send_json(internal.to_json())

    def join(self, internal_message):
        # Check if the room exist
        user = self.users[internal_message.get_identity()]
        room = internal_message.get_arguments()
        if len([item for item in self.rooms if item.get_name() == room]) == 0:
            print("Room not found")
            return
        # Notify the users in the room
        message = JOINED.format(room, user.get_login())
        others = [(key, value) for (key, value) in self.users.items() if value.get_room() == room]
        for (key, value) in others:
            internal = InternalMessage(key, Proxy.Commands.send.name, message)
            self.pusher.send_json(internal.to_json())
        # Send a confirmation message
        message = Controller.build_entering_message(room, others, user)
        internal = InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, message)
        self.pusher.send_json(internal.to_json())
        # Add the user to the room
        user.set_room(room)

    def leave(self, internal_message):
        user = self.users[internal_message.get_identity()]
        if user.get_room() == "":
            print("User doesn't belong to any room")
            return
        # Notify the users in the room
        message = LEAVING_ROOM.format(user.get_room(), user.get_login())
        others = [(key, value) for (key, value) in self.users.items() if value.get_room() == user.get_room() and
                  key != internal_message.get_identity()]
        for (key, value) in others:
            internal = InternalMessage(key, Proxy.Commands.send.name, message)
            self.pusher.send_json(internal.to_json())
        # Send a confirmation message
        message = Y_LEAVING_ROOM.format(user.get_room(), user.get_login())
        internal = InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, message)
        self.pusher.send_json(internal.to_json())
        # Remove the user from the room
        user.set_room("")

    def quit(self, internal_message):
        # Leave the room if the user belong to one
        self.leave(internal_message)
        # Update the list of users
        self.users.pop(internal_message.get_identity())
        # Say goodbye
        quit = InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, QUIT)
        self.pusher.send_json(quit.to_json())
        # Close the socket
        close = InternalMessage(internal_message.get_identity(), Proxy.Commands.close.name)
        self.pusher.send_json(close.to_json())

    def hard_quit(self, internal_message):
        # Clean the users
        self.leave(internal_message)

    #########################
    # AWorker
    #########################

    def get_pusher(self):
        return self.PUSHER

    def get_topics(self):
        return [self.ROOMS]

    def from_client(self, internal_message):
        if not internal_message.is_valid():
            return
        # Execute the command
        if internal_message.get_command() in self.commands:
            self.commands[internal_message.get_command()](self, internal_message)
        # Share the modified list of users
        self.share_users()

    def from_broadcast(self, topic, message):
        if topic == Constants.InternalTopics.rooms.name:
            self.rooms = Serializer.string_to_array(Room, message)

#########################
# Standalone option
#########################


def main():
    context = zmq.Context()
    controller = Controller(context)
    controller.run()

if __name__ == "__main__":
    main()