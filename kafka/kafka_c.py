from confluent_kafka import Consumer, KafkaError

# 카프카 브로커의 주소
bootstrap_servers = 'fs.miraecit.com:10000'

# 컨슈머 구성 설정
conf = {
    'bootstrap.servers': bootstrap_servers,
    'group.id': 'my_consumer_group',  # 그룹 ID를 지정합니다.
    'auto.offset.reset': 'earliest'   # 오프셋을 자동으로 조정하는 방법을 설정합니다. 여기서는 가장 이전 메시지부터 시작합니다.
}

# 컨슈머 생성
consumer = Consumer(conf)

# 구독할 토픽 설정
topic = 'test-topic'
#topic = 'tcp-data'
consumer.subscribe([topic])

# 메시지 수신 및 처리
try:
    while True:
        msg = consumer.poll(1.0)  # 1초 동안 메시지를 기다립니다.

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event 발생
                print(f"Reached end of partition on {msg.topic()}:{msg.partition()}")
            else:
                print(f"Error: {msg.error()}")
        else:
            # 메시지 처리 로직을 여기에 추가합니다.
            print(f"Received message: {msg.value().decode('utf-8')}")

except KeyboardInterrupt:
    pass
finally:
    # 컨슈머 종료
    consumer.close()
