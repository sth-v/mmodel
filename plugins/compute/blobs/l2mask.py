from compute_rhino3d import Util


class CalcMaskL2:
    __blob__ = """
    import Rhino.Geometry as rg
    import Rhino.Collections as rhc

    from ghpythonlib import parallel
    from ghpythonlib.treehelpers import list_to_tree
    import time
    pnls = rhc.CurveList(x)
    from collections import Callable

    class Solver(Callable):
        def __init__(self, f):
            self._data = None
            self._f = f
            self.interior = None
            self.exterior = None

        @property
        def func(self):
            return self._f

        @func.setter
        def func(self, value):
            self._f = value

        @property
        def data(self):
            return self._data

        @data.setter
        def data(self, value):
            self._data = value

        def method(self, d):
            return list(self.func(d, *self.args, **self.kwargs))

        def __call__(self, *args, **kwargs):
            self.start = time.time()
            self.args = args
            self.kwargs = kwargs
            p = parallel.run(self.method, zip(self.data, [i < len(interior) for i in range(len(interior) + len(exterior))]))
            self.end = time.time()
            self.t = self.end - self.start
            print("{} min. {} sec.".format(*divmod(self.t, 60)))
            return p


    @Solver
    def search((crv, predicate), panels):
        for i in panels:
            res = rg.Intersect.Intersection.CurveCurve(i, crv, 1.0, overlapTolerance=10)
            rr = []
            if res.Count == 0:
                continue
            else:

                if predicate:
                    r = rg.Curve.CreateBooleanDifference(i, crv, 1.0)

                else:
                    r = rg.Curve.CreateBooleanIntersection(i, crv, 1.0)
                yield list(r)


    search.data = interior+exterior
    ans = list(search(pnls))"""

    def __init__(self):
        object.__init__(self)

    def __get__(self, inst, own):
        def wrp(interior=[], exterior=[]):
            inp = {"x": inst["polycurve"], "interior": interior, "exterior": exterior}
            out = ["ans"]
            result = Util.PythonEvaluate(self.__blob__, inp, out)
            return result

        return wrp
