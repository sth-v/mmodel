# ~/miniforge3/envs/bin/python
import json
import os
import socket
import sys

import redis

REDISPASSWORD = os.getenv("REDISPASSWORD")
REDISHOST = os.getenv("REDISHOST")
REDISPORT = os.getenv("REDISPORT")
SSLCAPATH = os.getenv("SSLCAPATH")

if __name__ == "__main__":
    print(REDISPASSWORD, REDISHOST, REDISPORT, SSLCAPATH)
    r = redis.StrictRedis(
        host="c-c9q1muil9vsf3ol4p3di.rw.mdb.yandexcloud.net",
        port=6380,
        password="caMbuj-tabxy1-pikkij",
        ssl=True,
        ssl_ca_certs="/usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt")
    HOST = 'localhost'  # Symbolic name meaning all available interfaces
    PORT = 50007  # Arbitrary non-privileged port
    print(r.keys())
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            try:
                while True:

                    dt, aad, dtt = "append", "part-15", conn.recv(1024 * 32)

                    if (not dt) | (dt == b"") | (dt == ""):
                        continue
                    else:

                        f = getattr(r, dt)
                        data = f(aad, dtt)

                        if isinstance(data, (list, dict, tuple, set)):
                            for i, d in enumerate(data):

                                if isinstance(d, (bytes, bytearray)):
                                    data[i] = d.decode()
                            conn.sendall(json.dumps(data).encode())
                        elif isinstance(data, (str, bytes, bytearray)):

                            conn.sendall(data.encode()) if isinstance(data, str) else conn.sendall(data)


                        else:
                            conn.sendall(json.dumps(data).encode())
            except KeyboardInterrupt:
                print('Interrupted')
                try:
                    sys.exit(0)
                except SystemExit:
                    os._exit(0)
