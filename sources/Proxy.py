from enum import Enum

import zmq

from models.InternalMessage import InternalMessage
from models.TcpMessage import TcpMessage
from utils.NetworkConfiguration import NetworkConfiguration


class Commands(Enum):
    send = 1
    close = 2


##
## The Proxy is the gateway to the service,
## it basically handle the TCP sockets
##
## Every command are then dispatched through a PUSH/PULL with the Engine(s)
## easing the modification if we want to move the Engine as a microservice
##
class Controller():
    SECTION = "proxy"
    PORT = "port"
    PUSHER = "pusher"
    PULLER = "puller"

    def __init__(self, context):
        self.commands = {
            Commands.send.name: Controller.send,
            Commands.close.name: Controller.close
        }

        self.ip = []
        self.users = []

        network_configuration = NetworkConfiguration()
        self.router = network_configuration.raw_router(context, self.SECTION, self.PORT)
        self.pusher = network_configuration.pusher(context, self.SECTION, self.PUSHER)
        self.puller = network_configuration.puller(context, self.SECTION, self.PULLER)

    #########################
    # Private
    #########################

    def close(self, internal_message):
        self.router.send_multipart([bytes.fromhex(internal_message.get_identity()), b''])

    def send(self, internal_message):
        body = internal_message.get_arguments().encode()
        self.router.send_multipart([bytes.fromhex(internal_message.get_identity()), body])

    def receive_from_client(self, identity, message):
        try:
            string = message.decode("utf-8")
            tcp = TcpMessage(identity.hex(), body=string)
            self.pusher.send_json(tcp.to_json())
        except UnicodeDecodeError:
            return

    def receive_from_internal(self, json):
        internal = InternalMessage.from_json(json)
        if not internal.is_valid():
            return
        if internal.get_command() in self.commands.keys():
            self.commands[internal.get_command()](self, internal)

    #########################
    # Public
    #########################

    def run(self):
        poller = zmq.Poller()
        poller.register(self.router, zmq.POLLIN)
        poller.register(self.puller, zmq.POLLIN)

        while True:
            sockets = dict(poller.poll())

            if self.router in sockets and sockets[self.router] == zmq.POLLIN:
                identity, message = self.router.recv_multipart()
                self.receive_from_client(identity, message)
            if self.puller in sockets and sockets[self.puller] == zmq.POLLIN:
                json = self.puller.recv_json()
                self.receive_from_internal(json)


#########################
# Standalone option
#########################


def main():
    context = zmq.Context()
    controller = Controller(context)
    controller.run()


if __name__ == "__main__":
    main()
