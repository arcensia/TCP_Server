from datetime import datetime


# def unescape_data(data):
#     # Byte Stuffing을 처리하는 함수
#     # 두 코드 모두 0x7D가 나오면 다음 바이트에 XOR 연산을 적용하여 Byte Stuffing을 수행합니다
#     # C#의 commandParsing와 같습니다.
#     result = bytearray()
#     i = 0
#     while i < len(data):
#         if data[i:i + 1] == b"\x7D":
#             i += 1
#             result.append(data[i] ^ 0x20)
#         else:
#             result.extend(data[i:i + 1])
#         i += 1
#     return bytes(result)


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


def command_parsing(packet, command_parsing_escFlag):

    packCnt = 0
    packBuf = [0] * 250  # DefineConstants.MAX_PACK_SIZE를 250으로 가정

    chk = 32
    for ch in packet:
        # 현재 데이터가 ESC(0x7D)값이고 이전 상태가 ESC상태가 아니라면 ESC 상태로 변경
        if ch == 0x7D and command_parsing_escFlag == 0:
            command_parsing_escFlag = 1
        # ESC 상태라면, 즉 바로 전 데이터가 0x7D로 왔기 때문에
        # 이번 데이터는 플래그 데이터가 아닌 실제 값이다.
        elif command_parsing_escFlag == 1:
            # 플래그 클리어
            command_parsing_escFlag = 0
            # 그런데 만약 패킷 시작이 된 상태만 데이터 추가
            if packCnt != 0:
                packBuf[packCnt] = ch ^ chk
                packCnt += 1
        # 일반 상태
        else:
            # 일반 상태일때 플래그 데이터(STX, ETX)가 들어오면 실제 플래그 값으로 처리하면 된다.
            # 시작
            if ch == 0x7F:  # 여기서 0x7F로 수정
                # 패킷 시작
                packCnt = 0
                packBuf[packCnt] = ch
                packCnt += 1
            # 종료
            elif ch == 0x7E:  # 여기서 0x7E로 수정
                # 패킷 종료
                packBuf[packCnt] = ch
                packCnt += 1
            else:
                # 일반모드에서 플래그(STX, ETX) 데이터가 아니라면 모두 패킷 데이터
                packBuf[packCnt] = ch
                packCnt += 1
        # 만약 ETX가 발생하지 않고 최대 버퍼까지 증가했다면
        # 이상으로 간주하고 에러
        if packCnt >= 250:
            packCnt = 0

    # return is_available
    return packBuf, command_parsing_escFlag
