from .base import *
import os


DEBUG = False

try:
    from .local import *
except ImportError:
    pass
