import socket
import select
import logging
from src.Model.logger import Logger
from src.Helper.utils import Utils

from src.Helper.config_reader import ConfigReader
import queue


class Client:
    def __init__(self, algo, backup):
        self.algo = algo
        self.backup = backup
        self.pool_receive_queue = queue.Queue()
        self.server = self._connect()

    def _connect(self):
        settings = ConfigReader(self.algo)
        if self.backup:
            host = settings.get_pool_backup_url()
            port = settings.get_pool_port_backup()
        else:
            host = self.algo + '.eu.mine.zergpool.com'  # The server's hostname or IP address
            port = settings.get_pool_port()  # The port used by the server

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.setblocking(False)

        return s

    def restart(self):
        self.server.close()
        self._connect()

    def send(self, msg):
        self.server.sendall(msg)

    def receive(self):
        ready = select.select([self.server], [], [], 1000)

        if ready[0]:
            data = self.server.recv(8000)

            dec_data = data.decode("utf-8")
            received = dec_data.split('\n')

            for rec in received:
                if rec:
                    Logger.debug('Received from pool: ' + str(data) + '\n')
                    self.pool_receive_queue.put(rec + '\n')
