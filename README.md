# Image Processing Service

Сервис асинхронной обработки изображений с созданием миниатюр.

## Описание

Этот проект представляет собой backend-сервис для загрузки и асинхронной обработки изображений. Сервис:

- Принимает изображения через REST API
- Сохраняет информацию в PostgreSQL
- Ставит задачи на обработку в RabbitMQ
- Обрабатывает изображения в отдельном worker'е
- Создает миниатюры в трех размерах: 100x100, 300x300, 1200x1200

## Технологический стек

- **FastAPI** - REST API сервер
- **RabbitMQ** - очередь задач для асинхронной обработки
- **PostgreSQL** - база данных
- **Docker & Docker Compose** - контейнеризация
- **Alembic** - миграции базы данных
- **Pillow** - обработка изображений
- **pytest** - тестирование

## Структура проекта

```
├── src/
│   ├── api/                    # FastAPI приложение
│   │   ├── routes/            # API endpoints
│   │   ├── main.py           # Основное FastAPI приложение
│   │   └── schemas.py        # Pydantic модели
│   ├── worker/               # RabbitMQ worker
│   ├── models/               # SQLAlchemy модели
│   ├── services/            # Бизнес-логика
│   ├── database/            # Подключение к БД
│   └── config.py           # Настройки
├── migrations/             # Alembic миграции
├── tests/                 # Тесты
├── docker-compose.yml     # Docker Compose конфигурация
├── Dockerfile.api        # Dockerfile для API
├── Dockerfile.worker     # Dockerfile для Worker
└── requirements.txt      # Python зависимости
```

## API Endpoints

### POST /images
Загрузка изображения для обработки.

**Request:**
- Content-Type: multipart/form-data
- Body: file (изображение)

**Response:**
```json
{
  "id": "uuid",
  "status": "PROCESSING",
  "message": "Image uploaded successfully and queued for processing"
}
```

### GET /images/{id}
Получение информации об изображении.

**Response:**
```json
{
  "id": "uuid",
  "status": "DONE",
  "original_url": "string",
  "thumbnails": {
    "100x100": "url",
    "300x300": "url", 
    "1200x1200": "url"
  }
}
```

### GET /health
Проверка состояния сервиса.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": true,
    "rabbitmq": true
  },
  "timestamp": "2025-09-16T10:30:00Z"
}
```

## Быстрый старт

### Требования

- Docker
- Docker Compose

### Запуск

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd image-processing-service
```

2. Запустите сервисы:
```bash
docker compose up --build
```

3. Сервис будет доступен по адресу: http://localhost:8000

4. Документация API: http://localhost:8000/docs

5. RabbitMQ Management: http://localhost:15672 (guest/guest)

## Разработка

### Установка зависимостей

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Запуск тестов

```bash
# Все тесты
make test

# Или
pytest tests/ -v
```

### Линтинг и форматирование

```bash
# Проверка кода
make lint

# Форматирование
make format

# Все проверки
make check
```

### Миграции базы данных

```bash
# Применить миграции
alembic upgrade head

# Создать новую миграцию
alembic revision --autogenerate -m "Description"
```

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|-----------|----------|----------------------|
| DATABASE_URL | URL подключения к PostgreSQL | postgresql+asyncpg://postgres:postgres@db:5432/images_db |
| RABBITMQ_URL | URL подключения к RabbitMQ | amqp://guest:guest@rabbit:5672/ |
| STORAGE_PATH | Путь для сохранения файлов | /app/storage |
| MAX_FILE_SIZE | Максимальный размер файла (байты) | 10485760 |
| LOG_LEVEL | Уровень логирования | INFO |
| API_HOST | Хост API сервера | 0.0.0.0 |
| API_PORT | Порт API сервера | 8000 |

## Архитектура

### Компоненты

1. **API Server (FastAPI)** - обрабатывает HTTP запросы, сохраняет файлы, создает записи в БД
2. **Worker** - обрабатывает задачи из очереди, создает миниатюры
3. **Database (PostgreSQL)** - хранит метаданные изображений
4. **Message Queue (RabbitMQ)** - очередь задач для асинхронной обработки

### Процесс обработки

1. Клиент загружает изображение через POST /images
2. API сохраняет файл и создает запись в БД со статусом NEW
3. API отправляет задачу в RabbitMQ и обновляет статус на PROCESSING
4. Worker получает задачу из очереди
5. Worker создает миниатюры и обновляет статус на DONE (или ERROR)
6. Клиент может проверить статус через GET /images/{id}

## Тестирование

Проект включает:

- **Unit тесты** - тестирование отдельных компонентов
- **Integration тесты** - тестирование взаимодействия компонентов
- **API тесты** - тестирование HTTP endpoints

Покрытие кода: > 80%

## CI/CD

GitHub Actions pipeline включает:

1. **Lint** - проверка кода (flake8, mypy, black, isort)
2. **Test** - запуск тестов с PostgreSQL и RabbitMQ
3. **Build** - сборка и публикация Docker образов

## Производственное развертывание

### Docker

Образы доступны в Docker Hub:
- `username/image-processing-api:latest`
- `username/image-processing-worker:latest`

### Kubernetes

Пример манифестов для Kubernetes в папке `k8s/` (если есть).

### Мониторинг

- Health check endpoint: `/health`
- JSON логирование для structured logging
- Метрики через Prometheus (если настроено)

## Безопасность

- Валидация типов файлов
- Ограничение размера файлов
- SQL injection защита через SQLAlchemy ORM
- Асинхронная архитектура для защиты от DoS

## Лицензия

MIT License
