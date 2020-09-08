# -*- coding: utf-8 -*

class BaseDropInException(Exception):
    """
    Base exception used by drop-ins to raise errors
    """
    pass


class SecurityException(BaseDropInException):
    """
    Security-related exceptions like directory traversal, file access denied, ...
    """
    severity: str = None
    message: str = None

    def __init__(self, message: str, severity: str):
        self.severity = severity
        super().__init__(message)

    def __reduce__(self):
        return SecurityException, (self.message, self.severity)

    def __str__(self):
        return '{}: {}'.format(self.severity, self.message)


class Severity(object):
    """
    Class used to provide consistent severity levels
    """
    ATTACKER: str = 'ATTACKER'
    ERROR: str = 'ERROR'
    WARNING: str = 'WARNING'
    INFO: str = 'INFO'
    DEBUG: str = 'DEBUG'
    UNKNOWN: str = 'UNKNOWN'
