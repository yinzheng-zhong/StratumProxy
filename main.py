import sys
from .src.Proxy.server import StratumServer
import time

if __name__ == '__main__':
    arg = sys.argv[1]
    print('Mining using ' + arg)

    try:
        server = StratumServer(arg)
        server.run()
    except Exception as e:
        print(e, 'exception in main')

    time.sleep(10)
