import requests
from src.Model.logger import Logger
import time
from requests_html import HTMLSession
import html_to_json
import numpy as np


class Api:
    def __init__(self, algo, coin_lists):
        self.algo = algo
        self.coin_lists = coin_lists
        self.next_request_time = 0

        self.webpage_url = "https://zergpool.com/site/mining?algo=" + algo

        self.last_coin = ''
        self.last_profitability = 0

    def get_most_profitable(self):
        try:
            if time.time() < self.next_request_time:
                return self.last_coin, self.last_profitability

            response = self._make_request()

            max_profit = 0
            coin_to_mine = ''

            for i in self.coin_lists:
                for j in response.keys():
                    if i in j and response[j]['algo'] == self.algo:
                        current_estimate = float(response[j]['estimate_current'])
                        if current_estimate > max_profit:
                            max_profit = current_estimate
                            coin_to_mine = i

            self.last_coin = coin_to_mine
            self.last_profitability = max_profit

            return coin_to_mine, max_profit
        except Exception as e:
            Logger.warning(str(e))
            return self.coin_lists.keys()[0]

    def _make_request(self):
        try:
            Logger.info('Fetching profitability from zergpool')
            self.next_request_time = time.time() + 10

            response = {}

            session = HTMLSession()
            r = session.get(self.webpage_url)
            r.html.render(sleep=2, keep_page=True, scrolldown=1)

            maintable = r.html.find("#maintable3")[0].html

            rjson = html_to_json.convert(maintable)

            table = rjson['table'][0]['tbody'][0]['tr']

            for row in table:
                try:
                    coin_name = row['td'][2]['b'][0]['_value'].split(' ')[-1]   # coin name occurs at the 2rd row
                    profitability = row['td'][8]['b'][0]['_value']  # profitability occurs at the 8th row
                except Exception:
                    continue    # some rows aren't for coin info

                if coin_name and profitability:
                    # make a dict just like the normal request get from the API
                    response[coin_name] = {'algo': self.algo, 'estimate_current': float(profitability) / 1000}

            session.close()

            return response
        except Exception:
            Logger.warning('Back to API request')
            response = requests.get("http://api.zergpool.com:8080/api/currencies").json()
            return response
