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
