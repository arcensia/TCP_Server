import socket
import threading
import time

from . import ky_util
from . import ky_cloud_protocol as protocol
import logging
import queue

alarm_queue = queue.Queue()
data_queue = queue.Queue()
del_client_queue = queue.Queue()
del_sno_queue = queue.Queue()

data_dict = dict()
CLIENTS = dict()
sno_client_dict = dict()

START_OF_PACKET = 0x7F  # 패킷 시작값
END_OF_PACKET = 0x7E  # 패킷 종료값
PACK_ESC = 0x7D
MAX_PACK_SIZE = 250


def listener(tcp_host='localhost', tcp_port=1900):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((tcp_host, tcp_port))
        s.listen()
        while True:
            try:
                client_sock, client_address = s.accept()
                # logging.info(f"client_address connect: {client_address}")
                client_sock.settimeout(6 * 60)

                ############## 테스트
                received_packet = client_sock.recv(250)
                # b'\x7f\x00\x01\x00\xb7\x07\xe8\x02\x0f\n\x15\x1e\x02\x03\x00\x02\x02\x03\x00\x00\x00\x01\x01\x02\x00>\x00L\x0e\xf9\x10h\x00l\x10h\x00l\x00\x01\x00\x00\x00\x00C\xbe\x1d\x88C\x96\x99\x0eH=\x92\x90K\xd3*\xa8?{K\xebE\x0b\xa0\x00D\x94\x00\x00J8/\xa8J\x82}^\xe8I\xf4\x85\xd0Jk\xae\x18E\x980\x00K\xd3E\xdcK\xd3E\xdc\x00>\x00\x1fA\xd4%\x8bF\xf4I\xf7\x00\x00\x00\x00\x00\x00\x00\x00E\xcd \x00Fl@\xafF}^\xca\xa9F\x04p\x00\x00\x00\x00\x00H.\xb5\x1dH.\xb5\x1d\x00\x00\x00\x04\x00\x00\x00\x02\x00\x00\x03\xdc\x00\x00\x05m\x00\x00\x02n\x00\x00\x05\xa0\x00\x00\x00\x02\x00\x00#\xcb\x00\x00#\xcb\x00\x00\x00\x00\xde!~\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                if not received_packet:
                    logging.info(f"no packet s, sno: {sno}")
                    pass

                else:
                    low_received_packet = received_packet
                    command_parsing_esc_flag = 0
                    received_packet, command_parsing_esc_flag = ky_util.command_parsing(received_packet,
                                                                                        command_parsing_esc_flag)
                    received_packet = bytes(received_packet)
                    start_index = received_packet.find(START_OF_PACKET)
                    received_packet = received_packet[start_index:]
                    length = received_packet[3:5]
                    length = int.from_bytes(length, byteorder='big')
                    received_packet = received_packet[:length + 9]
                    end_index = received_packet.rfind(END_OF_PACKET)
                    received_packet = received_packet[:end_index + 1]

                    cmd = received_packet[1:3]
                    cmd = int.from_bytes(cmd, byteorder='big')
                    length = received_packet[3:5]
                    length = int.from_bytes(length, byteorder='big')
                    data = received_packet[5:length + 5]
                    packet_len = len(received_packet)  # cmd1: 191, cmd3: 43

                    if cmd == 3 and length == 35 and packet_len == 43:
                        decoded_data = protocol.cmd_three(data)
                        for data in decoded_data:
                            client_sock.send(ky_util.make_buff(cmd, 0))
                            sno = str(data.get('ai_pems_info').get('device_serial_number')) + str(
                                data.get('ai_pems_info').get('device_type')) + str(
                                data.get('ai_pems_info').get('device_sequence'))
                            if len(data.get('arlam_info')) == 0:
                                if len(CLIENTS.get(sno, '')) == 0:
                                    CLIENTS[sno] = {
                                        "client_address": client_address,
                                        "client_sock": client_sock
                                    }
                                    # logging.info(f"new client {client_address}, sno: {sno}")
                                else:
                                    old_sock = CLIENTS[sno].get("client_sock", '')
                                    try:
                                        old_sock.close()
                                    except Exception as e:
                                        # logging.info(f"{e}")
                                        pass
                                    CLIENTS[sno].update({
                                        "client_address": client_address,
                                        "client_sock": client_sock
                                    })
                                    # logging.info(f"update client {client_address}, sno: {sno}")
                            else:
                                pass
                                # client_sock.close()
                                # logging.info(f"disconnect: {client_address} ")
                                # logging.info(f"did get cmd3: {client_address} ")
                        ############## 테스트 end
                    else:
                        logging.info(
                            f"no cmd data. low_received_packet: {low_received_packet}, received_packet: {received_packet}")
            except Exception as e:
                logging.error("listener error: {}".format(e))


def runrun(tcp_host='localhost', tcp_port=1900):
    tcp_thread = threading.Thread(target=listener, args=(tcp_host, tcp_port))
    tcp_thread.daemon = True
    tcp_thread.start()

    while tcp_thread.is_alive():
        try:
            while not del_client_queue.empty():
                close_target = del_client_queue.get()
                for sno in close_target:
                    try:
                        old_client = close_target[sno].get('client_address')
                        old_sock = close_target[sno].get('client_socket', '')
                        if old_sock != '':
                            old_sock.close()
                    except Exception as e:
                        logging.info(f"{e}")
                    finally:
                        logging.info(f"sno: {sno} Client disconnected: {old_client}")

                    if CLIENTS.get(sno).get('client_sock') == close_target[sno].get('client_socket'):
                        logging.info(f"close Client. sno: {sno}")
                        print(f"close Client. sno: {sno}")
                        del CLIENTS[sno]

            clients = CLIENTS.copy()

            if clients is not None and len(clients) > 0:
                for sno in list(clients):
                    client_address = clients[sno].get('client_address')
                    client_socket = clients[sno].get('client_sock')
                    # for client_address, client_socket in clients.items():
                    try:

                        received_packet = client_socket.recv(250)
                        command_parsing_esc_flag = 0
                        received_packet, command_parsing_esc_flag = ky_util.command_parsing(received_packet,
                                                                                            command_parsing_esc_flag)
                        received_packet = bytes(received_packet)
                        if not received_packet:
                            logging.info(f"no packet, sno: {sno}")
                            pass

                        else:
                            row_recived_packet = received_packet
                            # logging.info(f"client_address: {client_address}")
                            start_index = received_packet.find(START_OF_PACKET)
                            received_packet = received_packet[start_index:]
                            length = received_packet[3:5]
                            length = int.from_bytes(length, byteorder='big')
                            received_packet = received_packet[:length + 9]
                            end_index = received_packet.rfind(END_OF_PACKET)
                            received_packet = received_packet[:end_index + 1]

                            packet_len = len(received_packet)  # cmd1: 191, cmd3: 43

                            # cmd에 따른 구분
                            cmd = received_packet[1:3]
                            cmd = int.from_bytes(cmd, byteorder='big')

                            if start_index == -1 or end_index == -1 or start_index > end_index:
                                client_socket.send(ky_util.make_buff(cmd, 1))
                                logging.info(f"start_index: {start_index} and end_index: {end_index}")
                                logging.info(f"sno: {sno}, client_address: {client_address}")
                                logging.info(
                                    f"len: {len(row_recived_packet)}, received_packet row: {row_recived_packet}")
                                logging.info(
                                    f"issu len: {len(received_packet)}, issu received_packet: {received_packet}")

                            elif len(received_packet) != 191 and cmd == 1:
                                client_socket.send(ky_util.make_buff(cmd, 1))
                                logging.info(
                                    f"CMD 1 len: {len(row_recived_packet)}, received_packet row: {row_recived_packet}")

                                logging.info(
                                    f"sno: {sno}, CMD 1 issu len: {len(received_packet)}, issu received_packet: {received_packet}")

                            if start_index != -1 and end_index != -1:
                                # 이전 버전
                                calculated_crc = ky_util.generate_crc(received_packet,
                                                                      len(received_packet))  # crc 16 생성
                                received_crc = int.from_bytes(received_packet[-3:-1], byteorder='big')  # 전송받은 crc16 추출

                                # 검증 정상적으로 들어오는 데이터도 crc가 일치하지 않는다.
                                checkcrc = (calculated_crc == received_crc)

                                # cmd에 따른 구분
                                cmd = received_packet[1:3]
                                cmd = int.from_bytes(cmd, byteorder='big')

                                # if checkcrc:
                                length = received_packet[3:5]
                                length = int.from_bytes(length, byteorder='big')

                                data = received_packet[5:length + 5]

                                # logging.info(f"received_packet slice : {received_packet}")

                                if cmd == 1 and length == 183 and packet_len == 191:
                                    client_socket.send(ky_util.make_buff(cmd, 0))  # 전송 결과를 return하도록 되어있다.
                                    # client_socket.send(ky_util.make_buff(cmd, 0))  # 전송 결과를 return하도록 되어있다.
                                    logging.info(f"sno: {sno}, running cmd 1 in {client_address}")
                                    # logging.info(f"received_packet: {received_packet}")
                                    decoded_data = protocol.cmd_one(data)
                                    sno = decoded_data.get('ai_pems_info').get('device_serial_number') + str(
                                        decoded_data.get('ai_pems_info').get('device_type')) + str(
                                        decoded_data.get('ai_pems_info').get('device_sequence'))

                                    data_queue.put({sno: protocol.get_cmd_one_param(decoded_data)})



                                elif cmd == 2 and length == 43:  # 사용안함
                                    print(cmd)
                                    client_socket.send(ky_util.make_buff(cmd))

                                elif cmd == 3 and length == 35 and packet_len == 43:
                                    # client_socket.send(ky_util.make_buff(cmd, 0))
                                    # logging.info(f"running cmd 3 in {client_address}")
                                    decoded_data = protocol.cmd_three(data)

                                    sno = decoded_data[0].get('ai_pems_info').get('device_serial_number') + str(
                                        decoded_data[0].get('ai_pems_info').get('device_type')) + str(
                                        decoded_data[0].get('ai_pems_info').get('device_sequence'))

                                    for data in decoded_data:
                                        if len(data.get('arlam_info')) != 0:
                                            alarm_queue.put(protocol.get_cmd_three_param(data))

                    except KeyboardInterrupt:
                        logging.exception("Keyboard Interrupt")
                        # client_socket.close()
                        del_client_queue.put({sno: {"client_address": client_address,
                                                   "client_socket": client_socket}})
                        break
                    except TimeoutError as timeoute:
                        logging.exception(f"timeout Error: {timeoute}")
                        logging.exception(f"client_address, client_socket: {client_address}, {client_socket}")
                        del_client_queue.put({sno: {"client_address": client_address,
                                                   "client_socket": client_socket}})
                        break

                    except WindowsError as Win:
                        logging.exception(f"Win Error: {Win}")
                        logging.exception(
                            f"stop client.  client_address, client_socket: {client_address}, {client_socket}")
                        del_client_queue.put({sno: {"client_address": client_address,
                                                   "client_socket": client_socket}})
                        # del CLIENTS[sno]
                        break
                    except Exception as e:
                        logging.exception(f"tcp runrun{e}")
                        del_client_queue.put({sno: {"client_address": client_address,
                                                   "client_socket": client_socket}})
                        break

            else:
                time.sleep(1)
                pass

        except Exception as e:
            logging.exception(f"tcp_server Exception: {e}")

# if __name__ == '__main__':
#     runrun()
