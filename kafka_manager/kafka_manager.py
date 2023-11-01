import time

from confluent_kafka import Producer
from kafka_manager.kafka_info import HOST, PORT
import logging

import json
"""
kafka_manager 메시지 전송 전략
전송데이터 목록
1. ip별 data전송 (ex CLIENTS)
2. Log
    - TCP_Server State 전송 
    - TCP_Server에 연결된 Client리스트 연결 상태 전송
    - 또 뭐가 필요하지?
"""

KAFKA_SERVER = HOST + ":" + str(PORT)


class kafka_manager:
    def __init__(self):
        self.producer = self.connect_to_kafka_broker(KAFKA_SERVER)
        logging.info("open kafka_manager Producer")

    def delivery_report(self, err, msg):
        """
        callback 함수
        :param err: error
        :param msg: str
        :return: isMessage
        """
        if err is not None:
            logging.info('kafka_manager 메시지 전송 실패: {}'.format(err))
            pass
        else:
            pass
            # print('메시지 전송 성공: {}'.format(msg.value()))

    def send_tcp_message(self, client_data):
        topic = 'tcp-data'
        value = {
            "electricity_data": client_data.electricity_data,
            "flow_data": client_data.flow_data,
            "pressure_Data": client_data.pressure_Data
        }
        json_value = json.dumps(value)
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
                    'bootstrap.servers': bootstrap_servers,
                    'client.id': 'python-client_flask_server'
                    # 'client.id': 'python-producer'
                })
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
    kfk = kafka_manager()
    kfk.test_send(message='test')
