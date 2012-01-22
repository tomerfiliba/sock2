"""
Options -- BSD sockets options
For years, everybody was too lazy to write this down... and frankly, I don't 
blame them ;). Anyway, I went over socketmodule.c and extracted all the socket 
options that the _socket module is able expose, read through the man pages 
what they mean and what their types are. I then went and created abstraction 
layers for all the types, and defined huge tables of 
(option name, pythonic name, type, doc) for each option level.

Notes:
    * not all options are supported on all platforms, so the properties are 
      added to the mixin class only if they are supported on the given platform
    * platforms may disagree on the types of the options (especially winsock),
      so I did my best to expose a consistent behavior
    * if options are added to/removed from socketmodule.c, don't forget to
      update this module as well
"""
import os
import struct
import _socket
import Consts
from Errors import SocketOptionError


#
# different option types
#
def option_error_decorator(func):
    def wrapper(*a, **k):
        try:
            return func(*a, **k)
        except _socket.error, (errno, info):
            raise SocketOptionError(errno, info)
    return wrapper

def BoolOption(level, option, doc):
    @option_error_decorator
    def getter(self):
        return bool(self._sock.getsockopt(level, option))
    @option_error_decorator
    def setter(self, value):
        return self._sock.setsockopt(level, option, int(value))
    return property(getter, setter, doc = doc)

def IntOption(level, option, doc):
    @option_error_decorator
    def getter(self):
        return int(self._sock.getsockopt(level, option))
    @option_error_decorator
    def setter(self, value):
        return self._sock.setsockopt(level, option, int(value))
    return property(getter, setter, doc = doc)

def LingerOption(level, option, doc):
    if os.name == "nt":
        format = "HH"
    else:
        format = "ii"
    size = struct.calcsize(format)
    
    @option_error_decorator
    def getter(self):
        active, value = struct.unpack(format, self._sock.getsockopt(level, option, size))
        if active:
            return value
        else:
            return None
    @option_error_decorator
    def setter(self, value):
        if value is None:
            active = 0
            value = 0
        else:
            active = 1
        return self._sock.setsockopt(level, option, struct.pack(format, active, value))
    return property(getter, setter, doc = doc)

def _winsock_timeval_option(level, option, doc):
    @option_error_decorator
    def getter(self):
        return self._sock.getsockopt(level, option) / 1000.0
    @option_error_decorator
    def setter(self, value):
        self._sock.setsockopt(level, option, int(value * 1000))
    return property(getter, setter, doc = doc)

def _bsd_timeval_option(level, option, doc):
    format = "ll"
    size = struct.calcsize(format)
    @option_error_decorator
    def getter(self):
        sec, usec = struct.unpack(format, self._sock.getsockopt(level, option, size))
        return sec + usec / 1e6
    @option_error_decorator
    def setter(self, value):
        sec = int(value)
        usec = int((value - sec) * 1e6)
        return self._sock.setsockopt(level, option, struct.pack(format, sec, usec))
    return property(getter, setter, doc = doc)

def TimevalOption(level, option, doc):
    if os.name == "nt":
        return _winsock_timeval_option(level, option, doc)
    else:
        return _bsd_timeval_option(level, option, doc)

def Ipv4MreqOption(level, option, doc):
    format = "4s4s"
    size = struct.calcsize(format)
    @option_error_decorator
    def getter(self):
        mcast, iface = struct.unpack(format, self._sock.getsockopt(level, option, size))
        return _socket.inet_ntoa(mcast), _socket.inet_ntoa(iface)
    @option_error_decorator
    def setter(self, (mcast, iface)):
        raw = struct.pack(format, _socket.inet_aton(mcast), _socket.inet_aton(iface))
        self._sock.setsockopt(level, option, raw)
    return property(getter, setter, doc = doc)

def Ipv6MreqOption(level, option, doc):
    format = "<16sI"
    size = struct.calcsize(format)
    @option_error_decorator
    def getter(self):
        mcast, iface = struct.unpack(format, self._sock.getsockopt(level, option, size))
        return _socket.inet6_ntoa(mcast), iface
    @option_error_decorator
    def setter(self, (mcast, iface)):
        raw = struct.pack(format, _socket.inet6_aton(mcast), iface)
        self._sock.setsockopt(level, option, raw)
    return property(getter, setter, doc = doc)

def SockaddrIn6Option(level, option, doc):
    format = "<BBHL16s"
    size = struct.calcsize(format)
    @option_error_decorator
    def getter(self):
        len, fam, port, flow, addr = struct.unpack(format, self._sock.getsockopt(level, option, size))
        return port, flow, _socket.inet6_ntoa(addr)
    @option_error_decorator
    def setter(self, (port, flow, addr)):
        raw = struct.pack(format, size, Consts.AddressFamily.IPv6, port, flow, _socket.inet6_aton(mcast))
        self._sock.setsockopt(level, option, raw)
    return property(getter, setter, doc = doc)

def RawOption(level, option, doc):
    @option_error_decorator
    def getter(self):
        return self._sock.getsockopt(level, option, 1024)
    @option_error_decorator
    def setter(self, value):
        self._sock.setsockopt(level, option, value)
    return property(getter, setter, doc = doc)


#
# option types
#
ip_level_options = (
    ("TTL",                    "ttl",                  IntOption,      "time to live (int)"),
    ("TOS",                    "tos",                  IntOption,      "type of service (int)"),
    ("MULTICAST_TTL",          "mcast_ttl",            IntOption,      "multicast time to live (int)"),
    
    ("HDRINCL",                "header_included",      BoolOption,     "include header in raw sockets (bool)"),
    ("RECVOPTS",               "recv_ip_options",      BoolOption,     "receive IP options (bool)"),
    ("RECVRETOPTS",            "recv_ip_ret_options",  BoolOption,     "receive the reflected options for use in replies (bool)"),
    ("RECVDSTADDR",            "recv_ip_dst_addr",     BoolOption,     "receive the destination address of the datagram (bool)"),
    ("RETOPTS",                "recv_ip_options_raw",  BoolOption,     "receive unprocessed IP options (bool)"),
    ("MULTICAST_LOOP",         "enable_mcast_loopback",BoolOption,     "send multicasted packets the sender as well (bool)"),
    
    ("MULTICAST_IF",           "mcast_interface",      Ipv4MreqOption, "multicast interface (mreq; a tuple of (ipaddr-string, ipaddr-string))"),
    ("ADD_MEMBERSHIP",         "_add_membership",      Ipv4MreqOption, "join multicast group (mreq; a tuple of (ipaddr-string, ipaddr-string))"),
    ("DROP_MEMBERSHIP",        "_drop_membership",     Ipv4MreqOption, "leave multicast group (mreq; a tuple of (ipaddr-string, ipaddr-string))"),
    
    ("OPTIONS",                "raw_options",           RawOption,      "raw ip-level options in the ip header (raw)"),
)

ipv6_level_options = (
    ("JOIN_GROUP",             "_join_group",          Ipv6MreqOption, "join multicast group (ip6-mreq; a tuple of (ipv6addr-string, interface-number))"),
    ("LEAVE_GROUP",            "_leave_group",         Ipv6MreqOption, "leave multicast group (ip6-mreq; a tuple of (ipv6addr-string, interface-number))"),
    
    ("V6ONLY",                 "allow_v6_only",        BoolOption,     "allows only IPv6 packets to be sent/recvd (bool)"),
    ("DONTFRAG",               "dont_fragment",        BoolOption,     "disables fragmentation (bool)"),
    ("USE_MIN_MTU",            "use_min_mtu",          BoolOption,     "uses the minimum MTU for transmission (bool)"),
    ("RECVTCLASS",             "recv_traffic_class",   BoolOption,     "receive the traffic class of incoming packets (bool)"),
    ("RECVPATHMTU",            "recv_path_mtu",        BoolOption,     "receive the path mtu of the inbound packet (bool)"),
    ("RECVDSTOPTS",            "recv_dst_options",     BoolOption,     "receive inbound packet's destination options extension header (bool)"),
    ("RECVHOPLIMIT",           "recv_hop_limit",       BoolOption,     "receive the inbound packet's current hoplimit (bool)"),
    ("RECVHOPOPTS",            "recv_hop_options",     BoolOption,     "receive inbound packet's IPv6 hop-by-hop extension header (bool)"),
    ("RECVPKTINFO",            "recv_packet_info",     BoolOption,     "receive the index of the interface the packet arrived on, and of the inbound packet's destination address (bool)"),
    ("RECVRTHDR",              "recv_routind_header",  BoolOption,     "inbound packet's IPv6 routing header (bool)"),
    ("MULTICAST_LOOP",         "mcast_loopback",       BoolOption,      "send multicasted packets the sender as well (bool)"),
    
    ("MULTICAST_HOPS",         "mcast_hops",           IntOption,      "default hop limit for multicast datagrams (int)"),
    ("MULTICAST_IF",           "mcast_interface",      IntOption,      "the index of the interface to use (int)"),
    ("CHECKSUM",               "checksum_offset",      IntOption,      "the offset of the 16bit checksum field; -1 disables checksuming (int)"),
    ("TCLASS",                 "traffic_class",        IntOption,      "the traffic class (0..255); -1 for default (int)"),
    ("HOPLIMIT",               "hoplimit",             IntOption,      "the initial hoplimit for outbound datagrams (int)"),
    ("UNICAST_HOPS",           "unicast_hops",         IntOption,       "default hop limit for unicast datagrams (int)"),
    
    ("DSTOPTS",                "destination_options",  RawOption,      "one or more destination options (raw)"),
    ("HOPOPTS",                "hop_options",          RawOption,      "one or more hop-by-hop options (raw)"),
    ("RTHDR",                  "routing_header",       RawOption,      "the IPv6 routing header (raw)"),
    ("RTHDRDSTOPTS",           "dest_routing_options", RawOption,      "one or more destination options for all intermediate hops (raw)"),
    
    ("NEXTHOP",                "next_hop",             None,           "the address of the first hop, which must be a neighbor of the sending host (sockaddr_in6)"),
    ("PATHMTU",                "path_mtu",             None,           "the path MTU associated with a connected socket (ip6_mtuinfo)"),
    ("PKTINFO",                "packet_info",          None,           "the source address and/or interface out which the packets will be sent (in6_pktinfo)"),
)

tcp_level_options = (
    ("NODELAY",                "no_delay",             BoolOption,     "disable delay (AKA Nagle's algorithm) (bool)"),
    ("CORK",                   "enable_cork",          BoolOption,     "don't send partial frames (bool)"),
    ("QUICKACK",               "quickack",             BoolOption,     "enable quick acks (bool)"),
    
    ("MAXSEG",                 "max_segment_size",     IntOption,      "max segment size (int)"),
    ("KEEPIDLE",               "keepalives_idle",      IntOption,      "idle time before starting keepalives, in seconds (int)"),
    ("KEEPINTVL",              "keepalives_interval",  IntOption,      "interval between keepalives, in seconds (int)"),
    ("KEEPCNT",                "max_keepalives",       IntOption,      "max number of keepalives before dropping the connection (int)"),
    ("SYNCNT",                 "connect_attempts",     IntOption,      "max number of connect attempts before failing (int)"),
    ("DEFER_ACCEPT",           "defer_accept",         IntOption,      "timeout for connect(), in seconds (int)"),
    ("LINGER2",                "fin_wait_timeout",     IntOption,      "timeout for FIN_WAIT2 (int)"),
    ("WINDOW_CLAMP",           "window_size",          IntOption,      "max TCP-window size (int)"),
    
    ("INFO",                   "_tcp_info",            RawOption,      "obtain TCP metrics for this socket; linux specific (raw)"),
)

socket_level_options = (
    ("DEBUG",              "debug_mode",               BoolOption,     "debug mode (bool)"),
    ("ACCEPTCONN",         "accept_connection",        BoolOption,     "allow accept()ing connections (bool)"),
    ("REUSEADDR",          "reuse_address",            BoolOption,     "allow rebinding the local endpoint (bool)"),
    ("EXCLUSIVEADDRUSE",   "exclusive_address",        BoolOption,     "don't allow rebinding the address (bool)"),
    ("KEEPALIVE",          "use_keepalives",           BoolOption,     "use keepalives (idle-time and interval are TCP-specific) (bool)"),
    ("DONTROUTE",          "dont_route",               BoolOption,     "disable routing (bool)"),
    ("BROADCAST",          "allow_broadcast",          BoolOption,     "allow broadcasts from this socket (bool)"),
    ("USELOOPBACK",        "use_loopback",             BoolOption,     "use the loopback device (bool)"),
    ("OOBINLINE",          "oob_inline",               BoolOption,     "keep out-of-band (urgent) data in-line (bool)"),
    ("REUSEPORT",          "reuse_port",               BoolOption,     "allow rebinding the local port (bool)"),
    
    ("SNDBUF",             "send_buffer_size",         IntOption,      "send buffer size (int)"),
    ("RCVBUF",             "recv_buffer_size",         IntOption,      "recv buffer size (int)"),
    ("SNDLOWAT",           "min_send_size",            IntOption,      "minimun size for send()ing (int)"),
    ("RCVLOWAT",           "min_recv_size",            IntOption,      "minimum size for recv()ing (int)"),
    ("ERROR",              "error_state",              IntOption,      "gets the error code of the socket (int)"),
    ("TYPE",               "socket_type",              IntOption,      "gets the type of the socket (one of Consts.SocketType.xxx) (int)"),
    
    ("SNDTIMEO",           "send_timeout",             TimevalOption,  "send timeout in seconds (float)"),
    ("RCVTIMEO",           "recv_timeout",             TimevalOption,  "recv timeout in seconds (float)"),
    
    ("LINGER",             "linger",                   LingerOption,   "linger-after-close timeout in seconds (int or None)"),
)


#
# per-level option classes
#
def LevelOptions(socklevel, level_namespace, options):
    def class_creator(name, bases, namespace):
        for (optname, propname, proptype, doc) in options:
            if proptype is None:
                continue
            if hasattr(level_namespace, optname):
                namespace[propname] = proptype(socklevel, getattr(level_namespace, optname), doc)
        return type(name, bases, namespace)
    return class_creator


class SocketLevelOptions(object):
    __metaclass__ = LevelOptions(Consts.OptionLevels.SOCKET, Consts.SocketLevelOptions, socket_level_options)
    __slots__ = []


class IpLevelMixin(object):
    __metaclass__ = LevelOptions(Consts.OptionLevels.IP, Consts.IpLevelOptions, ip_level_options)
    __slots__ = []
    
    def join_group(self, (mcast, iface)):
        """joins the given multicast group. takes a tuple of (ipaddr-string, ipaddr-string)"""
        self._add_membership = (mcast, iface)
    
    def leave_group(self, (mcast, iface)):
        """leaves the given multicast group. takes a tuple of (ipaddr-string, ipaddr-string)"""
        self._drop_membership = (mcast, iface)


class Ipv6LevelMixin(object):
    __metaclass__ = LevelOptions(Consts.OptionLevels.IP, Consts.IpLevelOptions, ipv6_level_options)
    __slots__ = []
    
    def join_group(self, (mcast, iface)):
        """joins the given multicast group. takes a tuple of (ipv6addr-string, interface-number)"""
        self._join_group = (mcast, iface)
    
    def leave_group(self, (mcast, iface)):
        """leaves the given multicast group. takes a tuple of (ipv6addr-string, interface-number)"""
        self._leave_group = (mcast, iface)


class TcpLevelMixin(object):
    __metaclass__ = LevelOptions(Consts.OptionLevels.TCP, Consts.TcpLevelOptions, tcp_level_options)
    __slots__ = []





