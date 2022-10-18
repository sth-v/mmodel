import unittest
from lahta.items import Bend, BendSegment, BendSegmentFres
from lahta.extrusions import Panel


import compas.geometry as cg
class TestBend(unittest.TestCase):
    def case1(self):
        fr = cg.Frame([-8, 2, 7], [-0.759688, 0, -0.650288], [-0.291821, 0.893654, 0.340914])
        two = BendSegment(45, 1.8, 90)
        one = BendSegment(25, 1.8, 90)
        four = BendSegmentFres(40, 0.8, 120, in_rad=0.3)
        ttt = Bend([one, four, two])
        ttt(parent_obj=fr)
        return ttt


class TestPanels(unittest.TestCase):
    triangles = [[[-3.54622, 290.882442, 708.682366],
                 [-46.144883, -274.077702, 511.184542],
                 [561.666406, 8.40237, 483.42763]],
                 [[519.067744, -556.557773, 285.929806],
                 [561.666406, 8.40237, 483.42763],
                 [-46.144883, -274.077702, 511.184542]],
                 [[561.666406, 8.40237, 483.42763],
                 [604.265069, 573.362513, 680.925454],
                 [-3.54622, 290.882442, 708.682366]],
                 [[-46.144883, -274.077702, 511.184542],
                 [-3.54622, 290.882442, 708.682366],
                 [-611.357509, 8.40237, 736.439278]]]

class TestExtrusion(unittest.TestCase):
    ooo = BendSegmentFres(36, 0.8, 90, in_rad=0.3)
    ttt = BendSegment(18, 1.0, 90)
    thh = BendSegment(7, 1.0, 90)
    one = Bend([ooo, ttt, thh])
    test = Panel(coor_axis=[[258.627489, 545.484455, 490.055883],
                            [36.862172, -12.028006, 490.055883],
                            [705.257292, 44.962907, 490.055883]], bend_types=[one, one, one])


if __name__ == "__main__":
    testcase = TestBend()
    testcase.case1()
