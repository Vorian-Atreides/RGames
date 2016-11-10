from models.AMessage import AMessage


class InternalMessage(AMessage):
    COMMAND = "command"
    ARGUMENTS = "arguments"

    def __init__(self, identity, command, arguments=""):
        super(InternalMessage, self).__init__()
        self.identity = identity
        self.command = command
        self.arguments = arguments

    @classmethod
    def from_json(cls, json):
        return cls(json.get(cls.IDENTITY, ""), json.get(cls.COMMAND, ""), json.get(cls.ARGUMENTS, ""))

    #########################
    # Public
    #########################

    def get_identity(self):
        return self.identity

    def get_command(self):
        return self.command

    def get_arguments(self):
        return self.arguments

    #########################
    # AMessage
    #########################

    def to_json(self):
        return {self.IDENTITY: self.identity, self.COMMAND: self.command, self.ARGUMENTS: self.arguments}

    def is_valid(self):
        return len(self.identity) > 0 and len(self.command) > 0
