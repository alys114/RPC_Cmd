# 需求
- 可以异步的执行多个命令
- 对多台机器

# 难点
pika 对 Rabbitmq 的封装太细，使用起来比较复杂

# 执行
- core/RPC_Server_1
- core/RPC_Client_1


# 部署环境
1. 必须安装rabbitmq到服务器（10.0.0.90）
2. 安装paramiko模块、pika模块；
3. 10.0.0.90和10.0.0.88服务器的ssh配置，请查看conf/setting.cnf

# 测试命令
run "ifconfig eth0" 10.0.0.90,10.0.0.88

# 运行截图
看doc下的测试截图.jpg





