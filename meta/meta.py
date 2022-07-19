# some version control
import copy
import hashlib
import posix
from typing import Optional, Any, TypeVar, Callable, ClassVar

import pandas as pd

from tools import TemplateBase

import logging


class context(type):
    def __new__(mcs, name, bases, dct):
        pass


class mm_meta(type):
    __template__ = TemplateBase

    def __new__(mcs, name, bases, dct):
        mcs.__template__(mcs.__name__, f'create new class: {name}')
        c = super().__new__(mcs, name, bases, dct)

        return c


class mm_meta_i(type):
    __template__ = TemplateBase

    def __new__(mcs, name, bases, dct):
        mcs.__template__(mcs.__name__, f'create new class: {name}')

        f = copy.deepcopy(dct['__init__'])

        def real__init__(self, *args, **kwargs):
            super().__init__(self)
            self.__meta_init__(**kwargs)
            self.__template__(f'__init__', f'run in {self.__name__}')
            f(self, *args, **kwargs)

        dct['__init__'] = real__init__
        c = super().__new__(mcs, name, bases, dct)

        return c

    def __meta_init__(cls, **kwargs):
        super().__init__(cls)
        cls.__template__(f'__meta_init__', f'run in {cls.__name__}')
        for k, v in kwargs.items():
            setattr(cls, k, v)


    class NaiveHashLogger:
        __import__ = ['os', 'sys', 'datatime', 'time']

        def __init__(self, fp):
            self.fp = fp

            scan = posix.scandir('dumps')
            last = fp.split('/')[-1]
            print(last, scan)

            if last in scan:
                self.statement = 'load'
                print(f'file [{scan}] read sucsess')
            else:
                print('no file')

                self.statement = 'create'


    class PrmFunc(Callable):

        def __init__(self, *inputs, **kwargs):
            super().__init__()
            self._inputs = inputs
            self.newclass = inputs[-1]
            self._method = None
            self._inpts = None
            self.__dict__ |= kwargs
            dct = []
            for inp in inputs:
                setattr(self, inp.__name__, inp)
                setattr(inp, 'func', self)
            self._dct = dct

            self.df = pd.DataFrame(self._dct)

        @property
        def inputs(self):
            return self._inpts

        @inputs.getter
        def inputs(self):
            return [getattr(self, cl.__name__) for cl in self._inputs]

        def __getitem__(self, keys):
            l = []
            for k in keys:
                l.append(getattr(self, k))

            return l

        def __setitem__(self, key, val):
            setattr(self, key, val)

        @property
        def method(self):
            return self._method

        @method.setter
        def method(self, val):
            self._method = val

        @method.deleter
        def method(self):
            del self._method

        def attach_version(self):
            dct = [(inp.__name__, inp.version) for inp in self.inputs[:-1]]

            setattr(self.newclass_object, 'version', dct)

        def __call__(self, **kwargs):

            m = self._method

            mm = m(self.A, self.B, self.C, **kwargs)
            setattr(self, 'newclass_object', mm)
            self.attach_version()
            return mm
