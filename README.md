# Gazprom Test

REST-сервис на FastAPI для учета и анализа статистики, поступающей с условных устройств.

Сервис принимает показания устройства в формате `{"x": float, "y": float, "z": float}`, сохраняет их с временной меткой в PostgreSQL и возвращает аналитику по устройству или пользователю.

## Соответствие ТЗ

| Требование | Статус | Где реализовано |
| --- | --- | --- |
| Сбор статистики с устройства по идентификатору | Реализовано | `POST /devices/{device_id}` |
| Формат статистики `x`, `y`, `z` | Реализовано | Pydantic-схема `CreateDevice` |
| Аналитика устройства за период и за все время | Реализовано | `GET /devices/{device_id}/analytics` |
| `min`, `max`, `count`, `sum`, `median` | Реализовано | SQLAlchemy aggregate-запросы |
| Добавление пользователей устройств | Реализовано | `POST /users` |
| Привязка устройств к пользователю | Реализовано | `POST /users/{user_id}/devices/{device_id}` |
| Аналитика по пользователю общая и по каждому устройству | Реализовано | `GET /users/{user_id}/analytics` |
| REST API | Реализовано | FastAPI routers |
| FastAPI | Реализовано | `app/main.py` |
| Хранение данных в БД | Реализовано | PostgreSQL |
| Асинхронная аналитика через Celery | Реализовано | `app/infrastructure/tasks.py` |
| Нагрузочное тестирование Locust | Реализовано | `locustfile.py` |
| Docker + Docker Compose | Реализовано | `Dockerfile`, `docker-compose.yml` |

## Стек

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy Async
- PostgreSQL 16
- Alembic
- Celery
- RabbitMQ
- Docker Compose
- Pytest
- Locust
- Ruff

## Архитектура

```text
app/
  core/                         конфигурация и логирование
  domain/                       доменные dataclass-модели
  infrastructure/               Celery app и фоновые задачи
  repositories/storage/models/  SQLAlchemy-модели
  repositories/storage/postgres PostgreSQL-репозиторий
  transport/api/v1/             FastAPI handlers и Pydantic-схемы
  usecase/                      сервисный слой
migrations/                     Alembic-миграции
reports/                        результаты нагрузочного тестирования
tests/                          unit-тесты
locustfile.py                   сценарий нагрузочного тестирования
docker-compose.yml              PostgreSQL, RabbitMQ, API, Celery worker
Makefile                        команды для разработки и проверки
```

Основной поток записи данных:

1. Клиент отправляет `POST /devices/{device_id}` с координатами `x`, `y`, `z`.
2. Сервис создает устройство, если его еще нет.
3. Показания сохраняются в таблицу `device_data` с `created_at`.
4. После коммита в Celery отправляется задача пересчета кеша аналитики устройства.
5. Celery worker пересчитывает агрегаты и делает upsert в таблицу `device_analytics`.

Если аналитика устройства запрашивается за все время, сервис сначала пытается взять свежий кеш. Для периода аналитика считается SQL-запросом по `device_data`.

## Быстрый запуск через Docker

Создать `.env`:

```bash
cp .env.example .env
```

Поднять окружение:

```bash
make docker-up
```

Или напрямую:

```bash
docker compose up --build -d
```

После запуска:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- RabbitMQ UI: `http://localhost:15672`
- RabbitMQ login/password: `guest / guest`

Миграции Alembic применяются автоматически при старте контейнера `api`.

Проверить доступность API:

```bash
curl http://localhost:8000/_info
```

## Makefile

```bash
make help
```

Основные команды:

```bash
make test          # запустить unit-тесты
make docker-up     # собрать и поднять сервисы
make docker-down   # остановить сервисы
make docker-clean  # остановить сервисы и удалить volume PostgreSQL
make docker-logs   # смотреть логи всех сервисов
make locust        # headless Locust-прогон
make locust-ui     # Locust UI
```

Параметры Locust можно переопределять:

```bash
make locust LOCUST_USERS=50 LOCUST_SPAWN_RATE=10 LOCUST_RUN_TIME=2m
```

Логи только API в реальном времени:

```bash
docker compose logs -f api
```

Логи Celery worker:

```bash
docker compose logs -f worker
```

## Переменные окружения

Пример для Docker Compose находится в `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_TASK_ALWAYS_EAGER=false
```

Если запускать API локально, а PostgreSQL и RabbitMQ оставить в Docker, нужно использовать `localhost`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_TASK_ALWAYS_EAGER=false
```

## API

### Healthcheck

```http
GET /_info
```

Ответ:

```json
200
```

### Создать пользователя

```http
POST /users
```

Тело запроса:

```json
{
  "name": "user-1"
}
```

Пример ответа:

```json
{
  "id": "e5f0e5be-d4d1-4f6d-95c7-5a8a6fba0d7d",
  "name": "user-1",
  "created_at": "2026-05-16T11:30:00.000000Z"
}
```

### Привязать устройство к пользователю

```http
POST /users/{user_id}/devices/{device_id}
```

Если устройства еще нет, оно создается автоматически.

Пример ответа:

```json
{
  "user_id": "e5f0e5be-d4d1-4f6d-95c7-5a8a6fba0d7d",
  "device_id": "7c9c8cbb-276c-4d20-b4e5-5df13b8b16ef",
  "created_at": "2026-05-16T11:31:00.000000Z"
}
```

### Отправить показания устройства

```http
POST /devices/{device_id}
```

Тело запроса:

```json
{
  "x": 1.2,
  "y": 3.4,
  "z": 5.6
}
```

Пример ответа:

```json
{
  "id": "7c9c8cbb-276c-4d20-b4e5-5df13b8b16ef",
  "x": 1.2,
  "y": 3.4,
  "z": 5.6,
  "created_at": "2026-05-16T11:32:00.000000Z"
}
```

### Получить аналитику устройства

За все время:

```http
GET /devices/{device_id}/analytics
```

За период:

```http
GET /devices/{device_id}/analytics?date_from=2026-05-16T00:00:00Z&date_to=2026-05-16T23:59:59Z
```

Пример ответа:

```json
{
  "id": "7c9c8cbb-276c-4d20-b4e5-5df13b8b16ef",
  "period": {
    "date_from": null,
    "date_to": null
  },
  "x": {
    "min": 1.2,
    "max": 10.0,
    "count": 2,
    "sum": 11.2,
    "median": 5.6
  },
  "y": {
    "min": 3.4,
    "max": 20.0,
    "count": 2,
    "sum": 23.4,
    "median": 11.7
  },
  "z": {
    "min": 5.6,
    "max": 30.0,
    "count": 2,
    "sum": 35.6,
    "median": 17.8
  }
}
```

### Получить аналитику пользователя

За все время:

```http
GET /users/{user_id}/analytics
```

За период:

```http
GET /users/{user_id}/analytics?date_from=2026-05-16T00:00:00Z&date_to=2026-05-16T23:59:59Z
```

Ответ содержит:

- `total` - агрегированную аналитику по всем устройствам пользователя;
- `devices` - аналитику отдельно по каждому устройству пользователя.

## Локальный запуск без Docker для API

Установить зависимости:

```bash
poetry install
```

Поднять PostgreSQL и RabbitMQ:

```bash
docker compose up -d db rabbitmq
```

В `.env` для локального API указать `localhost`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
```

Применить миграции:

```bash
poetry run alembic upgrade head
```

Запустить API:

```bash
poetry run uvicorn app.main:app --reload
```

Запустить Celery worker:

```bash
poetry run celery -A app.infrastructure.celery_app.celery_app worker --loglevel=info
```

## Тесты и линтер

Unit-тесты:

```bash
make test
```

или:

```bash
poetry run pytest
```

Тесты сервиса находятся в `tests/test_service.py`. База данных в них не используется: репозиторий, сессия и Celery task замоканы.

Ruff:

```bash
poetry run ruff check .
poetry run ruff format --check .
```

Автоисправления:

```bash
poetry run ruff check . --fix
poetry run ruff format .
```

Проверено локально:

```text
pytest: 11 passed
ruff check: All checks passed
ruff format --check: 27 files already formatted
```

## Нагрузочное тестирование

Сценарий находится в `locustfile.py`.

Сценарий:

1. Каждый виртуальный пользователь создает пользователя через `POST /users`.
2. Создает 5 устройств и привязывает их к пользователю.
3. Основная нагрузка пишет показания через `POST /devices/{device_id}`.
4. Дополнительно запрашивает аналитику устройства и пользователя.

Запуск headless:

```bash
make locust
```

Команда, которая будет выполнена:

```bash
poetry run locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://localhost:8000 --only-summary
```

Запуск Locust UI:

```bash
make locust-ui
```

После запуска UI открыть:

```text
http://localhost:8089
```

### Результат нагрузочного теста

Прогон выполнен локально 16 мая 2026 года на Docker Compose окружении:

- users: `20`;
- spawn rate: `5 users/s`;
- duration: `1m`;
- host: `http://localhost:8000`;
- total requests: `2713`;
- failures: `0`;
- aggregated throughput: `45.77 req/s`;
- aggregated avg response time: `259 ms`;
- aggregated median response time: `100 ms`;
- max response time: `1119 ms`.

Сводка по endpoint:

| Method | Endpoint | Requests | Failures | Avg, ms | Median, ms | Req/s |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| GET | `/devices/{device_id}/analytics` | 409 | 0 | 244 | 86 | 6.90 |
| GET | `/users/{user_id}/analytics` | 113 | 0 | 283 | 100 | 1.91 |
| POST | `/devices/{device_id}` | 2071 | 0 | 268 | 110 | 34.94 |
| POST | `/users` | 20 | 0 | 175 | 130 | 0.34 |
| POST | `/users/{user_id}/devices/{device_id}` | 100 | 0 | 117 | 62 | 1.69 |
| Aggregated | all | 2713 | 0 | 259 | 100 | 45.77 |

Полный отчет продублирован в `reports/locust-summary.md`.

## База данных

Основные таблицы:

- `user` - пользователи;
- `device` - устройства, опционально привязанные к пользователю;
- `device_data` - сырые показания `x`, `y`, `z` с временной меткой;
- `device_analytics` - кеш аналитики устройства за все время.

Медиана считается на стороне PostgreSQL через `percentile_cont(0.5)`.

## Docker-сервисы

`docker-compose.yml` поднимает:

- `db` - PostgreSQL 16;
- `rabbitmq` - RabbitMQ с management UI;
- `api` - FastAPI-приложение;
- `worker` - Celery worker для пересчета кеша аналитики.

Остановить контейнеры:

```bash
make docker-down
```

Остановить контейнеры и удалить данные PostgreSQL:

```bash
make docker-clean
```
