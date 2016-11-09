import abc

import zmq

from app.models.InternalMessage import InternalMessage
from app.utils.NetworkConfiguration import NetworkConfiguration

##
## The Worker is an abstract class used to define and configure the routing
## with the Engine
##
## It provide 2 abstract method needed for the routing and give
## 2 callbacks, which must be implemented to handle the data.
##
class AWorker():
    SECTION = "engine"
    ENGINE_IP = "ip"
    PULLER = "puller"
    PUBLISHER = "xpublisher"
    SUBSCRIBER = "subscriber"

    def __init__(self, context):
        network_configuration = NetworkConfiguration()
        self.pusher = network_configuration.pusher(context, self.SECTION, self.PULLER, self.ENGINE_IP)
        self.puller = network_configuration.puller(context, self.SECTION, self.get_pusher(), self.ENGINE_IP)
        self.pub = network_configuration.publisher(context, self.SECTION, self.SUBSCRIBER, self.ENGINE_IP)
        self.sub = network_configuration.subscriber(context, self.SECTION, self.PUBLISHER, self.ENGINE_IP)

    #########################
    # Public
    #########################

    def run(self):
        poller = zmq.Poller()
        poller.register(self.puller, zmq.POLLIN)
        poller.register(self.sub, zmq.POLLIN)

        while True:
            sockets = dict(poller.poll())

            if self.puller in sockets and sockets[self.puller] == zmq.POLLIN:
                json = self.puller.recv_json()
                internal = InternalMessage.from_json(json)
                self.from_client(internal)
            if self.sub in sockets and sockets[self.sub] == zmq.POLLIN:
                topic, message = self.sub.recv_multipart()
                self.from_broadcast(topic.decode(), message.decode())

    @abc.abstractmethod
    def get_pusher(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_topics(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def from_client(self, internal_message):
        raise NotImplementedError()

    @abc.abstractmethod
    def from_broadcast(self, topic, message):
        raise NotImplementedError()