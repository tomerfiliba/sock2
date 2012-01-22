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


class ConstContainer(object):
    def __init__(self, prefix):
        for name in dir(_socket):
            if name.startswith(prefix):
                setattr(self, name[len(prefix):].upper(), getattr(_socket, name))
    
    def __repr__(self):
        attrs = sorted("%s = %r" % (k, v) for k, v in self.__dict__.iteritems())
        return "<%s>" % ", ".join(attrs)


AddressFamily = ConstContainer("AF_")
IpProtocol = ConstContainer("IPPROTO_")
SocketType = ConstContainer("SOCK_")
OptionLevels = ConstContainer("SOL_")
SocketLevelOptions = ConstContainer("SO_")
IpLevelOptions = ConstContainer("IP_")
Ipv6LevelOptions = ConstContainer("IPV6_")
TcpLevelOptions = ConstContainer("TCP_")
IpAddresses = ConstContainer("INADDR_")
EthernetAddresses = ConstContainer("BDADDR_")
RecvFlags = ConstContainer("MSG_")
