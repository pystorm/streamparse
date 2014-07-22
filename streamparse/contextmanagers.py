from __future__ import print_function, unicode_literals

import subprocess
import time
from contextlib import contextmanager
from socket import error as SocketError

from six.moves.socketserver import UDPServer, TCPServer


def _port_in_use(port, server_type="tcp"):
    """Check to see whether a given port is already in use on localhost."""
    if server_type == "tcp":
        server = TCPServer
    elif server_type == "udp":
        server = UDPServer
    else:
        raise ValueError("Server type can only be: udp or tcp.")

    try:
        server(("localhost", port), None)
    except SocketError:
        return True

    return False


@contextmanager
def ssh_tunnel(user, host, local_port, remote_port):
    if _port_in_use(local_port):
        raise Exception("Local port: {} already in use, unable to open ssh "
                        "tunnel to {}:{}."
                        .format(local_port, host, remote_port))

    ssh_cmd = ["ssh",
               "{user}@{host}".format(user=user, host=host),
               "-NL",
               "{local}:localhost:{remote}".format(local=local_port,
                                                   remote=remote_port)]
    ssh_proc = subprocess.Popen(ssh_cmd, shell=False)
    # Validate that the tunnel is actually running before yielding
    while not _port_in_use(local_port):
        # Periodically check to see if the ssh command failed and returned a
        # value, then raise an Exception
        if ssh_proc.poll() is not None:
            raise Exception('Unable to open ssh tunnel via: "{}"'
                            .format(" ".join(ssh_cmd)))
        time.sleep(0.2)
    try:
        yield
    finally:
        ssh_proc.terminate()
