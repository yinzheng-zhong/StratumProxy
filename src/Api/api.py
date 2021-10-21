import requests
from src.Model.logger import Logger
import time


class Api:
    def __init__(self, algo, coin_lists):
        self.algo = algo
        self.coin_lists = coin_lists
        self.last_request = 0
        self.last_coin = ''
        self.last_profitability = 0

    def get_most_profitable(self):
        try:
            if time.time() - self.last_request < 1:
                return self.last_coin, self.last_profitability

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
            self.last_profitability = max_profit

            return coin_to_mine, max_profit
        except Exception as e:
            Logger.warning(str(e))
            return self.coin_lists[0]
