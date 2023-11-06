import socket
import threading
import logging
from TCP import protocol

# 클라이언트 연결에 타임아웃 설정
global TCP_TIMEOUT_SECONDS
global IS_SEND_DATA
global SERVER_RUNNING
CLIENTS = {}


def handle_client(conn, client_addr):
    global IS_SEND_DATA
    global SERVER_RUNNING

    client_ip = client_addr[0]
    client_data = CLIENTS[client_ip]['data']
    conn.settimeout(TCP_TIMEOUT_SECONDS)

    try:
        while SERVER_RUNNING:
            isRunning = CLIENTS[client_ip]['running']
            header = conn.recv(4)
            if (not header) or (not isRunning):
                break

            cmd, length = header[:2], header[2:]
            cmd = int.from_bytes(cmd, byteorder='big')
            length = int.from_bytes(length, byteorder='big')
            data = conn.recv(length)
            if cmd == 1:
                e_data, f_data, p_data = protocol.cmd_one(data, client_ip)
                client_data.set_electricity_data(e_data)
                client_data.set_flow_data(f_data)
                client_data.set_pressure_data(p_data)
                CLIENTS[client_ip]['data'] = client_data
            if cmd == 2:
                pass
                # is_used = protocol.cmd_two(data)
                # CLIENTS[client_ip]['is_used'] = is_used
                # service.send_message()

            # service.send_message()
            #### Data 전송 END###

    except socket.timeout:
        logging.warning(f"Client {client_ip} timed out and will be disconnected.")
    except Exception as e:
        logging.warning(f"An error occurred: {e}")
    finally:
        conn.close()
        if client_ip in CLIENTS:
            del CLIENTS[client_ip]
            logging.info(f"Connection with {client_ip} closed.")


def activate_server(tcp_host='localhost', tcp_port=1900):
    """
    TCP 서버 실행
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        TCP_server_open()
        s.bind((tcp_host, tcp_port))
        logging.info("TCP Server Open")
        try:
            s.listen()
            while SERVER_RUNNING:
                client_sock, client_address = s.accept()

                client_ip = client_address[0]
                client_data = Data()
                if client_ip in CLIENTS:
                    """
                    같은IP가 접근할 경우 이전 스레드 종료
                    """
                    old_thread = CLIENTS[client_ip]['thread']
                    client_data = CLIENTS[client_ip]['data']
                    CLIENTS[client_ip]['running'] = False
                    old_thread.join()  # 이전 스레드가 종료될 때까지 기다림
                    logging.info(f"Disconnected by {client_address[0]}")
                logging.info(f"Connected by {client_address}")

                client_thread = threading.Thread(target=handle_client, args=(client_sock, client_address))
                client_thread.daemon = True
                CLIENTS[client_ip] = {
                    'socket': client_sock,
                    'data': client_data,
                    'thread': client_thread,
                    'running': True
                }
                client_thread.start()

        except KeyboardInterrupt:
            print("서버를 종료합니다.")
        except Exception as e:
            logging.error(e)
        finally:
            for client in CLIENTS:
                client['thread'].join()
            s.close()

            TCP_server_close()

            logging.info("Server shutdown")


def TCP_server_open():
    global TCP_TIMEOUT_SECONDS
    global SERVER_RUNNING
    global IS_SEND_DATA
    TCP_TIMEOUT_SECONDS = 60 * 5
    SERVER_RUNNING = True
    IS_SEND_DATA = True


def TCP_server_close():
    global TCP_TIMEOUT_SECONDS
    global SERVER_RUNNING
    global IS_SEND_DATA

    SERVER_RUNNING = False
    IS_SEND_DATA = False


# Model
class Data:
    def __init__(self) -> None:
        self.electricity_data = []
        self.flow_data = []
        self.pressure_Data = []
        self.connectData = []

    def set_electricity_data(self, data):
        self.electricity_data = data

    def set_flow_data(self, data):
        self.flow_data = data

    def set_pressure_data(self, data):
        self.pressure_Data = data

    def set_connect_data(self, data):
        self.connectData = data

    def get_all_data(self):
        data = []
        data.extend(self.electricity_data)
        data.extend(self.flow_data)
        data.extend(self.pressure_Data)
        return data

    def clean(self):
        self.electricity_data = []
        self.flow_data = []
        self.pressure_Data = []


if __name__ == "__main__":
    activate_server(tcp_host='localhost', tcp_port=1900)
