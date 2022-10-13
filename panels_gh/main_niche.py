"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"
try:
    rs=__import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs


import ghpythonlib.treehelpers as th
import Rhino.Geometry as rh
import math
