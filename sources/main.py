from threading import Thread

import zmq

import Chat
import Engine
import Proxy
import Users
import Rooms


def run_chat(context):
    controller = Chat.Controller(context)
    controller.run()


def run_rooms(context):
    controller = Rooms.Controller(context)
    controller.run()


def run_users(context):
    controller = Users.Controller(context)
    controller.run()


def run_engine(context):
    engine = Engine.Controller(context)
    engine.run()


def run_children(context, chat_pool):
    children = [
        Thread(target=run_engine, args=[context]),
        Thread(target=run_users, args=[context]),
        Thread(target=run_rooms, args=[context])
    ]

    for i in range(0, chat_pool):
        child = Thread(target=run_chat, args=[context])
        children.append(child)
    for child in children:
        child.start()


def main():
    context = zmq.Context()
    run_children(context, 3)
    controller = Proxy.Controller(context)
    controller.run()


if __name__ == "__main__":
    main()