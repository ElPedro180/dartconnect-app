FROM mcr.microsoft.com/playwright/python:v1.47.0-focal

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

# Use Gunicorn as the entrypoint
CMD ["gunicorn", "-b", "0.0.0.0:${PORT:-3000}", "flask_app:app"]