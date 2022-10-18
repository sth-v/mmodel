#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

from __future__ import annotations

import copy
import inspect
import math
from itertools import *

import numpy as np
import rhino3dm
from numpy import ndarray
from rhino3dm import File3dm
from shapely.geometry import Point, Polygon


def np_to_shapely_points(arr):
    for a in arr:
        yield Point(a[0], a[1])


def np_to_shapely_polygons(arr):
    for a in arr:
        poly = []
        for pt in a:
            poly.append([pt[0], pt[1]])
        yield Polygon(poly)


# imports/exports

def int_formatter(val: int):
    if int(str(val), 10) in range(9):
        return '0' + str(val)


def np_to_shapely_polygons_z(arr, z=None):
    for a in arr:
        poly = []
        for pt in a:
            if z is not None:
                poly.append([pt[0], pt[1], z])
            else:
                poly.append([pt[0], pt[1], pt[2]])

        yield Polygon(poly)


def extract_polygon_z(arr):
    vals = []
    for polygon in arr:
        vals.append(np.unique(np.asarray(polygon)[..., 2])[0])
    return vals


def create_set(iterable):
    s = set()
    for i in iterable:
        s.add(i)
    return s


def zip_transpose(zipped):
    return zip(*zipped)


def filterf_(zipper):
    # unz=list(zipper)
    # # print(unz)
    # dct = dict(unz)
    # rint(dct.keys())
    keys_ = []
    vals_ = []
    for k, v in zipper:
        if k in keys_:
            i = keys_.index(k)
            vals_[i].append(v)
        else:
            keys_.append(k)
            # # print(f'key append {k}')
            vals_.append([v])
    return [keys_, vals_]


def oo(n):
    for i in inspect.getmembers(n):

        # to remove private and protected
        # functions
        if not i[0].startswith('_'):
            # To remove other methods that
            # doesnot start with a underscore

            # print(i)
            yield i


class RhLinked(type):
    def __new__(mcs, classname: str, file: str | File3dm, childnames=lambda x: getattr(x, "Name"), **attrs):
        classes_ = {}
        if type(file) == str:
            fl = rhino3dm.File3dm.Read(file)

        if type(file) == File3dm:
            fl = file

        classes_ |= {'file': fl}

        def n_init(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        objcts = fl.Objects
        # objct = rhino3dm.File3dmObject
        childset = set()
        i_l = []
        for objct in objcts:
            # print(objct)
            # attr_dict = objct.Attributes
            i_dict = dict(objct.Geometry.GetUserStrings())

            i_dict |= {'geometry': objct.Geometry}

            i_dict |= {'geometry': objct.Geometry}
            chn = childnames(objct)

            attr_dict = {}
            i_dict |= dict(oo(objct.Attributes))
            for k in i_dict.keys():
                attr_dict[k] = None

            attr_dict |= {'instance_attrs': []}
            # print(attr_dict)
            childset.add(chn)
            rh_mdl_cls = type(chn, (object,), attr_dict)

            i_dict |= {'__init__': n_init}

            i_l.append((chn, i_dict))
            classes_ |= {chn: rh_mdl_cls}
        for ch in childset:
            classes_ |= {ch + '_objects': []}
        # rh_cls = type(k, (object,), classes_)
        # classes |= {k: rh_cls}
        classes_ |= {'__childnames__': childset}
        for nm, at in i_l:
            # print(at)
            if nm in childset:
                # print(nm + '_objects')
                # print(at)
                cl = classes_[nm]
                o = cl()
                for k, v in at.items():
                    setattr(o, k, v)
                classes_[nm + '_objects'].append(o)

        classes_ |= attrs

        return type(classname, (object,), classes_)


def shortest_distance(x1, y1, z1, a, b, c, d):
    d = abs((a * x1 + b * y1 + c * z1 + d))
    e = (math.sqrt(a * a + b * b + c * c))
    # print("Perpendicular distance is", d / e)
    return d / e


def remap_interval(OldValue, OldMin, OldMax, NewMin, NewMax):
    OldRange = OldMax - OldMin
    if OldRange == 0:
        pass
    # print("none domain length")
    else:

        NewRange = NewMax - NewMin
        NewValue = (OldValue - OldMin) * NewRange / OldRange + NewMin
        return NewValue


def estimated(points, guids):
    for i, gd in enumerate(guids):
        for pt in points[i]:
            yield np.asarray(pt) - np.asarray(gd)


def solve_wall_domain(points_):
    listx = []
    listy = []
    listz = []
    for i in points_:
        listx.append(i[0])
        listy.append(i[1])
        listz.append(i[2])
    listx.sort()
    listy.sort()
    listz.sort()
    xmax, xmin = listx[0], listx[-1]
    ymax, ymin = listx[1], listx[-1]
    zmax, zmin = listz[1], listz[-1]
    bounds = zip([xmax, xmin], [ymax, ymin], [zmax, zmin])
    return bounds


def solve_normalize(points, bounds):
    max_, min_ = bounds
    xmx, ymx, zmx = max_
    xmn, ymn, zmn = min_
    for i in points:
        x_ = remap_interval(i[0], xmn, xmx, 0.0, 1.0)
        y_ = remap_interval(i[1], ymn, ymx, 0.0, 1.0)
        z_ = remap_interval(i[2], zmn, zmx, 0.0, 1.0)
        yield [x_, y_, z_]


# compython geometry base methods

def get_clusters(data, labels):
    """
    :param data: The dataset
    :param labels: The label for each point in the dataset
    :return: List[np.ndarray]: A list of arrays where the elements of each array
    are data points belonging to the label at that ind
    """
    return [data[np.where(labels == i)] for i in range(np.amax(labels) + 1)]


def map_domains(values, s_min, s_max, t_min, t_max):
    # Remap numbers into new numeric domain
    mapped = []
    for v in values:
        if s_max - s_min > 0:
            rv = ((v - s_min) / (s_max - s_min)) * (t_max - t_min) + t_min
        else:
            rv = (t_min + t_max) / 2
        mapped.append(rv)
    return mapped


def mns(a, b, k=1.9):
    l = list(zip(a, b))
    sl = list(starmap(lambda x, y: abs(x) - abs(y), l))
    ex = []
    for s in sl:
        u = abs(s) < k
        ex.append(u)
    # v = abs(sl[0]) < k and abs(sl[1]) < k and abs(sl[2]) < k
    se = set(ex)
    if se.__contains__(False):
        return False
    else:
        return True


def match_planes(pts, k):
    p = [pts[0]]
    indxs = [p.index(pts[0])]

    ptsq = pts[1:]

    while True:

        if len(ptsq) == 0:
            break
        pp = ptsq[0]

        p.reverse()
        for i in p:

            # print("\033[0, 37m{} {}\033".format(pp, i))

            if mns(i, pts[0], k):
                p.append(pp)

            if mns(pp, i, k):
                pii = p.index(i)
                indxs.append(pii)
                print("\033[1;35;40mMatch(\033[0;37;40m{}&{}\033[1;35;40m)\033".format(pp, i))
                print(":{}\033[1;35;40m{}\033".format(i, pii))
                break
        p.reverse()

        ptsq = ptsq[1:]
    set_indx = set([a for a in indxs])
    set_indx.__len__()
    li = [a for a in set_indx]
    li.sort()
    rli = range(set_indx.__len__())

    dli = dict(zip(li, rli))
    icc = []
    for i in indxs:
        icc.append(dli[i])

    return icc


def get_clusters_(data, labels):
    """
    :param data: The dataset
    :param labels: The label for each point in the dataset
    :return: List[np.ndarray]: A list of arrays where the elements of each array
    are data points belonging to the label at that ind
    """
    return [data[np.where(labels == i)] for i in range(np.amax(labels) + 1)]


class DynamicAttrs(type):
    def __new__(mcs, classname, parents=None, add_object=True, **kwargs):

        parent_set = set()

        if parents is None:
            add_object = True
        if add_object:
            parent_set.add(object)
        if parents is not None:
            parent_set.update(parents)

        return type(classname, tuple(parent_set), kwargs)


def _list_or_arr(some, _return_ndarray=True):
    if isinstance(some, ndarray):
        if _return_ndarray:
            return some
        else:
            return some.tolist()
    else:
        if _return_ndarray:
            return np.asarray(some)
        else:
            return some


def get_index_list(_list):
    _l = _list_or_arr(_list, False)
    size = len(_l)
    return np.arange(size)


def get_index_array(_list, return_ndarray=True):
    arr = _list_or_arr(_list, True)
    shape = copy.deepcopy(arr.shape)

    size = np.size(arr.flatten())

    index_arr = np.arange(size).reshape(shape)
    if return_ndarray:
        return index_arr
    else:
        return index_arr.tolist()


def halfsum(lst, halfs=6000):
    a = [0] * (halfs + 1)
    a[0] = -1
    best = halfs + 1
    for l in lst:
        for i in range(halfs, l - 1, -1):
            if (a[i - l] != 0) and a[i] == 0:
                a[i] = l
                best = min(halfs - i, best)
    id = halfs - best
    b = []
    while (id > 0):
        b.append(a[id])
        id = id - a[id]
    return b


def line_nest(lst_, halfs):
    for i, item in enumerate(lst_):
        if item > halfs:
            print(f'! value is most halfs {item} {halfs}\n auto replace {item} -> {halfs} ')
            lst_[i] = halfs
    ls = copy.deepcopy(lst_)
    result = []
    ost = 0
    while len(ls) > 0:

        hs = halfsum(ls, halfs)
        print(hs, sum(hs))
        ost += halfs - sum(hs)
        result.append(hs)
        for item in hs:
            ls.remove(item)
        print(len(ls))
    return result, ost


def conc(*datas):
    return np.c_[datas], np.asarray(list(map(lambda x: len(x.T), datas)))


"""planes = [
    [-0.7070897228208075, 0.7071237039189138, 0.00043730674572993943, -290.92373799967623],
    [0.7073591552420904, -0.7068542257852676, -0.00035914440886667054, 284.52671035465465],
    [0.7091583588299021, 0.7049927065615538, -0.008927810296750669, -495.7036010715342]]

plane_points=[]
plane_colors=[]
for j in planes:
    plane_points.append(plane_to_pt(j))
    plane_colors.append(plane_to_color_(j))

print(plane_points)
print(plane_colors)



def get_rh_model():
    pass



with o3d.utility.VerbosityContextManager(
            o3d.utility.VerbosityLevel.Debug) as cm:
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=9)
    print(mesh)
    o3d.visualization.draw_geometries([mesh])
    draw_result(planes, colors)

if __name__ == "__main__":

    data = {}
    point_filee = ["D:/testptcld/atom-005.e57", "D:/testptcld/atom-006.e57"]
    for pf in point_filee:
        e57 = pye57.E57(pf)

        dt = e57.read_scan(0, ignore_missing_fields=True)
        assert isinstance(dt["cartesianX"], np.ndarray)
        assert isinstance(dt["cartesianY"], np.ndarray)
        assert isinstance(dt["cartesianZ"], np.ndarray)
        data |= dt

    x = np.array(data["cartesianX"])
    y = np.array(data["cartesianY"])
    z = np.array(data["cartesianZ"])
    print('xy', x, y)
    point_file = "D:/testptcld/"
    # generate some neat n times 3 matrix using a variant of sync function
    #
    print(x)
    # mesh_x, mesh_y = np.meshgrid(x, x)

    # print('mesh',x,  mesh_x)
    # z = np.sinc((np.power(mesh_x, 2) + np.power(mesh_y, 2)))

    # z_norm = (z - z.min()) / (z.max() - z.min())
    # print(z_norm)
    xyz = np.zeros((np.size(x), 3))
    xyz[:, 0] = x
    xyz[:, 1] = y
    xyz[:, 2] = z
    print('xyz')
    print(xyz)
    # print(np.reshape(mesh_x, -1), x)

    # Pass xyz to Open3D.o3d.geometry.PointCloud and visualize
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz)
    o3d.io.write_point_cloud(f'{point_file}sync.ply', pcd)

    # Load saved point cloud and visualize it
    pcd_load = o3d.io.read_point_cloud(f'{point_file}sync.ply')
    # o3d.visualization.draw_geometries([pcd_load])

    print("Downsample the point cloud with a voxel of 0.05")
    downpcd = pcd_load.voxel_down_sample(voxel_size=0.5)
    # o3d.visualization.draw_geometries([downpcd])
    # normal colors 9
    print("Recompute the normal of the downsampled point cloud")
    downpcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=1.0, max_nn=30))

    o3d.visualization.draw_geometries([downpcd], point_show_normal=True)


    # convert Open3D.o3d.geometry.PointCloud to numpy array
    xyz_load = np.asarray(pcd_load.points)
    print('xyz_load')
    print(xyz_load)

    # save z_norm as an image (change [0,1] range to [0,255] range with uint8 type)
    img = o3d.geometry.Image((z_norm * 255).astype(np.uint8))
    o3d.io.write_image("../../TestData/sync.png", img)
    o3d.visualization.draw_geometries([img])
"""
