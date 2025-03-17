# Use official Python image
FROM python:3.13-alpine

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
