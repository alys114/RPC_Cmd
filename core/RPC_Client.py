# Author: Vincent.chan
# Blog: http://blog.alys114.com

'''命令的生产者，结果的消费者'''

import pika
import uuid
import common

# 全局变量
AMQP_SERVER = '10.0.0.90'
AMQP_PORT = 5672
AMQP_USER = 'oldboy'
AMQP_PASSWORD = '123456'

class RemoteCmd_RpcClient(object):
	def __init__(self):
		creds_broker = pika.PlainCredentials(AMQP_USER, AMQP_PASSWORD)
		conn_param = pika.ConnectionParameters(AMQP_SERVER, AMQP_PORT, credentials=creds_broker)
		self.conn = pika.BlockingConnection(conn_param)

		self.channel = self.conn.channel()

		result = self.channel.queue_declare(exclusive=True)
		self.callback_queue = result.method.queue

		# 消费：服务器返回的结果
		self.channel.basic_consume(self.on_response, no_ack=True,
								   queue=self.callback_queue)

	def on_response(self, ch, method, props, body):
		if self.corr_id == props.correlation_id:
			self.response = body

	def call(self, hosts,cmd):
		self.response = None
		self.corr_id = str(uuid.uuid4())
		self.channel.basic_publish(exchange='',
								   routing_key='rpc_queue',
								   properties=pika.BasicProperties(
									   reply_to=self.callback_queue,
									   correlation_id=self.corr_id,
								   ),
								   body=cmd)
		print(' [task_id]:',self.corr_id)
		while self.response is None:
			self.conn.process_data_events()
		return self.response.decode()

if __name__ == '__main__':

	cmd_rpc = RemoteCmd_RpcClient()
	remote_hosts = ['10.0.0.90']
	cmd ='df -h'
	for h in remote_hosts:
		print(" [x] Requesting (%s) running: %s "%(h,cmd))
		response = cmd_rpc.call(h,cmd)
		common.menuDisplay(("[ Got %r ]" % h).center(50,'#'))
		print(response)

