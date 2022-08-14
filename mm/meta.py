# some version control
from __future__ import annotations

import copy
import hashlib
import inspect
import posix
import Rhino
import time
from collections import defaultdict
from typing import Iterable, Iterator, List, Optional, Any, Tuple, TypeVar, Callable, ClassVar, Union
import vcs.utils
import pandas as pd

from mm.unactive import DictableItem
from mm.collections import _AbstractItemCollection, _ArgGettersItem, _AttrHandlerCollection
from mm.exceptions import MModelException
from tools import TemplateBase

import logging
from mm import Item


class MetaItem(type):
    """
    [0] Шаблон Создания структурированных коллекций
    [1] Шаблон универсальных сереализаций
        класс -> схема
        генерация кода для классов оберток для rh/gh
    [2] Генерация целевых классов для других фреймворков
    [3] Интеграция в вычислительный граф
    [3] Пиклирование/сохранение
    """

    __dict__ = defaultdict()
    schema = defaultdict()
    classes = dict()
    default_bases = (Item,)

    subclasses = []

    def __new__(mcs, classname, bases, dct, **kwds):
        mcs.__dict__ |= dct
        mcs.__dict__ |= kwds

        cls = super(MetaItem, mcs).__new__(name=classname, bases=bases + mcs.default_bases, dict=dct, **kwds)

        cls._uid = hex(id(cls))
        mcs.classes[classname] = cls
        return cls

    def __class_getitem__(mcs, item):
        return mcs.classes[item.__name__]

    def __call__(cls, *args, **kwargs):
        cls.item_base = cls.default_bases[0]
        cls.__dict__ |= kwargs
        cls.version = vcs.utils.HashVersion()

    @property
    def uid(cls):
        return cls._uid

    @uid.setter
    def uid(cls, val):
        cls._uid = val

    def __str__(self):
        return f"definition {self.__name__} version: {self.version} mro: {self.mro()}"

    def __set_name__(self, owner, name):
        print(f"Setting new name {name} for {owner}")
        self.schema[name] = None

    def __init_subclass__(mcs, **kwargs):
        print(f"Sub definition {mcs}, {kwargs}")
        mcs.subclasses.append(mcs)

    def __contains__(self, item):
        if item in self.subclasses:
            return "subclasses", item
        elif item in self.classes:
            return "classes", item
        else:
            return None


class MetaLoggingItem(MetaItem):
    log = ""
    logpath = "/Users/andrewastakhov/mmodel_server/meta/definelog"

    def __new__(mcs, classname, bases, dct, **kws):
        cls = super(MetaLoggingItem, mcs).__new__(classname=classname, bases=bases, dct=dct, **kws)
        return cls

    def __init_subclass__(mcs, **kwargs):
        tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst = time.gmtime(time.time())

        mcs.log += f'[{tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec,}] ("definition", {kwargs})\n'
        with open(mcs.logpath, "a") as fp:
            fp.write(mcs.log)
        del mcs.log
        mcs.log = ""
        print(f"Sub definition {mcs}, {kwargs}")


class MetaCollection(MetaLoggingItem):
    collection_classes = []
    target = Item
    default_collection_base = _AttrHandlerCollection

    def __new__(mcs, item, dct, **kws):
        dct |= dict(target=item)
        cls = super(MetaCollection, mcs).__new__(classname=item.__name__ + "Collection",
                                                 bases=(mcs.default_collection_base, Iterator), dct=dict, **kws)

        mcs.collection_classes.append(cls)
        return cls


class MetaItemCollection(MetaCollection):
    required_methods = "__next__", "__getitem__", "__setitem__", "__delitem__", "__iter__"
    default_collection_base = _AbstractItemCollection


    class CollectHandle(_ArgGettersItem):
        def __init__(self, collection, i=0, *args, **kwargs):
            self.ci = 0
            super().__init__(*args, **kwargs)
            self.collection = collection
            self._args = set()
            self.__call__(**kwargs)
            self._args.update(set(self.collection[i].__getinitargs__().keys()))

        def __call__(self, obj_i, *args, **kwargs):
            super().__call__(*args, **kwargs)

            self.__dict__ |= kwargs
            self._args.update(set(self.collection[obj_i].__getnewargs__().keys()))

        def pnext(self, obj):
            for t in self._args:
                yield t, getattr(obj, t)

        def __getitem__(self, item):
            return list(self.pnext(self.collection[item]))

        def __len__(self):
            return len(self.collection)


    clhend = None

    def __new__(mcs, classname, bases, dct, item=_ArgGettersItem, **kws):
        if "Collection" in classname:
            print(f"{mcs.__name__}.__new__({classname}), {bases} ,{dct}")
        cls = super(MetaItemCollection, mcs).__new__(item, dct=dct, **kws)
        mcs.clhend = mcs.CollectHandle(cls)
        keys = mcs.clhend._args

        def updater(self):

            for k in keys:
                setattr(self, k, self[k])

        def __call__(self, *args, **kwargs):
            super().__call__(*args, **kwargs)
            self.attrs_handler.collection = self
            self.updater()

        setattr(cls, "updater", updater)
        setattr(cls, "__call__", updater)
        return cls


class AbstractItemCollection(_AttrHandlerCollection):
    """
    >>> ddd = defaultdict()
    >>> ddd["x"]= 1,2,33,8,22,4,51,8
    >>> ddd["y"]= 11,45,3,99,12,2,1,3
    >>> dt=[dict([("x", ddd["x"][i]),("y",ddd["y"][i])]) for i in range(8)]
    >>> dt
    [{'x': 1, 'y': 11},
     {'x': 2, 'y': 45},
     {'x': 33, 'y': 3},
     {'x': 8, 'y': 99},
     {'x': 22, 'y': 12},
     {'x': 4, 'y': 2},
     {'x': 51, 'y': 1},
     {'x': 8, 'y': 3}]
    >>> AbstractItemCollection(*dt)
    Out[3]: <__main__.AbstractItem at 0x15a1e2e20>
    >>> t_collection =

    (*dt)
    >>> t_collection["x"]
    [1, 2, 33, 8, 22, 4, 51, 8]
    >>> t_collection["y"]
    [11, 45, 3, 99, 12, 2, 1, 3]
    >>> t_collection[0,"x"]
    Out[4]: 1
    >>>t_collection[0,"y"]
    Out[5]: 11
    >>>list(next(t_collection))[0].ikw
    Out[7]: {'x': 33, 'y': 3}
    >>>list(next(t_collection))[0].ikw
    Out[8]: {'x': 8, 'y': 99}
    >>>list(next(t_collection))[0].ikw
    Out[9]: {'x': 22, 'y': 12}
    >>>list(next(t_collection))[0].ikw
    Out[10]: {'x': 4, 'y': 2}
    >>>for o in t_collection:
    ....   print(list(o)[0].__dict__)
    {'ikw': {'x': 1, 'y': 11}, 'iar': (), '_uid': '0x12a5ab040', 'x': 1, 'y': 11, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 2, 'y': 45}, 'iar': (), '_uid': '0x12a5ab430', 'x': 2, 'y': 45, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 33, 'y': 3}, 'iar': (), '_uid': '0x12a5ab2b0', 'x': 33, 'y': 3, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 8, 'y': 99}, 'iar': (), '_uid': '0x11fc27eb0', 'x': 8, 'y': 99, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 22, 'y': 12}, 'iar': (), '_uid': '0x11fc27cd0', 'x': 22, 'y': 12, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 4, 'y': 2}, 'iar': (), '_uid': '0x11fc27f40', 'x': 4, 'y': 2, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 51, 'y': 1}, 'iar': (), '_uid': '0x11fc27880', 'x': 51, 'y': 1, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 8, 'y': 3}, 'iar': (), '_uid': '0x11fc27e50', 'x': 8, 'y': 3, 'version': '0x4d0x5b0x600x600x62'}
    """
    target = _ArgGettersItem


class FieldsMeta(type):
    root = DictableItem
    interfaces: dict = {}
    classname_prefix = "Mmodel"

    def __new__(mcs, classname, bases, attrs, interface=False, **kws):

        main_parent = bases[0]
        if interface:
            o = super().__new__(mcs, classname, bases, attrs, **kws)
            mcs.interfaces[classname] = o
            return o
        else:
            attrs['aliases'] = []
            attrs['main_parent'] = main_parent
            attrs['mro'] = lambda x: list(inspect.getmro(x.main_parent))
            if 'required_fields' in attrs.keys():
                arf = copy.deepcopy(attrs['required_fields'])

                attrs['required_fields'].update(main_parent.required_fields)

            else:
                arf = set()
                attrs['required_fields'] = main_parent.required_fields
            newarf = attrs['required_fields']

            if 'interfaces' in attrs.keys():
                call_plugins = []
                for i in attrs['interfaces']:

                    if (i in mcs.interfaces.keys()) and (not None):

                        call_plugins.append(mcs.interfaces[i])

                    else:

                        raise MModelException(
                            f'\nDeclared interface "{i}" is not defined!\n{mcs.interfaces.keys()}\n')

                    def call_with_fields(self, *args, **kwargs):
                        self.args, self.kw = args, kwargs
                        for plugin in self.call_plugins:
                            print(f'call {plugin.__name__} interface')
                            # print(self.args)
                            # print(self.kw, " ->")
                            plugin.interface_call(self)
                            # print("-> ", self.kw)
                        kws_ = self.kw
                        # print(kws_)
                        super(main_parent, self).__call__(*args, **kws_)

                    attrs['call_plugins'] = call_plugins
                    attrs['__call__'] = call_with_fields

            else:
                pass

            # print(
            #   f'{main_parent.__name__} required_fields ({main_parent.required_fields}) -> {classname} required_fields ({arf}) ->  {classname} required_fields ({newarf})')

            return super().__new__(mcs, classname, bases, attrs, **kws)
