## Запуск проекта MovieLibrary
Клонирование репозитория
```bash
git clone https://github.com/spytwo/MovieLibrary.git
```
Открыть проект в редакторе, в корне проекта создать файл `.env` и дополнить переменные окружения
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DB=films_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

VALID_CODE=

EMAIL=
EMAIL_APP_PASSWORD=

SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256

DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5

# Для бота
TELEGRAM_BOT_TOKEN=
API_BASE_URL=http://web:8000
```
Запуск приложения
```bash 
docker compose up --build -d
```
В браузере
```bash 
http://127.0.0.1:8002
```