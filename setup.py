try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name = "sock2",
    version = "0.7",
    description = "A modern, pythonic replacement for the socket module",
    author = "Tomer Filiba",
    author_email = "tomerfiliba@gmail.com",
    license = "MIT",
    url = "http://tomerfiliba.com/projects/sock2",
    packages = ['sock2']
)

