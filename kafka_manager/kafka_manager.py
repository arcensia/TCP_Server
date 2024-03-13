from confluent_kafka import Producer
# from kafka_manager.kafka_info import HOST, PORT
import logging
import time

import json

"""
kafka_manager 메시지 전송 전략
전송데이터 목록
1. ip별 data전송 (ex CLIENTS)
2. Log
    - TCP_Server State 전송 
    - TCP_Server에 연결된 Client리스트 연결 상태 전송
"""

# KAFKA_SERVER = HOST + ":" + str(PORT)


class kafka_manager:

    def __init__(self):
        # self.producer = Producer({
        #             'bootstrap.servers': KAFKA_SERVER, #카프카 서버 주소
        #             'client.id': 'python-client_flask_server'
        #             # 'client.id': 'python-producer'
        #
        #             ,'acks': 'all',  # 모든 복제본이 메시지를 성공적으로 저장할 때까지 재시도
        #             'retries': 3,  # 메시지 전송 재시도 횟수
        #             'retry.backoff.ms': 100  # 재시도 간격 (밀리초)
        #         })

        self.producer = self.connect_to_kafka_broker("localhost:19092")
        # self.producer = self.connect_to_kafka_broker(KAFKA_SERVER)

    def delivery_report(self, err, msg):
        """
        callback 함수
        :param err: error
        :param msg: str
        :return: isMessage
        """
        if err is not None:
            logging.info('kafka_manager 메시지 전송 실패: {}'.format(err))
        else:
            pass
            # print('메시지 전송 성공: {}'.format(msg.value()))

    def send_tcp_message(self, msg):
        topic = 'tcp-data'
        # value = {
        #     "electricity_data": client_data.electricity_data,
        #     "flow_data": client_data.flow_data,
        #     "pressure_Data": client_data.pressure_Data
        # }
        json_value = json.dumps(msg)
        self.producer.produce(topic, value=json_value, callback=self.delivery_report)
        self.producer.flush()

    def send_log(self, message):
        topic = 'log'
        self.producer.produce(topic, value=str(message), callback=self.delivery_report)
        self.producer.flush()

    def test_send(self, message):
        topic = 'test_send'
        self.producer.produce(topic, value=str(message), callback=self.delivery_report)
        self.producer.flush()
        logging.info('send message')

    def connect_to_kafka_broker(self, bootstrap_servers):
        while True:
            try:
                # 카프카 프로듀서 초기화
                producer = Producer({
                    'bootstrap.servers': bootstrap_servers, # 카프카 서버 주소
                    'client.id': 'python-client_flask_server'
                    # 'client.id': 'python-producer'

                    # , 'acks': 'all',  # 모든 복제본이 메시지를 성공적으로 저장할 때까지 재시도
                    # 'retries': 3,  # 메시지 전송 재시도 횟수
                    # 'retry.backoff.ms': 100  # 재시도 간격 (밀리초)
                })
                # producer.poll(0)
                # if producer.error():
                #     print(f"Error: {producer.error()}")
                # else:
                #     logging.info("open kafka_manager Producer")
                return producer

            except Exception as e:
                logging.info(f'Error connecting to Kafka: {str(e)}')
                print('Error connecting to Kafka, Retrying in 1 second...')
                time.sleep(1)

    def reconnect(self):
        # Kafka 연결 재시도 메서드
        if self.producer is not None:
            self.producer.close()
            self.producer = None
            logging.info("Disconnected from Kafka")

        while self.producer is None:
            try:
                # 카프카 프로듀서 초기화
                self.producer = Producer({
                    'bootstrap.servers': KAFKA_SERVER,
                    'client.id': 'python-client_flask_server'
                })
                logging.info("Reconnected to Kafka")
            except Exception as e:
                logging.info(f'Error connecting to Kafka: {str(e)}')
                print('Error connecting to Kafka, Retrying in 1 second...')
                time.sleep(1)

    def is_connected(self):
        return self.producer is not None


if __name__ == '__main__':
    from kafka_info import HOST, PORT

    kfk = kafka_manager()
    kfk.test_send(message='test')
