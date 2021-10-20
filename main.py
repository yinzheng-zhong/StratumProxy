import sys
from src.Proxy.server import StratumServer
from src.Helper.config_reader import ConfigReader
import time
import socket
from src.Model.logger import Logger
from src.Api.api import Api
import gc

if __name__ == '__main__':
    arg = sys.argv[1]

    list_conns = []
    setting = ConfigReader(arg)
    api = Api(arg, setting.get_coins())

    port = setting.get_server_port()

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", port))
        server.listen(5)

        while True:
            list_conns.append(StratumServer(arg, server, api).run())

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

    except Exception as e:
        print('Error at Main', e)
        sys.exit()
