.PHONY: install dev smoke test fmt clean help

help:
	@echo "Interior Design Agent · 常用命令"
	@echo "  make install   ── 安装 Python 依赖"
	@echo "  make dev       ── 启动后端开发服务器 (port 8000)"
	@echo "  make smoke     ── 端到端 mock 冒烟测试"
	@echo "  make test      ── 跑 pytest 单测"
	@echo "  make fmt       ── ruff 格式化"
	@echo "  make clean     ── 清理缓存"

install:
	pip install -e ".[dev]"

dev:
	uvicorn server.main:app --reload --port 8000

smoke:
	python -m tests.smoke_test

test:
	pytest tests/ -v

fmt:
	ruff check --fix .
	ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
