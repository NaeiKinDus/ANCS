# -*- coding: utf-8 -*-

from ancs.core.dropin.base_dropin import BaseDropIn
from copy import copy


class BaseI2CDropIn(BaseDropIn):
    """
    Base class used by I2C drop-ins.
    """

    _address: int = None
    _bus: int = None
    _connector: object = None

    def __init__(self, bus: int, address: int, connector: object = None) -> None:
        """
        Ctor

        :param bus: I2C bus number
        :type bus: int
        :param address: I2C address number
        :type address: int
        :param connector: Callable or object used to communicate with hardware sensors
        :type connector: object
        """
        self._bus = bus
        self._address = address
        self._connector = connector

    @property
    def connector(self) -> object:
        """
        Get the current connector object
        !!! IMPORTANT !!! Never ever use self.connector in a drop in as this method returns
            a shallow copy of it to avoid side effects and outside interference.

        :param value: a valid duck-typing connector used by the target DropIn
        :type value: object
        :return: a copy of the current connector.
        :rtype: object
        """
        return copy(self._connector)

    @connector.setter
    def connector(self, value: object) -> None:
        """
        Set a new connector object
        !!! IMPORTANT !!! Never ever use self.connector in a drop in as this method returns
            a shallow copy of it to avoid side effects and outside interference.

        :param value: a valid duck-typing connector used by the target DropIn
        :type value: object
        """
        self._connector = copy(value)

    @property
    def address(self) -> int:
        return self._address

    @address.setter
    def address(self, value: int) -> None:
        """
        Change I2C address used to talk to the sensor
        @todo: check if it is required to handle deco / reco and cleanup

        :param address: I2C address of the sensor
        :type value: int
        """
        self._address = value

    @property
    def bus(self) -> int:
        """
        Getter for the bus property.

        :return: Bus ID
        :rtype: int
        """
        return self._bus

    @bus.setter
    def bus(self, value: int) -> None:
        """
        Setter for the bus property.
        @todo: check if it is required to handle deco / reco and cleanup

        :param value: New bus value
        :type value: int
        """
        self._bus = value
