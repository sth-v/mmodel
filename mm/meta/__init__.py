#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

# some version control
from __future__ import annotations

import inspect
import itertools
from abc import ABCMeta
from functools import partial
from typing import Any, Callable, Optional

function_type = type(lambda: None)
from cxm_remote.sessions import S3Client

from mm.descriptors import HookDescriptor

from json import JSONEncoder


class CallBind(Callable):
    def __init__(self, func):
        self.__func__ = func

    def __set_name__(self, owner, name="__call__"):
        owner.__call__ = self
        self.name = name
        self.owner = owner

    def __call__(self, instance, owner, *args, **kwargs):

        args = list(args)
        for name in owner.__defaults__.names:
            if len(args) == 0:
                break
            else:
                owner.__defaults__[name] = args.pop()

        kwargs |= owner.__defaults__.dct
        return self.__func__(instance, **kwargs)

    def __get__(self, instance, owner):

        return partial(self.__call__, instance, owner)


class ItemCall(CallBind):
    def __init__(self):
        def func(instance, **kwargs):
            instance.__dict__ |= kwargs
            return instance

        super().__init__(func)


class DefaultFied:
    def __set_name__(self, owner, name):
        self.name = name
        self.default = owner.__default_fields__[self.name]
        self.private_name = "_" + self.name
        if self.name in owner.__annotations__.keys():
            print(owner.mcs.types)
            self.hint = owner.__annotations__[self.name]
        else:
            self.hint = Any

    def __get__(self, obj, objtype=None):

        return obj.default_fields[self.name]

    def __set__(self, obj, value):
        if self.validate(value):

            obj.default_fields[self.name] = value

        else:
            try:
                obj.default_fields[self.name] = self.hint(value)
            except:
                raise ValueError

    def validate(self, value):
        if self.hint is Any:
            return True
        else:
            if isinstance(value, self.hint):
                return True
            else:
                return False


class Dct(dict):
    exclude = ["default_fields", "encoder"]
    metadata = ["uid"]

    def __get__(self, obj, objtype=None):
        dct = dict()

        dct |= obj.default_fields
        dct_ = dict()

        self.trav(obj.default_fields, dct_, obj=obj)

        dct_['metadata'] = dict()
        for k in self.metadata:
            dct_['metadata'][k] = getattr(obj, k)
        self.trav(obj.__dict__, dct_['metadata'], obj=obj)
        return dct_

    def trav(self, dct, dct_, obj):
        for k, v in dct.items():
            if k in self.exclude:
                continue
            else:
                if hasattr(v, "dct"):
                    newdict = dict()
                    dct_[k] = newdict

                    self.trav(v.dct, newdict, obj=obj)


                else:
                    dct_[k] = v


class CallBinder:

    def __get__(self, instance, owner):
        def callwrapper(*args, **kwargs):
            d = dict(zip(owner.__default__.names[:len(args)], args))
            d |= kwargs
            return owner.__call(instance, **d)

        return callwrapper


class DF:
    def __init__(self, k, v=None):
        self.name = k
        self.default_name = k
        self.default_value = v
        self.value = v


class DFc(dict):
    def __init__(self):
        self._i = -1
        self._default_names = []

    def append(self, field: DF):
        if field.default_name not in self.names:
            self._default_names.append(field.default_name)
        dict.__setitem__(self, field.default_name, field.default_value)

    def __setitem__(self, k: str, v: Optional[Any] = None):
        if k not in self.names:
            self._default_names.append(k)

        dict.__setitem__(self, k, v)

    def __getitem__(self, name):
        return dict.__getitem__(self, name)

    @property
    def names(self):
        return self._default_names

    @property
    def values(self):
        return list(dict(self).values())

    @property
    def fields(self):
        return list(itertools.starmap(DF, zip(self.names, self.values)))

    @property
    def items(self):
        return list(zip(self.names, self.values))

    @property
    def dct(self):
        return dict(zip(self.names, self.values))

    def __iter__(self):
        return self

    def __next__(self):
        self._i += 1
        if self._i < len(self.names):
            return self.fields[self._i]
        else:
            raise StopIteration


class DFDescriptor:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):

        if isinstance(owner.__defaults__[self.name], property):
            return owner.__defaults__[self.name]
        elif instance is None:
            return owner.__defaults__[self.name]
        else:
            return instance.__dict__[self.name]

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value


class MetaItem(ABCMeta):
    types = dict()
    tables = dict()

    def __new__(mcs, name, base, attrs, default_descriptor=DefaultFied, dict_descriptor=Dct, **kws):
        print(attrs, "\n", kws)
        attrs |= dict(dtype=name)
        try:
            attrs["__call__"] = CallBind(attrs["__call__"])
        except:
            attrs["__call__"] = ItemCall()
        kws['mcs'] = mcs
        kws |= attrs
        c = super().__new__(mcs, name, base, kws)

        c.__defaults__ = DFc()

        for k, v in attrs.items():
            if (not inspect.ismethod(v)) and (not (k[0] == "_")):
                try:

                    c.__defaults__.append(DF(k, c.__annotations__[k]()))
                except:
                    c.__defaults__.append(DF(k, v))
                d = DFDescriptor()
                d.__set_name__(c, k)
                setattr(c, k, d)

            else:
                continue
        print(c.__dict__)
        print(c.__defaults__)

        mcs.types[name] = c
        return c


class ItemEncoder(JSONEncoder):

    def __init__(self, *, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, sort_keys=False,
                 indent=None, separators=None, default=None):
        """Constructor for JSONEncoder, with sensible defaults.

            If skipkeys is false, then it is a TypeError to attempt
            encoding of keys that are not str, int, float or None.  If
            skipkeys is True, such items are simply skipped.

            If ensure_ascii is true, the output is guaranteed to be str
            objects with all incoming non-ASCII characters escaped.  If
            ensure_ascii is false, the output can contain non-ASCII characters.

            If check_circular is true, then lists, dicts, and custom encoded
            objects will be checked for circular references during encoding to
            prevent an infinite recursion (which would cause an RecursionError).
            Otherwise, no such check takes place.

            If allow_nan is true, then NaN, Infinity, and -Infinity will be
            encoded as such.  This behavior is not JSON specification compliant,
            but is consistent with most JavaScript based encoders and decoders.
            Otherwise, it will be a ValueError to encode such floats.

            If sort_keys is true, then the output of dictionaries will be
            sorted by key; this is useful for regression tests to ensure
            that JSON serializations can be compared on a day-to-day basis.

            If indent is a non-negative integer, then JSON array
            elements and object members will be pretty-printed with that
            indent level.  An indent level of 0 will only insert newlines.
            None is the most compact representation.

            If specified, separators should be an (item_separator, key_separator)
            tuple.  The default is (', ', ': ') if *indent* is ``None`` and
            (',', ': ') otherwise.  To get the most compact JSON representation,
            you should specify (',', ':') to eliminate whitespace.

            If specified, default is a function that gets called for objects
            that can't otherwise be serialized.  It should return a JSON encodable
            version of the object or raise a ``TypeError``.

            """

        super().__init__(skipkeys=skipkeys, ensure_ascii=ensure_ascii, check_circular=check_circular,
                         allow_nan=allow_nan, sort_keys=sort_keys, indent=indent, separators=separators,
                         default=default)

    def default(self, o):
        """Implement this method in a subclass such that it returns
            a serializable object for ``o``, or calls the base implementation
            (to raise a ``TypeError``).

            For example, to support arbitrary iterators, you could
            implement default like this::

                def default(self, o):
                    try:
                        iterable = iter(o)
                    except TypeError:
                        pass
                    else:
                        return list(iterable)
                    # Let the base class default method raise the TypeError
                    return JSONEncoder.default(self, o)

            """
        if hasattr(o, "dct"):
            return o.dct
        else:
            return JSONEncoder.default(self, o)


class BufferDescriptor(dict):
    exclude = ["default_fields", "encoder"]
    metadata = ["uid", "dtype"]

    def __get__(self, obj, objtype=None):
        dct = dict()

        dct |= obj.__class__.table[obj.uid]
        dct['metadata'] = dict()
        for k in self.metadata:
            dct['metadata'][k] = getattr(obj, k)

        return dct

    def __set__(self, instance, value):
        instance.__class__.table[instance.uid] = value


class RemoteType(type):

    @classmethod
    def __prepare__(metacls, name, bases, prefix=None, client=S3Client, default_descriptor=HookDescriptor, **kws):
        dct = super(RemoteType, metacls).__prepare__(name, bases)
        print(dct)

        _client = client(**kws)
        kws["prefix"] = prefix

        table = _client.table(Prefix=prefix)
        kws["__client__"] = _client
        kws.update(dct)
        print(table.Key)
        for k in table.Key:
            ky = k.replace(prefix, '')
            if not ky == '':
                kws[ky] = default_descriptor()
            else:
                pass
        return kws

    def __new__(mcs, classname, bases, dct, **kwds):

        print(classname, bases, dct)
        return type(classname, bases, dct)


from json import JSONEncoder


class member_table(dict):
    def __init__(self):
        self.members = []
        self.methods = []

    def __setitem__(self, key, value: list[Any]):
        # if the key is not already defined, add to the
        # list of keys.

        ml = []
        for m, v in zip(self.members, value):
            setattr(m, key, v)

            ml.append(getattr(m, key))
            dict.__setitem__(self, m, {key: ml})

    def __getitem__(self, item):
        for m in self.members:
            yield getattr(m, item)

    def reload(self):
        del self.names_irerator
        self.names_irerator()

    def __setattr__(self, key, value):
        self[next(self.names_irerator)[self]].__setattr__(key, value)
        print(key, value)

    def __getattr__(self, k):
        return self[next(self.names_irerator)[self]].__getattr__(k)
