import sys, os, time
import logging
from logging.handlers import TimedRotatingFileHandler
import yaml
from datetime import datetime
from TCP.tcp_server_handler import make_tcp_server
from DB.db_handler import database_handler


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
        when='midnight', # 매 자정마다
        # when='M',  # 매 분마다
        interval=1,  # 1일동안 생성된 로그 저장
        backupCount=90,  # 90일간 저장
        encoding='utf-8'
    )

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[file_handler]
    )


class Equipment_Interface_Service:
    """
    1. logging할 위치와 tcp서버 정보를 설정합니다.
    2. tcp 서버를 open합니다.
    3. 데이터베이스와 연결합니다.
    """

    def __init__(self) -> None:
        set_logging_config()  # log파일 위치

        self.config_data = get_config_data()  # config.yml 정보

        tcp_host = self.config_data['tcp']['ip']
        tcp_port = self.config_data['tcp']['port']
        plant_target = self.config_data['tcp']['tcp_server_target']  # tcp서버를 구동시킬 타입 구분
        database_config = self.config_data['db']

        self.tcp_server = make_tcp_server(tcp_host, tcp_port, plant_target=plant_target)
        self.db = database_handler(config=database_config, plant_target=plant_target)
        self.is_send = False
        self.before_minute = None

    def can_i_send_data(self):
        """
        3가지 체크 사항을 점검합니다.
        1. 클라이언트 데이터 존재여부
        2. frequency_minute 주기 일치 여부 (config.yml에서 설정만 주기)
        3. 같은 시간에 1회만 전송
        """
        try:
            # 1.클라이언트 존재여부
            clients = self.tcp_server.get_clients_data()
            is_clients = bool(clients)

            # 2. frequency_minute 주기 일치 여부
            frequency = self.config_data['tcp']['frequency_minute']
            now = datetime.now()
            current_minute = now.minute
            # 00분부터 60분까지 yml에서 설정한 주기로 시간을 체크합니다.
            closest_frequency_minute = (now.minute // frequency) * frequency
            target_minute = closest_frequency_minute if now.minute % frequency == 0 else closest_frequency_minute - frequency


            if frequency == 1:
                self.before_minute = current_minute
                is_it_time = True
            else:
                if target_minute == current_minute:
                    is_it_time = True
                else:
                    is_it_time = False

            # 3.같은 시간에 1회만 전송
            """
            self.before_minute의 값을 update합니다.
            """
            if self.before_minute != current_minute:
                self.before_minute = current_minute
                is_before_send = True
            else:
                is_before_send = False


            # 최종 return값
            if is_clients and is_it_time and is_before_send:
                self.is_send = True
            else:
                self.is_send = False
            return self.is_send

        except Exception as e:
            logging.error(e)
            print(e)

    def send_data(self):
        try: 
            clients = self.tcp_server.get_clients_data()
            for ip in clients:
                data_master = clients[ip]['data']
                all_data = data_master.get_all_data()
                # print(all_data)
                self.db.insert_list_data(all_data)
                # data_master.clean()
        except Exception as e:
            logging.error(e)
            print(e)

def main():
    """
    .yml에 설정된 주기마다 데이터를 전송합니다.
    """

    try:    
        interface = Equipment_Interface_Service()
        interface.tcp_server.make_tcp_server_thread()
        interface.tcp_server.start_server()
        while True:
            if interface.can_i_send_data():
                interface.send_data()
                pass
            else:
                time.sleep(1)


    except Exception as e:
        logging.warning(e)
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
