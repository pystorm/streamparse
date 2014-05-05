"""Base primititve classes for working with Storm."""
import traceback

from ipc import send_message


class Component(object):
    """Base class for Spouts and Bolts which contains class methods for
    logging messages back to the Storm worker process."""

    def raise_exception(self, exception):
        """Report an exception back to Storm.

        :param exception: a Python exception.
        """
        self.log('Python exception raised: {}\n{}'
                 .format(exception.__class__.__name__,
                         traceback.format_exc(exception)))
        send_message({'command': 'sync'})  # sync up right away

    def log(self, message, level='info'):
        """Log a message to Storm optionally providing a logging level.

        :param message: any object that supports ``__str__()``.
        :param level: a ``str`` representing the log level.
        """
        send_message({'command': 'log', 'msg': str(message), 'level': level})


class Tuple(object):
    """Storm's primitive data type passed around via streams."""

    __slots__ = ['id', 'component', 'stream', 'task', 'values']

    def __init__(self, id, component, stream, task, values):
        self.id = id
        self.component = component
        self.stream = stream
        self.task = task
        self.values = values

    def __repr__(self):
        return '<{}: {}> {}'.format(self.__class__.__name__, self.id,
                                    self.values)
