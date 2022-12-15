import os

from setupsecrets import setup_secrets

myenv = setup_secrets()
from compute_rhino3d import Util
Util.apiKey = os.getenv('RHINO_COMPUTE_API_KEY')
Util.url = "http://" + os.getenv('RHINO_COMPUTE_URL') + ":" + os.getenv('RHINO_COMPUTE_PORT') + "/"
from .pyeval import ComputeBinder
