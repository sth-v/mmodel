import copy
from enum import Enum


class MutableEnum:
    """
        Decorator allowing you to dynamically extend Enum subclasses names & values

        >>> globals
        <built-in function globals>
        >>> @MutableEnum
        ... class C(str, Enum):
        ...     perspective="perspective"
        ...     ortho="ortho"
        ...     top="top"

        >>> C
        MutableEnum ref <enum 'C'>



        >>> list(C.enum)
        [<C.perspective: 'perspective'>, <C.ortho: 'ortho'>, <C.top: 'top'>]
        >>> C.extend("right", "left")
        >>> list(C.enum)
        [<C.perspective: 1>, <C.ortho: 2>, <C.top: 3>, <C.right: 4>, <C.left: 5>]
        >>> Mc, c = C()

        >>> Mc
        MutableEnum ref <enum 'C'>
        >>> c
        <enum 'C'>


    """

    def __init__(self, arg):
        self._arg = arg

        self.argname = copy.deepcopy(arg.__name__)
        globals().update({self.argname + "_": self._arg})

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self._arg)
        except:
            raise StopIteration

    def remove(self, *args):
        names = []
        [names.append(m) if not (m.name in args) else None for m in self._arg]
        self.global_update(names)

    def clear(self, *args):
        names = []
        [names.append(m) if not (m.name in args) else None for m in self._arg]
        self.global_update(names)

    def extend(self, *args):
        names = [m.name for m in self._arg] + list(args)
        self.global_update(names)

    def all_update(self, *args):
        self.global_update(args)

    def global_update(self, names):

        globals().update({self.argname + "_": Enum(self.argname, names)})

    def __str__(self):
        return f"{self.__class__.__name__} {self.names}"
    def __repr__(self):
        return f"{self.__class__.__name__} ref {self._arg}"
    @property
    def enum(self):
        return globals()[self.argname+"_"]

    @property
    def names(self):
        return [m.name for m in self._arg]

    def __call__(self):
        return self, self._arg
