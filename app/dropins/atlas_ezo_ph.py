# -*- coding: utf-8 -*-

from app.core.dropin.base_i2c_dropin import BaseI2CDropIn
from logging import Logger
from prometheus_client import Gauge, Counter, metrics, Info, Enum
from typing import Optional, Dict, Tuple, List


class DropIn(BaseI2CDropIn):
    """
    Drop-in to use Atlas' pH sensor using I2C.
    """

    DEFAULT_ADDRESS: int = 0x63  # dec: 99
    DEFAULT_BUS: int = 1
    DROP_IN_VERSION: str = '0.0.1'
    DROP_IN_ID: str = 'atlas_ph'
    SENSOR_TYPE: str = 'pH'
    DEFAULT_ERROR_VALUE = -99.0

    _metrics: Dict[str, metrics.MetricWrapperBase] = {}
    sensor_firmware: Optional[str] = None
    sensor_type: str = 'ph'
    """:type ._connector: PHWrapper"""
    _connector = None

    class PHWrapper:
        """
        Wrapper class to simplify read/write operations
        """
        _connector: object = None

        def __init__(self, connector: object) -> None:
            self._connector = connector

        @property
        def ph(self) -> Optional[float]:
            """
            Read the pH from the sensor and return the current value.
            Returns None if the measurement failed.

            :return: the current pH value
            :rtype: float
            """
            error_code, response = self._connector.query('R')
            return float(response) if not error_code else None

        def query(self, command: str) -> Tuple[bool, List[str]]:
            """
            Perform a query and parse the return.

            :param command: a string containing a valid command query.
            :type command: str
            :return: the parsed result
            :rtype: Tuple[bool, List[str]]
            """
            return self._connector.query(command)

    def __init__(self, logger: Logger, bus: int = None, address: int = None, connector: object = None) -> None:
        """
        Constructor.
        note: `connector` may be a lambda or function that returns an object that MUST exhibit the
            same properties as `.atlas.AtlasI2C()` for full compatibility. The
            function will be provided with two positional parameters, `bus` and `address`, corresponding to
            the I2C connection parameters.
        @todo Modify the way connectors are handled to allow easier configuration of I2C parameters.

        :param logger: logger instance
        :type logger: Logger
        :param bus: I2C bus used
        :type bus: int
        :param address: I2C address of the sensor
        :type address: int
        :param connector: connector used to talk to the I2C device, defaults to '.atlas.atlasI2C.AtlasI2C implementation
        """
        current_address: int = address or self.DEFAULT_ADDRESS
        current_bus: int = bus or self.DEFAULT_BUS
        current_connector: object

        if callable(connector):
            current_connector = connector(bus=current_bus, address=current_address)
        else:
            try:
                from .atlas.atlasi2c import AtlasI2C
                current_connector = AtlasI2C(
                    address=current_address,
                    bus=current_bus,
                    moduletype=self.SENSOR_TYPE
                )
            except BaseException as excp:
                logger.warning('Could not instantiate default connector (AtlasI2C): {}'.format(excp))
                raise
            try:
                response = current_connector.query('I')
            except Exception as excp:
                logger.warning('Could not query sensor: {}'.format(excp))
                raise
            try:
                if response[0] or len(response) != 2:
                    logger.warning(
                        'Could not retrieve sensor type, unstable system. Error code: {} // Response: {}'
                        .format(response[0], response[1])
                    )
                else:
                    identity_data = response[1].split(',')
                    self.sensor_type = identity_data[1]
                    self.sensor_firmware = identity_data[2]
                    current_connector._name = self.sensor_type or DropIn.SENSOR_TYPE
            except IndexError:
                logger.warning('Invalid board name returned, unspecified behaviour')

        super().__init__(current_bus, current_address, logger, connector=DropIn.PHWrapper(current_connector))
        self._setup_metrics()
        self._metrics['state'].labels('ph').state('ready')

    def _setup_metrics(self):
        # List of supported commands: https://www.atlas-scientific.com/_files/_datasheets/_circuit/pH_EZO_datasheet.pdf
        self._metrics['state'] = Enum(
            self.DROP_IN_ID + '_drop_in_status',
            'Current status of the drop-in',
            ['drop_in_name'],
            states=['starting', 'ready', 'measuring']
        )
        self._metrics['state'].labels('ph').state('starting')

        self._metrics['periodic_passes'] = Counter(
            self.DROP_IN_ID + '_measurements_count',
            'Number of times periodic measurements were performed',
            ['drop_in_name']
        )

        self._metrics['ph'] = Gauge(
            self.DROP_IN_ID + '_ph',
            'pH',
            ['drop_in_name']
        )

        self._metrics['atlas_ph'] = Info(
            self.DROP_IN_ID + '_drop_in',
            'Information regarding this drop_in',
            ['drop_in_name']
        )

        self._metrics['atlas_ph'].labels('ph').info(
            {
                'version': self.DROP_IN_VERSION,
                'id': self.DROP_IN_ID,
                'sensor_firmware': self.sensor_firmware,
                'capabilities': 'ph, settings, api'
            }
        )

    def periodic_call(self, context: dict = None) -> None:
        """
        Called by the watcher thread, used to perform periodic measurements and increase
        relevant Prometheus counters.
        """
        self.logger.debug('running periodic upkeep for {}'.format(self.DROP_IN_ID))
        self._metrics['state'].labels('ph').state('measuring')

        self._metrics['periodic_passes'].labels('ph').inc()
        current_ph = self._connector.ph
        if current_ph:
            current_ph = round(current_ph, 2)
        else:
            current_ph = -99.9
        self._metrics['ph'].labels('ph').set(current_ph)

        self._metrics['state'].labels('ph').state('ready')
        self.logger.debug('periodic upkeep succeeded')

    @property
    def identity(self) -> Dict[str, object]:
        return {
            'id': self.DROP_IN_ID,
            'version': self.DROP_IN_VERSION,
            'firmware': self.sensor_firmware
        }
