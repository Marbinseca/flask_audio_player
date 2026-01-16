FROM python:3.9-slim

# Install system dependencies (FFmpeg is critical)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Environment variables
ENV FLASK_APP=app.py
ENV PORT=8080

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
