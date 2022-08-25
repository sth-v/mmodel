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
#  """
#
#
import json
import os
from cxm_s3.sessions import BucketTargetSession, S3Session, WatchSession, WatchTargets
import boto3
import typing
import typing_extensions as tyex
import pandas as pd


class AppSession(S3Session):
    def __init__(self, buck=None):
        super().__init__(bucket=buck)
        self.dev_path = os.environ["CXM_DEV_PATH"]
        self.config = json.loads(self.s3.get_object(Bucket=self.bucket, Key=os.environ["CXM_DEV_PATH"].format(
            os.environ["CXM_APP_NAME"]) + "/config.json")["Body"].read())

    def g1(self, name, pref):
        return self.s3.get_object(Bucket=self.bucket, Key=pref + name)["Body"]

    def g2(self, pref):
        return self.s3.list_objects(Bucket=self.bucket, Prefix=pref)["Contents"]

    def g4(self, name, pref):
        return self.s3.get_object(Bucket=self.bucket, Key=pref + name)["Body"]

    def g3(self, pref):
        return list(map(lambda x: x["Key"].split("/")[-1], self.g2(pref)))

    def patch(self, name, data, pref):
        self.s3.put_object(Key=pref + name, Bucket=self.bucket, Body=data)
