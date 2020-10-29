# -*- coding: utf-8 -*-
from flask import Flask
from inspect import stack
from logging import Logger, getLogger
import os
import traceback
from typing import Iterable, Tuple


def load_drop_ins() -> Tuple[dict, dict]:
    """
    Loads existing drop-ins into the Flask app and returns a list
    of loaded drop-ins

    :return: a tuple containing loaded modules and API enabled handlers
    :rtype: Tuple[dict, dict]
    """
    logger = getLogger()
    logger.debug('loading drop-ins...')
    drop_ins: dict = {}
    api_namespaces: dict = {}
    for module_name in list_modules(logger):
        logger.debug('processing module "{}"'.format(module_name))

        # noinspection PyBroadException
        try:
            drop_in_module = __import__("app.dropins." + module_name, fromlist=["*"])
            drop_in = drop_in_module.DropIn(logger)
            module_id = drop_in.identity['id']
            logger.info('loaded drop-in {}'.format(module_name))
        except Exception:
            logger.error("could not register drop in {}:\n{}".format(module_name, traceback.format_exc()))
            continue
        try:
            # If an endpoint is defined, the module exposes an API
            api_namespaces[module_id] = drop_in_module.api_namespace
        except AttributeError:
            logger.info(
                'Module "{}" does not expose an API'
                .format(module_name)
            )
        except Exception as excp:
            logger.warning(
                'Unexpected error while loading module "{}", won\'t expose webservices. Error: {}'
                .format(module_name, str(excp))
            )
        else:
            logger.info(
                'registered module "{}" for API access'
                .format(module_name)
            )
        drop_ins[module_id] = drop_in

    return drop_ins, api_namespaces


def list_modules(logger: Logger) -> Iterable[str]:
    """
    Lists all loadable modules and yield them.

    :param logger: Logger instance
    :type logger: Logger
    :return: Iterable[str]
    """
    drop_ins_path = os.path.dirname(os.path.abspath(stack()[0][1]))
    for file in os.listdir(drop_ins_path):
        logger.debug('checking drop-in candidate "{}"'.format(file))
        if os.path.isfile(os.path.join(drop_ins_path, file)):
            purged_name = file[:file.rindex('.')]
            extension = file[file.rindex('.') + 1:]
            if extension != 'py':
                logger.debug('-> invalid extension')
                continue
            if purged_name not in ('__init__',):
                logger.debug('viable candidate found')
                yield purged_name
            else:
                logger.debug('-> invalid name')
                continue
        else:
            logger.debug('-> not a file')
            continue


loaded_drop_ins, api_drop_ins = load_drop_ins()
