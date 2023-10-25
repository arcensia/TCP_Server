import time

from confluent_kafka import Producer
from kafka.kafka_info import HOST, PORT
import logging

"""
kafka 메시지 전송 전략
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
        logging.info("open kafka Producer")

    def delivery_report(self, err, msg):
        """
        callback 함수
        :param err: error
        :param msg: str
        :return: isMessage
        """
        if err is not None:
            logging.info('kafka 메시지 전송 실패: {}'.format(err))
            pass
        else:
            pass
            # print('메시지 전송 성공: {}'.format(msg.value()))

    def send_message(self, message):
        topic = 'tcp-data'
        self.producer.produce(topic, value=str(message), callback=self.delivery_report)
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
                    'client.id': 'python-producer'
                })
                return producer
            except Exception as e:
                logging.info(f'Error connecting to Kafka: {str(e)}')
                print('Error connecting to Kafka, Retrying in 1 second...')
                time.sleep(1)


if __name__ == '__main__':
    kfk = kafka_manager()
    kfk.test_send(message='test')