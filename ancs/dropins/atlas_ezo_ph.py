# -*- coding: utf-8 -*-

from ancs.core.dropin.base_i2c_dropin import BaseI2CDropIn


class DropIn(BaseI2CDropIn):
    """
    Drop-in to use Adafruit's BME280 sensor using I2C.
    """
    DEFAULT_ADDRESS: int = 0x77  # dec: 119
    DEFAULT_BUS: int = 1

    def __init__(self, bus: int = None, address: int = None):
        """
        Constructor.

        :param bus: I2C bus used
        :type bus: int
        :param address: I2C address of the sensor
        :type address: int
        """
        current_address: int = address if address else self.DEFAULT_ADDRESS
        current_bus: int = bus if bus else self.DEFAULT_BUS

        super().__init__(bus=current_bus, address=current_address)

    def periodic_call(self, context: dict):
        self._get_readings()
        self._update_counters()
        pass

    def _get_readings(self):
        print("Getting readings from atlas...")

    def _update_counters(self):
        print("Updating counters from atlas...")

    @property
    def identity(self) -> dict:
        return {
        "id": "atlas_ezo_ph",
            "rule": "ph",
            "endpoint": "/ph",
            "version": "0.0.1-alpha"
        }
