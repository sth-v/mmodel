import inspect
from typing import Optional, Any, TypeVar

from datetime import date
import compas
import time
import json
from collections.abc import Iterable
import colored
import numpy as np
from colored import fg, attr
import rhino3dm
from vcs import Version, VersionController
from tools import TemplateBase
CONFIG_MM = {}
class Mmodel(object):
    """
    A base class from which all project classes should be inherited mmodel
    ....class MmodelProject(Mmodel):
    ....    ...
    """
    configs = CONFIG_MM

    def __init__(cls, fp="config.json"):
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

        # cls.VC = VersionController
        # cls.VC()

    def change_history(cls, name, kwargs):
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

        print(f'configurate from cls.configs:\n  {mcs.configs}')
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
            instance = super(C, self).__new__(self)
            for k, v in hst.items():
                setattr(instance, k, v)

            print(f'[metaclass] {C.__name__} attach attribute action: \n{hst.keys()}')
            instance.__init__(*args, **kwargs)
            setattr(self.__mmodel__, self.__name__.lower(), instance)

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
