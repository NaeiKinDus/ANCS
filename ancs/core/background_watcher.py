# -*- coding: utf-8 -*-

from flask import Flask
from logging import Logger
from prometheus_client import Counter
from threading import Thread, Event


class BackgroundWatcher(Thread):
    """
    Thread class used to regularly poll the drop-ins.
    """

    # Time, in seconds, between each run of the watcher
    REFRESH_FREQUENCY = 10

    app: Flask = None
    logger: Logger = None
    drop_ins: dict = {}
    _killSwitch: Event = None

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
        self._killSwitch = Event()

    def run(self) -> None:
        """
        Periodic measurements and cleanup thread. Used to make measurements
        and update Prometheus counters.

        :param drop_ins:
        :return:
        """
        iteration = 0
        c_iter = Counter('num_watcher_iter', 'Number of iterations the background watcher performed')
        while not self._killSwitch.is_set():
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
            self._killSwitch.wait(self.REFRESH_FREQUENCY)

    def stop(self) -> None:
        """
        Stops the thread using an Event.
        @todo Currently inoperative with Flask / uWSGI.
        """
        self._killSwitch.set()
