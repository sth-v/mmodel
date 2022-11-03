"""
Для того чтобы это работало
необходимо присутствие пространства имен py3ghredis

Объединение этих пакетов не возможно, как по причине разных версий python ,
так и в силу более широкогих возможностей использования py3ghredis.

По сути паттерн internal_redis_api + py3ghredis может быть без труда обобщен
до связок с любыми закрытыми програмными комплексами.
Такими как Revit, Tekla, и прочими решениями поддерживающими внутренний скриптинг.

Также паттерн стоит рассматривать как замену REST  ориентированному подходу,
такому как Grasshopper Hops

"""

__author__ = "andrewastakhov"

import copy
import json
import socket


# ---------------------------------------------------------------------------------
#    Да это достаточно быстро  >>>     ️   ....
# ---------------------------------------------------------------------------------

# Простите ...


class GhRedisSocket(object):
    """
    GhRedisSocket :
    >>> def main(host, port, command, msg=None):
    ...     with GhRedisSocket(host, port) as client:
    ...     print(client.qwery(command, msg))

    >>> if __name__ == "__main__":
    ...     print(host='localhost', port=50007, command="keys")
    """

    def __init__(self, host, port, **kwargs):
        object.__init__(self)
        self.HOST = host
        self.session_data = {}
        self.PORT = port
        self.__dict__.update(kwargs)

    def send(self, msg):
        self.s.sendall(msg)
        data = copy.deepcopy(self.s.recv(1024 ** 2))
        # print('Received', repr(data))
        return data

    def __enter__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.s.connect((self.HOST, self.PORT))

        def wrapper(command, msg=None):
            d = json.dumps([command, msg]) if msg else json.dumps([command])

            data = self.send(d)

            self.session_data[command] = copy.deepcopy(data)

            return data

        self.qwery = wrapper
        return self

    def __exit__(self, *args):
        pass
