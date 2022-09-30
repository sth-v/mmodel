#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

# some version control
from __future__ import annotations

import os
from abc import ABCMeta
from typing import Any

function_type = type(lambda: None)
from cxm_remote.sessions import S3Client

from mm.descriptors import HookDescriptor

from json import JSONEncoder


class DefaultFied:
    def __set_name__(self, owner, name):
        self.name = name
        self.default = owner.__default_fields__[self.name]
        self.private_name = "_" + self.name
        if self.name in owner.__annotations__.keys():
            # print(owner.mcs.types)
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


import copy


class MetaItem(ABCMeta):
    types = dict()
    tables = dict()

    def __new__(mcs, name, base, attrs, default_descriptor=DefaultFied, dict_descriptor=Dct, **kws):

        # print(attrs, "\n", kws)
        attrs["__default_fields__"] = dict()
        annotates = attrs["__annotations__"] if "__annotations__" in attrs.keys() else dict()
        attrs["__annotations__"] = annotates
        default_keys = list(annotates.keys())
        [attrs["__default_fields__"].update({k: None}) for k in default_keys]

        for k, v in attrs.items():
            seg = not isinstance(v, function_type), not isinstance(v, property), not (k[:2] == "__"), not (
                    k[:1] == "_" and not k[:2] == "__")
            if all(seg):
                # print(k)
                attrs["__default_fields__"][k] = v
                default_keys.append(k)
        for k in default_keys:
            attrs[k] = default_descriptor()
        attrs["__default_keys__"] = default_keys
        kws |= attrs
        c = super().__new__(mcs, name, base, kws)
        c._table = dict()
        mcs.tables[name] = c._table

        post_call = copy.deepcopy(c.__call__)
        post_init = copy.deepcopy(c.__init__)

        def init(slf, *args, **kwargs):
            slf.dtype = slf.__class__.__name__

            slf.default_fields = copy.deepcopy(slf.__class__.__default_fields__)
            post_init(slf, *args, **kwargs)

        def call(slf, *args, **kwargs):
            # print(args)
            argkeys = list(default_keys)[
                      :len(default_keys) if len(default_keys) < len(args) else len(args)]
            kwargs |= dict(zip(argkeys, args))

            return post_call(slf, **kwargs)

        c.__call__ = call
        c.__init__ = init
        c.dtype = name
        c.dct = dict_descriptor()
        mcs.types[name] = c
        c.mcs = mcs
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


STORAGE = os.getenv("STORAGE")
BUCKET = os.getenv("BUCKET")


class RemoteType(type):

    @classmethod
    def __prepare__(metacls, name, bases, bucket=BUCKET, prefix=None, client=S3Client,
                    default_descriptor=HookDescriptor, storage=STORAGE, **kws):

        dct = super(RemoteType, metacls).__prepare__(name, bases)
        # print(dct)

        _client = client(**kws)
        kws["prefix"] = prefix
        kws["bucket"] = bucket
        kws["storage"] = storage
        kws["default_descriptor"] = default_descriptor
        kws["client"] = _client
        table = _client.table(Prefix=prefix)

        kws["__client__"] = _client
        kws.update(dct)
        # print(table.Key)
        for k in table.Key:

            ky = k.replace(prefix, '').replace("/", '_').replace(".", '__')

            if not ky == '':
                kws[ky] = default_descriptor()
            else:
                pass
        return kws

    def __new__(mcs, classname, bases, dct, **kwds):

        # print(classname, bases, dct)
        return type(classname, bases, dct)


from json import JSONEncoder
