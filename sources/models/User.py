from models.AData import AData


##
## The User is a model to describe an user using our service
##
class User(AData):
    LOGIN = "login"
    ROOM = "room"

    def __init__(self, login = "", room = ""):
        self.login = login
        self.room = room

    #########################
    # AData
    #########################

    @classmethod
    def from_json(cls, json):
        return cls(json.get(cls.LOGIN, ""), json.get(cls.ROOM, ""))

    def to_json(self):
        return {self.LOGIN: self.login, self.ROOM: self.room}

    #########################
    # Public
    #########################

    def get_login(self):
        return self.login

    def get_room(self):
        return self.room

    def set_login(self, value):
        self.login = value

    def set_room(self, value):
        self.room = value