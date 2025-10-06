# Use official Playwright image with Python + all browser deps
FROM mcr.microsoft.com/playwright/python:v1.47.0-focal

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port 3000 inside container
EXPOSE 3000

# Run Flask on 0.0.0.0:3000 so Zeeploy can map it
CMD ["python", "flask_app.py"]