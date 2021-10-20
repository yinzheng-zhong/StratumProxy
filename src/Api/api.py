import requests
import logging
import time


class Api:
    def __init__(self, algo, coin_lists):
        self.algo = algo
        self.coin_lists = coin_lists
        self.last_request = 0
        self.last_coin = ''

    def get_most_profitable(self):
        try:
            if time.time() - self.last_request < 30:
                return self.last_coin

            response = requests.get("http://api.zergpool.com:8080/api/currencies").json()

            max_profit = 0
            coin_to_mine = ''

            for i in self.coin_lists:
                for j in response.keys():
                    if i in j and response[j]['algo'] == self.algo:
                        current_estimate = float(response[j]['estimate_current'])
                        if current_estimate > max_profit:
                            max_profit = current_estimate
                            coin_to_mine = i

            self.last_request = time.time()
            self.last_coin = coin_to_mine

            return coin_to_mine
        except Exception as e:
            logging.warning(e)
            return self.coin_lists[0]
