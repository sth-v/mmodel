#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
from __future__ import annotations

import copy
import itertools
from abc import ABC, abstractmethod

from collections.abc import Iterator
from functools import partial, wraps
from typing import Any, Callable, Generator, Iterable
import inspect

import numpy as np

from mm.baseitems import BaseItem, Item, ArgsItem


def t(glb):
    for i, kv in enumerate(glb.items()):
        k, v = kv

        yield i, k


def clsmap(seq, item):
    cls = seq[0].__class__
    cls_attr = getattr(cls, item)
    print(f"Target <{item}> is <{cls.__name__}>'s method or base attribute ...")
    if inspect.ismethod(cls_attr):
        print("It is method!")

        @wraps(cls_attr)
        def wrp(args, **kwargs):
            for i, slf in enumerate(cls.seq):
                arg = args[i]
                f = getattr(slf, item)
                print(f"Start yielding ...\nwith seq[{i}] yield {slf.__repr__()}.{item}(args={arg}, kwargs={kwargs})")

                try:
                    kw = dict(arg)
                    kw |= kwargs
                    yield f(**kw)
                finally:
                    yield f(*arg, **kwargs)
            return wrp
    else:
        raise "It is not method"


class BaseCollection(Item, Iterator):
    def __init__(self, seq, *args, **kwargs):
        try:
            iter(seq)
            self.seq = seq
        except:
            self.seq = [seq]
        self.item_dtype = seq[0].__class__
        super().__init__(*args, seq=seq, **kwargs)
        self._i = -1

    def reload(self):
        self._i = -1

    @property
    def state(self):
        return self._i

    def __iter__(self):
        return self

    def __call__(self, *args, **kwargs):
        super(BaseCollection, self).__call__(*args, **kwargs)
        self.item_dtype = self.seq[0].__class__

    def get(self, key):
        return self.seq[key]

    def __getattr__(self, item):
        try:
            cls_attr = getattr(self.item_dtype, item)
            print(f"Target <{item}> is <{self.item_dtype.__name__}>'s method or base attribute ...")
            if inspect.ismethod(cls_attr):
                print("It is method!")

                @wraps(cls_attr)
                def wrp(args, **kwargs):
                    for i, slf in enumerate(self.seq):
                        arg = args[i]
                        f = getattr(slf, item)
                        print(
                            f"Start yielding ...\nwith {self.uid}[{i}] yield {slf.__repr__()}.{item}(args={arg}, kwargs={kwargs})")

                        try:
                            kw = dict(arg)
                            kw |= kwargs
                            yield f(**kw)
                        finally:
                            yield f(*arg, **kwargs)
                    return wrp


            else:
                print(f"it is base attribute")
                for itm in self.seq:
                    yield getattr(itm, item)
        finally:
            print(
                f"WARN!  Вызываемый аттрибут <{item}> не является обязательным для типа коллекции <{self.item_dtype.__name__}> ."
                "У некоторых элементов он может отсутствовать. В этом случае будет сгенерирован None .")
            for itm in self.seq:
                try:
                    g = getattr(itm, item)
                    yield g
                except:

                    yield None

    def __setattr__(self, k, v):
        for i, itm in enumerate(self):
            setattr(itm, k, v[i])

    def call_item(self, args, **kwargs):
        """Safe call the __call__ method piecewise.
            Pass a list of private arguments to the args, common arguments can be passed as **kwargs."""
        return (item.__call__(args[i], **kwargs) for i, item in enumerate(self.seq))

    def __delitem__(self, key):
        del self.seq[key]

    def __getitem__(self, key):
        return self.seq[key]

    def __setitem__(self, key, value):
        self.seq[key] = value

    def __len__(self):
        return len(self.seq)

    def __next__(self):
        self._i += 1
        if len(self) > self._i:
            return self.seq[self._i]
        else:
            raise StopIteration

    def _fmt(self, prf, pfx, form="({})"):
        bs = "".join([f"{x[0]}={x[1]}" for x in self.__dict__.items()])
        return prf + form.format(bs) + form.format(pfx)

    def __str__(self):
        self._fmt(self.dtype, self.state, form=self.seq)
        return f"{self.dtype}({self.state} in {self.seq})"

    def __repr__(self):
        return f"<{self.dtype}({self.state} in {self.seq}) at {self.uid}>"


class _ItemCollection(Iterator):
    def __next__(self):
        pass

    target = ArgsItem

    def __init__(self, *args, **kwargs):
        ...


class _AbstractItemCollection(Iterator):
    target = None

    def __init__(self, *args, **kwargs):
        super(_AbstractItemCollection, self).__init__(**kwargs)
        self._i = 0

        self._collection = list(map(lambda x: self.target(**dict(x)), args))

        # map(lambda x: self.target(**dict(x)), args, seq if self._collection is None else self._collection)

    def __len__(self):
        return len(self._collection)

    def __iter__(self):
        return self

    def __call__(self, *args, **kwargs):
        self.collection_keys = dict(args[0])
        self._collection = list(map(lambda x, y: x(**dict(y)), self._collection, args))
        return self

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._collection[slice(item)]
        else:
            return self._collection[item]

    def __setitem__(self, item, val):
        if isinstance(item, slice):
            self._collection[slice(item)] = val
        else:
            self._collection[item] = val

    def __delitem__(self, item):
        del self._collection[item]

    def __next__(self):
        if self._i < len(self._collection):
            yield self.__getitem__(self._i)
            self._i += 1
        else:
            raise StopIteration


class _AttrHandlerCollection(_AbstractItemCollection):
    attrs_handler: Any

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.attrs_handler.collection = self

    def __getitem__(self, key):
        if isinstance(key, str):

            return list(map(lambda x: getattr(x, key), self._collection))
        elif isinstance(key, int):
            return self._collection[key]
        else:
            return getattr(self[key[1]], key[0])


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
    target = ArgsItem


class NamedNumericCollection(BaseItem):
    def __init__(self, arg, *args, **kwargs):
        self._i = -1
        print(arg, args)
        try:
            iter(arg)

            arg_ = arg
        except:
            arg_ = (arg,)

        if len(args) == 0:

            args_ = arg_


        else:

            args_ = arg_ + args
        super().__init__(*args_, **kwargs)

    def __setitem__(self, i, v):
        setattr(self, self.__default_keys__[i], v)

    def __iter__(self):
        return self

    def __next__(self):
        self._i += 1
        if self._i < len(self.__array__()):
            return self.__array__()[self._i]
        else:
            raise StopIteration

    def __array__(self, *args, **kwargs) -> np.ndarray:
        return np.asarray(list(self.default_fields.values))

    def __getitem__(self, i):
        return self.__array__()[i]


class AbstractPropertyCollection:
    shape: tuple[int]

    def __init__(self, func):
        super().__init__()
        self.func = func

    def __get__(self, obj, owner) -> object:
        return np.asarray(self.vectorize(obj, owner)).reshape(obj.shape).tolist()

    @abstractmethod
    def vectorize(self, obj, owner) -> Iterable:
        ...


class AbstractPropertyGenerator(AbstractPropertyCollection):

    def __get__(self, obj, owner) -> Generator:
        return self.vectorize(obj, owner)

    @abstractmethod
    def vectorize(self, obj, owner) -> Generator:
        ...


class AbstractMethodCollection(AbstractPropertyCollection):

    def __get__(self, obj, owner) -> Callable:
        @wraps(self.func)
        def wrap(*args, **kwargs):
            return np.asarray(list(map(lambda x, y: x(y, **kwargs), self.vectorize(obj, owner), args))).reshape(
                obj.shape).tolist()

        return wrap

    @abstractmethod
    def vectorize(self, obj, owner) -> Generator[partial]:
        ...


class GridPropertyCollection(AbstractMethodCollection):

    def vectorize(self, obj, owner) -> Generator[partial]:
        a, b, = obj.shape
        lst = []
        for i in range(a):
            for j in range(b):
                obj[i, j].ij=(i, j)

                lst.append(self.func(obj[i, j], owner))
        return lst


class GridPropertyGenerator(AbstractPropertyGenerator):

    def vectorize(self, obj, owner) -> Generator:
        a, b, = obj.shape

        for i in range(a):
            for j in range(b):
                obj[i, j].ij=(i, j)

                yield self.func(obj[i, j], owner)


class GridCollectionMethod(AbstractPropertyGenerator):
    shape: tuple[int, int]

    def vectorize(self, obj, owner) -> Generator:
        a, b, = obj.shape
        for i in range(a):
            for j in range(b):
                obj[i, j].ij = i, j
                yield partial(self.func, obj.iterable[i, j], owner)


def array_traversal(fun, ij, itr):
    # print(itr)

    for i in range(len(itr)):
        ijj = copy.deepcopy(ij)
        ijj.append(i)
        try:
            yield list(array_traversal(fun, ijj, itr[i]))



        except:
            itr[i].ij=ijj

            yield fun.fget(itr[i])



def partial_traversal(fun, ij, itr):
    # print(itr)

    for i in range(len(itr)):
        ijj = copy.deepcopy(ij)
        ijj.append(i)
        try:
            yield list(array_traversal(fun, ijj, itr[i]))



        finally:
            itr[i].ij=ijj

            yield partial(fun, itr[i])



class CollectionProperty(AbstractPropertyGenerator):
    root = [0]

    def vectorize(self, obj, owner) -> Any:
        return list(array_traversal(self.func, self.root, obj.iterable))


class CollectionMethod(AbstractMethodCollection):
    root = [0]

    def vectorize(self, obj, owner) -> Any:
        return itertools.chain(*partial_traversal(self.func, self.root, obj.iterable))


from typing import TypeVar

IT = TypeVar("IT", bound=Item)


class ItemCollectionProto(Iterable[IT]):
    source = IT

    def __init__(self, iterable: Iterable[IT] | Any | None = (), **kwargs):
        self.source_methods()
        self.source_method_descriptors()
        self.source_data_descriptors()
        super().__init__(**kwargs)

        self._iterable = np.asarray(iterable)

    def __list__(self):
        return self.iterable.tolist()

    def __len__(self):
        return len(self.iterable)

    def __iter__(self):
        return self

    def __generate_descriptors__(self):
        print(self.source_methods())
        print(self.source_method_descriptors())
        print(self.source_data_descriptors())

    @classmethod
    def source_data_descriptors(cls):
        d = []
        for name, m in inspect.getmembers(
                cls.source,
                lambda x: inspect.isdatadescriptor(x) | inspect.isgetsetdescriptor(x)):
            if name[0] != "_":
                setattr(cls, name, CollectionProperty(m))
                d.append(cls.__dict__[name])
        return d

    @classmethod
    def source_method_descriptors(cls):
        d = []
        for name, m in inspect.getmembers(
                cls.source,
                lambda x: inspect.ismemberdescriptor(x)):
            if name[0] != "_":
                setattr(cls, name, CollectionMethod(m))
                d.append(cls.__dict__[name])

        return d

    @classmethod
    def source_methods(cls):
        d = []
        for name, m in inspect.getmembers(cls.source,
                                          lambda x: inspect.ismethod(x)):
            print(name, m)
            if name != "_":
                setattr(cls, name, CollectionMethod(m))
                d.append(cls.__dict__[name])
        return d

    def __getitem__(self, item) -> Iterable[IT] | IT:
        return self.iterable.__getitem__(item)

    def __setitem__(self, item, v) -> Iterable[IT] | IT:
        self.iterable.__setitem__(item, v)




    def append(self, v):
        lst = self.__list__()
        lst.append(v)

        self.iterable = lst

    @property
    def shape(self):
        return self.iterable.shape

    def __array__(self):
        return self.iterable

    @property
    def iterable(self):
        return self._iterable

    @iterable.setter
    def iterable(self, v: np.ndarray | list | Iterable):
        self._iterable = np.asarray(v)
