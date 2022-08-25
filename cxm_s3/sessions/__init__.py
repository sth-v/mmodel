#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import os
from functools import wraps

import boto3

os.environ["STORAGE"]="https://storage.yandexcloud.net/"
class WatchSession:
    session = boto3.session.Session()
    storage = os.environ["STORAGE"]

    def __init__(self, bucket=None):
        self.bucket = bucket


class S3Session(WatchSession):
    def __init__(self, bucket=None):
        super().__init__(bucket)
        self.s3 = self.session.client(
            service_name='s3',
            endpoint_url=self.storage
        )


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
    def __init__(self, bucket=None, prefix=None, postfix=None, **kwargs):
        super().__init__(bucket=bucket)

        self.prefix = prefix
        self.postfix = postfix
        self.__dict__ |= kwargs
        for k in self.s3.meta.method_to_api_mapping.keys():

            setattr(self, k, self._decorate(getattr(self.s3,k)))
            print(f"decorate {k}")

    def _decorate(self, m):
        @wraps(m)
        def wrapper(key, body=None, prefix=self.prefix, postfix=self.postfix, **kwargs):
            if body is not None:
                return m(Bucket=self.bucket, Key=f"{prefix}/{key}{postfix}", **kwargs)
            else:
                return m(Bucket=self.bucket, Key=f"{prefix}/{key}{postfix}", Body=body, **kwargs)


        return wrapper


class BucketTargetSession(BucketSession, WatchTargets):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer = self.state

    @property
    def state(self):
        return self.targets(self.s3.list_objects(Bucket=self.bucket)["Contents"])
