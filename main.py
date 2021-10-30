import sys
from src.Proxy.proxy import Proxy
from src.Helper.config_reader import ConfigReader
import time
import socket
from src.Model.logger import Logger
from src.Api.api import Api
import threading
import gc


class Server:
    INSTANCES = 20

    def __init__(self, algo):
        self.algo = algo
        self.setting = ConfigReader(algo)
        self.api = Api(algo)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", self.setting.get_server_port()))
        self.server.listen(Server.INSTANCES)

        self.prev_profitable = 0  # 0: init, 1 profitable, 2: not profitable

        self.list_conns_zerg = []
        self.list_conns_backup = []

    def run(self):
        while True:
            _, profitability = self.api.get_most_profitable()

            if profitability > 0:
                if profitability * 0.8 > self.setting.get_bid():
                    if self.prev_profitable != 1:
                        Logger.important('Profitable: ' + str(profitability))
                        self.prev_profitable = 1
                    self.destroy_backup()
                    self.start_zerg_proxies(Server.INSTANCES)
                else:
                    if self.prev_profitable != -1:
                        Logger.warning('Not profitable at the moment: ' + str(profitability))
                        self.prev_profitable = -1
                    self.destroy_zerg()
                    self.start_backup_proxies(Server.INSTANCES)

            #gc.collect()

            #Logger.warning('Number of connections: ' + str(len(self.list_conns_zerg)))

            time.sleep(0.1)

    def start_zerg_proxies(self, num_conns):
        while len(self.list_conns_zerg) < num_conns:
            self.list_conns_zerg.append(Proxy(self.algo, self.server, self.api, backup=False).start())

    def start_backup_proxies(self, num_conns):
        while len(self.list_conns_backup) < num_conns:
            self.list_conns_backup.append(Proxy(self.algo, self.server, self.api, backup=True).start())

    def destroy_zerg(self):
        for proxy in self.list_conns_zerg:
            try:
                proxy.close()#
            except AttributeError:
                continue

        tmp = []

        for proxy in self.list_conns_zerg:
            if not proxy.exit_signal:
                tmp.append(proxy)

        self.list_conns_zerg = tmp

    def destroy_backup(self):
        for proxy in self.list_conns_backup:
            try:
                proxy.close()
            except AttributeError:
                continue

        tmp = []

        for proxy in self.list_conns_backup:
            if not proxy.exit_signal:
                tmp.append(proxy)

        self.list_conns_backup = tmp


if __name__ == '__main__':
    algo_ = sys.argv[1]

    s = Server(algo_)

    s.run()
