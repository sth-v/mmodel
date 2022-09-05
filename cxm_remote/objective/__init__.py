import boto3
from cxm_remote.sessions import S3Client
from mm.baseitems import Item
from mm.utils import DotView


class BaseClientDescriptor(object):

    def __set_name__(self, owner, name):
        self.bucket = owner.bucket
        self.prefix = owner.prefix

        self.name = name

    def __get__(self, instance, owner=None):
        return instance.__client__.get_object(Bucket=self.bucket, Key=f"{self.prefix}{self.name}")

    def __set__(self, instance, value):
        instance.__client__.put_object(Bucket=self.bucket, Key=f"{self.prefix}{self.name}{instance.suffix}", Body=value)


class HookDescriptor(BaseClientDescriptor):

    def __set__(self, instance, value):
        super(HookDescriptor, self).__set__(instance, instance.__sethook__(value))

    def __get__(self, instance, owner=None):
        return instance.__gethook__(super(HookDescriptor, self).__get__(instance, owner))


class ClientDescriptor(object):
    def __set_name__(self, owner, name):
        self.bucket = owner.bucket
        self.prefix = owner.prefix
        self.name = name

    def __get__(self, instance, owner=None):
        print(instance, owner)
        return instance.__gethook__(instance.client.get_object(Bucket=self.bucket, Key=f"{self.prefix}{self.name}"))

    def __set__(self, instance, value):
        print(instance, value)
        instance.client.put_object(Bucket=self.bucket, Key=f"{self.prefix}{self.name}{instance.suffix}",
                                   Body=instance.__sethook__(value))


class DCt(dict):

    def __init__(self, client: S3Client):
        dict.__setattr__("__client__", client)
        self.keynames = []

    def __setattr__(self, key, value):
        if not key in self.keynames:
            self.keynames.append(self.keynames)
        dict.__setattr__(key, value)


class RemoteType(type):

    @classmethod
    def __prepare__(metacls, name, bases, prefix=None, **kws):
        dct = super(RemoteType, metacls).__prepare__(name, bases)
        print(dct)

        client = S3Client(**kws)
        kws["prefix"] = prefix

        table = client.table(Prefix=prefix)
        kws["__client__"] = client
        kws.update(dct)
        print(table.Key)
        for k in table.Key:
            ky=k.replace(prefix, '')
            if not ky == '':
                kws[ky] = HookDescriptor()
            else:
                pass
        return kws

    def __new__(mcs, classname, bases, dct, **kwds):

        print(classname, bases, dct)
        return type(classname, (Item,) + bases, dct)



import json


class H(metaclass=RemoteType, bucket="lahta.contextmachine.online", prefix="cxm/internal/"):

    def __gethook__(self, hook):
        print(f"{self}.__gethook__() -> body")
        return json.loads(hook["Body"].read())

    def __sethook__(self, hook):
        print(f"{self}.__sethook__()")
        return hook
