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

        self.id_ = str(self)


    def run(self):
        self.server_conn, addr = self.server.accept()
        Logger.warning('New conn from ' + str(addr), id_=self.id_)

        self.exit_signal = False

        thread_pool_receiver = threading.Thread(target=self.receive_from_pool)
        thread_pool_processor = threading.Thread(target=self.process_from_pool)
        thread_miner_receiver = threading.Thread(target=self.receive_from_miner)
        thread_miner_processor = threading.Thread(target=self.process_from_miner)
        thread_pool_sender = threading.Thread(target=self.send_to_pool)

        thread_periodic_calls = threading.Thread(target=self.periodic_calls)

        thread_pool_receiver.start()
        Logger.debug('thread_pool_receiver started', id_=self.id_)

        thread_pool_processor.start()
        Logger.debug('thread_pool_processor started', id_=self.id_)

        thread_miner_receiver.start()
        Logger.debug('thread_mine_receiver started', id_=self.id_)

        thread_miner_processor.start()
        Logger.debug('thread_miner_processor started', id_=self.id_)

        thread_pool_sender.start()
        Logger.debug('thread_pool_sender started', id_=self.id_)

        thread_periodic_calls.start()
        Logger.debug('thread_periodic_calls started', id_=self.id_)

        return self

        #thread_pool_receiver.join()
        #thread_pool_processor.join()
        #thread_miner_receiver.join()
        #thread_miner_processor.join()
        #thread_pool_sender.join()
        #thread_periodic_calls.join()

    def init_coin(self, data_dic):
        Logger.debug('Entered init_coin', id_=self.id_)

        coin = self.api.get_most_profitable()

        req_params = data_dic['params']
        for i in range(len(req_params)):
            # initial phase, get proxy from miner
            if 'proxy' in req_params[i]:
                Logger.debug('proxy keyword detected', id_=self.id_)
                req_params[i] = self.setting.get_param() + ',mc=' + coin

        json_data = json.dumps(data_dic) + '\n'

        Logger.debug('init_coin() modified request to: ' + json_data, id_=self.id_)

        self.last_coin = coin

        self.pool_sending_queue.put(json_data)
        Logger.warning('\n' + '=' * 256, id_=self.id_)
        Logger.warning('\nMiner start to mine $' + coin, id_=self.id_)

        self.last_switching = time.time()

    def choose_coin(self):
        if time.time() - self.last_switching < 20:
            return

        Logger.debug('Entered choose_coin', id_=self.id_)
        self.last_switching = time.time()

        coin = self.api.get_most_profitable()

        if self.last_coin and coin != self.last_coin:
            Logger.warning('\nMiner Switching to $' + coin, id_=self.id_)
            self.exit_signal = True

            self.restart()
        else:
            Logger.info('Keep mining $' + coin, id_=self.id_)

    def restart(self):
        self.exit_signal = True
        Logger.warning('Server restart', id_=self.id_)
        self.server_conn.close()
        time.sleep(0.15)
        # raise Exception('Server restart')

    def periodic_calls(self):
        while True:
            if self.exit_signal:
                Logger.debug('periodic_calls exit_signal', id_=self.id_)
                return

            self.choose_coin()

            time.sleep(0.1)

    def send_to_pool(self):
        while True:
            if self.exit_signal:
                Logger.debug('send_to_pool exit_signal', id_=self.id_)
                return

            try:
                sending_data = self.pool_sending_queue.get(block=True, timeout=0.1)
            except queue.Empty as e:
                continue

            enc_data = sending_data.encode('utf-8')

            try:
                self.client.send(enc_data)
            except OSError as e:
                Logger.error(str(e) + 'OSError in server.py send_to_pool()', id_=self.id_)
                self.client = Client(self.algo)
                self.client.send(enc_data)
                Logger.error(e, id_=self.id_)

    def receive_from_pool(self):
        while True:
            if self.exit_signal:
                Logger.debug('receive_from_pool exit_signal', id_=self.id_)
                return

            try:
                self.client.receive()
            except socket.error:
                continue

    def process_from_pool(self):
        while True:
            if self.exit_signal:
                Logger.debug('process_from_pool exit_signal', id_=self.id_)
                return

            try:
                pool_data = self.client.pool_receive_queue.get(block=True, timeout=0.1)
            except queue.Empty:
                continue

            json_obj = json.loads(pool_data)
            if 'result' in json_obj.keys() and json_obj['result'] is False:
                Logger.warning('Pool: ' + pool_data, id_=self.id_)
            else:
                Logger.info2('Pool: ' + repr(pool_data), id_=self.id_)

            # redirect the data strait to the miner
            self.send_to_miner(pool_data)

    def receive_from_miner(self):
        while True:
            if self.exit_signal:
                Logger.debug('receive_from_miner exit_signal', id_=self.id_)
                return

            ready = select.select([self.server_conn], [], [], 0.1)  # this bit basically block for a second
            if ready[0]:
                try:
                    data = self.server_conn.recv(8000)
                except ConnectionAbortedError:
                    Logger.warning('ConnectionAbortedError', id_=self.id_)
                    self.restart()
                    return
                except OSError:
                    Logger.warning('Socket might already closed', id_=self.id_)
                    self.restart()
                    return

                try:
                    dec_data = data.decode("utf-8")
                except AttributeError:
                    self.restart()
                    return

                received = dec_data.split('\n')

                for rec in received:
                    if rec:
                        self.miner_receive_queue.put(rec + '\n')

    def process_from_miner(self):
        while True:
            if self.exit_signal:
                Logger.debug('process_from_miner exit_signal', id_=self.id_)
                return

            try:
                miner_data = self.miner_receive_queue.get(block=True, timeout=0.1)
            except queue.Empty:
                continue

            Logger.info('Miner: ' + miner_data, id_=self.id_)

            # Here is for worker reg, choose the coin now.
            data_dic = json.loads(miner_data)

            if data_dic['method'] == 'mining.authorize' or data_dic['method'] == 'eth_submitLogin':
                Logger.debug('Mining authorize detected', id_=self.id_)
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

