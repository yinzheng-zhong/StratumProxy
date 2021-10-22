import requests
from src.Model.logger import Logger
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
import html_to_json
import numpy as np
import threading


class Api:
    def __init__(self, algo, coin_lists):
        self.algo = algo
        self.coin_lists = coin_lists

        self.webpage_url = "https://zergpool.com/site/mining?algo=" + algo
        self.driver = webdriver.Chrome('drivers/chromedriver')

        self.last_coin = ''
        self.last_profitability = 0

        self.thre = threading.Thread(target=self.start_fetching)
        self.thre.start()

    def get_most_profitable(self):
        return self.last_coin, self.last_profitability

    def start_fetching(self):
        while True:
            try:
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
                print(e)

            time.sleep(5)

    def _make_request(self):
        try:
            Logger.info('Fetching profitability from zergpool')

            response = {}

            self.driver.get(self.webpage_url)

            element = WebDriverWait(self.driver, 5).until(
                ec.presence_of_element_located((By.ID, "maintable3"))
            )

            maintable = element.get_attribute('innerHTML')

            rjson = html_to_json.convert(maintable)

            table = rjson['tbody'][0]['tr']

            for row in table:
                try:
                    coin_name = row['td'][2]['b'][0]['_value'].split(' ')[-1]   # coin name occurs at the 2rd row
                    profitability = row['td'][8]['b'][0]['_value']  # profitability occurs at the 8th row
                except Exception:
                    continue    # some rows aren't for coin info

                if coin_name and profitability:
                    # make a dict just like the normal request get from the API
                    response[coin_name] = {'algo': self.algo, 'estimate_current': float(profitability) / 1000}

            return response
        except Exception as e:
            Logger.warning('Back to API request')
            print(e)
            response = requests.get("http://api.zergpool.com:8080/api/currencies").json()
            return response
