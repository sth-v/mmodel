import unittest
from lahta.items import Bend, BendSegment, BendSegmentFres
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


if __name__=="__main__":
    testcase=TestBend()
    testcase.case1()