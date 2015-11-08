"""
Module to add streamparse-specific extensions to pystorm Spout class
"""

import pystorm

from .component import Component

class Spout(pystorm.spout.Spout, Component):
    """pystorm Spout with streamparse-specific additions"""
    pass
