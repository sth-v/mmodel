import unittest

from vcs.utils import HexTimer, Version, HashNode
from tools.colors import TemplateObjVcs, TemplateTestsFail, TemplateTestsSucsess
import numpy as np


class TestDecorate:
    __templates__ = TemplateTestsSucsess
    __templatef__= TemplateTestsFail
    cases=[]
    def __init__(self, arg):
        self._arg = arg
        self.__class__.cases.append(self)
    def __call__(self):
        print(
            f'\nTest {self._arg.__name__} start\n')
        try:
            self._arg()
            self.__templates__(self._arg.__name__+' sucsess', '\n__________________________________________________________________\n\n')

        except:

            self.__templatef__(self._arg.__name__+' failed', '\n__________________________________________________________________\n\n')
            raise Exception(f'Test {self._arg.__name__} failed')
    @classmethod
    def run(cls):
        try:
            for case in cls.cases:
                case()
            cls.__templates__(cls.__name__ + ' All Sucsess',
                               '\n__________________________________________________________________\n\n')
        except:
            cls.__templatef__(cls.__name__ + ' Failed',
                               '\n__________________________________________________________________\n\n')
            raise Exception()
        del cls.cases



@TestDecorate
def case1():
    hx_timer = HexTimer()

    print(hx_timer)
    print(hx_timer.__hash__())


@TestDecorate
def case4():
    class HashVersion(Version, metaclass=HashNode):
        __template__ = TemplateObjVcs

        def __init__(self, val=None):
            super().__init__(val)
            self.val = np.asarray(
                [str(self.date_tag)[:2], str(self.date_tag)[2:4], str(self.date_tag)[4:6], self.hours, self.minutes],
                dtype=int)


    hv = HashVersion()

    print(hv)
    print(hv.__hash__())


def main():

    case1()
    case4()


if __name__ == '__main__':
    TestDecorate.run()
