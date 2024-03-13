import struct
from datetime import datetime

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
        datas = []
        datas.extend(self.electricity_data)
        datas.extend(self.flow_data)
        datas.extend(self.pressure_Data)

        data_recode = []

        for data in datas:
            if len(data) == 8:
                equip_id, equip_type, plant_cd, instantaneous, accumulate, power_fact, client_ip, rdate = data
                data_recode.append({
                    'PLANT_CD': plant_cd,
                    'EQUIP_ID': equip_id,
                    'EQUIP_TYPE': equip_type,
                    'INSTANTANEOUS': instantaneous,
                    'ACCUMULATE': accumulate,
                    'POWERFACT': power_fact,
                    'CLIENT_IP': client_ip,
                    'RDATE': rdate
                })

        return data_recode


    def clean(self):
        self.electricity_data = []
        self.flow_data = []
        self.pressure_Data = []


### 시리얼 통신 디코딩 ###
def get_str_datetime():
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return formatted_time


def cmd_one(data, client_ip):
    offset = 0
    plant_cd = 1

    electricity_data = []
    flow_data = []
    pressure_Data = []

    while len(data) == 650 and offset < len(data):
        # 전력
        offset_length = 13
        for i in range(0, 20, 1):
            chunk = data[offset:offset + offset_length]
            energy_id = int.from_bytes(chunk[:1], byteorder='big')
            active_energy = struct.unpack('!f', chunk[1:5])[0]  # struct.unpack() == 바이너리 데이터 to float
            active_power = struct.unpack('!f', chunk[5:9])[0]
            power_factor = struct.unpack('!f', chunk[9:len(chunk)])[0]

            electricity_data.append([energy_id, "E", plant_cd, active_energy, active_power, power_factor, client_ip,
                                     get_str_datetime()])

            offset += offset_length

        # 유량
        offset_length = 9
        for i in range(0, 10, 1):
            chunk = data[offset:offset + offset_length]
            energy_id = int.from_bytes(chunk[:1], byteorder='big')
            EFlowRate = struct.unpack('!f', chunk[1:5])[0]
            EFlow = struct.unpack('!f', chunk[5:9])[0]
            flow_data.append([energy_id, "F", plant_cd, EFlowRate, EFlow, 0, client_ip, get_str_datetime()])
            offset += offset_length

        # 유압
        offset_length = 5
        for i in range(0, 60, 1):
            chunk = data[offset:offset + offset_length]
            energy_id = int.from_bytes(chunk[:1], byteorder='big')
            EPressure = struct.unpack('!f', chunk[1:5])[0]
            pressure_Data.append([energy_id, "P", plant_cd, EPressure, EPressure, 0, client_ip, get_str_datetime()])
            offset += offset_length

    return electricity_data, flow_data, pressure_Data


# 0을 False로, 1을 True로 변환
def isValue(value):
    isValue = False
    if value == 0 or value == 1:
        isValue = True if value == 1 else False
    return isValue


def cmd_two(data):
    offset = 0
    plant_cd = 1
    is_use_board = []
    if len(data) == 24:
        offset_length = 2
        for i in range(0, 2):
            chunk = data[offset:offset + offset_length]

            id = i + 1
            use_able = isValue(chunk[0])
            connect_state = isValue(chunk[1])
            is_use_board.append(["gethering_board", id, use_able, connect_state])
            offset += offset_length

        for i in range(0, 10):
            chunk = data[offset:offset + offset_length]

            id = i + 1
            use_able = isValue(chunk[0])
            connect_state = isValue(chunk[1])
            is_use_board.append(["pems_pro", id, use_able, connect_state])

            offset += offset_length

    return is_use_board
