"""A simple abstract class for implementing the decorator pattern.
"""

class DecoratorClass(object):
    """A simple abstract class for implementing the decorator pattern.

    Instances are initialized with the decorated object, and when
    an attribute lookup fails, the instance will redirect it to
    the decorated object.
    """

    def __init__(self, decorated):
        self.__decorated = decorated

    def __getattr__(self, attr):
        return getattr(self.__decorated, attr)

    @property
    def decoratedObject(self):
        return self.__decorated
