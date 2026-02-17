# Travel AI Agent

## Project Structure
- `docker-compose.yml` — сервисы: n8n + app (telegram-бот / AI-агент)
- `Dockerfile` — сборка основного Python-сервиса
- `.github/workflows/deploy.yml` — автодеплой на VM при пуше в main
- `scripts/setup-vm.sh` — первичная настройка VM (Docker + клон репо)

## Deploy
- Push в `main` → GitHub Actions → SSH на VM → `git pull` + `docker compose up -d --build`
- GitHub Secrets: `VM_HOST`, `VM_USER`, `VM_SSH_KEY`

## Local Development
```bash
cp .env.example .env  # заполнить переменные
docker compose up -d --build
```
