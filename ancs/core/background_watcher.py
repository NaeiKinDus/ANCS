# -*- coding: utf-8 -*-

from prometheus_client import Counter
from threading import Thread, Event


class BackgroundWatcher(Thread):
    """
    Thread class used to regularly poll the drop-ins.
    """

    # Time, in seconds, between each run of the watcher
    REFRESH_FREQUENCY = 10

    drop_ins: dict = {}
    _killSwitch: Event = None

    def __init__(self, drop_ins: dict = None) -> None:
        """
        Ctor

        :param drop_ins: dictionary of loaded drop ins
        :type drop_ins: dict
        """
        super().__init__()
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
            for di_name, di_instance in self.drop_ins.items():
                try:
                    di_instance.periodic_call()
                except BaseException as excp:
                    print('ERR: drop-in "{}" is invalid encountered an error: {}'.format(di_name, str(excp)))

            iteration += 1
            c_iter.inc()
            self._killSwitch.wait(self.REFRESH_FREQUENCY)

    def stop(self) -> None:
        """
        Stops the thread using an Event.
        @todo Currently inoperative with Flask / uWSGI.
        """
        self._killSwitch.set()
