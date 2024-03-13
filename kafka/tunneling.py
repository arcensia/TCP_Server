import sshtunnel

def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

with sshtunnel.open_tunnel(
        ('fs.miraecit.com', 22),
        ssh_username="sshuser",
        ssh_password="ssh@@1205",
        remote_bind_address=('192.168.1.111', 10000),
        local_bind_address=('127.0.0.1', 49092)
) as tunnel:
    pass
