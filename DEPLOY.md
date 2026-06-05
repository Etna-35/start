# Деплой бота на VPS (Ubuntu) — пошагово

От свежей Ubuntu до работающего бота на `https://chronobot.no-money-no-honey.ru`.
Поддомен меняется в одном месте — переменной `BOT_DOMAIN` в `.env`.

---

## 0. Что должно быть готово

- VPS с Ubuntu 22.04/24.04 LTS, тип виртуализации **KVM**, публичный IPv4.
- Домен `no-money-no-honey.ru` под твоим управлением.

## 1. DNS: направить поддомен на VPS

В панели домена добавь **A-запись**:

| Тип | Имя | Значение | TTL |
|---|---|---|---|
| `A` | `chronobot` | `212.67.8.145` | `300` |

Проверка (с любого компа), что запись разъехалась:
```bash
dig +short chronobot.no-money-no-honey.ru     # должен вернуть IP твоего VPS
```
Основной сайт (`@`, `www`) не трогаешь — он остаётся на своём сервере.

## 2. Установить Docker на VPS

Подключись по SSH (`ssh root@<IP>`), затем:
```bash
apt update && apt -y upgrade
curl -fsSL https://get.docker.com | sh
# проверка:
docker --version && docker compose version
```

## 3. Открыть порты (если включён firewall)

Нужны только 22 (SSH), 80 и 443:
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```
> Порт 5432 (Postgres) и 8000 (app) наружу НЕ открываем — в прод-стеке они не публикуются.

## 4. Забрать код

```bash
apt -y install git
git clone https://github.com/Etna-35/start.git /opt/chrono-bot
cd /opt/chrono-bot
```

## 5. Настроить .env

```bash
cp .env.example .env
nano .env
```
Заполни как минимум:
```
BOT_DOMAIN=chronobot.no-money-no-honey.ru
ACME_EMAIL=твой@email.ru
POSTGRES_PASSWORD=<длинный-случайный-пароль>
MAX_WEBHOOK_SECRET=<длинная-случайная-строка>
APP_ENV=production
# MAX_BOT_TOKEN можно оставить пустым, пока бот на проверке — впишешь, когда придёт токен.
```
`DATABASE_URL` в проде подставляется автоматически из `POSTGRES_PASSWORD` (см. `docker-compose.prod.yml`), отдельно его задавать не нужно.

## 6. Запустить

```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Это поднимет Postgres, прогонит миграции (`alembic upgrade head`), запустит app и Caddy. Caddy сам выпустит HTTPS-сертификат для поддомена (нужно, чтобы DNS из шага 1 уже работал).

Логи, если что-то не так:
```bash
docker compose -f docker-compose.prod.yml logs -f caddy   # выпуск сертификата
docker compose -f docker-compose.prod.yml logs -f app     # приложение
```

## 7. Проверить, что живо

```bash
curl https://chronobot.no-money-no-honey.ru/health
# {"status":"ok"}
```
Если ответ есть и сертификат валиден (зелёный замок) — инфраструктура готова.

## 8. Когда придёт токен MAX

1. Впиши `MAX_BOT_TOKEN=...` в `.env` и перезапусти app:
   ```bash
   docker compose -f docker-compose.prod.yml up -d app
   ```
2. Зарегистрируй webhook у MAX на адрес:
   ```
   https://chronobot.no-money-no-honey.ru/webhook/max
   ```
   и в заголовке секрета используй значение `MAX_WEBHOOK_SECRET` (заголовок по умолчанию `X-Max-Bot-Api-Secret`).
   Зарегистрировать можно методом `MaxClient.set_webhook(url)` или вручную через MAX API — уточни по их документации точный эндпоинт подписки.
3. Напиши боту `/start` в MAX — должно прийти приветствие.

---

## Обновление кода в будущем

```bash
cd /opt/chrono-bot
git pull
docker compose -f docker-compose.prod.yml up -d --build
```
Миграции применяются автоматически при старте app.

## Бэкап базы (рекомендуется)

Разовый дамп:
```bash
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U chrono chrono > backup_$(date +%F).sql
```
Для регулярных бэкапов добавь эту команду в `cron` (например, ночью). В базе —
приватные дневники людей, поэтому бэкапы и их хранение держи в надёжном месте.
