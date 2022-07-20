from mm.baseitems import Item
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon


class Element(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


# геометрические примитивы
class PolygonObj(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        try:
            self.vertices = args[0].tolist()
            if self.vertices[0] == self.vertices[-1]:
                del self.vertices[-1]
        except AttributeError:
            self.vertices = args[0]
            if self.vertices[0] == self.vertices[-1]:
                del self.vertices[-1]

        self.polygon = self.get_poly()
        self.polygon_lines = self.get_lines()

    def get_poly(self):
        return Polygon(self.vertices)

    def get_lines(self):
        return self.polygon.lines

    def poly_offset(self, dist):
        return offset_polygon(self.vertices, dist)






# разные типы отгибов
class BendProfile_A(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.profile = self.profile_geometry()

    def profile_geometry(self):
        return self


class BendProfile_B(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.profile = self.profile_geometry()

    def profile_geometry(self):
        return self



# Отгиб панели - профиль получается в зависимости от типа
class PanelBend(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        # пишу пока просто для общего понимания, что за тип данных будет передан в класс
        self.grid_hash = kwargs['grid_hash']  # identical for panel and bend
        self.side = kwargs['side']  # integer
        self.type = kwargs['type']  # bend type name str

        # получение профиля отгиба в зависимости от типа
        if self.type == 'A':
            self.profile = BendProfile_A().profile
        elif self.type == 'B':
            self.profile = BendProfile_B().profile


# Сама панель
class Panel(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        # пишу пока просто для общего понимания, что за тип данных будет передан в класс
        self.grid_hash = kwargs['grid_hash']  # identical for panel and bend
        self.vertices = kwargs['vertices']  # фактическое положение вершин

        #self.perforation = kwargs['perforation']

    # линия офсета от панели в осях, внешний край загиба (до радиуса)
    def panel_outer_bend_line(self):
        dist = 7.5  # may be changed
        frame = PolygonObj(self.vertices)
        print(frame)
        return frame.poly_offset(dist)


b = Panel(grid_hash='1234', vertices = [[-1383.220328, 1499.49728, -160.132],
[-882.411001, 2121.091646, 186.82],
[-448.874568, 1451.682329, -186.82],[-1383.220328, 1499.49728, -160.132]
])
print(b.panel_outer_bend_line())