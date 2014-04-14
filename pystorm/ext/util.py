import json


def get_config():
    config = json.load(open("config.json"))
    return config
