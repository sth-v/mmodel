from gh_redis_api import GhReddisDict, GhRedisProperty
from main import Niche, Schov, Side, rs


class Panel:

    @GhRedisProperty
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.schov.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        if self.type == 0:
            fr = self.side[0].fres.FrameAt(self.side[0].fres.Domain[1])[1]
            bound_plane = rh.Plane(b_r.Min, fr.XAxis, fr.YAxis)
        else:
            fr = self.side[1].fres.FrameAt(self.side[1].fres.Domain[0])[1]
            bound_plane = rh.Plane(b_r.Max, fr.XAxis, fr.YAxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def top_parts(self):
        top = [self.side[0].top_part.DuplicateCurve(), self.niche.top_part.DuplicateCurve(),
               self.side[1].top_part.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in top]
        return top

    @GhRedisProperty
    def fres(self):
        fres = [self.side[0].fres.DuplicateCurve(), self.niche.fres.DuplicateCurve(),
                self.side[1].fres.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in fres]
        return fres

    @GhRedisProperty
    def cut(self):
        if self.cogs_bend is True:
            side = \
                rh.Curve.JoinCurves([self.side[0].join, self.niche.join_region[0], self.side[1].join, self.schov.fres])[
                    0]
            side.Transform(self.bound_plane)

            cut = [side]

            reg = self.niche.join_region[1:]

            for i in reg:
                ii = i.DuplicateCurve()
                ii.Transform(self.bound_plane)
                cut.append(ii)
        else:
            side = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.schov.fres])[0]
            side.Transform(self.bound_plane)
            cut = [side]
        return cut

    @property
    def unroll_dict(self):
        self._unroll_dict = {'tag': self.tag, 'unroll': self.unrol_surf, 'frame': {'bb': 0}, }
        return self._unroll_dict

    @GhRedisProperty
    def production_dict(self):
        self._production_dict = {'tag': self.tag, 'unroll': self.unrol_surf, 'frame': {'bb': 0}, }
        return

    def __init__(self, surface, type, cogs_bend, tag):
        self.__target__ = GhReddisDict(self)
        self.type = type
        self.cogs_bend = cogs_bend
        self.tag = tag

        self.surf = surface

        self.unrol_surf = rh.Unroller(self.surf).PerformUnroll()[0][0]
        self.edges = self.unrol_surf.Curves3D

        self.side_types()

    def side_types(self):

        if self.type == 0:
            self.niche = Niche(self.edges[0])
            self.schov = Schov(self.edges[2])
            self.side = [Side(self.edges[1], True), Side(self.edges[3], False)]

        else:
            self.niche = Niche(self.edges[2])
            self.schov = Schov(self.edges[0])
            self.side = [Side(self.edges[1], False), Side(self.edges[3], True)]

        self._side_types = [self.niche, self.schov, self.side[0], self.side[1]]
        self.intersect()

    def intersect(self):
        for i, v in enumerate(self._side_types):
            param = []
            for ind, val in enumerate(self._side_types):
                if i != ind:
                    inters = rs.CurveCurveIntersection(v.fres, val.fres)
                    if inters is not None:
                        param.append(inters[0][5])
            param = sorted(param)

            trimed = rh.Curve.Trim(v.fres, param[0], param[1])
            v.fres = trimed
