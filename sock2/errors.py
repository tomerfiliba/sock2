"""
a common place to define the package's exception classes. they are used in
several modules, so i had to refactor them out in order to avoid cyclic
importing
"""
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

class AddressError(IOError):
    pass


#
# all sorts of timeout errnos (not all are treated correctly by _socket)
#
timeout_errnos = set(getattr(errno, name, None)
    for name in ("EAGAIN", "EWOULDBLOCK", "WSAEWOULDBLOCK", "WSAETIMEDOUT"))
timeout_errnos.discard(None)


