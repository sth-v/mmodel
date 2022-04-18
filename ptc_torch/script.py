import open3d as o3d
import numpy as np


from sys import exit
from sys import stderr

from CGAL.CGAL_Kernel import Point_3
from CGAL.CGAL_Polyhedron_3 import Polyhedron_3
from CGAL.CGAL_Point_set_3 import Point_set_3
from CGAL.CGAL_Advancing_front_surface_reconstruction import *
from CGAL.CGAL_Point_set_processing_3 import edge_aware_upsample_point_set
import copy
import numpy as np
import json
import open3d as o3d


bb = o3d.io.read_point_cloud('/home/sthv/mmodel-local/dumps/PTC/pl.ply')
cc = o3d.io.read_point_cloud("/home/sthv/mmodel-local/dumps/PTC/pli.ply")


aa = o3d.io.read_point_cloud("/home/sthv/mmodel-local/dumps/PTC/pre.ply")

aa=aa+bb


def rb():
    f = open("/home/sthv/mmodel-local/dumps/PTC/boxes.json")
    data = json.load(f)
    return np.asarray(data)

ptc = copy.deepcopy(aa)
for i, b in enumerate(rb()):

    b_ = o3d.geometry.OrientedBoundingBox.create_from_points(o3d.utility.Vector3dVector(b))

    print(b)
    print('box')
    inli = ptc.select_by_index(b_.get_point_indices_within_bounding_box(ptc.points))
    ptc = ptc.select_by_index(b_.get_point_indices_within_bounding_box(ptc.points), invert=True)
    o3d.visualization.draw_geometries([inli])
    o3d.io.write_point_cloud(f'/home/sthv/mmodel-local/dumps/PTC/cache/fiture_ptc_{i}_inli.ply', inli)
    print('task done')
    o3d.io.write_point_cloud(f'/home/sthv/mmodel-local/dumps/PTC/cache/fiture_ptc_{i}_inli.ply', inli)

    points = Point_set_3(f'/home/sthv/mmodel-local/dumps/PTC/cache/fiture_ptc_{i}_inli.ply')
    print('adv')
    P = Polyhedron_3()
    #edge_aware_upsample_point_set(points,sharpness_angle=40, edge_sensitivity=1, neighbor_radius=1, number_of_output_points=points.size()*3)
    advancing_front_surface_reconstruction(points, P)
    
    P.write_to_file(f"/home/sthv/mmodel-local/dumps/PTC/mesh_shapes/oni{i}.off")
    del P

o3d.io.write_point_cloud(f'/home/sthv/mmodel-local/dumps/PTC/cache/ptc.ply', ptc)

points_ = Point_set_3(f'/home/sthv/mmodel-local/dumps/PTC/cache/ptc.ply')
P_ = Polyhedron_3()
advancing_front_surface_reconstruction(points_, P_)
P_.write_to_file(f"/home/sthv/mmodel-local/dumps/PTC/mesh_shapes/onout.off")