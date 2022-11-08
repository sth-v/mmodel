import gzip
import json
import os
import time

import rhino3dm


class RH:
    def __init__(self, tag, frame, layers, **kwargs):
        super().__init__()
        self.frame = frame
        self.tag = tag
        self.__dict__ |= kwargs
        self.model = rhino3dm.File3dm()
        self.layers = []
        for l in layers:
            self.layers.append(Lay(model=self.model, **l))

    def write(self):
        os.mkdir(f"dumps/build{self.time}/{self.tag}")
        self.model.Write(f"dumps/build{self.time}/{self.tag}/{self.tag}" + ".3dm")
        # self.model.Write(f"dumps/{self.tag}/{self.tag}"+".dxf")


class Lay:

    def __init__(self, model=None, **kwargs):
        super().__init__()
        self.model = model
        self._lay = rhino3dm.Layer()
        self._lay.Name = kwargs["name"]

        self._lay.Color = tuple(kwargs["color"] + [255])
        self._lay.SetPersistentVisibility(kwargs["isvisible"])

        lay_index = self.model.Layers.Add(self._lay)
        if kwargs["objects"] is not None:
            for o in kwargs["objects"]:
                # obj = list(self.model.Objects)[-1]
                attrs = rhino3dm.ObjectAttributes()
                attrs.PlotColorSource = rhino3dm.ObjectPlotColorSource.PlotColorFromLayer
                attrs.ColorSource = rhino3dm.ObjectColorSource.ColorFromLayer
                attrs.LayerIndex = lay_index
                o["archive3dm"] = 70
                obj = rhino3dm.CommonObject.Decode(o)

                print(obj)
                self.model.Objects.Add(obj, attrs)


s = round(time.time())
os.mkdir(f"dumps/build{s}")
with gzip.open("dumps/build-0x7065f.gz", "rb", compresslevel=9) as gz:
    for obj in json.loads(gz.read()):
        print(obj)
        a = RH(**obj, time=s)
        a.write()
