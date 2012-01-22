#
# both the Socket module and the Options module use these, so i had to 
# refactor the exceptions out
#
import errno


class SocketError(IOError):
    pass
class TimeoutError(SocketError):
    pass
class SocketClosed(SocketError):
    pass
class AcceptError(SocketError):
    pass
class SocketOptionError(SocketError):
    pass
class NotBoundError(SocketError):
    pass
class NotConnectedError(SocketError):
    pass
class BindError(SocketError):
    pass
class AlreadyBoundError(BindError):
    pass
class ConnectError(SocketError):
    pass
class AlreadyConnectedError(ConnectError):
    pass


#
# all sorts of timeout errnos (not all are treated correctly by _socket)
#
timeout_errnos = set(getattr(errno, name, None) 
    for name in ("EAGAIN", "EWOULDBLOCK", "WSAEWOULDBLOCK", "WSAETIMEDOUT"))
timeout_errnos.discard(None)
