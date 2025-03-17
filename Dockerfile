# Use official Python image
FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1

ENV INFLUXDB_URL=http://influxdb:8086 \
    INFLUXDB_TOKEN="" \
    INFLUXDB_ORG=virdi \
    INFLUXDB_BUCKET=virdi_metrics

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY virdi virdi
COPY main.py .

# Expose port
EXPOSE 8080

# Run the FastAPI server
CMD ["python", "main.py"]
