#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import json
import os
import sys

import dotenv

from cxm_remote.sessions import S3Client

dotenv.load_dotenv(".env")
sys.path.extend(
    [os.getenv("HOME") + "/mmodel", os.getenv("HOME") + "/mmodel/lahta",
     os.getenv("HOME") + "/mmodel/cxm_remote", os.getenv("HOME") + "/mm",
     os.getenv("HOME") + "/mmodel/cxm_remote/sessions"])
from lahta.items import *
from mm.meta import RemoteType

sys.path.extend(os.getenv("HOME") + "/mmodel")

import dotenv

dotenv.load_dotenv(dotenv.find_dotenv(".env"))
import os

BUCKET = os.getenv("BUCKET")
STORAGE = os.getenv("STORAGE")


class ModelAttrDescriptor:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, inst, own):
        return getattr(inst.model, self.name)


from lahta.extrusions import RhinoFriendlyPanel
from mm.baseitems import Item
import itertools


class L2Model(metaclass=RemoteType, client=S3Client, storage=STORAGE, bucket=BUCKET, prefix="cxm/internal/L2/",
              suffix=""):
    bucket = BUCKET
    storage = STORAGE
    client: S3Client

    def __gethook__(self, hook):
        data = json.loads(hook["Body"].read())

        return data

    def __sethook__(self, hook):
        return json.dumps(hook)


class TS(Item):
    model = L2Model()
    mask = ModelAttrDescriptor()
    client = ModelAttrDescriptor()
    target_triangles = ModelAttrDescriptor()

    def solve_celling(self):
        self.cells = []
        self.warns = []
        size = 40
        prefix = "Building "

        l = 200

        out = sys.stdout

        def show(j):
            x = int(size * j / l)
            print(f"{prefix}{u'█' * x}{('.' * (size - x))} {j}/{l}", end='\r', file=out, flush=True)

        show(0)

        for i, pnl in enumerate(self.target_triangles[:200]):

            ll = [Bend([BendSegmentFres(36, 0.8, 90, in_rad=0.3),
                        BendSegment(18, 1.0, 90),
                        BendSegment(7, 1.0, 90)])]
            ll.extend(list(itertools.repeat(Bend([BendSegment(18, 1.0, 90)]), len(pnl[:-1]) - 1)))
            show(i + 1)

            # print(ll, pnl[:-1])
            try:
                self.cells.append(RhinoFriendlyPanel(coor_axis=pnl[:-1], bend_types=ll))

            except:
                raise Exception(i, pnl)
        return self.cells


if __name__ == "__main__":
    ts = TS()
    ts.solve_celling()
    # print(ts)
