from mm.baseitems import Item


class Element(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


class Panel(Item):
    # __init__ нужен только когда требуется задать специфический порядок первой инициализации
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        # Здесь писать все что нужно для инициализации
