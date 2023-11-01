import logging
from datetime import datetime
from sqlalchemy import text
from TCP.TCP_Server import CLIENTS
from kafka_manager.kafka_manager import kafka_manager
from DB.DataBaseManager import DatabaseManager
import json


class Cmd_Service:
    def __init__(self):
        self.conn = DatabaseManager
        self.kfk = kafka_manager()

    def send_message(self, client_data):
        self.kfk.send_tcp_message(client_data)

    def send_query(self):
        global IS_SEND_DATA
        #### 각 쓰레드로부터 쌓인 address별 CLIENTS에 담긴 data들을 5분마다 한번씩 Data 전송 ###
        now = datetime.now()
        closest_5_minute = (now.minute // 5) * 5
        target_minute = closest_5_minute if now.minute % 5 == 0 else closest_5_minute - 5
        # 현재 시간의 시, 분을 가져옵니다
        # current_hour = now.hour
        current_minute = now.minute

        if current_minute == target_minute:
            if IS_SEND_DATA:
                for ip in CLIENTS:
                    data_master = CLIENTS[ip]['data']
                    all_data = data_master.get_all_data()
                    for i in all_data:
                        self.cmd_one_procedure(i)
                        IS_SEND_DATA = False
                        # print(i)
                    logging.info("Send Query")
                    data_master.clean()
        else:
            IS_SEND_DATA = True

    def cmd_one_procedure(self, data):
        """
        MMMT_EQUIP_SERIAL_INSERT
        @EQUIP_ID       int,
        @EQUIP_TYPE     varchar(64),
        @PLANT_CD       varchar(100),
        @INSTANTANEOUS  float,
        @ACCUMULATE     float,
        @POWERFACT      float,
        @CLIENTIP       varchar(20)
        """
        query = "EXEC MMMT_EQUIP_SERIAL_INSERT :EQUIP_ID, :EQUIP_TYPE, :PLANT_CD, :INSTANTANEOUS, :ACCUMULATE, :POWERFACT, :CLIENTIP"
        params = {
            "EQUIP_ID": data[0],
            "EQUIP_TYPE": data[1],
            "PLANT_CD": data[2],
            "INSTANTANEOUS": data[3],
            "ACCUMULATE": data[4],
            "POWERFACT": data[5],
            "CLIENTIP": data[6]
        }
        stmt = text(query).bindparams(**params)
        self.conn.execute(stmt)
        self.conn.commit()

    def cmd_two_procedure(self, *args):
        """
        MMMT_EQUIP_STATUS_INSERT
        @EQUIP_ID   int,
        @PLANT_CD   varchar(100),
        @USE_YN varchar(6),
        @CONNECT_STATUS varchar(6),
        @CLIENTIP   varchar(20)
        """
        query = "EXEC MMMT_EQUIP_STATUS_INSERT :EQUIP_ID, :PLANT_CD, :USE_YN, :CONNECT_STATUS, :CLIENTIP"
        params = {
            "EQUIP_ID": args[0],
            "PLANT_CD": args[1],
            "USE_YN": args[2],
            "CONNECT_STATUS": args[3],
            "CLIENTIP": args[4]
        }

        stmt = text(query).bindparams(**params)
        self.conn.execute(stmt)
        self.conn.commit()
