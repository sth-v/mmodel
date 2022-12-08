from compute_rhino3d import Util

__all__ = ["ComputeBinder"]

import dill
from typing import Callable, Type


def extract_out(lines):
    return lines[-1].replace("    ", "").replace("\n", "").split(" ")[1:]


def extract_inputs(func, method=False):
    aa = list(func.__code__.co_varnames[:func.__code__.co_argcount])
    if method:
        del aa[0]
    return aa


def sort_vars(func: Type[Callable]) -> tuple[set[str], set[str], set[str]]:
    inputs = set(extract_out(dill.source.getsourcelines(func)))
    out = set(extract_inputs(func))
    intern = set(func.__code__.co_varnames) - inputs.union(out)
    return inputs, intern, out


class ComputeBinder(Callable):
    """
    result = Util.PythonEvaluate("import Rhino.Geometry as rg\nres=rg.NurbsCurve.CreateControlPointCurve([rg.Point3d(xx,yy,zz) for xx,yy,zz in zip(eval(x),eval(y),eval(z))], 3)",
                                 {
                                     "x": '[0.0,1.0,2.0,3.0,4.0,5.0,6.0]',
                                     "y": '[0.0,1.0,2.0,3.0,4.0,5.0,6.0]',
                                     "z": '[0.0,1.0,2.0,3.0,4.0,5.0,6.0]'
                                 }, ["res"])"""

    def __init__(self, meth: Type[Callable]):
        self._method = meth
        self._lines = dill.source.getsourcelines(self._method)[0]
        print(self._lines)
        self.inputs = set(extract_inputs(self._method, True))
        self.out = set(extract_out(self._lines))
        self.intern = set(self._method.__code__.co_varnames) - self.inputs.union(self.out)

    def __call__(self, **kwargs):
        inp = kwargs

        out = list(self.out)
        script = ""

        for line in self._lines[2:-1]:
            script += line.replace("        ", "")
        print(script)
        print(inp)
        print(out)
        return Util.PythonEvaluate(script, inp, out)
