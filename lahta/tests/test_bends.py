import unittest
from lahta.items import Bend, BendSegment, BendSegmentFres
class TestBend(unittest.TestCase):
    def case1(self):
        two = BendSegment(45, 1.8, 90)
        one = BendSegment(25, 1.8, 90)
        four = BendSegmentFres(40, 0.8, 120, in_rad=0.3)
        ttt = Bend([one, four, two])


if __name__=="__main__":
    testcase=TestBend()
    testcase.case1()