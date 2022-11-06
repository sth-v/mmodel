# coding=utf-8
"""
Для того чтобы это работало
необходимо присутствие пространства имен py3ghredis

Объединение этих пакетов не возможно, как по причине разных версий python ,
так и в силу более широкогих возможностей использования py3ghredis.

По сути паттерн internal_redis_api + py3ghredis может быть без труда обобщен
до связок с любыми закрытыми програмными комплексами.
Такими как Revit, Tekla, и прочими решениями поддерживающими внутренний скриптинг.

Также паттерн стоит рассматривать как замену REST  ориентированному подходу,
такому как Grasshopper Hops

"""

__author__ = "andrewastakhov"

import copy
import os
import socket


# ---------------------------------------------------------------------------------
#    Да это достаточно быстро  >>>     ️   ....
# ---------------------------------------------------------------------------------

# Простите ...


class GhRedisSocket(object):
    """
    GhRedisSocket :
    >>> def main(host, port, command, msg=None):
    ...     with GhRedisSocket(host, port) as client:
    ...         print(client.qwery(command, msg))

    >>> if __name__ == "__main__":
    ...     print main(host='localhost', port=50007, command="keys")
    """

    def __init__(self, host, port, **kwargs):
        object.__init__(self)
        self.HOST = host
        self.session_data = {}
        self.PORT = port
        self.__dict__.update(kwargs)

    def send(self, msg):
        self.s.sendall(msg)
        # print('Received', repr(data))
        return self.s.recv(1024 * 8)

    def __enter__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.s.connect((self.HOST, self.PORT))

        def wrapper(command, msg=None):
            d = json.dumps([command, msg]) if msg else json.dumps([command])

            data = self.send(d)

            self.session_data[command] = copy.deepcopy(data)

            return data

        self.qwery = wrapper
        return self

    def __exit__(self, *args):
        pass


"""
class pathtype(type):
    child_registry = []

    def __new__(mcs, name, bases, attrs):

        attrs["owner"] = mcs
        if attrs["__parent__"] is None:
            t=type.__new__(mcs, classname, (PathRoot,) + bases, attrs)
            t.child_registry = {t.__path__()}
            pathtype.child_registry.append(weakref.ref(t.child_registry))

            return t
        else:

            return type(classname, (PathMember,) + bases, attrs)


class Pathable(object):

    @property
    def parent(self):
        return self._parent

    @parent.deleter
    def parent(self):
        self._parent.childs.remove(hex(id(inst)))
        self._parent = None

    @parent.setter
    def parent(self, v):
        self._parent = v

    def __init__(self, parent=None, *args, **kwargs):
        object.__init__(self)
        self.parent = parent

    def __path__(self): return self.parent.__path__() + ":" + hex(id(inst))


class Childs(set):
    def __init__(self): set.__init__(self)

    def __set_name__(self, owner, name="childs"):
        self.owner = owner
        self.name = name

    def __iadd__(self, other):
        owner.child_registry[hex(id(instance))] += set(other)
        return self

    def __isub__(self, other):
        owner.child_registry[hex(id(instance))] -= set(other)
        return self

    def remove(self, other):
        owner.child_registry[hex(id(instance))] -= set(other)
        return self

    def add(self, other):
        owner.child_registry[hex(id(instance))].add(set(other))

    def __get__(self, instance, owner):
        return owner.child_registry[hex(id(instance))]

    def __set__(self, instance, value):
        self.owner.child_registry[hex(id(instance))] = value


class PathRoot(Pathable):
    childs = Childs()
    namespace = 'ghredis'


    @property
    def parent(self):
        if self._parent:
            return Pathable
        else:
            return self.namespace + "@"

    def __path__(self):
        try:
            return Pathable.__path__(self)
        except:
            return self.namespace + "@:" + hex(id(inst))




class PathMember(Pathable):
    __metaclass__=pathtype
    def __init__(self, *args, **kwargs):
        Pathable.__init__(self,*args, **kwargs)
        self.__target__= GhReddisDict()
    def __path__(self):
        return Pathable.__path__(self)
"""


class GhRedisProperty:

    def __init__(self, fun):
        self._fun=fun
        self.name=self._fun.__name__

        self.host, self.port = os.getenv("GH_REDIS_HOST"), os.getenv("GH_REDIS_PORT")

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner
        self.path = self.owner.__path__()

    def __get__(self, inst,own):
        try:
            with GhRedisSocket(self.host, self.port) as conn:
                res=conn.qwery('get', inst.tag + ":" + self.name)
                if res:
                    return res.decode()
                else:
                    getattr(inst,'_'+ self.name)
        except:
            raise KeyError("Key Error")

    def __set__(self, inst, v):

        inst.__target__[inst]=dict(RhIterArgParser(v))

        try:
            with GhRedisSocket(self.host, self.port) as conn:
                conn.qwery('set', (inst.tag + ":" + self.name, v))
        except:
            raise KeyError("Key Error")



import json


class GhReddisDict(dict):
    def __init__(self, owner, **kwargs):

        dict.__init__(self, **kwargs)
        self.owner=owner


    def __getitem__(self, item):
        return dict.__getitem__(self, item).__get__(self)

    def __setitem__(self, k, v):
        if k in self.keys():
            gd = GhRedisProperty(v)
            gd.__set_name__(self.owner, k)
            gd.__set__(k, v)
            dict.__setitem__(self, k, gd)




