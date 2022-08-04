import copy

import boto3
import pandas as pd


class BucketConsumer:
    session = boto3.session.Session()
    storage = "https://storage.yandexcloud.net/"

    def __init__(self, bucket=None, prefix=None, postfix=None):
        self.s3 = self.session.client(
            service_name='s3',
            endpoint_url=self.storage
        )
        self.bucket = bucket
        self.prefix = prefix
        self.postfix = postfix
        self.upd_keys_default = dict(modify=dict(), delete=[])
        self.upd_keys = copy.deepcopy(self.upd_keys_default)

    def __call__(self, **kw):
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
        return self.request_call(**kw)


    def object_modify(self, state):

        for key in state.modify:
            obj = self.s3.get_object(Bucket=self.bucket, Key=key)
            self.upd_keys["modify"][key] = True

    def object_add(self, state):

        for key in state.add:
            obj = self.s3.get_object(Bucket=self.bucket, Key=key)

            self.upd_keys["modify"][key] = True

    def object_delete(self, state):
        for key in state.delete:
            del self.upd_keys["modify"][key]
            self.upd_keys["delete"].append(key)

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
        return lst

    def request_call(self, **kwargs):
        s = copy.deepcopy(self.upd_keys)
        setattr(self, 'upd_keys', dict(modify=dict(), delete=[]))
        return s



    def upd_call(self, state):
        self.object_delete(state)
        self.object_add(state)
        self.object_modify(state)
