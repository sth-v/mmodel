__all__=["HashVersion", "HashNode", "Version", "HashVerDec", "HexTimer"]
import json
import time
from datetime import date

import numpy as np

from tools.colors import TemplateVcs, TemplateObjVcs



class HashNode(type):
    __template__ = TemplateVcs

    key = np.array([99, 99, 99, 99, 99])
    val = None

    def __new__(mcs, name, bases, dct, **kws):
        mcs.__template__(mcs.__name__, f'create new class: {name}')
        if not ('__template__' in dct.keys()):
            dct['__template__'] = mcs.__template__
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
    __template__ = TemplateObjVcs

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
    __template__ = TemplateObjVcs
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
        return "".join(map(lambda y: hex(y), self.key - np.asarray(self.val, dtype=np.int)))

    def __hash__(self):
        return self.__hex__()

    def __eq__(self, other):
        return self.__hex__() == other.__hex__()

    def __str__(self):
        st = f"Version (\n"
        for k, v in self.version_dict.items():
            st += f"\n {k} = {v}"

        return st + ')'

    def _dict(self):

        return {'version':self.__hex__()}
    def __repr__(self):
        return f"v{self.__hex__()}"
    def encode(self):
        return json.dump(self._dict())
    def to_json(self):
        return self._dict()