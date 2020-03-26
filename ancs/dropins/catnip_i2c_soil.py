# -*- coding: utf-8 -*-

from ancs.core.dropin.base_i2c_dropin import BaseI2CDropIn
from flask import current_app, jsonify, g, request
from logging import Logger
from prometheus_client import Gauge, Counter, metrics, Info, Enum
from typing import Optional, Dict


class DropIn(BaseI2CDropIn):
    """
    Drop-in to use Catnip's soil moisture sensor using I2C.
    """
    DEFAULT_ADDRESS: int = 0x20  # dec: 32
    DEFAULT_BUS: int = 1
    DROP_IN_VERSION: str = '0.0.1'
    DROP_IN_ID: str = 'catnip_soil'
    FLASK_ROUTING_RULE: str = 'soil'
    HANDLED_METHODS: tuple = ('GET', 'POST')
    # The values below should reflect your specific device state, perform a calibration
    # if needed beforehand.
    CALIBRATED_MIN_MOISTURE: int = 221
    CALIBRATED_MAX_MOISTURE: int = 614

    _metrics: Dict[str, metrics.MetricWrapperBase] = {}

    def __init__(self, logger: Logger, bus: int = None, address: int = None, connector: object = None):
        """
        Constructor.
        note: `connector` may be a lambda or function that returns an object that MUST exhibit the
            same properties as `.catnip.chirp.chirp()` for full compatibility. The
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
                from .catnip.chirp import Chirp
            except NotImplementedError:
                logger.warning('Missing python dependencies, please review your setup')
                raise
            current_connector = Chirp(
                bus=current_bus,
                address=current_address,
                min_moist=self.CALIBRATED_MIN_MOISTURE,
                max_moist=self.CALIBRATED_MAX_MOISTURE,
            )
        super().__init__(current_bus, current_address, logger, connector=current_connector)
        self._setup_metrics()
        self._metrics['state'].labels('soil').state('ready')

    def _setup_metrics(self):
        self._metrics['state'] = Enum(
            self.DROP_IN_ID + '_drop_in_status',
            'Current status of the drop-in',
            ['drop_in_name'],
            states=['starting', 'ready', 'measuring']
        )
        self._metrics['state'].labels('soil').state('starting')

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
        self._metrics['capacitance'] = Gauge(
            self.DROP_IN_ID + '_capacitance',
            # see https://github.com/Miceuz/i2c-moisture-sensor/issues/27#issuecomment-434716035
            'Capacitance value (arbitrary unit)',
            ['drop_in_name']
        )
        self._metrics['moisture'] = Gauge(
            self.DROP_IN_ID + '_moisture',
            'Moisture (%)',
            ['drop_in_name']
        )
        self._metrics['brightness'] = Gauge(
            self.DROP_IN_ID + '_brightness',
            # see https://www.tindie.com/products/miceuz/i2c-soil-moisture-sensor/ - #Rugged Version
            'Brightness (arbitrary unit)',
            ['drop_in_name']
        )

        self._metrics['soil'] = Info(
            self.DROP_IN_ID + '_drop_in',
            'Information regarding this drop_in',
            ['drop_in_name']
        )
        self._metrics['soil'].labels('soil').info(
            {
                'version': self.DROP_IN_VERSION,
                'id': self.DROP_IN_ID,
                'rule': self.FLASK_ROUTING_RULE,
                'capabilities': 'temperature, capacitance, brightness, moisture'
            }
        )

    def periodic_call(self, context: dict = None):
        """
                Called by the watcher thread, used to perform periodic measurements and increase
                relevant Prometheus counters.
                """
        self.logger.debug('running periodic upkeep for {}'.format(self.DROP_IN_ID))
        self._metrics['state'].labels('soil').state('measuring')

        self._metrics['periodic_passes'].labels('soil').inc()
        # Perform readings
        self._connector.trigger()

        self._metrics['temperature'].labels('soil').set(self._connector.temp)
        self._metrics['capacitance'].labels('soil').set(self._connector.moist)
        self._metrics['moisture'].labels('soil').set(self._connector.moist_percent)
        self._metrics['brightness'].labels('soil').set(self._connector.light)

        self._metrics['state'].labels('soil').state('ready')
        self.logger.debug('periodic upkeep succeeded')

    def handler(self, context: dict = None) -> Optional[str]:
        pass

    @property
    def identity(self) -> dict:
        return {
            'id': self.DROP_IN_ID,
            'rule': self.FLASK_ROUTING_RULE,
            'endpoint': '/' + self.FLASK_ROUTING_RULE,
            'version': self.DROP_IN_VERSION,
            'handler': self.handler,
            'methods': self.HANDLED_METHODS
        }
