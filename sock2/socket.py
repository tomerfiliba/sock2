import _socket
import consts
from errors import (TimeoutError, SocketClosed, AcceptError, BindError, 
    ConnectError, NotBoundError, NotConnectedError, AlreadyBoundError, 
    AlreadyConnectedError, timeout_errnos)
from options import SocketLevelOptions, IpLevelMixin, TcpLevelMixin


__all__ = [
    "Socket", 
    "ConnectedSocket", "ListenerSocket", "DatagramSocket", "RawSocket",
    "TcpConnectedSocket", "TcpListenerSocket",  "UdpSocket",
]


#
# a closed socket
# 
class closed_socket(object):
    def __getattribute__(self, name):
        raise SocketClosed()
closed_socket = closed_socket()


#
# the base socket
#
class Socket(SocketLevelOptions):
    """base socket"""
    __slots__ = ["_sock", "_is_bound"]
    
    def __init__(self, familty, type, protocol):
        self._sock = _socket.socket(familty, type, protocol)
        self._is_bound = False
    
    def __del__(self):
        self.close()
    
    def __repr__(self):
        if self.closed:
            return "<%s(closed)>" % (self.__class__.__name__,)
        else:
            return "<%s(fd = %d)>" % (self.__class__.__name__, self.fileno())
    
    @classmethod
    def wrap(cls, **kw):
        """creates a socket wrapper around a real socket"""
        obj = object.__new__(cls)
        for k, v in kw.iteritems():
            setattr(obj, k, v)
        return obj
    
    def close(self):
        """closes the socket"""
        if not self.closed:
            self._sock.close()
            self._sock = closed_socket
    
    def fileno(self):
        return self._sock.fileno()
    
    def _get_closed(self):
        return self._sock is closed_socket
    closed = property(_get_closed, doc = 
        "indicates whether or not this socket is closed")
    
    def _get_blocking(self):
        return self._sock.gettimeout() == None
    def _set_blocking(self, value):
        self._sock.setblocking(bool(value))
    blocking = property(_get_blocking, _set_blocking, doc = 
        "gets or sets the socket's blocking mode (bool)")
    
    def _get_timeout(self):
        return self._sock.gettimeout()
    def _set_timeout(self, value):
        self._sock.settimeout(value)
    timeout = property(_get_timeout, _set_timeout, doc = 
        "the timeout for operations, in seconds (float). "
        "None means infinite timeout (blocking)")
    
    def shutdown(self, mode = "rw"):
        """shuts down the socket, for reading, writing or both. mode must be
        one of ('r', 'w', 'rw')"""
        if   mode == "r":
            self._sock.shutdown(_socket.SHUT_RD)
        elif mode == "w":
            self._sock.shutdown(_socket.SHUT_WR)
        elif mode == "rw":
            self._sock.shutdown(_socket.SHUT_RDWR)
        else:
            raise ValueError("mode can be 'r', 'w', or 'rw'")
    
    def bind(self, local_endpoint):
        """binds the socket to the given local endpoint"""
        if self._is_bound:
            raise AlreadyBoundError()
        try:
            self._sock.bind(local_endpoint)
        except _socket.timeout:
            raise TimeoutError()
        except _socket.error, (errno, info):
            if errno in timeout_errnos:
                raise TimeoutError()
            else:
                raise BindError(errno, info)
        self._is_bound = True
    
    def _get_sockname(self):
        if not self._is_bound:
            raise NotBoundError()
        return self._sock.getsockname()
    local_endpoint = property(_get_sockname, doc = 
        "the socket's local endpoint")


#
# connection-oriented (stream) sockets
#
class ListenerSocket(Socket):
    """represents server sockets (binds to local address, can accept)"""
    __slots__ = ["_backlog"]
    
    def __init__(self, familty, type, protocol, local_endpoint = None, backlog = 4):
        Socket.__init__(self, familty, type, protocol)
        self._backlog = backlog
        if local_endpoint is not None:
            self.bind(local_endpoint)
    
    def _get_backlog(self):
        return self._backlog
    def _set_backlog(self, value):
        if not self._is_bound:
            raise NotBoundError()
        self._sock.listen(value)
        self._backlog = value
    backlog = property(_get_backlog, _set_backlog, doc = 
        "gets or sets the socket's listen-backlog (int)")
    
    def bind(self, local_endpoint):
        """binds the socket and listens"""
        Socket.bind(self, local_endpoint)
        self._sock.listen(self.backlog)
    
    def accept(self):
        """accepts a connection -- returns a real-socket that should 
        be wrap()ped by a subclass of ClientSocket"""
        if not self._is_bound:
            raise NotBoundError()
        try:
            newsock, addrinfo = self._sock.accept()
        except _socket.timeout:
            raise TimeoutError()
        except _socket.error, (errno, info):
            if errno in timeout_errnos:
                raise TimeoutError()
            else:
                raise AcceptError(errno, info)
        return newsock


class ConnectedSocket(Socket):
    """
    represents client sockets (connected to server). 
    this is the type sockets that NetworkStream works over.
    """
    __slots__ = ["_is_connected"]
    
    def __init__(self, familty, type, protocol, remote_endpoint = None):
        Socket.__init__(self, familty, type, protocol)
        self._is_connected = False
        if remote_endpoint is not None:
            self.connect(remote_endpoint)
    
    def connect(self, endpoint):
        """connects this socket to a remote endpoint. if the socket is not 
        already bound, it is automatically bound to a free local endpoint"""
        if self._is_connected:
            raise AlreadyConnectedError()
        try:
            self._sock.connect(endpoint)
        except _socket.timeout:
            raise TimeoutError()
        except _socket.error, (errno, info):
            if errno in timeout_errnos:
                raise TimeoutError()
            else:
                raise ConnectError(errno, info)
        self._is_connected = True
        self._is_bound = True
    
    def _get_peername(self):
        if not self._is_connected:
            raise NotConnectedError()
        return self._sock.getpeername()
    remote_endpoint = property(_get_peername, doc = 
        "the socket's remote endpoint")
    
    def recv(self, count):
        """receives data from the socket. the length of the recv()ed data
        may be less than or equal to `count`"""
        if not self._is_connected:
            raise NotConnectedError()
        try:
            data = self._sock.recv(count)
        except _socket.timeout:
            return ""
        except _socket.error, (errno, info):
            if errno in timeout_errnos:
                return ""
            else:
                raise SocketError(errno, info)
        if not data:
            raise EOFError()
        return data
    
    def send(self, data):
        """sends the given data over the socket, returns the number of bytes
        actually transmitted"""
        if not self._is_connected:
            raise NotConnectedError()
        try:
            return self._sock.send(data)
        except _socket.timeout:
            raise TimeoutError()
        except _socket.error, (errno, info):
            if errno in timeout_errnos:
                raise TimeoutError()
            else:
                raise SocketError(errno, info)


#
# connection-less (datagram) sockets
#
class DatagramSocket(Socket):
    """datagram sockets (not connected)"""
    
    def __init__(self, familty, type, protocol, local_endpoint = None):
        Socket.__init__(self, familty, type, protocol)
        if local_endpoint is not None:
            self.bind(local_endpoint)
    
    def send(self, data, addr):
        try:
            return self._sock.sendto(data, addr)
        except _socket.timeout:
            raise TimeoutError()
        except _socket.error, (errno, info):
            raise SocketError(errno, info)
    
    def recv(self, count):
        try:
            return self._sock.recvfrom(count)
        except _socket.timeout:
            return "", None
        except _socket.error, (errno, info):
            if errno in timeout_errnos:
                return "", None
            else:
                raise SocketError(errno, info)


class RawSocket(Socket):
    """to be implemented"""
    pass


#
# protocol-specific sockets
#
class TcpConnectedSocket(ConnectedSocket, IpLevelMixin, TcpLevelMixin):
    """a connected (client) socket wrapper for TCP/IP"""
    __slots__ = []
    def __init__(self, *endpoint, **kw):
        remote_endpoint = endpoint or None
        family = kw.pop("family", consts.AddressFamily.INET)
        ConnectedSocket.__init__(self, family, consts.SocketType.STREAM, 
            consts.IpProtocol.TCP, remote_endpoint, **kw)


class TcpListenerSocket(ListenerSocket, IpLevelMixin, TcpLevelMixin):
    """a listener (server) socket wrapper for TCP/IP"""
    __slots__ = []
    def __init__(self, *endpoint, **kw):
        local_endpoint = endpoint or None
        family = kw.pop("family", consts.AddressFamily.INET)
        ListenerSocket.__init__(self, family, consts.SocketType.STREAM, 
            consts.IpProtocol.TCP, local_endpoint, **kw)
    
    def accept(self):
        return TcpConnectedSocket.wrap(
            _sock = ListenerSocket.accept(self), 
            _is_bound = True,
            _is_connected = True
        )


class UdpSocket(DatagramSocket, IpLevelMixin):
    """udp sockets"""
    __slots__ = []
    def __init__(self, *endpoint, **kw):
        local_endpoint = endpoint or None
        family = kw.pop("family", consts.AddressFamily.INET)
        DatagramSocket.__init__(self, family, consts.SocketType.DGRAM, 
            consts.IpProtocol.UDP, local_endpoint, **kw)





