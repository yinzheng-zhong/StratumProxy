import json
import logging


class ConfigReader:
    def __init__(self, algo, path='config.json'):
        self.path = path
        self.algo = algo

        self.data = self._read_file()

        self.data_settings = self.data['setting']

    def _read_file(self):
        with open(self.path) as json_data_file:
            data = json.load(json_data_file)

        return data

    def get_coins(self):
        return self.data_settings[self.algo]['coins']

    def get_pool_port(self):
        return self.data_settings[self.algo]['pool_port']

    def get_server_port(self):
        return self.data_settings[self.algo]['server_port']

    def get_param(self):
        return self.data['param']

    def refresh(self):
        self.data = self._read_file()

    def get_logging_level(self):
        level = self.data['param']

        if level == 'critical' or level == 'fatal':
            return logging.CRITICAL
        elif level == 'error':
            return logging.ERROR
        elif level == 'warning' or level == 'warn':
            return logging.WARNING
        elif level == 'info':
            return logging.INFO
        else:
            return logging.DEBUG


if __name__ == '__main__':
    conf = ConfigReader('scrypt')

    o = conf.get_coins()
    oo = conf.get_param()
    ooo = conf.get_pool_port()