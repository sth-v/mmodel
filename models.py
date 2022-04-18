from vcs import Mmodel, BaseItem
from utils.utils import *


class MmodelProject(Mmodel):
    def __init__(self, fp):
        super().__init__(fp)

        self.__ptc = o3d.io.read_point_cloud(self.ptc_root)
        self.ptc = {
            'points': np.asarray(self.__ptc.points).tolist(),
            'colors': np.asarray(self.__ptc.colors).tolist(),
            'normals': np.asarray(self.__ptc.normals).tolist()
        }

    def api_kwargs_example(self, **kwargs):
        arg_dict = self.roofshapes.__dict__
        if kwargs is not None:
            for k in ['outlines', 'pointgrid']:
                if k in kwargs.keys():
                    arg_dict[k] = kwargs[k]

        return arg_dict

    def estimate_plane_collisions(self, bounds=[300, 1000], **kwargs):

        outlines = list(np_to_shapely_polygons(self.roofshapes.outlines))
        labels = []
        arg_dict = self.roofshapes.__dict__
        if kwargs is not None:
            for k in ['pointgrid']:
                if k in kwargs.keys():
                    arg_dict[k] = kwargs[k]
        pointgrid = list(np_to_shapely_points(arg_dict['pointgrid']))

        for pt in pointgrid:
            first_list = []
            for polygon in outlines:
                if pt.within(polygon):
                    l = []
                    for i in range(len(bounds)):
                        if polygon.overlaps(pt.buffer(bounds[i])):
                            l.append(i + 2)
                            continue
                        else:
                            l.append(len(bounds) + 2)
                    first_list.append(min(l))
                    continue
                elif polygon.overlaps(pt.buffer(bounds[0])):
                    first_list.append(1)
                    continue
                else:
                    first_list.append(0)
            f_list = set(first_list)
            labels.append(max(f_list))

        return labels


mmodel = MmodelProject(fp='config.json')


class Grid(metaclass=BaseItem):
    load = 'version'
    mmodel = MmodelProject


class RoofShapes(metaclass=BaseItem):
    load = 'version'
    mmodel = MmodelProject


Grid()
RoofShapes()
