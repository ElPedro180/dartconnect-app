FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies for Playwright
RUN apt-get update && \
	apt-get install -y --no-install-recommends\
	cs-certificates \
	wget \
	unzip \
	fonts-liberation \
	libnss3 \
	libatk-bridge2.0-0 \
	libxss1 \
	libasound2 \
	libx11-xcb1 \
	libxcomposite1 \
	libxdamage1 \
	libxrandr2 \
    libgbm1 \
	libgtk-3-0 \
	libpango-1.0-0 \
	libpangocairo-1.0-0 \
	libxext6 \
	libxfixes3 \
	libxi6 \
	libxtst6 && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install

EXPOSE 8080
CMD ["python", "flask_app.py"]