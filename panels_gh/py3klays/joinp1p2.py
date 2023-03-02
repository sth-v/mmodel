import copy
import gzip
import json
import os
import sys
import time

sys.path.extend(["/Users/andrewastakhov/PycharmProjects", "/Users/andrewastakhov/PycharmProjects/mmodel/panels_gh"])

import rhino3dm
from rhino3dm import _rhino3dm as rh

PANELS_GH_DUMPS = os.getenv('PANELS_GH_DUMPS')


class RH:
    def __init__(self, tag, time, layers, **kwargs):
        self.time = time
        super().__init__()
        # self.frame = frame
        self.tag = tag
        self.__dict__ |= kwargs
        self.model = rhino3dm.File3dm()
        self.model2 = rhino3dm.File3dm()
        self.layers = []
        self._layers = layers
        self.layers2 = []

    def write(self):
        spl = self.tag.split("-")

        try:
            os.makedirs(f"{os.getenv('PANELS_GH_DUMPS')}/build/cut/{self.tag[:-2]}", exist_ok=False)
            os.makedirs(f"{os.getenv('PANELS_GH_DUMPS')}/build/frez/{self.tag[:-2]}", exist_ok=False)
        except:
            pass
        fp = f"{os.getenv('PANELS_GH_DUMPS')}/build/cut/{self.tag[:-2]}/{self.tag}.3dm"
        fpfrez = f"{os.getenv('PANELS_GH_DUMPS')}/build/frez/{self.tag[:-2]}/{self.tag}.3dm"

        if int(self.tag[-1]) in [1, 2]:
            for l in copy.deepcopy(self._layers):
                self.layers.append(Lay(model=self.model, **l))
            for l2 in self._layers:
                self.layers2.append(Lay2(model=self.model2, **l2))
            self.model2.Write(fpfrez, 7)

            self.model.Write(fp, 7)
        else:
            for l in copy.deepcopy(self._layers):
                self.layers.append(LayP3(model=self.model, **l))
            self.model.Write(fp, 7)

        # todxf(fp + ".3dm", fp2 + ".dxf")

        # self.model.Write(f"dumps/{self.tag}/{self.tag}"+".dxf")
        # client.s3.put_object(Bucket=client.bucket,Key=f"{client.bucket}/{client.prefix}/build{self.time}/{self.tag}/{self.time}", Body=self.model.Encode())
        return f"{os.getenv('PANELS_GH_DUMPS')}/build/cut/{spl[:-1]}/{self.tag}.3dm"


class Lay:

    def __init__(self, model=None, **kwargs):
        super().__init__()
        self.model = model
        self._lay = rhino3dm.Layer()
        self._lay.Name = kwargs["name"]

        self._lay.Color = tuple(kwargs["color"])
        self._lay.Visible = (kwargs["visible"])

        lay_index = self.model.Layers.Add(self._lay)
        m = rh.Transform.Mirror(rhino3dm.Plane.WorldYZ())
        if kwargs["objects"] is not None:
            for o in kwargs["objects"]:
                # obj = list(self.model.Objects)[-1]

                attrs = rhino3dm.ObjectAttributes()
                attrs.PlotColorSource = rhino3dm.ObjectPlotColorSource.PlotColorFromLayer
                attrs.ColorSource = rhino3dm.ObjectColorSource.ColorFromLayer
                attrs.LayerIndex = lay_index
                o["archive3dm"] = 70
                obj = rhino3dm.CommonObject.Decode(o)
                obj.Transform(m)
                # print(obj)
                self.model.Objects.Add(obj, attrs)


class Lay2:

    def __init__(self, model=None, **kwargs):
        super().__init__()
        self.model = model
        self._lay = rhino3dm.Layer()
        self._lay.Name = kwargs["name"]

        self._lay.Color = tuple(kwargs["color"] + [255])
        self._lay.Visible = (not kwargs["visible"])

        lay_index = self.model.Layers.Add(self._lay)
        m = rh.Transform.Mirror(rhino3dm.Plane.WorldYZ())
        if kwargs["objects"] is not None:
            for o in kwargs["objects"]:
                # obj = list(self.model.Objects)[-1]

                attrs = rhino3dm.ObjectAttributes()
                attrs.PlotColorSource = rhino3dm.ObjectPlotColorSource.PlotColorFromLayer
                attrs.ColorSource = rhino3dm.ObjectColorSource.ColorFromLayer
                attrs.LayerIndex = lay_index
                o["archive3dm"] = 70
                obj = rhino3dm.CommonObject.Decode(o)

                # print(obj)
                self.model.Objects.Add(obj, attrs)


class LayP3:

    def __init__(self, model=None, **kwargs):
        super().__init__()
        self.model = model
        self._lay = rhino3dm.Layer()
        self._lay.Name = kwargs["name"]

        self._lay.Color = tuple(kwargs["color"])
        self._lay.Visible = (kwargs["visible"])

        lay_index = self.model.Layers.Add(self._lay)
        m = rh.Transform.Mirror(rhino3dm.Plane.WorldYZ())
        if kwargs["objects"] is not None:
            for o in kwargs["objects"]:
                # obj = list(self.model.Objects)[-1]

                attrs = rhino3dm.ObjectAttributes()
                attrs.PlotColorSource = rhino3dm.ObjectPlotColorSource.PlotColorFromLayer
                attrs.ColorSource = rhino3dm.ObjectColorSource.ColorFromLayer
                attrs.LayerIndex = lay_index
                o["archive3dm"] = 70
                obj = rhino3dm.CommonObject.Decode(o)
                # obj.Transform(m)
                # print(obj)
                self.model.Objects.Add(obj, attrs)


if __name__ == "__main__":

    s = round(time.time())
    os.makedirs(f"{os.getenv('PANELS_GH_DUMPS')}/build/cut", exist_ok=True)
    os.makedirs(f"{os.getenv('PANELS_GH_DUMPS')}/build/frez", exist_ok=True)
    # client = sessions.S3Client(bucket=os.getenv('BUCKET'), prefix="workspace/cxm/arc/")
    for i in os.scandir(f"{os.getenv('PANELS_GH_DUMPS')}/panels"):
        with gzip.open(f"{os.getenv('PANELS_GH_DUMPS')}/panels/{i.name}", "rb", compresslevel=9) as gz:
            try:
                bts = gz.read()

                # client.s3.put_object(Bucket=client.bucket, Key=f"{client.bucket }/{client.prefix}/build", Body=bts)
                for obj in json.loads(bts):
                    # print(obj)
                    a = RH(**obj, time=1)
                    a.write()
            except:
                print(i.name)