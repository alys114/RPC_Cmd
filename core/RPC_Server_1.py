# Author: Vincent.chan
# Blog: http://blog.alys114.com

import pika
import paramiko
import common

# 全局变量
AMQP_SERVER = '10.0.0.90'
AMQP_PORT = 5672
AMQP_USER = 'oldboy'
AMQP_PASSWORD = '123456'

creds_broker = pika.PlainCredentials(AMQP_USER, AMQP_PASSWORD)
conn_param = pika.ConnectionParameters(AMQP_SERVER, AMQP_PORT, credentials=creds_broker)
conn = pika.BlockingConnection(conn_param)
channel = conn.channel()

channel.exchange_declare(exchange='direct_logs',exchange_type='direct')

result = channel.queue_declare(exclusive=True)  # 一次性消费
queue_name = result.method.queue

hosts_list = ['10.0.0.90','10.0.0.88'] #监听的routing_key = IP
for h in hosts_list:
    channel.queue_bind(exchange='direct_logs',
                      queue=queue_name,
                      routing_key=h)

class ssh_host():
    def __init__(self, host, ip, port, user, password):
        self.host = host
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password

def get_host_info(host):
    p_ip = common.ReadConfig(host, 'ip')
    p_port = int(common.ReadConfig(host, 'port'))
    p_user = common.ReadConfig(host, 'user')
    p_password = common.ReadConfig(host, 'password')
    return ssh_host(host, p_ip, p_port, p_user, p_password)

def remote_run(cmd, remote_info):
    '''
    远程登录执行命令（只能执行一次性命令，不能执行类似top、vim命令）
    类似于ssh
    :return:
    '''
    # 创建SSH对象
    ssh = paramiko.SSHClient()
    # 允许链接不在know_hosts文件中的主机
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 链接服务器
    ssh.connect(remote_info.ip, remote_info.port, username=remote_info.user, password=remote_info.password)

    # 执行命令
    stdin, stdout, stderr = ssh.exec_command(cmd)

    # 获取命令结果
    if stdout is not None:
        result = stdout.read()
    else:
        result = stderr.read()

    print(('[%s]执行结果'%remote_info.host).center(30,'-'))
    print(result.decode())

    # 关闭
    ssh.close()

    return result.decode()

def cmd_run(hosts, cmd):
    remote_host = get_host_info(hosts)
    return remote_run(cmd, remote_host)


def on_request(ch, method, props, body):
    cmd = body.decode()
    print(" [.] running cmd:( %s )" % cmd)

    response = cmd_run(method.routing_key, cmd)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=response)

    ch.basic_ack(delivery_tag=method.delivery_tag)
    print('channel is open:',ch.is_open)


channel.basic_qos(prefetch_count=1)
print(queue_name)
channel.basic_consume(on_request, queue=queue_name)

print(" [x] Awaiting RPC requests")
channel.start_consuming()
