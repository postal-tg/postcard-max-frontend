# Postcard MAX Frontend

Внутренняя web-панель для команды.

Что внутри:

- серверный frontend на `FastAPI + Jinja2`
- логин по cookie session
- страницы для пользователей, промптов, генераций и ошибок
- чтение данных из backend internal API
- детальные карточки по пользователям, промптам и генерациям
- проксированный CSV-экспорт без раскрытия internal API key
- проксированный просмотр изображений генерации через frontend

## Проверки в CI

```bash
pip install ".[dev]"
ruff check src
python -m compileall src
```

## Документация

Общая документация и deploy-файлы ведутся в backend-репозитории как в основной точке входа проекта:

- Backend repo: https://github.com/postal-tg/postcard-max-backend
- Техническое задание: https://github.com/postal-tg/postcard-max-backend/blob/main/docs/TZ.md
- Архитектура: https://github.com/postal-tg/postcard-max-backend/blob/main/docs/ARCHITECTURE.md
- Конфигурация: https://github.com/postal-tg/postcard-max-backend/blob/main/docs/CONFIGURATION.md
- Деплой: https://github.com/postal-tg/postcard-max-backend/blob/main/docs/DEPLOY.md

Этот репозиторий содержит только frontend-код админки.
