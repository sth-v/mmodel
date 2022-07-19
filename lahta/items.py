from mm.baseitems import Item
from compas.geometry import Point, Polygon

class Element(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


class Panel(Item):
    # __init__ нужен только когда требуется задать специфический порядок первой инициализации
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.vertices = kwargs['vertices']
        self.perforation = kwargs['perforation']

    def panel_shape(self):
        return Polygon(self.vertices)

    @property
    def perforation(self):
        return self._perforation

    @property
    def hole(self):
        self.hole = 5
        return self.hole

    # для того чтобы пометить дырку, нужно получить объект пересекающийся с панелью (возможно от другого класса)
    @hole.setter
    def hole(self, value):
        self._hole = value

    @perforation.setter
    def perforation(self, value):
        self._perforation = value
