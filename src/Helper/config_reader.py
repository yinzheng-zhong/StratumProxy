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
        return list(self.data_settings[self.algo]['coins'].keys())

    def get_pool_port(self):
        return self.data_settings[self.algo]['pool_port']

    def get_pool_backup_url(self):
        return self.data_settings[self.algo]['pool_backup_url']

    def get_pool_port_backup(self):
        return self.data_settings[self.algo]['pool_port_backup']

    def get_server_port(self):
        return self.data_settings[self.algo]['server_port']

    def get_params(self, coin):
        return self.data_settings[self.algo]['coins'][coin]

    def get_payout(self):
        return self.data['payout_coin']

    def get_wallet_address(self):
        return self.data['wallet']

    def get_wallet_address_backup(self):
        return self.data['wallet_backup']

    def refresh(self):
        self.data = self._read_file()

    def get_bid(self):
        return self.data_settings[self.algo]["bid"]

    def get_conversation(self):
        return self.data_settings[self.algo]["hash_conversion"]

    def get_logging_level(self):
        level = self.data['debug_level']

        if level == 'critical' or level == 'fatal':
            return logging.CRITICAL
        elif level == 'error':
            return logging.ERROR
        elif level == 'warning' or level == 'warn':
            return logging.WARNING
        elif level == 'important':
            return 25
        elif level == 'info':
            return logging.INFO
        else:
            return logging.DEBUG


if __name__ == '__main__':
    conf = ConfigReader('scrypt')

    o = conf.get_coins()
    oo = conf.get_params()
    ooo = conf.get_pool_port()
