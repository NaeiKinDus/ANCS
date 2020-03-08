# -*- coding: utf-8 -*-
"""
Factory to create and configure a Flask instance
"""

import os
from flask import Flask
from dotenv import load_dotenv
from ancs.core.background_watcher import background_watcher


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
    database = os.getenv("ANCS_DATABASE")

    # create and configure the ancs app
    app = Flask(__name__, instance_relative_config=True)

    if not database:
        database = os.path.join(app.instance_path, 'ancs.sqlite')

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE=database,
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
        if module_name[-3:] != '.py':
            continue

        try:
            dropin_module = __import__("ancs.dropins." + module_name[:-3], fromlist=["*"])
            drop_in = dropin_module.DropIn()
            drop_ins[drop_in.identity['id']] = drop_in
        except Exception as excp:
            print("Could not register drop in {}: {}".format(module_name[:-3], str(excp)))
            continue
        try:
            app.add_url_rule(
                drop_in.identity['endpoint'],
                drop_in.identity['rule'],
                drop_in.identity['handler'],
                methods=drop_in.identity['methods']
            )
        except KeyError as excp:
            print("Invalid identity for module {}: {}".format(module_name[:-3], str(excp)))
            continue

    return drop_ins
