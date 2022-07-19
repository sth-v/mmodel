import unittest
from mm.baseitems import I\
from mm.exceptions import MModelException


class A(NamedElement):
    ...


class B(NamedElement):
    ...


class PointLike(BaseFieldsInterface):
    required_fields = {'x', 'y', 'z'}

    @classmethod
    def __field_missing__(cls, key, kws):
        if key == 'z':
            kws['z'] = 0.0
        else:
            super().__field_missing__(key, kws)


class MyTestCase(unittest.TestCase):
    def test_correct_name(self):
        adict = dict(name=str("A"), x=8)
        a = A(**adict)
        self.assertEqual(a.x, 8)  # add assertion here
        self.assertEqual(a.name, str("A"))

    def test_uncorrect_name(self):
        adict = dict(name=str("A"), x=8)
        self.assertRaises(MModelException, B, **adict)

    def test_change_args(self):
        adict = dict(name=str("A"), x=8)
        a = A(**adict)
        self.assertEqual(a.x, 8)
        a.x = 15
        self.assertEqual(a.x, 15)

    def test_pointlike(self):
        input = dict(x=1, y=2, z=3)
        ptl = PointLike(**input)
        self.assertDictEqual(ptl.__element_dict__, input)

    def test_pointlike_z(self):
        a = PointLike(x=1.0, y=2.0)
        self.assertTupleEqual((a.x, a.y, a.z), (1.0, 2.0, 0.0))


if __name__ == '__main__':
    unittest.main()
