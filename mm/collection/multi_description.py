# Copyright (c) CONTEXTMACHINE
# Andrew Astkhov (sth-v) aa@contextmachine.ru
import itertools
from typing import Any, Callable, Generic, Iterable, Type, TypeVar


# Multi Getter concept.
# Simple functional and objective implementation for a generic collections getter.

# See more in original gist: https://gist.github.com/sth-v/7898cb37b9c56d11ca004936a823e366

# Functional Implementation
# -----------------------------------------------------------------------------------------------------------------------

def multi_getter(z): return lambda y: map(lambda x: getattr(x, y), z)


def multi_getitem(z): return lambda y: map(lambda x: x[y], z)


# Уместен ли здесь сеттер -- спорное утверждение. Не факт что этот метод будет пользоваться популярностью.
# Тем не менее мне хотелось бы предоставить возможность и инструмент
# для простого назначения атрибутивной строки всем элементам сразу.
# Это чем то похоже на работу с простой таблицей SQL или Excel

def multi_setter(y) -> Callable[[str, Any], None]:
    def wrap(k: str, v: Any) -> None:
        list(itertools.starmap(lambda xz, zz: setattr(xz, k, zz), zip(y, v)))

    return wrap


def multi_setitem(y) -> Callable[[str, Any], None]:
    def wrap(k: str, v: Any) -> None:
        list(itertools.starmap(lambda xz, zz: xz.__setitem__(k, zz), zip(y, v)))

    return wrap


# Class Implementation
# -----------------------------------------------------------------------------------------------------------------------

T = TypeVar("T")
Seq = TypeVar("Seq", bound=Iterable)


class CollectionItemGetter(Generic[Seq, T]):
    """
    # Multi Getter
    Simple functional and objectiv implementation for a generic collection getter.
    Example using python doctest:

    >>> from dataclasses import dataclass

    >>> @dataclass
    ... class ExampleNamespace:
    ...     foo: str
    ...     some: dict

    >>> ex1 = ExampleNamespace(foo="bar", some={"message":"hello"})
    >>> ex2 = ExampleNamespace(foo="nothing", some={"message":"github"})
    >>> exs = ex1, ex2
    >>> getter = multi_getter(exs)
    >>> list(getter("foo"))
    ['bar', 'nothing']
    >>> mg = CollectionItemGetter(exs)
    >>> mg["foo"]
    ['bar', 'nothing']
    >>> ex1.foo = "something else"
    >>> mg["foo"]
    ['something else', 'nothing']
    """

    def __init__(self, seq: Generic[Seq, T]):
        super().__init__()
        self._seq = seq
        if isinstance(seq[0], dict):
            self._getter = multi_getitem(self._seq)
        else:
            self._getter = multi_getter(self._seq)

    def __getitem__(self, k) -> Seq:
        return list(self._getter(k))


class CollectionItemGetSetter(CollectionItemGetter[Seq, T]):
    """
    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class ExampleNamespace:
    ...     foo: str
    ...     some: dict

    >>> ex1 = ExampleNamespace(foo="bar", some={"message":"hello"})
    >>> ex2 = ExampleNamespace(foo="nothing", some={"message":"github"})
    >>> exs = ex1, ex2
    >>> mg = CollectionItemGetSetter(exs)
    >>> mg["foo"]
    ['bar', 'nothing']
    >>> mg["foo"] = 'something else', 'nothing'
    >>> ex1.foo
    'something else'
    """

    def __init__(self, seq: Generic[Seq, T]):
        self._inst: Type[T] = type(seq[0])

        super().__init__(seq)
        if isinstance(seq[0], dict):
            self._setter = multi_setitem(self._seq)
        else:
            self._setter = multi_setter(self._seq)

    def __setitem__(self, key: str, value):
        # print("v")
        self._setter(key, value)


from collection.masks import Mask
import hashlib


class MultiDescriptorMask(Mask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def wrapper(mask, instance, owner, constrains,
                **kwargs):  # Strong, very strong, functional programming ... 💪🏼💪🏼💪🏼
        return lambda key: list(filter(constrains(instance[key], **kwargs), instance))  # 💄💋 By, baby


class MaskedGetSetter(CollectionItemGetSetter):
    masks = {}

    def set_mask(self, name: str, mask: Mask):
        self.__dict__[name] = mask
        mask.__set_name__(self, name)
        self.masks[name] = mask

    def get_mask(self, name):
        return self.masks[name]


class MultiDescriptor(CollectionItemGetSetter):
    """
    Common class
    """

    def __hash__(self):
        self.sha = hashlib.sha256(f"{self['__dict__']}".encode())
        return int(self.sha.hexdigest(), 36)
