#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction process"
import copy
import json
from abc import ABCMeta, abstractmethod

import numpy as np
import requests

from mm.baseitems import Base, DictableItem, Item


class AbstractParametricFunction(Item):

    def evaluate(self, t):
        ...


class SimpleCircle(DictableItem):
    x0 = 0.0
    y0 = 0.0
    r = 1.0

    def evaluate(self, t):
        x = self.x0 + self.r * np.cos(t)
        y = self.y0 + self.r * np.sin(t)
        return x, y


class PrmGenerator(AbstractParametricFunction, metaclass=ABCMeta):
    stop = 2 * np.pi
    start = 0.0

    def __init__(self, *args, **kwargs):
        self._step = None
        super().__init__(*args, **kwargs)
        self.si = self.start




    @abstractmethod
    def evaluate(self, t):
        ...

    def __call__(self, step=None, **kwargs):

        super().__call__(**kwargs)
        self.step = step
        self.si = self.start

    def __iter__(self):
        return self

    def __next__(self):

        if self.si <= self.stop + 0.001:
            print(self.si, self.start, self.stop, self.step)
            t = copy.deepcopy(self.si)
            self.si += self.step
            return self.evaluate(t)
        else:
            raise StopIteration

    def __getitem__(self, item: slice):

        if isinstance(item, (float, int)):

            return self.evaluate(item)

        elif isinstance(item, slice):
            slf = copy.deepcopy(self)
            slf.__call__(start=item.start, stop=item.stop, step=item.step)

            return slf

    @abstractmethod
    def __repr__(self):
        ...

    @property
    def step(self):

        return self._step

    @step.setter
    def step(self, val):

        self._step = val


class ParametricType(PrmGenerator):

    @property
    def parameterisation(self):
        l = []
        for base in self.__class__.__bases__:
            if issubclass(base, ParametricType):
                l.append(base)
        return l

    def __format__(self, *format_spec):
        nm, literal = format_spec
        l = f"(parameterisation: Base "
        for base in self.parameterisation:
            l += f"-> {base.__name__}"

        return l + f" -> ({literal}))"


class Linear(ParametricType):
    a = 1.0
    b = 0.0

    def __format__(self, *format_spec):
        a, b = format_spec

        return f"{self.__class__.__name__}(a={a}, b={b})" + super().__format__("Linear",
                                                                               "Ax + By + Cz + D= 0")

    def __repr__(self):
        return self.__format__(self.a, self.b)


class Circular(ParametricType):
    stop = 2 * np.pi
    start = 0.0
    x0 = 0.0
    y0 = 0.0

    r = 1.0

    def __format__(self, *format_spec):
        r, x, y = format_spec

        return f"{self.__class__.__name__}(r={r}, x0={x}, y0={y})" + super().__format__("Circular",
                                                                                        "Ax^2 + By^2 + Cx + Dy + F = 0")

    def __repr__(self):
        return self.__format__(self.r, self.x0, self.y0)


class Quadratic(ParametricType):
    stop = 1 * np.pi
    start = -1 * np.pi
    x0 = 0.0
    y0 = 0.0

    a = 1
    b = 1

    def __format__(self, *format_spec):
        a, b, x, y = format_spec
        return f"{self.__class__.__name__}(a={a}, b={b}, x0={x}, y0={y}))" + super(
            Quadratic, self).__format__("Quadratic", "Ax^2 + By^2 + Cz^2 + Dx + Fy + Iz + J = 0")

    def __repr__(self):
        return self.__format__(self.a, self.b, self.x0, self.y0)


class ClassicLinear(Linear):
    x0 = 0.0
    y0 = 0.0
    a = 1.0
    b = 0.0

    def evaluate(self, t):
        x = self.x0 + self.a * t
        y = self.y0 + self.b * t
        return x, y


class Circle(Circular):
    r = 1.0

    def evaluate(self, t):
        x = self.x0 + self.r * np.cos(t)
        y = self.y0 + self.r * np.sin(t)
        return x, y


class Ellipse(Quadratic):
    a = 1
    b = 1

    def evaluate(self, t):
        x = self.x0 + self.a * np.cos(t)
        y = self.y0 + self.b * np.sin(t)
        return x, y


class Hyperbola(Quadratic):
    """
    The equation is y2 / a2 − x2 / b2 = 1,
    where the asymptotes of the hyperbola are x = [b / a] * y and x = [−b / a] * y.
    """
    a = 1
    b = 1

    def evaluate(self, t):
        x = self.x0 + self.a * np.cosh(t)
        y = self.y0 + self.b * np.sinh(t)
        return x, y


class ParametricEquation(Base):
    ...


class Cone(ParametricEquation):
    def __call__(self, *args, **kwargs):
        ...


