import socket
import threading
import logging
from datetime import datetime
from TCP.ky_tcp_server import ky_cloud_protocol as protocol

global TCP_TIMEOUT_SECONDS
global SERVER_RUNNING
global CLIENTS
TCP_TIMEOUT_SECONDS = 0
SERVER_RUNNING = False
CLIENTS = {}
# 클라이언트 형식
# CLIENTS[client_address] = {
#             'socket': client_sock,
#             'data': client_data,
#             'thread': client_thread,
#             'running': True,
#             'sno': ""
#         }
# global SNO
# SNO = {}

"""
TCP_server.py 목적
1. 데이터 수신
2. 데이터 무결성 검정 (7F~7E), 0x7F 와 0x7E 사이의 구간은 0x7D 로 Byte Stuffing 을 해준다.
3. cmd에 따른 데이터 처리방법 결정
4. protocol에서 처리된 값 작성
 - 분리된 데이터를 Client info에 작성
 - protocol로부터 받은 이벤트 처리
server_IP = "121.254.224.199"
server_port = 1900
"""


def unescape_data(data):
    # Byte Stuffing을 처리하는 함수
    # 두 코드 모두 0x7D가 나오면 다음 바이트에 XOR 연산을 적용하여 Byte Stuffing을 수행합니다
    # C#의 commandParsing와 같습니다.
    result = bytearray()
    i = 0
    while i < len(data):
        if data[i:i + 1] == b"\x7D":
            i += 1
            result.append(data[i] ^ 0x20)
        else:
            result.extend(data[i:i + 1])
        i += 1
    return bytes(result)

def create_model(conn, client_addr, client_data):

    START_OF_PACKET = 0x7F  # 패킷 시작값
    END_OF_PACKET = 0x7E  # 패킷 종료값
    returnData=""
    # 1. 데이터 패킷 수신
    received_packet = conn.recv(512)  # 최대길이 512바이트

    logging.info(f"received_packet: {received_packet}")
    # 3. 0x7f, 0x7e를 찾는다.
    start_index = received_packet.find(START_OF_PACKET)
    received_packet = received_packet[start_index:]
    end_index = received_packet.find(END_OF_PACKET)

    # 2. Byte Stuffing
    received_packet = unescape_data(received_packet[:end_index + 1])

    # cmd에 따른 구분
    cmd = received_packet[1:3]
    cmd = int.from_bytes(cmd, byteorder='big')

    # if checkcrc:
    length = received_packet[3:5]
    length = int.from_bytes(length, byteorder='big')

    data = received_packet[5:length + 5]

    if cmd == 1 and length == 183:
        logging.info("cmd1 running")
        decoded_data = protocol.cmd_one(data)
        client_data.set_cmd_one(decoded_data)
        sno = decoded_data.get('ai_pems_info').get('device_serial_number')
        conn.send(make_buff(cmd, 0))  # 전송 결과를 return하도록 되어있다.


    elif cmd == 3 and length == 35:
        logging.info("cmd3 running")
        decoded_data = protocol.cmd_three(data)
        sno = decoded_data[0].get('ai_pems_info').get(
            'device_serial_number')
        client_data.set_cmd_three(decoded_data)
        conn.send(make_buff(cmd, 0))
    return sno, client_data
# elif cmd == 3 and length == 35:
# decoded_data = protocol.cmd_three(data)
# clent_data.set_cmd_three(decoded_data)
# sno = clent_data.get_cmd_three().get('cmd_three')[0].get('ai_pems_info').get(
#     'device_serial_number')
# CLIENTS[client_ip]['data'] = clent_data
# CLIENTS[client_ip]['sno'] = sno
# conn.send(make_buff(cmd, 0))
#
# for client_address in CLIENTS:
#     if CLIENTS[client_address]['sno'] == sno and client_address != client_ip:
#         CLIENTS[client_address]['running'] = False


def handle_client(conn, client_addr):
    """
    전략
    1. 256바이트 단위로 데이터 패킷을 받는다.
    2. 해당 recv데이터를 0x7F 와 0x7E 사이의 구간은 0x7D로 Byte Stuffing을 해석한다.
    3. 받은 리시브 데이터에 7f, 7e값을 찾는다.
    4. crc16로 검증한다.
    5. response 작성
    6. clients 등록
    """
    global SERVER_RUNNING
    global TCP_TIMEOUT_SECONDS
    global CLIENTS
    # global SNO
    client_ip = client_addr
    conn.settimeout(TCP_TIMEOUT_SECONDS)  # 서버 타임아웃 설정
    START_OF_PACKET = 0x7F  # 패킷 시작값
    END_OF_PACKET = 0x7E  # 패킷 종료값

    isRunning = CLIENTS[client_ip]['running']
    try:
        while isRunning:
            isRunning = CLIENTS[client_ip]['running']
            if not isRunning:
                break
            checkcrc = False

            # 1. 데이터 패킷 수신
            received_packet = conn.recv(512)  # 최대길이 512바이트

            if not received_packet:
                # sleep(1)
                continue
            else:
                # logging.info(f"received_packet: {received_packet}")

                # 3. 0x7f, 0x7e를 찾는다.
                start_index = received_packet.find(START_OF_PACKET)
                received_packet = received_packet[start_index:]
                end_index = received_packet.find(END_OF_PACKET)

                # 2. Byte Stuffing
                received_packet = unescape_data(received_packet[:end_index+1])

                if start_index != -1 and end_index != -1:
                    length = received_packet[3:5]
                    length = int.from_bytes(length, byteorder='big')
                    packet_len = len(received_packet) # cmd1: 191

                if start_index != -1 and end_index != -1:
                    # received_packet = received_packet[:end_index + 1]
                    calculated_crc = generate_crc(received_packet, len(received_packet))  # crc 16 생성
                    received_crc = int.from_bytes(received_packet[-3:-1], byteorder='big')  # 전송받은 crc16 추출

                    # # 4. 검증
                    checkcrc = (calculated_crc == received_crc)
                    # logging.info(f"c, r, check: {calculated_crc}, {received_crc}, {checkcrc}")
                    # 검증단계가 필요하다 정상적으로 들어오는 데이터도 crc가 일치하지 않는다.

                    # cmd에 따른 구분
                    cmd = received_packet[1:3]
                    cmd = int.from_bytes(cmd, byteorder='big')

                    # if checkcrc:
                    length = received_packet[3:5]
                    length = int.from_bytes(length, byteorder='big')

                    data = received_packet[5:length + 5]

                    clent_data = CLIENTS[client_ip]['data']
                    if cmd == 1 and length == 183:
                        logging.info("running cmd 1")
                        # logging.info(str(protocol.cmd_one(data)))
                        decoded_data = protocol.cmd_one(data)
                        clent_data.set_cmd_one(decoded_data)
                        # clent_data.cmd_one.update(decoded_data)
                        sno = clent_data.get_cmd_one().get('cmd_one').get('ai_pems_info').get('device_serial_number')
                        CLIENTS[client_ip]['data'] = clent_data
                        CLIENTS[client_ip]['sno'] = sno
                        conn.send(make_buff(cmd, 0))  # 전송 결과를 return하도록 되어있다.
                        """
                        make_buff 예시: b'\x7f\x00\x01\x00\x01\x00%\xd4~'
                        """
                    elif cmd == 2 and length == 43:  # 사용안함
                        logging.info(str(protocol.cmd_twe(data)))
                        conn.send(make_buff(cmd))
                    elif cmd == 3 and length == 35:
                        logging.info("running cmd 3")
                        # logging.info(f"cmd_three packet: {received_packet}")
                        # logging.info(str(protocol.cmd_three(data)))
                        decoded_data = protocol.cmd_three(data)
                        clent_data.set_cmd_three(decoded_data)
                        sno = clent_data.get_cmd_three().get('cmd_three')[0].get('ai_pems_info').get(
                            'device_serial_number')
                        CLIENTS[client_ip]['data'] = clent_data
                        CLIENTS[client_ip]['sno'] = sno
                        conn.send(make_buff(cmd, 0))

                    for client_address in CLIENTS:
                        if CLIENTS[client_address]['sno'] == sno and client_address != client_ip:
                            CLIENTS[client_address]['running'] = False

    except socket.timeout:
        logging.warning(f"Client {client_ip} timed out and will be disconnected.")
    except Exception as e:
        logging.warning(f"An error occurred: {e}")
        print(e)
    finally:
        conn.close()
        del CLIENTS[client_addr]
        logging.info(f"close {client_ip}")

    # try:
    #     del CLIENTS[client_addr]
    #     logging.info(f"close {client_ip}")
    #     if SNO.get(key) is not None:
    #         for key in SNO:
    #             if SNO.get(key, '') == client_ip:
    #                 del SNO[key]
    #                 break
    # except Exception
    #     # for sno in SNO:
    #     #     if SNO.get(sno) == client_ip:
    #     #         del SNO[sno]


def activate_server(tcp_host='localhost', tcp_port=1900):
    """
    TCP 서버 실행
    1. tcp_host:tcp_port로 tcp소켓 open
    2. ip에 따라 데몬 쓰레드 부여
    """
    # global SNO

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # 1. tcp 소켓 open
            TCP_server_open()
            s.bind((tcp_host, tcp_port))
            logging.info(f"TCP Server Open, {tcp_host}:{tcp_port}")
            s.listen()
            while SERVER_RUNNING:
                client_sock, client_address = s.accept()  # 큐 대기상태
                client_data = protocol.Data()

                sno, client_data = create_model(client_sock, client_address, client_data) # 여기서 클라이언트를 다 만들어야해.
                client_thread = threading.Thread(target=handle_client, args=(client_sock, client_address))
                client_thread.daemon = True
                CLIENTS[client_address] = {
                    'socket': client_sock,
                    'data': client_data,
                    'thread': client_thread,
                    'running': True,
                    'sno': sno
                }

                for client in CLIENTS:
                    if CLIENTS[client]['sno'] == sno and client != client_address:
                        logging.info(f"sno: {sno}, client: {client}, new: {client_address}")
                        old_thread = CLIENTS[client]['thread']
                        # client_data = CLIENTS[client_address]['data']  # 이전 데이터 저장
                        CLIENTS[client]['running'] = False
                        old_thread.join()  # 이전 스레드가 종료될 때까지 기다림
                        logging.info(f"Disconnected by {client_address}")
                        del CLIENTS[client_address]

                        break


                # if client_address in CLIENTS:
                #     """
                #     같은IP, port가 접근할 경우 이전 스레드 종료
                #     """
                #     old_thread = CLIENTS[client_address]['thread']
                #     client_data = CLIENTS[client_address]['data']  # 이전 데이터 저장
                #     CLIENTS[client_address]['running'] = False
                #     old_thread.join()  # 이전 스레드가 종료될 때까지 기다림
                #     logging.info(f"Disconnected by {client_address}")
                #     del CLIENTS[client_address]

                logging.info(f"Connected by {client_address}")
                # client_thread = threading.Thread(target=handle_client, args=(client_sock, client_address))
                # client_thread.daemon = True
                # CLIENTS[client_address] = {
                #     'socket': client_sock,
                #     'data': client_data,
                #     'thread': client_thread,
                #     'running': True,
                #     'sno': sno
                # }
                client_thread.start()

    except Exception as e:
        logging.error(e)
    finally:
        s.close()
        TCP_server_close()
        for client in CLIENTS:
            client['thread'].join()
        logging.info("Server shutdown")


def TCP_server_open():
    """
    while문 동작 설정 및 TCP 연결시간 제한 설정
    """
    global TCP_TIMEOUT_SECONDS
    global SERVER_RUNNING  # 서버 running
    TCP_TIMEOUT_SECONDS = 60 * 60
    SERVER_RUNNING = True


def TCP_server_close():
    global TCP_TIMEOUT_SECONDS
    global SERVER_RUNNING

    SERVER_RUNNING = False


def generate_crc(buf_ptr, length):
    """
    crc-16 계산함수.

    위의 generate_crc 함수는 주어진 buf_ptr의 CRC-16 값을 계산합니다. 코드에서 사용된 테이블과 알고리즘은 일반적인 CRC-16 계산을 수행합니다.
    여기서 buf_ptr은 바이트의 배열이며, length는 계산에 사용되는 바이트 수입니다.
    함수는 초기 CRC 값인 0xFFFF로 시작하고, 주어진 바이트 배열의 각 바이트를 차례대로 처리하여 최종 CRC 값을 계산합니다.
    이 함수는 주어진 특정 buf_ptr과 length에 대해 CRC-16 값을 생성하는 데 사용됩니다.
    만약 이 함수를 호출한 후의 CRC 값을 사용하려면, 함수 호출 전에 buf_ptr과 length를 적절히 설정해야 합니다.
    """
    CRC16_TABLE = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401, 0xA001, 0x6C00, 0x7800, 0xB401,
                   0x5000, 0x9C01, 0x8801, 0x4400]
    usCRC = 0xFFFF
    for data in buf_ptr[:length]:
        usCRC = (usCRC >> 4) ^ CRC16_TABLE[(usCRC ^ (data & 0x0F)) & 0x0F]
        usCRC = (usCRC >> 4) ^ CRC16_TABLE[(usCRC ^ (data >> 4)) & 0x0F]

    return usCRC


def bytestuffing(dst, src, length):
    """
    0x7F, 0x7E, 0x7D 중 데이터 값이 같은경우, 0x7D을 추가함.
    """
    i = 0
    dst_len = 0
    # 0 and length-1 are Flags
    # 0 is STX
    dst[0] = src[0]  # DefineConstants.PACK_STX
    dst_len += 1

    for i in range(1, length - 1):
        if src[i] in [0x7F, 0x7E, 0x7D]:  # DefineConstants.PACK_STX, DefineConstants.PACK_ETX, DefineConstants.PACK_ESC
            dst[dst_len] = 0x7D  # DefineConstants.PACK_ESC
            dst_len += 1
        dst[dst_len] = src[i]
        dst_len += 1

    # length-1 is ETX
    dst[dst_len] = src[length - 1]
    dst_len += 1

    return dst_len


def make_buff(cmd, *args):
    """
    1. header+msg작성
    2. crc 적용
    3. buff 작성
    """

    msg_length = 5
    msg = bytearray(msg_length)
    RePcka = bytearray(msg_length)

    msg[:5] = [0, cmd, 0, 1, args[0]]

    if cmd == 2:
        msg_length = 11
        msg = bytearray(msg_length)
        RePcka = bytearray(msg_length)
        msg[:4] = [0, cmd, 0, msg_length]

        current_datetime = datetime.now()
        msg[4] = (current_datetime.year >> 8) & 0xFF  # yearHigh
        msg[5] = current_datetime.year & 0xFF  # yearLow
        msg[6] = current_datetime.month
        msg[7] = current_datetime.day
        msg[8] = current_datetime.hour
        msg[9] = current_datetime.minute
        msg[10] = current_datetime.second

    crc = generate_crc(msg, msg_length)
    CRCLow, CRCHigh = crc & 0xFF, (crc >> 8) & 0xFF
    """
    CRCLow와 CRCHigh는 주어진 crc 값을 바이트로 분할하는 연산을 나타냅니다.
    crc & 0xFF: 이 연산은 crc의 하위 8비트를 얻어내는 것으로, 이 값을 CRCLow에 할당합니다. 0xFF는 8비트의 모든 비트가 1인 값이기 때문에, 이 연산은 crc의 하위 8비트를 그대로 가져오는 효과를 가집니다.
    (crc >> 8) & 0xFF: 이 연산은 crc를 8비트 오른쪽으로 시프트한 다음, 그 결과의 하위 8비트를 얻어내는 것으로, 이 값을 CRCHigh에 할당합니다.이는 crc의 상위 8비트를 가져오는 효과를 가집니다.
    이렇게 함으로써 crc를 16비트로 나누어 CRCHigh는 상위 8비트, CRCLow는 하위 8비트가 되도록 합니다. 
    """

    RePckaLen = bytestuffing(RePcka, msg, msg_length)

    Sendbuff = bytearray(4 + RePckaLen)
    Sendbuff[0] = 127
    Sendbuff[1:RePckaLen + 1] = RePcka[:RePckaLen]
    Sendbuff[RePckaLen + 1] = CRCLow
    Sendbuff[RePckaLen + 2] = CRCHigh
    Sendbuff[RePckaLen + 3] = 126

    # # Simulating network write
    # logging.info(f"Simulated sending data for cmd {cmd}: {str(Sendbuff)}")
    return Sendbuff
    # If actual network write is needed, use the appropriate library or method


if __name__ == "__main__":
    import sys, os


    def get_script_directory():
        """
        파일위치 불러오기
        """
        # frozen: PyInstaller, cx_Freeze, etc.
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        # script file
        script_path = os.path.realpath(sys.argv[0])
        return os.path.dirname(script_path)


    def set_logging_config(log_directory):
        """
        log작성 config설정
        - root경로로부터 폴더명, 파일명을 지정한다.
        """
        if not os.path.exists(log_directory):  # log폴더가 없을경우 생성
            os.makedirs(log_directory)

        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d")
        logging.basicConfig(
            filename=f'{log_directory}/Interface__{formatted_time}.log',
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


    root = get_script_directory()
    log_directory = os.path.join(root, 'log')
    set_logging_config(log_directory)

    try:
        activate_server(tcp_host='localhost', tcp_port=1900)
        # activate_server(tcp_host='192.168.15.175', tcp_port=1900)
        # activate_server(tcp_host='121.254.224.199', tcp_port=1900)
    except KeyboardInterrupt:
        logging.info("Server shutdown by KeyboardInterrupt.")
