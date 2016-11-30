# encoding: utf-8
from __future__ import print_function

import socket
import os

def name_of_submitting_host():
    """Returns name of ssh clients host, usually this will be euler-portal.ethz.ch
    or eulertest-portal.ethz.ch for the imsb worfklows."""
    ssh_connection = os.environ.get("SSH_CONNECTION", "")
    ssh_connection_ip = ssh_connection.split(" ")[0]
    try:
        return socket.gethostbyaddr(ssh_connection_ip)[0]
    except socket.error:
        return None


if __name__ == "__main__":
    print(name_of_submitting_host())
