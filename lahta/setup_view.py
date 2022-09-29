#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import sys

NO_VIEW = [ \
    '/tmp',
    '/tmp/mmodel_server_remote', '/tmp/mmodel_server_remote', '/tmp/mmodel_server_remote/lahta/',
    '/tmp/mmodel_server_remote/lahta',
    '/tmp/mmodel_server_remote/bucket_watchdog/', '/tmp/mmodel_server_remote/mm/tests/',
    '/tmp/mmodel_server_remote/tests/', '/tmp/mmodel_server_remote/bucket_watchdog/',
    '/tmp/mmodel_server_remote/mm/tests/', '/tmp/mmodel_server_remote/tests/', '/Users/andrewastakhov/mmodel'
                                                                               '/tmp/mmodel_server_remote/',
    '/tmp/mmodel_server_remote/',
    '/tmp/mmodel_server_remote/bucket_watchdog', '/tmp/mmodel_server_remote/mm/tests',
    '/tmp/mmodel_server_remote/tests', '/tmp/mmodel_server_remote/bucket_watchdog',
    '/tmp/mmodel_server_remote/mm/tests', '/tmp/mmodel_server_remote/tests', '/Users/andrewastakhov/mmodel'
]


class AppBind:
    def add(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        pass


view = AppBind()
DRAW = False
for env in NO_VIEW:
    if env in sys.path:
        DRAW = False

        view = AppBind()
        break
    else:
        DRAW = True
        continue
if DRAW:
    from compas_view2.app import App

    view = App()
