#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import gzip
import json
import os

from cxm_s3.sessions import S3Session
import argparse

sess = S3Session(bucket="lahta.contextmachine.online")


def three_gzip_reader():
    with gzip.open(sess.s3.get_object(Bucket=sess.bucket, Key="tmp/panel_f1")["Body"], compresslevel=9) as gzstreem:
        data = json.load(gzstreem)


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
