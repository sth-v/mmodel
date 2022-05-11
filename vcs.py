# some version control
import inspect
from typing import Optional, Any, TypeVar

from datetime import date
import compas
import time
import json
from collections.abc import Iterable

import rhino3dm

CONFIG_MM = {}


class Mmodel(object):
    """
    A base class from which all project classes should be inherited mmodel
    ....class MmodelProject(Mmodel):
    ....    ...
    """
    configs = CONFIG_MM




    def __init__(self, fp="config.json"):
        global CONFIG_MM

        self.config_fp = fp
        print('\033[92mbuild mmodel\033[37m ...')
        print(f'\033[92mconfigurate with:\033[37m {self.config_fp}')
        f = open(self.config_fp)
        self.configs = json.load(f)
        f.close()
        CONFIG_MM |= self.configs
        for k, v in self.configs.items():
            setattr(self, k, v)

        self.vc = VersionController(self.history)
        setattr(BaseItem, 'vc', self.vc)

        # self.VC = VersionController
        # self.VC()

    def change_history(self, name, kwargs):
        name = name.upper()
        print(f'change history about {name}')
        v = Version(val=None)
        print(f'version: {v()}')
        changed_dict = {
            v(): kwargs
        }

        self.vc.change_history(name, changed_dict)
        self.vc = VersionController(self.history)
        setattr(BaseItem, 'vc', self.vc)
        return v()


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

    def __init__(self, val: Optional):
        if not val:
            super().__init__()
            self.version = self.date_tag
            self.build = self.hours
            self.val = str(self.version) + str(self.build)
        if val:
            a, b = str(val)[:6], str(val)[5:]
            print(a, b)
            self.version = a
            self.build = b
            self.val = val

    def __call__(self):
        return str(self.val)

    def __str__(self):
        return f'version:\033[92m {self.version}\033[37m build:\033[92m {self.build}\033[37m '


class VersionController(object):

    def __init__(self, _h):

        self.history = _h
        print(f'\033[92m[{self.__class__.__name__}] \033[37m run ...\033[37m')
        print(f'\033[92m[{self.__class__.__name__}] \033[37m call mmodel history: {self.history}\033[37m')
        print(f'\033[92m[{self.__class__.__name__}] \033[37m read history: {self.history}\033[37m')
        print(f'\033[92m[{self.__class__.__name__}] \033[37m history data read to >>> self.history_data\033[37m')

        self.changes = []

    def read(self):
        history_data = compas.json_load(self.history)
        return history_data

    def write(self, history_data):
        compas.json_dump(history_data)

    def last_version(self, item_cls, history_data):
        var = history_data[item_cls.__name__.upper()]
        vers = list(var.keys())

        # print(vers)
        def validator(vers):
            new = []
            for v in vers:
                if len(v) == 8:
                    print('valid: {}'.format(v))
                    new.append(v)
                else:
                    print('\033[31minvalid: {}'.format(v))
                    print(
                        f'Version {v} cannot be used as it does not comply with the protocol format\n    the length of '
                        f'the character string must be 8 characters, now: {len(v)}\033[37m')

            return new

        srtvers = validator(vers)
        srtvers.sort(reverse=True)

        last_version = srtvers[0]

        print(f'\033[92mlast: {last_version}\033[37m')
        return last_version

    def change_history(self, name, kwargs: dict):
        history_data = self.read()
        if name.upper() not in history_data.keys():
            v = Version(val=None)
            history_data[name.upper()] = {v():kwargs}

        named_history = history_data[name.upper()]
        named_history |= kwargs
        history_data |= named_history
        compas.json_dump(history_data, self.history)

    def item_from_last_version(self, item_cls):
        history_data = self.read()
        if item_cls.__name__.upper() not in history_data.keys():
            v = Version(val=None)
            history_data[item_cls.__name__.upper()] = {v():{'name': item_cls.__name__.lower()}}
        print(f'{self.__class__.__name__}: {item_cls.__name__} search last version...')
        last_v = self.last_version(item_cls, history_data)
        print(f'{self.__class__.__name__}:  ')
        scope_ = history_data[item_cls.__name__.upper()]
        dct = scope_[str(last_v)]
        dct |= {'version': last_v}
        return dct

    def item_from_spec_version(self, item_cls, version):
        history_data = self.read()
        var = history_data[item_cls.__name__.upper()]
        return var[str(version)]

    def read_version(self, item):
        history_data = self.read()
        var = history_data[item.__class__.__name__.upper()]

        try:

            last_version = self.last_version(item.__class__, history_data)

            print(f'{self.__class__.__name__}: last version from {item.__class__.__name__} : {last_version}')
            if item.version == last_version:
                print(f'{self.__class__.__name__}: pbj version is last')
                return item
            elif item.version > last_version:
                print(f'{self.__class__.__name__}: pbj version is most\n change history')
                var[item.version()] = item.__dict__
                history_data[item.__class__.__name__.upper()] = var
                return item
            else:
                print(f'{self.__class__.__name__}: item version is old')
                new_item = self.item_from_version(item.__class__)

            return new_item
        except Exception:
            print(f'{self.__class__.__name__}: no item with this name')

    def add_new_cls(self, item_cls):
        history_data = self.read()
        history_data[item_cls.__name__.upper()] = {}
        self.write(history_data)


class BaseItem(type):
    """
    A basic metaclass for creating GSA BIM elements and families of master model BIM elements and other project targets

    In addition to inheriting building element classes such as walls, tapes, etc, the metaclass should be used when
    creating project elements such as bindings, construction planes, etc.

    """
    configs = CONFIG_MM
    __rh__ = 'rh'
    __mmodel__ = None
    __instances__ = {}

    def __new__(mcs, classname, bases, attrs):

        print(f'configurate from mcs.configs:\n  {mcs.configs}')
        print(mcs.__mmodel__)





        C = type(classname, bases, attrs)
        C.vc = mcs.vc
        C.__mmodel__ = mcs.__mmodel__



        def _new_(cls, *args, **kwargs):
            if C.load == 'version':
                hst = C.vc.item_from_last_version(C)
                if '__rhino__' in attrs.keys():
                    keys = attrs['__rhino__']
                    for k in keys:
                        geom = mcs.__rh_attrs__(hst[k])
                        hst[k] = geom
            instance = super(C, cls).__new__(cls)
            for k, v in hst.items():
                setattr(instance, k, v)

            print(f'[metaclass] {C.__name__} attach attribute action: \n{hst.keys()}')
            instance.__init__(*args, **kwargs)
            setattr(mcs.__mmodel__, cls.__name__.lower(), instance)

            return instance
        C.__new__ = _new_
        return C

    def __rh_attrs__(mcs, attr):
        data = attr[mcs.__rh__]
        if isinstance(data, Iterable):
            list_ = []
            for i in data:
                list_.append(rhino3dm.GeometryBase.Decode(i))
            g = {"geom": list_}
        else:
            g = {"geom": rhino3dm.GeometryBase.Decode(data)}
        attr |= g
        return attr
