import threading
import sys
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import yaml
from Listener import tcp_server
import time
from DB.db_handler import DatabaseHandler
from datetime import datetime


def get_script_directory():
    """
    파일실행위치 불러오기
    """
    # frozen: PyInstaller, cx_Freeze, etc.
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # script file
    script_path = os.path.realpath(sys.argv[0])
    return os.path.dirname(script_path)


def get_config_data():
    """
    config파일을 가져옵니다.
    """
    root = get_script_directory()
    config_root = root + '\config.yml'
    with open(config_root, 'r', encoding='UTF-8') as config_file:
        config_data = yaml.load(config_file, Loader=yaml.FullLoader)
        set_location = config_data['profiles']['active']
        config_data = config_data[set_location]

    return config_data


def set_logging_config():
    """
    log를 작성할 폴더와 파일명을 지정합니다.
    """
    root = get_script_directory()
    log_directory = os.path.join(root, 'log')

    if not os.path.exists(log_directory):  # log폴더가 없을경우 생성
        os.makedirs(log_directory)

    file_handler = TimedRotatingFileHandler(
        filename=f'{log_directory}/TCP_server.log',
        when='midnight',  # 매 자정마다
        # when='M',  # 매 분마다
        interval=1,  # 1일동안 생성된 로그 저장
        backupCount=30,  # 90일간 저장
        encoding='utf-8'
    )

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[file_handler]
    )


class KyInterface:
    def __init__(self):
        set_logging_config()  # log파일 위치
        config_data = get_config_data()  # config.yml 정보

        tcp_host = config_data['tcp']['ip']
        tcp_port = config_data['tcp']['port']
        self.tcp_thread = threading.Thread(target=tcp_server.runrun, args=(tcp_host, tcp_port))

        plant_target = config_data['tcp']['tcp_server_target']
        self.frequency_minute = config_data['tcp']['frequency_minute']
        self.db = DatabaseHandler(config_data['db'], plant_target)

        self.last_sent_time = None
        self.data_dict = dict()

    def can_i_send(self):

        current_time = time.time()
        current_minute = time.localtime(current_time).tm_min

        # 1. 1회만 전송
        """
        self.before_minute의 값을 update합니다.
        """
        if current_time != self.last_sent_time:
            self.last_sent_time = current_time
            is_before_send = True
        else:
            is_before_send = False

        # 2. 주기마다 전송
        if current_minute % self.frequency_minute == 0:
            is_it_time = True
        else:
            is_it_time = False

        # 3. 데이터 존재 유무 파악
        if len(self.data_dict) > 0:
            is_data = True
        else:
            is_data = False

        return is_it_time and is_before_send and is_data



def main():
    ky_interface = KyInterface()
    ky_interface.tcp_thread.daemon = True
    ky_interface.tcp_thread.start()

    while True:
        try:

            # tcp서버에서 알람데이터를 받을경우 즉시 전송합니다.
            while not tcp_server.alarm_queue.empty():
                alarm = tcp_server.alarm_queue.get()
                ky_interface.db.insert_list_data(alarm)  # 체크

            # tcp서버에 전송할 데이터 생성될 경우 최신 데이터로 update합니다.
            while not tcp_server.data_queue.empty():
                tcp_data = tcp_server.data_queue.get()
                if len(tcp_data) > 0:
                    for key, value in tcp_data.items():
                        ky_interface.data_dict.update(tcp_data)

            # config.yml에 설정한 주기마다 update되어있는 데이터를 전송합니다.
            if ky_interface.can_i_send():
                for sno in list(ky_interface.data_dict):  # list()를 사용하여 사본을 만들어 순회
                    ky_interface.db.insert_list_data(ky_interface.data_dict.pop(sno))  # data_dict에서 데이터 추출 및 삭제
            time.sleep(1)

        except Exception as e:
            logging.error(f"main e : {e}")


if __name__ == '__main__':
    main()
