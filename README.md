# Gazprom Test

REST-сервис на FastAPI для сбора и анализа показаний условных устройств.

## Возможности

- прием статистики устройства по UUID в формате `{"x": float, "y": float, "z": float}`;
- хранение пользователей, устройств и показаний в PostgreSQL;
- аналитика по устройству за все время или за период;
- аналитика по пользователю: агрегировано по всем устройствам и отдельно по каждому устройству;
- расчет кеша аналитики устройства через Celery и RabbitMQ;
- запуск окружения через Docker Compose;
- сценарий нагрузочного тестирования через Locust.

Для каждой величины `x`, `y`, `z` рассчитываются `min`, `max`, `count`, `sum`, `median`.

## API

`POST /devices/{device_id}`  
Сохраняет показания устройства. Если устройства еще нет, оно создается автоматически.

```json
{
  "x": 1.2,
  "y": 3.4,
  "z": 5.6
}
```

`GET /devices/{device_id}/analytics?date_from=2026-05-15T00:00:00Z&date_to=2026-05-15T23:59:59Z`  
Возвращает аналитику устройства. Параметры периода необязательны.

`POST /users`  
Создает пользователя.

```json
{
  "name": "user-1"
}
```

`POST /users/{user_id}/devices/{device_id}`  
Привязывает устройство к пользователю. Если устройства еще нет, оно создается.

`GET /users/{user_id}/analytics`  
Возвращает агрегированную аналитику по всем устройствам пользователя и аналитику по каждому устройству.

`GET /_info`  
Простая проверка доступности API.

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

После запуска:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- RabbitMQ UI: `http://localhost:15672` (`guest` / `guest`)

Миграции применяются автоматически при старте контейнера `api`.

## Локальная разработка

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

Тесты:

```bash
poetry run pytest
```

## Нагрузочное тестирование

Сценарий находится в `locustfile.py`. Он создает пользователя, привязывает несколько устройств, активно пишет показания и периодически читает аналитику.

Команда запуска:

```bash
poetry run locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://localhost:8000 --only-summary
```

Результат последнего локального запуска фиксируется в `reports/locust-summary.md`.
