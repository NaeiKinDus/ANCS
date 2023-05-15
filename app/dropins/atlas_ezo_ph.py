# -*- coding: utf-8 -*-

from app.core.dropin.base_i2c_dropin import BaseI2CDropIn
from .atlas.api_schemas import I2CDeviceSchema, CalibrationSchema
from flask import request
from flask_restx import Resource, Namespace
from http import HTTPStatus
from logging import Logger, getLogger
from prometheus_client import Gauge, Counter, metrics, Info, Enum
from typing import Optional, Dict, Tuple, List


api_namespace = Namespace("pH", description="Available operations for Atlas EZO pH sensor")

# for name, model in api_models.items():
#     api_namespace.model()


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

        def query(self, command: str) -> Optional[Tuple[int, Optional[str]]]:
            """
            Perform a query and parse the return.

            :param command: a string containing a valid command query.
            :type command: str
            :return: the parsed result
            :rtype: Optional[Tuple[int, Optional[str]]]
            """
            return self._connector.query(command)

    def query(self, command: str) -> Optional[Tuple[int, Optional[str]]]:
        """
        Perform a query and parse the return.

        :param command: a string containing a valid command query.
        :type command: str
        :return: the parsed result
        :rtype: Optional[Tuple[int, Optional[str]]]
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

    def setup_metrics(self):
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
        self._metrics['state'].labels('ph').state('ready')

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


@api_namespace.route('/device')
class Device(Resource):
    @classmethod
    def get(cls):
        logger = getLogger()
        device = DropIn(logger=logger)
        dev_response = device.query('I')

        try:
            _, dev_type, firmware = dev_response[1].split(',')
        except (ValueError, AttributeError):
            _, dev_type, firmware = (None, 'N/A', 'N/A')

        return {
            'status': 200,
            'result': {
                'ret_code': int(dev_response[0]),
                'raw': dev_response[1],
                'device_type': dev_type,
                'firmware_version': firmware
            }
        }, 200


@api_namespace.route('/calibration')
class Calibration(Resource):
    @classmethod
    def get(cls):
        logger = getLogger()
        device = DropIn(logger=logger)
        dev_response = device.query('Cal,?')

        cal_points = None
        try:
            cal_points = int(dev_response[1][-1:])
        except TypeError:
            pass

        response = {
            'status': 200,
            'result': {
                'ret_code': int(dev_response[0]),
                'raw': dev_response[1],
                'is_calibrated': False if dev_response[1] == '?CAL,0' else True,
                'cal_points': cal_points
            }
        }

        return response, 200

    @classmethod
    def post(cls):
        """
        Create a calibration point.
        :return:
        """
        logger = getLogger()
        device = DropIn(logger=logger)

        pass


@api_namespace.route('/calibration/data')
class CalibrationData(Resource):
    @classmethod
    def get(cls):
        logger = getLogger()
        device = DropIn(logger=logger)
        export_query = device.query('Export,?')
        _, lines_count, bytes_count = export_query[1].split(',')
        lines_count = int(lines_count)
        bytes_count = int(bytes_count)

        export_data = ''
        for i in range(1, lines_count + 1):
            export_query = device.query('export')
            export_data += export_query[1]

        return {
            'status': 200,
            'result': {
                'ret_code': 0,
                'raw': export_data,
                'lines_count': lines_count,
                'bytes_count': bytes_count
            }
        }

    @classmethod
    def put(cls):
        """
        Import calibration data
        :return:
        """
        logger = getLogger()
        device = DropIn(logger=logger)

        pass
