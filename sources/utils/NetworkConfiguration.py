import configparser
import os

import zmq


class NetworkConfiguration():
    NETWORK_FILE = "./resources/{0}".format(os.environ["network_file"])# "./resources/cluster.cfg"

    def __init__(self):
        self.network_config = configparser.ConfigParser()
        self.network_config.read(self.NETWORK_FILE)

    #########################
    # Private
    #########################

    def init_configuration(self, context, config_section, socket_type):
        configuration = self.network_config[config_section]
        socket = context.socket(socket_type)
        return configuration, socket

    @staticmethod
    def attach_socket(configuration, socket, port_name, ip_name = ""):
        if ip_name == "":
            socket.bind("tcp://*:{0}".format(configuration[port_name]))
        else:
            socket.connect("tcp://{0}:{1}".format(configuration[ip_name], configuration[port_name]))
        return socket

    def configure(self, context, config_section, socket_type, port_name, ip_name = ""):
        configuration, socket = self.init_configuration(context, config_section, socket_type)
        return NetworkConfiguration.attach_socket(configuration, socket, port_name, ip_name)

    #########################
    # Public
    #########################

    def pusher(self, context, config_section, port_name, ip_name = ""):
        return self.configure(context, config_section, zmq.PUSH, port_name, ip_name)

    def puller(self, context, config_section, port_name, ip_name = ""):
        return self.configure(context, config_section, zmq.PULL, port_name, ip_name)

    def publisher(self, context, config_section, port_name, ip_name = ""):
        return self.configure(context, config_section, zmq.PUB, port_name, ip_name)

    def subscriber(self, context, config_section, port_name, ip_name = ""):
        return self.configure(context, config_section, zmq.SUB, port_name, ip_name)

    def router(self, context, config_section, port_name):
        return self.configure(context, config_section, zmq.ROUTER, port_name)

    def raw_router(self, context, config_section, port_name):
        configuration, socket = self.init_configuration(context, config_section, zmq.ROUTER)
        socket.router_raw = True
        return self.attach_socket(configuration, socket, port_name)
