#base

FROM python:3.13-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=0

#sys deps
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libpq-dev netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

#python deps
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt -r requirements-dev.txt


#project code
COPY . .

# create unprivileged user & group
RUN groupadd -r app && useradd -r -g app app

# make sure app dir is owned by that user
WORKDIR /app
COPY . .
RUN chown -R app:app /app

# drop privileges for runtime
USER app




#runtime cmd

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "flashpoll.asgi:application"]