# syntax=docker/dockerfile:1

# --- INFO: Stage 1: build the tailwind css (node only lives in this stage) ---
FROM node:22-slim AS css
WORKDIR /app
COPY theme/static_src/package.json theme/static_src/package-lock.json theme/static_src/
RUN npm ci --prefix theme/static_src
# Tailwind scans the templates/python files for class names, so copy the project.
COPY . .
RUN npm run build --prefix theme/static_src


# --- INFO: Stage 2: the actual app ---
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --create-home appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=css /app/theme/static /app/theme/static

# Strip Windows line endings (in case of a Windows checkout), then bake the static files into the image.
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh \
    && DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && chown -R appuser:appuser /app/data

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn"]
