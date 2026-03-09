FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/uploads
EXPOSE 8000
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py makemigrations authentication datasets rules checks reports --noinput && python manage.py migrate --noinput && gunicorn datapulse.wsgi:application -c gunicorn.conf.py"]
