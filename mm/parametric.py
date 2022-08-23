from mm.baseitems import Base, DictableItem
from typing import TypeVar, Type

ChildItem = TypeVar("ChildItem", bound=DictableItem)

class ParamPoint(DictableItem):
    fields = dict(x=0, y=0)

    format_spec = "x", "y"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, x=0, y=0, **kwargs):
        super().__call__(**kwargs)
        self.x=x
        self.y=y


class ParametricEquation(Base, ChildItem):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.child=ChildItem(**kwargs)

    def __call__(self, *args, **kwargs) -> ChildItem:

        super(ParametricEquation, self).__call__(**kwargs)

        self.child.__call__(*args)





class Cone(ParametricEquation):
    def __call__(self, *args, **kwargs):
        ...
