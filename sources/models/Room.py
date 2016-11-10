from models.AData import AData


##
## The Rooms is a model to describe a room in our service
##
class Room(AData):
    NAME = "name"
    CONNECTED_USERS = "connected_users"

    def __init__(self, name="", connect_users=0):
        self.name = name
        self.connected_users = connect_users

    #########################
    # AData
    #########################

    @classmethod
    def from_json(cls, json):
        return cls(json.get(cls.NAME, ""), json.get(cls.CONNECTED_USERS, 0))

    def to_json(self):
        return {self.NAME: self.name, self.CONNECTED_USERS: self.connected_users}

    #########################
    # Public
    #########################`

    def get_name(self):
        return self.name

    def get_connected_users(self):
        return self.connected_users

    def set_name(self, value):
        self.name = value

    def set_connected_users(self, value):
        self.connected_users = value
