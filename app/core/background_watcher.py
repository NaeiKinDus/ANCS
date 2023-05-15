# -*- coding: utf-8 -*-

from flask import Flask
from logging import Logger
from prometheus_client import Counter
from threading import Thread, Event
from app.core.helper.singleton import Singleton


class BackgroundWatcher(Thread, metaclass=Singleton):
    """
    Thread class used to regularly poll the drop-ins.
    """

    # Time between each run of the watcher, in seconds
    REFRESH_FREQUENCY = 10
    # Time before the first periodic call is performed, in seconds
    DELAY_BEFORE_ACTIVATION = 10

    app: Flask = None
    logger: Logger = None
    drop_ins: dict = {}
    _kill_switch: Event = None

    def __init__(self, app: Flask, drop_ins: dict = None, **kwargs) -> None:
        """
        Ctor

        :param drop_ins: dictionary of loaded drop ins
        :type drop_ins: dict
        """
        super().__init__(**kwargs)
        self.app = app
        self.logger = app.logger
        if not drop_ins:
            drop_ins = {}
        self.drop_ins = drop_ins
        self._kill_switch = Event()

    def run(self) -> None:
        """
        Periodic measurements and cleanup thread. Used to make measurements
        and update Prometheus counters.

        :param drop_ins:
        :return:
        """
        iteration = 0
        c_iter = Counter('num_watcher_iter', 'Number of iterations the background watcher performed')
        self._kill_switch.wait(self.DELAY_BEFORE_ACTIVATION)
        while not self._kill_switch.is_set():
            self.logger.debug('Starting background watcher cycle...')
            for di_name, di_instance in self.drop_ins.items():
                self.logger.debug('- running periodic_call for drop-in {} ({})'.format(di_name, type(di_instance)))
                try:
                    di_instance.periodic_call()
                except BaseException as excp:
                    self.logger.error('drop-in "{}" encountered an error: {}'.format(di_name, excp))
                else:
                    self.logger.debug('- call succeeded')

            iteration += 1
            c_iter.inc()
            self.logger.debug('Success')
            self._kill_switch.wait(self.REFRESH_FREQUENCY)

    def stop(self) -> None:
        """
        Stops the thread using an Event.
        @todo Currently inoperative with Flask / uWSGI.
        """
        self._kill_switch.set()
