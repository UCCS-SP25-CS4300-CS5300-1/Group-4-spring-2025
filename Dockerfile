FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PRODUCTION=1             

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY myproject/ .

RUN mkdir -p /app/database \
    && mkdir -p /app/staticfiles \
    && mkdir -p /app/mediafiles \
    && mkdir -p /app/ssl \
    && chown -R root:root /app/ssl \
    && chmod -R 600 /app/ssl

RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

RUN python manage.py create_admin_team 

COPY <<-"EOF" /app/entrypoint.sh
#!/bin/bash
if [ "$RUNNING_FROM_SCRIPT" = "1" ]; then
    echo -e "${GREEN}The application will be available at https://localhost:8000/${NC}"
    echo -e "${RED}NOTE: Browser security warnings are expected since we're using a self-signed certificate${NC}"
    echo -e "${GREEN}Press Ctrl+C to stop the container${NC}"
fi
exec "$@"
EOF

CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-"] 