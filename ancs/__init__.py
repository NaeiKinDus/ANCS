# -*- coding: utf-8 -*-
"""
Factory to create and configure a Flask instance
"""

import os
from dotenv import load_dotenv
from flask import Flask
import traceback


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
    print('Loading drop-ins...')
    drop_ins: dict = {}
    modules_list = os.listdir('ancs/dropins')
    for module_name in modules_list:
        if module_name[-3:] != '.py' or module_name == '__init__.py':
            continue

        try:
            drop_in_module = __import__("ancs.dropins." + module_name[:-3], fromlist=["*"])
            drop_in = drop_in_module.DropIn()
        except Exception:
            print("Could not register drop in {}:\n{}".format(module_name[:-3], traceback.format_exc()))
            continue
        try:
            if drop_in.identity['handler']:
                app.add_url_rule(
                    drop_in.identity['endpoint'],
                    drop_in.identity['rule'],
                    drop_in.identity['handler'],
                    methods=drop_in.identity['methods']
                )
        except KeyError as excp:
            print(
                'Invalid `identity` attribute for module {}: {}'
                .format(module_name[:-3], str(excp))
            )
            continue
        except NotImplementedError as excp:
            print(
                'No `identity` attribute available for module "{}"'
                .format(module_name[:-3])
            )
            continue
        else:
            drop_ins[drop_in.identity['id']] = drop_in

    return drop_ins
