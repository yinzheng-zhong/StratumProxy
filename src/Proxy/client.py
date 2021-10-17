import socket
from src.Helper.config_reader import ConfigReader
import queue


class Client:
    def __init__(self, algo):
        self.algo = algo
        self.pool_receive_queue = queue.Queue()
        self.server = self._connect()

    def _connect(self):
        settings = ConfigReader(self.algo)
        host = self.algo + '.eu.mine.zergpool.com'  # The server's hostname or IP address
        port = settings.get_pool_port()  # The port used by the server

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        #s.setblocking(0)

        return s

    def restart(self):
        self.server.close()
        self._connect()

    def send(self, msg):
        self.server.sendall(msg)

    def receive(self):
        data = self.server.recv(8000)

        dec_data = data.decode("utf-8")
        received = dec_data.split('\n')

        for rec in received:
            if rec:
                self.pool_receive_queue.put(rec + '\n')
