# Author: Vincent.chan
# Blog: http://blog.alys114.com

'''命令的生产者，结果的消费者'''

import pika
import uuid
import common
import re

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
		# 生产者：不指定queue，
		self.channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

		# 生产指定的返回queue
		result = self.channel.queue_declare(exclusive=True)
		self.callback_queue = result.method.queue
		# print(self.callback_queue)
		# 消费：服务器返回的结果
		self.channel.basic_consume(self.on_response, no_ack=True,
								   queue=self.callback_queue)

	def on_response(self, ch, method, props, body):
		if self.corr_id == props.correlation_id:
			self.response = body

	def call(self, hosts,cmd):
		self.response = None
		self.corr_id = str(uuid.uuid4())

		self.channel.basic_publish(exchange='direct_logs',
								   routing_key=hosts,
								   properties=pika.BasicProperties(
									   reply_to=self.callback_queue,
									   correlation_id=self.corr_id,
								   ),
								   body=cmd)
		print(' [task_id]:',self.corr_id)


	def get_result(self):
		while self.response is None:
			self.conn.process_data_events()
		return self.response.decode()


if __name__ == '__main__':
	while True:
		# input_cmd = 'run "ifconfig eth0" --hosts 10.0.0.90    10.0.0.88'
		input_cmd = input('>>:([q:退出]) ')
		remote_hosts = None
		cmd = None
		if input_cmd == 'q':
			break
		elif input_cmd.startswith('run'):
			input_cmd = input_cmd.strip().replace("'", '"')
			cmd = re.search('"(.*)"', input_cmd).group(1)
			data = input_cmd.split(" --hosts ")
			if len(data) > 1:
				remote_hosts = data[1].split()
				# print(remote_hosts)
				cmd_rpc = RemoteCmd_RpcClient()
				for h in remote_hosts:
					print(" [x] Requesting (%s) running: %s " % (h, cmd))
					cmd_rpc.call(h, cmd)
					response = cmd_rpc.get_result()
					common.menuDisplay(("[ Response from %r ]" % h).center(50, '#'))
					print(response)
		else:
			common.errorPrompt('run "ifconfig eth0" --hosts 10.0.0.90    10.0.0.88')




