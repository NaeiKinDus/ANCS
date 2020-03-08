# -*- coding: utf-8 -*-

import adafruit_bme280
from ancs.core.dropin.base_i2c_dropin import BaseI2CDropIn
import busio
from flask import current_app, jsonify, g, request
import digitalio
# try:
#     import board
# except NotImplementedError as excp:
#     # Happens if running on a non ARM board
#     # @todo: properly handle error
#     import sys
#     print(excp)
#     sys.exit()


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
        """
        Called by the watcher thread, used to perform periodic measurements and increase
        relevant Prometheus counters.
        """
        self._get_readings()
        self._update_counters()

    def _get_readings(self):
        print('Getting readings from bme280...')

    def _update_counters(self):
        print('Updating counters from bme280...')

    def handler(self):
        """
        Exposed as a REST webservice; call that handles queries that match a specific endpoint.
        :return: a json-encoded string that contains the response
        :rtype: str
        """
        print(request.method)
        if request.method == 'POST':
            with current_app.app_context():
                print(type(g.drop_ins))
        print('Handler called for bme280...')
        return jsonify({"message": "wokay"})

    @property
    def identity(self) -> dict:
        """
        Property returning a dictionary used to register drop-ins and their end point(s).

        :return: identity dict for this drop-in
        :rtype: dict
        """
        return {
            'id': 'adafruit_bme280',
            'rule': 'bme280',
            'endpoint': '/bme280',
            'version': '0.0.1-alpha',
            'handler': self.handler,
            'methods': ('GET', 'POST')
        }
