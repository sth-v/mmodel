from abc import ABC
from collections import namedtuple
import compas.geometry
import compas.data
import compas.datastructures
import compas
import numpy as np
import compas_rhino
#import rhino3dm

from mm.baseitems import Item

RootParents = namedtuple("RootParents", ["main_parent", "FramrworkParent"])


class GeometryMeta(type):
    target_framework = compas
    mapping_framework = dict(

    )


class GeometryItem(Item, compas.data.Data, ABC):
    """
    geometry item
    """

    def __init__(self, *args, **kwargs):
        compas.data.Data.__init__()
        super(GeometryItem, self).__init__(*args, **kwargs)
        # super(GeometryItem, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super(GeometryItem, self).__call__(*args, **kwargs)



