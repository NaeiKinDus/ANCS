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
    FLASK_ROUTING_RULE: str = 'ph'
    HANDLED_METHODS: tuple = ('GET', 'POST')
    SENSOR_TYPE: str = 'pH'
    DEFAULT_ERROR_VALUE = -99.0

    _metrics: Dict[str, metrics.MetricWrapperBase] = {}

    class PHWrapper(object):
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
            response = self._connector.query('R')
            status_ok, value = self.parse_response(response)
            if value[0]:
                value = float(value[0])

            return value if status_ok else None

        def query(self, command: str) -> Tuple[bool, List[str]]:
            """
            Perform a query and parse the return.

            :param command: a string containing a valid command query.
            :type command: str
            :return: the parsed result
            :rtype: Tuple[bool, List[str]]
            """
            return self.parse_response(self._connector.query(command))

        @staticmethod
        def parse_response(str_resp: str) -> Tuple[bool, List[str]]:
            """
            Parse the given string, detects if the call succeeded and returns the sanitized interesting part
            as an array of strings.

            :param str_resp: a string containing the response of a call to the connector
            :return: a tuple containing the call result (true | false) and the answer part
            :rtype: Tuple[bool, List[str]]
            :raises: ValueError
            """
            parts = str_resp.split(':')
            try:
                status = parts[0].split(' ')[0]
            except BaseException as excp:
                raise ValueError('"{}" is not a valid string') from excp
            succeeded = False
            if status.lower() == 'success':
                succeeded = True

            try:
                # From the actual response, remove leading spaces and trailing (\x00) chars and return split elements
                value = parts[1].strip('\x00 ').split(',')
            except BaseException as excp:
                raise ValueError('"{}" is not a valid string') from excp

            return succeeded, value

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
        current_address: int = address if address else self.DEFAULT_ADDRESS
        current_bus: int = bus if bus else self.DEFAULT_BUS
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
                dev_name = response.split(',')[1]
                current_connector._name = dev_name
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
        dev_info = self._connector.query('I')
        if dev_info[0]:
            firmware_version = dev_info[1][2]
        else:
            firmware_version = 'Unknown'
        self._metrics['atlas_ph'].labels('ph').info(
            {
                'version': self.DROP_IN_VERSION,
                'id': self.DROP_IN_ID,
                'sensor_firmware': firmware_version,
                'rule': self.FLASK_ROUTING_RULE,
                'capabilities': 'ph, settings'
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

    def handler(self, context: dict = None) -> Optional[str]:
        pass

    @property
    def identity(self) -> Dict[str, object]:
        return {
            'id': self.DROP_IN_ID,
            'rule': self.FLASK_ROUTING_RULE,
            'endpoint': '/' + self.FLASK_ROUTING_RULE,
            'version': self.DROP_IN_VERSION,
            'handler': self.handler,
            'methods': self.HANDLED_METHODS
        }
