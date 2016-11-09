import json


def string_to_dict(cls, message):
    tmp = {}
    dict = json.loads(message)
    for key in dict.keys():
        tmp[key] = cls.from_json(dict[key])
    return tmp


def string_to_array(cls, message):
    tmp = []
    array = json.loads(message)
    for item in array:
        tmp.append(cls.from_json(item))
    return tmp


def dict_to_string(items):
    dict = {}
    for key in items.keys():
        dict[key] = items[key].to_json()
    return json.dumps(dict)


def array_to_string(items):
    array = []
    for item in items:
        array.append(item.to_json())
    return json.dumps(array)