# Use an official, stable Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to optimize Python inside the container
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container container
WORKDIR /app

# Install system dependencies needed for compiling certain Python extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python library requirements
# If you don't have a requirements.txt, this step installs the core packages safely
RUN pip install --upgrade pip
RUN pip install django djangorestframework requests sphinx sphinx-rtd-theme

# Copy the entire local project directory into the container working workspace
COPY . /app/

# Expose port 8000 to allow traffic to reach the app container engine
EXPOSE 8000

# Run database migrations and boot the Django network engine automatically on launch
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
