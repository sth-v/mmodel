import Rhino

input = [{
    "name": "Laser Cut",
    "color": [255, 255, 255],
    "objects": []
},
    {
        "name": "Frezerovka",
        "color": [255, 0, 0],
        "objects": []
    },

    {
        "name": "Razmetka Frezer",
        "color": [0, 255, 0],
        "objects": []
    },
    {
        "name": "Markirovka Laser",
        "color": [255, 255, 0],
        "objects": []
    }]


class Layer(object, dict):
    objects = []

    def __init__(self, name="Default", color=(255, 255, 255), isvisible=True, objects=[], **properties):
        object.__init__(self)
        self.name = name
        self.color = color

        self._layer = Rhino.DocObjects.Layer()
        self._layer.Name = self.name
        self._layer.Color = self.color
        self._layer.PlotColor = self.color
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

    def __iadd__(self, other):
        try:
            self.objects += list(other)
        except:
            self.objects += [other]

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
