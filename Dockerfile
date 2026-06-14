FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    OPEN_BROWSER=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       fonts-noto-color-emoji fonts-freefont-ttf fonts-unifont \
       fonts-ipafont-gothic fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m cloakbrowser install
COPY . .

EXPOSE 8000
CMD ["python", "run.py"]
