import numpy as np
import open3d as o3d
import random
from utils.utils import get_clusters,conc

from sklearn.cluster import DBSCAN, OPTICS, KMeans
from datetime import date


def unpac(cluster,func, *args):
    global GLOBSI
    lg = np.asarray(list(func(*args)), dtype=object)
    if len(np.unique(cluster.labels_)) == len(lg):
        print(f'true {len(lg)}')
    return lg


def clust_to_vis(labels, *datas):
    data, dims = conc(*datas)
    clusts = get_clusters(data, labels)
    for clust in clusts:
        r = random.random()
        g = random.random()
        b = random.random()
        color = np.asarray([r, g, b]).repeat(len(clust)).reshape(3, len(clust)).T
        yield np.c_[clust, color]

def ptc_generate(pack, cloud, cloud_n):

    for u in pack:
        vv = o3d.geometry.PointCloud()
        vv2= o3d.geometry.PointCloud()
        vv.points = o3d.utility.Vector3dVector(u[:, :3])
        vv2.points = o3d.utility.Vector3dVector(u[:, 3:6])
        vv2.colors = o3d.utility.Vector3dVector(u[:, 6:])

        cloud += vv
        cloud_n += vv2
        del vv
        del vv2


def main(path, cluster_method, **kwargs):
    aa = o3d.io.read_point_cloud(path)
    bb = o3d.io.read_point_cloud('/home/sthv/mmodel-local/dumps/PTC/pl.ply')
    cc= o3d.io.read_point_cloud("/home/sthv/mmodel-local/dumps/PTC/pli.ply")
    aa+=bb
    print('web vis')
    o3d.web_visualizer.draw(aa)
    aa+=cc
    #o3d.visualization.draw(aa)
    exp_data = np.asarray(aa.points) * np.asarray(aa.normals)
    cluster = cluster_method(**kwargs).fit(exp_data)
    v = o3d.geometry.PointCloud()
    v_ = o3d.geometry.PointCloud()
    ptc_generate(unpac(cluster, clust_to_vis, cluster.labels_, np.asarray(aa.points), exp_data), v, v_)
    print(v)
    #o3d.visualization.draw([v, v_])
    
    o3d.io.write_point_cloud('dump.ply', v)
    return 0

if __name__ == '__main__':
    main('/home/sthv/mmodel-local/dumps/PTC/pre.ply', DBSCAN, eps=0.6, min_samples=90)