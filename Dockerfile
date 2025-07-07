# Use official Python image as base
FROM python:3.12-slim

# Set environment variable for data directory
ENV DATA_DIR=/data

# Create app directory and data directory
RUN mkdir -p /app ${DATA_DIR}

# Set working directory in container
WORKDIR /app

# Copy requirements if you have one (optional)
# If you don't have requirements.txt, skip this step
COPY requirements.txt .

# Install dependencies (if you have requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your app files to the container
COPY . .

# Expose port 5000 (Flask default)
EXPOSE 5000

# Command to run the app
CMD ["python", "app.py"]
