#!/usr/bin/python3
# -*- coding: utf-8 -*-

from ancs import create_app, load_drop_ins
from ancs.core.background_watcher import background_watcher
from os import getenv
from prometheus_client import make_wsgi_app
from threading import Thread
from werkzeug.middleware.dispatcher import DispatcherMiddleware


ancs_app = create_app(getenv('FLASK_ENV', "test"))
drop_ins = load_drop_ins(ancs_app)

# Start watcher thread
try:
    thd = Thread(target=background_watcher, args=(drop_ins,))
    thd.start()
except:
    print("Could not start thread !")
else:
    print("Properly started thread !")
print('Initialization ended.')

# add Prometheus entry point for metrics
app = DispatcherMiddleware(
    ancs_app,
    {
        '/metrics': make_wsgi_app()
    }
)
