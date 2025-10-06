FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libnss3 libatk-bridge2.0-0 libxss1 libasound2 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libgtk-3-0 libpango-1.0-0 libpangocairo-1.0-0 libxext6 libxfixes3 libxi6 libxtst6 \
    wget unzip fonts-liberation && \
    apt-get clean

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install

EXPOSE 8080
CMD ["python", "flask_app.py"]