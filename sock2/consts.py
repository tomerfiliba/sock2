"""
Consts:
a module containing all sorts of constants of the original socket module,
in case you need to use a not-commonly-used socket.
Note that the constants are laid in hierarchies, to make them easier to
work with.
these consts are platform dependent and are generated from the _socket
module when this module is loaded.
"""
import _socket


class _ConstContainer(object):
    def __init__(self, prefix):
        for name in dir(_socket):
            if name.startswith(prefix):
                setattr(self, name[len(prefix):].upper(), getattr(_socket, name))

    def __repr__(self):
        attrs = sorted("%s = %r" % (k, v) for k, v in self.__dict__.iteritems())
        return "<%s>" % ", ".join(attrs)


AddressFamily = _ConstContainer("AF_")
IpProtocol = _ConstContainer("IPPROTO_")
SocketType = _ConstContainer("SOCK_")
OptionLevels = _ConstContainer("SOL_")
SocketLevelOptions = _ConstContainer("SO_")
IpLevelOptions = _ConstContainer("IP_")
Ipv6LevelOptions = _ConstContainer("IPV6_")
TcpLevelOptions = _ConstContainer("TCP_")
IpAddresses = _ConstContainer("INADDR_")
EthernetAddresses = _ConstContainer("BDADDR_")
RecvFlags = _ConstContainer("MSG_")
