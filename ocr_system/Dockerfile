# Use the official Python slim image as a base
FROM python:3.11-slim

# Prevent python from writing pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Also install gunicorn to serve the Flask app in production
RUN pip install --no-cache-dir gunicorn

# Copy the rest of the application code
COPY . .

# Expose the port Render assigns
EXPOSE ${PORT}

# Run Gunicorn, binding to Render's dynamic port
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "--timeout", "120", "--workers", "2", "src.web.app:app"]
