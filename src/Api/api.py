import requests
from src.Model.logger import Logger
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from src.Helper.config_reader import ConfigReader
import html_to_json
import numpy as np
import threading


class Api:
    def __init__(self, algo):
        self.algo = algo
        self.setting = ConfigReader(algo)
        self.coin_lists = self.setting.get_coins()

        self.webpage_url = "https://zergpool.com/site/mining?algo=" + algo

        self.driver = None
        self.init_driver()

        self._thre = threading.Thread(target=self.start_fetching)
        self._thre.start()

        self._last_coin = ''
        self._last_profitability = 0

    def get_most_profitable(self):
        return self._last_coin, self._last_profitability

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

                self._last_coin = coin_to_mine
                self._last_profitability = max_profit

                Logger.important('Current estimate: ' + str(max_profit))
            except Exception as e:
                print(e)

            time.sleep(5)

    def _make_request(self):
        try:
            Logger.info('Fetching profitability from zergpool')

            response = {}
            self.driver.refresh()

            element = WebDriverWait(self.driver, 15).until(
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
                    response[coin_name] = {
                        'algo': self.algo,
                        'estimate_current': float(profitability) / self.setting.get_conversation()
                    }

            return response
        except Exception as e:
            Logger.warning('Back to API request')
            Logger.debug(str(e))
            try:
                response = requests.get("http://api.zergpool.com:8080/api/currencies").json()
            except Exception as e:
                Logger.debug(str(e))
                response = {}

            return response

    def init_driver(self):
        #try:
        #    self.driver = webdriver.Chrome('drivers/chromedriver')
        #except Exception as e:
        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome('drivers/chromedriver', options=options)
        Logger.warning('Switch to headless driver')

        self.driver.get(self.webpage_url)
