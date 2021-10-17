import sys
from src.Proxy.server import StratumServer
import time

if __name__ == '__main__':
    arg = sys.argv[1]
    print('Mining using ' + arg)

    while True:
        try:
            server = StratumServer(arg)
            server.run()
        except Exception as e:
            print(e)

        time.sleep(10)
