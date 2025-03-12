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

RUN python manage.py collectstatic --noinput

RUN echo '#!/bin/bash\n\
    set -e\n\
    \n\
    ## Run migrations at container startup\n\
    echo "Running database migrations..."\n\
    python manage.py migrate\n\
    \n\
    ## Create admin team if it does not exist\n\
    echo "Setting up admin team..."\n\
    python manage.py create_admin_team || true\n\
    \n\
    if [ "$RUNNING_FROM_SCRIPT" = "1" ]; then\n\
    echo "The application will be available at https://localhost:8000/"\n\
    echo "NOTE: Browser security warnings are expected since we are using a self-signed certificate"\n\
    echo "Press Ctrl+C to stop the container"\n\
    fi\n\
    \n\
    ## Execute the command passed to docker run\n\
    exec "$@"' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-"] 