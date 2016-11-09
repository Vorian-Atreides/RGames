from app.models.AMessage import AMessage


class TcpMessage(AMessage):
    BODY = "body"

    def __init__(self, identity, body):
        super(TcpMessage, self).__init__()
        self.identity = identity
        self.body = body

    @classmethod
    def from_json(cls, json):
        return cls(json.get(cls.IDENTITY, ""), json.get(cls.BODY, ""))

    #########################
    # Public
    #########################

    def get_identity(self):
        return self.identity

    def get_body(self):
        return self.body

    #########################
    # AMessage
    #########################

    def to_json(self):
        return {self.IDENTITY: self.identity, self.BODY: self.body}

    def is_valid(self):
        return len(self.identity) > 0
