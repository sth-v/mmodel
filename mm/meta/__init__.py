#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

# some version control
from __future__ import annotations

import copy
import inspect
import time
from collections import defaultdict
from typing import Iterator
import vcs.utils


from mm.collections import _AttrHandlerCollection
from mm.exceptions import MModelException

from mm.baseitems import Item, DictableItem


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
    logpath = "/Users/andrewastakhov/mmodel/meta/definelog"

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
