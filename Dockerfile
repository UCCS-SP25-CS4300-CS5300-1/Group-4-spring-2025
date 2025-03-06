FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PRODUCTION=1             

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY myproject/ .

RUN mkdir -p /app/database
RUN mkdir -p /app/staticfiles
RUN mkdir -p /app/mediafiles

RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

CMD gunicorn myproject.wsgi:application --bind 0.0.0.0:8000 