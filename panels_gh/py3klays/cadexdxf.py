import gzip
import json
import os
import sys
import time

sys.path.extend(["/Users/andrewastakhov/PycharmProjects", "/Users/andrewastakhov/PycharmProjects/mmodel/panels_gh"])

import rhino3dm
import compute_rhino3d.Util
from rhino3dm import _rhino3dm as rh
from py3klays import cadex_license as license
import cadexchanger.CadExCore as cadex
import cadexchanger.CadExRhino as rhino
import cadexchanger.CadExDXF as dxf


def todxf(theSource: str, theDest: str):
    aKey = license.Value()

    if not cadex.LicenseManager.Activate(aKey):
        print("Failed to activate CAD Exchanger license.")
        return 1

    aModel = cadex.ModelData_Model()

    print("Conversion started...")

    aReader = rhino.Rhino_Reader()
    # Opening and converting the file
    if not aReader.ReadFile(cadex.Base_UTF16String(theSource)):
        print("Failed to open and convert the file " + theSource)
        return 1
    if not aReader.Transfer(aModel):
        print("Failed to transfer the model into inner format")
        return 1
    aWriter = dxf.DXF_Writer()
    aWriterParams: dxf.DXF_WriterParameters = aWriter.Parameters()

    # Set some writer parameteres
    aWriterParams.SetLengthUnit(cadex.Base_LU_Millimeters)
    aWriterParams.SetDXFVersion(aWriterParams.AutoCAD_2007).SetLengthUnit(cadex.Base_LU_Millimeters)
    aWriterParams.SetWritePolyRepresentation(True)
    # Converting model data to a new format
    if not aWriter.Transfer(aModel):
        print("Failed to transfer model data to specified format")
        return 1

    # Writing model data to file
    if not aWriter.WriteFile(cadex.Base_UTF16String(theDest)):
        print("Failed to write the file")
        return 1

    print("Completed")

    return 0


class RH:
    def __init__(self, tag, time, layers, **kwargs):
        self.time = time
        super().__init__()
        # self.frame = frame
        self.tag = tag
        self.__dict__ |= kwargs
        self.model = rhino3dm.File3dm()
        self.layers = []
        for l in layers:
            self.layers.append(Lay(model=self.model, **l))

    def write(self):
        os.mkdir(f"{os.getenv('PANELS_GH_DUMPS')}/build{s}/{self.tag}")
        os.mkdir(f"{os.getenv('PANELS_GH_DUMPS')}/build{s}-dxf/{self.tag}")
        fp = f"{os.getenv('PANELS_GH_DUMPS')}/build{s}/{self.tag}/{self.tag}"
        fp2 = f"{os.getenv('PANELS_GH_DUMPS')}/build{s}-dxf/{self.tag}/{self.tag}"
        self.model.Write(fp + ".3dm", 7)
        todxf(fp + ".3dm", fp2 + ".dxf")

        # self.model.Write(f"dumps/{self.tag}/{self.tag}"+".dxf")
        # client.s3.put_object(Bucket=client.bucket,Key=f"{client.bucket}/{client.prefix}/build{self.time}/{self.tag}/{self.time}", Body=self.model.Encode())
        return f"{os.getenv('PANELS_GH_DUMPS')}/build{s}/{self.tag}/{self.tag}.3dm"


class Lay:

    def __init__(self, model=None, **kwargs):
        super().__init__()
        self.model = model
        self._lay = rhino3dm.Layer()
        self._lay.Name = kwargs["name"]

        self._lay.Color = tuple(kwargs["color"] + [255])
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
                print(obj)
                self.model.Objects.Add(obj, attrs)


if __name__ == "__main__":

    s = round(time.time())
    os.mkdir(f"{os.getenv('PANELS_GH_DUMPS')}/build{s}")
    os.mkdir(f"{os.getenv('PANELS_GH_DUMPS')}/build{s}-dxf")
    # client = sessions.S3Client(bucket=os.getenv('BUCKET'), prefix="workspace/cxm/arc/")
    with gzip.open(f"{os.getenv('PANELS_GH_DUMPS')}/input.gz", "rb", compresslevel=9) as gz:
        bts = gz.read()
        # client.s3.put_object(Bucket=client.bucket, Key=f"{client.bucket }/{client.prefix}/build{s}", Body=bts)
        for obj in json.loads(bts):
            print(obj)
            a = RH(**obj, time=1)

            os.environ['RHINO_TARGET'] = a.write()
