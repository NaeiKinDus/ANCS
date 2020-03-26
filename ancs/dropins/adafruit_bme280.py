# -*- coding: utf-8 -*-

from ancs.core.dropin.base_i2c_dropin import BaseI2CDropIn
from logging import Logger
from prometheus_client import Gauge, Counter, metrics, Info, Enum
from typing import Optional, Dict


class DropIn(BaseI2CDropIn):
    """
    Drop-in to use Adafruit's BME280 sensor using I2C.
    """
    DEFAULT_ADDRESS: int = 0x77  # dec: 119
    DEFAULT_BUS: int = 1
    DROP_IN_VERSION: str = '0.0.1'
    DROP_IN_ID: str = 'adafruit_bme280'
    FLASK_ROUTING_RULE: str = 'bme280'
    HANDLED_METHODS = ('GET', 'POST')

    _metrics: Dict[str, metrics.MetricWrapperBase] = {}

    def __init__(self, logger: Logger, bus: int = None, address: int = None, connector: object = None):
        """
        Constructor.
        note: `connector` may be a lambda or function that returns an object that MUST exhibit the
            same properties as adafruit_bme280.Adafruit_BME280_I2C() for full compatibility. The
            function will be provided with two positional parameters, `bus` and `address`, corresponding to
            the I2C connection parameters.
        @todo Modify the way connectors are handled to allow easier configuration of I2C parameters.

        :param logger: logger instance
        :type logger: Logger
        :param bus: I2C bus used
        :type bus: int
        :param address: I2C address of the sensor
        :type address: int
        :param connector: connector used to talk to the I2C device, defaults to adafruit_bme280 implementation
        :type connector: object
        """
        current_address: int = address if address else self.DEFAULT_ADDRESS
        current_bus: int = bus if bus else self.DEFAULT_BUS
        current_connector: object

        if callable(connector):
            current_connector = connector(bus=current_bus, address=current_address)
        else:
            try:
                from adafruit_bme280 import Adafruit_BME280_I2C
                import board
                import busio
            except NotImplementedError:
                logger.error('Missing python dependencies, please review your setup')
                raise

            i2c_setup = busio.I2C(board.SCL, board.SDA)
            current_connector = Adafruit_BME280_I2C(i2c_setup)
        super().__init__(current_bus, current_address, logger, connector=current_connector)
        self._setup_metrics()
        self._metrics['state'].labels('bme280').state('ready')

    def _setup_metrics(self):
        # Setup metrics objects. Should never be called by anything except the # __init__() method.
        self._metrics['state'] = Enum(
            self.DROP_IN_ID + '_drop_in_status',
            'Current status of the drop-in',
            ['drop_in_name'],
            states=['starting', 'ready', 'measuring']
        )
        self._metrics['state'].labels('bme280').state('starting')

        self._metrics['periodic_passes'] = Counter(
            self.DROP_IN_ID + '_measurements_count',
            'Number of times periodic measurements were performed',
            ['drop_in_name']
        )

        self._metrics['temperature'] = Gauge(
            self.DROP_IN_ID + '_temperature',
            'Temperature (Celsius degrees)',
            ['drop_in_name']
        )
        self._metrics['altitude'] = Gauge(
            self.DROP_IN_ID + '_altitude',
            'Altitude (meters)',
            ['drop_in_name']
        )
        self._metrics['humidity'] = Gauge(
            self.DROP_IN_ID + '_humidity',
            'Humidity (%)',
            ['drop_in_name']
        )
        self._metrics['pressure'] = Gauge(
            self.DROP_IN_ID + '_pressure',
            'Pressure (hPa)',
            ['drop_in_name']
        )

        self._metrics['bme280'] = Info(
            self.DROP_IN_ID + '_drop_in',
            'Information regarding this drop_in',
            ['drop_in_name']
        )
        self._metrics['bme280'].labels('bme280').info(
            {
                'version': self.DROP_IN_VERSION,
                'id': self.DROP_IN_ID,
                'rule': self.FLASK_ROUTING_RULE,
                'capabilities': 'temperature, altitude, humidity, pressure'
            }
        )

    def periodic_call(self, context: dict = None) -> None:
        """
        Called by the watcher thread, used to perform periodic measurements and increase
        relevant Prometheus counters.
        """
        self.logger.debug('running periodic upkeep for {}'.format(self.DROP_IN_ID))
        self._metrics['state'].labels('bme280').state('measuring')

        self._metrics['periodic_passes'].labels('bme280').inc()
        self._metrics['temperature'].labels('bme280').set(round(self._connector.temperature, 1))
        self._metrics['humidity'].labels('bme280').set(round(self._connector.humidity))
        self._metrics['pressure'].labels('bme280').set(round(self._connector.pressure))
        self._metrics['altitude'].labels('bme280').set(round(self._connector.altitude))

        self._metrics['state'].labels('bme280').state('ready')
        self.logger.debug('periodic upkeep succeeded')

    def handler(self, context: dict = None) -> Optional[str]:
        """
        Exposed as a REST webservice; call that handles queries that match a specific endpoint.
        :param context: an optional context object containing a query's context data
        :type context: dict
        :return: a json-encoded string that contains the response
        :rtype: str
        """
        pass

    @property
    def identity(self) -> dict:
        """
        Property returning a dictionary used to register drop-ins and their end point(s).

        :return: identity dict for this drop-in
        :rtype: dict
        """
        return {
            'id': self.DROP_IN_ID,
            'rule': self.FLASK_ROUTING_RULE,
            'endpoint': '/' + self.FLASK_ROUTING_RULE,
            'version': self.DROP_IN_VERSION,
            'handler': self.handler,
            'methods': self.HANDLED_METHODS
        }
