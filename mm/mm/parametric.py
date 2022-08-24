from mm.mm.baseitems import Base, Item, DictableItem
from mm.mm.item_collections import BaseCollection
from typing import TypeVar, Type, Iterable, Union, Any
import numpy as np
from numpy import ndarray
from mm.mm.geom import Point

ChildItem = TypeVar("ChildItem", bound=DictableItem)


class AbstractParametricFunction(Item):

    def _evaluate(self, t):
        ...


class Circle(Item):
    x0 = 0.0
    y0 = 0.0
    r = 1.0

    def evaluate(self, t):
        x = self.x0 + self.r * np.cos(t)
        y = self.y0 + self.r * np.sin(t)
        return Point(x=x, y=y)


class ParametricEquation(Base, ChildItem):
    ...


class Cone(ParametricEquation):
    def __call__(self, *args, **kwargs):
        ...
