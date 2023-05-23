# -*- coding: utf-8 -*-
from adafruit_bme280.basic import Adafruit_BME280_I2C
from app.core.dropin.base_i2c_dropin import BaseI2CDropIn
from board import I2C
from logging import Logger
from os import environ
from prometheus_client import Gauge, Counter, metrics, Info, Enum
from random import choices
from string import ascii_letters
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
    STANDARD_PRESSURE: str = "1013.25"

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
        self._metrics: Dict[str, metrics.MetricWrapperBase] = {}
        if not "SEA_LEVEL_PRESSURE" in environ:
            logger.warning(
                f"No custom sea level pressure is defined, falling back to the standard one ({self.STANDARD_PRESSURE} hPa)"
                "but some readings will be off; adjust it by setting the environment variable SEA_LEVEL_PRESSURE"
            )
        self.SEA_LEVEL_PRESSURE: float = float(environ.get("SEA_LEVEL_PRESSURE", self.STANDARD_PRESSURE))
        current_address: int = address if address else self.DEFAULT_ADDRESS
        current_bus: int = bus if bus else self.DEFAULT_BUS
        current_connector: object

        if callable(connector):
            current_connector = connector(bus=current_bus, address=current_address)
        else:
            i2c_setup = I2C()
            current_connector = Adafruit_BME280_I2C(i2c_setup)
            current_connector.sea_level_pressure = self.SEA_LEVEL_PRESSURE
        super().__init__(current_bus, current_address, logger, connector=current_connector)


    def setup_metrics(self):
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
        self._metrics['state'].labels('bme280').state('ready')

    def periodic_call(self, context: dict = None) -> None:
        """
        Called by the watcher thread, used to perform periodic measurements and increase
        relevant Prometheus counters.
        """
        self.logger.debug('running periodic upkeep for {}'.format(self.DROP_IN_ID))
        self._metrics['state'].labels('bme280').state('measuring')

        self._metrics['periodic_passes'].labels('bme280').inc()
        self._metrics['temperature'].labels('bme280').set(round(self._connector.temperature, 1))
        self._metrics['humidity'].labels('bme280').set(round(self._connector.humidity, 2))
        self._metrics['pressure'].labels('bme280').set(round(self._connector.pressure, 2))
        self._metrics['altitude'].labels('bme280').set(round(self._connector.altitude, 2))

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


class TestBme280(object):
    import pytest

    LOWEST_ALT: float = -430.0 # Dead Sea shores
    HIGHEST_ALT: float = 8848.0 # Mount Everest
    LOWEST_PRESS: float = 870.0 # Sea level pressure; Typhoon Tip
    HIGHEST_PRESS: float = 1083.8 # Sea level pressure; Agata, Russia

    _metrics_caps = [
        "periodic_passes", "temperature", "humidity", "pressure", "altitude"
    ]
    _metrics_ignore = [
        "bme280", "state"
    ]

    @pytest.fixture(scope="function")
    def dropin(self, dummy_logger) -> DropIn:
        try:
            return DropIn(dummy_logger)
        except Exception as excp:
            assert False, f"Could not initialize BME280 DropIn for the following reason: {excp}"

    @pytest.mark.order(0)
    def test_metrics(self, dropin: DropIn) -> None:
        try:
            dropin.DROP_IN_ID = "".join(choices(ascii_letters, k=6))
            dropin.setup_metrics()
        except Exception as excp:
            assert False, f"Could not setup BME280 DropIn metrics for the following reason: {excp}"
        missing_keys = [cap for cap in self._metrics_caps if cap not in dropin._metrics]
        extraneous_keys = [cap for cap in dropin._metrics.keys() if cap not in self._metrics_caps + self._metrics_ignore]
        assert len(missing_keys) == 0, f"Some keys are missing in the metrics setup: {missing_keys}"
        assert len(extraneous_keys) == 0, f"Some keys are not supposed to be exposed in the metrics: {extraneous_keys}"
        assert "state" in dropin._metrics, f"Missing state info in dropin metrics data."
        assert "bme280" in dropin._metrics, f"Missing device info (\"bme280\") in dropin metrics data."

    def test_periodic(self, dropin: DropIn) -> None:
        dropin.DROP_IN_ID = "".join(choices(ascii_letters, k=6))
        dropin.setup_metrics()
        state_metric = dropin._metrics["state"].labels("bme280")
        passes_metric = dropin._metrics["periodic_passes"].labels("bme280")

        assert state_metric._states[state_metric._value] == "ready", "Expected \"ready\" state before measurements, got {state_metric._states[state_metric._value]}"
        current_passes = passes_metric._value.get()
        assert current_passes == 0.0, f"Expected that no periodic passes were triggered but passes count is set to \"{current_passes}\""
        dropin.periodic_call()
        assert state_metric._states[state_metric._value] == "ready", "Expected \"ready\" state after measurements, got {state_metric._states[state_metric._value]}"
        current_passes = passes_metric._value.get()
        assert current_passes == 1.0, f"Expected that only one periodic passe was triggered but passes count is set to \"{current_passes}\" "

        float_tests = {
            "temperature": (-99.0, 99.0),
            "humidity": (0.0, 100.0),
            "pressure": (self.LOWEST_PRESS, self.HIGHEST_PRESS),
            "altitude": (self.LOWEST_ALT, self.HIGHEST_ALT)
        }
        for metric_name, bounds in float_tests.items():
            assert metric_name in dropin._metrics, f"Metric named {metric_name} was not found in declared metrics"
            metric = dropin._metrics[metric_name].labels("bme280")
            current_value = metric._value.get()
            print(f"{metric_name}: {current_value}\n")
            assert isinstance(current_value, float), f"Expected type for \"{metric_name}\" is float, got: " + str(type(current_value))
            assert bounds[0] < current_value < bounds[1], f"Metric {metric_name} is not within expected boundaries {bounds[0]} and {bounds[1]}"

        assert False