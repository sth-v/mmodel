#  Copyright (c)  CONTEXTMACHINE 2022.
#  AEC, computational geometry, digital engineering and Optimizing construction processes.
#
#  Author: Andrew Astakhov <sthv@contextmachine.space>
#
#  Computational Geometry, Digital Engineering and Optimizing your construction processes
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 2 of the License, or (at your
#  option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
#  the full text of the license.
#
#
import json
import os
import time
import boto3
import requests
from colored import attr, fg
from dataclasses import dataclass, field, fields
from timer import Timer
from typing import Union, Any


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


@dataclass
class Changes:
    patch: set[Union[str, None]] = field(default_factory=set)
    delete: set[Union[str, None]] = field(default_factory=set)

    def __init__(self):
        self.delete = set()
        self.patch = set()

    def __call__(self, delete: set = None, patch: set = None):
        if delete is not None:
            self.delete.update(delete)
        if patch is not None:
            self.patch.update(patch)


class BucketSession(S3Session, WatchTargets):
    def __init__(self, bucket=None, prefix=None, postfix=None, **kwargs):
        super().__init__(bucket=bucket, **kwargs)

        self.prefix = prefix
        self.postfix = postfix
        self.buffer = self.state



    @property
    def state(self):
        return self.targets(self.s3.list_objects(Bucket=self.bucket)["Contents"])


class BucketWatchDog(BucketSession):
    def __init__(self,url=None, **kwargs):

        super().__init__(**kwargs)
        self.url = url
        self.changes = Changes()
        self.changes(patch=self.buffer)
        print(
            f"\n{Timer()} {self.__class__.__name__} {fg('#F97BB0') + attr('bold')}init{attr('reset')} \n{fg('#F97BB0') + attr('bold')}configs{attr('reset')}\n    {fg('#FFA245')}bucket:{attr('reset')}{self.bucket}\n    {fg('#FFA245')}prefix:{attr('reset')} {self.prefix}\n    {fg('#FFA245')}postfix:{attr('reset')} {self.postfix}\n    {fg('#FFA245')}url:{attr('reset')} {self.url}\n    {fg('#FFA245')}initial changes:{attr('reset')}  {self.changes}")
        try:
            requests.post(self.url, data=json.dumps(self.changes))
        except:
            print("[WARN] Request Failed")
    def __call__(self, **kwargs):
        """
        @event: "all" , "add", "delete", "modify".
        🇬🇧 If "all" returns the dictionary with all keys ("add", "delete", "modify").
        Otherwise, the dictionary with the selected key
        🇷🇺 Если "all" вернется словарь со всеми ключами("add", "delete", "modify")
        В противном случае словарь с выбранным ключем
        return: dict[str, list]
        🇬🇧 The function automatically sends a POST request to self.url . Failure is ignored.
        For implementations that don't involve communication via api,
        the request content is returned from the __call__ method as a dictionary.
        🇷🇺 Функция автоматически отправляет запрос POST на self.url . Неудача игнорируется.
        Для реализаций не предполагающих общение через api,
        контент запроса возвращается из методa __call__ в виде словаря.
        """
        list_obj = self.targets(self.s3.list_objects(Bucket=self.bucket)["Contents"])
        set1 = set(map(lambda x: x["Key"], list_obj))
        set2 = set(map(lambda x: x["Key"], self.buffer))

        deleted = set2 - set1
        modified = set1 - (set2 - deleted)
        checklist = set1 - modified

        buffer_dict = dict(map(lambda x: (x["Key"], x["LastModified"]), self.buffer))
        for i, path in enumerate(list_obj):
            p = path['Key']
            if p in checklist:
                if path["LastModified"] == buffer_dict[p]:
                    pass
                else:
                    modified.add(p)

        if (len(list(deleted)) == 0) and (len(list(modified)) == 0):
            pass

        else:

            print(
                f"\n{Timer()} Bucket Watchdog {fg('#F97BB0') + attr('bold')}changes detection{attr('reset')}\n{fg('#FFA245')}changes:{attr('reset')}  {self.changes}")
            self.changes(delete=set(deleted), patch=set(modified))
            try:

                requests.post(self.url, data=json.dumps(self.changes))
            except:
                print("[WARN] Request Failed")
            self.buffer = self.state
        return self.changes


async def bucket_watch_session(bucket, target_url, delay=5.0, **kwargs):
    observer = BucketWatchDog(bucket=bucket, url=target_url, **kwargs)
    try:
        print(f"\n{observer.__class__.__name__} ID: {id(observer)} Running.")
        while True:
            observer()
            time.sleep(delay)
    except KeyboardInterrupt:
        del observer
        exit()

