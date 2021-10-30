class Utils:
    @staticmethod
    def zerg_to_nice_algo_converter(zerg_algo):
        if zerg_algo == 'ethash':
            return 'daggerhashimoto'
        else:
            return zerg_algo
