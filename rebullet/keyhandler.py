"""Keyhandler imports"""

from . import utils
from .charDef import UNDEFINED_KEY


def register(key):
    """
    Mark the function with the key code that it handles so
    that it can found by _KeyHandlerRegisterer.
    """

    def wrap(func):
        if not hasattr(func, "_handle_key"):
            func._handle_key = [key]
        else:
            func._handle_key.append(key)
        return func

    return wrap


def init(cls):
    """Rewrite the class to include the _KeyHandlerRegisterer metaclass."""
    return _KeyHandlerRegisterer(cls.__name__, cls.__bases__, cls.__dict__.copy())


class _KeyHandlerRegisterer(type):
    _key_handler = {}

    def __new__(cls, name, bases, classdict):
        result = super().__new__(cls, name, bases, classdict)
        if not hasattr(result, "_key_handler"):
            result._key_handler = {}
        else:
            # Create a copy of the _key_handler attribute to avoid
            # inherited classes from changing parent.
            result._key_handler = result._key_handler.copy()
        result.handle_input = _KeyHandlerRegisterer.handle_input

        for value in classdict.values():
            handled_keys = getattr(value, "_handle_key", [])
            for key in handled_keys:
                result._key_handler[key] = value

        return result

    # TODO - This method is static and also using self. Figure out which should be kept!
    @staticmethod
    def handle_input(self):
        c = utils.getchar()
        i = c if c == UNDEFINED_KEY else ord(c)
        handler = self._key_handler.get(i)
        return handler(self) if handler is not None else None
