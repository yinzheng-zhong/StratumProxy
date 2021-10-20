import socket
import sys

from src.Proxy.client import Client
from src.Api.api import Api
import time
import numpy as np
from src.Helper.config_reader import ConfigReader
import json
import queue
from src.Model.logger import Logger
import threading
import select


class StratumServer:
    def __init__(self, algo, server, coin_profit_api):
        self.algo = algo
        self.setting = ConfigReader(algo)
        self.last_switching = np.inf
        self.last_coin = ''

        self.miner_receive_queue = queue.Queue()
        self.pool_sending_queue = queue.Queue()

        self.api = coin_profit_api
        self.client = Client(algo)

        self.server = server
        self.server_conn = None
        self.exit_signal = False

        #self._start_server()

    def run(self):
        self.server_conn, addr = self.server.accept()
        Logger.warning('New conn from ' + addr)

        self.exit_signal = False

        thread_pool_receiver = threading.Thread(target=self.receive_from_pool)
        thread_pool_processor = threading.Thread(target=self.process_from_pool)
        thread_miner_receiver = threading.Thread(target=self.receive_from_miner)
        thread_miner_processor = threading.Thread(target=self.process_from_miner)
        thread_pool_sender = threading.Thread(target=self.send_to_pool)

        thread_periodic_calls = threading.Thread(target=self.periodic_calls)

        thread_pool_receiver.start()
        Logger.debug('thread_pool_receiver started')

        thread_pool_processor.start()
        Logger.debug('thread_pool_processor started')

        thread_miner_receiver.start()
        Logger.debug('thread_mine_receiver started')

        thread_miner_processor.start()
        Logger.debug('thread_miner_processor started')

        thread_pool_sender.start()
        Logger.debug('thread_pool_sender started')

        thread_periodic_calls.start()
        Logger.debug('thread_periodic_calls started')

        return self

        #thread_pool_receiver.join()
        #thread_pool_processor.join()
        #thread_miner_receiver.join()
        #thread_miner_processor.join()
        #thread_pool_sender.join()
        #thread_periodic_calls.join()

    def init_coin(self, data_dic):
        Logger.debug('Entered init_coin')

        coin = self.api.get_most_profitable()

        req_params = data_dic['params']
        for i in range(len(req_params)):
            # initial phase, get proxy from miner
            if 'proxy' in req_params[i]:
                Logger.debug('proxy keyword detected')
                req_params[i] = self.setting.get_param() + ',mc=' + coin

        json_data = json.dumps(data_dic) + '\n'

        Logger.debug('init_coin() modified request to: ' + json_data)

        self.last_coin = coin

        self.pool_sending_queue.put(json_data)
        Logger.warning('\n' + '=' * 256)
        Logger.warning('\nMiner start to mine $' + coin)

        self.last_switching = time.time()

    def choose_coin(self):
        Logger.debug('Entered choose_coin')
        self.last_switching = time.time()

        coin = self.api.get_most_profitable()

        if self.last_coin and coin != self.last_coin:
            Logger.warning('\nMiner Switching to $' + coin)
            self.exit_signal = True

            self.restart()
        else:
            Logger.info('Keep mining $' + coin)

    def restart(self):
        self.exit_signal = True
        Logger.warning('Server restart')
        time.sleep(1.5)
        raise Exception('Server restart')

    def periodic_calls(self):
        while True:
            if self.exit_signal:
                Logger.debug('periodic_calls exit_signal')
                return

            if time.time() - self.last_switching > 60:
                self.choose_coin()
                self.setting.refresh()

            time.sleep(1)

    def send_to_pool(self):
        while True:
            if self.exit_signal:
                Logger.debug('send_to_pool exit_signal')
                return

            try:
                sending_data = self.pool_sending_queue.get(block=True, timeout=1)
            except queue.Empty as e:
                continue

            enc_data = sending_data.encode('utf-8')

            try:
                self.client.send(enc_data)
            except OSError as e:
                Logger.error(str(e) + 'OSError in server.py send_to_pool()')
                self.client = Client(self.algo)
                self.client.send(enc_data)
                Logger.error(e)

    def receive_from_pool(self):
        while True:
            if self.exit_signal:
                Logger.debug('receive_from_pool exit_signal')
                return

            try:
                self.client.receive()
            except socket.error:
                continue

    def process_from_pool(self):
        while True:
            if self.exit_signal:
                Logger.debug('process_from_pool exit_signal')
                return

            try:
                pool_data = self.client.pool_receive_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue

            json_obj = json.loads(pool_data)
            if 'result' in json_obj.keys() and json_obj['result'] is False:
                Logger.warning('Pool: ' + pool_data)
            else:
                Logger.info2('Pool: ' + repr(pool_data))

            # redirect the data strait to the miner
            self.send_to_miner(pool_data)

    def receive_from_miner(self):
        while True:
            if self.exit_signal:
                Logger.debug('receive_from_miner exit_signal')
                return

            ready = select.select([self.server_conn], [], [], 1)  # this bit basically block for a second
            if ready[0]:
                try:
                    data = self.server_conn.recv(8000)
                except ConnectionAbortedError:
                    Logger.warning('ConnectionAbortedError')
                    data = None
                    self.restart()

                dec_data = data.decode("utf-8")
                received = dec_data.split('\n')

                for rec in received:
                    if rec:
                        self.miner_receive_queue.put(rec + '\n')

    def process_from_miner(self):
        while True:
            if self.exit_signal:
                Logger.debug('process_from_miner exit_signal')
                return

            try:
                miner_data = self.miner_receive_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue

            Logger.info('Miner: ' + miner_data)

            # Here is for worker reg, choose the coin now.
            data_dic = json.loads(miner_data)

            if data_dic['method'] == 'mining.authorize' or data_dic['method'] == 'eth_submitLogin':
                Logger.debug('Mining authorize detected')
                self.init_coin(data_dic)
            else:  # decode and put into queue
                self.pool_sending_queue.put(miner_data)

    def send_to_miner(self, pool_data):
        """
        no sending queue, send straight to miner
        :param pool_data:
        :return:
        """

        try:
            self.server_conn.sendall(pool_data.encode('utf-8'))
        except OSError:
            self.restart()

