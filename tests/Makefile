.PHONY: up dn uplogs start stop restart status logs

HOST := 192.168.219.3
PORT := 33033
DATA_DIR := .

up: start

dn: stop
down: stop

uplogs: up logs

start:
	@pulse serve $(DATA_DIR) --host $(HOST) --port $(PORT) \
		--allow-non-localhost-access-with-plaintext-transmission-risk
	@echo "服务已启动: http://$(HOST):$(PORT)"

stop:
	@pulse stop || echo "服务已停止或未运行"

restart:
	@pulse restart || echo "服务已重启"

status:
	@pulse status || echo "服务未运行"

logs:
	tail -f $(DATA_DIR)/web.log
