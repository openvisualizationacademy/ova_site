# Use official Python 3.13 image (slim + Bookworm base)
FROM python:3.13-slim-bookworm

# Create a non-root user for running the app
RUN useradd wagtail

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DJANGO_SETTINGS_MODULE=ova.settings.dev \
    DEBUG=1

# Install system dependencies required by Wagtail/Django
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set workdir
WORKDIR /app

# Copy dependency files first (for build caching)
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv pip install -r <(uv pip compile --generate-hashes pyproject.toml)

# Copy app source and set ownership
COPY --chown=wagtail:wagtail . .

# Set correct user and permissions
RUN chown -R wagtail:wagtail /app

USER wagtail

# Port for development server
EXPOSE 8000

# Command to run migrations (optional) and start Daphne
CMD set -xe; python manage.py migrate --noinput; daphne -b 0.0.0.0 -p 8000 ova.asgi:application
