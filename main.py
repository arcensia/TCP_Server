# python = 3.10.4
from DB.DataBaseManager import DatabaseManager
from kafka_manager.kafka_manager import kafka_manager
from datetime import datetime
from TCP.TCP_Server import activate_server

import os
import sys
import logging
import yaml

### DB연결 정보 불러오기 ###
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

# # DB연결
# db = DatabaseManager(config_data['db'])
# db.open_session()

activate_server(tcp_host=tcp_host, tcp_port=tcp_port)

# try:
#     # TCP서버 실행
#     activate_server(tcp_host=tcp_host, tcp_port=tcp_port)
# except Exception as e:
#     logging.warning(e)
# finally:
#     SERVER_RUNNING = False

# db.close_session()
logging.info("Close Program")
sys.exit(0)

# sc create TCPIFTEST binPath= "D:\tcp server\dist\tcpServer.exe"
# C:\Users\zxckl\OneDrive\바탕 화면\work\개발\GetData_source\server\TCP\test\dist\tcpServer