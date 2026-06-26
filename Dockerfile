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
RUN pip install --no-cache-dir -r requirements.txt || \
    (pip install --no-cache-dir ccxt pandas numpy ta stable-baselines3 gymnasium shimmy torch \
     scikit-learn matplotlib python-dotenv pyyaml loguru schedule \
     xgboost lightgbm catboost requests && \
     pip install --no-cache-dir tradingagents || echo "tradingagents skipped")

COPY web/backend/requirements.txt /tmp/web-requirements.txt
RUN pip install --no-cache-dir -r /tmp/web-requirements.txt

COPY . .

RUN mkdir -p models logs data_cache

EXPOSE 8000

CMD ["uvicorn", "web.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
