FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps (add libpq-dev if you plan to use Postgres)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip install --upgrade pip

# copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy project
COPY . .

RUN python Escola/manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "Escola.wsgi:application", "--bind", "0.0.0.0:8000"]
ENTRYPOINT ["/app/entrypoint.sh"]
