FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g dukascopy-node \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p models logs data_cache

EXPOSE 8000

CMD ["sh", "-c", "cd web/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
