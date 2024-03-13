import logging
import threading

from .tcp_server import TCP_server as base_tcp_server
from .ky_tcp_server import KY_TCP_server as ky_tcp_server


class make_tcp_server():
    def __init__(self, tcp_host, tcp_port, plant_target):
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.tcp_server = None
        self.tcp_server_thread = None

        if plant_target == 'tcp_server':
            self.tcp_server = base_tcp_server
        elif plant_target == 'ky_tcp_server':
            self.tcp_server = ky_tcp_server
        else:
            self.tcp_server = None

    def make_tcp_server_thread(self):
        """
        tcp서버를 구동하는 스레드를 만듭니다.
        """
        logging.info(f"self.tcp_server.activate_server: {self.tcp_server.activate_server}\n" +
                     f"self.tcp_host: {self.tcp_host}\n" +
                     f"self.tcp_port: {self.tcp_port}")

        self.tcp_server_thread = threading.Thread(target=self.tcp_server.activate_server,
                                                  args=(self.tcp_host, self.tcp_port))  # tcp 서버 Thread 설정
        self.tcp_server_thread.daemon = True

    def get_clients_data(self):
        return self.tcp_server.CLIENTS

    def get_all_cmd_three(self):
        clients = self.tcp_server.CLIENTS
        cmd_three_dict = dict()
        for client in clients:
            client_data = clients[client]['data']
            cmd_three_dict[client] = client_data.get_cmd_three()
        return cmd_three_dict

    def start_server(self):
        self.tcp_server.TCP_server_open()
        self.tcp_server_thread.start()

    def stop_server(self):
        self.tcp_server.TCP_server_close()
        self.tcp_server_thread.join()

    def is_thread_running(self):
        return self.tcp_server_thread.is_alive()

# if __name__ == '__main__':
#     ky_tcp_server = make_tcp_server(tcp_host='192.168.15.175', tcp_port=1900, plant_target='ky_tcp_server')
#     ky_tcp_server.make_tcp_server_thread()
#     ky_tcp_server.start_server()
