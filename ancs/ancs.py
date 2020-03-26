#!/usr/bin/python3
# -*- coding: utf-8 -*-

from ancs import create_app, load_drop_ins
from ancs.core.background_watcher import BackgroundWatcher
import atexit
from os import getenv
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import signal


ancs_app = create_app(getenv('FLASK_ENV', "test"))
drop_ins = load_drop_ins(ancs_app)

# Start watcher thread
try:
    thd = BackgroundWatcher(ancs_app, drop_ins)
    thd.start()
    atexit.register(lambda: thd.stop())
except BaseException as excp:
    ancs_app.logger.error('could not start background watcher, aborting ! Reason: {}'.format(excp))
else:
    ancs_app.logger.debug('started background watcher, frequency = {}'.format(BackgroundWatcher.REFRESH_FREQUENCY))

# @todo signals setup not working ATM, must look at Flask / UWSGI doc.
# Setting up signal trapping for a clean exit
signal.signal(signal.SIGHUP, lambda: thd.stop())
signal.signal(signal.SIGTERM, lambda: thd.stop())
signal.signal(signal.SIGINT, lambda: thd.stop())

ancs_app.logger.info('initialization ended successfully')

# add Prometheus entry point for metrics
app = DispatcherMiddleware(
    ancs_app,
    {
        '/metrics': make_wsgi_app()
    }
)
