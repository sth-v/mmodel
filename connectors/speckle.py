import compas.geometry
import numpy as np
from compas.data import DataDecoder
from compas.data import DataEncoder

from specklepy.objects import Base


class SpeckleDataBridge(Base):
    data: dict = {}

    @classmethod
    def from_compas(cls, compas_obj):
        encoder = DataEncoder()
        return cls(data=encoder.default(compas_obj))

    def to_compas(self):
        decoder = DataDecoder()
        return decoder.object_hook(self.data)


if __name__ == '__main__':
    from compas.datastructures import Mesh as cMesh

    from specklepy.api import operations

    from specklepy.objects.geometry import Line, Point, Mesh

    from specklepy.api.client import SpeckleClient
    from specklepy.api.credentials import get_default_account, get_account_from_token
    from specklepy.transports.server.server import ServerTransport
    from specklepy.objects.base import Base

    mesh = cMesh()
    smesh = SpeckleDataBridge.from_compas(mesh)

    client = SpeckleClient(host="speckle.xyz")

    client.authenticate_with_token(token='b6df5ab76888a726d7d82897998caf017a7854590e')

    print(f'account: {client}')
    stream_id = '489451a9f8'
    transport = ServerTransport(client=client, stream_id=stream_id)
    # object_id = operations.send(base=smesh, transports=[transport])
    # commid_id = client.commit.create(stream_id=stream_id, object_id=object_id, message='Test commit')
    # base_obj = operations.receive(obj_id='9de5e083f6d656bb9cf9cd13fc093de6', remote_transport=transport)
    # print(f'resived: {base_obj}')
    # br = SpeckleDataBridge()
    # base_obj.get_member_names()
    import rhino3dm
    import open3d as o3d


    def line():
        newline = Line()
        end, start = Point(), Point()
        end.x, end.y, end.z = 1.2, 33, 0.23
        start.x, start.y, start.z = 56.2, 2.1, 12.8
        newline.start = start
        newline.end = end
        print(newline)


    tetr = o3d.geometry.TriangleMesh.create_tetrahedron(radius=2.0, create_uv_map=True)
    tetr.compute_vertex_normals()

    verts = np.asarray(tetr.vertices, dtype=float).flatten().tolist()
    faces = np.asarray(tetr.triangles, dtype=int).flatten().tolist()

    speckle_mesh = Mesh.create(vertices=verts, faces=faces, colors=[40, 40, 40, 40])

    object_id = operations.send(base=speckle_mesh, transports=[transport])
    commid_id = client.commit.create(stream_id=stream_id, object_id=object_id, message='Test tetrahedron commit')
    print(speckle_mesh, object_id, commid_id)
