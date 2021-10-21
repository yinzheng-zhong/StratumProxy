import logging
from src.Helper.config_reader import ConfigReader


class Logger:
    level = ConfigReader(None).get_logging_level()
    last_message = ''

    HEADER = '\033[95m'
    DEBUG = '\033[94m'
    INFO = '\033[92m'
    INFO2 = '\033[37m'
    PLACEHOLDER = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    CRITICAL = '\033[95m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def warning(msg='', id_=''):
        m = Logger.WARNING + id_ + ' WARNING: ' + msg + Logger.ENDC
        if Logger.level <= logging.WARNING and m != Logger.last_message:
            print(m)
            Logger.last_message = m

    @staticmethod
    def error(msg='', id_=''):
        m = Logger.ERROR + id_ + ' ERROR: ' + msg + Logger.ENDC
        if Logger.level <= logging.ERROR and m != Logger.last_message:
            print(m)
            Logger.last_message = m

    @staticmethod
    def debug(msg='', id_=''):
        m = Logger.DEBUG + id_ + ' DEBUG: ' + msg + Logger.ENDC
        if Logger.level <= logging.DEBUG and m != Logger.last_message:
            print(m)
            Logger.last_message = m

    @staticmethod
    def important(msg='', id_=''):
        m = Logger.INFO + id_ + ' INFO: ' + msg + Logger.ENDC
        if Logger.level <= 25 and m != Logger.last_message:
            print(m)
            Logger.last_message = m

    @staticmethod
    def info(msg='', id_=''):
        m = Logger.INFO2 + id_ + ' INFO: ' + msg + Logger.ENDC
        if Logger.level <= logging.INFO and m != Logger.last_message:
            print(m)
            Logger.last_message = m

    @staticmethod
    def critical(msg='', id_=''):
        m = Logger.CRITICAL + id_ + ' CRITICAL: ' + msg + Logger.ENDC
        if Logger.level <= logging.CRITICAL and m != Logger.last_message:
            print(m)
            Logger.last_message = m