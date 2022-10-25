from typing import TypeVar, Generic, Any

import numpy as np

from mmodel.mm.baseitems import Item, Base, Identifiable

SP = TypeVar("SP")  # descriptor
KT = TypeVar("KT")
VT = TypeVar("VT")  # descriptor
T1 = TypeVar("T1", bound=Base)
T2 = TypeVar("T2")


def args_flatten(arg, *args):
    arr = np.asarray((arg,)).flatten()
    for barr in args:
        arr = np.concatenate([arr, np.asarray((barr,)).flatten()])
    return arr


class D3(Generic[T1, SP, KT, VT], Base, dict[str, VT]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        dict[str, VT].__init__(self, **self.__dict__)

    def __getitem__(self, k: KT) -> VT: return dict[str, VT].__getitem__(self, k)

    def __setitem__(self, k: KT, v: VT) -> None: dict[str, VT].__setitem__(self, k, v)

    def __call__(self, **kwargs) -> Generic[T1, SP, KT, VT]:
        Base.__call__(self, **kwargs)
        self.update(kwargs)  # self: D3[T1, SP, KT, VT] kwargs:dict[str, VT]
        return self


DctBaseI = D3[Base, dict, str, Any]
DctIdentifiableI = D3[Identifiable, dict, str, Any]
DctItem = D3[Item, dict, str, Any]
