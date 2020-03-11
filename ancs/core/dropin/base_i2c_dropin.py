# -*- coding: utf-8 -*-

from ancs.core.dropin.base_dropin import BaseDropIn


class BaseI2CDropIn(BaseDropIn):
    """
    Base class used by I2C drop-ins.
    """

    _address: int = None
    _bus: int = None

    def __init__(self, bus: int, address: int) -> None:
        """
        Ctor

        :param bus: I2C bus number
        :param address: I2C address number
        """
        self._bus = bus
        self._address = address

    @property
    def address(self) -> int:
        return self._address

    @address.setter
    def address(self, value: int):
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
    def bus(self, value: int):
        """
        Setter for the bus property.

        :param value: New bus value
        :type value: int
        """
        self._bus = value
