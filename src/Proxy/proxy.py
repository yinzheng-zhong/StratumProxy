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


class Proxy:
    BLOCK_TIME = 0.1
    USER = 'zxhaxdr'

    def __init__(self, algo, server, coin_profit_api, backup=False):
        self.algo = algo
        self.setting = ConfigReader(algo)
        self.client = None
        self.api = coin_profit_api
        self.backup = backup
        #self.last_switching = np.inf
        #self.last_coin = ''

        self.wallet = self.setting.get_wallet_address()
        self.wallet_backup = self.setting.get_wallet_address_backup()

        self.mining_params = None
        self.create_mining_params()

        self.user_name = None
        self.create_user_name()

        self.miner_receive_queue = queue.Queue()
        self.miner_sending_queue = queue.Queue()
        self.pool_sending_queue = queue.Queue()

        self.server = server
        self.server_conn = None
        self.exit_signal = False

        self.id_ = str(self).split('0x')[-1]

    def create_mining_params(self):
        payout_coin = self.setting.get_payout()
        mining_coin, _ = self.api.get_most_profitable()
        mining_params = self.setting.get_params(mining_coin)

        if self.backup:
            self.mining_params = 'x'
        else:
            if mining_params:
                self.mining_params = 'c=' + payout_coin + ',' + mining_params + ',' + 'mc=' + mining_coin
            else:
                self.mining_params = 'c=' + payout_coin + ',' + 'mc=' + mining_coin

    def create_user_name(self):
        if self.backup:
            self.user_name = self.wallet_backup + '.prox'
        else:
            self.user_name = self.wallet

    def start(self):
        proxy_thread = threading.Thread(target=self.run)
        proxy_thread.start()

        return self

    def run(self):
        addr = ''
        while not self.server_conn:
            if self.exit_signal:  # and self.miner_sending_queue.empty(): # make sure to send the reconnect signal to the miner.
                return

            try:
                self.server_conn, addr = self.server.accept()
            except Exception:
                continue

        self.client = Client(self.algo, self.backup)
        Logger.warning('New conn from ' + str(addr) + ' ' + str(self.backup), id_=self.id_)

        thread_pool_receiver = threading.Thread(target=self.receive_from_pool)
        thread_pool_processor = threading.Thread(target=self.process_from_pool)
        thread_miner_receiver = threading.Thread(target=self.receive_from_miner)
        thread_miner_processor = threading.Thread(target=self.process_from_miner)
        thread_miner_sender = threading.Thread(target=self.send_to_miner)
        thread_pool_sender = threading.Thread(target=self.send_to_pool)

        #thread_periodic_calls = threading.Thread(target=self.periodic_calls)

        thread_pool_processor.start()
        Logger.debug('thread_pool_processor started', id_=self.id_)

        thread_miner_processor.start()
        Logger.debug('thread_miner_processor started', id_=self.id_)

        thread_pool_sender.start()
        Logger.debug('thread_pool_sender started', id_=self.id_)

        thread_pool_receiver.start()
        Logger.debug('thread_pool_receiver started', id_=self.id_)

        thread_miner_sender.start()
        Logger.debug('thread_miner_sender started', id_=self.id_)

        thread_miner_receiver.start()
        Logger.debug('thread_mine_receiver started', id_=self.id_)

        #thread_periodic_calls.start()
        #Logger.debug('thread_periodic_calls started', id_=self.id_)

        thread_pool_receiver.join()
        thread_pool_processor.join()
        thread_miner_receiver.join()
        thread_miner_processor.join()
        thread_miner_sender.join()
        thread_pool_sender.join()

        #thread_periodic_calls.join()

        return# self

    """
    def init_coin(self, data_dic):
        Logger.debug('Entered init_coin', id_=self.id_)

        coin, profitability = self.api.get_most_profitable()

        req_params = data_dic['params']
        for i in range(len(req_params)):
            # initial phase, get proxy from miner
            if 'proxy' in req_params[i]:
                Logger.debug('proxy keyword detected', id_=self.id_)
                req_params[i] = self.setting.get_param(coin) + ',mc=' + coin

                json_data = json.dumps(data_dic) + '\n'

                Logger.debug('init_coin() modified request to: ' + json_data, id_=self.id_)

                self.last_coin = coin

                self.pool_sending_queue.put(json_data)
                Logger.warning('\n' + '=' * 256, id_=self.id_)
                Logger.warning('\nMiner start to mine $' + coin, id_=self.id_)
                Logger.important('Current profitability: ' + str(profitability))

                #self.last_switching = time.time()
                
                
    def choose_coin(self):
        if time.time() - self.last_switching < 1:
            return

        Logger.debug('Entered choose_coin', id_=self.id_)
        self.last_switching = time.time()

        coin, profitability = self.api.get_most_profitable()

        if self.last_coin and coin != self.last_coin:
            Logger.warning('\nMiner Switching to $' + coin, id_=self.id_)
            Logger.important('Current profitability: ' + str(profitability))
            self.exit_signal = True

            self.close()
    """

    def close(self, hard=False):
        t = threading.Thread(target=self._close_thread, args=(hard,))
        t.start()

    def _close_thread(self, hard=False):
        if not hard:
            self.miner_sending_queue.put('{"id":0,"method":"client.reconnect","params":[]}\n')
        self.exit_signal = True

        Logger.debug('Server restart', id_=self.id_)
        time.sleep(5)
        try:
            self.server_conn.close()
        except AttributeError:
            pass

        self.server = None

        try:
            self.client.server.close()
        except AttributeError:
            pass

        # raise Exception('Server restart')

    def periodic_calls(self):
        while True:
            if self.exit_signal:
                Logger.debug('periodic_calls exit_signal', id_=self.id_)
                return

            self.choose_coin()

            self.server_conn

            time.sleep(Proxy.BLOCK_TIME)

    def send_to_pool(self):
        while True:
            if self.exit_signal:
                Logger.debug('send_to_pool exit_signal', id_=self.id_)
                return

            if not self.client:
                continue

            try:
                sending_data = self.pool_sending_queue.get(block=True, timeout=Proxy.BLOCK_TIME)
            except queue.Empty:
                continue

            enc_data = sending_data.encode('utf-8')

            try:
                self.client.send(enc_data)
            except OSError as e:
                Logger.error(str(e) + 'OSError in proxy.py send_to_pool()', id_=self.id_)
                self.close()

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
        consecutive_rejections = 0
        while True:
            if self.exit_signal:
                Logger.debug('process_from_pool exit_signal', id_=self.id_)
                return

            try:
                pool_data = self.client.pool_receive_queue.get(block=True, timeout=Proxy.BLOCK_TIME)
            except queue.Empty:
                continue

            if 'mining.notify' in pool_data:
                print()

            json_obj = json.loads(pool_data)
            if 'result' in json_obj.keys() and json_obj['result'] is False:
                Logger.warning('Pool: ' + pool_data, id_=self.id_)

                # prevent rejections
                consecutive_rejections += 1

                if consecutive_rejections >= 3:
                    self.close()
            else:
                Logger.info('Pool: ' + repr(pool_data), id_=self.id_)
                consecutive_rejections = 0

            #if self.backup:
            #    if 'mining.notify' in pool_data:
            #        if 'result' in json_obj.keys() and json_obj['result'][2] <= 3:
            #            json_obj['result'][2] = 4  # change difficulty to 4

                         #pool_data = json.dumps(json_obj)

                #if 'mining.set_difficulty' in pool_data:
                #    if json_obj['params'][0] < 500000:
                #        json_obj['params'][0] = 500000

            # if reconnect, send it then close sometime after
            if 'client.reconnect' in pool_data:
                self.close()
                return

            # redirect the data strait to the miner
            self.miner_sending_queue.put(pool_data)

    def receive_from_miner(self):
        while True:
            if self.exit_signal:
                Logger.debug('receive_from_miner exit_signal', id_=self.id_)
                return

            ready = select.select([self.server_conn], [], [], Proxy.BLOCK_TIME)  # this bit basically block for a second
            if ready[0]:
                try:
                    data = self.server_conn.recv(8000)
                except ConnectionAbortedError:
                    Logger.warning('ConnectionAbortedError', id_=self.id_)
                    self.close()
                    return
                except OSError:
                    Logger.warning('Socket might already closed', id_=self.id_)
                    self.close()
                    return

                try:
                    dec_data = data.decode("utf-8")
                except AttributeError:
                    self.close()
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
                miner_data = self.miner_receive_queue.get(block=True, timeout=Proxy.BLOCK_TIME)
            except queue.Empty:
                continue

            Logger.important('Miner: ' + miner_data, id_=self.id_)

            ''' Change the proxy user pass'''
            miner_data = miner_data.replace('proxy', self.mining_params)
            miner_data = miner_data.replace(Proxy.USER, self.user_name)

            ''' Change Nicehash miner to cgminer '''
            miner_data = miner_data.replace('NiceHash', 'cgminer')

            Logger.debug('Miner Modified ' + miner_data)
            self.pool_sending_queue.put(miner_data)

    def send_to_miner(self):
        """
        no sending queue, send straight to miner
        :param pool_data:
        :return:
        """

        while True:
            if self.exit_signal and self.miner_sending_queue.empty():
                Logger.debug('send_to_miner exit_signal', id_=self.id_)
                return

            try:
                sending_data = self.miner_sending_queue.get(block=True, timeout=Proxy.BLOCK_TIME)
            except queue.Empty as e:
                continue

            enc_data = sending_data.encode('utf-8')

            try:
                self.server_conn.sendall(enc_data)
            except OSError as e:
                Logger.error(str(e) + 'OSError in proxy.py send_to_miner()', id_=self.id_)
                self.close(hard=True)

