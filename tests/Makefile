.PHONY: up dn uplogs start stop restart status logs

HOST := 192.168.219.3
PORT := 33033
DATA_DIR := .

up: start
up_init: start_init

dn: stop
dn_init: stop_init
down: stop
down_init: stop_init

uplogs: up logs

start_init: clean_init_data
	@pulse serve init_data --host $(HOST) --port 33034 \
                --allow-non-localhost-access-with-plaintext-transmission-risk

stop_init:
	@pulse stop init_data

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

clean_init_data:
	rm -r ./init_data/data || echo "文件已清理"

logs:
	tail -f $(DATA_DIR)/web.log
