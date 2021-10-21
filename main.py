import sys
from src.Proxy.proxy import StratumServer
from src.Helper.config_reader import ConfigReader
import time
import socket
from src.Model.logger import Logger
from src.Api.api import Api
import gc

if __name__ == '__main__':
    algo = sys.argv[1]

    list_conns = []
    setting = ConfigReader(algo)
    api = Api(algo, setting.get_coins())

    port = setting.get_server_port()


    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(5)

    is_profitable = True

    while True:
        _, profitability = api.get_most_profitable()

        if profitability * 0.95 > 0.0062:
            is_profitable = True
            list_conns.append(StratumServer(algo, server, api).run())
        elif is_profitable:
            Logger.warning('No profitable at the moment: ' + str(profitability))
            is_profitable = False

        new_list = []
        for conn in list_conns:
            if conn.exit_signal:
                Logger.warning('Delete conn' + str(conn))
                del conn
            else:
                new_list.append(conn)

        list_conns = new_list[:]
        gc.collect()

        Logger.warning('list_conns' + str(len(list_conns)))
        time.sleep(0.1)
