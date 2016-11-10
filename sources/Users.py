from enum import Enum

import zmq

from models.InternalMessage import InternalMessage
from models.Room import Room
from models.User import User
from utils import Serializer
from AWorker import AWorker
import Constants
import Proxy

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
ROOM_NOT_FOUND = "<= The room: {0} doesn't exist\n"
ROOM_NOT_JOINED = "<= You haven't joined any room.\n"


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

    @staticmethod
    def internal_create(internal_message):
        return InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, WELCOME)

    @staticmethod
    def internal_configure(internal_message, users):
        name = internal_message.get_arguments()
        # Compare if the name is taken
        others = [key for (key, value) in users.items() if value.get_login() == name]
        succeed = len(others) == 0
        message = WELCOME_LOGGED.format(name) if succeed else LOGIN_ALREADY_USED
        return succeed, InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, message)

    @staticmethod
    def internal_join(internal_message, users, rooms):
        # Check if the room exist
        user = users[internal_message.get_identity()]
        room = internal_message.get_arguments()
        if len([item for item in rooms if item.get_name() == room]) == 0:
            err = InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, ROOM_NOT_FOUND.format(room))
            return False, [err]
        # Notify the users in the room
        message = JOINED.format(room, user.get_login())
        others = [(key, value) for (key, value) in users.items() if value.get_room() == room]
        messages = [InternalMessage(key, Proxy.Commands.send.name, message) for (key, value) in others]
        # Notify the user
        message = Controller.build_entering_message(room, others, user)
        messages.append(InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, message))
        return True, sorted(messages, key=lambda message: message.get_identity())

    @staticmethod
    def internal_leave(internal_message, users):
        user = users[internal_message.get_identity()]
        if user.get_room() == "":
            err = InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, ROOM_NOT_JOINED)
            return False, [err]
        # Notify the users in the room
        message = LEAVING_ROOM.format(user.get_room(), user.get_login())
        messages = [InternalMessage(key, Proxy.Commands.send.name, message) for (key, value) in users.items()
                    if value.get_room() == user.get_room() and key != internal_message.get_identity()]
        message = Y_LEAVING_ROOM.format(user.get_room(), user.get_login())
        messages.append(InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, message))
        return True, messages

    @staticmethod
    def internal_quit(internal_message, users):
        quit_messages = [
            InternalMessage(internal_message.get_identity(), Proxy.Commands.send.name, QUIT),
            InternalMessage(internal_message.get_identity(), Proxy.Commands.close.name)
        ]

        succeed, messages = Controller.internal_leave(internal_message, users)
        if not succeed:
            messages = []
        messages.extend(quit_messages)
        return messages

    #########################
    # Commands
    #########################

    def create(self, internal_message):
        internal = self.internal_create(internal_message)
        self.users[internal_message.get_identity()] = User()
        self.pusher.send_json(internal.to_json())

    def configure(self, internal_message):
        succeed, internal = self.internal_configure(internal_message, self.users)
        if succeed:
            user = self.users[internal_message.get_identity()]
            user.set_login(internal_message.get_arguments())
        self.pusher.send_json(internal.to_json())

    def join(self, internal_message):
        succeed, messages = self.internal_join(internal_message, self.users, self.rooms)
        if not succeed:
            self.pusher.send_json(messages[0].to_json())
            return
        for message in messages:
            self.pusher.send_json(message.to_json())
        # Update the user
        user = self.users[internal_message.get_identity()]
        user.set_room(internal_message.get_arguments())

    def leave(self, internal_message):
        succeed, messages = self.internal_leave(internal_message, self.users)
        if not succeed:
            self.pusher.send_json(messages[0].to_json())
            return
        for message in messages:
            self.pusher.send_json(message.to_json())
        # Update the user
        user = self.users[internal_message.get_identity()]
        user.set_room("")

    def quit(self, internal_message):
        # Leave the room if the user belongs to one
        messages = self.internal_quit(internal_message, self.users)
        for message in messages:
            self.pusher.send_json(message.to_json())
        # Update the user
        self.users.pop(internal_message.get_identity())

    def hard_quit(self, internal_message):
        # Leave the room if the user joined one
        succeed, messages = self.internal_leave(internal_message, self.users)
        if not succeed:
            messages = []
        # Notify the user from the room if the user joined one
        for message in messages:
            self.pusher.send_json(message.to_json())
        self.users.pop(internal_message.get_identity())

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