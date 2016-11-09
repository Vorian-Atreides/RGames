import re

import zmq

from app import Chat
from app import Constants
from app import Proxy
from app import Rooms
from app import Users
from app.models.InternalMessage import InternalMessage
from app.models.TcpMessage import TcpMessage
from app.models.User import User
from app.utils import Serializer
from app.utils.NetworkConfiguration import NetworkConfiguration

UNKNOWN_COMMAND = "<= Unknown command: {0}, you should use /help\n"
HELP_MESSAGE = "<= Commands: /rooms, /join, /create, /leave, /quit, /help\n"

##
## The Engine is the backbone of the service,
## it dispatch the request coming from the Proxy to a PUSH/PULL for
## the Users, the Rooms and the Chat.
## The Engine also provide a PUB/SUB system, used for sharing the data
## between the workers, they can subscribe to a topic and gather only
## the required data.
##
## Once again, we use a PUSH/PULL system to ease the maintenance and move
## the Users and/or the Rooms as a microservice
##
## Chat is the only real microservice due to its lack of dependencies,
## the main limitation for the Users, the Rooms and the Engine for not
## being a full microservice is to keep the list of users and the list of rooms
## integrities.
##
## I must have only one instance of Rooms and Users to have a consistent
## list of users and rooms. Of course providing a DBMS would remove this
## limitation.
##
class Controller():
    SECTION = "engine"
    PROXY_SECTION = "proxy"
    PROXY_IP = "ip"
    PROXY_PUSHER = "pusher"
    PROXY_PULLER = "puller"
    XPUBLISHER = "xpublisher"
    SUBSCRIBER = "subscriber"
    USERS_PUSHER = "users_pusher"
    ROOMS_PUSHER = "rooms_pusher"
    CHAT_PUSHER = "chat_pusher"
    PULLER = "puller"

    def __init__(self, context):
        self.commands = {
            "^=> \/join (\w+)\n$": Controller.join_room,
            "^=> \/leave\n$": Controller.leave_room,
            "^=> \/quit\n$": Controller.quit,
            "^=> \/create (\w+)\n$": Controller.create_room,
            "^=> \/rooms\n$": Controller.list_rooms,
            "^$": Controller.brutaly_quit
        }
        self.configure = ("^=> (\w+)\n$", Controller.configure_user)
        self.broadcast = ("^=> (.+)\n$", Controller.chat_broadcast)

        self.users = {}

        network_configuration = NetworkConfiguration()
        self.proxy_pusher = network_configuration.pusher(context, self.PROXY_SECTION, self.PROXY_PULLER, self.PROXY_IP)
        self.proxy_puller = network_configuration.puller(context, self.PROXY_SECTION, self.PROXY_PUSHER, self.PROXY_IP)
        self.users_pusher = network_configuration.pusher(context, self.SECTION, self.USERS_PUSHER)
        self.rooms_pusher = network_configuration.pusher(context, self.SECTION, self.ROOMS_PUSHER)
        self.chat_pusher = network_configuration.pusher(context, self.SECTION, self.CHAT_PUSHER)
        self.puller = network_configuration.puller(context, self.SECTION, self.PULLER)
        self.xpub = network_configuration.publisher(context, self.SECTION, self.XPUBLISHER)
        self.sub = network_configuration.subscriber(context, self.SECTION, self.SUBSCRIBER)

        self.sub.setsockopt_string(zmq.SUBSCRIBE, Constants.InternalTopics.users.name)
        self.sub.setsockopt_string(zmq.SUBSCRIBE, Constants.InternalTopics.rooms.name)

    #########################
    # Private
    #########################

    def create_user(self, identity, arguments):
        print("Create user")
        message = InternalMessage(identity, Users.Commands.create.name)
        self.users_pusher.send_json(message.to_json())

    def configure_user(self, identity, arguments):
        print("Configure user")
        message = InternalMessage(identity, Users.Commands.configure.name, arguments[0])
        self.users_pusher.send_json(message.to_json())

    def join_room(self, identity, arguments):
        print("Join room")
        message = InternalMessage(identity, Users.Commands.join.name, arguments[0])
        self.users_pusher.send_json(message.to_json())

    def leave_room(self, identity, arguments):
        print("Leave room")
        message = InternalMessage(identity, Users.Commands.leave.name)
        self.users_pusher.send_json(message.to_json())

    def quit(self, identity, arguments):
        print("Quit")
        message = InternalMessage(identity, Users.Commands.quit.name)
        self.users_pusher.send_json(message.to_json())

    def brutaly_quit(self, identity, arguments):
        print("Brutaly quit")
        message = InternalMessage(identity, Users.Commands.hard_quit.name)
        self.users_pusher.send_json(message.to_json())

    def create_room(self, identity, arguments):
        print("Create room")
        message = InternalMessage(identity, Rooms.Commands.create.name, arguments[0])
        self.rooms_pusher.send_json(message.to_json())

    def list_rooms(self, identity, arguments):
        print("List rooms")
        message = InternalMessage(identity, Rooms.Commands.list.name)
        self.rooms_pusher.send_json(message.to_json())

    def chat_broadcast(self, identity, arguments):
        print("Broadcast")
        message = InternalMessage(identity, Chat.Commands.broadcast.name, arguments[0])
        self.chat_pusher.send_json(message.to_json())

    def from_client(self, json):
        # Check if the message is valid
        message = TcpMessage.from_json(json)
        if not message.is_valid():
            print("Invalid message")
            return
        print("Message: {0}".format(message.get_body()))
        # Check if it is an new user
        if message.get_identity() not in self.users.keys():
            self.create_user(message.get_identity(), "")
            return
        user = self.users[message.get_identity()]
        # Check if the user has a valid login
        if len(user.get_login()) == 0:
            result = re.search(self.configure[0], message.get_body())
            if result:
                self.configure[1](self, message.get_identity(), result.groups())
            return
        # Check the commands
        for command in self.commands.keys():
            result = re.search(command, message.get_body())
            if result:
                self.commands[command](self, message.get_identity(), result.groups())
                return
        # Check if the user is in a room and is chatting
        if user.get_room() != "":
            result = re.search(self.broadcast[0], message.get_body())
            if result:
                self.broadcast[1](self, message.get_identity(), result.groups())
                return
        # Send an error if the command isn't recognized
        internal = InternalMessage(message.get_identity(), Proxy.Commands.send.name, HELP_MESSAGE)
        self.proxy_pusher.send_json(internal.to_json())

    def from_broadcast(self, topic, message):
        print(topic)
        if topic.decode() == Constants.InternalTopics.users.name:
            self.users = Serializer.string_to_dict(User, message.decode())
        self.xpub.send_multipart([topic, message])

    #########################
    # Public
    #########################

    def run(self):
        poller = zmq.Poller()
        poller.register(self.proxy_puller, zmq.POLLIN)
        poller.register(self.sub, zmq.POLLIN)
        poller.register(self.puller, zmq.POLLIN)

        while True:
            sockets = dict(poller.poll())

            if self.proxy_puller in sockets and sockets[self.proxy_puller] == zmq.POLLIN:
                json = self.proxy_puller.recv_json()
                self.from_client(json)
            if self.puller in sockets and sockets[self.puller] == zmq.POLLIN:
                json = self.puller.recv_json()
                self.proxy_pusher.send_json(json)
            if self.sub in sockets and sockets[self.sub] == zmq.POLLIN:
                topic, message = self.sub.recv_multipart()
                self.from_broadcast(topic, message)

#########################
# Standalone option
#########################


def main():
    context = zmq.Context()
    controller = Controller(context)
    controller.run()

if __name__ == "__main__":
    main()
