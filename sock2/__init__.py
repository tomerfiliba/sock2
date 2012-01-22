"""
Sock2 -- Pythonic Sockets
Version 0.6

Mission Statement:
The standard python socket module wraps the BSD-socket C-APIs, with only 
minimal abstraction. It exposes a very low-level and rigid API to working
with sockets, which does not fit with pythonic paradigms. One thing, for 
instance, which demonstrates this "writing C in python", is the setsockopt 
method of socket objects: is that how it should be done in python?

Another design flaw is pushing all the socket methods into a single class.
For example, all sockets, even those connected to a server, or those opened
over UDP,  have the accept() method. Does this make sense?

Since the BDFL intends to replace python's (quite-outdated) IO intrastructure, 
it was suggested to revamp the socket module as well. For more info, see this
link: http://mail.python.org/pipermail/python-3000/2006-April/001497.html 

Design Goals:
    * a mission-oriented design:
        * different protocols are exposed by different classes
        * these classes are tailored per the protocol
    * a unified and convenient way to access socket options, via properties:
        * make options work with normal python objects, dependent on on the 
          option's underlying type
        * make options platform agnostic (winsock/bsd issues)
    * don't reinvent the wheel: 
        * uses _socket for the low-level stuff
        * just wraps it with a better API
        * no C code added to the branch
        * rely on a tested codebase
    * easy to use and more intuitive:
        * properties instead of methods, where appropriate
        * expose simple interfaces to common use cases
        * but still support less-frequently-used protocols and options
        * expose socket constants under namespaces, rather than a mishmash
        * better exceptions, all derive from IOError
    * more logical behavior:
        * EOF error instead of empty string when closed
        * when recv times-out, return empty string instead of exception
    * kick out legacy stuff:
        * ntohl, etc. -- just use the struct module
        * makefile -- iostack's NetworkStream does that
        * inet_aton -- ideally no one will need that; if need arises, 
          export those to a utility module
    * pull out DNS stuff:
        * make it a module on its own
        * unify the APIs
    * backwards-compatible when possible
        * rename socket.py to oldsocket.py
        * existing code that wants to retain the old semantics, would just
          need to  "import oldsocket as socket"
    * integrate with iostack's NetworkStream

To-do list for the final version:
    * finish ipv6 support
    * finish raw sockets support
    * thorough unittests
    * documentation:
        * user level docs and examples
        * developer docs
    * py3k issue: use the `bytes` type for send/recv, not `str`
"""
import consts
from errors import *
from socket import *


# shorthands
TcpSocket = TcpConnectedSocket
TcpListener = TcpListenerSocket
