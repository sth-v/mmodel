#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import gzip
import json
import os

from cxm_remote.sessions import S3Session
import argparse

sess = S3Session(bucket="lahta.contextmachine.online")


def gzip_encoder(data):

    return gzip.compress(data.encode(), compresslevel=9)


def gzip_decoder(data):
    return gzip.decompress(data).decode()

def three_gzip_light_reader():
    with gzip.open(sess.s3.get_object(Bucket=sess.bucket, Key="tmp/panel_f1")["Body"], compresslevel=9) as gzstreem:
        data = json.load(gzstreem)
    return data


def togzipone(name):
    jsn = sess.s3.get_object(Bucket=sess.bucket, Key=f"tmpj/{name}")["Body"].read()
    print(f"Success GET {name}")
    sess.s3.put_object(Bucket=sess.bucket, Key=f"tmp/{name}", Body=gzip.compress(jsn, compresslevel=9))
    print(f"Success PUT {name}")
    print(f"exit")


if __name__ == "__main__":
    print("input fnames: ")
    names = input().split(" ")
    for name in names:
        print(f"Start {name}")
        togzipone(name)
