# some version control
from typing import Optional, Any, TypeVar

from datetime import date
import compas
import time
import json

CONFIG_MM = {}

class Mmodel(object):

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


class Timer(object):
    TIME_SIGN = [3, 4]

    def __init__(self):
        _ts = self.__class__.TIME_SIGN
        _init_date = date.today().isoformat()

        _init_time = [time.gmtime()[i] for i in range(len(time.gmtime()))]
        _hours, _minutes = [_init_time[i] for i in _ts]
        self.date_tag = int(_init_date.replace('-', '')[2:], 10)
        self.hours, self.minutes = str(_minutes)[:2], str(_hours)[:2]

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
        named_history = history_data[name]
        named_history |= kwargs
        history_data |= named_history
        compas.json_dump(history_data, self.history)


    def item_from_last_version(self, item_cls):
        history_data = self.read()
        print(f'{self.__class__.__name__}: {item_cls.__name__} search last version...')
        last_v = self.last_version(item_cls, history_data)
        print(f'{self.__class__.__name__}:  ')
        scope_ = history_data[item_cls.__name__.upper()]
        dct = scope_[str(last_v)]

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

    def __new__(mcs, classname, bases, attrs):

        print(f'configurate from mcs.configs:\n  {mcs.configs}')

        c = type(classname, bases, attrs)
        # fp = mcs.configs["mm_parts"]["dev"]["dumps"] + "/" + classname.upper()
        # c.fp = fp
        c.vc = mcs.vc

        def init_by_kwargs(self, kwargs):

            print(kwargs.keys(), kwargs.values())
            for k, v in kwargs.values():
                setattr(self, k, v)

            setattr(self.__class__.mmodel, self.name, self)

        if c.load == 'fp':
            def init__(self, name, version):
                self.version = version

                self.name = name
                self.fp = self.__class__.fp + "/" + self.__class__.__name__.lower() + "_" + self.name + "_" + self.version + "_"
                kwargs = compas.json_load(self.fp + ".json")
                self.__dict__ |= kwargs
                setattr(self.__class__.mmodel, self.name, self)
        if c.load == 'version':

            def init__(self, version='last'):
                if version == 'last':
                    kwargs = self.__class__.vc.item_from_last_version(self.__class__)
                    print(f'[metaclass] {c.__name__} attach attribute action: \n{kwargs.keys()}')
                else:
                    kwargs = self.__class__.v.item_from_spec_version(self.__class__, version)
                    print(
                        f'[metaclass] {c.__name__} with specific version: {version}\nattach attribute action: \n{kwargs}')
                self.__dict__ |= kwargs
                setattr(self.__class__.mmodel, self.name, self)

        if c.load == 'kwargs':
            def init__(self, name, kwargs):
                self.name = name
                init_by_kwargs(self, kwargs)

        def dump_(self, *args, **kwargs) -> str:
            ...

        c.__init__ = init__
        c.dump = dump_
        return c
