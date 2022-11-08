import json

import Rhino
import System.Drawing.Color as Color

with open("layers.json") as f:
    input = json.load(f)


class Layer(dict):

    def __init__(self, name="Default", color=(255, 255, 255, 255), isvisible=True, objects=[], **properties):
        object.__init__(self)
        self._dict = None
        self.name = name
        self.color = color
        self.objects = []
        self._layer = Rhino.DocObjects.Layer()
        self._layer.Name = self.name
        self._layer.Color = Color.FromArgb(*self.color)
        self._layer.PlotColor = Color.FromArgb(*self.color)
        self.isvisible = isvisible
        self.objects += objects
        self.dict.update(properties)
        dict.__init__(self, **self.dict)

    @property
    def isvisible(self):
        return self._layer.IsVisible

    @isvisible.setter
    def isvisible(self, v):
        self._layer.IsVisible = v

    @property
    def dict(self):
        if self._dict is None:
            self._dict = dict(
                name=self.name,
                color=self.color,
                isvisible=self.isvisible,
                objects=self.objects
            )

        return self._dict

    @dict.setter
    def dict(self, v):
        self._dict = v


layers = [Layer(**i) for i in input]
