from typing import Callable
from colored import fg, attr


class CliTemplate(Callable):
    templates = {}

    col = 7
    att = 2

    highlight = '[{}]'

    def __new__(cls, name, bases, dct):
        if name in cls.templates.keys():
            return cls.templates[name]
        else:

            c = super().__new__(cls)
            for k, v in dct.items():
                setattr(c, k, v)
            c.__init__()
            cls.templates[name] = c
            return c

    def __call__(self, st, nst=''):
        print(self.__tstr__().format(st) + ' ' + nst)

    def __tstr__(self):
        ff = f"{fg(self.col)}{attr(self.att)}"
        return ff + self.highlight + f"{attr(0)}"


class TemplateBase(metaclass=CliTemplate):
    col = 141
    att = 'bold'


class TemplateContext(metaclass=CliTemplate):
    col = 63
    att = 'bold'


class TemplateVcs(metaclass=CliTemplate):
    col = 141
    att = 'bold'


class TemplateObjVcs(metaclass=CliTemplate):
    col = 141
    att = 'bold'
    highlight = '@{}'


class TemplateTestsFail(metaclass=CliTemplate):
    col = 9
    att = 'bold'
    highlight = '\n!Test {}'


class TemplateTestsSucsess(metaclass=CliTemplate):
    col = 41
    att = 'bold'
    highlight = '\n*Test {}'
