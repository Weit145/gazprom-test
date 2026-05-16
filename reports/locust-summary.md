# Locust Load Test Summary

Прогон выполнен локально 16 мая 2026 года на Docker Compose окружении.

## Команда

```bash
poetry run locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://localhost:8000 --only-summary
```

## Параметры

- users: `20`
- spawn rate: `5 users/s`
- duration: `1m`
- host: `http://localhost:8000`

## Итог

- total requests: `2713`
- failures: `0`
- aggregated throughput: `45.77 req/s`
- aggregated avg response time: `259 ms`
- aggregated median response time: `100 ms`
- max response time: `1119 ms`

## Сводка по endpoint

| Method | Endpoint | Requests | Failures | Avg, ms | Min, ms | Max, ms | Median, ms | Req/s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GET | `/devices/{device_id}/analytics` | 409 | 0 | 244 | 7 | 1058 | 86 | 6.90 |
| GET | `/users/{user_id}/analytics` | 113 | 0 | 283 | 18 | 936 | 100 | 1.91 |
| POST | `/devices/{device_id}` | 2071 | 0 | 268 | 7 | 1119 | 110 | 34.94 |
| POST | `/users` | 20 | 0 | 175 | 22 | 410 | 130 | 0.34 |
| POST | `/users/{user_id}/devices/{device_id}` | 100 | 0 | 117 | 18 | 507 | 62 | 1.69 |
| Aggregated | all | 2713 | 0 | 259 | 7 | 1119 | 100 | 45.77 |

## Percentiles

| Endpoint | p50 | p66 | p75 | p80 | p90 | p95 | p98 | p99 | p100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `GET /devices/{device_id}/analytics` | 86 | 280 | 470 | 530 | 680 | 800 | 900 | 950 | 1100 |
| `GET /users/{user_id}/analytics` | 100 | 410 | 540 | 610 | 720 | 810 | 890 | 900 | 940 |
| `POST /devices/{device_id}` | 110 | 360 | 490 | 570 | 720 | 820 | 900 | 960 | 1100 |
| `POST /users` | 130 | 260 | 260 | 270 | 370 | 410 | 410 | 410 | 410 |
| `POST /users/{user_id}/devices/{device_id}` | 64 | 100 | 150 | 160 | 380 | 460 | 480 | 510 | 510 |
| Aggregated | 100 | 330 | 480 | 550 | 710 | 810 | 900 | 950 | 1100 |
