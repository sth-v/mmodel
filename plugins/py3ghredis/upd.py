import socketserver

import redis

if __name__ == "__main__":
    r = redis.StrictRedis(
        host="c-c9q1muil9vsf3ol4p3di.rw.mdb.yandexcloud.net",
        port=6380,
        password="caMbuj-tabxy1-pikkij",
        ssl=True,
        ssl_ca_certs="/usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt")


class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def handle(self):
        data = self.request[0].strip()
        print(data)
        socket = self.request[1]
        print(socket)
        print("{} wrote:".format(self.client_address[0]))
        print(data)
        res = redis.append("panel-test", data)
        socket.sendto(res, self.client_address)


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
        server.serve_forever()
