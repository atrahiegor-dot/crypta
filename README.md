# TON Tasks Bot

Telegram-бот с интеграцией TON-блокчейна, системой XP, заданиями, таблицей лидеров и реферальной программой.

## Стек

- **Python 3.12** + **aiogram 3.13**
- **PostgreSQL 16** + **SQLAlchemy 2 (async)**
- **Redis 7** (FSM, кэш, TON Connect)
- **pytonconnect** — подключение TON-кошельков
- **Docker Compose** — оркестрация

---

## Быстрый старт

### 1. Конфигурация

```bash
cp .env.example .env
```

Заполните `.env`:

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis URL |
| `TON_CONNECT_MANIFEST_URL` | Публичный URL к `tonconnect-manifest.json` |
| `ADMIN_IDS` | Telegram ID администраторов (через запятую) |

### 2. TON Connect Manifest

Файл `tonconnect-manifest.json` нужно разместить по публичному HTTPS-адресу.
Например, загрузите его на GitHub Pages или любой статичный хостинг, затем
укажите URL в `TON_CONNECT_MANIFEST_URL`.

Содержимое файла:
```json
{
  "url": "https://t.me/your_bot_username",
  "name": "TON Tasks Bot",
  "iconUrl": "https://ton.org/download/ton_symbol.png"
}
```

### 3. Запуск через Docker

```bash
docker compose up -d --build
```

### 4. Запуск вручную (разработка)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Применить миграции
alembic upgrade head

# Запустить бота
python -m bot.main
```

---

## Структура проекта

```
bot/
├── config.py              # Конфигурация (pydantic-settings)
├── main.py                # Точка входа
├── database/
│   ├── base.py            # SQLAlchemy engine + session factory
│   ├── models.py          # ORM-модели
│   └── crud.py            # Все запросы к БД
├── services/
│   ├── xp_service.py      # Начисление XP, уровни, стрики
│   ├── task_service.py    # Логика заданий и сабмишнов
│   ├── referral_service.py# Реферальная система
│   └── ton_connect.py     # TON Connect интеграция
├── handlers/
│   ├── start.py           # /start, реферальный deep-link
│   ├── profile.py         # Профиль, достижения
│   ├── tasks.py           # Задания + FSM отправки доказательств
│   ├── wallet.py          # TON-кошелёк
│   ├── leaderboard.py     # Таблица лидеров (всё время / неделя / месяц)
│   ├── referral.py        # Реферальная программа
│   ├── checkin.py         # Ежедневный бонус
│   ├── moderation.py      # Очередь модерации
│   └── admin.py           # Административная панель
├── keyboards/
│   ├── inline.py          # Все inline-клавиатуры
│   └── reply.py           # Reply-клавиатуры (главное меню)
├── middlewares/
│   ├── database.py        # Инжекция сессии БД в хендлер
│   ├── auth.py            # Авторизация / регистрация / бан
│   └── throttling.py      # Rate limiting через Redis
└── utils/
    ├── helpers.py         # Форматирование текстов, escape
    └── decorators.py      # Декораторы для проверки ролей
```

---

## Система XP и уровней

| Уровень | Нужно XP |
|---|---|
| 1→2 | 100 |
| 2→3 | 300 |
| 3→4 | 600 |
| 4→5 | 1 000 |
| N→N+1 | N × (N+1) × 50 |

---

## Роли пользователей

| Роль | Возможности |
|---|---|
| `user` | Задания, рейтинг, рефералы |
| `moderator` | + Проверка заявок |
| `developer` | + Создание заданий, управление пользователями, статистика |

Назначение через `ADMIN_IDS` в `.env` (автоматически developer) или через команду `/admin`.

---

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Главное меню |
| `/profile` | Профиль |
| `/tasks` | Задания |
| `/wallet` | TON-кошелёк |
| `/leaderboard` | Таблица лидеров |
| `/referral` | Реферальная программа |
| `/checkin` | Ежедневный бонус |
| `/admin` | Панель администратора |
| `/mod_next` | Следующая заявка на проверке |
