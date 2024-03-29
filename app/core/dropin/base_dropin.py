# -*- coding: utf-8 -*-

from logging import Logger
from typing import Optional


class BaseDropIn(object):
    """
    Base class used by drop-ins.
    """

    def __init__(self, logger: Logger) -> None:
        """
        Ctor

        :param logger: a logger instance
        :type logger: Logger
        """
        self.logger = logger

    def periodic_call(self, context: dict = None) -> None:
        """
        Called by the watcher thread, used to perform periodic measurements and increase
        relevant Prometheus counters.
        This method is optional.

        """
        self.logger.info(
            'method `periodic_call` is not implemented by "{}", no upkeep will be performed'
            .format(self.identity['id'])
        )

    def handler(self, context: dict = None) -> Optional[str]:
        """
        Exposed as a REST webservice; method that handles queries that match a specific route.
        This method is optional.

        :param context: an optional context object containing a query's context data
        :type context: dict
        :return: a json-encoded string that contains the response
        :rtype: str
        """
        self.logger.info(
            'method `handler` is not implemented by {}, no routing available for this drop-in'
            .format(self.identity['id'])
        )
        return

    @property
    def identity(self) -> dict:
        """
        Property returning a dictionary used to register drop-ins and their end point(s).

        :return:
        """
        raise NotImplementedError(
            'Attribute `identity` is required but not implemented by drop-in "{}"'
            .format(self.identity['id'])
        )
