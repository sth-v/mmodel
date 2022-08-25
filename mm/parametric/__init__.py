#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

from mm.baseitems import Base, Item, DictableItem
from typing import TypeVar
import numpy as np

import compas
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
        return x,y


class ParametricEquation(Base, ChildItem):
    ...


class Cone(ParametricEquation):
    def __call__(self, *args, **kwargs):
        ...
