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
