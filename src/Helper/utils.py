class Utils:
    @staticmethod
    def zerg_to_nice_algo_converter(zerg_algo):
        if zerg_algo == 'ethash':
            return 'daggerhashimoto'
        elif zerg_algo == 'sha256':
            return 'sha256asicboost'
        else:
            return zerg_algo

    @staticmethod
    def price_difference(price_1, price_2):
        if price_1 == 0 and price_2 == 0:
            return 0

        if price_1 > price_2:
            return (price_1 - price_2) / price_1
        else:
            return (price_2 - price_1) / price_2
