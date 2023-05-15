# -*- coding: utf-8 -*-

from marshmallow import Schema, fields, validate


class I2CDeviceSchema(Schema):
    bus = fields.Int(required=True)
    address = fields.Int(required=True)


class CalibrationSchema(I2CDeviceSchema):
    points = fields.Int(required=True, validate=validate.Range(min=1, max=3))
