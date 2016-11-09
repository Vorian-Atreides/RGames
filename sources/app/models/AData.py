import abc


class AData():
    @abc.abstractmethod
    def from_json(cls, json):
        raise NotImplementedError()

    @abc.abstractmethod
    def to_json(self):
        raise NotImplementedError()