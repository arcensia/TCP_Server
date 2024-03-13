import time

import sshtunnel
from confluent_kafka import Producer



def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


def produce_message():
    producer_conf = {
        # 'bootstrap.servers': '192.168.1.111:10000',  # Kafka 브로커의 주소
        'bootstrap.servers': 'fs.miraecit.com:10000',  # Kafka 브로커의 주소
        # 'bootstrap.servers': '106.251.228.82:10000',  # Kafka 브로커의 주소
        'client.id': 'ipp01'
    }

    producer = Producer(producer_conf)

    topic = 'test-topic'
    key = 'key'
    value = 'Hello, Kafka!'

    producer.produce(topic, key=key, value=value, callback=delivery_report)
    producer.flush()


produce_message()

# with sshtunnel.open_tunnel(
#         ('fs.miraecit.com', 22),
#         ssh_username="sshuser",
#         ssh_password="ssh@@1205",
#         remote_bind_address=('192.168.1.111', 10000),
#         local_bind_address=('127.0.0.1', 10000)
# ) as tunnel:
#     produce_message()
    # while True:
    #     time.sleep(1)

