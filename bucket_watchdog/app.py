#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import itertools
import json
import argparse
import json
import os
import time
from datetime import date

import boto3
import requests
from colored import attr, fg


class Timer(object):
    """
    Basic immutable class fixing the initialisation time
    >>> t = Timer()
    >>> t()
    >>> t.date_tag
    >>> t.hours, t.minutes
    """
    TIME_SIGN = [3, 4, 5]

    def __init__(self):
        _ts = self.__class__.TIME_SIGN
        _init_date = date.today().isoformat()

        _init_time = [time.gmtime()[i] for i in range(len(time.gmtime()))]
        _hours, _minutes, _secs = [_init_time[i] for i in _ts]
        self.date_tag = int(_init_date.replace('-', '')[2:], 10)
        self.hours = '0{}'.format(_hours) if len(str(_hours)[:2]) == 1 else str(_hours)
        self.minutes = '0{}'.format(_minutes) if len(str(_minutes)[:2]) == 1 else str(_minutes)
        self.seconds = '0{}'.format(_secs) if len(str(_secs)[:2]) == 1 else str(_secs)

    def __str__(self):
        return f"{('#49B0CE')}{self.date_tag} {self.hours}:{self.minutes}.{self.seconds}{attr('reset')}"

    def __call__(self):
        return self.date_tag, self.hours, self.minutes, self.seconds





class BucketWatchDog:
    session = boto3.session.Session()
    storage = "https://storage.yandexcloud.net/"

    def __init__(self, bucket=None, prefix=None, postfix=None, url=None):
        self.s3 = self.session.client(
            service_name='s3',
            endpoint_url=self.storage
        )
        self.bucket = bucket
        self.prefix = prefix
        self.postfix = postfix
        self.url = url
        # print(self.prefix,self.postfix)
        self.buffer = self.targets(self.s3.list_objects_v2(Bucket=bucket, Prefix=self.prefix)["Contents"])

        init_changes = {
            "delete": [],
            "add": self.buffer['key'],
            "modify": []
        }
        bk=self.buffer["key"]

        print(
            f"\n{Timer()} Bucket Watchdog {fg('#F97BB0') + attr('bold')}init{attr('reset')} "
            f"\n\n{fg('#F97BB0') + attr('bold')}buffer:{attr('reset')}\n{bk}\n"
            f"\n{fg('#F97BB0') + attr('bold')}configs{attr('reset')}\n    {fg('#FFA245')}bucket:{attr('reset')}{self.bucket}\n    {fg('#FFA245')}prefix:{attr('reset')} {self.prefix}\n    {fg('#FFA245')}postfix:{attr('reset')} {self.postfix}\n    {fg('#FFA245')}url:{attr('reset')} {self.url}\n    {fg('#FFA245')}initial changes:{attr('reset')}  {init_changes}")
        try:
            requests.post(self.url, data=json.dumps(init_changes, ensure_ascii=False))
        except:
            print("[WARN] Request Failed")

    def __call__(self, event="all", **kwargs):
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
        list_obj = self.targets(self.s3.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)["Contents"])
        set1 = set(list_obj["key"])
        set2 = set(self.buffer["key"])
        deleted = set2 - set1
        new_details = set1 - (set2 - deleted)
        checklist = set1 - new_details
        modified = set()
        buffer_dict = dict(zip( self.buffer["key"],self.buffer["last_modify"]))
        for k, lm in zip( list_obj["key"],list_obj["last_modify"]):


            if k in checklist:
                if lm == buffer_dict[k]:
                    pass
                else:
                    modified.add(k)

        changes = {
            "delete": list(deleted),

            "add": list(new_details),
            "modify": list(modified)
        }

        if (len(list(deleted)) == 0) and (len(list(new_details)) == 0) and (len(list(modified)) == 0):
            pass

        else:
            print(f"\n{Timer()} Bucket Watchdog {fg('#F97BB0') + attr('bold')}changes detection{attr('reset')}\n{fg('#FFA245')}changes:{attr('reset')}  {changes}")
            try: requests.post(self.url, data=json.dumps(changes, ensure_ascii=False))
            except: print("[WARN] Request Failed")
            self.buffer = list_obj
        return changes

    def targets(self, items):

        lst = []
        lm=[]
        for req in items:
            path = req["Key"]
            lmm = req["LastModified"]
            path = path.replace(self.prefix, "")

            if not (path == ""):
                if not(self.postfix==''):
                    try:
                        if path.split(".")[1:] == self.postfix.split(".")[1:]:
                            lst.append(path)
                            lm.append(lmm)
                            #print(f"{fg('#F97BB0') + attr('bold')}watch :{attr('reset')}"
                            #      f"              {self.prefix}:{path}:{self.postfix}")

                        else:

                            #print(f"{fg('#F97BB0') + attr('bold')}passing :{attr('reset')}"
                            #      f"            {self.prefix}:{path}:{self.postfix}  # non match postfix")
                            pass
                    except:
                        pass
                else:
                    lst.append(path)
                    lm.append(lmm)
                    #print(f"{fg('#F97BB0') + attr('bold')}watch :{attr('reset')}"
                    #      f"              {self.prefix}:{path}:{self.postfix}")
            else:
                #print(f"{fg('#F97BB0') + attr('bold')}passing :{attr('reset')}"
                #      f"            {self.prefix}:{path}:{self.postfix}  # root path")
                pass
        return dict(key=lst, last_modify=lm)


def watchdog(event='all', delay=5.0, **kwargs):
    observer = BucketWatchDog(**kwargs)
    try:
        print("\nBucket Watchdog running")
        while True:
            observer(event=event)
            time.sleep(delay)
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AWS Object Storage watchdog.')
    parser.add_argument('-d', dest='delay', type=float, default=5.0)
    parser.add_argument('-e', dest='event', type=str, default="all", help=BucketWatchDog.__call__.__doc__)
    args = parser.parse_args()
    watchdog(bucket=os.environ["BUCKET"],
             prefix=os.environ["PREFIX"],
             postfix=os.environ["POSTFIX"],
             url=f'{os.environ["CALL_URL"]}/{os.environ["PREFIX"].replace("/","-")}?p={os.environ["POSTFIX"].replace(".", "_")}',
             event="all",
             delay=1.0
             )
