import unittest
from lahta.items import Bend, BendSegment, BendSegmentFres


class TestBend(unittest.TestCase):
    def case1(self):
        two = BendSegment(45, 1.8, 90)
        one = BendSegment(25, 1.8, 90)
        four = BendSegmentFres(40, 0.8, 120, in_rad=0.3)
        ttt = Bend([one, four, two])


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


if __name__ == "__main__":
    testcase = TestBend()
    testcase.case1()
