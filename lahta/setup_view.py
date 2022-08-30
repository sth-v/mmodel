import sys

DRAW = None
NO_VIEW = ['/Users/andrewastakhov/mmodel', '/tmp/mmodel_server_remote/']


class AppBind:
    def add(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        pass


for env in NO_VIEW:
    if env in sys.path:
        DRAW = False

        view = AppBind()
        break
    else:
        DRAW = True
        from compas_view2.app import App

        view = App()
        continue
