# Unified Dockerfile - Frontend + Backend in one container

FROM node:20-slim AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./

ARG VITE_API_BASE_URL=/
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/tests ./tests

COPY --from=frontend-build /frontend/dist ./app/static

RUN mkdir -p /data

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/api/health')"

CMD ["python3", "-m", "uvicorn", "app.main:App", "--host", "0.0.0.0", "--port", "8001"]
