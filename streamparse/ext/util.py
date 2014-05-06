from __future__ import absolute_import
import json
import os
import sys

from fabric.colors import red


def die(msg, error_code=1):
    print("{}: {}".format(red("error"), msg))
    sys.exit(error_code)


def get_config():
    if not os.path.exists("config.json"):
        die("No config.json found. You must run this command inside a"
            "streamparse project directory.")

    with open("config.json") as fp:
        config = json.load(fp)
    return config
