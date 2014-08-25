"""Base primititve classes for working with Storm."""
from __future__ import absolute_import, print_function, unicode_literals

from traceback import format_exc

from .ipc import send_message

# Support for Storm Log levels as per STORM-414
_STORM_LOG_TRACE = 0
_STORM_LOG_DEBUG = 1
_STORM_LOG_INFO = 2
_STORM_LOG_WARN = 3
_STORM_LOG_ERROR = 4
_STORM_LOG_LEVELS = {
    'trace': _STORM_LOG_TRACE,
    'debug': _STORM_LOG_DEBUG,
    'info': _STORM_LOG_INFO,
    'warn': _STORM_LOG_WARN,
    'error': _STORM_LOG_ERROR,
}


class Component(object):
    """Base class for Spouts and Bolts which contains class methods for
    logging messages back to the Storm worker process."""

    def _setup_component(self, storm_conf, context):
        """Add helpful instance variables to component after initial handshake
        with Storm.
        """
        self._topology_name = storm_conf.get('topology.name', '')
        self._task_id = context.get('taskid', '')
        self._component_name = context.get('task->component', {})\
                                      .get(str(self._task_id), '')
        self._debug = storm_conf.get("topology.debug", False)
        self._storm_conf = storm_conf
        self._context = context

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
        self.log(message, 'error')
        send_message({'command': 'sync'})  # sync up right away

    def log(self, message, level=None):
        """Log a message to Storm optionally providing a logging level.

        :param message: the log message to send to Storm.
        :type message: str
        :param level: the logging level that Storm should use when writing the
                      ``message``. Can be one of: trace, debug, info, warn, or
                      error (default: ``info``).
        :type level: str
        """
        level = _STORM_LOG_LEVELS.get(level, _STORM_LOG_INFO)
        send_message({'command': 'log', 'msg': str(message), 'level': level})
