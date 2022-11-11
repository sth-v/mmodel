import json
import socket
import os
import redis

if __name__ == "__main__":
    r = redis.StrictRedis(
        host="c-c9q1muil9vsf3ol4p3di.rw.mdb.yandexcloud.net",
        port=6380,
        password=os.getenv("REDISPSWD"),
        ssl=True,
        ssl_ca_certs="/usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt")

    HOST = 'localhost'  # Symbolic name meaning all available interfaces
    PORT = 50007  # Arbitrary non-privileged port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            try:
                while True:

                    dt = conn.recv(1024 ** 2)
                    print(dt)
                    if (not dt) | (dt == b"") | (dt == ""):
                        pass
                    else:
                        kv = json.loads(dt)
                        if len(kv) == 2:
                            key, value = kv
                            f = getattr(r, key)
                            data = f(value)
                        else:
                            f = getattr(r, kv[0])
                            data = f()

                        if isinstance(data, (list, bytes)):
                            conn.sendall(json.dumps([k.decode() for k in data]).encode())
                        else:
                            conn.sendall(json.dumps(data).encode())
            except KeyboardInterrupt:
                print('Interrupted')
                try:
                    sys.exit(0)
                except SystemExit:
                    os._exit(0)
