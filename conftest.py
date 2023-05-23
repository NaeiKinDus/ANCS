# -*- coding: utf-8 -*-
from app import create_app
from os import environ
import pytest
import sys

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True
    })

    yield app

@pytest.fixture(scope="session")
def dummy_logger():
    DummyLogger = type(
        'DummyLogger',
        (),
        {
            "__getattr__": lambda *args: None,
            "__setattr__": lambda *args: None,
            "critical": lambda *args: None,
            "debug": lambda *args: None,
            "error": lambda *args: None,
            "exception": lambda *args: None,
            "fatal": lambda *args: None,
            "info": lambda *args: None,
            "log": lambda *args: None,
            "warn": lambda *args: None,
            "warning": lambda *args: None
        }
    )
    return DummyLogger()

pytest_plugins: tuple[str, ...] = ("pytest_order",)

def pytest_configure(config: pytest.Config) -> None:
    environ["SEA_LEVEL_PRESSURE"] = "1021.0"
    sys.__pytest_running__ = True

def pytest_unconfigure(config: pytest.Config) -> None:
    del sys.__pytest_running__
