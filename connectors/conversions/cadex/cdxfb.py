import json

import rhino3dm
from rhino3dm import _rhino3dm as rh
import cadexchanger.CadExCore as cadex
import cadexchanger.CadExRhino as rhino


def readrhino(sorce_path):
    aReader = rhino.Rhino_Reader()
    aReader.ReadFile(cadex.Base_UTF16String(sorce_path))
    return aReader


def to_cadex_viewer(reader,
                          target_path="/home/sthv/cadexchanger-web-toolkit-examples/public/assets/models/native/PNL_all_Arc.cdxfb"):
    aModel = cadex.ModelData_Model()
    reader.Transfer(aModel)
    aWriter = cadex.ModelData_ModelWriter()
    # params
    aParams = cadex.ModelData_WriterParameters()
    aParams.SetFileFormat(cadex.ModelData_WriterParameters.Cdxfb)
    aParams.SetWriteBRepRepresentation(True)
    aParams.SetWritePolyRepresentation(True)
    aParams.SetPreferredLOD(cadex.ModelData_RM_FineLOD)
    aParams.SetWriteTextures(False)
    aParams.SetWritePMI(True)

    aWriter.SetWriterParameters(aParams)
    # wright model
    res = aWriter.Write(aModel, cadex.Base_UTF16String(target_path))
    if res:
        return True
    else:
        print(res)
