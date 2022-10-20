from __future__ import annotations

__all__ = ["Timer", "HashVersion", "HashNode", "Version", "HashVerDec", "HexTimer"]

#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import json
import time
from datetime import date

import numpy as np


class HashNode(type):
    key = np.array([99, 99, 99, 99, 99])
    val = None

    def __new__(mcs, name, bases, dct, **kws):

        if not ('key' in dct.keys()):
            dct['key'] = mcs.key

        def __hex__(self):
            return "".join(map(lambda y: hex(y), self.key - np.asarray(self.val, dtype=np.int)))

        def __hash__(self):
            return self.__hex__()

        def __eq__(self, other):
            return self.__hex__() == other.__hex__()

        def __str__(self):
            s = self.__template__(f'{self.__hex__()} ', self.__class__.__name__ + " object ")
            return f'{s}'

        ms = [__hex__, __hash__, __eq__]
        for m in ms:
            if m.__name__ in dct.keys():
                pass
            else:
                dct[m.__name__] = m

        c = super().__new__(mcs, name, bases, dct)

        return c

    @classmethod
    def __decode__(mcs, other):
        return mcs.key - np.asarray([int(other[i:i + 4], 16) for i in range(0, len(other), 4)])


class Timer(object):
    """
    Basic immutable class fixing the initialisation time
    >>>t = Timer()
    >>>t()
    >>>t.date_tag
    >>>t.hours, t.minutes
    """
    TIME_SIGN = [3, 4]

    def __init__(self):
        _ts = self.__class__.TIME_SIGN
        _init_date = date.today().isoformat()

        _init_time = [time.gmtime()[i] for i in range(len(time.gmtime()))]
        _hours, _minutes = [_init_time[i] for i in _ts]
        self.date_tag = int(_init_date.replace('-', '')[2:], 10)
        self.hours = '0{}'.format(_hours) if len(str(_hours)[:2]) == 1 else str(_hours)
        self.minutes = '0{}'.format(_minutes) if len(str(_minutes)[:2]) == 1 else str(_minutes)

    def __str__(self):
        return f'timer at: {self.date_tag} {self.hours} {self.minutes}'

    def __call__(self):
        return self.date_tag, self.hours, self.minutes


class Version(Timer):

    def __init__(self, val=None):
        if not val:
            super().__init__()
            self.version = self.date_tag
            self.build = self.hours
            self._val = str(self.version) + str(self.build)
        if val is not None:
            a, b = str(val)[:6], str(val)[5:]
            print(a, b)
            self.version = a
            self.build = b
            self._val = val

    def __call__(self):
        return str(self._val)

    def __str__(self):
        return f'version:\033[92m {self.version}\033[37m build:\033[92m {self.build}\033[37m '

    def __repr__(self):
        return f"id{id(self)} {self.__str__()}"


class HexTimer(Timer, metaclass=HashNode):
    key = np.array([99, 99, 99, 99, 99])

    def __init__(self):
        super().__init__()
        self.tm = time.time_ns()
        self.key = self.__class__.key
        self.val = np.asarray(
            [str(self.date_tag)[:2], str(self.date_tag)[2:4], str(self.date_tag)[4:6], self.hours, self.minutes],
            dtype=int)


class HashVerDec:
    def __init__(self, cls):
        self._cls = cls

    def __call__(self, *args, val=None, **kwargs):
        if val is None:
            obj = self._cls(*args, val=val, **kwargs)
        else:
            obj = self._cls.__decode__(val)
        return obj


@HashVerDec
class HashVersion(HexTimer):
    key = np.array([99, 99, 99, 99, 99])

    def __init__(self, val):
        if val is None:
            super().__init__()

        else:
            self.val = val

        self.year, self.mount, self.day, self.hour, self.minute = self.val
        self.version_dict = dict(
            year=self.year, mount=self.mount, day=self.day, hour=self.hour, minute=self.minute
        )
        self._val = ''.join([str(v) for v in self.val])

        self.date_tag = int(self._val)

    @classmethod
    def __decode__(cls, other):
        return cls(cls.key - np.asarray([int(other[i:i + 4], 16) for i in range(0, len(other), 4)]))

    def __call__(self):
        return self._val

    def __hex__(self):
        return "".join(map(lambda y: hex(y), self.key - np.asarray(self.val, dtype=int)))

    def __hash__(self):
        return self.__hex__()

    def __eq__(self, other):
        return self.__hex__() == other.__hex__()

    def __str__(self):
        st = f"Version (\n"
        for k, v in self.version_dict.items():
            st += f"\n {k} = {v}"

        return st + ')'

    def _dct(self):

        return {'version': self.__hex__()}

    def __repr__(self):
        return f"v{self.__hex__()}"

    def encode(self):
        return json.dumps(self._dct())

    def to_json(self):
        return json.dumps(self._dct())


class Vector(list):
    def __new__(cls, follow=None, **kwargs):

        instance = super().__new__(cls, list(kwargs.values()))
        if follow is None:
            instance._follow = hex(id(instance))
        else:
            instance._follow = follow
        instance.cls = cls
        instance._vals = np.asarray(list(kwargs.values()))
        instance._kws = kwargs
        instance._keys = np.asarray(list(kwargs.keys()))
        return instance

    @property
    def keys(self):
        return self._keys

    @property
    def follow(self):
        return self._follow

    @keys.setter
    def keys(self, v):
        k, v = v
        self._keys[self._keys.index(k)] = v
        self.__dict__ |= self.dct

    @property
    def dct(self):
        return dict(zip(self.keys, self.values))

    @property
    def values(self):
        return self._vals

    @values.setter
    def values(self, v):
        k, v = v
        self.dct[k] = v
        self.__dict__ |= self.dct

    def __add__(self, other):
        vl = []
        keys = []
        for key in set(tuple(self.keys) + tuple(other.keys)):
            vl.append(self.cls(**{key: [self.dct[key], other.dct[key]]}))
            keys.append(key)
        return self.cls(**dict(zip(list(keys), vl)))


"""
class Vers(Vector):
    _tsl:int = 3
    _ishex:bool=False
    _view:tuple=None
    def __new__(cls, follow="",  v=Vector((0,)), init_timestamp=time.gmtime(), **kwargs):

        super().__new__(cls, (follow, v, init_timestamp), _follow=follow,  _i=v,init_timestamp=init_timestamp, _timestamp=init_timestamp, **kwargs)

    def __next__(self):
        self._i += 1
        self._timestamp = time.gmtime()
        return self
    @property
    def follow(self):
        return self._follow

    def __iadd__(self, other):
        for i in range(other):
            next(self)
        return self

    def timestamp_len(self):
        return self._tsl

    @property
    def timestamp(self):
        return self._timestamp[self._tsl]
    @property
    def vers_view(self):
        if self._ishex:

            self._view =self.follow ,hex(self._i), hex(int(self.timestamp))
        else:
            self._view =self.follow, self._i, int(self.timestamp)
        return self._view

    @vers_view.setter
    def vers_view(self, v:bool):
        self._ishex = v

    @timestamp_len.setter
    def timestamp_len(self, v):
        self._tsl = v

    def encode(self):
        return b"v'".join(bytes(self.follow)).join(bytes(self.vers_view))+b"'"
    def __str__(self):
        v,t=self.vers_view

        return f"v'{self.follow} {v} {t}'"
    @classmethod
    def decode(cls, v: bytes|str):

        newcls=cls()
        if isinstance(v,str):
            vv=v.encode()
        elif isinstance(v, bytes):
            vv=v
        else:
            raise TypeError(f"MM expected bytes or string, not {type(v)} .")
        if vv.startswith(b"v'"):
            follow, vrs, tms = vv.removesuffix(b"'").removeprefix(b"v'").split(b" ")
            newcls._follow=follow.decode()
            newcls._i =vrs
            newcls._timestamp  = time.gmtime( float(tms.decode())*1e-9)
            return newcls
        else:
            raise TypeError(f"MM {vv[:1]} is not {cls.__name__} byte-tag. Expected b''v' .")

    def __iadd__(self, other):
        self._i += 1
        return self
    def __repr__(self):

        return f"<{self.__str__()} object at {hex(id(self))}>"
    def __radd__(self, other):
        if isinstance(other, Vers):
            return self, other
        elif isinstance(other, list(Vers)):
            return other+self

class SimpleSemanticVersion:
    def __init__(self):

        self._i = 0
        self._instance = None

    def __iadd__(self, other):
        self._i += 1
        return self

    def __set_name__(self, owner, name):
        self.name = name
        self.priv_name = "_" + self.name
        try:
            owner.vers[self.name] = self
        except:
            owner.vers = dict()
            owner.vers[self.name] = self
        setattr(owner, self.priv_name, None)
        self.owner = owner

    def __set__(self, instance, value):
        if getattr(instance, self.priv_name) == value:
            pass
        else:
            next(self)

            instance.vers[self.name] += 1
            setattr(instance, self.priv_name, value)

    def __get__(self, instance, owner):
        return self
class CombineVersion:
    def __set_name__(self, owner, name):
        self.name = "vers"
        self.owner = owner
        self._dct = dict()
        setattr(self.owner, "vers", "dict")

    def follow(self, f):

        self._dct[f.__name__].__set_name__(self.owner, name=f.__name__)

    def __get__(self, instance, value):
        return"""
