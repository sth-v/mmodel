from __future__ import print_function
from CGAL.CGAL_Kernel import Point_3
from CGAL.CGAL_Kernel import Vector_3
from CGAL.CGAL_Point_set_3 import Point_set_3
from CGAL.CGAL_Polyhedron_3 import Polyhedron_3
from CGAL.CGAL_Shape_detection import *
import copy
import numpy as np
import json
import open3d as o3d

import numpy as np
from CGAL.CGAL_Point_set_processing_3 import wlop_simplify_and_regularize_point_set, edge_aware_upsample_point_set, \
    grid_simplify_point_set, vcm_estimate_normals
from CGAL.CGAL_Advancing_front_surface_reconstruction import advancing_front_surface_reconstruction
import os

SOURCE = os.environ.get('MM-SOURCE')
DUMP = os.environ.get('MM-DUMP')

bb = o3d.io.read_point_cloud('/home/sthv/mmodel-local/dumps/PTC/pl.ply')
cc = o3d.io.read_point_cloud("/home/sthv/mmodel-local/dumps/PTC/pli.ply")

aa = o3d.io.read_point_cloud("/home/sthv/mmodel-local/dumps/PTC/pre.ply")

aa = aa+ bb
ptc = copy.deepcopy(aa)




aa.points

o3d.io.write_point_cloud(f'/home/sthv/mmodel-local/dumps/PTC/cache/ones.ply', aa)

points = Point_set_3(f'/home/sthv/mmodel-local/dumps/PTC/cache/ones.ply')

P = Polyhedron_3()
    # edge_aware_upsample_point_set(points,sharpness_angle=40, edge_sensitivity=1, neighbor_radius=1, number_of_output_points=points.size()*3)
advancing_front_surface_reconstruction(points, P)

P.write_to_file(f"/home/sthv/mmodel-local/dumps/PTC/mesh_shapes/oni.off")


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('y')
