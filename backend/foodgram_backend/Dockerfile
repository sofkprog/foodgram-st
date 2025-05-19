FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё содержимое в /app
COPY . .

# Копируем скрипт ожидания БД
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Запуск по умолчанию (можно будет переопределить в docker-compose)
CMD ["gunicorn", "foodgram_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
