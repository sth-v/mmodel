from meta import Mmodel, BaseItem
from utils.utils import *



class MmodelProject(Mmodel):
    def __init__(self, fp):
        super().__init__(fp)
        BaseItem.__mmodel__ = self

    def api_kwargs_example(self, **kwargs):
        arg_dict = self.roofshapes.__dict__
        if kwargs is not None:
            for k in ['outlines', 'pointgrid']:
                if k in kwargs.keys():
                    arg_dict[k] = kwargs[k]

        return arg_dict

    def estimate_plane_collisions(self, bounds=(450, 1000), **kwargs):

        multipolygon = self.roofshapes.__multipolygon__
        labels = []
        arg_dict = copy.deepcopy(self.roofshapes.__dict__)
        arg_dict |= kwargs

        pointgrid = list(np_to_shapely_points(arg_dict['pointgrid']))

        for pt in pointgrid:
            if pt.within(multipolygon):
                first_list = []
                if multipolygon.overlaps(pt.buffer(bounds[0])):
                    labels.append(1)
                    continue
                else:
                    labels.append(0)
                    continue
            else:
                second_list = []
                for i in range(len(bounds)):
                    if multipolygon.overlaps(pt.buffer(bounds[i])):
                        second_list.append(i + 2)
                        break
                    else:
                        second_list.append(len(bounds) + 2)
                        continue
                labels.append(min(second_list))

        ans = {'labels': labels, 'bounds': bounds}
        ans |= arg_dict

        return ans

    def get_column_axis(self, **kwargs):
        arg_dict = copy.deepcopy(self.roofshapes.__dict__)
        arg_dict |= kwargs
        pointgrid = list(np_to_shapely_points(arg_dict['pointgrid']))
        point_pairs = []
        low_polygons = list(np_to_shapely_polygons_z(self.zmask.low, z=0))
        high_polygons = list(np_to_shapely_polygons_z(self.zmask.high, z=0))
        z_low = extract_polygon_z(self.zmask.low)
        z_high = extract_polygon_z(self.zmask.high)

        for l in low_polygons:
            for h in high_polygons:
                for p in pointgrid:
                    if l.contains(p) and h.contains(p):

                        p_low = [p.x, p.y, int(z_low[low_polygons.index(l)])]
                        p_high = [p.x, p.y, int(z_high[high_polygons.index(h)])]
                        point_pairs.append([p_low, p_high])
                    else:
                        pass

        ans = {'column_axis': point_pairs}
        ans |= {'zmask': self.zmask.__dict__}
        return ans


mmodel = MmodelProject(fp='config.json')


class Grid(metaclass=BaseItem):
    load = 'version'


class RoofShapes(metaclass=BaseItem):
    load = 'version'

    def multipolygon(self):
        mpolygon = list(np_to_shapely_polygons(self.outlines))[0]
        outlines = list(np_to_shapely_polygons(self.outlines))
        for i in outlines:
            if i.is_valid:
                mpolygon = mpolygon.difference(i)
            else:
                print(outlines.index(i))
        setattr(self, '__multipolygon__', mpolygon)


class ZMask(metaclass=BaseItem):
    load = 'version'


class SberLogo(metaclass=BaseItem):
    load = 'version'
    rhino = ['simple', 'crv']


class Rail(metaclass=BaseItem):
    load = 'version'
    rhino = ['profile']


class Rails(metaclass=BaseItem):
    load = 'version'
    rhino = []


Grid()
RoofShapes().multipolygon()
ZMask()
SberLogo()
Rail(), Rails()
