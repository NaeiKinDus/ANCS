# -*- coding: utf-8 -*-

import time
from prometheus_client import Summary, Gauge, Counter


def background_watcher(drop_ins: dict = None):
    """
    Periodic measurements and cleanup thread. Used to make measurements
    and update Prometheus counters.

    :param drop_ins:
    :return:
    """
    iteration = 0
    c_iter = Counter('num_watcher_iter', 'Number of iterations the background watcher performed')
    while True:
        iteration += 1
        c_iter.inc()
        with open('/tmp/debug.log', 'a') as fd:
            fd.write("Iteration #{}\n".format(iteration))

        time.sleep(5)
    pass
