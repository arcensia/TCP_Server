from kafka_manager.kafka_manager import kafka_manager


class Cmd_Service:
    def __init__(self):
        self.kfk = kafka_manager()

    def send_message(self, client_data):
        self.kfk.send_tcp_message(client_data)
