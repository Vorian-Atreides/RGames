import abc


class AMessage():
    IDENTITY = "identity"

    @abc.abstractmethod
    def from_json(cls, json):
        raise NotImplementedError()

    @abc.abstractmethod
    def is_valid(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def to_json(self):
        raise NotImplementedError()
