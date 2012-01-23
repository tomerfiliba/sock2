"""
The DNS APIs have been pulled out of their conventional place in the socket
module, into a new one. This module takes a more pythonic approach to working
with resolved host names: instead of getXXXbyYYY, you use the Address class
to represent resolved DNS records.
"""
import _socket
import re
from errors import AddressError


#
# internals
#
ipaddr_regexp = re.compile(r"\A" r"([0-9]{1,3})\." r"([0-9]{1,3})\." 
    r"([0-9]{1,3})\." r"([0-9]{1,3})" r"\Z")

def canonize_ipaddr(text):
    """canonizes the given ip address string (removes leading zeroes)"""
    mo = ipaddr_regexp.match(text)
    if mo is None:
        raise ValueError("invalid format")
    particles = []
    for part in mo.groups():
        n = int(part)
        if n > 255 or n < 0:
            raise ValueError("particle out of range (0..255)", n)
        particles.append(str(n))
    return ".".join(particles)

#
# APIs
#
class Address(object):
    """
    instances of this class represent resolved DNS addresses. you are not
    supposed to create instance of this class directly. instead you may use
    one of the factory functions (from_addr and from_name), which resolve
    by an ip address or a host name, respectively; or the resolve() function,
    which 'guesses' the format of the host.
    
    name - the (official) name of the host
    addr - the primary address 
    aliases - a list of alias names
    addresses - a list of alias addresses
    """
    __slots__ = ["name", "aliases", "addr", "addresses"]
    
    def __init__(self, name, addr, aliases, addresses):
        self.name = name
        self.addr = canonize_ipaddr(addr)
        self.aliases = tuple(set(aliases))
        self.addresses = tuple(set(canonize_ipaddr(a) for a in addresses))
    
    def __str__(self):
        return self.addr
    
    def __repr__(self):
        return "<%s(%r)>" % (self.__class__.__name__, self.name)
    
    def __hash__(self):
        """hash by address, not by id"""
        return hash(self.addr)
    
    def __cmp__(self, other):
        """compare by address. can compare against another Address instance or
        directly against an ip-string"""
        if hasattr(other, "addr"):
            return cmp(self.addr, other.addr)
        else:
            return cmp(self.addr, canonize_ipaddr(str(other)))
    
    @classmethod
    def from_addr(cls, addr):
        """creates an Address instance from a host address"""
        try:
            name, aliases, addresses = _socket.gethostbyaddr(addr)
        except _socket.error, ex:
            raise AddressError(*ex.args)
        return cls(name, addr, aliases, addresses)
    
    @classmethod
    def from_name(cls, name):
        """creates an Address instance from a host name"""
        try:
            official_name, aliases, addresses = _socket.gethostbyname_ex(name)
        except _socket.error, ex:
            raise AddressError(*ex.args)
        aliases.append(official_name)
        aliases.append(name)
        return cls(official_name, addresses[0], aliases, addresses)


def resolve(name_or_addr):
    """
    resolves the given host name or host address to a Resolver instance.
    this function uses a heuristic to 'guess' the format of name_or_addr:
    if it's a valid ip string, it is resolved by address; otherwise it is
    resolved by name. if you need to be explicit, use Address.from_addr or
    Address.from_name instead.
    """
    try:
        canonize_ipaddr(name_or_addr)
    except ValueError:
        return Address.from_name(name_or_addr)
    else:
        return Address.from_addr(name_or_addr)

#
# built-in addresses
#
loopback = Address.from_addr("127.0.0.1")
thishost = Address.from_name(_socket.gethostname())
anyhost = Address.from_addr("0.0.0.0")


