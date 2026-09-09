<div align="center">

# ◈ File Exchange

### Рефакторинг fullstack-файлообменника (MVP)

**Слоёный backend на FastAPI · Параллельная обработка через Celery chord · Frontend на Next.js**

[![CI](https://github.com/Alpha-Oi/fullstack-test-task-solution/actions/workflows/ci.yml/badge.svg)](https://github.com/Alpha-Oi/fullstack-test-task-solution/actions/workflows/ci.yml)
[![Лицензия: MIT](https://img.shields.io/badge/license-MIT-22a06b.svg)](LICENSE)
[![Последний коммит](https://img.shields.io/github/last-commit/Alpha-Oi/fullstack-test-task-solution?color=1f6feb)](https://github.com/Alpha-Oi/fullstack-test-task-solution/commits/main)

[English](README.md) · [Русский](README.ru.md) · [Как внести вклад](CONTRIBUTING.md) · [Правила сообщества](CODE_OF_CONDUCT.md) · [Безопасность](SECURITY.md)

</div>

---

Рефакторинг MVP-файлообменника из исходного [тестового задания](https://github.com/sputnik-llc/fullstack-test-task). Приложение загружает и хранит файлы, асинхронно проверяет их признаки, извлекает метаданные и создаёт алерты.

## Что реализовано

- backend разделён на HTTP, application, domain и infrastructure слои;
- сохранены исходные endpoints, response models и правила проверки файлов;
- загрузка идёт частями по 1 MiB без чтения целого файла в память;
- блокирующая обработка файлов вынесена из event loop;
- конфигурация БД, Redis, CORS и хранилища централизована;
- исправлены Docker-конфигурация PostgreSQL, Redis и сборка frontend;
- удаление файла каскадно удаляет связанные alerts;
- добавлены индексы для сортировки файлов и alerts по дате;
- frontend разделён на API, hooks, features, components, lib и types;
- добавлены backend-тесты, typecheck frontend и CI.

## Архитектура backend

```text
src/
├── api/              # FastAPI routers и dependency wiring
├── services/         # сценарии работы с файлами и обработка содержимого
├── domain/           # ошибки и статусы предметной области
├── infrastructure/   # SQLAlchemy repositories и файловое хранилище
├── workers/          # Celery app и фоновые задачи
├── core/             # конфигурация и единая DB session factory
├── models.py         # ORM-модели
├── schemas.py        # API-схемы
└── app.py            # composition root
```

API-слой отвечает только за HTTP. `FileService` координирует use cases и границы транзакций. Репозитории инкапсулируют SQLAlchemy-запросы, а `LocalFileStorage` — работу с диском. Чистые функции проверки и извлечения метаданных тестируются отдельно от Celery и БД.

## Дополнительная оптимизация

В исходной реализации фоновые этапы выполнялись последовательно:

```text
scan → metadata → alert
```

Проверка признаков угроз использует данные из БД, а извлечение метаданных читает сохранённый файл. Эти операции не зависят друг от друга, поэтому workflow перестроен в Celery chord:

```text
mark processing → (scan ‖ metadata) → finalize + alert
```

Это уменьшает общую задержку обработки до времени самого медленного из двух этапов вместо их суммы. Redis используется и как broker, и как result backend, необходимый для синхронизации chord. Дополнительно backend и worker используют одну фабрику SQLAlchemy sessions вместо дублирующих engine/pool.

## Архитектура frontend

```text
src/
├── app/              # Next.js page и layout
├── api/              # HTTP client
├── hooks/            # состояние и orchestration страницы
├── features/         # пользовательский сценарий загрузки
├── components/       # таблицы и presentation-компоненты
├── lib/              # форматирование и UI helpers
└── types/            # API-типы
```

Компоненты не знают адреса API и не содержат сетевую логику. Состояние страницы находится в `useFileDashboard`, а форма загрузки изолирована как feature.

## Запуск

Требуется Docker с Compose plugin.

```bash
docker compose -f docker-compose.dev.yml up --build
```

В другом терминале применить миграции:

```bash
docker exec -it backend alembic upgrade head
```

После запуска:

- frontend: <http://localhost:3000/test>
- Swagger UI: <http://localhost:8000/docs>

PostgreSQL доступен только сервисам внутри Docker-сети на стандартном порту `5432`.

## Проверка

Backend:

```bash
cd backend
uv sync --group dev
uv run ruff check .
uv run pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

Тесты покрывают CRUD и скачивание через API, каскадное удаление alerts, потоковое сохранение, правила проверки, извлечение текстовых/PDF-метаданных и структуру параллельного Celery workflow.

## Сохранённая бизнес-логика

- `.exe`, `.bat`, `.cmd`, `.sh`, `.js` считаются подозрительными;
- файл больше 10 MiB требует внимания;
- несовпадение расширения `.pdf` и MIME-типа требует внимания;
- для текста рассчитываются `line_count` и `char_count`;
- для PDF приблизительно рассчитывается число страниц;
- результат обработки создаёт `info`, `warning` или `critical` alert.

## Ограничения MVP

Проверка основана на признаках файла и не является антивирусом. Локальное хранилище подходит для одного узла; в распределённой среде adapter можно заменить на S3-совместимое хранилище без изменения HTTP и application слоёв. Для гарантированной доставки задания при одновременном отказе БД и broker следующим шагом был бы transactional outbox.
