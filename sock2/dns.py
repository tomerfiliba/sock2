"""
DNS-related APIs
The Resolver class is meant to replace all gethostbyaddr/gethostbyname
by a simple-to-use object. 
"""
import _socket
import re


class ResolverError(Exception):
    pass


class Resolver(object):
    """
    instances of this class represent resolved DNS addresses. you are not
    supposed to create instance of this class directly. instead you may use
    one of the fractory functions (from_addr and from_name), which resolve
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
        self.addr = addr
        self.aliases = aliases
        self.addresses = addresses
    
    def __str__(self):
        return self.addr
    
    def __repr__(self):
        return "<%s(%r)>" % (self.__class__.__name__, self.name)
    
    @classmethod
    def from_addr(cls, addr):
        """creates a resolver instance from a host address"""
        try:
            name, aliases, addresses = _socket.gethostbyaddr(addr)
        except _socket.error, ex:
            raise ResolverError(*ex.args)
        return cls(name, addr, aliases, addresses)
    
    @classmethod
    def from_name(cls, name):
        """creates a resolver instance from a host name"""
        try:
            official_name, aliases, addresses = _socket.gethostbyname_ex(name)
        except _socket.error, ex:
            raise ResolverError(*ex.args)
        aliases.append(official_name)
        aliases.append(name)
        return cls(official_name, addresses[0], aliases, addresses)


_ipaddr_regexp = re.compile(r"\A([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\Z")
def _is_valid_ipaddr(text):
    mo = _ipaddr_regexp.match(text)
    if mo is None:
        return False
    for part in mo.groups():
        n = int(part)
        if n < 0 or n > 255:
            return False
    return True

def resolve(name_or_addr):
    """
    resolves the given host name or host address to a Resolver instance.
    this function uses a heuristic to 'guess' the format of name_or_addr:
    if it's a valid ip string, it is resolved by address; otherwise it is
    resolved by name. if you need to be explicit, use Resolver.from_addr
    or Resolver.from_name instead.
    """
    if _is_valid_ipaddr(name_or_addr):
        return Resolver.from_addr(name_or_addr)
    else:
        return Resolver.from_name(name_or_addr)

class _MyHost(object):
    """
    represents the local machine (not to be confused with 127.0.0.1). instances
    of this class are meant to look like instances of Resolver. 
    this class has a singleton instance called myhost. you are not supposed to 
    create instance of this class by yourself.
    """
    __slots__ = []
    
    def __str__(self):
        return self.addr
    
    def __repr__(self):
        return "<%s(%r)>" % (self.__class__.__name__, self.name)
    
    def _get_name(self):
        return _socket.gethostname()
    name = property(_get_name)
    
    def _get_addr(self):
        return _socket.gethostbyname(self.name)
    addr = property(_get_addr)
    
    def _get_aliases(self):
        return _socket.gethostbyname_ex(self.name)[1]
    aliases = property(_get_aliases)
    
    def _get_addresses(self):
        return _socket.gethostbyname_ex(self.name)[2]
    addresses = property(_get_addresses)


myhost = _ThisHost()


































