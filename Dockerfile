FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for OpenCV and scientific libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY outgraph/requirements.txt /app/outgraph/requirements.txt
RUN pip install --no-cache-dir -r /app/outgraph/requirements.txt

# Copy application source code
COPY . /app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "outgraph.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
