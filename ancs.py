#!/usr/bin/python3
# -*- coding: utf-8 -*-

from app import create_app
from app.core.background_watcher import BackgroundWatcher
import atexit
from os import getenv
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware


app = create_app(getenv('FLASK_ENV', "development"))

from app.dropins import loaded_drop_ins
drop_ins = loaded_drop_ins

from app.api.module import api
api.init_app(app)

# Start watcher thread
try:
    thd = BackgroundWatcher(app, drop_ins)
    thd.start()
    atexit.register(lambda: thd.stop())
except BaseException as excp:
    app.logger.error('could not start background watcher, aborting ! Reason: {}'.format(excp))
else:
    app.logger.debug('started background watcher, frequency = {}'.format(BackgroundWatcher.REFRESH_FREQUENCY))


# add Prometheus and REST entry points
app.wsgi_app = DispatcherMiddleware(
    app.wsgi_app,
    {
        '/metrics': make_wsgi_app()
    }
)

app.logger.info('initialization ended successfully')
