import socket
import threading
import logging
from TCP.tcp_server import protocol as protocol

global TCP_TIMEOUT_SECONDS
global SERVER_RUNNING
TCP_TIMEOUT_SECONDS = 5 * 60
SERVER_RUNNING = False
CLIENTS = {}

"""
TCP_server.py 목적
1. 데이터 수신
2. cmd에 따른 데이터 처리방법 결정
3. protocol에서 처리된 값 작성
 - 분리된 데이터를 Client info에 작성
"""


def handle_client(conn, client_addr):
    global SERVER_RUNNING
    global TCP_TIMEOUT_SECONDS

    client_ip = client_addr[0]
    client_data = CLIENTS[client_ip]['data']
    conn.settimeout(TCP_TIMEOUT_SECONDS)
    try:
        while SERVER_RUNNING:
            isRunning = CLIENTS[client_ip]['running']
            header = conn.recv(4)
            if not header or not isRunning:
                break

            cmd, length = header[:2], header[2:]
            cmd = int.from_bytes(cmd, byteorder='big')
            length = int.from_bytes(length, byteorder='big')
            data = conn.recv(length)

            # 1. 검증
            # 2. 데이터 프로토콜 실행
            if cmd == 1 and length == 650:
                e_data, f_data, p_data = protocol.cmd_one(data, client_ip)
                client_data.set_electricity_data(e_data)
                client_data.set_flow_data(f_data)
                client_data.set_pressure_data(p_data)
                CLIENTS[client_ip]['data'] = client_data
                # logging.info('CLIENTS: ', CLIENTS[client_ip]['data'])
            if cmd == 2:
                #cmd2의 경우 lengeth == 24
                pass
                # 현재 사용안함
                # is_used = protocol.cmd_two(data)
                # CLIENTS[client_ip]['is_used'] = is_used

            # service.send_message()
            #### Data 전송 END###

    except socket.timeout:
        logging.warning(f"Client {client_ip} timed out and will be disconnected.")
    except Exception as e:
        logging.warning(f"An error occurred: {e}")
    finally:
        conn.close()
        if client_ip in CLIENTS:
            CLIENTS[client_ip]['running'] = False
            logging.info(f"Connection with {client_ip} closed.")


def activate_server(tcp_host='localhost', tcp_port=1900):
    """
    TCP 서버 실행
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # tcp 소켓 open
            s.bind((tcp_host, tcp_port))
            logging.info(f"TCP Server Open, {tcp_host}:{tcp_port}")
            s.listen()
            while SERVER_RUNNING:
                client_sock, client_address = s.accept()
                client_ip = client_address[0]
                client_data = protocol.Data()
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

            # except KeyboardInterrupt:
            #     print("서버를 종료합니다.")
    except Exception as e:
        logging.error(e)
    finally:
        for client in CLIENTS:
            CLIENTS[client]['running'] = False
        s.close()
        TCP_server_close()
        logging.info("Server shutdown")



def TCP_server_open():
    """
    while문 동작 설정 및 TCP 연결시간 제한 설정
    """
    global TCP_TIMEOUT_SECONDS
    global SERVER_RUNNING  # 서버 running
    TCP_TIMEOUT_SECONDS = 5 * 60
    SERVER_RUNNING = True


def TCP_server_close():
    global SERVER_RUNNING

    SERVER_RUNNING = False

if __name__ == "__main__":
    from datetime import datetime
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d")
    logging.basicConfig(
        filename=f'D:/EquipIF/TCP_Server/log/TCP_server_{formatted_time}.log',
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    TCP_server_open()
    activate_server(tcp_host='192.168.0.232', tcp_port=1900)
    # make_tcp_server(tcp_host='localhost', tcp_port=1900).start_server()
