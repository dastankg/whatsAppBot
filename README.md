## Запуск проекта

### 1. Клонировать репозиторий

```bash
  git clone https://github.com/your-username/your-repo.git](https://github.com/dastankg/whatsAppBot.git
  cd whatsAppBot
```

### 2. Создать `.env` файл

```bash
  touch .env
```

Заполните значения в `.env` (например, WHAPI_TOKEN и другие параметры).

### 3. Запустить проект с Docker

```bash
  docker-compose up --build
```

Приложение будет доступно по адресу:

```
http://localhost:5000
```

### 4. Убедитесь, что Webhook (BOT_WEBHOOK_URL) правильно указывает на `/hook/messages` вашего сервера.

Webhook должен быть зарегистрирован в панели WHAPI.

