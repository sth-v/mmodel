#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import typing
from abc import abstractmethod

import compas.geometry as cg
import numpy as np
import pydantic
from OCC.Core.gp import gp_Pnt
from rhino3dm import Point3d

from mm.baseitems import GeomConversionMap
from mm.baseitems import GeomDataItem, ReprData


class BufferGeometryGroup(pydantic.BaseModel):
    count: int
    start: int = 0
    materialIndex: int = 0


class BufferGeometryProperty(pydantic.BaseModel):
    array: list[float]
    itemSize: int = 3
    type: str = "Float32Array"
    normalized: bool = False


class BufferGeometryPosition(BufferGeometryProperty): ...


class BufferGeometryNormal(BufferGeometryProperty): ...


class BufferGeometryUV(BufferGeometryProperty):
    itemSize: int = 2


class BufferGeometryBoundingSphere(pydantic.BaseModel):
    center: list[float, float, float]
    radius: float = 1.0


class BufferGeometryData(pydantic.BaseModel):
    attributes: dict[str, BufferGeometryProperty]
    boundingSphere: BufferGeometryBoundingSphere
    groups: list[BufferGeometryGroup | None] = []


class BufferGeometryModel(pydantic.BaseModel):
    data: BufferGeometryData
    uuid: str
    type: str = "BufferGeometry"


class BufferPointMap(GeomConversionMap):
    include = ["array"]
    exclude = ["x", "y", "z", 'args', 'kw', 'representation', 'aliases', 'fields', 'uid', '__array__', '_dtype']

    def __get_dict__(self, instance, owner):
        data = BufferGeometryData(attributes=dict(
            position=BufferGeometryPosition(array=instance.array),
        ),
            boundingSphere=BufferGeometryBoundingSphere(center=instance.array, radius=0.5)
        )

        return BufferGeometryModel(data=data, uuid=instance.uuid, type='BufferGeometry')


class BufferGeometryItem(GeomDataItem, typing.Sequence):
    representation = ReprData("array")
    geometries = BufferPointMap()

    def __getitem__(self, item):
        return self.array[item]

    def __len__(self):
        return len(self.array)

    @abstractmethod
    def __array__(self, *args, **kw) -> np.ndarray: ...

    def __list__(self) -> list[float]:
        return self.__array__().tolist()

    @property
    def array(self) -> list[float]:
        return self.__array__().tolist()


class BufferPoint(BufferGeometryItem):
    """
    >>> point = BufferPoint(1, 2, 3)
    >>> print(point.to_json(indent=3))
    {
        "metadata": {
            "uuid": "4c6adef0bf554c2fb2731e8ddd8dcab3",
            "dtype": "Point",
            "version": "0x4d0x590x500x5c0x60",
            "custom_fields": [
                "custom_fields",
                "_uuid",
                "base_fields",
                "version"
            ],
            "base_fields": [
                "x",
                "y",
                "z"
            ]
        },
        "geometries": {
            "data": {
                "attributes": {
                    "position": {
                        "array": [
                            1.0,
                            2.0,
                            3.0
                        ],
                        "itemSize": 3,
                        "type": "Float32Array",
                        "normalized": false
                    }
                },
                "boundingSphere": {
                    "center": [
                        1.0,
                        2.0,
                        3.0
                    ],
                    "radius": 0.5
                },
                "groups": []
            },
            "uuid": "4c6adef0bf554c2fb2731e8ddd8dcab3",
            "type": "BufferGeometry"
        }
    }

    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __contains__(self, item):
        return item in self.array

    @property
    def shape(self):
        return 3,

    def __init__(self, x, y, z, *args, **kwargs):
        super().__init__(x=x, y=y, z=z, *args, **kwargs)

    def __array__(self, *args, **kw):
        return np.asarray([self.x, self.y, self.z], dtype=float).reshape(self.shape)

    def to_dict(self):
        dict_ = super().to_dict()
        del dict_["x"], dict_["y"], dict_["z"]

        return dict_

    def to_compas(self):
        return cg.Point(self.x, self.y, self.z)

    def to_occ(self):
        return gp_Pnt(self.x, self.y, self.z)

    def to_rhino(self):
        return Point3d(self.x, self.y, self.z)


class BufferFaceMap(GeomConversionMap):
    include = ["array"]
    exclude = ["vertices", 'args', 'kw', 'representation', 'aliases', 'fields', 'uid', '__array__', '_dtype']

    def __get_dict__(self, instance, owner):
        data = BufferGeometryData(attributes=dict(
            position=BufferGeometryPosition(array=instance.array),
        ),
            boundingSphere=BufferGeometryBoundingSphere(center=instance.array, radius=0.5)
        )

        return BufferGeometryModel(data=data, uuid=instance.uuid, type='BufferGeometry')


class BufferFace(BufferGeometryItem):
    geometries = BufferPointMap()
    representation = ReprData("array")
    vertices: list[BufferPoint] = [BufferPoint(0, 1, 0), BufferPoint(1, 0, 0), BufferPoint(0, 0, 1)]

    def __contains__(self, item):
        return item in self.vertices

    @property
    def shape(self):
        return int(len(self.vertices) * 3),

    def __init__(self, *args, **kwargs):
        super().__init__(vertices=list(args), **kwargs)

    def __array__(self, *args, **kw):
        return np.asarray(self.vertices, dtype=object).flatten().reshape(self.shape)

    def to_dict(self):
        dct_ = super().to_dict()
        del dct_["vertices"]
        return dct_
