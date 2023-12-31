# python = 3.10.4
from datetime import datetime
from TCP.TCP_Server import activate_server
from TCP.cmd_service import Cmd_Service
from TCP.TCP_Server import CLIENTS
from kafka_manager.kafka_manager import kafka_manager

import os
import sys
import logging
import yaml
import threading
import time

if __name__=="__main__":
    ### 정보 불러오기 ###
    root = 'C:/TCP'
    config_root = root + '/config.yml'
    with open(config_root, 'r', encoding='UTF-8') as config_file:
        config_data = yaml.load(config_file, Loader=yaml.FullLoader)
        set_location = config_data['profiles']['active']
        config_data = config_data[set_location]

    ### log작성 config설정 ###
    log_directory = os.path.join(root, 'log')
    if not os.path.exists(log_directory):  # log폴더가 없을경우 생성
        os.makedirs(log_directory)

    # #mac
    # log_directory= './'

    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d")
    logging.basicConfig(
        filename=f'{log_directory}/Interface__{formatted_time}.log',
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    ## tcp 서버 설정
    tcp_host = config_data['tcp']['ip']
    tcp_port = config_data['tcp']['port']

    # tcp_host = 'localhost'
    # tcp_port = 19100

    tcp_server = threading.Thread(target=activate_server, args=(tcp_host, tcp_port))
    tcp_server.daemon = True

    global IS_SEND_DATA

    try:
        tcp_server.start()
        service = kafka_manager()  # 서비스
        while True:
            now = datetime.now()
            closest_5_minute = (now.minute // 5) * 5
            target_minute = closest_5_minute if now.minute % 5 == 0 else closest_5_minute - 5
            # 현재 시간의 시, 분을 가져옵니다
            # current_hour = now.hour
            current_minute = now.minute

            if current_minute == target_minute:  # 5분일 경우 데이터 전송
                if IS_SEND_DATA and bool(CLIENTS):  # IS_SEND_DATA: 중복전송 방지, bool(CLIENTS): clients 존재유무
                    IS_SEND_DATA = False

                    for ip in CLIENTS:
                        data_master = CLIENTS[ip]['data']

                        all_data = data_master.get_all_data()
                        for data in all_data:
                            service.send_tcp_message(msg=data)
                        logging.info("Send Query")
                        data_master.clean()
            else:
                IS_SEND_DATA = True
                time.sleep(1)

    except KeyboardInterrupt:
        print("서버를 종료합니다.")
        logging.info("press Ctrl+c")
    except Exception as e:
        logging.warning(e)
    finally:
        SERVER_RUNNING = False
        # tcp_server.join() #데몬스레드 이므로 메인 스레드 종료시 모두 종료
        logging.info("Close Program")

#cmd에서 실행
## 서비스 등록
# sc create TCPIFTEST binPath= "C:\TCP\TCP_Server_main.exe"
## 서비스 제거
# sc delete TCPIFTEST

# C:\Users\zxckl\OneDrive\바탕 화면\work\개발\GetData_source\server\TCP\test\dist\tcpServer