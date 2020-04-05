# -*- coding: utf-8 -*-
"""
Factory to create and configure a Flask instance
"""

from dotenv import load_dotenv
from flask import Flask
from inspect import stack
from logging.config import dictConfig
from logging import Logger
import os
import traceback
from typing import Iterable


def create_app(env=None) -> Flask:
    """
    Returns an instance of a configured Dispatcher, containing the app itself and a prometheus endpoint.

    :param test_config: use test configuration
    :type param_test_config: dict
    :return: a configured Flask instance
    :rtype: Flask
    """
    load_dotenv(override=True)
    secret_key = os.getenv("SECRET_KEY")

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
                'level': os.getenv('LOG_LEVEL', 'INFO'),
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
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app


def load_drop_ins(app: Flask) -> dict:
    """
    Loads existing drop-ins into the Flask app and returns a list
    of loaded drop-ins

    :param app: The flask app
    :type app: Flask
    :return: loaded modules
    :rtype: dict
    """
    logger = app.logger
    logger.debug('loading drop-ins...')
    drop_ins: dict = {}
    for module_name in list_modules(logger):
        logger.debug('processing module "{}"'.format(module_name))

        try:
            drop_in_module = __import__("app.dropins." + module_name, fromlist=["*"])
            drop_in = drop_in_module.DropIn(logger)
            logger.info('loaded drop-in {}'.format(module_name))
        except Exception:
            logger.error("could not register drop in {}:\n{}".format(module_name, traceback.format_exc()))
            continue
        try:
            if drop_in.identity['handler']:
                app.add_url_rule(
                    drop_in.identity['endpoint'],
                    drop_in.identity['rule'],
                    drop_in.identity['handler'],
                    methods=drop_in.identity['methods']
                )
            module_id = drop_in.identity['id']
        except KeyError as excp:
            logger.warning(
                'invalid `identity` attribute for module {}, won\'t expose webservices: {}'
                .format(module_name, str(excp))
            )
            continue
        except NotImplementedError:
            logger.warning(
                'No `identity` attribute available for module "{}", won\'t expose webservices.'
                .format(module_name)
            )
            continue
        else:
            drop_ins[module_id] = drop_in
            logger.info(
                'registered module "{}" for webservices, exposing endpoint "/{}" to methods {}'
                .format(module_name, drop_in.identity['rule'], drop_in.identity['methods'])
            )

    return drop_ins


def list_modules(logger: Logger) -> Iterable[str]:
    """
    Lists all loadable modules and yield them.

    :param path: path where the modules are located
    :type path: str
    :return: Iterable[str]
    """
    drop_ins_path = os.path.dirname(os.path.abspath(stack()[0][1])) + '/dropins'
    for file in os.listdir(drop_ins_path):
        logger.debug('checking drop-in candidate "{}"'.format(file))
        if os.path.isfile(os.path.join(drop_ins_path, file)):
            purged_name = file[:file.rindex('.')]
            extension = file[file.rindex('.') + 1:]
            if extension != 'py':
                logger.debug('-> invalid extension')
                continue
            if purged_name not in ('__init__'):
                logger.debug('viable candidate found')
                yield purged_name
            else:
                logger.debug('-> invalid name')
                continue
        else:
            logger.debug('-> not a file')
            continue
