# -*- coding: utf-8 -*-
from app.dropins import api_drop_ins
from flask_restx import Api
from logging import getLogger

API_VERSION = '0.1'
API_TITLE = 'ANCS API'
API_DESCR = 'ANCS API access to drop-ins capabilities'

api = Api(
    version=API_VERSION,
    title=API_TITLE,
    description=API_DESCR
)

logger = getLogger()
api_modules = api_drop_ins
for module_id, api_namespace in api_modules.items():
    api.add_namespace(api_namespace, path="/api/{}".format(module_id))
