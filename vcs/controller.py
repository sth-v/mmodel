import compas

from .utils import Version


class VersionController(object):

    def __init__(self, _h):

        self.history = _h
        print(f'\033[92m[{self.__class__.__name__}] \033[37m run ...\033[37m')
        print(f'\033[92m[{self.__class__.__name__}] \033[37m call mmodel history: {self.history}\033[37m')
        print(f'\033[92m[{self.__class__.__name__}] \033[37m read history: {self.history}\033[37m')
        print(f'\033[92m[{self.__class__.__name__}] \033[37m history data read to >>> cls.history_data\033[37m')

        self.changes = []

    def read(cls):
        history_data = compas.json_load(cls.history)
        return history_data

    def write(cls, history_data):
        compas.json_dump(history_data)

    def last_version(cls, item_cls, history_data):
        var = history_data[item_cls.__name__.upper()]
        vers = list(var.keys())

        # print(vers)
        def validator(vers):
            new = []
            for v in vers:
                if len(v) == 8:
                    print('valid: {}'.format(v))
                    new.append(v)
                else:
                    print('\033[31minvalid: {}'.format(v))
                    print(
                        f'Version {v} cannot be used as it does not comply with the protocol format\n    the length of '
                        f'the character string must be 8 characters, now: {len(v)}\033[37m')

            return new

        srtvers = validator(vers)
        srtvers.sort(reverse=True)

        last_version = srtvers[0]

        print(f'\033[92mlast: {last_version}\033[37m')
        return last_version

    def change_history(self, name, kwargs: dict):
        history_data = self.read()
        if name.upper() not in history_data.keys():
            v = Version(val=None)
            history_data[name.upper()] = {v(): kwargs}

        named_history = history_data[name.upper()]
        named_history |= kwargs
        history_data |= named_history
        compas.json_dump(history_data, self.history)

    def item_from_last_version(self, item_cls):
        history_data = self.read()
        if item_cls.__name__.upper() not in history_data.keys():
            v = Version(val=None)
            history_data[item_cls.__name__.upper()] = {v(): {'name': item_cls.__name__.lower()}}
        print(f'{self.__class__.__name__}: {item_cls.__name__} search last version...')
        last_v = self.last_version(item_cls, history_data)
        print(f'{self.__class__.__name__}:  ')
        scope_ = history_data[item_cls.__name__.upper()]
        dct = scope_[str(last_v)]
        dct |= {'version': last_v}
        return dct

    def item_from_spec_version(self, item_cls, version):
        history_data = self.read()
        var = history_data[item_cls.__name__.upper()]
        return var[str(version)]

    def read_version(self, item):
        history_data = self.read()
        var = history_data[item.__class__.__name__.upper()]

        try:

            last_version = self.last_version(item.__class__, history_data)

            print(f'{self.__class__.__name__}: last version from {item.__class__.__name__} : {last_version}')
            if item.version == last_version:
                print(f'{self.__class__.__name__}: pbj version is last')
                return item
            elif item.version > last_version:
                print(f'{self.__class__.__name__}: pbj version is most\n change history')
                var[item.version()] = item.__dict__
                history_data[item.__class__.__name__.upper()] = var
                return item
            else:
                print(f'{self.__class__.__name__}: item version is old')
                new_item = self.item_from_version(item.__class__)

            return new_item
        except Exception:
            print(f'{self.__class__.__name__}: no item with this name')

    def add_new_cls(self, item_cls):
        history_data = self.read()
        history_data[item_cls.__name__.upper()] = {}
        self.write(history_data)
