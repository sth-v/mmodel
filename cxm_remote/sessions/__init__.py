#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import json
from functools import wraps

import boto3

BUCKET = "lahta.contextmachine.online"
STORAGE = "https://storage.yandexcloud.net/"
REGION = "ru-central1"
AWS_ACCESS_KEY_ID = "YCAJEWyfhMEdpJv5yhuXECVLT"
AWS_SECRET_ACCESS_KEY = "YCPsGaw0zZXczhE-vtsG2_XYgM7yW1F_FqCg7de1"


class WatchSession:
    session = boto3.session.Session()
    storage = STORAGE

    def __init__(self, bucket=None):
        self.bucket = bucket


class S3Session(WatchSession):
    def __init__(self, bucket=None):
        super().__init__(bucket)
        self.s3 = self.session.client(
            service_name='s3',
            endpoint_url=self.storage
        )
        # self.s3.__init__()


class WatchTargets:
    def __init__(self):
        self._postfix = None
        self._prefix = None

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, val):
        self._prefix = val

    @prefix.deleter
    def prefix(self):
        del self._prefix

    @property
    def postfix(self):
        return self._postfix

    @postfix.setter
    def postfix(self, val):
        self._postfix = val

    @postfix.deleter
    def postfix(self):
        del self._postfix

    def targets(self, items):
        lst = []
        for path in items:

            split_targ = self.prefix.split("/")
            splitted = path["Key"].split("/")[:len(split_targ)]
            if self.postfix is not None:
                if (split_targ == splitted) and (path["Key"].split(".")[-1] == self.postfix):
                    lst.append(path)
            else:
                if split_targ == splitted:
                    lst.append(path)
        return set(lst)


class BucketSession(S3Session):
    def __init__(self, bucket=BUCKET, prefix=None, postfix=None, **kwargs):
        super().__init__(bucket=bucket)

        self.prefix = prefix
        self.postfix = postfix
        self.__dict__ |= kwargs
        for k in self.s3.meta.method_to_api_mapping.keys():
            setattr(self, k, self._decorate(getattr(self.s3, k)))
            # print(f"decorate {k}")

    def _decorate(self, m):
        @wraps(m)
        def wrapper(Key=None, Body=None, Prefix=self.prefix, Postfix=self.postfix, **kwargs):

            kwargs["Key"] = f"{Key}{Postfix}"
            kwargs["Body"] = Body
            kwargs["Prefix"] = Prefix
            kwargs["Bucket"] = self.bucket
            kw = dict()
            for k, v in kwargs.items():

                if k in m.__code__.co_varnames and (v is not None):
                    kw[k] = v
                else:
                    continue
            return m(**kw)

        return wrapper


class BucketTargetSession(BucketSession, WatchTargets):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer = self.state

    @property
    def state(self):
        return self.targets(self.s3.list_objects(Bucket=self.bucket)["Contents"])


import pandas as pd
from botocore.client import BaseClient


class AuthTypes(dict):
    auth_type: str = ""

    def credentials_json(self, path="credentials.json"):

        with open(path, "rb") as fp:
            self.__dict__ |= json.load(fp)

    def credentials(self):
        ...

    def dotenv(self):
        import dotenv
        dotenv.load_dotenv(dotenv.find_dotenv('.env'))
        dict.__ior__(self, dotenv.dotenv_values(dotenv.find_dotenv('.env')))

    def __call__(self, *args, path=None, **kwargs):
        if self.auth_type == "credentials":
            self.credentials()
        elif self.auth_type == "credentials.json":
            self.credentials_json(path) if path is not None else self.credentials_json()
        elif self.auth_type == "dotenv":
            self.dotenv()
        return self


class S3Client(WatchSession):
    storage = STORAGE
    service_name = 's3'
    region_name: str = REGION
    aws_access_key_id: str = None,
    aws_secret_access_key: str = None
    auth_dict = AuthTypes()

    def __init__(self, bucket: str = BUCKET, prefix="", auth_type="credentials.json", **kwargs):
        self.prefix = prefix
        self.auth_dict.auth_type = auth_type
        self.auth_dict(**kwargs)
        super().__init__(bucket)
        self.__dict__ |= self.auth_dict

    @property
    def client(self) -> BaseClient:
        return self.session.client(
            service_name=self.service_name,
            region_name=self.region_name,
            endpoint_url=self.storage,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=AWS_ACCESS_KEY_ID
        )

    def __getattr__(self, item):
        try:
            return getattr(self, item)
        except:

            return getattr(self.client, item)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

    def table(self, **kwargs):
        # print(self.bucket)
        return pd.DataFrame(self.client.list_objects_v2(Bucket=self.bucket, **kwargs)["Contents"])
