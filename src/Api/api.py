import requests
import logging


class Api:
    def __init__(self, algo, coin_lists):
        self.algo = algo
        self.coin_lists = coin_lists

    def get_most_profitable(self):
        try:
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

            return coin_to_mine
        except Exception as e:
            logging.warning(e)
            return self.coin_lists[0]