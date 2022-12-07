# TO STAY COMPLIANT WITH THE CAD EXCHANGER SDK LICENSE AGREEMENT YOU SHOULD UPDATE THE LICENSE KEY WITH EVERY UPDATE THEREOF.
# Building an application with CAD Exchanger SDK requires an active subscription and an up-to-date SDK license key.
# When your license key expires you may no longer rebuild your application with CAD Exchanger SDK.
# If you already received a newer version of the license key then please use it to replace the expired license key.
# Otherwise please contact sales@cadexchanger.com to renew your license.


from setupsecrets import setup_secrets


def Value() -> str:
    return setup_secrets()["CADEX_LICENSE"]
