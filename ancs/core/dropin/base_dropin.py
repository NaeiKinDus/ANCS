# -*- coding: utf-8 -*-


class BaseDropIn(object):
    """
    Base class used by drop-ins.
    """
    def periodic_call(self, context: dict):
        """
        Called by the watcher thread, used to perform periodic measurements and increase
        relevant Prometheus counters.
        """
        pass

    def handler(self):
        """
        Exposed as a REST webservice; call that handles queries that match a specific endpoint.
        :return: a json-encoded string that contains the response
        :rtype: str
        """
        pass

    @property
    def identity(self) -> dict:
        """
        Property returning a dictionary used to register drop-ins and their end point(s).

        :return:
        """
        raise NotImplementedError("Please implement the property `identity`")
