# GiveawayBot

Production-ready Telegram bot for running giveaways inside the bot. The channel is used only to verify subscription.

## Features
- Deep link participation: `https://t.me/<botname>?start=gw_<giveaway_id>`
- Subscription check via `getChatMember` for one required channel
- Unique participation per giveaway (DB constraint)
- Auto finish by timer + safety check every minute
- Manual finish by admin
- Broadcasts to participants with rate limiting and error handling

## Requirements
- Python 3.11+
- PostgreSQL
- Bot must be **admin** in the required channel to correctly check membership and publish posts

## Setup
1. Create a bot via BotFather and get `BOT_TOKEN`.
2. Add the bot as **admin** in the required channel (mandatory for `getChatMember`).
3. Copy `.env.example` to `.env` and fill values.

Example `.env`:
```
BOT_TOKEN=123456:ABCDEF
ADMINS=123456789,987654321
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/giveaway
```

Docker Compose note: inside the container the DB host is `db`, not `localhost`.
If you set `DATABASE_URL` manually for Docker, use:
`postgresql+asyncpg://postgres:postgres@db:5432/giveaway`

## Run with Docker Compose
```
docker compose up --build
```

## Admin usage
- Create giveaway: `/new` (wizard)
- Open admin panel: `/admin`

When giveaway is created, you will get a deep link and can optionally publish a post to the channel:
`https://t.me/<botname>?start=gw_<giveaway_id>`

## Admin panel
For each giveaway:
- `👥 Участники (count)` — show participants
- `🎲 Выбрать победителей` — finish and pick winners
- `⏹ Завершить сейчас` — finish immediately
- `📣 Рассылка участникам` — send text to all participants
- `📝 Изменить описание` — update giveaway description
- `⏰ Изменить дату окончания` — update end time
- `#️⃣ Изменить кол-во победителей` — update winners count
- `🔁 Сгенерировать новую ссылку` — show deep link
- `📊 Статус/сводка` — show giveaway summary
- `🗑 Удалить конкурс` — delete giveaway

## Broadcast limitations
Telegram allows bots to message only users who have opened the bot chat (started the bot). If a user blocks the bot or chat is not found, their `can_dm` is set to `false`.

## Rate limits
The bot enforces conservative rate limits to avoid 429 errors:
- ~30 msg/sec globally
- ~1 msg/sec per user
- ~20 msg/min per chat (channel/group)

Broadcasts are queued and sent with throttling; if Telegram returns 429, the bot waits `retry_after` and resumes from the last cursor. Jobs are resumable after restart.

## Time format
All dates are expected in **UTC**. Use format: `YYYY-MM-DD HH:MM`.

## How to run locally (without Docker)
### Windows (PowerShell)
1. Install Python 3.11+ and PostgreSQL.
2. Create a database (example: `giveaway`) and user.
3. Create venv and install deps:
```
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```
4. Create `.env` from `.env.example` and set:
```
BOT_TOKEN=...
ADMINS=123456789
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/giveaway
```
5. Run migrations:
```
alembic upgrade head
```
6. Start bot:
```
python -m app.main
```

### macOS/Linux
1. Create a PostgreSQL database and user.
2. Install dependencies: `pip install -r requirements.txt`
3. Set env vars (`BOT_TOKEN`, `ADMINS`, `DATABASE_URL`).
4. Run migrations: `alembic upgrade head`
5. Start bot: `python -m app.main`

## Stability notes
- The bot waits for PostgreSQL readiness before running migrations and starting.
- Database container has a healthcheck and restarts automatically.
- If DB credentials change, update `DATABASE_URL` and restart containers.
