# -*- coding: utf-8 -*-
"""
Factory to create and configure a Flask instance
"""

from dotenv import load_dotenv
from flask import Flask
from logging.config import dictConfig
from os import getenv, makedirs


def create_app(env=None) -> Flask:
    """
    Returns an instance of a configured Dispatcher, containing the app itself and a prometheus endpoint.

    :param test_config: use test configuration
    :type param_test_config: dict
    :return: a configured Flask instance
    :rtype: Flask
    """
    load_dotenv(override=True)
    secret_key = getenv("SECRET_KEY")

    # Setup the logger
    dictConfig(
        {
            'version': 1,
            'formatters': {
                'default': {
                    'format': '[%(asctime)s] %(levelname)s in %(module)s at line %(lineno)d: %(message)s'
                }
            },
            'handlers': {
                'wsgi': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://flask.logging.wsgi_errors_stream',
                    'formatter': 'default'
                }
            },
            'root': {
                'level': getenv('LOG_LEVEL', 'INFO'),
                'handlers': ['wsgi']
            }
        }
    )

    # create and configure the ANCS app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        EXECUTOR_PROPAGATE_EXCEPTIONS=True
    )

    # ensure the instance folder exists
    try:
        makedirs(app.instance_path)
    except OSError:
        pass

    return app
