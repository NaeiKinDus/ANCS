![GitHub](https://img.shields.io/github/license/NaeiKinDus/ANCS?style=plastic)
#### ANCS
Software used to monitor climate variables when growing vegetables and plants.

As of yet it is in an early but working beta if you have the same sensors as my own setup, which consists of:
- RaspberryPi 3,
- [Tentacle T3](https://www.whiteboxes.ch/shop/tentacle-t3-for-raspberry-pi/) for RPi,
- [Catnip's soil sensor](https://www.whiteboxes.ch/shop/i2c-soil-moisture-sensor/),
- [a BME280 sensor](https://www.adafruit.com/product/2652),
- [Atlas Scientific EZO pH circuit](https://www.whiteboxes.ch/shop/ezo-ph-circuit/)
- [Atlas Scientific consumer-grade sensor](https://www.whiteboxes.ch/shop/consumer-grade-ph-probe/).

> Disclaimer
>
> This list is given so you can compare what you have to what's implemented, I am in no way affiliated to
this particular shop (I just like being able to order everything I need on a single webshop, and they offer the T3).

The documentation is currently not my point of focus but it will get better in time.


#### How it works
The app is to be run by uWSGI and registers available sensors via a system of drop-ins.
Each drop-in allows for the app to perform periodic calls to take measures (or perform any type of task really)
and expose them using [Prometheus](https://prometheus.io/).

Prometheus is then queried by [Grafana](https://grafana.com/) which in turns displays nice graphs for monitoring like so:
![](docs/grafana_dashboard.png)


## Installation
### Requirements
Tested on Python 3.9.2.
Latest pip version.
Rustc >= 1.48

```shell
sudo apt install -y libgpiod-dev i2c-tools
sudo raspi-config nonint do_i2c 0

python3 -m virtualenv venv
source venv/bin/activate
python3 -m pip install -r requirements-dev.txt # or requirements.txt
```

> WARNING
>
> Under construction, more will come later.

## Usage
### Environment variables
Project variables
- SEA_LEVEL_PRESSURE: specify the pressure at your location to obtain more accurate readings from the BME280 chip,

Flask variables:
- FLASK_ENV: `development` or `production`, used to alter Flask's env,
- FLASK_APP: should be `ancs.py:app` by default in dev mode,
- FLASK_DEBUG: enable debug mode,
- LOG_LEVEL: log level for the debugger

**Running tests**
`python3 -m pytest .`

**Running in dev mode**
`SEA_LEVEL_PRESSURE=1017 FLASK_APP="ancs.py:app" FLASK_ENV=development FLASK_DEBUG=0 LOG_LEVEL=DEBUG python3 -u -m flask run --host=0.0.0.0 --port=8000`

If you can find your way around this yourself, install python3, all required dependencies, and fire uWSGI like so:
`LOG_LEVEL=DEBUG uwsgi uwsgi.ini`

The `--enable-threads` is mandatory, else the background watcher will not start.
