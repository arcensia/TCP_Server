import struct
from datetime import datetime
import logging

"""
protocol 목적
1. 수신된 값 0x7F~0x7E까지 분리
2. cmd에 따른 필요한 데이터 분리
3. 오류발생시 이벤트 발생.
"""


class Data:
    def __init__(self) -> None:
        self.cmd_one = dict()
        self.cmd_two = dict()
        self.cmd_three = dict()

    def set_cmd_one(self, data):
        self.cmd_one.update(data)

    def set_cmd_two(self, data):
        self.cmd_two = data

    def set_cmd_three(self, data):
        self.cmd_three = data

    def get_cmd_three(self):
        return {'cmd_three': self.cmd_three}

    def get_cmd_data(self):
        send_data = list()
        if self.cmd_one:
            send_data.append({'cmd1': self.cmd_one})
        if self.cmd_two:
            send_data.append({'cmd2': self.cmd_two})
        if self.cmd_three:
            send_data.append({'cmd3': self.cmd_three})
        return send_data

    def clean(self):
        self.cmd_one = dict()
        self.cmd_two = dict()
        self.cmd_three = dict()


### 시리얼 통신 디코딩 ###
def decode_extract_datetime_from_data(data):
    """
    byteorder가 big Endian인 데이터를 년월일시분초 값로 분리한다.

    Parameters:
        data(byte): 시간이데이터가 합쳐져있는 byte
    Returns:
        dict: {year, month, day, hour, minute, second}
    """
    time_info = dict()
    time_info.update({"year": int.from_bytes(data[:2], byteorder='big'),
                      "month": int.from_bytes(data[2:3], byteorder='big'),
                      "day": int.from_bytes(data[3:4], byteorder='big'),
                      "hour": int.from_bytes(data[4:5], byteorder='big'),
                      "minute": int.from_bytes(data[5:6], byteorder='big'),
                      "second": int.from_bytes(data[6:7], byteorder='big')})
    return time_info


def decode_ai_PEMS_info(data):
    """
    받은 AI PEMS값을 분리한다.
    Parameters:
        data(byte): AI PEMS 구간 byte
    Returns:
        dict: {device_serial_number, device_type, device_sequence}
    """
    device_serial_number = ""
    for byte in data[:10]:
        device_serial_number += str(int(byte))

    ai_pems_info = {"device_serial_number": device_serial_number,
                    "device_type": int.from_bytes(data[10:11], byteorder='big'),
                    "device_sequence": int.from_bytes(data[11:12], byteorder='big')}
    return ai_pems_info


def decode_data_splite_day_f(data):
    """
    받은 accumulated_data을 일~토, 월, 년 에 대한값으로 분리한다.
    Parameters:
        data(byte): accumulated_data구간 byte
    Returns:
        dict: {device_serial_number, device_type, device_sequence}
    """
    accumulated_energy_data = {
        "sunday_energy": struct.unpack('>f', data[:4])[0],
        "monday_energy": struct.unpack('>f', data[4:8])[0],
        "tuesday_energy": struct.unpack('>f', data[8:12])[0],
        "wednesday_energy": struct.unpack('>f', data[12:16])[0],
        "thursday_energy": struct.unpack('>f', data[16:20])[0],
        "friday_energy": struct.unpack('>f', data[20:24])[0],
        "saturday_energy": struct.unpack('>f', data[24:28])[0],
        "monthly_energy": struct.unpack('>f', data[28:32])[0],
        "yearly_energy": struct.unpack('>f', data[32:36])[0]
    }
    return accumulated_energy_data


def decode_data_splite_day(data):
    """
    받은 accumulated_data을 일~토, 월, 년 에 대한값으로 분리한다.
    Parameters:
        data(byte): accumulated_data구간 byte
    Returns:
        dict: {device_serial_number, device_type, device_sequence}
    """
    accumulated_energy_data = {
        "sunday_energy": struct.unpack('>I', data[:4])[0],
        "monday_energy": struct.unpack('>I', data[4:8])[0],
        "tuesday_energy": struct.unpack('>I', data[8:12])[0],
        "wednesday_energy": struct.unpack('>I', data[12:16])[0],
        "thursday_energy": struct.unpack('>I', data[16:20])[0],
        "friday_energy": struct.unpack('>I', data[20:24])[0],
        "saturday_energy": struct.unpack('>I', data[24:28])[0],
        "monthly_energy": struct.unpack('>I', data[28:32])[0],
        "yearly_energy": struct.unpack('>I', data[32:36])[0]
    }
    return accumulated_energy_data


def cmd_one(data):
    """
    데이터 전송용 프로토콜
    data 총 byte 183
    from_data_time_info: 시간데이터(7) data[0:7]
    ai_pems_info: AI PEMS정보 (12) data[7:19]
    ai_pems_data: AI PEMS 데이터 (20) data[19:39]
    power_meter_data: 전력계 데이터 (20) data[39:59]
    accumulated_energy_data: 누적 전력량 데이터 (36) data[59:95]
    flow_meter_data: 유량계 데이터 (12) data[95:107]
    accumulated_flow_data: 누적 유량 데이터(36) data[107:143]
    operating_time_data: 가동 시간 데이터(36) data[143:179]
    humidity_sensor_data: 습도계 데이터 (4) data[179:183]

    서버 Response Body - Length 1 byte
    0: 운전, 1: 전송중 오류
    """
    from_data_time_info_low_data = data[:7]
    ai_pems_info_low_data = data[7:19]
    ai_pems_data_low_data = data[19:39]
    power_meter_data_low_data = data[39:59]
    accumulated_energy_data_low_data = data[59:95]
    flow_meter_data_low_data = data[95:107]
    accumulated_flow_data_low_data = data[107:143]
    operating_time_data_low_data = data[143:179]
    humidity_sensor_data_low_data = data[179:183]

    # if len(from_data_time_info_low_data) == 7 and \
    #         len(ai_pems_info_low_data) == 12 and \
    #         len(ai_pems_data_low_data) == 20 and \
    #         len(power_meter_data_low_data) == 20 and \
    #         len(accumulated_energy_data_low_data) == 36 and \
    #         len(flow_meter_data_low_data) == 12 and \
    #         len(accumulated_flow_data_low_data) == 36 and \
    #         len(operating_time_data_low_data) == 36 and \
    #         len(humidity_sensor_data_low_data) == 4:
    #     pass

    try:
        from_data_time_info = decode_extract_datetime_from_data(from_data_time_info_low_data)
        ai_pems_info = decode_ai_PEMS_info(ai_pems_info_low_data)
        ai_pems_data = {
            "pressure": struct.unpack('>H', ai_pems_data_low_data[:2])[0],
            "temperature": struct.unpack('>H', ai_pems_data_low_data[2:4])[0],
            "hz": struct.unpack('>H', ai_pems_data_low_data[4:6])[0],
            "consumable_setup_time": struct.unpack('>H', ai_pems_data_low_data[6:8])[0],
            "consumable_usage_time": struct.unpack('>H', ai_pems_data_low_data[8:10])[0],
            "motor_grease_setup_time": struct.unpack('>H', ai_pems_data_low_data[10:12])[0],
            "motor_grease_time": struct.unpack('>H', ai_pems_data_low_data[12:14])[0],
            # "pressure": int.from_bytes(ai_pems_data_low_data[:2], byteorder='big') / 10.0,
            # "temperature": int.from_bytes(ai_pems_data_low_data[2:4], byteorder='big'),
            # "hz": int.from_bytes(ai_pems_data_low_data[4:6], byteorder='big'),  # rpm
            # "consumable_setup_time": int.from_bytes(ai_pems_data_low_data[6:8], byteorder='big'),
            # "consumable_usage_time": int.from_bytes(ai_pems_data_low_data[8:10], byteorder='big'),
            # "motor_grease_setup_time": int.from_bytes(ai_pems_data_low_data[10:12], byteorder='big'),
            # "motor_grease_time": int.from_bytes(ai_pems_data_low_data[12:14], byteorder='big'),

            "vsd_fsd": 1 if ai_pems_data_low_data[14] else 0,
            # "vsd_fsd": "VSD" if ai_pems_data_low_data[14] else "FSD",

            "operation_status": "운전" if ai_pems_data_low_data[15] else "정지",

            "total_operation_time": struct.unpack('>I', ai_pems_data_low_data[16:])[0],
            # "total_operation_time": int.from_bytes(ai_pems_data_low_data[16:], byteorder='big'),
        }
        power_meter_data = {
            "average_voltage": struct.unpack('>f', power_meter_data_low_data[:4])[0],
            "average_current": struct.unpack('>f', power_meter_data_low_data[4:8])[0],
            "instantaneous_power": struct.unpack('>f', power_meter_data_low_data[8:12])[0],
            "accumulated_energy": struct.unpack('>f', power_meter_data_low_data[12:16])[0],
            "power_factor": struct.unpack('>f', power_meter_data_low_data[16:20])[0]
        }

        accumulated_energy_data = decode_data_splite_day_f(accumulated_energy_data_low_data)

        flow_meter_data = {
            "pressure": struct.unpack('>H', flow_meter_data_low_data[:2])[0] / 10.0,
            # 압력이 x10된 값이라, 나누어주어야함. 프로토콜 excel 참고
            "temperature": struct.unpack('>H', flow_meter_data_low_data[2:4])[0],  # 체크 값이다름
            # "pressure": int.from_bytes(flow_meter_data_low_data[:2], byteorder='big') / 10.0,
            # "temperature": int.from_bytes(flow_meter_data_low_data[2:4], byteorder='big'),

            "instantaneous_flow": struct.unpack('>f', flow_meter_data_low_data[4:8])[0],
            "accumulated_flow": struct.unpack('>f', flow_meter_data_low_data[8:12])[0]
        }
        accumulated_flow_data = decode_data_splite_day_f(accumulated_flow_data_low_data)
        operating_time_data = decode_data_splite_day(operating_time_data_low_data)

        humidity_sensor_data = {
            "humidity": int.from_bytes(humidity_sensor_data_low_data[:2], byteorder='big') / 10.0,  # 프로토콜 참고
            "temperature": int.from_bytes(humidity_sensor_data_low_data[2:], byteorder='big')
        }

        decoded_packet = {"from_data_time_info": from_data_time_info,
                          "ai_pems_info": ai_pems_info,
                          "ai_pems_data": ai_pems_data,
                          "power_meter_data": power_meter_data,
                          "accumulated_energy_data": accumulated_energy_data,
                          "flow_meter_data": flow_meter_data,
                          "accumulated_flow_data": accumulated_flow_data,
                          "operating_time_data": operating_time_data,
                          "humidity_sensor_data": humidity_sensor_data
                          }
    except Exception as ex:
        return ex
    return decoded_packet


def get_cmd_one_param(cmd_one):
    params = {
        'cmd_one': dict(),
        'cmd_two': dict(),
        'cmd_three': dict()
    }
    if bool(cmd_one) and len(cmd_one) > 0:
        reg_date_info = cmd_one.get('from_data_time_info')
        ai_pems_info = cmd_one.get('ai_pems_info')
        ai_pems_data = cmd_one.get('ai_pems_data')
        power_meter_data = cmd_one.get('power_meter_data')
        accumulated_energy_data = cmd_one.get('accumulated_energy_data')
        flow_meter_data = cmd_one.get('flow_meter_data')
        accumulated_flow_data = cmd_one.get('accumulated_flow_data')
        operating_time_data = cmd_one.get('operating_time_data')
        humidity_sensor_data = cmd_one.get('humidity_sensor_data')

        # Construct datetime object from received information
        reg_date = datetime(reg_date_info['year'], reg_date_info['month'], reg_date_info['day'],
                            reg_date_info['hour'], reg_date_info['minute'], reg_date_info['second'])
        reg_date = reg_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        params['cmd_one'] = {
            "reg_date": reg_date,
            "equip_sno": str(ai_pems_info['device_serial_number']),
            "equip_type": str(ai_pems_info['device_type']),
            "equip_no": str(ai_pems_info['device_sequence']),
            "pressure": float(ai_pems_data['pressure']),  # 압력이 x10된 값, 프로시저에서 나누어줌
            "temperature": float(ai_pems_data['temperature']),
            "hz": float(ai_pems_data.get('hz', 0)) / 100,  # 체크
            "setting_time": int(ai_pems_data.get('consumable_setup_time', 0)),
            "use_time": int(ai_pems_data.get('consumable_usage_time', 0)),
            "grease_setting_time": int(ai_pems_data.get('motor_grease_setup_time', 0)),
            "grease_use_time": int(ai_pems_data.get('motor_grease_time', 0)),
            "vsd_fsd": int(ai_pems_data.get('vsd_fsd', 0)),  # 0: 정지, 1: 운전
            "driving_stop": int(ai_pems_data.get('operation_status', '') == '운전'),
            # Assuming '운전' means '운전' and everything else is '정지'
            "total_driving": ai_pems_data.get('total_operation_time', 0),
            "average_voltage": power_meter_data.get('average_voltage', 0),
            "average_watt": power_meter_data.get('average_current', 0),
            "instantaneous_e": power_meter_data.get('instantaneous_power', 0),  # 체크
            "accumulate_e": power_meter_data.get('accumulated_energy', 0),
            "power_factor": power_meter_data.get('power_factor', 0),
            "sun_current_e": accumulated_energy_data.get('sunday_energy', 0),
            "mon_current_e": accumulated_energy_data.get('monday_energy', 0),
            "tue_current_e": accumulated_energy_data.get('tuesday_energy', 0),
            "wed_current_e": accumulated_energy_data.get('wednesday_energy', 0),
            "thu_current_e": accumulated_energy_data.get('thursday_energy', 0),
            "fri_current_e": accumulated_energy_data.get('friday_energy', 0),
            "sat_current_e": accumulated_energy_data.get('saturday_energy', 0),
            "month_current_e": accumulated_energy_data.get('monthly_energy', 0),
            "year_current_e": accumulated_energy_data.get('yearly_energy', 0),

            # C#에서 아래 4개는 insert시 int로 변환해서 전송. 프로토콜은 float형태가 올바름.
            "press_f": int(flow_meter_data.get('pressure', 0)),  # 체크 # 압력이 x10된 값이라, 나누어주어야함. 프로토콜 excel 참고
            "temperature_f": int(flow_meter_data.get('temperature', 0)),  # 0인데 20,21
            "instantaneous_f": int(flow_meter_data.get('instantaneous_flow', 0)),
            "accumulate_f": int(flow_meter_data.get('accumulated_flow', 0)),

            "sun_current_f": accumulated_flow_data.get('sunday_energy', 0),
            "mon_current_f": accumulated_flow_data.get('monday_energy', 0),
            "tue_current_f": accumulated_flow_data.get('tuesday_energy', 0),
            "wed_current_f": accumulated_flow_data.get('wednesday_energy', 0),
            "thu_current_f": accumulated_flow_data.get('thursday_energy', 0),
            "fri_current_f": accumulated_flow_data.get('friday_energy', 0),
            "sat_current_f": accumulated_flow_data.get('saturday_energy', 0),
            "month_current_f": accumulated_flow_data.get('monthly_energy', 0),
            "year_current_f": accumulated_flow_data.get('yearly_energy', 0),
            "sun_operationtime": int(operating_time_data.get('sunday_energy', 0)),
            "mon_operationtime": int(operating_time_data.get('monday_energy', 0)),
            "tue_operationtime": int(operating_time_data.get('tuesday_energy', 0)),
            "wed_operationtime": int(operating_time_data.get('wednesday_energy', 0)),
            "thu_operationtime": int(operating_time_data.get('thursday_energy', 0)),
            "fri_operationtime": int(operating_time_data.get('friday_energy', 0)),
            "sat_operationtime": int(operating_time_data.get('saturday_energy', 0)),
            "month_operationtime": int(operating_time_data.get('monthly_energy', 0)),
            "year_operationtime": int(operating_time_data.get('yearly_energy', 0)),
            "humidity": humidity_sensor_data.get('humidity', 0),
            "temperature_h": humidity_sensor_data.get('temperature', 0)
        }

    return params


def cmd_twe(data):
    """
    시간 동기화용 프로토콜

    data: 19byte
    from_data_time_info: 시간데이터(7) data[0:7]
    ai_pems_info: AI PEMS정보 (12) data[7:19]

    # 서버ResponseBody - Length 7 byte
    년	월	일	시간	분	초
    2 byte (uint16)	1 byte	1 byte	1 byte	1 byte	1 byte
    """
    try:
        from_data_time_info = decode_extract_datetime_from_data(data[:7])
        ai_pems_info = decode_ai_PEMS_info(data[7:19])
    except Exception as ex:
        return ex
    return from_data_time_info, ai_pems_info


def cmd_three(data):
    # logging.info("running cmd 3")
    """
    고장, 경보 정보 전송용 cmd
    data 총 byte 35
    from_data_time_info: 시간데이터(7) data[0:7]
    ai_pems_info: AI:PEMS정보 (12) data[7:19]
    error_fault_msg: 고장 정보 (8) data[19:27]
    error_maintenance_msg: 경보 정보 (8) data[27:35]


    서버 Response Body - Length 1 byte
    0: 운전, 1: 전송중 오류
    """
    # fault_list = [
    #     {
    #         1: "미확인 고장",
    #         2: "비상 정지",
    #         4: "EXT 1 통신 불량",
    #         8: "EXT 2 통신 불량",
    #         16: "EXT 1 이상",
    #         32: "EXT 2 이상",
    #         64: "인버터 통신 불량",
    #         128: "인버터 이상"
    #         ##
    #     },
    #     {
    #         1: "메인 모터 과전류",
    #         2: "팬 모터 과전류",
    #         4: "메인 모터 역상",
    #         8: "냉각수 부족",
    #         16: "메인 모터 쿨링팬 이상",
    #         32: "온도센서 단선[T1]",
    #         34: "온도센서 단선[T2]",
    #         128: "미확인 고장",
    #     },
    #     {
    #         1: "미확인 고장",
    #         2: "온도센서 단선[T5]",
    #         4: "압력센서 단선[P1]",
    #         8: "압력센서 단선[P2]",
    #         16: "압력센서 단선[P3]",
    #         32: "오일 펌프 과전류",
    #         64: "토출 공기 온도 상승 / 2단 토출 공기 온도 상승",
    #         128: "오일 온도 상승",
    #     },
    #     {
    #         1: "1단 토출 공기 온도 상승",
    #         2: "에어 압력 상승 / 2단 토출 압력 상승",
    #         4: "1단 토출 압력 상승",
    #         8: "오일 압력 상승",
    #         16: "오일 압력 저하",
    #         32: "순간 정전",
    #         64: "기동반 이상",
    #         128: "압축기 모델 점검",
    #     },
    #     {
    #         1: "무부하 운전 과다 이상",
    #         2: "인버터 4 ~ 20 mA 불량 F",
    #         4: "인버터 4 ~ 20 mA 불량 L",
    #         8: "DAC 통신 불량",
    #         16: "인버터 이상 [저전압]"
    #     }
    # ]

    fault_dict = {
        0x0000000000000001: "미확인 고장",
        0x0000000000000002: "비상 정지",
        0x0000000000000004: "EXT 1 통신 불량",
        0x0000000000000008: "EXT 2 통신 불량",
        0x0000000000000010: "EXT 1 이상",
        0x0000000000000020: "EXT 2 이상",
        0x0000000000000040: "인버터 통신 불량",
        0x0000000000000080: "인버터 이상",

        0x0000000000000100: "메인 모터 과전류",
        0x0000000000000200: "팬 모터 과전류",
        0x0000000000000400: "메인 모터 역상",
        0x0000000000000800: "냉각수 부족",
        0x0000000000001000: "메인 모터 쿨링팬 이상",
        0x0000000000002000: "온도센서 단선[T1]",
        0x0000000000004000: "온도센서 단선[T2]",
        0x0000000000008000: "미확인 고장",

        0x0000000000010000: "미확인 고장",
        0x0000000000020000: "온도센서 단선[T5]",
        0x0000000000040000: "압력센서 단선[P1]",
        0x0000000000080000: "압력센서 단선[P2]",
        0x0000000000100000: "압력센서 단선[P3]",
        0x0000000000200000: "오일 펌프 과전류",
        0x0000000000400000: "토출 공기 온도 상승 / 2단 토출 공기 온도 상승",
        0x0000000000800000: "오일 온도 상승",

        0x0000000001000000: "1단 토출 공기 온도 상승",
        0x0000000002000000: "에어 압력 상승 / 2단 토출 압력 상승",
        0x0000000004000000: "1단 토출 압력 상승",
        0x0000000008000000: "오일 압력 상승",
        0x0000000010000000: "오일 압력 저하",
        0x0000000020000000: "순간 정전",
        0x0000000040000000: "기동반 이상",
        0x0000000080000000: "압축기 모델 점검",

        0x0000000100000000: "무부하 운전 과다 이상",
        0x0000000200000000: "인버터 4 ~ 20 mA 불량 F",
        0x0000000400000000: "인버터 4 ~ 20 mA 불량 L",
        0x0000000800000000: "DAC 통신 불량",
        0x0000001000000000: "인버터 이상 [저전압]"
    }
    maintenance_dict = ({
        0x0000000000000001: "토출 공기 온도 점검 / 2단 토출 공기 온도 점검",
        0x0000000000000002: "1단 토출 공기 온도 점검",
        0x0000000000000004: "에어 압력 점검 / 2단 토출 압력 점검",
        0x0000000000000008: "1단 토출 공기 압력 저하",
        0x0000000000000010: "오일 필터 점검",
        0x0000000000000020: "세퍼레이터 점검",
        0x0000000000000040: "에어 필터 점검",
        0x0000000000000080: "모터 구리스 주입",
        0x0000000000000100: "자동 드레인 벨브 점검",
        0x0000000000000200: "소모품 교체",
        0x0000000000000400: "전력계 통신 불량",
        0x0000000000000800: "모터 구리스 보충",
        0x0000000000001000: "SLAVE 1 번 통신불량",
        0x0000000000002000: "SLAVE 2 번 통신불량",
        0x0000000000004000: "SLAVE 3 번 통신불량",
        0x0000000000008000: "SLAVE 4 번 통신불량",
        0x0000000000010000: "SLAVE 5 번 통신불량",
        0x0000000000020000: "SLAVE 6 번 통신불량",
        0x0000000000040000: "SLAVE 7 번 통신불량",
        0x0000000000080000: "SLAVE 8 번 통신불량",
        0x0000000000100000: "SLAVE 9 번 통신불량",
        0x0000000000200000: "MASTER 통신불량",
        0x0000000000400000: "Modbus 시작",
        0x0000000000800000: "Modbus 정지",
        0x0000000001000000: "SD 카드 불량",
        0x0000000002000000: "유량계 통신 불량",
        0x0000000004000000: "습도계 통신 불량"
    })
    #
    # maintenance_list = [{
    #     0x0000000000000001: "토출 공기 온도 점검 / 2단 토출 공기 온도 점검",
    #     0x0000000000000002: "1단 토출 공기 온도 점검",
    #     0x0000000000000004: "에어 압력 점검 / 2단 토출 압력 점검",
    #     0x0000000000000008: "1단 토출 공기 압력 저하"
    # }, {
    #     1: "오일 필터 점검",
    #     2: "세퍼레이터 점검",
    #     4: "에어 필터 점검",
    #     8: "모터 구리스 주입"
    # }, {
    #     1: "자동 드레인 벨브 점검",
    #     2: "소모품 교체",
    #     4: "전력계 통신 불량",
    #     8: "모터 구리스 보충"
    # }, {
    #     1: "SLAVE 1 번 통신불량",
    #     2: "SLAVE 2 번 통신불량",
    #     4: "SLAVE 3 번 통신불량",
    #     8: "SLAVE 4 번 통신불량",
    # }, {
    #     1: "SLAVE 5 번 통신불량",
    #     2: "SLAVE 6 번 통신불량",
    #     4: "SLAVE 7 번 통신불량",
    #     8: "SLAVE 8 번 통신불량"},
    #     {
    #         1: "SLAVE 9 번 통신불량",
    #         2: "MASTER 통신불량",
    #         4: "Modbus 시작",
    #         8: "Modbus 정지",
    #     }, {
    #         1: "SD 카드 불량",
    #         2: "유량계 통신 불량",
    #         4: "습도계 통신 불량"
    #     }]

    info_type = list()
    arlam_info = list()
    try:
        from_data_time_info = decode_extract_datetime_from_data(data[:7])
        ai_pems_info = decode_ai_PEMS_info(data[7:19])
        fault_data = data[19:27]
        fault_data = int.from_bytes(fault_data, byteorder='big')
        maintenance_data = data[27:35]
        maintenance_data = int.from_bytes(maintenance_data, byteorder='big')

        # logging.debug(f"from_data_time_info: {fault_data}")
        # logging.debug(f"maintenance_data: {maintenance_data}")

        if fault_data != 0:
            target_binary = bin(fault_data)[2:].zfill(64)  # 64비트
            formatted_target_hex = '0x' + ''.join(f'{int(target_binary[i:i + 8], 2):02X}' for i in range(0, 64, 8))
            # logging.info(f"Hexadecimal representation of target_value: {formatted_target_hex}")

            for key, description in fault_dict.items():
                key_binary = bin(key)[2:].zfill(64)  # 64비트
                matching_bits = [i for i, (bit_target, bit_key) in enumerate(zip(target_binary, key_binary)) if
                                 bit_target == '1' == bit_key]

                if matching_bits:
                    formatted_key_hex = '0x' + ''.join(f'{int(key_binary[i:i + 8], 2):02X}' for i in range(0, 64, 8))
                    info_type.append("F")
                    arlam_info.append(formatted_key_hex)

        if maintenance_data != 0:
            target_binary = bin(maintenance_data)[2:].zfill(64)  # 64비트

            for key, description in maintenance_dict.items():
                key_binary = bin(key)[2:].zfill(64)  # 64비트
                matching_bits = [i for i, (bit_target, bit_key) in enumerate(zip(target_binary, key_binary)) if
                                 bit_target == '1' == bit_key]

                if matching_bits:
                    formatted_key_hex = '0x' + ''.join(f'{int(key_binary[i:i + 8], 2):02X}' for i in range(0, 64, 8))
                    info_type.append("A")
                    arlam_info.append(formatted_key_hex)

    except Exception as ex:
        return ex

    decoded_packet_list = list()
    for i in range(0, len(info_type)):
        decoded_packet = {
            "from_data_time_info": from_data_time_info,
            "ai_pems_info": ai_pems_info,
            "info_type": info_type[i],
            "arlam_info": arlam_info[i]
        }
        decoded_packet_list.append(decoded_packet)
    if len(decoded_packet_list) == 0:
        decoded_packet = {
            "from_data_time_info": from_data_time_info,
            "ai_pems_info": ai_pems_info,
            "info_type": "",
            "arlam_info": ""
        }
        decoded_packet_list.append(decoded_packet)
    return decoded_packet_list


def get_cmd_three_param(cmd_three):
    params = {}
    if bool(cmd_three):
        cmd_three_list = list()
        # Extract relevant information
        reg_date_info = cmd_three.get('from_data_time_info')
        ai_pems_info = cmd_three.get('ai_pems_info')

        info_type = cmd_three.get('info_type')
        arlam_info = cmd_three.get('arlam_info')
        # Construct datetime object from received information
        reg_date = datetime(reg_date_info['year'], reg_date_info['month'], reg_date_info['day'],
                            reg_date_info['hour'], reg_date_info['minute'], reg_date_info['second'])
        # reg_date = reg_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        cmd_three_list.append({
            "reg_date": reg_date,
            "equip_sno": ai_pems_info['device_serial_number'],
            "equip_type": ai_pems_info['device_type'],
            "equip_no": ai_pems_info['device_sequence'],
            "info_type": info_type,
            # F: 고장정보, A: 경보정보
            "arlam_info": arlam_info  # 고장정보
        })
    params.update({'cmd_three': cmd_three_list})

    return params





# if __name__ == '__main__':
#     hex_values_list = []
#     int_list = [127, 0, 1, 0, 183, 7, 232, 2, 13, 0, 0, 0, 2, 4, 0, 1, 3, 0, 1, 3, 1, 1, 1, 1, 0, 65, 0, 10, 0, 0, 11, 184, 2, 210, 11, 184, 2, 210, 1, 0, 0, 0, 0, 0, 67, 197, 82, 173, 0, 0, 0, 0, 0, 0, 0, 0, 77, 123, 234, 65, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 69, 14, 238, 122, 0, 66, 0, 12, 0, 0, 0, 0, 72, 111, 197, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 90, 46, 126, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#     data = b'\x7f\x00\x01\x00\xb7\x07\xe8\x02\x0c\x00\x00\x00\x02\x04\x00\x01\x03\x01\x00\x03\x01\x01\x01\x02\x00\x00\x00\x03\x00\x00\x0b\xb8\x06}\x0b\xb8\x06}\x01\x00\x00\x00\x00\x00C\xc3\xd4\xa5\x00\x00\x00\x00\x00\x00\x00\x00M\xd2\x8c\xc2\x00\x00\x00\x00\x00\x00\x00\x00H\xaf\xd0.IN\xad\xcdIO\xcb\x1dI_#6H\xf2Nd\x00\x00\x00\x00J\xae\xe3\xaeK\xf0\xec\xe5\x00\x00\x00\x01?\x1d\xd0+Jz!\xf2\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x10\x00\x00\x02\xbf\x00\x00\x02\xbf\x00\x00\x02\xfc\x00\x00\x01\xdb\x00\x00\x00\x00\x00\x00\x13\x0f\x00\x00g\x15\x00\x00\x00\x00\xe8$~\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
#
#     head = 5
#     for value in int_list:
#         hex_values_list.append(hex(value))
#
#     hex_values_list = [struct.pack('B', value) for value in int_list]
#     result = b''
#     for i in range(0, len(hex_values_list)):
#         result += hex_values_list[i]
#
#     # hex_values_list_ = [struct.pack('B', value) for value in int_list]
#     a = cmd_one(result[head:])
#     print()
