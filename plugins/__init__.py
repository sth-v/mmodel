import os

from compute_rhino3d import Util


Util.apiKey = os.getenv('RHINO_COMPUTE_API_KEY')
Util.url = "http://"+os.getenv('RHINO_COMPUTE_URL')+"/"
result=Util.PythonEvaluate("import Rhino.Geometry as rg\nres=rg.NurbsCurve.CreateControlPointCurve([rg.Point3d(xx,yy,zz) for xx,yy,zz in zip(eval(x),eval(y),eval(z))], 3)",{
    "x":'[0.0,1.0,2.0,3.0,4.0,5.0,6.0]',
    "y":'[0.0,1.0,2.0,3.0,4.0,5.0,6.0]',
    "z":'[0.0,1.0,2.0,3.0,4.0,5.0,6.0]'
},["res"])
