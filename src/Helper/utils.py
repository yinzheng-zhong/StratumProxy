class Utils:
    @staticmethod
    def zerg_to_nice_algo_converter(zerg_algo):
        if zerg_algo == 'ethash':
            return 'daggerhashimoto'
        elif zerg_algo == 'sha256':
            return 'sha256asicboost'
        else:
            return zerg_algo
