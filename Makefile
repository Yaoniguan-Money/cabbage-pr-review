.PHONY: demo prod test-backend test-frontend aliyun-verify

# 本机验收（需在已 docker compose up 的环境执行，或由 scripts/aliyun-verify-demo.sh 调用）
aliyun-verify:
	bash scripts/aliyun-verify-demo.sh

# 零密钥演示（默认 .env.demo，可选 .env 覆盖）
demo:
	docker compose up --build

# 生产：确保存在 .env 后启动（需自行填写 DEEPSEEK_API_KEY）
prod:
	@test -f .env || cp .env.example .env
	docker compose up --build

test-backend:
	cd backend && PYTHONPATH=. pytest tests/ -q

test-frontend:
	cd frontend && npm test -- --run
