import logging
from src.Helper.config_reader import ConfigReader


class Logger:
    logging.warning('')
    level = ConfigReader(None).get_logging_level()

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
    def warning(msg=''):
        if Logger.level >= logging.WARNING:
            print(Logger.WARNING + 'WARNING: ' + msg + Logger.ENDC)

    @staticmethod
    def error(msg=''):
        if Logger.level >= logging.ERROR:
            print(Logger.ERROR + 'ERROR: ' + msg + Logger.ENDC)

    @staticmethod
    def debug(msg=''):
        if Logger.level >= logging.DEBUG:
            print(Logger.DEBUG + 'DEBUG: ' + msg + Logger.ENDC)

    @staticmethod
    def info(msg=''):
        if Logger.level >= logging.INFO:
            print(Logger.INFO + 'INFO: ' + msg + Logger.ENDC)

    @staticmethod
    def info2(msg=''):
        if Logger.level >= logging.INFO:
            print(Logger.INFO2 + 'INFO: ' + msg + Logger.ENDC)

    @staticmethod
    def critical(msg=''):
        if Logger.level >= logging.CRITICAL:
            print(Logger.CRITICAL + 'CRITICAL: ' + msg + Logger.ENDC)