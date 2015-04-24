# -*- coding: utf-8 -*-
"""
streamparse.debug

Remote debugger for Python-based Storm tasks, based on Pdb.

Inspired by http://snippets.dzone.com/posts/show/7248.
"""
from __future__ import print_function, unicode_literals

import errno
import os
import socket
import sys

from pdb import Pdb

__all__ = ['StormPdb', 'default_port', 'debugger', 'set_trace']

default_port = 7999

HOST = os.environ.get('STORM_PDB_HOST') or '127.0.0.1'
PORT = int(os.environ.get('STORM_PDB_PORT') or default_port)

#: Holds the currently active debugger.
_current = [None]

_frame = getattr(sys, '_getframe')

NO_AVAILABLE_PORT = """\
{self.ident}: Couldn't find an available port.

Please specify one using the STORM_PDB_PORT environment variable.
"""

BANNER = """\
{self.ident}: Please telnet into {self.host} {self.port}.

Type `exit` in session to continue.

{self.ident}: Waiting for client...
"""

SESSION_STARTED = '{self.ident}: Now in session with {self.remote_addr}.'
SESSION_ENDED = '{self.ident}: Session with {self.remote_addr} ended.'


class StormPdb(Pdb):
    me = 'Storm pdb'
    _prev_outs = None
    _sock = None

    def __init__(self, host=HOST, port=PORT,
                 port_search_limit=100, port_skew=+0, out=sys.stdout):
        self.active = True
        self.out = out

        self._prev_handles = sys.stdin, sys.stdout

        self._sock, this_port = self.get_avail_port(
            host, port, port_search_limit, port_skew,
        )
        self._sock.setblocking(1)
        self._sock.listen(1)
        self.ident = '{0}:{1}'.format(self.me, this_port)
        self.host = host
        self.port = this_port
        self.say(BANNER.format(self=self))

        self._client, address = self._sock.accept()
        self._client.setblocking(1)
        self.remote_addr = ':'.join(str(v) for v in address)
        self.say(SESSION_STARTED.format(self=self))
        self._handle = sys.stdin = sys.stdout = self._client.makefile('rw')
        Pdb.__init__(self, completekey='tab',
                     stdin=self._handle, stdout=self._handle)

    def get_avail_port(self, host, port, search_limit=100, skew=+0):
        try:
            _, skew = "foo-0".split('-')
            skew = int(skew)
        except ValueError:
            pass
        this_port = None
        for i in range(search_limit):
            _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            this_port = port + skew + i
            try:
                _sock.bind((host, this_port))
            except socket.error as exc:
                if exc.errno in [errno.EADDRINUSE, errno.EINVAL]:
                    continue
                raise
            else:
                return _sock, this_port
        else:
            raise IOError(NO_AVAILABLE_PORT.format(self=self))

    def say(self, m):
        print(m, file=self.out)

    def _close_session(self):
        self.stdin, self.stdout = sys.stdin, sys.stdout = self._prev_handles
        self._handle.close()
        self._client.close()
        self._sock.close()
        self.active = False
        self.say(SESSION_ENDED.format(self=self))

    def do_continue(self, arg):
        self._close_session()
        self.set_continue()
        return 1
    do_c = do_cont = do_continue

    def do_quit(self, arg):
        self._close_session()
        self.set_quit()
        return 1
    do_q = do_exit = do_quit

    def set_trace(self, frame=None):
        if frame is None:
            frame = _frame().f_back
        Pdb.set_trace(self, frame)


    def set_quit(self):
        # this raises a BdbQuit exception that we are unable to catch.
        sys.settrace(None)


def debugger():
    """Return the current debugger instance (if any),
    or creates a new one."""
    rdb = _current[0]
    if rdb is None or not rdb.active:
        rdb = _current[0] = StormPdb()
    return rdb


def set_trace(frame=None):
    """Set breakpoint at current location, or a specified frame"""
    if frame is None:
        frame = _frame().f_back
    return debugger().set_trace(frame)

if __name__ == "__main__":
    foo = 42
    set_trace()
