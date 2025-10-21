# 是否开启debug模式
debug = False
# 访问地址
bind = "0.0.0.0:3244"
# 工作进程数
workers = 2
# 工作线程数
threads = 2
# 超时时间
timeout = 600
# gunicorn + apscheduler场景下，解决多worker运行定时任务重复执行的问题
preload_app = False