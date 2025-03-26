# Use an official Python slim image as the base image
FROM python:3.11-slim

# Install system dependencies required for Selenium, Chrome, and Chromedriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chrome/Chromedriver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Create and set working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 5000 (the port your Flask app runs on)
EXPOSE 5000

# Set the command to run the Flask app
CMD ["python", "app.py"]
