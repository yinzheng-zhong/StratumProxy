import socket
from src.Proxy.client import Client
from src.Api.api import Api
import time
import numpy as np
from src.Helper.config_reader import ConfigReader
import json
import queue
import logging
import threading


class StratumServer:
    def __init__(self, algo):
        self.algo = algo
        self.setting = ConfigReader(algo)
        self.port = self.setting.get_server_port()
        self.last_switching = np.inf
        self.last_coin = ''

        self.last_id = 0

        self.miner_receive_queue = queue.Queue()
        self.pool_sending_queue = queue.Queue()

        self.api = Api(algo, self.setting.get_coins())
        self.client = Client(algo)

        self.server = None
        self.server_conn = None
        self.exit_signal = False

        logging.basicConfig(level=self.setting.get_logging_level())
        self._start_server()

    def _start_server(self):
        self.exit_signal = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", self.port))
        self.server.listen(1)

        self.server_conn, addr = self.server.accept()

    def run(self):
        thread_pool_receiver = threading.Thread(target=self.receive_from_pool)
        thread_pool_processor = threading.Thread(target=self.process_from_pool)
        thread_miner_receiver = threading.Thread(target=self.receive_from_miner)
        thread_miner_processor = threading.Thread(target=self.process_from_miner)
        thread_pool_sender = threading.Thread(target=self.send_to_pool)

        thread_periodic_calls = threading.Thread(target=self.periodic_calls)

        thread_pool_receiver.start()
        logging.debug('thread_pool_receiver started')

        thread_pool_processor.start()
        logging.debug('thread_pool_processor started')

        thread_miner_receiver.start()
        logging.debug('thread_mine_receiver started')

        thread_miner_processor.start()
        logging.debug('thread_miner_processor started')

        thread_pool_sender.start()
        logging.debug('thread_pool_sender started')

        thread_periodic_calls.start()
        logging.debug('thread_periodic_calls started')

        thread_pool_receiver.join()
        thread_pool_processor.join()
        thread_miner_receiver.join()
        thread_miner_processor.join()
        thread_pool_sender.join()
        thread_periodic_calls.join()

    def init_coin(self, data_dic):
        self.last_switching = time.time()

        coin = self.api.get_most_profitable()

        req_params = data_dic['params']
        for i in range(len(req_params)):
            # initial phase, get proxy from miner
            if 'proxy' in req_params[i]:
                req_params[i] = self.setting.get_param() + ',mc=' + coin

        json_data = json.dumps(data_dic) + '\n'

        self.last_coin = coin

        self.pool_sending_queue.put(json_data)
        logging.warning('\n' + '=' * 256)
        logging.warning('Miner Switching to $' + coin)

    def choose_coin(self):
        self.last_switching = time.time()

        coin = self.api.get_most_profitable()

        if self.last_coin and coin != self.last_coin:
            logging.warning('\n' + '=' * 256)
            logging.warning('Miner Switching to $' + coin)
            self.exit_signal = True

            self.restart()

            #self.pool_sending_queue.put('{"id": ' + str(self.last_id+1) + ', "method": "mining.subscribe", "params": ["cgminer/4.9.0", "08dce1352bf4a4c420efca8c7d46f753"]}\n')
            #self.pool_sending_queue.put(json.dumps(self.auth) + '\n')

        #self.last_coin = coin

        #print('Miner Switching to $' + coin)

    def restart(self):
        self.server_conn.close()

        self.client.restart()
        self._start_server()

    def periodic_calls(self):
        while True:
            if time.time() - self.last_switching > 30:
                self.choose_coin()
                self.setting.refresh()

            time.sleep(30)

            if self.exit_signal:
                return

    def send_to_pool(self):
        while True:
            sending_data = self.pool_sending_queue.get()#block=False)

            obj = json.loads(sending_data)
            self.last_id = obj['id']

            enc_data = sending_data.encode('utf-8')

            logging.info('Miner: ' + repr(enc_data))

            try:
                self.client.send(enc_data)
            except OSError as e:
                self.client = Client(self.algo)
                self.client.send(enc_data)
                logging.error(e)

            if self.exit_signal:
                return

    def receive_from_pool(self):
        while True:
            self.client.receive()

            if self.exit_signal:
                return

    def process_from_pool(self):
        while True:
            pool_data = self.client.pool_receive_queue.get()#block=False)
            logging.info('Pool: ' + repr(pool_data))

            # redirect the data strait to the miner
            self.send_to_miner(pool_data)

            if self.exit_signal:
                return

    def receive_from_miner(self):
        while True:
            data = self.server_conn.recv(8000)

            dec_data = data.decode("utf-8")
            received = dec_data.split('\n')

            for rec in received:
                if rec:
                    self.miner_receive_queue.put(rec + '\n')

            if self.exit_signal:
                return

    def process_from_miner(self):
        while True:
            miner_data = self.miner_receive_queue.get()  # block=False)

            # Here is for worker reg, choose the coin now.
            data_dic = json.loads(miner_data)

            if data_dic['method'] == 'mining.authorize' or data_dic['method'] == 'eth_submitLogin':
                self.init_coin(data_dic)
            else:  # decode and put into queue
                self.pool_sending_queue.put(miner_data)

            if self.exit_signal:
                return

    def send_to_miner(self, pool_data):
        """
        no sending queue, send straight to miner
        :param pool_data:
        :return:
        """
        try:
            self.server_conn.sendall(pool_data.encode('utf-8'))
        except OSError as e:
            logging.error(e)
            self.server_conn, addr = self.server.accept()
