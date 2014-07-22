"""Base primititve classes for working with Storm."""
from __future__ import absolute_import, print_function, unicode_literals

from traceback import format_exc

from .ipc import send_message


class Component(object):
    """Base class for Spouts and Bolts which contains class methods for
    logging messages back to the Storm worker process."""

    def raise_exception(self, exception, tup=None):
        """Report an exception back to Storm via logging.

        :param exception: a Python exception.
        :param tup: a :class:`Tuple` object.
        """
        if tup:
            message = ('Python {exception_name} raised while processing tuple '
                       '{tup!r}\n{traceback}')
        else:
            message = 'Python {exception_name} raised\n{traceback}'
        message = message.format(exception_name=exception.__class__.__name__,
                                 tup=tup,
                                 traceback=format_exc())
        self.log(message)
        send_message({'command': 'sync'})  # sync up right away

    def log(self, message, level='info'):
        """Log a message to Storm optionally providing a logging level.

        :param message: the log message to send to Storm.
        :type message: str
        :param level: the logging level that Storm should use when writing the
                      ``message``.
        :type level: str
        """
        send_message({'command': 'log', 'msg': str(message), 'level': level})
