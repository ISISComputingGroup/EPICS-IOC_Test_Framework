import socket


def get_free_ports(n):
    """
    Returns n free port numbers on the current machine.

    :param n: the number of ports required
    :return:  a tuple containing n free port numbers
    """
    socks = list()
    ports = list()
    for i in range(0, n):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        s.bind(("", 0))
        ports.append(s.getsockname()[1])
        socks.append(s)
    for s in socks:
        s.close()
    return tuple(ports)


def get_free_ports_from_list(n, port_low, port_high):
    """
    Return n free ports by testing specified range

    :param n: the number of ports required
    :param port_low: the minimum of the ports range
    :param port_high: the maximum of the port range
    :return: a tuple containing n free port numbers
    """
    socks = list()
    ports = list()
    for i in range(0, n):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        for j in range(port_low, port_high):
            try:
                s.bind(("", j))
                ports.append(s.getsockname()[1])
                socks.append(s)
                break
            except:
                pass
    for s in socks:
        s.close()
    return tuple(ports)
